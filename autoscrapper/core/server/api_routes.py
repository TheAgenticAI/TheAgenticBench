import asyncio
import json
import logging
import os
import uuid
import sys
import pytz
import uvicorn
from queue import Empty, Queue
from typing import AsyncGenerator
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from asyncio.subprocess import Process

from core.orchestrator import Orchestrator

class CommandQueryModel(BaseModel):
    command: str = Field(..., description="The command related to web navigation to execute.")
    client_id: str = Field(None, description="The unique identifier for the client.")

# App constants
APP_VERSION = "1.0.0"
APP_NAME = "Web Agent Web API"
API_PREFIX = "/api"
IS_DEBUG = False
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8082))
WORKERS = 1

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn")


 #Utility functions 


def get_ist_time(timestamp=None):
    """Convert timestamp to IST"""
    ist = pytz.timezone('Asia/Kolkata')
    if timestamp:
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = datetime.now()
    return dt.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S IST')

def calculate_duration(start_time, end_time=None):
    """Calculate duration between timestamps"""
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time) if end_time else datetime.now()
    duration = end - start
    return str(duration).split('.')[0]  # Returns HH:MM:SS


def get_app() -> FastAPI:
    """Initialize and configure FastAPI application"""
    fast_app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=IS_DEBUG)
    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    return fast_app

app = get_app()

async def stream_subprocess_output(process: Process, all_stdout: list, all_stderr: list):
    """Stream output from subprocess with real-time terminal logging."""
    
    async def read_stream(stream, store_list, is_stderr=False):
        while True:
            line = await stream.readline()
            if not line:
                break
                
            line_str = line.decode().rstrip()
            store_list.append(line_str)
            
            # Print to terminal in real-time
            if is_stderr:
                print(line_str, file=sys.stderr, flush=True)
                logger.error(line_str)
            else:
                print(line_str, file=sys.stdout, flush=True)
                logger.info(line_str)

    # Create tasks for both streams
    await asyncio.gather(
        read_stream(process.stdout, all_stdout),
        read_stream(process.stderr, all_stderr, True)
    )

active_tasks = {}

@app.post("/execute_task")
async def execute_task(request: Request, query_model: CommandQueryModel) -> StreamingResponse:
    """Execute a web navigation task"""
    task_id = query_model.client_id or str(uuid.uuid4())

    if task_id in active_tasks:
        raise HTTPException(
            status_code=400, 
            detail=f"Task with ID {task_id} is already in progress."
        )
    
    try:
        # Create task-specific orchestrator with headless browser
        orchestrator = Orchestrator(input_mode="API")
        await orchestrator.async_init()
        
        # Setup notification queue
        notification_queue = Queue()
        orchestrator.notification_queue = notification_queue

        # Store task context
        active_tasks[task_id] = {
            "orchestrator": orchestrator,
            "notification_queue": notification_queue,
            "start_time": datetime.now()
        }
    
        # Start the task in the background
        asyncio.create_task(
            orchestrator.run(
                query_model.command,
            )
        )

    except Exception as e:
        await cleanup_task(task_id)
        logger.error(f"Failed to initialize task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Task initialization failed")

    return StreamingResponse(
        stream_notifications(task_id),
        media_type="text/event-stream"
    )


async def stream_notifications(task_id: str) -> AsyncGenerator[str, None]:
    """Stream notifications to the client."""
    notification_queue = active_tasks[task_id]["notification_queue"]

    try:
        while task_id in active_tasks:
            try:
                notification = notification_queue.get_nowait()
                yield f"data: {json.dumps(notification)}\n\n"
                
                # Handle completion states
                if isinstance(notification, dict):
                    if notification.get("type") in ["final", "error", "COMPLETE", "ERROR"]:
                        break
            except Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing notification for task {task_id}: {e}")
                break

    except asyncio.CancelledError:
            logger.info(f"Streaming cancelled for task {task_id}")
    finally:
        await cleanup_task(task_id)


async def cleanup_task(task_id: str):
    """Centralized cleanup function"""
    if task_id in active_tasks:
        task_context = active_tasks[task_id]

        try:
            orchestrator = active_tasks[task_id]["orchestrator"]
            await orchestrator.cleanup()

            # Calculate duration if start_time exists
            if "start_time" in task_context:
                duration = datetime.now() - task_context["start_time"]
                logger.info(f"Task {task_id} completed in {duration}")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            del active_tasks[task_id]
            logger.info(f"Task {task_id} cleaned up successfully")

if __name__ == "__main__":
    logger.info("**********Application Started**********")
    uvicorn.run("main:app", host=HOST, port=PORT, workers=WORKERS, reload=IS_DEBUG, log_level="info")