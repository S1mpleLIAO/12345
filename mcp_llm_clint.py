import asyncio
import json
from typing import List, Dict, Any, Optional, Callable, Awaitable

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from fastmcp import Client

VLLM_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
VLLM_KEY = "sk-5099122b242b4e9c884ddd22828b3760"
MODEL_NAME = "qwen-plus"

MAX_TOOL_LOOPS = 10
MAX_COMPLETION_TOKENS = 16384
MAX_TOOL_OUTPUT_CHARS = 8192
MAX_HISTORY_MESSAGES = 10
MAX_LLM_RETRIES = 3

MAX_TRACE_TEXT_CHARS = 2000

EventCB = Optional[Callable[[Dict[str, Any]], Awaitable[None]]]


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
            "\n摘要不要冗长。然后再发起 tool_calls。"
        )
    return {"role": "system", "content": base}


class MCPClientWrapper:
    def __init__(self, mcp_entry: str, model: str = MODEL_NAME):
        self.mcp_entry = mcp_entry
        self.model = model

        self.client = AsyncOpenAI(api_key=VLLM_KEY, base_url=VLLM_URL)

        self._mcp_client_ctx: Optional[Client] = None
        self.session: Optional[Client] = None

        self.tools: List[Dict[str, Any]] = []
        self.tools_index: Dict[str, str] = {}

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
        print("MCP client disconnected.")

    async def prepare_tools(self):
        if self.session is None:
            raise RuntimeError("MCP client not connected. Use `async with MCPClientWrapper(...) as client:`")

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
        self.tools_index = {t["function"]["name"]: (t["function"].get("description") or "") for t in self.tools}

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

    def _plan_title_for_tool(self, tool_name: str) -> str:
        n = tool_name.lower()
        if "daily_report" in n:
            return "拉取日报基础数据（受理量/解决率/满意率、昨日对比、热点TOP5、企业诉求等）"
        if "monthly_assessment" in n:
            return "拉取月考核期数据（本期与上期对比、环比变化、指标）"
        if "street_assessment" in n:
            return "拉取乡镇街道考核数据（综合成绩排序、前三/后三）"
        if "unit_assessment" in n:
            return "拉取区直单位考核数据（三率统计表）"
        if "lagging_street_rank_trends" in n:
            return "生成倒数三街镇月度排名趋势（每日累计排名）"
        return "调用工具获取所需事实数据"

    async def chat(
        self,
        question: str,
        *,
        debug: bool = False,
        reasoning_summary: bool = False,
        event_cb: EventCB = None,
        section: Optional[str] = None,
    ) -> str:
        if not self.tools:
            await self.prepare_tools()

        self.trace = []

        async def emit(evt: Dict[str, Any]):
            if section:
                evt["section"] = section
            self.trace.append(evt)
            if event_cb:
                await event_cb(evt)

        # plan state
        plan_emitted = False
        plan_steps: List[Dict[str, Any]] = []
        step_map: Dict[str, int] = {}  # tool -> step

        def add_step_for_tool(tool_name: str) -> int:
            """动态扩展计划：遇到新工具则追加 step，并返回 step index"""
            nonlocal plan_steps, step_map
            if tool_name in step_map:
                return step_map[tool_name]
            new_step = len(plan_steps) + 1
            step_map[tool_name] = new_step
            plan_steps.append({"step": new_step, "tool": tool_name, "title": self._plan_title_for_tool(tool_name)})
            return new_step

        async def emit_plan_update(note: str, current_step: int):
            await emit(
                {
                    "type": "plan_update",
                    "round": loop_count,
                    "steps": plan_steps,
                    "current_step": current_step,
                    "note": note,
                }
            )

        messages: List[Dict[str, Any]] = [
            build_system_msg(reasoning_summary),
            {"role": "user", "content": question},
        ]

        loop_count = 0

        while True:
            loop_count += 1
            if loop_count > MAX_TOOL_LOOPS:
                return f"已达到最大工具调用轮数 {MAX_TOOL_LOOPS}，未能确定答案。"

            messages = self._truncate_history(messages)

            # 1) decide tools
            try:
                response = await self._llm_chat_with_retry(
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=MAX_COMPLETION_TOKENS,
                )
            except Exception as e:
                err_text = f"LLM 调用失败：{e}"
                await emit({"type": "error", "round": loop_count, "message": err_text})
                return err_text

            msg = response.choices[0].message

            await emit(
                {
                    "type": "llm_decide_tools",
                    "round": loop_count,
                    "assistant_content": self._clip(msg.content or "", MAX_TRACE_TEXT_CHARS),
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                            "description": self._clip(self.tools_index.get(tc.function.name, ""), 400),
                        }
                        for tc in (msg.tool_calls or [])
                    ],
                }
            )

            if not msg.tool_calls:
                return msg.content or ""

            # 1.5) emit plan once
            if (not plan_emitted) and msg.tool_calls:
                tool_names = [tc.function.name for tc in msg.tool_calls]
                plan_steps = []
                step_map = {}
                for t in tool_names:
                    add_step_for_tool(t)
                await emit(
                    {
                        "type": "plan",
                        "round": loop_count,
                        "steps": plan_steps,
                        "current_step": 1,
                        "note": "已生成执行计划，开始逐步拉取数据并生成报告。",
                    }
                )
                plan_emitted = True

            # push assistant(tool_calls)
            messages.append(
                {"role": "assistant", "tool_calls": [tc.model_dump() for tc in msg.tool_calls], "content": msg.content or ""}
            )

            # 2) execute tools
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except Exception:
                    args = {}

                # ✅ ensure step exists (dynamic extend)
                step_idx = add_step_for_tool(tool_name)
                if plan_emitted:
                    # 如果这是新增工具（不在初始 plan 中），发 plan_update
                    if len(plan_steps) != len(step_map):  # 理论不会成立（同长度），留空
                        pass

                # 若该工具是“新增”导致 plan_steps 变长：这里通过判断 step_idx 是否刚创建来触发 update
                # 简单做法：如果 step_idx == len(plan_steps) 且 tool_name 是刚加的，就更新
                # 我们用一个条件：如果 step_idx == len(plan_steps) 且 tool_name 刚出现在 step_map 中
                # 由于 add_step_for_tool 内部已经处理了重复，无法直接知道是否新增，这里用 contains 前判断：
                # （重做一次最简单）
                # -> 这里改成：先查有没有，再加
                # 为了不改结构太多：用一个前置变量
                # ----
                # 重新实现一次更清晰：
                # (不影响功能，只是判断是否新增)
                # ----
                # 已经拿到了 step_idx，这里做一个“新增检测”
                # 如果 plan_steps 的长度 == step_idx 且 plan_steps[-1].tool == tool_name，视作新增
                is_new = False
                if plan_steps and plan_steps[-1]["tool"] == tool_name and plan_steps[-1]["step"] == step_idx:
                    # 但这也可能是原本最后一个工具；不过只有在此前 tool 不存在时才会 append
                    # 这里进一步判断：如果 tool 在 plan_steps 里出现次数为 1 且 step==最后一个
                    cnt = sum(1 for s in plan_steps if s["tool"] == tool_name)
                    if cnt == 1 and step_idx == len(plan_steps):
                        # 仍可能是初始 plan 的最后一个工具（非新增），所以只在“计划已发出且当前轮出现未在初始 plan 的工具”时触发
                        # 我们用：tool_name 不在最初那批工具名集合（无法保存的话就直接触发也无妨，前端会覆盖同样 steps）
                        is_new = True

                if plan_emitted and is_new and len(plan_steps) > 0:
                    await emit_plan_update(
                        note=f"发现新增工具 {tool_name}，已追加到计划中（Step {step_idx}）。",
                        current_step=step_idx,
                    )

                await emit(
                    {
                        "type": "tool_start",
                        "round": loop_count,
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "args": args,
                        "step": step_idx,
                        "description": self._clip(self.tools_index.get(tool_name, ""), 400),
                    }
                )

                tool_output = await self._safe_call_tool(tool_name, args)

                await emit(
                    {
                        "type": "tool_end",
                        "round": loop_count,
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "step": step_idx,
                        "output": self._clip(tool_output, MAX_TRACE_TEXT_CHARS),
                    }
                )

                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": tool_output}
                )

            messages = self._truncate_history(messages)

            # 3) post tools
            try:
                final_resp = await self._llm_chat_with_retry(
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=MAX_COMPLETION_TOKENS,
                )
            except Exception as e:
                err_text = f"LLM 调用失败（在使用工具之后）：{e}"
                await emit({"type": "error", "round": loop_count, "message": err_text})
                return err_text

            final_msg = final_resp.choices[0].message

            await emit(
                {
                    "type": "llm_post_tools",
                    "round": loop_count,
                    "assistant_content": self._clip(final_msg.content or "", MAX_TRACE_TEXT_CHARS),
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                            "description": self._clip(self.tools_index.get(tc.function.name, ""), 400),
                        }
                        for tc in (final_msg.tool_calls or [])
                    ],
                }
            )

            if final_msg.tool_calls:
                # 继续下一轮（追加工具也会动态扩展 plan）
                messages.append(
                    {"role": "assistant", "content": final_msg.content or "", "tool_calls": [tc.model_dump() for tc in final_msg.tool_calls]}
                )
                continue

            return final_msg.content or ""
