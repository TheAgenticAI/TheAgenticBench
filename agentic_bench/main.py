from fastapi import FastAPI, WebSocket
from typing import Optional, List

from agentic_bench.orchestrator import SystemOrchestrator

app: FastAPI = FastAPI()
orchestrator: SystemOrchestrator = SystemOrchestrator()

async def generate_response(task: str, websocket: Optional[WebSocket] = None):
    return await orchestrator.run(task, websocket)

@app.get("/agent/chat")
async def agent_chat(task: str) -> List:
    final_agent_response = await generate_response(task)
    return final_agent_response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await generate_response(data, websocket)
