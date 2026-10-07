# **Code added by Cursor**
# Planned structure.txt already lists the only legal order:
# res_ag, rough_draft_ag, revise_draft_ag, rag_ag, final_draft_ag, graphic_ag.
# Nothing in the upload calls them in that order. This runner does, once each,
# and never asks an agent to return to an earlier one.

from __future__ import annotations

from pathlib import Path

from agents.final_draft_ag import final_draft_ag
from agents.graphic_ag import graphic_ag
from agents.rag_ag import rag_ag
from agents.res_ag import res_ag
from agents.revise_draft_ag import revise_draft_ag
from agents.rough_draft_ag import rough_draft_ag
from app.llm import model_available
from app.render import footnotes_in, fragment, paper_document


STAGES = [
    ("res_ag", "Agent 1", "Gather sources"),
    ("rough_draft_ag", "Agent 2", "Write the first draft"),
    ("revise_draft_ag", "Agent 3", "Revise the draft"),
    ("rag_ag", "RAG Agent", "Compare with indexed texts"),
    ("final_draft_ag", "Agent 5", "Edit the final paper"),
    ("graphic_ag", "Agent 6", "Draw one picture"),
]


def run_pipeline(query: str, emit, job_dir: Path) -> dict:
    job_dir.mkdir(parents=True, exist_ok=True)
    composition = "model" if model_available() else "local"

    _running(emit, "res_ag")
    brief = res_ag(query)
    _done(emit, "res_ag", "Research brief", brief, footnotes_in(brief))

    _running(emit, "rough_draft_ag")
    draft = rough_draft_ag(brief)
    draft_text = draft.get("first_draft", "")
    _done(emit, "rough_draft_ag", "First draft", draft_text, footnotes_in(draft_text))

    _running(emit, "revise_draft_ag")
    revised = revise_draft_ag(draft)
    reflection = revised.get("reflection", "")
    revised_text = revised.get("revised_report", "")
    _done(
        emit,
        "revise_draft_ag",
        "Revised draft",
        reflection + "\n\n" + revised_text,
        footnotes_in(reflection + "\n" + revised_text),
    )

    _running(emit, "rag_ag")
    compared = rag_ag(revised)
    rag_notes = compared.get("footnotes") or []
    _done(
        emit,
        "rag_ag",
        "Comparison and footnotes",
        compared.get("comparison", ""),
        rag_notes,
    )

    _running(emit, "final_draft_ag")
    final = final_draft_ag(compared)
    final_text = final.get("final_paper", "")
    html_path = job_dir / "paper.html"
    html_path.write_text(paper_document(final_text), encoding="utf-8")
    _done(
        emit,
        "final_draft_ag",
        "Final paper",
        final_text,
        final.get("footnotes") or footnotes_in(final_text),
        extra={"paper_url": f"/api/jobs/{job_dir.name}/paper.html"},
    )

    _running(emit, "graphic_ag")
    image_path = job_dir / "digest.jpg"
    graphic = graphic_ag(final, destination=image_path)
    _done(
        emit,
        "graphic_ag",
        "Visual digest",
        "One picture. The paper is still the argument.",
        [],
        extra={"image": f"/api/jobs/{job_dir.name}/digest.jpg"},
    )

    return {
        "job_id": job_dir.name,
        "composition": composition,
        "paper_html": str(html_path),
        "graphic": str(image_path),
        "caption": graphic.get("caption", ""),
    }


def _running(emit, stage_id: str) -> None:
    label, action = _meta(stage_id)
    emit({"type": "step", "id": stage_id, "state": "running", "label": label, "action": action})


def _done(emit, stage_id: str, heading: str, text: str, footnotes: list, extra: dict | None = None) -> None:
    label, action = _meta(stage_id)
    article, _title = fragment(text)
    event = {
        "type": "step",
        "id": stage_id,
        "state": "done",
        "label": label,
        "action": action,
        "heading": heading,
        "html": article,
        "footnotes": footnotes,
    }
    if extra:
        event.update(extra)
    emit(event)


def _meta(stage_id: str) -> tuple[str, str]:
    for sid, label, action in STAGES:
        if sid == stage_id:
            return label, action
    return stage_id, ""
