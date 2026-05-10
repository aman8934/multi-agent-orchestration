"""
FastAPI backend for the Multi-Agent Research Pipeline.
Run with: uvicorn main:app --reload
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── Import your pipeline ──────────────────────────────────────────────────────
from agents import (
    build_reader_agent,
    build_search_agent,
    writer_chain,
    critic_chain,
)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Research Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schema ────────────────────────────────────────────────────────────────────
class ResearchRequest(BaseModel):
    topic: str


# ── SSE helper ────────────────────────────────────────────────────────────────
def sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


# ── Streaming generator ───────────────────────────────────────────────────────
async def run_pipeline_stream(topic: str) -> AsyncGenerator[str, None]:
    """
    Runs each agent step sequentially and streams SSE events so the
    frontend can update each agent card in real time.
    """
    state: dict = {}

    # ── Step 1 · Search ───────────────────────────────────────────────────────
    yield sse_event("agent_start", {"agent": "search", "step": 1})

    try:
        search_agent = build_search_agent()
        search_result = await asyncio.to_thread(
            search_agent.invoke,
            {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]},
        )
        state["search_results"] = search_result["messages"][-1].content
        yield sse_event("agent_done", {
            "agent": "search",
            "step": 1,
            "result": state["search_results"],
        })
    except Exception as exc:
        yield sse_event("agent_error", {"agent": "search", "step": 1, "error": str(exc)})
        return

    # ── Step 2 · Reader ───────────────────────────────────────────────────────
    yield sse_event("agent_start", {"agent": "reader", "step": 2})

    try:
        reader_agent = build_reader_agent()
        reader_result = await asyncio.to_thread(
            reader_agent.invoke,
            {
                "messages": [(
                    "user",
                    f"Based on the following search results about '{topic}', "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{state['search_results'][:800]}",
                )]
            },
        )
        state["scraped_content"] = reader_result["messages"][-1].content
        yield sse_event("agent_done", {
            "agent": "reader",
            "step": 2,
            "result": state["scraped_content"],
        })
    except Exception as exc:
        yield sse_event("agent_error", {"agent": "reader", "step": 2, "error": str(exc)})
        return

    # ── Step 3 · Writer ───────────────────────────────────────────────────────
    yield sse_event("agent_start", {"agent": "writer", "step": 3})

    try:
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        state["report"] = await asyncio.to_thread(
            writer_chain.invoke,
            {"topic": topic, "research": research_combined},
        )
        yield sse_event("agent_done", {
            "agent": "writer",
            "step": 3,
            "result": state["report"],
        })
    except Exception as exc:
        yield sse_event("agent_error", {"agent": "writer", "step": 3, "error": str(exc)})
        return

    # ── Step 4 · Critic ───────────────────────────────────────────────────────
    yield sse_event("agent_start", {"agent": "critic", "step": 4})

    try:
        state["feedback"] = await asyncio.to_thread(
            critic_chain.invoke,
            {"report": state["report"]},
        )
        yield sse_event("agent_done", {
            "agent": "critic",
            "step": 4,
            "result": state["feedback"],
        })
    except Exception as exc:
        yield sse_event("agent_error", {"agent": "critic", "step": 4, "error": str(exc)})
        return

    # ── Pipeline complete ─────────────────────────────────────────────────────
    yield sse_event("pipeline_done", {
        "topic": topic,
        "search_results": state.get("search_results", ""),
        "scraped_content": state.get("scraped_content", ""),
        "report": state.get("report", ""),
        "feedback": state.get("feedback", ""),
    })


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Research Pipeline API is running"}


@app.post("/research/stream")
async def research_stream(req: ResearchRequest):
    """
    Stream SSE events as each agent finishes.
    Frontend connects with EventSource / fetch + ReadableStream.
    """
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    return StreamingResponse(
        run_pipeline_stream(req.topic.strip()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if proxied
        },
    )


@app.post("/research")
async def research_sync(req: ResearchRequest):
    """
    Blocking endpoint — runs the full pipeline and returns all results at once.
    Useful for testing without SSE.
    """
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    from pipeline import run_research_pipeline   # local import to avoid circular deps
    result = await asyncio.to_thread(run_research_pipeline, req.topic.strip())
    return result