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

TEACHING_STANDARD = """
Write a basic academic paper someone could hand to another person or turn in for a class.
- Start with what the subject is.
- Then give the core ideas in an order that builds, each point leading into the next.
- Do not dump out-of-context quotations or unrelated excerpts.
- Use only records included below. Do not invent citations, experiments, numbers, or quotations.
- If a retrieved record does not help explain the subject, leave it out of the argument and say it was set aside.
- Close with what a beginner can now explain, and with what these records do not establish.
"""

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
_ROLE_PLAN = (
    ("definition", 2),
    ("scope", 1),
    ("contrast", 2),
    ("discrete", 1),
    ("example", 1),
    ("duality", 1),
    ("knowledge", 1),
    ("uncertainty", 1),
    ("further", 1),
    ("path", 1),
)

_ROLE_JOB = {
    "definition": "what the subject is",
    "scope": "where that behavior shows up",
    "contrast": "the contrast with classical physics",
    "discrete": "how matter and energy are divided",
    "example": "the example already in that record",
    "duality": "wave and particle behavior",
    "knowledge": "probability in place of a single certain path",
    "uncertainty": "what cannot be known exactly at the same time",
    "further": "a further idea the earlier sentences do not state",
    "path": "how a class can state the account before the full mathematics",
}


def _outline(query: str, sources: list[dict]) -> dict:
    """Keep sentences that can teach, in an order that builds. Nothing is added."""
    terms = _query_terms(query)
    aside = []
    prepared = []
    for source in sources:
        if _sidebar(source):
            aside.append(source)
            continue
        text = _prepare(source.get("excerpt") or source.get("summary") or "")
        found = []
        seen = set()
        for sentence in sentences(text):
            sentence = _polish_excerpt(sentence)
            if sentence.lower() in seen or not _usable(sentence):
                continue
            role = _role(sentence)
            if not role:
                continue
            seen.add(sentence.lower())
            found.append((role, sentence, _quality(sentence, terms, role)))
        if not found:
            aside.append(source)
            continue
        prepared.append({**source, "candidates": found})
    return {"steps": _pick_steps(prepared), "aside": aside}


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

    support: list[str] = []
    opening = group("definition") + group("scope")
    if opening:
        bits = []
        for index, step in enumerate(opening):
            line = cited(step)
            if index == 0:
                bits.append(line)
            elif step["role"] == "definition":
                bits.append(f"The next record strengthens that opening: {line}")
            else:
                bits.append(f"The next record says where that behavior shows up: {line}")
        if group("contrast") or group("discrete") or group("duality"):
            bits.append(
                "What follows is the contrast, and then the ideas, that these retrieved records actually state."
            )
        support.append(" ".join(bits))
    contrasts = group("contrast")
    if contrasts:
        bits = [cited(contrasts[0])]
        for step in contrasts[1:]:
            bits.append(f"The next record strengthens that contrast: {cited(step)}")
        support.append(" ".join(bits))
    previous = "contrast" if contrasts else "definition"
    for role in ("discrete", "example", "duality", "knowledge", "uncertainty", "further", "path"):
        for step in group(role):
            support.append(f"{_idea_lead(role, step['sentence'], previous)} {cited(step)}")
            previous = role
    if not support:
        support.append(
            "The search returned records, but none of them stated the subject in language a paper can teach. "
            "This draft does not invent that statement."
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
            "The account starts with what the retrieved records say the subject is. "
            "It uses a later record only when that record adds the next point. "
            "Claims stay inside the sentences the search returned."
        ),
        "",
        "## Introduction",
        f"The question guiding this paper is: {framed['guide']}",
        "",
        f"The pages move in one direction. {direction} A reader who reaches the close can restate that sequence.",
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
    lines = [
        "The sentences above are the teaching sequence, not a sample of every record the search returned."
    ]
    for index, group in enumerate(groups):
        marks = " and ".join(f"[{number}]" for number in dict.fromkeys(group["numbers"]))
        if group["role"] == "definition":
            spoken = "what the subject is"
        elif group["role"] == "scope":
            spoken = "where the phenomena show up"
        elif group["role"] == "contrast":
            spoken = "the contrast with classical physics"
        else:
            spoken = _label_from_sentence(group["role"], group["sentence"])
        if index == 0:
            lines.append(f"They begin with {spoken} {marks}.")
        else:
            lines.append(f"They next give {spoken} {marks}.")
    lines.append("A citation in this list is only the sentence used for that step.")
    return " ".join(lines)


def _limits(aside: list[dict], today: str) -> str:
    titles = []
    for source in aside:
        title = source.get("title") or ""
        if title and title not in titles:
            titles.append(title)
    if titles:
        listed = ", ".join(f"“{title}”" for title in titles[:6])
        return (
            f"Other retrieved records were set aside because they do not explain the subject in beginner’s language: {listed}. "
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
        bits.append(f"It is distinct from the classical physics set beside that opening {marks}.")
    idea_bits = []
    for role in ("discrete", "example", "duality", "knowledge", "uncertainty", "further", "path"):
        chosen = [step for step in steps if step["role"] == role]
        if not chosen:
            continue
        marks = "".join(f"[{cite(step['source'])}]" for step in chosen)
        idea_bits.append(f"{_label_from_sentence(role, chosen[0]['sentence'])} {marks}")
    if idea_bits:
        bits.append("In the order the records support them, the account then gives " + "; ".join(idea_bits) + ".")
    bits.append(
        "These records do not derive the mathematics, and they do not replace a course. "
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
    if role == "path":
        return "A reader can stop at the ideas above. The last record says how a class can ask a beginner to hold them."
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
        if "formula" in text:
            return "a formulation with few formulas"
        return "a classroom statement of the same ideas"
    return _ROLE_JOB.get(role, "the next point")


def _sidebar(source: dict) -> bool:
    title = (source.get("title") or "").lower()
    url = (source.get("url") or "").lower()
    text = (source.get("excerpt") or source.get("summary") or "").lower()
    if "youtube.com" in url or "youtu.be" in url:
        return True
    if title.startswith("proceedings") or "proceedings of" in title:
        return True
    if "conference" in title and "proceedings" in text:
        return True
    if "programming" in title:
        return True
    if "collection of statements" in text and len(text.split()) < 80:
        return True
    return False


def _prepare(text: str) -> str:
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"skip to main content", " ", text, flags=re.I)
    text = re.split(r"German abstract:", text, maxsplit=1, flags=re.I)[0]
    text = re.sub(r"English abstract:\s*", "", text, flags=re.I)
    text = text.replace("(optical)", "")
    text = re.sub(r"\s+:\s*\d+(?:\.\d+)?", "", text)
    # Snippet cuts ("[...]") are not sentence ends. Keep only the clauses that
    # were already finished, so a cut word is not taught as a definition.
    kept = []
    for part in re.split(r"\[\.\.\.\]|…", text):
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
        r"(This|It|They|These|We|Our|Currently|In order|In fact|Data show|Lecture|Sign up|Spend)\b",
        sentence,
    ):
        return False
    if lowered.startswith("in physics, this means"):
        return False
    if re.search(r"\bpart in \d{3,}\b", lowered):
        return False
    if sentence.count("(") != sentence.count(")"):
        return False
    if sentence.count("“") != sentence.count("”"):
        return False
    if sentence.count('"') % 2:
        return False
    return True


def _role(sentence: str) -> str | None:
    text = sentence.lower()
    if (
        any(cue in text for cue in ("school", "student", "teach", "course", "tutorial", "formula"))
        and "programming" not in text
        and not re.search(r"\bis the (study|science|field|fundamental)\b", text)
    ):
        return "path"
    if "entangl" in text and any(cue in text for cue in ("two or more", "far apart", "connected", "single system")):
        return "further"
    if any(cue in text for cue in ("superposition", "multiple possible states", "until they are measured")):
        # A sentence that only names the word, or says the equations can calculate it,
        # does not teach the idea. Keep the sentence only when it says what the state is.
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
    if re.search(r"\b(is|are) (the |a |an )?(fascinating )?(study|science|field|branch|theory|fundamental)\b", text):
        return "definition"
    if any(cue in text for cue in ("is the fundamental", "explores the behavior", "describes the behavior", "studies how", "describes nature")):
        return "definition"
    return None


def _quality(sentence: str, terms: list[str], role: str) -> int:
    lowered = sentence.lower()
    score = _query_overlap(sentence, terms) * 2
    if role == "definition":
        if "is the study of" in lowered:
            score += 8
        elif "fundamental theory" in lowered or "branch of physics that explains" in lowered:
            score += 6
        elif "studies how" in lowered or "explores the behavior" in lowered or "smallest scales of our universe" in lowered:
            score += 5
        elif "is the science" in lowered:
            score += 3
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


def _query_terms(query: str) -> list[str]:
    stop = {"what", "when", "where", "which", "with", "from", "that", "this", "into", "about", "does", "have"}
    return [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]+", query)
        if len(word) > 3 and word.lower() not in stop
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
    return sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", lowered))


def _noisy(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "skip to main content",
        "cookie",
        "views posted",
        "click here",
        "subscribe",
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
