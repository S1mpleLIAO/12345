import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from report.dailyreport_llm_mcp import generate_daily_report
from report.heatingreport_llm_mcp import generate_heating_report
from report.emergencyreport_llm_mcp import generate_emergency_report

app = FastAPI(title="12345 智能报表生成系统")

DAILY_MCP_ENTRY = "http://127.0.0.1:9001/daily_report_mcp"
HEATING_MCP_ENTRY = "http://127.0.0.1:9002/heating_report_mcp"
EMERGENCY_MCP_ENTRY = "http://127.0.0.1:9003/emergency_report_mcp"

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReportRequest(BaseModel):
    """日报/紧急专报请求体"""
    date: str  # YYYY-MM-DD


class HeatingReportRequest(BaseModel):
    """供暖报告请求体"""
    year: int


@app.get("/")
async def root_index():
    # 首页
    return FileResponse("static/index.html")


@app.post("/api/generate_report")
async def generate_report_api(request: ReportRequest):
    date_str = request.date
    print(f"收到【日报】生成请求，日期: {date_str}")
    try:
        report_content = await generate_daily_report(date_str, DAILY_MCP_ENTRY)
        return {"status": "success", "report": report_content}
    except Exception as e:
        print(f"日报生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_heating_report")
async def generate_heating_report_api(request: HeatingReportRequest):
    year = request.year
    print(f"收到【供暖报告】生成请求，年份: {year}")
    try:
        report_content = await generate_heating_report(year, HEATING_MCP_ENTRY)
        return {"status": "success", "report": report_content}
    except Exception as e:
        print(f"供暖报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_emergency_report")
async def generate_emergency_report_api(request: ReportRequest):
    date_str = request.date
    print(f"收到【紧急专报】生成请求，日期: {date_str}")
    try:
        report_content = await generate_emergency_report(date_str, EMERGENCY_MCP_ENTRY)
        return {"status": "success", "report": report_content}
    except Exception as e:
        print(f"紧急专报生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ✅ 静态资源只挂载 /static（不要再 mount "/"）
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=8889, reload=True)
