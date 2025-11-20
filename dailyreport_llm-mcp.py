import asyncio
from datetime import date
import json
from typing import List, Dict, Any

from openai import AsyncOpenAI
from fastmcp import Client
from mcp_llm_clint import MCPClientWrapper

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
    mcp_client = MCPClientWrapper()
    async with mcp_client.session:
        answer = await mcp_client.chat(question)
    print("回答：", answer)


if __name__ == "__main__":
    asyncio.run(main("2025-05-19"))
