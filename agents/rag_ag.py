# **Original code commented out**
# RAG Agent.txt is preserved unchanged. The function is only a docstring:
# `def rag_ag:` does not parse, and it never reads an index. The job in that
# docstring was close: compare the revised paper with indexed texts and write
# footnotes that say why the draft misses their standard.
#
# **Code added by Cursor**
# This agent runs once, after Agent 3, and does not call back. It compares
# sentence length and piled-modifier runs in the revised paper with the
# public texts that could actually be indexed. Sources that could not be
# retrieved are named in the comparison and are not quoted.

from __future__ import annotations

import re

import research_tools
from rag.index import documents, sentences


_VERBS = {
    "is", "are", "was", "were", "be", "been", "being",
    "show", "shows", "showed", "found", "finds", "suggest", "suggests",
    "report", "reports", "include", "includes", "compare", "compared",
    "argue", "argues", "use", "used", "test", "tested", "examine", "examined",
    "measure", "measured", "decrease", "decreased", "increase", "increased",
    "remain", "remains", "does", "do", "did", "has", "have", "had",
    "can", "may", "might", "should", "would", "will",
}


def rag_ag(report) -> dict:
    paper = research_tools.parse_input(report)
    indexed = documents()
    draft_sentences = [s for s in sentences(paper) if not s.startswith("[")]
    draft_lengths = [len(s.split()) for s in draft_sentences]
    mean = round(sum(draft_lengths) / len(draft_lengths), 1) if draft_lengths else 0
    piled = [s for s in draft_sentences if _piled_run(s) >= 4]
    available = [doc for doc in indexed if doc.get("text")]
    missing = [doc for doc in indexed if not doc.get("text")]

    lincoln = _find(available, "lincoln-second-manuscript") or _find(available, "lincoln-addresses")
    pinker = _find(available, "pinker-turgid-prose")
    hyland = _find(available, "hyland-persuasion")
    gernsbacher = _find(available, "gernsbacher-empirical")
    readability = _find(available, "pubmed-28873054")
    confidence = _find(available, "pubmed-34512473")
    plain = _find(available, "pubmed-38008266")
    king = _find(available, "king-dream-essay")

    footnotes = []
    if lincoln and lincoln.get("stats"):
        lincoln_mean = lincoln["stats"].get("mean_sentence_words")
        exemplar = (lincoln.get("exemplars") or ["With malice toward none; with charity for all."])[0]
        footnotes.append(
            {
                "id": "1",
                "criterion": "Sentence length",
                "agent": "RAG Agent",
                "text": (
                    f"The revised draft averages {mean} words a sentence. "
                    f"The indexed {lincoln['title']} averages {lincoln_mean}. "
                    f"A short sentence from that text: “{_clip(exemplar, 140)}” "
                    "Match the clarity, not the oratory."
                ),
                "recommendation": "Break sentences that run past a semicolon so each clause carries one claim.",
            }
        )
    if pinker:
        quote = _clip(pinker["text"], 220)
        footnotes.append(
            {
                "id": "2",
                "criterion": "Piled modifiers and buried verbs",
                "agent": "RAG Agent",
                "text": (
                    f"{len(piled)} sentence(s) in the draft stack four or more long words before a verb. "
                    f"The public abstract of “{pinker['title']}” says: “{quote}”"
                ),
                "recommendation": "Move the verb forward and unpack noun stacks. Do not add new claims while doing it.",
            }
        )
    if readability or confidence or plain:
        bits = []
        for doc in (readability, confidence, plain):
            if doc:
                bits.append(f"{doc['title']}: “{_clip(doc['text'], 180)}”")
        footnotes.append(
            {
                "id": "3",
                "criterion": "Readability of scholarly prose",
                "agent": "RAG Agent",
                "text": "Indexed abstracts on scientific style: " + " ".join(bits),
                "recommendation": "Keep a plain topic sentence at the start of each section, then the evidence.",
            }
        )
    if hyland or gernsbacher:
        citation_count = len(re.findall(r"\[\d+\]", paper))
        hyland_bit = ""
        if hyland:
            hyland_bit = f" Hyland’s indexed text treats interaction and citation as part of the argument: “{_clip(hyland['text'], 180)}”"
        gern_bit = ""
        if gernsbacher:
            gern_bit = f" Gernsbacher’s public abstract asks empirical writing to show its limits: “{_clip(gernsbacher['text'], 180)}”"
        footnotes.append(
            {
                "id": "4",
                "criterion": "Thoroughness and citation",
                "agent": "RAG Agent",
                "text": (
                    f"The draft has {citation_count} citation marker(s). "
                    "Thoroughness here means staying with the retrieved record, not padding it."
                    + hyland_bit
                    + gern_bit
                ),
                "recommendation": "Keep every real citation. Do not fill a thin spot with an unretrieved source.",
            }
        )
    if king:
        footnotes.append(
            {
                "id": "5",
                "criterion": "Specificity of speech",
                "agent": "RAG Agent",
                "text": (
                    "The King Institute page indexed for this desk is a historical article about the speech, not a full transcript. "
                    "Its prose stays concrete: dates, places, and named texts. "
                    f"“{_clip((king.get('exemplars') or [king['text']])[0], 160)}”"
                ),
                "recommendation": "Prefer a named source and a date over a general claim about “the literature.”",
            }
        )
    if missing:
        names = "; ".join(doc["title"] for doc in missing)
        footnotes.append(
            {
                "id": "6",
                "criterion": "Index coverage",
                "agent": "RAG Agent",
                "text": f"These listed sources could not be indexed and were not used as models: {names}.",
                "recommendation": "Do not write as if those texts had been read.",
            }
        )

    comparison_lines = [
        "# Comparison with the indexed texts",
        "",
        f"The revised paper has {len(draft_sentences)} measurable sentences, with a mean length of {mean} words.",
        f"Indexed and usable: {len(available)}. Not retrieved: {len(missing)}.",
        "",
        "## Why the draft does not yet meet the indexed standard",
    ]
    if not footnotes:
        comparison_lines.append("No indexed text was available, so no quality claim is made.")
    for note in footnotes:
        comparison_lines.append(f"- {note['criterion']}: {note['text']} Recommendation: {note['recommendation']}")
    comparison_lines.extend(["", "## Indexed sources"])
    for doc in indexed:
        comparison_lines.append(f"- {doc['status']}: {doc['title']} — {doc['reason']}")

    return {
        "comparison": "\n".join(comparison_lines).strip() + "\n",
        "footnotes": footnotes,
        "revised_report": paper,
    }


def _find(docs: list[dict], doc_id: str) -> dict | None:
    for doc in docs:
        if doc["id"] == doc_id:
            return doc
    return None


def _piled_run(sentence: str) -> int:
    best = run = 0
    for raw in sentence.split():
        token = re.sub(r"[^A-Za-z]", "", raw).lower()
        if len(token) >= 6 and token not in _VERBS:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def _clip(text: str, limit: int) -> str:
    words = " ".join(text.split())
    if len(words) <= limit:
        return words
    return words[: limit - 1].rsplit(" ", 1)[0] + "…"
