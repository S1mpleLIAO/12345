import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp_llm_clint import MCPClientWrapper
import uvicorn
import os

app = FastAPI(title="12345日报生成系统")

# 允许跨域（方便调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求体模型
class ReportRequest(BaseModel):
    date: str  # 格式 YYYY-MM-DD

# 确保 static 目录存在
if not os.path.exists("static"):
    os.makedirs("static")

# 挂载静态文件（前端页面）
app.mount("/ui", StaticFiles(directory="static", html=True), name="static")

@app.post("/api/generate_report")
async def generate_report(request: ReportRequest):
    date_str = request.date
    print(f"收到生成请求，日期: {date_str}")
    
    # 这里复用 dailyreport_llm-mcp.py 中的 Prompt 模板
    # 注意：保持 Prompt 逻辑不变，以便 LLM 能够正确调用工具
    prompt = f"""
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

### 4. 企业诉求专报
企业诉求方面，我区受理 **[企业诉求总量]** 件，具体情况如下：

[企业诉求列表]
##列表生成逻辑：请遍历企业诉求数据，按以下Markdown列表格式输出每一条：
1. **[企业名称]**：[精简后的具体诉求内容]。（承办单位：[处置部门]）
例如：
1. **北京笑盈小竹商店**：反映因管道爆裂跑水导致货物被泡，要求赔偿。（承办单位：区教委）
##
"""

    try:
        # 实例化 MCP 客户端并调用
        mcp_client = MCPClientWrapper()
        async with mcp_client.session:
            answer = await mcp_client.chat(prompt)
        
        return {"status": "success", "report": answer}
    
    except Exception as e:
        print(f"生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 启动 Web 服务
    uvicorn.run("web_server:app", host="0.0.0.0", port=8889, reload=True)