import asyncio
from datetime import date
import json
from typing import List, Dict, Any

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError  # 👈 多加了几个异常类型
from fastmcp import Client

VLLM_URL = "http://localhost:8003/v1"
VLLM_KEY = "EMPTY"
MODEL_NAME = "qwen-next"


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
MAX_COMPLETION_TOKENS = 16384
MAX_TOOL_OUTPUT_CHARS = 8192
MAX_HISTORY_MESSAGES = 10
MAX_LLM_RETRIES = 3 


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

    # ===== 新增：LLM 调用带重试封装 =====
    async def _llm_chat_with_retry(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: str,
        max_tokens: int,
        temperature: float = 0.0,
    ):
        last_err: Exception | None = None
        for attempt in range(1, MAX_LLM_RETRIES + 1):
            try:
                return await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (APIError, RateLimitError, APITimeoutError, TimeoutError) as e:
                # 可根据需要 logging，这里简单记录
                last_err = e
                if attempt == MAX_LLM_RETRIES:
                    break
                # 简单指数退避：1s, 2s, 4s ...
                await asyncio.sleep(2 ** (attempt - 1))
            except Exception as e:
                # 其它异常不重试，直接抛出
                last_err = e
                break
        # 把最后一个异常抛回调用方
        raise last_err if last_err is not None else RuntimeError("未知的 LLM 调用错误")

    # ===== 新增：工具调用封装，避免一个工具挂掉导致整个对话失败 =====
    async def _safe_call_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            result = await self.session.call_tool(tool_name, args)
            tool_output = self._unwrap_call_tool_result(result)
        except Exception as e:
            tool_output = f"调用工具 {tool_name} 出错：{e}"
        return self._truncate_tool_output(tool_output)

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

            # 第一次调用：让模型决定要不要用工具（带重试）
            try:
                response = await self._llm_chat_with_retry(
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=MAX_COMPLETION_TOKENS,
                )
            except Exception as e:
                return f"LLM 调用失败：{e}"

            choice = response.choices[0]
            msg = choice.message

            # 没有 tool_calls，直接返回
            if not msg.tool_calls:
                return f"\n\n{msg.content or ''}"

            # 先把带 tool_calls 的 assistant 消息放回上下文
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                    "content": msg.content or "",
                }
            )

            # 对每一个 tool_call 调用 MCP 工具（加了异常保护）
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except Exception:
                    args = {}

                tool_output = await self._safe_call_tool(tool_name, args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_output,
                    }
                )

            messages = self._truncate_history(messages)

            # 第二次调用：基于工具结果继续推理或给最终答案（同样带重试）
            try:
                final_resp = await self._llm_chat_with_retry(
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=MAX_COMPLETION_TOKENS,
                )
            except Exception as e:
                return f"LLM 调用失败（在使用工具之后）：{e}"

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
