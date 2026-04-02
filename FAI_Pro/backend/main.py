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


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Plug-and-play chat endpoint.
    Accepts a natural language query and returns structured housing insights.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    graph = get_graph()

    try:
        result = graph.invoke({"query": request.query})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(
        answer=result.get("answer", "Sorry, I could not generate a response."),
        intent=result.get("intent_type"),
        chart_data=result.get("chart_data"),
        sources=result.get("sources", []),
        key_metrics=result.get("key_metrics", {}),
        session_id=request.session_id,
    )


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
