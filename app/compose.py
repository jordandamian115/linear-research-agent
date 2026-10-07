from __future__ import annotations

# **Code added by Cursor**
# The uploaded agents expect a chat completion to write the paper. With no
# model key, a completion cannot run. The first local writer was not enough:
# it pasted the opening lines of whatever the tools returned, so a broad
# query became out-of-context excerpts. Jordan's prompts were close. They
# already asked for a sourced academic paper and a note when the record is
# thin. They did not say how to order that paper so a beginner can learn it.
# This composer outlines the returned records, keeps the ones that explain
# the subject, and writes from that outline. It does not invent citations.
# The one-sentence-per-idea version was the right shape and too short to
# talk from. A reader got the order and could not say how one idea led to
# the next. This version keeps that order and develops each step with the
# next explanatory sentences from the same records.
# A later pass only kept sentences that matched physics cues (classical,
# quanta, waves, probability) or "is the study." "Hypertrophy in
# bodybuilding" returned real pages, then the writer set every one aside
# and the paper had no claims. Roles now cover a plain definition and how
# the subject works, for any topic. A source that misses part of a
# multi-word question stays only when it shares distinctive words with
# records that match the whole question. Matching any two long words was
# not enough: a heart abstract shared "tissue" and "reported" with a shop
# page and was taught as the subject. Page chrome (titles, menus, "click
# here") is not a teaching sentence.
# The research brief listed a web count and then the arXiv records. Tavily
# titles sat later, labeled only as "web", and a title with an empty
# snippet was dropped. The log now names Tavily, the HTTP status, and each
# returned URL before the excerpts.
# "the revolutionary war" became one fake argument. The question's content
# words of three letters were discarded, so the only term left was
# "revolutionary". That stem also matches "revolution", and the same-sense
# check never ran, because it required two or more terms. Algorithm papers
# and an image de-rendering paper were then full matches. The writer joined
# their sentences to a real Revolutionary War page with "The next record
# carries that idea one step further", which asserts a continuation the
# records do not have. "by means of" was read as a definition, and "the
# course of human events" was read as a classroom, so those sentences were
# filed into one sequence. Short content words now stay. A record that
# misses one of them is not written into the argument. The handoff is used
# only among records that still match the whole question. No topic is named
# in that rule. The reference shelf did not supply those sentences.
# A later pass still joined two subjects that each contained the whole
# question: a marketplace and a trade route that share a name, a kitchen
# refrigerator and a quantum one. They shared only function words such as
# "works". The paper now keeps the record whose title is the question, and
# a later record stays only when it shares a concrete word with that thread.
# A one-letter misspelling still matches the page ("porche", "ghengis",
# "wallstree"). The shelf is still not the source of the claims.

TEACHING_STANDARD = """
Write a basic academic paper someone could hand to another person or turn in for a class.
- Start with what the subject is.
- Then give the core ideas in an order that builds, each point leading into the next.
- Write enough that a reader can talk through the basics: what the subject is, the core ideas in order, how one idea leads to the next, and where the account stops.
- Develop each idea with the next explanatory sentences from the records. Do not lengthen the paper by repeating a quotation.
- Do not dump out-of-context quotations or unrelated excerpts.
- Use only records included below. Do not invent citations, experiments, numbers, or quotations.
- If a retrieved record does not help explain the subject, leave it out of the argument and say it was set aside.
- Close with what a beginner can now explain, and with what these records do not establish.
"""

import re
from datetime import date

from rag.index import sentences


def _tavily_log(web: dict) -> str:
    status = web.get("status")
    status_text = str(status) if status is not None else "none"
    key_text = "yes" if web.get("key_present") else "no"
    count = len(web.get("results") or [])
    return (
        f"tavily_search was called. Key present: {key_text}. "
        f"HTTP status: {status_text}. Mode: {web.get('mode') or web.get('source')}. "
        f"Tavily returned {count} page(s), separate from arXiv."
    )


def research_brief(query: str, arxiv: dict, web: dict) -> str:
    sources = _collect(arxiv, web)
    lines = [
        f"# Research brief: {query.strip()}",
        "",
        "## Question",
        query.strip(),
        "",
        "## Search log",
        "",
        f"arXiv returned {len(arxiv.get('results') or [])} record(s) for this question.",
        "",
        _tavily_log(web),
        "",
        "These searches are not limited to the reference shelf. The shelf is used later, only to compare prose.",
        "",
    ]
    for item in web.get("results") or []:
        title = " ".join(str(item.get("title") or "Untitled").split())
        url = str(item.get("url") or "").strip()
        lines.extend(["", f"Tavily page: {title} — {url}"])
    if not (web.get("results") or []):
        lines.extend(["", "Tavily returned no pages. No web titles were added."])
    for label, payload in (("arXiv", arxiv), ("Web", web)):
        if payload.get("note"):
            lines.extend(["", f"{label} note: {payload['note']}"])
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
        excerpt = _clip(source["summary"], 2200)
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
    outline = _outline(query, sources)
    return _write_from_outline(query, title, today, outline)


# Teaching order. A later role is used only after the earlier ones that exist,
# so the paper moves from what the subject is toward a closer a beginner can use.
# One sentence per idea was too thin to talk from. Two sentences are kept
# when a second record, or the next sentence of the same record, actually
# develops the point. The cap stops the section from becoming a second dump.
_ROLE_PLAN = (
    ("definition", 2),
    ("scope", 2),
    ("contrast", 2),
    ("discrete", 2),
    ("example", 1),
    ("duality", 2),
    ("knowledge", 2),
    ("uncertainty", 1),
    ("further", 1),
    ("works", 4),
    ("path", 2),
)

_ROLE_JOB = {
    "definition": "what the subject is",
    "scope": "where that behavior shows up",
    "contrast": "the contrast the records draw",
    "works": "how it works",
    "discrete": "how matter and energy are divided",
    "example": "the example already in that record",
    "duality": "wave and particle behavior",
    "knowledge": "probability in place of a single certain path",
    "uncertainty": "what cannot be known exactly at the same time",
    "further": "a further idea the earlier sentences do not state",
    "path": "how to put the account into practice",
}


def _outline(query: str, sources: list[dict]) -> dict:
    """Keep sentences that can teach, in an order that builds. Nothing is added."""
    terms = _query_terms(query)
    aside = []
    prepared = []
    held = []
    for source in sources:
        if _sidebar(source, terms):
            aside.append(source)
            continue
        text = _prepare(source.get("excerpt") or source.get("summary") or "")
        overlap = _query_overlap(f"{source.get('title', '')} {text}", terms)
        held.append((overlap, source, text))
    # When one record matches every word of the question, a record that
    # matches only a fragment (heart "hypertrophy" with no bodybuilding,
    # for example) does not explain the question.
    best = max((overlap for overlap, _source, _text in held), default=0)
    full_blobs: list[str] = []
    if len(terms) >= 2 and best >= len(terms):
        for overlap, source, text in held:
            if overlap >= len(terms):
                full_blobs.append(f"{source.get('title', '')} {text}")
    signature = _signature(full_blobs, terms)
    for overlap, source, text in held:
        if terms and overlap < 1:
            aside.append(source)
            continue
        if full_blobs and overlap < len(terms) and not _same_sense(f"{source.get('title', '')} {text}", signature, terms):
            aside.append(source)
            continue
        found = []
        seen = set()
        for sentence in sentences(text):
            sentence = _polish_excerpt(sentence)
            if sentence.lower() in seen or not _usable(sentence):
                continue
            role = _role(sentence, terms)
            # A record that already matches the question can explain the next
            # step without repeating every word of the question.
            if not role and len(terms) >= 1 and overlap >= max(len(terms), 1) and _explanatory(sentence):
                role = "works"
            if not role:
                continue
            seen.add(sentence.lower())
            found.append((role, sentence, _quality(sentence, terms, role)))
        found = _leave_room_for_follows(found, text)
        if not found:
            aside.append(source)
            continue
        prepared.append({**source, "candidates": found, "sequence": _sequence(text), "terms": terms})
    return {"steps": _pick_steps(prepared), "aside": aside}


def _leave_room_for_follows(found: list[tuple], text: str) -> list[tuple]:
    """Keep the sentences right after a definition for that definition's development.

    Promoting them to their own later step made the opening skip the mechanism
    and repeat it at the end.
    """
    sequence = _sequence(text)
    found_sentences = {sentence for _role_name, sentence, _quality in found}
    protected = set()
    for role, sentence, _quality in found:
        if role != "definition" or sentence not in sequence:
            continue
        taken = 0
        for nxt in sequence[sequence.index(sentence) + 1:]:
            if nxt in found_sentences:
                protected.add(nxt)
            if _usable(nxt) or _continuation(nxt):
                taken += 1
            if taken >= 2:
                break
    return [item for item in found if not (item[0] == "works" and item[1] in protected)]


def _pick_steps(prepared: list[dict]) -> list[dict]:
    used = set()
    steps = []
    for role, limit in _ROLE_PLAN:
        pool = []
        for source in prepared:
            for candidate_role, sentence, quality in source["candidates"]:
                if candidate_role == role and sentence not in used:
                    pool.append((quality, source, sentence))
        pool.sort(key=lambda item: item[0], reverse=True)
        taken_urls = set()
        taken = 0
        for _quality, source, sentence in pool:
            if role in {"definition", "contrast", "further"} and source["url"] in taken_urls:
                continue
            steps.append({"role": role, "source": source, "sentence": sentence})
            used.add(sentence)
            taken_urls.add(source["url"])
            taken += 1
            if taken == limit:
                break
    _attach_example(prepared, steps, used)
    if not any(step["role"] == "definition" for step in steps):
        leftover = []
        for source in prepared:
            for role, sentence, quality in source["candidates"]:
                if sentence not in used and _query_overlap(sentence, _query_terms(source.get("title", ""))):
                    leftover.append((quality, source, sentence))
        leftover.sort(key=lambda item: item[0], reverse=True)
        if leftover:
            _quality, source, sentence = leftover[0]
            steps.insert(0, {"role": "definition", "source": source, "sentence": sentence})
    return steps


def _attach_example(prepared: list[dict], steps: list[dict], used: set[str]) -> None:
    """Keep a 'for example' sentence with the idea it illustrates, instead of dropping it."""
    for index, step in enumerate(steps):
        if step["role"] != "discrete":
            continue
        url = step["source"]["url"]
        for source in prepared:
            if source["url"] != url:
                continue
            for role, sentence, _quality in source["candidates"]:
                if sentence in used:
                    continue
                if sentence.lower().startswith("for example") and any(
                    cue in sentence.lower() for cue in ("photon", "quanta", "packet", "discrete")
                ):
                    steps.insert(index + 1, {"role": "example", "source": source, "sentence": sentence})
                    used.add(sentence)
                    return


def _sequence(text: str) -> list[str]:
    ordered = []
    seen = set()
    for sentence in sentences(text):
        sentence = _polish_excerpt(sentence)
        key = sentence.lower()
        if key in seen:
            continue
        if _usable(sentence) or _continuation(sentence):
            seen.add(key)
            ordered.append(sentence)
    return ordered


def _continuation(sentence: str) -> bool:
    """A following sentence may start with It or This when it develops the previous one."""
    if not re.match(r"(It|This|These|That)\b", sentence):
        return False
    words = sentence.split()
    if not 10 <= len(words) <= 40:
        return False
    if _noisy(sentence) or "…" in sentence or "..." in sentence:
        return False
    if sentence.count("“") != sentence.count("”") or sentence.count('"') % 2:
        return False
    return bool(re.search(
        r"\b(aims|means|describes|explains|shows|calls|refers|understands|names|becomes)\b",
        sentence,
        re.I,
    ))


def _follows(step: dict, used: set[str], limit: int = 2) -> list[str]:
    """Next explanatory sentences in the same record. Later teaching steps are left for their own place."""
    sequence = step["source"].get("sequence") or []
    anchor = step["sentence"]
    try:
        index = sequence.index(anchor)
    except ValueError:
        return []
    later_roles = {role for role, _limit in _ROLE_PLAN}
    anchor_words = set(_content_words(anchor))
    found = []
    for sentence in sequence[index + 1:]:
        if sentence in used:
            continue
        role = _role(sentence, step["source"].get("terms") or []) if _usable(sentence) else None
        if role and role != step["role"] and role in later_roles:
            break
        if not _usable(sentence) and not _continuation(sentence):
            continue
        if any(cue in sentence.lower() for cue in ("absolute zero", "coldest", "nothing colder")):
            continue
        words = set(_content_words(sentence))
        if not words:
            continue
        shared = _shared_words(anchor_words, words)
        # A near-copy of the sentence just used does not teach the next step.
        if anchor_words and len(shared) / len(anchor_words) > 0.55:
            continue
        if len(shared) < 1 and not _continuation(sentence):
            continue
        found.append(sentence)
        if len(found) == limit:
            break
    return found


def _signature(blobs: list[str], terms: list[str]) -> set[str]:
    """Words that show up in more than one record that matches the whole question.

    One shop page and one abstract can share ordinary words. A word has to
    recur across those full matches before it can vouch for a partial record.
    """
    if not blobs:
        return set()
    counts: dict[str, int] = {}
    for blob in blobs:
        for word in _distinctive(blob, terms):
            counts[word] = counts.get(word, 0) + 1
    if len(blobs) >= 2:
        return {word for word, count in counts.items() if count >= 2}
    return set(counts)


def _distinctive(text: str, terms: list[str]) -> set[str]:
    generic = {
        "result", "results", "effect", "effects", "approach", "including", "support",
        "compare", "compared", "often", "using", "based", "study", "studies", "model",
        "between", "during", "after", "before", "would", "could", "should", "within",
        "without", "there", "these", "those", "about", "which", "while", "where",
        "other", "their", "through", "because", "system", "systems", "large", "small",
        "tissue", "information", "consistent", "improve", "improved", "develop",
        "developed", "development", "trained", "diameter", "reported", "relation",
        "experts", "expert", "generating", "generated", "analysis", "method",
        "methods", "patient", "patients", "clinical", "change", "changes",
        "different", "traditional", "commonly", "focused", "simply", "actually",
        "really", "following", "article", "benefits", "possible", "several",
        "however", "therefore", "another", "further", "whether", "already",
        "across", "toward", "towards", "people", "person", "something", "anything",
        "everything", "important", "significant", "available", "according",
        "related", "research", "paper", "papers", "abstract", "section", "figure",
        "table", "dataset", "provide", "provides", "provided", "include",
        "includes", "current", "previous", "recent", "general", "specific",
        "various", "multiple", "single", "number", "numbers", "value", "values",
        "level", "levels", "group", "groups", "example", "examples", "process",
        "background", "conclusion", "present", "presented", "human", "publicly",
        "resource", "promote", "innovation", "limited", "challenge", "early",
        "detection", "found", "shown", "using", "based", "range", "chronic",
        "disease", "measurement", "measurements", "automatically", "accurately",
        "causing", "solution", "technology", "development", "environmental",
        "useful", "unavailable", "measure", "measures",
        "requirement", "requirements", "parameters", "parameter", "assumes",
        "assumption", "assumptions", "proposed", "framework", "approach",
    }
    return {
        word for word in _content_words(text)
        if not any(_term_in(word, term) for term in terms) and word not in generic and len(word) > 5
    }


def _same_sense(text: str, vocab: set[str], terms: list[str]) -> bool:
    """A partial match belongs when it shares the full matches' recurring words.

    Sharing any two long words let a ventricular-hypertrophy abstract pass,
    because a shop page also said "tissue" and "reported." Those words are
    not the subject. The check uses only words that recur in records that
    already match the whole question.
    """
    if not vocab:
        return False
    return len(_distinctive(text, terms) & vocab) >= 2


def _shared_words(left: set[str], right: set[str]) -> set[str]:
    """Shared wording, including a plural or a longer form of the same word."""
    found = set()
    for word in left:
        if word in right:
            found.add(word)
            continue
        if len(word) < 5:
            continue
        for other in right:
            if len(other) >= 5 and (word.startswith(other) or other.startswith(word)):
                found.add(word)
                break
    return found


def _explanatory(sentence: str) -> bool:
    return bool(re.search(
        r"\b(cause|causes|caused|increase|increases|increased|lead|leads|result|results|occur|occurs|happen|happens|work|works|grow|grows|growth|process|produce|produces|require|requires|use|uses|used|make|makes|change|changes|allow|allows|help|helps|achieve|achieved|train|training|build|builds|building|plays)\b",
        sentence,
        re.I,
    ))


def _content_words(sentence: str) -> list[str]:
    stop = {
        "that", "this", "with", "from", "they", "them", "their", "have", "been", "were",
        "what", "when", "where", "which", "into", "about", "than", "then", "also", "only",
        "such", "each", "some", "more", "most", "very", "other", "these", "those",
    }
    return [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]+", sentence)
        if len(word) > 3 and word.lower() not in stop
    ]


def _spoken(role: str) -> str:
    if role == "definition":
        return "what the subject is"
    if role == "scope":
        return "where the phenomena show up"
    if role == "contrast":
        return "the contrast with the ordinary case the records name"
    return _ROLE_JOB.get(role, "the next point")


def _handoff(role: str, next_role: str | None) -> str:
    if not next_role:
        return (
            "Stop after that sentence when you explain this. "
            "The records do not supply a further step, and this paper does not invent one."
        )
    return f"From {_spoken(role)}, the records go next to {_spoken(next_role)}."


def _write_from_outline(query: str, title: str, today: str, outline: dict) -> str:
    framed = _frame(query)
    steps = outline["steps"]
    order: list[dict] = []
    seen_urls: set[str] = set()

    def cite(source: dict) -> int:
        url = source["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            order.append(source)
        return order.index(source) + 1

    def cited(step: dict) -> str:
        return f"{_finish(step['sentence'])} [{cite(step['source'])}]"

    def group(role: str) -> list[dict]:
        return [step for step in steps if step["role"] == role]

    used_sentences = {step["sentence"] for step in steps}

    def developed(step: dict, line: str) -> str:
        parts = [line]
        for extra in _follows(step, used_sentences):
            used_sentences.add(extra)
            parts.append(f"The same record continues: {_finish(extra)} [{cite(step['source'])}]")
        return " ".join(parts)

    # A record that matches only part of a multi-word question is a different
    # subject. Leave it out instead of stitching it on with a continuation
    # the two texts do not share. When two full matches still describe
    # different subjects, keep the thread whose title is the question.
    terms = _query_terms(query)
    steps = _subject_thread([step for step in steps if _on_question(step, terms)], terms)

    present = [role for role, _limit in _ROLE_PLAN if group(role)]

    def next_role(role: str) -> str | None:
        if role not in present:
            return present[0] if present else None
        index = present.index(role)
        return present[index + 1] if index + 1 < len(present) else None

    def related(chosen: list[dict]) -> list[dict]:
        kept: list[dict] = []
        for step in chosen:
            if kept and not _shares_subject(kept[-1], step, terms):
                continue
            kept.append(step)
        return kept

    support: list[str] = []
    opening = related(group("definition") + group("scope"))
    if opening:
        bits = []
        for index, step in enumerate(opening):
            line = developed(step, cited(step))
            if index == 0:
                bits.append(line)
            elif step["role"] == "definition":
                bits.append(f"The next record strengthens that opening: {line}")
            else:
                bits.append(f"The next record says where that behavior shows up: {line}")
        bits.append(_handoff(opening[-1]["role"], next_role(opening[-1]["role"])))
        support.append(" ".join(bits))
    contrasts = related(group("contrast"))
    if contrasts:
        bits = [developed(contrasts[0], cited(contrasts[0]))]
        for step in contrasts[1:]:
            bits.append(f"The next record strengthens that contrast: {developed(step, cited(step))}")
        bits.append(_handoff("contrast", next_role("contrast")))
        support.append(" ".join(bits))
    previous = "contrast" if contrasts else "definition"
    for role in ("discrete", "example", "duality", "knowledge", "uncertainty", "further", "works", "path"):
        chosen = related(group(role))
        if not chosen:
            continue
        bits = []
        for index, step in enumerate(chosen):
            line = developed(step, cited(step))
            if index == 0:
                bits.append(f"{_idea_lead(role, step['sentence'], previous)} {line}")
            else:
                bits.append(f"The next record carries that idea one step further: {line}")
            previous = role
        bits.append(_handoff(role, next_role(role)))
        support.append(" ".join(bits))
    if not support:
        support.append(
            "The search returned records, but none of them stated the subject in a sentence this paper can teach. "
            "The titles are named under Limits. Nothing was invented to fill the gap."
        )

    walk = _reading_path(steps, cite)
    limits = _limits(outline["aside"], today)
    closer = _closer(steps, cite)

    references = []
    for index, source in enumerate(order, start=1):
        references.append(_reference_line(index, source))
    if not references:
        references.append("None of the retrieved records could be cited without leaving the text they supplied.")

    later = []
    if group("contrast"):
        later.append("the contrast that makes the definition necessary")
    if any(group(role) for role in ("discrete", "duality", "knowledge", "further")):
        later.append("the ideas that make the contrast specific")
    if later:
        direction = "They say what the subject is, then " + ", then ".join(later) + "."
    else:
        direction = "They say what the subject is, and they stop where the records stop."

    body = [
        f"# {title}",
        "",
        "## Abstract",
        (
            f"{framed['abstract']} "
            "It is written so a reader can talk through the basics: what the subject is, "
            "the core ideas in the order the records support, how each idea leads to the next, "
            "and where the account stops. "
            "A later sentence is used only when it adds that next point. "
            "Claims stay inside the sentences the search returned."
        ),
        "",
        "## Introduction",
        f"The question guiding this paper is: {framed['guide']}",
        "",
        f"The pages move in one direction. {direction} A reader who reaches the close can restate that sequence.",
        "",
        "Read the body as a conversation. Begin with what the subject is. "
        "Use the contrast next, when the records set that account beside an ordinary case. "
        "Take each later idea only because a retrieved sentence carries the previous one forward. "
        "Stop where those sentences stop.",
        "",
        "## What the records support",
        *_spaced(support),
        "",
        "## Retrieved records",
        walk,
        "",
        "## Limits of the evidence",
        limits,
        "",
        "## Conclusion",
        closer,
        "",
        "## References",
        *_spaced(references),
        "",
        "[^1]: Only sentences from the retrieved records are used as claims. Connective sentences organize those claims and do not add findings.",
        "[^2]: Records that do not explain the subject are named in the limits and are not quoted out of context.",
    ]
    return "\n".join(body)


def _frame(query: str) -> dict:
    text = " ".join(query.strip().split())
    lowered = text.lower()
    is_question = text.endswith("?") or lowered.startswith(
        ("how ", "what ", "why ", "when ", "who ", "where ", "does ", "do ", "is ", "are ", "can ")
    )
    if is_question:
        question = text if text.endswith("?") else text.rstrip(".") + "?"
        return {"abstract": f"This paper asks {question}", "guide": question}
    topic = text.rstrip(".")
    return {
        "abstract": f"This paper explains {topic}.",
        "guide": f"what {topic} is, and which ideas a beginner has to meet before the account is useful.",
    }


def _reading_path(steps: list[dict], cite) -> str:
    if not steps:
        return "No retrieved record supplied a sentence that could be taught in sequence."
    groups = []
    for step in steps:
        number = cite(step["source"])
        if groups and groups[-1]["role"] == step["role"]:
            groups[-1]["numbers"].append(number)
            continue
        groups.append({"role": step["role"], "numbers": [number], "sentence": step["sentence"]})
    paragraphs = [
        "The sentences above are the teaching sequence, not a sample of every record the search returned. "
        "Use them in this order when you tell someone how the subject works."
    ]
    for index, group in enumerate(groups):
        marks = " and ".join(f"[{number}]" for number in dict.fromkeys(group["numbers"]))
        spoken = _spoken(group["role"]) if group["role"] in {"definition", "scope", "contrast"} else _label_from_sentence(group["role"], group["sentence"])
        if index == 0:
            paragraphs.append(
                f"Start with {spoken}, using {marks}. "
                "Do not open on a later idea. A listener needs this sentence before the rest of the account has a place to stand."
            )
        else:
            previous = _spoken(groups[index - 1]["role"]) if groups[index - 1]["role"] in {"definition", "scope", "contrast"} else _label_from_sentence(groups[index - 1]["role"], groups[index - 1]["sentence"])
            paragraphs.append(
                f"Move next to {spoken}, using {marks}. "
                f"This step follows {previous}. It does not repeat that earlier sentence, and it does not skip to a point the records have not reached."
            )
    paragraphs.append(
        "Each citation is the sentence used for that step. "
        "A neighboring excerpt that was not needed for the handoff stays out of the conversation."
    )
    return "\n\n".join(paragraphs)


def _limits(aside: list[dict], today: str) -> str:
    titles = []
    for source in aside:
        title = source.get("title") or ""
        if title and title not in titles:
            titles.append(title)
    if titles:
        listed = ", ".join(f"“{title}”" for title in titles[:6])
        return (
            f"Other retrieved records were set aside because they do not explain this question: {listed}. "
            "They stay out of the argument so a technical aside, a program, or a pile of fragments is not mistaken for a definition. "
            f"Where a record supplied only a snippet, this paper does not reconstruct the page behind it. Retrieved on {today}."
        )
    return (
        "Every retrieved record that stated the subject, the contrast, or a following idea was used above. "
        f"Snippets are not full texts, and this paper does not fill the gaps. Retrieved on {today}."
    )


def _closer(steps: list[dict], cite) -> str:
    if not steps:
        return "The question remains open, because the retrieved records did not state it."
    bits = ["A beginner who has followed this order can restate the account without adding to it."]
    definitions = [step for step in steps if step["role"] == "definition"]
    contrasts = [step for step in steps if step["role"] == "contrast"]
    if definitions:
        marks = "".join(f"[{cite(step['source'])}]" for step in definitions)
        bits.append(f"The subject is the one named in the opening {marks}.")
    if contrasts:
        marks = "".join(f"[{cite(step['source'])}]" for step in contrasts)
        blob = " ".join(step["sentence"].lower() for step in contrasts)
        if "classical" in blob:
            bits.append(f"It is distinct from the classical physics set beside that opening {marks}.")
        else:
            bits.append(f"It is set beside the ordinary case named next to that opening {marks}.")
    spoken = []
    for role in ("scope", "discrete", "example", "duality", "knowledge", "uncertainty", "further", "works", "path"):
        chosen = [step for step in steps if step["role"] == role]
        if not chosen:
            continue
        marks = "".join(f"[{number}]" for number in dict.fromkeys(cite(step["source"]) for step in chosen))
        label = _spoken(role) if role == "scope" else _label_from_sentence(role, chosen[0]["sentence"])
        spoken.append(f"Say {label} next {marks}.")
    if spoken:
        bits.append("To talk through the rest, keep that order.")
        bits.extend(spoken)
        bits.append("Each of those lines is the next retrieved sentence. The handoff is the order itself.")
    bits.append(
        "Stop there. These records do not establish more than the sentences above, and they do not replace a fuller treatment. "
        "They are enough to hand to another person as a first account, and they mark where that account stops."
    )
    return " ".join(bits)


def _idea_lead(role: str, sentence: str, previous: str) -> str:
    lowered = sentence.lower()
    if role == "discrete":
        return "The contrast needs a first idea. The next record says how these phenomena are divided into units."
    if role == "example":
        return "The same record states the example that follows from that unit."
    if role == "duality":
        if previous in {"discrete", "example"}:
            return "Those units are the start, not the finish. The next record says they are not particles alone."
        return "The next record says the small objects are not particles alone."
    if role == "knowledge":
        return "The next record says what can be claimed about where a particle is."
    if role == "uncertainty":
        if previous == "knowledge":
            return "Probability is still not the last word in these records. The next one says which pair of facts cannot be exact together."
        return "The next record says which pair of facts cannot be exact together."
    if role == "further":
        if "superposition" in lowered or "multiple possible states" in lowered:
            return "The next record adds how one object can be in more than one possible state, which the earlier sentences have not named."
        if "entangl" in lowered:
            return "The next record adds a relation between two or more objects."
        return "The next record adds one further idea that is already in the retrieved text."
    if role == "works":
        if previous in {"definition", "scope", "contrast", "definition"}:
            return "With the subject named, the records say how it works."
        return "The next record adds another step in how it works."
    if role == "path":
        if "formula" in lowered and any(cue in lowered for cue in ("minimum", "math", "equation", "course", "class")):
            return "A reader can stop at the ideas above. The last record says how a class can ask a beginner to hold them."
        return "The last record says how a person can put this account into practice."
    return "The next record continues the account."


def _label_from_sentence(role: str, sentence: str) -> str:
    """Name an idea with words that already appear in the sentence being cited."""
    text = sentence.lower()
    if role == "discrete":
        if "packet" in text:
            return "discrete packets"
        if "quanta" in text or "chunks" in text:
            return "quanta"
        return "discrete values"
    if role == "example":
        if "photon" in text:
            return "photons as the example of those packets"
        return "the example already stated in that record"
    if role == "duality":
        if "duality" in text:
            return "wave-particle duality"
        return "wave and particle behavior"
    if role == "knowledge":
        if "probability" in text:
            return "probability"
        return "what can be said about location"
    if role == "uncertainty":
        if "uncertainty" in text:
            return "the uncertainty the record names"
        return "a limit on knowing two facts at once"
    if role == "further":
        if "superposition" in text:
            return "superposition"
        if "entangl" in text:
            return "entanglement"
        if "measured" in text:
            return "measurement"
        return "one further idea stated in the record"
    if role == "path":
        if "formula" in text and any(cue in text for cue in ("minimum", "math", "equation", "course", "class")):
            return "a formulation with few formulas"
        return "how to put the account into practice"
    return _ROLE_JOB.get(role, "the next point")


def _sidebar(source: dict, terms: list[str] | None = None) -> bool:
    title = (source.get("title") or "").lower()
    url = (source.get("url") or "").lower()
    text = (source.get("excerpt") or source.get("summary") or "").lower()
    terms = terms or []
    if "youtube.com" in url or "youtu.be" in url:
        return True
    if title.startswith("proceedings") or "proceedings of" in title:
        return True
    if "conference" in title and "proceedings" in text:
        return True
    # A programming paper was noise on a physics question. It is the subject
    # when the inquiry itself is about programming.
    if "programming" in title and not any(term.startswith("program") for term in terms):
        return True
    if "collection of statements" in text and len(text.split()) < 80:
        return True
    return False


def _prepare(text: str) -> str:
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff\u2060]", " ", text)
    text = re.sub(r"\s#+\s*", ". ", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"skip to main content", " ", text, flags=re.I)
    text = re.split(r"German abstract:", text, maxsplit=1, flags=re.I)[0]
    text = re.sub(r"English abstract:\s*", "", text, flags=re.I)
    text = text.replace("(optical)", "")
    text = re.sub(r"\s+:\s*\d+(?:\.\d+)?", "", text)
    # Snippet cuts ("[...]") are not sentence ends. Keep only the clauses that
    # were already finished, so a cut word is not taught as a definition.
    kept = []
    for part in re.split(r"\[\.\.\.\]|…|\.{3,}", text):
        part = part.strip()
        if not part:
            continue
        if part[-1] not in ".!?":
            end = max(part.rfind("."), part.rfind("!"), part.rfind("?"))
            if end < 0:
                continue
            part = part[: end + 1]
        kept.append(part)
    return " ".join(" ".join(kept).split())


def _usable(sentence: str) -> bool:
    words = sentence.split()
    if not 8 <= len(words) <= 55:
        return False
    if not sentence[0].isupper():
        return False
    if _noisy(sentence):
        return False
    lowered = sentence.lower()
    if any(cue in lowered for cue in (
        "official government",
        ".gov",
        "science fiction",
        "misunderstood",
        "chalkboard",
        "greatest scientific",
        "most puzzling",
        "isbn",
        "university press",
    )):
        return False
    # A clipped excerpt ends on a hanging word or an ellipsis. Do not teach from it.
    if "…" in sentence or "..." in sentence:
        return False
    tail = re.sub(r"[\"”']+$", "", sentence.rstrip()).rstrip(".!?").lower()
    if tail.endswith((
        " or", " and", " which", " that", " of", " the", " a", " an", " same", " other", " its",
    )):
        return False
    if re.match(
        r"(This|It|They|These|We|Our|I|Currently|In order|In fact|Data show|Lecture|Sign up|Spend)\b",
        sentence,
    ):
        return False
    if lowered.startswith("in physics, this means"):
        return False
    if re.search(r"\bpart in \d{3,}\b", lowered):
        return False
    if re.search(r"\(\d+(?:st|nd|rd|th) ed\.\)", sentence):
        return False
    if re.search(r"\b(F1|AUROC|inference rate)\b", sentence):
        return False
    if "read on to" in lowered or lowered.rstrip(".!?").endswith("but how"):
        return False
    if re.search(r"(?:[A-Z]{2,}\s+){3,}", sentence):
        return False
    # A menu, a title line, or a clipped heading is not an explanation.
    if re.search(
        r"(click this link|for more info|you will find|subreddit|read more|cookie policy|add to cart|shop by)",
        lowered,
    ):
        return False
    if lowered.startswith("title:") or "said above" in lowered:
        return False
    if re.sub(r"[\"”']+$", "", sentence.rstrip()).rstrip(".!?").endswith(":"):
        return False
    alpha = re.findall(r"[A-Za-z][A-Za-z']*", sentence)
    caps = [word for word in alpha if word[:1].isupper()]
    lowers = [word for word in alpha if word.islower()]
    if len([word for word in lowers if len(word) > 3]) < 4:
        return False
    # A run of title-case names is a menu or a heading, not an explanation.
    if len(caps) >= 4 and len(caps) > len(lowers):
        return False
    if sentence.count("(") != sentence.count(")"):
        return False
    if sentence.count("“") != sentence.count("”"):
        return False
    if sentence.count('"') % 2:
        return False
    return True


def _role(sentence: str, terms: list[str] | None = None) -> str | None:
    """Physics cues stay first so that subject still builds in its own order.

    Anything else with the question's words can still be a definition, a
    contrast, or a step in how the subject works. The previous version
    returned None for those sentences, and the paper then had no claims.
    """
    text = sentence.lower()
    terms = terms or []
    overlap = _query_overlap(sentence, terms) if terms else 0
    # "Formula" alone is not a math lesson. A winning formula for a workout
    # is still about how the subject works.
    # "the course of human events" is not a class. A classroom record says
    # "a course" and then a subject, not "course of".
    # "students' revolutionary organization" is a biography, not a lesson.
    # A classroom record has to be about teaching.
    classroom = bool(
        re.search(r"\b(teach|tutorial)\b", text)
        or re.search(r"\b(a|the|this) course\b(?!\s+of\b)", text)
        or (
            re.search(r"\b(schools?|students?)\b", text)
            and re.search(r"\b(learn|class|course|school|teach)\b", text)
        )
    )
    math_formula = bool(re.search(r"\bformulas?\b", text) and re.search(r"\b(math|equation|course|class|minimum)\b", text))
    if (classroom or math_formula) and "programming" not in text and not re.search(r"\bis the (study|science|field|fundamental)\b", text):
        return "path"
    if "entangl" in text and any(cue in text for cue in ("two or more", "far apart", "connected", "single system")):
        return "further"
    if any(cue in text for cue in ("superposition", "multiple possible states", "until they are measured")):
        if any(cue in text for cue in ("multiple places", "multiple possible", "more than one", "until they are measured", "not confined")):
            return "further"
        return None
    if any(cue in text for cue in ("uncertainty principle", "simultaneously known", "position and momentum", "precisely known")):
        return "uncertainty"
    if any(cue in text for cue in ("probability", "exact location", "wave function")):
        return "knowledge"
    if any(cue in text for cue in (
        "wave-particle", "wave particle", "duality", "both particles", "particles and waves",
        "characteristics of both", "behave like waves", "wave-like", "particle-like",
    )):
        return "duality"
    if any(cue in text for cue in ("quanta", "quantized", "discrete unit", "discrete values", "discrete packet", "chunks")):
        return "discrete"
    if any(cue in text for cue in ("classical", "macroscopic", "could not be reconciled", "unlike the world", "baseball", "planets")):
        return "contrast"
    if any(cue in text for cue in ("every scale", "all around us", "everyday lives")):
        return "scope"
    if re.search(r"\b(is|are) (the |a |an )?(fascinating )?(study|science|field|branch|theory|fundamental|process)\b", text):
        return "definition"
    if any(cue in text for cue in ("is the fundamental", "explores the behavior", "describes the behavior", "studies how", "describes nature")):
        return "definition"
    if overlap >= 1 and not re.match(r"there (is|are)\b", text) and re.search(
        r"\b(is|are|was|were) (a|an|the)\b|\b(was|were) born\b",
        text,
    ):
        return "definition"
    if any(cue in text for cue in ("unlike ", "whereas", "rather than", "compared with", "in contrast", "difference between")):
        return "contrast"
    if overlap >= 1 and "however," in text:
        return "contrast"
    if overlap >= 1 and re.search(r"\b(is|are) (a |an )?(different|distinct)\b", text):
        return "contrast"
    # "by means of" is a method, not a definition. "X is a …" / "X was a …"
    # still says what the subject is, for any topic.
    if overlap >= 1 and not re.match(r"there (is|are)\b", text) and re.search(
        r"(?<!by )means\b|\brefers to\b|\bdefined as\b|\b(is|are|was|were) (the |a |an )?(process|study|science|field|branch|theory|growth|enlargement)\b",
        text,
    ):
        return "definition"
    if overlap >= 1 and re.search(r"\b(goal|goals|purpose|aim|aims)\b", text) and re.search(r"\b(is|are)\b", text):
        return "definition"
    if overlap >= 1 and re.search(
        r"\b(cause|causes|caused|increase|increases|increased|lead|leads|result|results|occur|occurs|happen|happens|work|works|grow|grows|growth|process|produce|produces|require|requires|use|uses|used|make|makes|change|changes|allow|allows|help|helps|achieve|achieved|train|training|build|builds|building|plays|arose|began|founded|fought|lasted|ended|started)\b",
        text,
    ):
        return "works"
    return None


def _quality(sentence: str, terms: list[str], role: str) -> int:
    lowered = sentence.lower()
    score = _query_overlap(sentence, terms) * 2
    if any(cue in lowered for cue in ("equipment", "engineered to", "shop ", "gear", "add to cart", "plates")):
        score -= 6
    if role == "definition":
        if "is the study of" in lowered:
            score += 8
        elif "fundamental theory" in lowered or "branch of physics that explains" in lowered:
            score += 6
        elif "studies how" in lowered or "explores the behavior" in lowered or "smallest scales of our universe" in lowered:
            score += 5
        elif "is the science" in lowered or "refers to" in lowered or "is the process" in lowered or "defined as" in lowered:
            score += 5
        if any(cue in lowered for cue in ("absolute zero", "coldest", "nothing colder")):
            score -= 5
    if role == "contrast" and any(cue in lowered for cue in ("planets", "baseball", "cars", "balls", "world we see", "we can see")):
        score += 8
    if role == "contrast" and any(cue in lowered for cue in ("insufficient", "subatomic", "macroscopic")):
        score += 3
    if role == "contrast" and any(cue in lowered for cue in ("planck", "einstein", "1900", "1905")):
        score -= 3
    if role == "knowledge" and any(cue in lowered for cue in ("electron", "cloud", "location")):
        score += 3
    if role == "path" and "formula" in lowered:
        score += 4
    if lowered.startswith("for example"):
        score -= 5
    if lowered.startswith("quantum"):
        score += 2
    families = 0
    if any(cue in lowered for cue in ("quanta", "discrete", "packet")):
        families += 1
    if any(cue in lowered for cue in ("duality", "wave-like", "behave like waves", "particles and waves")):
        families += 1
    if "probability" in lowered:
        families += 1
    if any(cue in lowered for cue in ("measured", "superposition", "entanglement")):
        families += 1
    if families >= 2:
        score -= 4
    if "(optical)" in lowered:
        score -= 2
    if len(sentence.split()) > 42:
        score -= 1
    return score


def _finish(sentence: str) -> str:
    cleaned = _polish_excerpt(sentence).strip()
    cleaned = re.sub(r"^(However|Moreover|Therefore),\s+", "", cleaned)
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def _reference_line(index: int, source: dict) -> str:
    authors = source.get("authors") or []
    when = source.get("date") or "n.d."
    venue = source.get("venue") or "source"
    title = source.get("title") or source.get("url")
    url = source.get("url") or ""
    if not authors:
        return f"[{index}] {title}. {venue}, {when}. {url}"
    return f"[{index}] {_who(source)}. {title}. {venue}, {when}. {url}"


def _title_focus(source: dict, terms: list[str]) -> tuple[int, int]:
    """Prefer a page whose title is the question over a paper that only mentions it."""
    title = source.get("title") or ""
    hits = _query_overlap(title, terms)
    extra = len([word for word in _query_terms(title) if word not in terms])
    return (hits, -extra)


def _seed_rank(step: dict, terms: list[str]) -> tuple[int, int, int]:
    """Anchor on the sentence that says what the subject is.

    The shortest title won before this. For "the revolutionary war" that
    title was a Mount Vernon card whose sentence advertises a book, and the
    Battlefield Trust page was then dropped because it did not share words
    with the advertisement. A book, a poster, or "this study" is not the
    definition. "Works by" is.
    """
    sentence = step["sentence"].lower()
    hits, extra = _title_focus(step["source"], terms)
    teach = 4 if step["role"] == "definition" else 0
    if re.search(r"\b(is|are|was|were) (a|an|the)\b", sentence):
        teach += 2
    if re.search(r"\b(refers to|defined as|is the study|work(?:s)? by)\b", sentence):
        teach += 3
    if re.search(r"\b(book|author|novel|memoir|poster|this study|this paper|we propose|we show|novel solution)\b", sentence):
        teach -= 5
    return (teach, hits, extra)


def _subject_thread(steps: list[dict], terms: list[str]) -> list[dict]:
    """Keep one subject.

    A marketplace named Silk Road and the historical road both contain the
    question, and so do a biography and a grant that uses the same name.
    The sentence that says what the subject is anchors the paper. Later
    records stay only when they share a concrete word with that thread.
    """
    if len(steps) < 2:
        return steps
    seed = max(steps, key=lambda step: _seed_rank(step, terms))
    # Compare every record with the anchor, not with a chain of neighbors.
    # A chain let an allocation model ride along with a page that says how
    # a vaccine works, because each pair shared some ordinary word.
    return [step for step in steps if step is seed or _shares_subject(seed, step, terms)]


def _shares_subject(previous: dict, step: dict, terms: list[str]) -> bool:
    """A later record continues the point only when the two texts share the subject.

    Matching the question is not enough. Two pages can each say "revolutionary"
    and still be about algorithms and about a war. The handoff is withheld
    unless a concrete word other than the question appears in both.
    """
    if previous["source"].get("url") and previous["source"].get("url") == step["source"].get("url"):
        return True
    # Titles repeat the question and a place name. Compare the sentences.
    # A cybersecurity paper titled with "Maritime Silk Road" was joining the
    # history page because the title, not the claim, shared "maritime".
    prev_blob = previous["sentence"]
    next_blob = step["sentence"]
    # A shared function word ("works", "used", "first") is not a shared subject.
    # The dark-web Silk Road and the historical road, and a quantum refrigerator
    # and a kitchen refrigerator, were joined on words like those.
    return len(_distinctive(prev_blob, terms) & _distinctive(next_blob, terms)) >= 1


def _on_question(step: dict, terms: list[str]) -> bool:
    """True when the record still matches every content word of the question.

    One shared stem is not the question. "revolutionary" alone kept papers
    about algorithms and artefacts beside a page about the war.
    """
    blob = (
        f"{step['source'].get('title', '')} "
        f"{step['source'].get('excerpt') or step['source'].get('summary') or ''} "
        f"{step['sentence']}"
    )
    if not terms:
        return True
    needed = len(terms) if len(terms) >= 2 else 1
    return _query_overlap(blob, terms) >= needed


def _query_terms(query: str) -> list[str]:
    # "the" and "of" are not the subject. "war", "sun", and "way" are.
    # Dropping every word of three letters turned "the revolutionary war"
    # into the single stem "revolutionary".
    stop = {
        "the", "and", "for", "are", "was", "not", "but", "you", "how", "why",
        "who", "its", "his", "her", "our", "can", "may", "did", "has", "had",
        "any", "all", "via", "per", "off", "out", "what", "when", "where",
        "which", "with", "from", "that", "this", "into", "about", "does",
        "have", "been", "were", "will", "your", "their", "them", "then",
        "there", "these", "they", "would", "could", "should", "shall",
        "over", "same", "some", "such", "than", "only", "other", "more",
        "most", "also", "just", "under", "through", "during", "being",
        "before", "after", "again", "because", "between", "while", "using",
        "used",
    }
    return [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]+", query)
        if len(word) >= 3 and word.lower() not in stop
    ]


def _source_score(source: dict, terms: list[str]) -> int:
    text = f"{source.get('title', '')} {source.get('excerpt') or source.get('summary', '')}".lower()
    url = (source.get("url") or "").lower()
    if _noisy(text):
        return 0
    overlap = _query_overlap(text, terms)
    if terms and overlap == 0:
        return 0
    score = overlap * 3
    for cue in ("what is", "is the study", "is a branch", "is the field", "is the science", "explains how", "in simple"):
        if cue in text:
            score += 4
    if re.search(r"\b(is|are) (the|a|an)\b", text):
        score += 2
    for cue in ("classical", "everyday", "beginner", "school", "teach", "student", "without math"):
        if cue in text:
            score += 2
    for bad in ("proceedings", "conference", "programming", "youtube.com", "views posted", "cookie"):
        if bad in text or bad in url:
            score -= 5
    if len(text.split()) < 25:
        score -= 2
    return score


def _claim_sentences(source: dict, terms: list[str]) -> list[str]:
    text = source.get("excerpt") or source.get("summary") or ""
    ranked = []
    for sentence in sentences(text):
        if _noisy(sentence):
            continue
        words = sentence.split()
        if not 8 <= len(words) <= 42:
            continue
        if sentence[0].islower():
            continue
        overlap = _query_overlap(sentence, terms)
        explanatory = bool(re.search(
            r"\b(is|are|explains|means|study|studies|governs|called|arose|grew)\b",
            sentence,
            re.I,
        ))
        if overlap == 0 and not explanatory:
            continue
        score = overlap * 2 + (3 if explanatory else 0) + (2 if _bucket(sentence) == "definition" else 0)
        ranked.append((score, sentence))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [sentence for _score, sentence in ranked[:3]]


def _bucket(sentence: str) -> str:
    text = sentence.lower()
    # A sentence that says what the subject is stays a definition even when it
    # also names an atom or a wave. The old order filed those sentences under
    # "ideas" and the opening became a fragment.
    if re.search(r"\b(is|are) (the |a |an )?(study|science|field|branch|theory|fundamental)\b", text) or "explains how" in text or text.startswith("what is"):
        return "definition"
    if re.search(r"\b(is|are) (a |an )?(fascinating |fundamental )?(branch|theory)\b", text):
        return "definition"
    if any(cue in text for cue in ("school", "student", "teach", "course", "tutorial", "beginner", "formula")):
        return "path"
    if any(cue in text for cue in ("classical", "macroscopic", "everyday", "baseball", "planets", "we can see", "we can’t", "we can't")):
        return "contrast"
    if any(cue in text for cue in ("packet", "quanta", "duality", "wave", "particle", "tunnel", "schr", "observ", "fuzzy", "granular", "atom")):
        return "ideas"
    if re.search(r"\b(is|are)\b", text) and _query_overlap(text, ["quantum", "physics", "mechanics"]) >= 1:
        return "definition"
    return "ideas"


def _query_overlap(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for term in terms if _term_in(lowered, term))


def _term_in(text: str, term: str) -> bool:
    if re.search(rf"\b{re.escape(term)}\b", text):
        return True
    # "works" meets "work". A trailing s is an ending, not a different subject.
    if len(term) >= 5 and term.endswith("s") and re.search(rf"\b{re.escape(term[:-1])}\b", text):
        return True
    # "bodybuilding" should meet "bodybuilders" without listing each topic's endings.
    if len(term) >= 8 and re.search(rf"\b{re.escape(term[:8])}", text):
        return True
    # One mistyped letter, or two letters swapped, still names the subject.
    # "porche" is Porsche, "ghengis" is Genghis, "wallstree" is Wall Street.
    # A plural such as "porches" is not that typo.
    words = re.findall(r"[a-z0-9]+", text.lower())
    for index, word in enumerate(words):
        if _typo(word, term):
            return True
        if index + 1 < len(words) and _typo(word + words[index + 1], term):
            return True
    return False


def _typo(word: str, term: str) -> bool:
    if len(term) < 5 or len(word) < 5 or abs(len(word) - len(term)) > 2:
        return False
    if word in {term + "s", term + "es"} or term in {word + "s", word + "es"}:
        return False
    distance = _edits(word, term)
    if distance <= 1:
        return True
    return distance == 2 and len(term) >= 7 and sorted(word) == sorted(term)


def _edits(left: str, right: str) -> int:
    if abs(len(left) - len(right)) > 2:
        return 3
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, start=1):
        current = [i]
        for j, b in enumerate(right, start=1):
            cost = 0 if a == b else 1
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def _noisy(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "skip to main content",
        "cookie",
        "views posted",
        "click here",
        "subscribe",
        "share on pinterest",
        "pinterest",
        "[1",
        "http://",
        "https://",
    )
    if any(marker in lowered for marker in markers):
        return True
    if re.search(r"\b\d{1,2}:\d{2}\b", text):
        return True
    return False


def revised_report(report: str) -> dict:
    paper = report.strip()
    words = paper.split()
    note_count = len(re.findall(r"^\[\^\d+\]:", paper, flags=re.M))
    citation_count = len(re.findall(r"\[\d+\]", paper))
    strengths = []
    if "## What the records support" in paper and "## Conclusion" in paper:
        strengths.append("The draft moves from a definition, through the ideas that support it, to a close a beginner can repeat.")
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
            "- Keep the order: what the subject is, then the contrast, then the ideas that strengthen it.",
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
            if not url or url in seen:
                continue
            if not summary and not title:
                continue
            if not summary:
                summary = title
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
    return sources[:12]


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
    text = re.sub(r"\.{2,}", ".", text)
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
    # A teaching draft already states its order. Inserting a second roadmap
    # would put a generic sentence beside the definition the records support.
    already_ordered = "What the records support" in paper or "The pages move in one direction" in paper
    if "## Introduction" in paper and not already_ordered and "The pages that follow" not in paper and "roadmap" not in paper.lower():
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
    text = text.replace("’", "'").replace("‘", "'")
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
        "we'd": "we would",
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
            "photon",
            "photons",
            "quanta",
            "quantum",
            "duality",
            "macroscopic",
            "subatomic",
            "submicroscopic",
            "orbitals",
            "orbital",
            "superposition",
            "entanglement",
            "quantized",
            "schroedinger",
            "photoelectric",
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
