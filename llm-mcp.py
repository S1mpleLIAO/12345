import asyncio
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
        "你是一个只通过工具获取事实数据的助手。"
        "对于涉及文件、表格、指标、排名的任何问题，你必须至少调用一个提供的工具，"
        "绝不能凭空捏造数据，也不能仅根据记忆或常识回答。"
        "如果一次工具调用不够，你可以继续调用工具，直到得到可靠结果。"
    ),
}

MAX_TOOL_LOOPS = 10


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
        #从 MCP 拉工具，并转换成 OpenAI tools 规范
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

    async def chat(self, question: str) -> str:
        """
        1. 用 system + user 初始化消息
        2. 多轮：LLM -> 工具 -> 再 LLM，最多 MAX_TOOL_LOOPS 轮
        3. 返回最终 LLM 文本答案
        """
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

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",  
                temperature=0,
            )

            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                return f"(警告：本次未使用工具，结果可能不可靠)\n\n{msg.content or ''}"

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except Exception:
                    args = {}

                result = await self.session.call_tool(tool_name, args)

                tool_output = self._unwrap_call_tool_result(result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_output,
                    }
                )

            final_resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0,
            )

            final_msg = final_resp.choices[0].message
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


async def main():
    question = "我想知道2025年1月2日的统计情况，按照以下格式输出：今日，我区12345热线受理诉求{}件，解决率、满意率（全口径含剔除诉求）分别为{}和{}，较昨日分别上升或者下降{}和{}个百分点（）。11月考核期，前三：{}；后三：{}。"
    mcp_client = MCPClientWrapper(MCP_ENTRY, model=MODEL_NAME)
    async with mcp_client.session:
        answer = await mcp_client.chat(question)
    print("问题：", question)
    print("回答：", answer)

if __name__ == "__main__":
    asyncio.run(main())

