"""
BlazeAI v5 - FastAPI Streaming Server
Created by ShortCodeGuy Studio

Connects the BlazeAI local inference engine to a responsive Web UI.
Features real-time Server-Sent Events (SSE) token streaming, model switching,
session statistics, and conversation management with ZERO hardcoded knowledge.
"""

import json
import os
import queue
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from benchmark import (
    get_current_ram_mb,
    get_system_ram_info,
    session_benchmark,
)
from config import BASE_DIR, DATA_DIR, generation_config, system_config
from conversation import ConversationManager
from inference import InferenceEngine
from model import ModelManager

# Directory paths
WEB_DIR = BASE_DIR / "web"
WEB_DIR.mkdir(parents=True, exist_ok=True)

# Shared backend instances
model_manager = ModelManager.get_instance()
conversation_manager = ConversationManager()
inference_engine = InferenceEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load model weights into RAM on startup for fast first-turn inference."""
    print("\n[BlazeAI] Pre-loading local model weights into RAM...")
    try:
        model_manager.load_model()
        print(f"[BlazeAI] Model ready in {model_manager.load_time_sec:.2f}s! Inference device: CPU\n")
    except Exception as e:
        print(f"[BlazeAI Warning] Could not pre-load model at startup: {e}\n")
    yield


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="BlazeAI v5 API",
    description="Real local AI chatbot API created by ShortCodeGuy Studio",
    version="5.0.0",
    lifespan=lifespan,
)

# CORS middleware for local development and file:// client support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


# Request Models
class ChatRequest(BaseModel):
    message: str


class SettingsRequest(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_new_tokens: Optional[int] = None
    repetition_penalty: Optional[float] = None
    do_sample: Optional[bool] = None


class ModelSwitchRequest(BaseModel):
    model_id: str


class SaveRequest(BaseModel):
    filename: Optional[str] = None


class LoadRequest(BaseModel):
    filename: str


@app.get("/")
async def serve_index():
    """Serves the main single-page application interface."""
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Web UI index.html not found.")
    return FileResponse(index_path)


@app.get("/api/health")
async def health_check():
    """Simple healthcheck endpoint to verify backend connectivity."""
    return {
        "status": "online",
        "service": "BlazeAI v5",
        "creator": "ShortCodeGuy Studio",
        "model_loaded": model_manager.model is not None,
        "active_model": model_manager.model_id or system_config.default_model_id,
    }


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streams tokens in real time via Server-Sent Events (SSE).
    Uses a thread-safe Queue to push model-generated tokens instantly to the client.
    """
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    event_queue: queue.Queue = queue.Queue()

    def token_callback(token: str):
        if token:  # Only emit non-empty tokens
            event_queue.put({"type": "token", "content": token})

    def worker_thread():
        try:
            full_resp, metrics = inference_engine.stream_generate(
                conversation_manager=conversation_manager,
                user_input=user_message,
                on_token_callback=token_callback,
            )
            event_queue.put(
                {
                    "type": "metrics",
                    "data": {
                        "generated_tokens": metrics.generated_tokens,
                        "prompt_tokens": metrics.prompt_tokens,
                        "total_tokens": metrics.total_tokens,
                        "ttft_ms": round(metrics.time_to_first_token_sec * 1000, 1),
                        "speed_tok_s": round(metrics.tokens_per_sec, 2),
                        "total_latency_s": round(metrics.total_latency_sec, 2),
                        "process_ram_mb": round(metrics.process_ram_mb, 1),
                        "system_ram_percent": round(metrics.system_ram_percent, 1),
                    },
                }
            )
            event_queue.put({"type": "done"})
        except Exception as e:
            event_queue.put({"type": "error", "message": str(e)})

    # Start generation in worker thread
    t = threading.Thread(target=worker_thread)
    t.daemon = True
    t.start()

    def event_stream():
        while True:
            try:
                item = event_queue.get(timeout=180.0)
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Generation timed out after 180s'})}\n\n"
                break

            if item["type"] == "token":
                payload = json.dumps({"type": "token", "content": item["content"]})
                yield f"data: {payload}\n\n"
            elif item["type"] == "metrics":
                payload = json.dumps({"type": "metrics", "data": item["data"]})
                yield f"data: {payload}\n\n"
            elif item["type"] == "done":
                payload = json.dumps({"type": "done"})
                yield f"data: {payload}\n\n"
                break
            elif item["type"] == "error":
                payload = json.dumps({"type": "error", "message": item["message"]})
                yield f"data: {payload}\n\n"
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/clear")
async def clear_conversation():
    """Clears current multi-turn conversation memory."""
    conversation_manager.clear()
    return {"status": "cleared", "turns": 0}


@app.get("/api/stats")
async def get_stats():
    """Returns live diagnostic benchmarks and memory profile."""
    sys_ram = get_system_ram_info()
    proc_ram = get_current_ram_mb()
    return {
        "model_name": session_benchmark.model_name or system_config.default_model_id,
        "model_load_time_sec": round(session_benchmark.model_load_time_sec, 2),
        "total_turns": session_benchmark.total_turns,
        "total_tokens_produced": session_benchmark.total_tokens_generated,
        "avg_speed_tok_s": round(session_benchmark.average_speed_tok_per_sec, 2),
        "avg_ttft_ms": round(session_benchmark.average_ttft_ms, 1),
        "process_ram_mb": round(proc_ram, 1),
        "system_ram_used_mb": round(sys_ram["used_mb"], 1),
        "system_ram_total_mb": round(sys_ram["total_mb"], 1),
        "system_ram_percent": sys_ram["percent"],
    }


@app.get("/api/settings")
async def get_settings():
    """Returns current generation hyperparameters."""
    return {
        "temperature": generation_config.temperature,
        "top_p": generation_config.top_p,
        "top_k": generation_config.top_k,
        "max_new_tokens": generation_config.max_new_tokens,
        "repetition_penalty": generation_config.repetition_penalty,
        "do_sample": generation_config.do_sample,
    }


@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    """Updates generation hyperparameters."""
    if req.temperature is not None:
        generation_config.temperature = req.temperature
    if req.top_p is not None:
        generation_config.top_p = req.top_p
    if req.top_k is not None:
        generation_config.top_k = req.top_k
    if req.max_new_tokens is not None:
        generation_config.max_new_tokens = req.max_new_tokens
    if req.repetition_penalty is not None:
        generation_config.repetition_penalty = req.repetition_penalty
    if req.do_sample is not None:
        generation_config.do_sample = req.do_sample
    return {"status": "updated", "settings": await get_settings()}


@app.get("/api/models")
async def list_models():
    """Returns the loaded model details and list of available local models."""
    info = model_manager.get_model_info()
    return {
        "active_model": model_manager.model_id or system_config.default_model_id,
        "model_info": info,
        "available_models": system_config.available_models,
    }


@app.post("/api/model/switch")
async def switch_model(req: ModelSwitchRequest):
    """Switches the active language model."""
    try:
        model_manager.load_model(req.model_id)
        return {
            "status": "success",
            "model_id": req.model_id,
            "load_time_sec": round(model_manager.load_time_sec, 2),
            "model_info": model_manager.get_model_info(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")


@app.get("/api/transcripts")
async def list_transcripts():
    """Lists saved conversation transcripts in data/ directory."""
    files = [
        f.name
        for f in DATA_DIR.glob("*.json")
        if f.is_file()
    ]
    return {"transcripts": sorted(files, reverse=True)}


@app.post("/api/save")
async def save_transcript(req: SaveRequest):
    """Saves the active conversation history."""
    try:
        saved_file = conversation_manager.save(req.filename)
        return {"status": "saved", "filename": saved_file.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/load")
async def load_transcript(req: LoadRequest):
    """Loads a previously saved conversation transcript."""
    try:
        turns = conversation_manager.load(req.filename)
        return {"status": "loaded", "turns": turns, "history": conversation_manager.history}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Starts the Uvicorn web server."""
    print(f"\n============================================================")
    print(f"       BlazeAI v5 Web Server - ShortCodeGuy Studio          ")
    print(f"============================================================")
    print(f"  Web Interface : http://localhost:{port} (or http://127.0.0.1:{port})")
    print(f"  API Docs      : http://localhost:{port}/docs")
    print(f"============================================================\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
