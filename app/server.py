# **Code added by Cursor**
# The upload asks for a locally hosted desk: a question, each agent in order,
# every draft, the footnotes, and downloads for HTML and JPEG. No server was
# in the project. This is that desk, and it does not alter the agent files
# Jordan wrote.

from __future__ import annotations

import asyncio
import json
import os
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.llm import model_available
from app.pipeline import STAGES, run_pipeline
from rag.index import public_status
import research_tools

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "data" / "jobs"
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Linear Research Desk")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class QueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    research_tools.load_local_env()
    return {
        "ok": True,
        "composition": "model" if model_available() else "local",
        "tavily": "api-key" if os.environ.get("TAVILY_API_KEY", "").strip() else "keyless-with-local-fallback",
        "stages": [{"id": sid, "label": label, "action": action} for sid, label, action in STAGES],
    }


@app.get("/api/index")
def index():
    return {"documents": public_status()}


@app.post("/api/research")
async def research(payload: QueryIn):
    query = " ".join(payload.query.split())
    if len(query) < 8:
        raise HTTPException(status_code=400, detail="Write a research question of at least a few words.")
    job_id = uuid.uuid4().hex[:12]
    job_dir = JOBS / job_id

    async def stream():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def emit(event):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def work():
            try:
                result = run_pipeline(query, emit, job_dir)
                emit({"type": "done", "job_id": job_id, **{k: result[k] for k in ("composition", "caption")}})
            except Exception as exc:
                emit({"type": "error", "message": str(exc)})
            finally:
                emit(None)

        threading.Thread(target=work, daemon=True).start()
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/jobs/{job_id}/paper.html")
def paper(job_id: str):
    path = _job_file(job_id, "paper.html")
    return FileResponse(path, media_type="text/html", filename="research-paper.html")


@app.get("/api/jobs/{job_id}/digest.jpg")
def digest(job_id: str):
    path = _job_file(job_id, "digest.jpg")
    return FileResponse(path, media_type="image/jpeg", filename="visual-digest.jpg")


def _job_file(job_id: str, name: str) -> Path:
    if not job_id.isalnum():
        raise HTTPException(status_code=404, detail="That draft is not on this desk.")
    path = JOBS / job_id / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="That file is not ready.")
    return path
