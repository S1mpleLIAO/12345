import asyncio
import json
import os
from typing import Any, Dict, Callable, Awaitable, Optional

from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 你的三个生成脚本（按你上传的文件名）
from report.dailyreport_llm_mcp import generate_daily_report
from report.heatingreport_llm_mcp import generate_heating_report
from report.emergencyreport_llm_mcp import generate_emergency_report


# =========================
# Config
# =========================
# 你原来就是这么写的 MCP ENTRY（示例）
DAILY_MCP_ENTRY = "http://127.0.0.1:9001/daily_report_mcp"
HEATING_MCP_ENTRY = "http://127.0.0.1:9001/heating_report_mcp"
EMERGENCY_MCP_ENTRY = "http://127.0.0.1:9001/emergency_report_mcp"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI()

# 静态资源（如果你有 static 目录，里面放 index.html）
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =========================
# Helpers
# =========================
async def _sse_stream(run_coro: Callable[[Callable[[Dict[str, Any]], Awaitable[None]]], Awaitable[str]]):
    """
    run_coro(event_cb) -> awaitable[str]
    event_cb: async fn(evt)->None, 用于接收 agent 的过程事件
    """
    queue: asyncio.Queue = asyncio.Queue()
    done = asyncio.Event()

    async def event_cb(evt: Dict[str, Any]):
        # 每条过程事件
        await queue.put({"type": "event", "data": evt})

    async def runner():
        try:
            report_text = await run_coro(event_cb)
            await queue.put({"type": "final", "data": {"report": report_text}})
        except Exception as e:
            await queue.put({"type": "error", "data": {"message": str(e)}})
        finally:
            done.set()

    task = asyncio.create_task(runner())

    async def gen():
        try:
            while True:
                if done.is_set() and queue.empty():
                    break
                msg = await queue.get()
                yield "data: " + json.dumps(msg, ensure_ascii=False) + "\n\n"
        finally:
            # 客户端断开时，取消后台任务，防止泄漏
            if not task.done():
                task.cancel()

    return StreamingResponse(gen(), media_type="text/event-stream")


# =========================
# Pages
# =========================
@app.get("/", response_class=HTMLResponse)
async def index():
    """
    首页：返回 static/index.html（如果存在）
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(
        "<h3>index.html not found</h3><p>Please create static/index.html</p>",
        status_code=404,
    )


# =========================
# Non-stream APIs (可选保留)
# =========================
@app.post("/api/generate_report")
async def generate_report_api(payload: Dict[str, Any] = Body(...)):
    date_str = payload.get("date")
    if not date_str:
        return JSONResponse({"error": "missing date"}, status_code=400)

    report = await generate_daily_report(date_str, DAILY_MCP_ENTRY)
    return {"report": report}


@app.post("/api/generate_heating_report")
async def generate_heating_report_api(payload: Dict[str, Any] = Body(...)):
    date_str = payload.get("date")
    if not date_str:
        return JSONResponse({"error": "missing date"}, status_code=400)

    report = await generate_heating_report(date_str, HEATING_MCP_ENTRY)
    return {"report": report}


@app.post("/api/generate_emergency_report")
async def generate_emergency_report_api(payload: Dict[str, Any] = Body(...)):
    date_str = payload.get("date")
    if not date_str:
        return JSONResponse({"error": "missing date"}, status_code=400)

    report = await generate_emergency_report(date_str, EMERGENCY_MCP_ENTRY)
    return {"report": report}


# =========================
# Stream APIs (SSE)
# =========================
@app.post("/api/generate_report/stream")
async def generate_report_stream(payload: Dict[str, Any] = Body(...)):
    """
    POST SSE：
    payload: { "date": "2025-02-13" }
    """
    date_str = payload.get("date")
    if not date_str:
        return JSONResponse({"error": "missing date"}, status_code=400)

    async def run(event_cb):
        # generate_daily_report 需要你在下一步改成支持 event_cb 参数：
        # generate_daily_report(date_str, mcp_entry, event_cb=event_cb)
        return await generate_daily_report(date_str, DAILY_MCP_ENTRY, event_cb=event_cb)

    return await _sse_stream(run)


@app.post("/api/generate_heating_report/stream")
async def generate_heating_report_stream(payload: Dict[str, Any] = Body(...)):
    date_str = payload.get("date")
    if not date_str:
        return JSONResponse({"error": "missing date"}, status_code=400)

    async def run(event_cb):
        return await generate_heating_report(date_str, HEATING_MCP_ENTRY, event_cb=event_cb)

    return await _sse_stream(run)


@app.post("/api/generate_emergency_report/stream")
async def generate_emergency_report_stream(payload: Dict[str, Any] = Body(...)):
    date_str = payload.get("date")
    if not date_str:
        return JSONResponse({"error": "missing date"}, status_code=400)

    async def run(event_cb):
        return await generate_emergency_report(date_str, EMERGENCY_MCP_ENTRY, event_cb=event_cb)

    return await _sse_stream(run)



if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=8889, reload=True)
