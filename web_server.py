import asyncio
import os
from fastapi.responses import FileResponse
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from report.dailyreport_llm_mcp import generate_daily_report

app = FastAPI(title="12345日报生成系统")
DAILY_MCP_ENTRY = "http://127.0.0.1:9001/daily_report_mcp"
# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReportRequest(BaseModel):
    date: str  # 格式 YYYY-MM-DD

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
@app.get("/")
async def root_index():
    return FileResponse("static/index.html")

@app.post("/api/generate_report")
async def generate_report_api(request: ReportRequest):
    """
    API 端点：接收日期，调用业务逻辑生成报告
    """
    date_str = request.date
    print(f"收到生成请求，日期: {date_str}")
    
    try:
        # 直接调用分离出来的业务逻辑函数
        report_content = await generate_daily_report(date_str,DAILY_MCP_ENTRY)
        
        return {
            "status": "success", 
            "report": report_content
        }
    
    except Exception as e:
        print(f"生成失败: {e}")
        # 在生产环境中建议记录详细日志
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 启动 Web 服务
    uvicorn.run("web_server:app", host="0.0.0.0", port=8889, reload=True)