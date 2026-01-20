import json
import asyncio
import uvicorn
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- Requests ---------
class GenerateStreamRequest(BaseModel):
    report_type: str  # "daily" | "heating" | "emergency"
    date: Optional[str] = None  # YYYY-MM-DD for daily/emergency
    year: Optional[int] = None  # year for heating


class ReportRequest(BaseModel):
    date: str  # YYYY-MM-DD


class HeatingReportRequest(BaseModel):
    year: int


# --------- Static ---------
@app.get("/")
async def root_index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")


# --------- SSE helpers ---------
def sse_pack(obj: Dict[str, Any]) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


@app.post("/api/generate/stream")
async def generate_stream(req: GenerateStreamRequest):
    """
    统一 SSE 接口：
    - daily: {report_type:"daily", date:"YYYY-MM-DD"}
    - emergency: {report_type:"emergency", date:"YYYY-MM-DD"}
    - heating: {report_type:"heating", year:2024}
    """
    q: asyncio.Queue = asyncio.Queue()

    async def event_cb(evt: Dict[str, Any]):
        await q.put({"type": "event", "data": evt})

    async def worker():
        try:
            rt = (req.report_type or "").strip().lower()

            if rt == "daily":
                if not req.date:
                    raise ValueError("daily 需要 date (YYYY-MM-DD)")
                report = await generate_daily_report(req.date, DAILY_MCP_ENTRY, event_cb=event_cb)
                await q.put({"type": "final", "data": {"report": report}})

            elif rt == "emergency":
                if not req.date:
                    raise ValueError("emergency 需要 date (YYYY-MM-DD)")
                report = await generate_emergency_report(req.date, EMERGENCY_MCP_ENTRY, event_cb=event_cb)
                await q.put({"type": "final", "data": {"report": report}})

            elif rt == "heating":
                if req.year is None:
                    raise ValueError("heating 需要 year (int)")
                report = await generate_heating_report(req.year, HEATING_MCP_ENTRY, event_cb=event_cb)
                await q.put({"type": "final", "data": {"report": report}})

            else:
                raise ValueError(f"未知 report_type: {req.report_type}")

        except Exception as e:
            await q.put({"type": "error", "data": {"message": str(e)}})
        finally:
            await q.put(None)

    async def gen():
        task = asyncio.create_task(worker())
        try:
            while True:
                item = await q.get()
                if item is None:
                    break
                yield sse_pack(item)
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(gen(), media_type="text/event-stream")


# --------- Non-streaming (保留原接口) ---------
@app.post("/api/generate_report")
async def generate_report_api(request: ReportRequest):
    try:
        report_content = await generate_daily_report(request.date, DAILY_MCP_ENTRY)
        return {"status": "success", "report": report_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_heating_report")
async def generate_heating_report_api(request: HeatingReportRequest):
    try:
        report_content = await generate_heating_report(request.year, HEATING_MCP_ENTRY)
        return {"status": "success", "report": report_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_emergency_report")
async def generate_emergency_report_api(request: ReportRequest):
    try:
        report_content = await generate_emergency_report(request.date, EMERGENCY_MCP_ENTRY)
        return {"status": "success", "report": report_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=8889, reload=True)
