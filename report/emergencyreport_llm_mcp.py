import os
import sys
import asyncio
from typing import Optional, Callable, Awaitable, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mcp_llm_clint import MCPClientWrapper

EventCB = Optional[Callable[[Dict[str, Any]], Awaitable[None]]]


def _get_prompts(date_str: str) -> str:
    return f"""
请统计{date_str}的紧急敏感诉求日报情况。根据提供的各种数据，生成一份严格的 **Markdown** 格式日报。
内容如下：
# {date_str} 紧急敏感诉求日报
今日，我区受理紧急敏感诉求[紧急敏感诉求总数]件，环比上升/下降 [比昨日]；其中，供暖诉求 [供暖诉求件数]件，扬言诉求 [扬言诉求件数]件，消防安全 [消防安全件数]件、供水诉求[供水诉求件数] 件。
今日，已办结[办结件数]件，区中心有效回访  [有效回访件数] 件，响应率、解决率和满意率为 [响应率、解决率和满意率分别为多少]。

## 诉求分类
日办结诉求“三率”变化趋势
| 日期 | 响应率 | 解决率 | 满意率 |
|------|--------|--------|--------|
| [考核期第一天] | [响应率] | [解决率] | [满意率] |
| ··· | [响应率] | [解决率] | [满意率] |
| {date_str} | [响应率] | [解决率] | [满意率] |

## 扬言诉求
1、扬言诉求1：[扬言诉求1内容]，处理结果：[扬言诉求1处理结果]
2、扬言诉求2：[扬言诉求2内容]，处理结果：[扬言诉求2处理结果]
······

## 消防安全诉求
1、消防安全诉求1：[消防安全诉求1内容]，处理结果：[消防安全诉求1处理结果]
2、消防安全诉求2：[消防安全诉求2内容]，处理结果：[消防安全诉求2处理结果]
······

## 供水诉求
1、供水诉求1：[供水诉求1内容]，处理结果：[供水诉求1处理结果]
2、供水诉求2：[供水诉求2内容]，处理结果：[供水诉求2处理结果]
······

## 供暖诉求
1、供暖诉求1：[供暖诉求1内容]，处理结果：[供暖诉求1处理结果]
2、供暖诉求2：[供暖诉求2内容]，处理结果：[供暖诉求2处理结果]
······
"""


async def generate_emergency_report(
    date_str: str,
    mcp_entry: str,
    event_cb: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> str:
    """
    生成紧急敏感诉求报告
    """
    prompts = _get_prompts(date_str)
    
    print(f"[{date_str}] 开始生成紧急敏感诉求日报")
    
    async with MCPClientWrapper(mcp_entry=mcp_entry) as mcp_client:
        ans = await mcp_client.chat(
            prompts,
            debug=False,
            reasoning_summary=True,
            event_cb=event_cb,
            section="emergency",
        )
    
    print("紧急敏感诉求日报生成完毕。")
    return ans


if __name__ == "__main__":
    MCP_ENTRY = "http://127.0.0.1:9003/emergency_report_mcp"
    print(asyncio.run(generate_emergency_report("2025-10-26", MCP_ENTRY)))
