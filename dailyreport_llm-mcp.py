import asyncio
from datetime import date
import json
from typing import List, Dict, Any

from openai import AsyncOpenAI
from fastmcp import Client

VLLM_URL = "http://localhost:8003/v1"
VLLM_KEY = "EMPTY"
MODEL_NAME = "qwen-next"

MCP_ENTRY = "http://127.0.0.1:9001/mysql"

SYSTEM_MSG = {
    "role": "system",
    "content": (
        "你是一个通过工具获取事实数据并生成报告的助手。"
        "对于涉及文件、表格、指标、排名的任何问题，你必须至少调用一个提供的工具，"
        "绝不能凭空捏造数据，也不能仅根据记忆或常识回答。"
        "如果一次工具调用不够，你可以继续调用工具，直到得到可靠结果。"
    ),
}

MAX_TOOL_LOOPS = 10
MAX_COMPLETION_TOKENS = 2048  # 每次最多生成 2048 token，避免 vLLM 默认拉满 26 万
MAX_TOOL_OUTPUT_CHARS = 4000  # 工具返回内容最长截断
MAX_HISTORY_MESSAGES = 10  # 最多保留最近 40 条（不含 system）


class MCPClientWrapper:
    def __init__(self, mcp_entry: str, model: str = MODEL_NAME):
        self.mcp_entry = mcp_entry
        self.model = model

        self.client = AsyncOpenAI(
            api_key=VLLM_KEY,
            base_url=VLLM_URL,
        )

        self.session = Client(mcp_entry)

        self.tools: List[Dict[str, Any]] = []

    async def prepare_tools(self):
        tools = await self.session.list_tools()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": (tool.inputSchema or {}).get("type", "object"),
                        "properties": (tool.inputSchema or {}).get("properties", {}),
                        "required": (tool.inputSchema or {}).get("required", []),
                    },
                },
            }
            for tool in tools
        ]

    @staticmethod
    def _unwrap_call_tool_result(result: Any) -> str:
        for attr in ("text", "data", "json", "content"):
            if hasattr(result, attr):
                val = getattr(result, attr)
                if val is None:
                    continue
                if attr == "text":
                    return val
                try:
                    return json.dumps(val, ensure_ascii=False, indent=2)
                except Exception:
                    return str(val)

        try:
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception:
            return str(result)

    @staticmethod
    def _truncate_tool_output(text: str) -> str:
        if len(text) <= MAX_TOOL_OUTPUT_CHARS:
            return text
        return (
            text[:MAX_TOOL_OUTPUT_CHARS]
            + "\n\n(工具输出过长，已截断，仅保留前部分内容供分析)"
        )

    @staticmethod
    def _truncate_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保留第一个 system，后面只保留最近 N 条"""
        if len(messages) <= MAX_HISTORY_MESSAGES + 1:
            return messages
        system_msg = messages[0]
        others = messages[1:]
        return [system_msg] + others[-MAX_HISTORY_MESSAGES:]

    async def chat(self, question: str) -> str:
        if not self.tools:
            await self.prepare_tools()

        messages: List[Dict[str, Any]] = [
            SYSTEM_MSG,
            {"role": "user", "content": question},
        ]

        loop_count = 0

        while True:
            loop_count += 1
            if loop_count > MAX_TOOL_LOOPS:
                return f"已达到最大工具调用轮数 {MAX_TOOL_LOOPS}，未能确定答案。"

            messages = self._truncate_history(messages)

            # 第一次调用：让模型决定要不要用工具
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0,
                max_tokens=MAX_COMPLETION_TOKENS,
            )

            choice = response.choices[0]
            msg = choice.message

            # 没有 tool_calls，直接返回
            if not msg.tool_calls:
                return f"(未使用工具/已经无须工具调用)\n\n{msg.content or ''}"

            # 规范：先把带 tool_calls 的 assistant 消息放回上下文
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                    "content": msg.content or "",
                }
            )

            # 对每一个 tool_call 调用 MCP 工具
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except Exception:
                    args = {}

                result = await self.session.call_tool(tool_name, args)
                tool_output = self._unwrap_call_tool_result(result)
                tool_output = self._truncate_tool_output(tool_output)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_output,
                    }
                )

            messages = self._truncate_history(messages)

            # 第二次调用：让模型基于工具结果给最终答案（或者继续要工具）
            final_resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0,
                max_tokens=MAX_COMPLETION_TOKENS,
            )

            final_msg = final_resp.choices[0].message

            # 如果还要继续调工具，就把这条 assistant 消息也塞回去，然后下一轮
            if final_msg.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": final_msg.content or "",
                        "tool_calls": [tc.model_dump() for tc in final_msg.tool_calls],
                    }
                )
                continue

            return final_msg.content or ""


async def main(date_str: str):
    question = f"""
请统计{date_str}的日报情况。根据提供的各种数据，生成一份严格的 **Markdown** 格式日报。

请严格遵守以下排版和逻辑要求（##包裹的内容为处理逻辑，不要输出在结果中）：
# 怀柔区12345市民热线反映
## 专报
### 日报 {date_str}
### 1. 总体情况
今日，我区12345热线受理诉求 **[今日受理量]** 件。
解决率、满意率（全口径含剔除诉求）分别为 **[今日解决率]%** 和 **[今日满意率]%**。
较昨日分别[解决率变化描述] **[解决率变化绝对值]** 和[满意率变化描述] **[满意率变化绝对值]** 个百分点。
##逻辑：(今日指标 - 昨日指标)，正数写“上升”，负数写“下降”，零写“持平”。数值取绝对值。##

### 2. 考核排名
* **11月考核期前三**：[前三列表]
* **11月考核期后三**：[后三列表]

### 3. 诉求热点分析
11月考核期，今日我区12345热线受理诉求 **[今日受理量]** 件。
主要集中在 **[最高诉求类型top5-1]**、**[最高诉求类型top5-2]**、**[最高诉求类型top5-3]**、**[最高诉求类型top5-4]**、**[最高诉求类型top5-5]** 等方面。

具体情况如下表所示：

| 序号 | 热点问题/诉求类型 | 数量(件) | 占比 |
| :--- | :--- | :--- | :--- |
| 1 | [Top1类型] | [Top1数量] | [Top1占比]% |
| ···|··· | ···|··· |

##表格要求：按数量降序排列，占比保留一位小数##

### 4. 企业诉求专报
企业诉求方面，我区受理 **[企业诉求总量]** 件，具体情况如下：

[企业诉求列表]
##列表生成逻辑：请遍历企业诉求数据，按以下Markdown列表格式输出每一条：
1. **[企业名称]**：[精简后的具体诉求内容]。（承办单位：[处置部门]）
例如：
1. **北京笑盈小竹商店**：反映因管道爆裂跑水导致货物被泡，要求赔偿。（承办单位：区教委）
##
"""
    mcp_client = MCPClientWrapper(MCP_ENTRY, model=MODEL_NAME)
    async with mcp_client.session:
        answer = await mcp_client.chat(question)
    print("回答：", answer)


if __name__ == "__main__":
    asyncio.run(main("2025-01-02"))
