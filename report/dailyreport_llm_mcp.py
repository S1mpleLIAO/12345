import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import asyncio
from mcp_llm_clint import MCPClientWrapper
from config.loader import config

def _get_prompts(date_str: str):
    """
    构造并返回三个 Prompt 字符串。
    """
    street_count = len(config.raw_streets)
    unit_count = len(config.raw_units)

    q_daily_report = f"""
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

[date所在月份]考核期##上个月19日到当日##，共受理诉求 **[考核期受理量]** 件，环比[月考核期受理诉求变化描述] **[月考核期受理诉求变化率绝对值]**。
##月考核期受理诉求变化逻辑：(本月考核期受理量 - 上月考核期受理量) / 上月考核期受理量，正数写“上升”，负数写“下降”，零写“持平”。数值取绝对值的百分比。##
解决率[月考核期解决率]、满意率分别为 [月考核期满意率]，环比分别[月考核期解决率变化描述] **[月考核期解决率变化绝对值]** 个百分点和[月考核期满意率变化描述] **[月考核期满意率变化绝对值]** 个百分点。
##逻辑：(本月考核期指标 - 上月考核期指标)，正数写“上升”，负数写“下降”，零写“持平”。数值取绝对值。##
 
### 2. 考核排名
##根据【乡镇街道】考核排名数据（综合成绩排序）##
* **[date所在月份]考核期前三**：[前三列表]
* **[date所在月份]考核期后三**：[后三列表]
### 3. 诉求热点分析
今日我区12345热线受理诉求 **[今日受理量]** 件。
主要集中在 **[最高诉求类型top5-1]**、**[最高诉求类型top5-2]**、**[最高诉求类型top5-3]**、**[最高诉求类型top5-4]**、**[最高诉求类型top5-5]** 等方面。

具体情况如下表所示：

| 序号 | 热点问题/诉求类型 | 数量(件) | 占比 |
| :--- | :--- | :--- | :--- |
| 1 | [Top1类型] | [Top1数量] | [Top1占比]% |
| ···|··· | ···|··· |

##表格要求：按数量降序排列，占比保留一位小数##

### 4. 企业诉求
企业诉求方面，今日我区受理 **[企业诉求总量]** 件，具体情况如下：

[企业诉求列表]
##列表生成逻辑：请遍历企业诉求数据，按以下Markdown列表格式输出每一条：
1. **[企业名称]**：[精简后的具体诉求内容]。（承办单位：[处置部门]）
例如：
1. **北京笑盈小竹商店**：反映因管道爆裂跑水导致货物被泡，要求赔偿。（承办单位：区教委）
##
##不要输出其他额外##
"""
    q_street_bottom3_rank = f"""**任务目标：** 生成“落后街镇排名动态监控”趋势表
**基准日期：** {date_str}

请执行以下步骤：
1.  **锁定对象：** 识别出 {date_str} 当日综合考核排名**倒数后三位**的街镇（下文称为 Town_A, Town_B, Town_C）。
2.  **确定周期：** 锁定 {date_str} 所在的完整“月考核周期”（Start_Date 至 End_Date）。
3.  **获取数据：** 查询这三个特定街镇在上述周期内，**每一天**的综合排名数据。
4.  **输出表格：** 生成一份严格的 Markdown 表格。

**格式约束：**
* **严禁**生成任何分析、总结、前言或后缀文字。
* **只需要生成排名变化表格即可**。
* **动态表头：** 表格的第一行必须显示具体的街镇名称，不要使用“街镇1”这种代号。
* **内容：** 单元格内仅填充“排名数字”（整数）。

**期望输出格式示例（仅参考结构，请替换为实际数据）：**

## 后三街镇（[Town_A]、[Town_B]、[Town_C]）月度排名趋势

| 日期 | [Town_A名称] | [Town_B名称] | [Town_C名称] |
| :--- | :--- | :--- | :--- |
| xxxx-xx-xx | 14 | 12 | 16 |
| ... | ... | ... | ... |
| ... | ... | ... | ... |
| ... | ... | ... | ... |
| {date_str} | 16 | 15 | 14 |
只需要生成这个表格
"""
    # --- 街道 Prompt ---
    q_street = f"""请统计{date_str}的街道镇乡综合成绩情况。根据提供的各个街道镇乡的各种数据，生成一份严格的 **Markdown** 格式日报综合成绩情况。
请根据提供的数据中的街道镇乡数据（这是一个包含 {street_count} 个街道数据的列表），直接生成 markdown 表格(输出只包含表名和表格)。

**提供的数据字段对应关系如下：**
- `department` -> 承办单位
- `total` -> 受理量
- `valid` -> 有效回访
- `contact` -> 联系数
- `solved` -> 解决数
- `satisfied` -> 满意数
- `basic_satisfied` -> 基本满意
- `response_rate` -> 响应率 (小数转百分比，保留一位，如 0.532 -> 53.2%)
- `solved_rate` -> 解决率 (小数转百分比，保留一位)
- `satisfied_rate` -> 满意率 (小数转百分比，保留一位)
- `score` -> 综合成绩
- `summary`: 一条已经计算好的“汇总”记录，字段含义与 `records` 中完全一致，其中：
  - `total` / `valid` / `contact` / `solved` / `satisfied` / `basic_satisfied` 为求和结果；
  - `response_rate` / `solved_rate` / `satisfied_rate` / `score` 为算术平均值。

要求：
1. 数据已经由后台排好序并补全了缺失项，**请输出所有 {street_count} 行数据**，按照综合成绩高低排序。
2. 即使该街道各项数据为 0，也要原样输出。
3. 严禁引入任何不在此列表中的单位。

### [镇乡街道诉求办理“三率”统计表[{date_str}所在月份的上个月19日]-[{date_str}]（不含剔除诉求）]
##表名例如：镇乡街道诉求办理“三率”统计表6.19-7.4（全口径含剔除诉求）##
| 序号 | 承办单位 | 受理量 | 有效回访 | 联系数 | 解决数 | 满意数 | 基本满意 | 响应率(%) | 解决率(%) | 满意率(%) | 综合成绩 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | [排名第1的名称] | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
...
| {street_count} | [排名第{street_count}的名称] | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 汇总 |  | [总受理量] | [总有效回访] | [总联系数] | [总解决数] | [总满意数] | [总基本满意] | [平均响应率]% | [平均解决率]% | [平均满意率]% | [平均综合成绩] |
"""


    # --- 区直单位 Prompt ---
    q_unit = f"""请统计{date_str}的考核期各个区直单位综合成绩情况。根据提供的各个区直单位的各种数据，生成一份严格的 **Markdown** 格式日报综合成绩情况。

**提供的数据字段对应关系如下：**
- `department` -> 承办单位
- `total` -> 受理量
- `valid` -> 有效回访
- `contact` -> 联系数
- `solved` -> 解决数
- `satisfied` -> 满意数
- `basic_satisfied` -> 基本满意
- `response_rate` -> 响应率 (小数转百分比，保留一位，如 0.532 -> 53.2%)
- `solved_rate` -> 解决率 (小数转百分比，保留一位)
- `satisfied_rate` -> 满意率 (小数转百分比，保留一位)
- `score` -> 综合成绩
- `summary`: 一条已经计算好的“汇总”记录，字段含义与 `records` 中完全一致，其中：
  - `total` / `valid` / `contact` / `solved` / `satisfied` / `basic_satisfied` 为所有单位的求和结果；
  - `response_rate` / `solved_rate` / `satisfied_rate` / `score` 为算术平均值。

要求：
1. 数据已经由后台排好序并补全了缺失项，**请直接按顺序输出所有 {unit_count} 行数据**，不要做任何筛选或重新排序。
2. 即使该单位各项数据为 0，也要原样输出。
3. 严禁引入任何不在此列表中的单位（如街道、乡、镇等）。

### [区直单位诉求办理“三率”统计表[{date_str}所在月份的上个月19日]-[{date_str}]（不含剔除诉求）]
##表名例如：区直单位诉求办理“三率”统计表6.19-7.4（全口径含剔除诉求）##
| 序号 | 承办单位 | 受理量 | 有效回访 | 联系数 | 解决数 | 满意数 | 基本满意 | 响应率(%) | 解决率(%) | 满意率(%) | 综合成绩 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | [排名第1的名称] | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
...
| {unit_count} | [排名第{unit_count}的名称] | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 汇总 |  | [总受理量] | [总有效回访] | [总联系数] | [总解决数] | [总满意数] | [总基本满意] | [平均响应率]% | [平均解决率]% | [平均满意率]% | [平均综合成绩] |
"""

    return q_daily_report,q_street_bottom3_rank,q_street,q_unit


async def generate_daily_report(date_str: str,mcp_entry: str):
    # 1. 获取构造好的 Prompts
    q_daily,q_street_bottom3_rank,q_street,q_unit = _get_prompts(date_str)
    
    mcp_client = MCPClientWrapper(mcp_entry=mcp_entry)
    
    async with mcp_client.session:
        print(f"[{date_str}] 开始生成日报")
        print(">> 正在生成主体日报...")
        answer1 = await mcp_client.chat(q_daily)
        print("主体日报生成完毕。")
    async with mcp_client.session:
        print(">> 正在生成街道统计表...")
        answer2 = await mcp_client.chat(q_street_bottom3_rank)
        print("街道统计表生成完毕。")
    async with mcp_client.session:
        print(">> 正在生成街道统计表...")
        answer3 = await mcp_client.chat(q_street)
        print("街道统计表生成完毕。")
    async with mcp_client.session:
        print(">> 正在生成委办局统计表...")
        answer4 = await mcp_client.chat(q_unit)
        print("委办局统计表生成完毕。")

    print("生成完毕，正在合并结果...")
    answer = answer1 + "\n\n" + answer2 + "\n\n" + answer3  + "\n\n" + answer4
    return answer2

if __name__ == "__main__":
    MCP_ENTRY = "http://127.0.0.1:9001/daily_report_mcp"
    answer=asyncio.run(generate_daily_report("2025-02-13",MCP_ENTRY))
    print("日报生成任务已完成。", answer)