import json
import asyncio
import uuid
import os
from typing import Dict, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.graph import create_graph
from utils.reporting import generate_report

app = FastAPI(title="AI Pentest Dashboard")
templates = Jinja2Templates(directory="web/templates")

# In-memory storage for scan sessions and their states
scans: Dict[str, dict] = {}
connections: Dict[str, List[WebSocket]] = {}
events_queue: Dict[str, asyncio.Queue] = {}

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.post("/api/scan")
async def start_scan(request: Request, target: str = Form(...), scope: str = Form("all"), deep: bool = Form(False), model: str = Form("google")):
    scan_id = str(uuid.uuid4())
    scans[scan_id] = {
        "id": scan_id,
        "target": target,
        "scope": scope,
        "deep": deep,
        "model_provider": model,
        "status": "initializing",
        "current_state": "START",
        "findings": [],
        "evidence": [],
        "logs": []
    }
    events_queue[scan_id] = asyncio.Queue()

    # Run the scan in the background
    asyncio.create_task(run_scan_task(scan_id))

    return JSONResponse({"scan_id": scan_id})

async def run_scan_task(scan_id: str):
    scan_data = scans[scan_id]
    graph = create_graph()

    initial_state = {
        "target": scan_data["target"],
        "scope": scan_data["scope"],
        "deep": scan_data["deep"],
        "model_provider": scan_data["model_provider"],
        "findings": [],
        "evidence": [],
        "current_state": "START",
        "status": "success",
        "confidence": 0.0
    }

    config = {"configurable": {"thread_id": scan_id}}

    try:
        current_input = initial_state
        while True:
            async for event in graph.astream(current_input, config, stream_mode="values"):
                if not event: continue
                scans[scan_id].update(event)
                phase = event.get("current_state", "Processing")
                status = event.get("status", "working")

                log_msg = f"Phase: {phase} | Status: {status}"
                if not scans[scan_id]["logs"] or scans[scan_id]["logs"][-1] != log_msg:
                    scans[scan_id]["logs"].append(log_msg)

                await broadcast_update(scan_id, {
                    "type": "update",
                    "phase": phase,
                    "status": status,
                    "findings": event.get("findings", []),
                    "log": log_msg
                })

            # Check for interrupts
            state_snapshot = await graph.aget_state(config)
            if state_snapshot.next:
                next_node = state_snapshot.next[0]
                await broadcast_update(scan_id, {
                    "type": "interrupt",
                    "node": next_node,
                    "data": state_snapshot.values
                })

                # Wait for user confirmation from WebSocket
                approved = await events_queue[scan_id].get()
                if not approved:
                    scans[scan_id]["status"] = "cancelled"
                    await broadcast_update(scan_id, {"type": "cancelled"})
                    break

                # Resume with None to continue from checkpoint
                current_input = None
            else:
                break

        scans[scan_id]["status"] = "completed"
        await broadcast_update(scan_id, {"type": "completed"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        scans[scan_id]["status"] = "failed"
        scans[scan_id]["error"] = str(e)
        await broadcast_update(scan_id, {"type": "error", "message": str(e)})

async def broadcast_update(scan_id: str, message: dict):
    if scan_id in connections:
        for ws in connections[scan_id]:
            try:
                await ws.send_json(message)
            except:
                pass

@app.websocket("/ws/{scan_id}")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    if scan_id not in connections:
        connections[scan_id] = []
    connections[scan_id].append(websocket)

    if scan_id in scans:
        await websocket.send_json({"type": "init", "data": scans[scan_id]})

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "confirm" and scan_id in events_queue:
                await events_queue[scan_id].put(msg.get("approved", False))
    except WebSocketDisconnect:
        if scan_id in connections:
            connections[scan_id].remove(websocket)

@app.get("/api/report/{scan_id}/{format}")
async def get_report(scan_id: str, format: str):
    if scan_id not in scans:
        return JSONResponse({"error": "Scan not found"}, status_code=404)

    report_bytes = generate_report(scans[scan_id], format=format)
    filename = f"report_{scan_id}.{format}"
    filepath = f"/tmp/{filename}"
    with open(filepath, "wb") as f:
        f.write(report_bytes)
    return FileResponse(filepath, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
