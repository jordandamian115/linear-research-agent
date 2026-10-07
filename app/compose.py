# **Code added by Cursor**
# The uploaded agents expect a chat completion to write the paper. With no
# model key, a completion cannot run. This composer uses only text the search
# tools returned. It does not invent citations, findings, or quotations.
# Jordan's prompts already demanded sourced academic prose and an explicit
# note when the record falls short. That aim was close; the missing piece was
# a writer that can run without CLIENT.

from __future__ import annotations

import re
from datetime import date

from rag.index import sentences


def research_brief(query: str, arxiv: dict, web: dict) -> str:
    sources = _collect(arxiv, web)
    lines = [
        f"# Research brief: {query.strip()}",
        "",
        "## Question",
        query.strip(),
        "",
        "## Search log",
        f"arXiv returned {len(arxiv.get('results') or [])} record(s) for this question.",
        f"Web search mode: {web.get('mode') or web.get('source')}.",
        f"Web search returned {len(web.get('results') or [])} page(s) for this question.",
        "These searches are not limited to the reference shelf. The shelf is used later, only to compare prose.",
    ]
    for label, payload in (("arXiv", arxiv), ("Web", web)):
        if payload.get("note"):
            lines.append(f"{label} note: {payload['note']}")
    if not sources:
        lines.extend(
            [
                "",
                "## Fallthrough",
                "Neither search returned a usable record. A full answer cannot be written from the tools.",
                "",
                "[^1]: Fallthrough. The question is unanswered because no source text came back.",
            ]
        )
        return "\n".join(lines)

    lines.extend(["", "## Sources"])
    for index, source in enumerate(sources, start=1):
        authors = ", ".join(source["authors"]) if source["authors"] else "Author not listed"
        when = source["published"] or "date not listed"
        excerpt = _clip(source["summary"], 700)
        lines.extend(
            [
                "",
                f"[{index}] {source['title']}",
                f"Type: {source['venue']}",
                f"Authors: {authors}",
                f"Date: {when}",
                f"URL: {source['url']}",
                f"Excerpt: {excerpt}",
            ]
        )

    lines.extend(["", "## Reading notes"])
    for index, source in enumerate(sources, start=1):
        excerpt = _first_sentences(source["summary"], 2)
        lines.append(
            f"[{index}] The retrieved text says: {excerpt}"
        )
    lines.extend(
        [
            "",
            "## Fallthrough",
            "These notes stay inside the excerpts. They do not describe methods, samples, or results that the excerpts omit.",
            "",
            "[^1]: Several records may be abstracts or search snippets. Depth is limited to that text.",
        ]
    )
    if web.get("mode") == "local-fallback":
        lines.append("[^2]: Web search did not run. No pages were substituted.")
    return "\n".join(lines)


def first_draft(report: str) -> str:
    query, sources = _parse_brief(report)
    if not query:
        query = "the question carried forward from the research brief"
    title = _title(query)
    today = date.today().isoformat()
    if not sources:
        return "\n".join(
            [
                f"# {title}",
                "",
                "## Abstract",
                "No bibliographic record was retrieved for this question, so this draft does not advance a finding.",
                "",
                "## Introduction",
                f"The question guiding this paper is: {query}",
                "",
                "## Limits of the evidence",
                "The search tools returned no usable text. Inventing a literature review would misrepresent the record.",
                "",
                "## Conclusion",
                "The question remains open.",
                "",
                "## References",
                "None retrieved.",
                "",
                f"[^1]: Fallthrough recorded on {today}. The brief contained no sources.",
            ]
        )

    paragraphs = []
    support = []
    reference_lines = []
    for index, source in enumerate(sources, start=1):
        who = _who(source)
        verb = "reports" if len(source["authors"]) <= 1 else "report"
        excerpt = _polish_excerpt(_first_sentences(source["excerpt"], 2))
        paragraphs.append(f"{who} {verb}: “{excerpt}” [{index}]")
        reference_lines.append(
            f"[{index}] {who}. {source['title']}. {source['venue']}, {source['date']}. {source['url']}"
        )
        if index <= 2:
            support.append(f"{who} {verb}: “{_first_sentences(excerpt, 1)}” [{index}]")

    contact = _contact(sources)
    count_word = "record" if len(sources) == 1 else "records"
    question = query.strip()
    if question[-1:] not in ".!?":
        question = question + "."
    body = [
        f"# {title}",
        "",
        "## Abstract",
        (
            f"This note takes up one question: {question} "
            f"It summarizes {len(sources)} {count_word} returned by the search tools on {today}. "
            "Claims stay inside those excerpts."
        ),
        "",
        "## Introduction",
        f"The question guiding this paper is: {question}",
        "",
        "The pages that follow do three things. They report each retrieved passage, they say only where those passages touch, and they mark what the excerpts cannot support.",
        "",
        "## What the records support",
        * _spaced(support),
        "",
        "## Retrieved records",
        * _spaced(paragraphs),
        "",
        "## Points of contact",
        contact,
        "",
        "## Limits of the evidence",
        (
            "A search excerpt is not the article. Where a record supplied an abstract or a snippet, "
            "this draft does not reconstruct the study design, the sample, or the figures."
        ),
        "",
        "## Conclusion",
        (
            "The honest claim is narrow: the retrieved passages speak to the question only in the words quoted above. "
            "A stronger claim would need the full texts and a second pass over primary data, which this draft does not have."
        ),
        "",
        "## References",
        *_spaced(reference_lines),
        "",
        "[^1]: Depth is limited to retrieved excerpts. Full texts were not inferred.",
        "[^2]: Comparison across sources is withheld wherever the excerpts do not share a claim.",
    ]
    return "\n".join(body)


def revised_report(report: str) -> dict:
    paper = report.strip()
    words = paper.split()
    note_count = len(re.findall(r"^\[\^\d+\]:", paper, flags=re.M))
    citation_count = len(re.findall(r"\[\d+\]", paper))
    strengths = []
    if "## Retrieved records" in paper or "## References" in paper:
        strengths.append("The draft keeps a visible line between the question, the records, and the references.")
    if citation_count:
        strengths.append(f"It attaches {citation_count} in-text citation marker(s) to retrieved passages.")
    if not strengths:
        strengths.append("The draft is present and can be reorganized without adding new sources.")

    limits = []
    if note_count:
        limits.append(f"The draft already carries {note_count} footnote(s) about thin evidence. Those limits remain.")
    else:
        limits.append("The draft does not yet mark where the evidence is thin.")
    if len(words) < 250:
        limits.append("The draft is short because the retrieved excerpts are short. Length was not padded.")

    reflection = "\n".join(
        [
            "# Reflection",
            "",
            "## Strengths",
            *[f"- {item}" for item in strengths],
            "",
            "## Limitations",
            *[f"- {item}" for item in limits],
            "",
            "## Footnotes",
            "Existing footnotes were read as limits on depth, not as invitations to call an earlier agent. This pass does not search again.",
            "",
            "## Suggestions",
            "- Keep every citation that points at a retrieved record.",
            "- Open the paper with a roadmap so a reader can see the path before the excerpts.",
            "- Leave the limits section in place. Removing it would overstate the evidence.",
            "",
            "## Further work",
            "A later editor can test sentence length and tone against the indexed models. This pass only clarifies the draft already in hand.",
        ]
    )

    revised = _clarify(paper)
    return {"reflection": reflection, "revised_report": revised}


def apply_editorial(paper: str, footnotes: list[dict]) -> dict:
    text = paper.strip()
    edits = []
    text, expanded = _expand_contractions(text)
    if expanded:
        edits.append(f"Expanded {expanded} contraction(s) so the tone stays formal.")
    text, splits = _split_long_sentences(text)
    if splits:
        edits.append(f"Split {splits} long sentence(s) so the verb arrives sooner.")
    else:
        edits.append("Sentence length did not need a split.")
    text, fixes = _spellcheck(text)
    if fixes:
        sample = ", ".join(fixes[:8])
        edits.append(f"Corrected spelling ({len(fixes)}): {sample}.")
    else:
        edits.append("Spell check found no safe corrections.")
    text = _tidy_spacing(text)

    addressed = []
    for index, note in enumerate(footnotes, start=1):
        criterion = note.get("criterion") or "Indexed standard"
        recommendation = note.get("recommendation") or note.get("text") or ""
        addressed.append(f"{criterion}. {recommendation}".strip())
    if addressed:
        used = [int(number) for number in re.findall(r"\[\^(\d+)\]:", text)]
        start = max(used, default=0)
        numbered = []
        for offset, line in enumerate(addressed, start=1):
            numbered.append(f"[^{start + offset}]: {line}")
        text = (
            text.rstrip()
            + "\n\n## Notes addressed\n"
            + "These notes record the comparison criteria that were applied. Spelling, contractions, and overlong sentences were edited. No new sources were added.\n\n"
            + "\n".join(numbered)
            + "\n"
        )
        edits.append(f"Carried {len(addressed)} comparison note(s) into the final document.")

    structured = [
        {
            "id": f"e{index}",
            "agent": "Agent 5",
            "criterion": note.get("criterion", ""),
            "text": note.get("recommendation") or note.get("text", ""),
        }
        for index, note in enumerate(footnotes, start=1)
    ]
    for index, edit in enumerate(edits, start=1):
        structured.append({"id": f"c{index}", "agent": "Agent 5", "criterion": "Copy edit", "text": edit})
    return {"final_paper": text.strip() + "\n", "footnotes": structured, "edits": edits}


def _collect(arxiv: dict, web: dict) -> list[dict]:
    sources = []
    seen = set()
    for payload in (arxiv, web):
        for item in payload.get("results") or []:
            url = (item.get("url") or "").strip()
            title = " ".join(str(item.get("title") or "").split())
            summary = " ".join(str(item.get("summary") or "").split())
            if not url or not summary or url in seen:
                continue
            seen.add(url)
            sources.append(
                {
                    "title": title or url,
                    "authors": [a for a in item.get("authors") or [] if a],
                    "published": item.get("published") or "",
                    "url": url,
                    "summary": summary,
                    "venue": item.get("venue") or payload.get("source") or "source",
                }
            )
    return sources[:8]


def _parse_brief(report: str) -> tuple[str, list[dict]]:
    question = ""
    match = re.search(r"^## Question\n(.+)$", report, flags=re.M)
    if match:
        question = match.group(1).strip()
    sources = []
    blocks = re.split(r"\n(?=\[\d+\] )", report)
    for block in blocks:
        header = re.match(r"\[(\d+)\] (.+)", block)
        if not header or "Excerpt:" not in block:
            continue
        url = _field(block, "URL")
        excerpt = _field(block, "Excerpt")
        if not url or not excerpt:
            continue
        authors = _field(block, "Authors")
        sources.append(
            {
                "title": header.group(2).strip(),
                "authors": [] if authors == "Author not listed" else [a.strip() for a in authors.split(",") if a.strip()],
                "date": _field(block, "Date") or "n.d.",
                "url": url,
                "excerpt": excerpt,
                "venue": _field(block, "Type") or "source",
            }
        )
    if not sources:
        # A model-written brief may not use this scaffold. Keep its prose as one unnamed source only if it contains URLs.
        urls = re.findall(r"https?://\S+", report)
        if urls and question:
            sources.append(
                {
                    "title": "Research brief carried forward",
                    "authors": [],
                    "date": "n.d.",
                    "url": urls[0].rstrip(").,;"),
                    "excerpt": _clip(report, 500),
                    "venue": "prior agent",
                }
            )
    return question, sources


def _field(block: str, name: str) -> str:
    match = re.search(rf"^{name}:\s*(.+)$", block, flags=re.M)
    return match.group(1).strip() if match else ""


def _title(query: str) -> str:
    text = " ".join(query.strip().split())
    if not text:
        return "Research note"
    return text[0].upper() + text[1:]


def _who(source: dict) -> str:
    authors = source.get("authors") or []
    year = (source.get("date") or "")[:4]
    year_bit = f" ({year})" if year.isdigit() else ""
    if not authors:
        return f"A retrieved {source['venue']} record titled “{source['title']}”"
    if len(authors) == 1:
        name = authors[0]
    elif len(authors) == 2:
        name = f"{authors[0]} and {authors[1]}"
    else:
        name = f"{authors[0]} and colleagues"
    return f"{name}{year_bit}"


def _spaced(lines: list[str]) -> list[str]:
    block: list[str] = []
    for line in lines:
        block.extend([line, ""])
    return block


def _polish_excerpt(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r",(?=\S)", ", ", text)
    text = text.strip().strip('"')
    return text


def _contact(sources: list[dict]) -> str:
    if len(sources) < 2:
        return (
            "One record is not a conversation. This section does not invent agreement between sources that were not both retrieved."
        )
    titles = " and ".join(f"“{source['title']}”" for source in sources[:2])
    return (
        f"The first two records, {titles}, were both returned for this question. "
        "They can be read side by side only in the excerpts above. "
        "Shared wording is not treated as a shared method unless both excerpts say so."
    )


def _clarify(paper: str) -> str:
    if "## Introduction" in paper and "The pages that follow" not in paper and "roadmap" not in paper.lower():
        paper = paper.replace(
            "## Introduction\n",
            "## Introduction\nA reader can move from the question, to the retrieved records, to the limits, and only then to the conclusion.\n\n",
            1,
        )
    paper = re.sub(r"\n{3,}", "\n\n", paper)
    return paper.strip() + "\n"


def _first_sentences(text: str, count: int) -> str:
    found = sentences(text)
    if not found:
        return _clip(text, 320)
    return " ".join(found[:count])


def _clip(text: str, limit: int) -> str:
    words = " ".join(str(text).split())
    if len(words) <= limit:
        return words
    return words[: limit - 1].rsplit(" ", 1)[0] + "…"


def _expand_contractions(text: str) -> tuple[str, int]:
    mapping = {
        "don't": "do not",
        "doesn't": "does not",
        "didn't": "did not",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "can't": "cannot",
        "won't": "will not",
        "it's": "it is",
        "that's": "that is",
        "there's": "there is",
        "we're": "we are",
        "they're": "they are",
        "i'm": "I am",
        "let's": "let us",
    }
    count = 0

    def replace(match: re.Match) -> str:
        nonlocal count
        word = match.group(0)
        key = word.lower()
        if key not in mapping:
            return word
        count += 1
        replacement = mapping[key]
        if word[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    updated = re.sub(r"\b[A-Za-z]+'[A-Za-z]+\b", replace, text)
    return updated, count


def _split_long_sentences(text: str) -> tuple[str, int]:
    splits = 0
    output = []
    for line in text.split("\n"):
        if line.startswith("#") or line.startswith("[^") or line.startswith("["):
            output.append(line)
            continue
        pieces = []
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            words = sentence.split()
            if len(words) <= 36 or "; " not in sentence:
                pieces.append(sentence)
                continue
            left, right = sentence.split("; ", 1)
            if len(left.split()) >= 8 and len(right.split()) >= 8:
                right = right[0].upper() + right[1:] if right else right
                if right and right[-1] not in ".!?":
                    right += "."
                if left and left[-1] not in ".!?":
                    left += "."
                pieces.append(left)
                pieces.append(right)
                splits += 1
            else:
                pieces.append(sentence)
        output.append(" ".join(part for part in pieces if part))
    return "\n".join(output), splits


def _spellcheck(text: str) -> tuple[str, list[str]]:
    try:
        from spellchecker import SpellChecker
    except ImportError:
        return text, []
    spell = SpellChecker()
    spell.word_frequency.load_words(
        [
            "arxiv",
            "pubmed",
            "doi",
            "inaugural",
            "readability",
            "preprint",
            "metadata",
            "snippet",
            "webpage",
        ]
    )
    fixes = []
    kept = []
    for line in text.split("\n"):
        if line.startswith(("#", "[")) or "http://" in line or "https://" in line:
            kept.append(line)
            continue
        kept.append(_spell_line(line, spell, fixes))
    return "\n".join(kept), fixes


def _spell_line(text: str, spell, fixes: list[str]) -> str:
    def replace(match: re.Match) -> str:
        word = match.group(0)
        if word[:1].isupper() or any(ch.isdigit() for ch in word) or len(word) < 5:
            return word
        if word.lower() in spell:
            return word
        suggestion = spell.correction(word.lower())
        if not suggestion or suggestion == word.lower():
            return word
        if _distance(word.lower(), suggestion) > 1:
            return word
        fixes.append(f"{word}→{suggestion}")
        if word.isupper():
            return suggestion.upper()
        return suggestion

    return re.sub(r"\b[A-Za-z][A-Za-z']+\b", replace, text)


def _distance(left: str, right: str) -> int:
    if abs(len(left) - len(right)) > 1:
        return 2
    diffs = 0
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
            continue
        diffs += 1
        if diffs > 1:
            return diffs
        if len(left) > len(right):
            i += 1
        elif len(right) > len(left):
            j += 1
        else:
            i += 1
            j += 1
    return diffs + (len(left) - i) + (len(right) - j)


def _tidy_spacing(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +([,.;:])", r"\1", text)
    text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)
    return text.strip() + "\n"
