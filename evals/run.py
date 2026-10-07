# **Code added by Cursor**
# Jordan's notes do not describe an eval run. This script calls the same
# path the agent uses: Agent 1 searches, then Agents 2, 3, the RAG agent,
# Agent 5, and Agent 6 run once each. It saves the paper, the records
# Agent 1 kept, and a verdict. It does not add a topic-specific branch.

from __future__ import annotations

import re
import sys
from pathlib import Path

from agents.final_draft_ag import final_draft_ag
from agents.graphic_ag import graphic_ag
from agents.rag_ag import rag_ag
from agents.res_ag import res_ag
from agents.revise_draft_ag import revise_draft_ag
from agents.rough_draft_ag import rough_draft_ag
from app.compose import _query_overlap, _query_terms

ROOT = Path(__file__).resolve().parent

INQUIRIES = [
    "hypertrophy in bodybuilding",
    "quantum physics",
    "quantum computing",
    "the revolutionary war",
    "the revolutionary way",
    "ghengis khan",
    "sun tzu",
    "the wolf of wallstree",
    "stock market",
    "porche",
    "the boston tea party",
    "the silk road",
    "the fall of the berlin wall",
    "cleopatra",
    "ada lovelace",
    "marie curie",
    "the printing press",
    "a compass",
    "the telescope",
    "how a refrigerator works",
    "how vaccines work",
    "how a lock and key works",
    "transformer",
    "diffusion",
    "entropy",
]

_SHELF = (
    "gettysburg",
    "i have a dream",
    "hyland",
    "gernsbacher",
    "piled modifiers",
    "king institute",
    "second inaugural",
)


def slug(inquiry: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", inquiry.lower()).strip("-")
    return cleaned or "inquiry"


def _section(paper: str, start: str, end: str) -> str:
    begin = paper.find(start)
    if begin < 0:
        return ""
    finish = paper.find(end, begin + len(start))
    if finish < 0:
        return paper[begin:]
    return paper[begin:finish]


def word_count(paper: str) -> int:
    body = _section(paper, "## Abstract", "\n## Notes")
    if not body:
        body = paper
    return len(body.split())


def opening_sentence(paper: str) -> str:
    support = _section(paper, "## What the records support", "## Retrieved records")
    text = re.sub(r"\s+", " ", support)
    text = re.sub(r"^## What the records support\s*", "", text).strip()
    if not text:
        return ""
    match = re.match(r".+?[.!?]", text)
    return match.group(0) if match else text[:240]


def _titles(brief: str) -> list[str]:
    return re.findall(r"^\[(\d+)\] (.+)$", brief, flags=re.M)


def judge(inquiry: str, brief: str, paper: str) -> tuple[str, str, str]:
    terms = _query_terms(inquiry)
    support = _section(paper, "## What the records support", "## Retrieved records")
    support_l = support.lower()
    words = word_count(paper)
    titles = [title for _n, title in _titles(brief)]

    if "No bibliographic record was retrieved" in paper or "## Sources" not in brief:
        return (
            "fell through",
            "empty tools",
            "The search returned no usable record, so the paper does not advance a finding.",
        )

    for marker in _SHELF:
        if marker in support_l:
            return (
                "fell through",
                "RAG shelf",
                f"A claim in the paper uses shelf wording ({marker}).",
            )

    if "none of them is a page about this subject" in support_l:
        return (
            "fell through",
            "search relevance",
            "The search returned records, but no title is a page about this subject, so the paper does not invent one.",
        )

    if "none of them stated the subject" in support_l:
        blob = brief.lower()
        matched = _query_overlap(blob, terms) >= (len(terms) if len(terms) >= 2 else 1)
        if matched:
            return (
                "fell through",
                "writer stitching",
                "Agent 1 kept records, but the writer taught none of their sentences.",
            )
        return (
            "fell through",
            "search relevance",
            "The records Agent 1 kept do not contain the question.",
        )

    if _query_overlap(support, terms) < (len(terms) if len(terms) >= 2 else 1):
        return (
            "fell through",
            "search relevance",
            "The paper's claims do not carry the words of the question.",
        )

    if words < 500:
        return (
            "fell through",
            "writer stitching",
            f"The paper is a short tidbit ({words} words), not an overview a person could talk through.",
        )

    claim_words = len(re.sub(r"\[[0-9]+\]", " ", support).split())
    if claim_words < 180:
        return (
            "fell through",
            "search relevance",
            "The records about this subject are only a short excerpt, so the paper does not invent a longer overview.",
        )

    if not titles:
        return (
            "fell through",
            "empty tools",
            "Agent 1 saved no titled record.",
        )
    return ("worked", "", "")


def run_one(inquiry: str) -> dict:
    folder = ROOT / "inquiries" / slug(inquiry)
    folder.mkdir(parents=True, exist_ok=True)
    brief = res_ag(inquiry)
    draft = rough_draft_ag(brief)
    revised = revise_draft_ag(draft)
    compared = rag_ag(revised)
    final = final_draft_ag(compared)
    paper = final.get("final_paper", "")
    graphic = graphic_ag(final, destination=folder / "digest.jpg")
    status, stage, reason = judge(inquiry, brief, paper)
    steps = (graphic.get("content") or {}).get("steps") or []
    lines = [
        f"inquiry: {inquiry}",
        f"verdict: {status}",
        f"stage: {stage or 'none'}",
        f"words: {word_count(paper)}",
        f"graphic_steps: {len(steps)}",
        f"opening: {opening_sentence(paper)}",
        f"failure: {reason or 'none'}",
    ]
    (folder / "paper.md").write_text(paper, encoding="utf-8")
    (folder / "records.md").write_text(brief, encoding="utf-8")
    (folder / "verdict.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "inquiry": inquiry,
        "status": status,
        "stage": stage,
        "words": word_count(paper),
        "reason": reason,
        "opening": opening_sentence(paper),
        "steps": len(steps),
    }


def main(only: list[str] | None = None) -> None:
    chosen = only or INQUIRIES
    for inquiry in chosen:
        print(f"=== {inquiry} ===", flush=True)
        result = run_one(inquiry)
        print(
            f"{result['status']} words={result['words']} steps={result['steps']} {result['reason']}",
            flush=True,
        )


if __name__ == "__main__":
    main(sys.argv[1:] or None)
