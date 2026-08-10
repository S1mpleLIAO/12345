import os
import sys
import asyncio
from typing import Optional, Callable, Awaitable, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from mcp_llm_clint import MCPClientWrapper
from config.loader import config

def _get_prompts(year: int) -> Dict[str, str]:
    """
    构造供暖季和非供暖季的 Prompt 字典
    """
    q_heating_report = f"""
请统计{year}的供暖季情况。根据提供的各种数据，生成一份严格的 **Markdown** 格式报告。

请严格遵守以下排版和逻辑要求（##包裹的内容为处理逻辑，不要输出在结果中）：
# 一、{year}年供暖季情况
{year}年供暖季（{year}年11月-{year+1}年3月），我区受理供暖诉求**[今年供暖季供暖诉求件数]**件，包括集中供热、清洁能源自采暖和燃煤取暖，整体诉求量与{year-1}年供暖季相比同比上升/下降**[诉求量变化绝对值]** 个百分点；从区中心回访结果看，解决率 **[今年供暖季供暖诉求解决率]%**，满意率**[今年供暖季供暖诉求满意率]%**。
##同比计算逻辑：(今年指标 - 去年指标)，正数写“上升”，负数写“下降”，零写“持平”。数值取绝对值。##

## （一）分月受理情况
{year}年供暖季，我区共受理供暖诉求**[今年供暖季供暖诉求件数]**件，同比上升/下降**[诉求量变化绝对值]** 个百分点。其中**[今年供暖季诉求量最高月份]**诉求量最高，为**[今年供暖季诉求量最高月份诉求量]**件，占比**[今年供暖季诉求量最高月份占比]%**，**[今年供暖季诉求量最低月份]**诉求量最低，为**[今年供暖季诉求量最低月份诉求量]**件，占比**[今年供暖季诉求量最低月份占比]%**
{year-1}年与{year}年各月受理诉求量对比如下表所示：

| 月份 | {year-1}年诉求量(件) | {year}年诉求量(件) |
| :--- | :--- | :--- |
| 11月 | [11月去年诉求量] | [11月今年诉求量] |
| 12月 | [12月去年诉求量] | [12月今年诉求量] |
| 1月 | [1月去年诉求量] | [1月今年诉求量] |
| 2月 | [2月去年诉求量] | [2月今年诉求量] |
| 3月 | [3月去年诉求量] | [3月今年诉求量] |
##表格要求：按月份顺序排列，占比保留一位小数##

## （二）集中供暖综合情况
1.从整体情况来看：{year}年供暖季，我区集中供暖诉求**[今年供暖季集中供热诉求件数]**件，占比**[今年供暖季集中供热占比]%**，在3类取暖方式中占比最高，同比上升/下降**[供暖季集中供热量变化绝对值]** 个百分点。从区回访结果看，解决率 **[今年供暖季集中供热诉求解决率]%**，满意率**[今年供暖季集中供热诉求满意率]%**。
2.主要反映：**[今年供暖季集中供热诉求所有类型]**问题
##写出前六种问题##
3.从供热公司看，反映**[今年供暖季供热公司诉求量排名第一]**诉求最多，为**[今年供暖季供热公司诉求量排名第一件数]**件，其次是**[今年供暖季供热公司诉求量排名第二]****[今年供暖季供热公司诉求量排名第二件数]**件、**[今年供暖季供热公司诉求量排名第三]****[今年供暖季供热公司诉求量排名第三件数]**件。
集中供暖诉求点位分布表（50件以上）
| 供热公司 | 诉求量(件) |
| :--- | :--- |
| [供热公司1] | [诉求量1] |
|···| ··· |
##表格要求：按诉求量降序排列##

## （三）调研点位情况
##逻辑：请根据提供的调研点位数据进行描述##
"""

    q_heating_off_report = f"""
请统计{year}下一年非供暖季的供暖诉求情况。根据提供的各种数据，生成一份严格的 **Markdown** 格式报告。
# 二、{year}年非供暖季供暖诉求情况
## （一）综合情况
[非供暖季起止时间月份]（例如4月-10月），共受理集中供暖诉求[非供暖季供暖诉求件数]件。从诉求内容看，主要反映：[问题类型]，具体分类占比情况如下：
| 问题类型 | 数量 |占比 |
| :--- | :--- | :--- |
| [问题类型1] | [数量1] | [占比1]% |
|···| ··· | ··· |
##表格要求：按数量降序排列，占比保留一位小数##
## （二）调研点位情况
##逻辑：请根据提供的非供暖季调研数据进行描述##
"""
    return {
        "season": q_heating_report,
        "off_season": q_heating_off_report
    }

async def generate_heating_report(
    year: int,
    mcp_entry: str,
    event_cb: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> str:
    """
    生成供暖报告（分供暖季和非供暖季两段）
    """
    prompts = _get_prompts(year)
    
    print(f"[{year}] 开始生成供暖季专题报告")

    async with MCPClientWrapper(mcp_entry=mcp_entry) as mcp_client:
        # 第一段：供暖季
        print(">> 正在生成供暖季综合分析...")
        ans1 = await mcp_client.chat(
            prompts["season"],
            debug=False,
            reasoning_summary=False,
            event_cb=event_cb,
            section="heating_season",
        )

        # 第二段：非供暖季
        print(">> 正在生成非供暖季数据分析...")
        ans2 = await mcp_client.chat(
            prompts["off_season"],
            debug=False,
            reasoning_summary=False,
            event_cb=event_cb,
            section="heating_offseason",
        )

    print("供暖专题报告生成完毕，正在合并结果...")
    return ans1 + "\n\n" + ans2

if __name__ == "__main__":
    MCP_ENTRY = "http://127.0.0.1:9002/heating_report_mcp"
    ans = asyncio.run(generate_heating_report(2024, MCP_ENTRY))
    print("任务已完成。")
    print(ans)