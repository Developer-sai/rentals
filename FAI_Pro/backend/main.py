"""
main.py
FastAPI entry point for the Agentic RAG Irish Housing Assistant.
Exposes /api/chat as a plug-and-play endpoint.
"""
import os
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from graph import get_graph

app = FastAPI(
    title="Irish Housing AI Assistant",
    description="Agentic RAG-powered chatbot for Irish housing market analysis",
    version="1.0.0",
)

# CORS – allow all origins so the frontend can be served from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChartData(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    labels: Optional[list] = None
    values: Optional[list] = None
    unit: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    chart_data: Optional[dict] = None
    sources: Optional[list] = None
    key_metrics: Optional[dict] = None
    session_id: Optional[str] = None


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "Irish Housing Assistant"}


import json
import asyncio
from fastapi.responses import StreamingResponse

from session_manager import session_store

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Streaming chat endpoint using SSE.
    Yields status updates and final data chunks.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    graph = get_graph()
    session_id = request.session_id or "default"

    async def event_generator():
        try:
            # 1. Get existing history for this session
            history = session_store.get_history(session_id)
            
            # Initialize with user query and history
            input_state = {
                "query": request.query,
                "history": history
            }
            
            # 2. Stream the graph execution
            async for event in graph.astream(input_state, stream_mode="updates"):
                for node_name, node_state in event.items():
                    status = node_state.get("status", f"Node {node_name} working...")
                    yield f"data: {json.dumps({'type': 'status', 'message': status})}\n\n"
                    await asyncio.sleep(0.05)

            # 3. Final execution to get the state
            final_result = await graph.ainvoke(input_state)
            
            # 4. Update session history with the new pair
            session_store.add_message(session_id, "user", request.query)
            session_store.add_message(session_id, "bot", final_result.get("answer", ""))

            # Yield the final 'data' event
            payload = {
                "type": "data",
                "answer": final_result.get("answer", ""),
                "intent": final_result.get("intent_type"),
                "chart_data": final_result.get("chart_data"),
                "sources": final_result.get("sources", []),
                "key_metrics": final_result.get("key_metrics", {}),
                "session_id": session_id
            }
            yield f"data: {json.dumps(payload)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/meta/counties")
def get_counties():
    """Return list of all available counties."""
    from data_manager import get_counties as _get
    return {"counties": _get()}


@app.get("/api/meta/years")
def get_years():
    """Return list of all available years."""
    from data_manager import get_years as _get
    return {"years": _get()}


# ──────────────────────────────────────────────
# Serve Frontend (Vite React build → frontend/dist/)
# Run: cd frontend && npm run build
# Dev: run React dev server (npm run dev) + FastAPI separately
# ──────────────────────────────────────────────
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Serve React SPA — all non-API routes return index.html."""
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
