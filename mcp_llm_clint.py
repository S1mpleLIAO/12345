import asyncio
import json
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from fastmcp import Client

VLLM_URL = "http://localhost:8003/v1"
VLLM_KEY = "EMPTY"
MODEL_NAME = "qwen-next"

MAX_TOOL_LOOPS = 10
MAX_COMPLETION_TOKENS = 16384
MAX_TOOL_OUTPUT_CHARS = 8192
MAX_HISTORY_MESSAGES = 10
MAX_LLM_RETRIES = 3

MAX_TRACE_TEXT_CHARS = 2000
MAX_PRINT_TOOL_OUTPUT_CHARS = 1200
MAX_PRINT_CONTENT_CHARS = 1500


def build_system_msg(reasoning_summary: bool) -> Dict[str, Any]:
    base = (
        "你是一个通过工具获取事实数据并生成报告的助手。"
        "对于涉及文件、表格、指标、排名的任何问题，你必须至少调用一个提供的工具，"
        "绝不能凭空捏造数据，也不能仅根据记忆或常识回答。"
        "如果一次工具调用不够，你可以继续调用工具，直到得到可靠结果。"
    )

    if reasoning_summary:
        base += (
            "\n\n当你准备调用工具时，请先在回复正文输出【工具选择摘要】（简短、可执行）："
            "\n- 你缺少哪些关键事实/字段"
            "\n- 你准备调用哪些工具（工具名）"
            "\n- 每个工具分别要解决什么问题"
            "\n摘要不要冗长、不要输出详细推理。然后再发起 tool_calls。"
        )

    return {"role": "system", "content": base}


class MCPClientWrapper:
    """
    ✅ 关键：fastmcp.Client 必须 async with 才会连接
    """

    def __init__(self, mcp_entry: str, model: str = MODEL_NAME):
        self.mcp_entry = mcp_entry
        self.model = model

        self.client = AsyncOpenAI(api_key=VLLM_KEY, base_url=VLLM_URL)

        self._mcp_client_ctx: Optional[Client] = None
        self.session: Optional[Client] = None

        self.tools: List[Dict[str, Any]] = []
        self.trace: List[Dict[str, Any]] = []

    async def __aenter__(self):
        self._mcp_client_ctx = Client(self.mcp_entry)
        self.session = await self._mcp_client_ctx.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._mcp_client_ctx is not None:
            await self._mcp_client_ctx.__aexit__(exc_type, exc, tb)
        self._mcp_client_ctx = None
        self.session = None

    async def prepare_tools(self):
        if self.session is None:
            raise RuntimeError(
                "MCP client not connected. Use: `async with MCPClientWrapper(...) as client:`"
            )
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
                last_err = e
                if attempt == MAX_LLM_RETRIES:
                    break
                await asyncio.sleep(2 ** (attempt - 1))
            except Exception as e:
                last_err = e
                break
        raise last_err if last_err is not None else RuntimeError("未知的 LLM 调用错误")

    async def _safe_call_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        if self.session is None:
            return "调用工具失败：MCP 未连接（session is None）"
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
        return text[:MAX_TOOL_OUTPUT_CHARS] + "\n\n(工具输出过长，已截断)"

    @staticmethod
    def _truncate_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(messages) <= MAX_HISTORY_MESSAGES + 1:
            return messages
        system_msg = messages[0]
        others = messages[1:]
        return [system_msg] + others[-MAX_HISTORY_MESSAGES:]

    @staticmethod
    def _clip(s: str, limit: int) -> str:
        if not s:
            return ""
        return s if len(s) <= limit else s[:limit] + " ...<truncated>"

    def _print_round_header(self, title: str):
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)

    def _print_content(self, content: str):
        content = self._clip(content or "", MAX_PRINT_CONTENT_CHARS)
        if content.strip():
            print("\n🤔 Assistant Content:")
            print(content)
        else:
            print("\n🤔 Assistant Content: (empty)")

    def _print_tool_calls(self, tool_calls):
        print("\n🛠️ Tool Calls:")
        for tc in tool_calls:
            print(f"  - tool_call_id: {tc.id}")
            print(f"    name: {tc.function.name}")
            print(f"    arguments: {tc.function.arguments}")

    async def chat(
        self,
        question: str,
        *,
        debug: bool = False,
        trace_path: Optional[str] = None,
        reasoning_summary: bool = False,
    ) -> str:
        if not self.tools:
            await self.prepare_tools()

        self.trace = []

        messages: List[Dict[str, Any]] = [
            build_system_msg(reasoning_summary),
            {"role": "user", "content": question},
        ]

        loop_count = 0

        while True:
            loop_count += 1
            if loop_count > MAX_TOOL_LOOPS:
                final = f"已达到最大工具调用轮数 {MAX_TOOL_LOOPS}，未能确定答案。"
                if trace_path:
                    with open(trace_path, "w", encoding="utf-8") as f:
                        json.dump(self.trace, f, ensure_ascii=False, indent=2)
                return final

            messages = self._truncate_history(messages)

            # decide tools
            try:
                response = await self._llm_chat_with_retry(
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=MAX_COMPLETION_TOKENS,
                )
            except Exception as e:
                final = f"LLM 调用失败：{e}"
                if trace_path:
                    with open(trace_path, "w", encoding="utf-8") as f:
                        json.dump(self.trace, f, ensure_ascii=False, indent=2)
                return final

            msg = response.choices[0].message

            self.trace.append(
                {
                    "round": loop_count,
                    "phase": "decide_tools",
                    "assistant_content": self._clip(msg.content or "", MAX_TRACE_TEXT_CHARS),
                    "tool_calls": [
                        {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                        for tc in (msg.tool_calls or [])
                    ],
                }
            )

            if debug:
                self._print_round_header(f"🔄 Round {loop_count} | decide_tools")
                self._print_content(msg.content or "")
                if msg.tool_calls:
                    self._print_tool_calls(msg.tool_calls)
                else:
                    print("\n🛑 No tool calls. Will answer directly.")

            # no tools -> done
            if not msg.tool_calls:
                final_answer = msg.content or ""
                if trace_path:
                    with open(trace_path, "w", encoding="utf-8") as f:
                        json.dump(self.trace, f, ensure_ascii=False, indent=2)
                return final_answer

            # push assistant tool-call msg
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                    "content": msg.content or "",
                }
            )

            # execute tools
            tool_exec_records = []
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except Exception:
                    args = {}

                if debug:
                    print(f"\n>>> 执行工具: {tool_name} (tool_call_id={tool_call.id})")
                    print(f"    args(dict): {args}")

                tool_output = await self._safe_call_tool(tool_name, args)

                tool_exec_records.append(
                    {
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "args": args,
                        "output": self._clip(tool_output, MAX_TRACE_TEXT_CHARS),
                    }
                )

                if debug:
                    print("<<< 工具输出(截断):")
                    print(self._clip(tool_output, MAX_PRINT_TOOL_OUTPUT_CHARS))

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_output,
                    }
                )

            self.trace.append({"round": loop_count, "phase": "tool_results", "tools": tool_exec_records})

            messages = self._truncate_history(messages)

            # post tools
            try:
                final_resp = await self._llm_chat_with_retry(
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=MAX_COMPLETION_TOKENS,
                )
            except Exception as e:
                final = f"LLM 调用失败（在使用工具之后）：{e}"
                if trace_path:
                    with open(trace_path, "w", encoding="utf-8") as f:
                        json.dump(self.trace, f, ensure_ascii=False, indent=2)
                return final

            final_msg = final_resp.choices[0].message

            self.trace.append(
                {
                    "round": loop_count,
                    "phase": "post_tools",
                    "assistant_content": self._clip(final_msg.content or "", MAX_TRACE_TEXT_CHARS),
                    "tool_calls": [
                        {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                        for tc in (final_msg.tool_calls or [])
                    ],
                }
            )

            if debug:
                self._print_round_header(f"🔄 Round {loop_count} | post_tools")
                self._print_content(final_msg.content or "")
                if final_msg.tool_calls:
                    print("\n🧩 Need more tools, continuing...")
                    self._print_tool_calls(final_msg.tool_calls)
                else:
                    print("\n✅ Enough info. Final answer ready.")

            if final_msg.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": final_msg.content or "",
                        "tool_calls": [tc.model_dump() for tc in final_msg.tool_calls],
                    }
                )
                continue

            final_answer = final_msg.content or ""
            if trace_path:
                with open(trace_path, "w", encoding="utf-8") as f:
                    json.dump(self.trace, f, ensure_ascii=False, indent=2)
            return final_answer
