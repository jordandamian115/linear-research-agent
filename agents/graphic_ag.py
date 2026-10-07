# **Original code commented out**
# Agent 6.txt is empty. There was no design and no line to disable.
#
# **Code added by Cursor**
# The project note asks for one picture of the paper for a visual learner.
# The first JPEG was not that picture. It drew the run: a question, the
# records, two claims, a limit, and a citation count. Jordan had the right
# outcome, a single graphic after the paper, and no picture of the ideas.
# This version reads the paper's claims in order and draws five or six
# steps. Each step is a concept from those claims and an example already
# in the same words. It does not draw the agents or the search.

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from research_tools.parse_input import parse_input

_WIDTH = 1200
_INK = (30, 26, 22)
_RED = (156, 59, 46)
_CREAM = (246, 241, 231)
_CARD = (255, 250, 244)
_MUTED = (90, 78, 66)
_RULE = (214, 201, 182)
_GREEN = (36, 62, 52)

_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
_SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
_SERIF_ITALIC = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
_SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

_DROP = re.compile(
    r"^(From .+ the records go next\b"
    r"|Stop after that sentence\b"
    r"|The records do not supply\b"
    r"|The contrast needs\b"
    r"|Those units are the start\b"
    r"|A reader can stop\b"
    r"|The last record says\b"
    r"|With the subject named\b"
    r"|The next record says\b"
    r"|The next record adds\b"
    r"|Read the body\b"
    r"|The pages move\b"
    r"|The question guiding\b"
    r"|Use them in this order\b"
    r"|Start with\b"
    r"|Move next to\b"
    r"|Each citation is\b"
    r"|Do not open\b"
    r"|A listener needs\b"
    r"|This step follows\b"
    r"|It does not repeat\b"
    r"|A neighboring excerpt\b)",
    re.I,
)
_PREFIX = re.compile(
    r"^(?:The same record continues:\s*"
    r"|The next record strengthens that (?:opening|contrast):\s*"
    r"|The next record carries that idea one step further:\s*"
    r"|The next record adds [^:]{0,80}:\s*)",
    re.I,
)


def graphic_ag(report, destination: str | Path | None = None) -> dict:
    paper = parse_input(report)
    if isinstance(report, dict) and report.get("final_paper"):
        paper = report["final_paper"]
    content = _extract(paper)
    image = _draw(content)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    payload = buffer.getvalue()
    path = None
    if destination:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return {
        "caption": content["title"],
        "image_bytes": payload,
        "image_path": str(path) if path else "",
        "content": {
            "title": content["title"],
            "steps": content["steps"],
        },
    }


def _extract(paper: str) -> dict:
    title = "Research note"
    for line in paper.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    body = _section(paper, "what the records support")
    steps = _steps(body)
    if len(steps) < 5:
        extra = _section(paper, "conclusion")
        steps = _steps(body + "\n\n" + extra)
    steps = steps[:6]
    if len(steps) > 6:
        steps = steps[:6]
    if len(steps) < 5:
        steps = _pad_steps(steps, body or paper)
    return {"title": title, "steps": steps[:6]}


def _section(paper: str, heading: str) -> str:
    parts = re.split(r"\n## ", paper)
    for part in parts[1:]:
        name, _, body = part.partition("\n")
        if name.strip().lower() == heading:
            return body.strip()
    return ""


def _steps(body: str) -> list[dict]:
    paragraphs = []
    for block in re.split(r"\n\s*\n", body):
        sentences = _claims(block)
        if sentences:
            paragraphs.append(sentences)
    if not paragraphs:
        return []
    target = 6 if sum(len(item) for item in paragraphs) >= 6 else min(5, sum(len(item) for item in paragraphs))
    if target < 5:
        target = min(5, sum(len(item) for item in paragraphs))
    if len(paragraphs) > 6:
        paragraphs = [paragraphs[index] for index in _spread(len(paragraphs), 6)]
    if len(paragraphs) >= 5:
        chosen = paragraphs if len(paragraphs) <= 6 else [paragraphs[index] for index in _spread(len(paragraphs), 6)]
        return [_step_from(group) for group in chosen]
    counts = _slot_counts(paragraphs, 6 if sum(len(item) for item in paragraphs) >= 6 else 5)
    steps = []
    for sentences, slots in zip(paragraphs, counts):
        for group in _chunks(sentences, slots):
            steps.append(_step_from(group))
    return steps


def _slot_counts(paragraphs: list[list[str]], target: int) -> list[int]:
    counts = [1] * len(paragraphs)
    extras = target - len(paragraphs)
    guard = 0
    while extras > 0 and guard < 40:
        guard += 1
        available = [index for index in range(len(paragraphs)) if counts[index] < len(paragraphs[index])]
        if not available:
            break
        index = max(available, key=lambda item: len(paragraphs[item]) / counts[item])
        counts[index] += 1
        extras -= 1
    return counts


def _chunks(sentences: list[str], slots: int) -> list[list[str]]:
    if slots <= 1 or len(sentences) <= 1:
        return [sentences]
    slots = min(slots, len(sentences))
    groups = []
    for index in range(slots):
        start = round(index * len(sentences) / slots)
        end = round((index + 1) * len(sentences) / slots)
        piece = sentences[start:end]
        if piece:
            groups.append(piece)
    return groups or [sentences]


def _spread(count: int, take: int) -> list[int]:
    if count <= take:
        return list(range(count))
    raw = [round(index * (count - 1) / (take - 1)) for index in range(take)]
    chosen = []
    used = set()
    for index in raw:
        if index not in used:
            used.add(index)
            chosen.append(index)
    if len(chosen) < take:
        for index in range(count):
            if index not in used:
                chosen.append(index)
                used.add(index)
            if len(chosen) == take:
                break
        chosen.sort()
    return chosen


def _claims(block: str) -> list[str]:
    text = " ".join(block.split())
    found = []
    for part in re.split(r"(?<=[.!?])\s+", text):
        sentence = _bare(part)
        if not sentence or _DROP.match(sentence):
            continue
        if len(sentence.split()) < 6:
            continue
        if found and _overlap(found[-1], sentence) > 0.72:
            continue
        found.append(sentence)
    return found


def _bare(text: str) -> str:
    cleaned = re.sub(r"\[\d+\]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    previous = None
    while cleaned and cleaned != previous:
        previous = cleaned
        cleaned = _PREFIX.sub("", cleaned).strip()
    return cleaned


def _step_from(sentences: list[str]) -> dict:
    concept = _concept(sentences[0])
    example = _example(sentences, concept)
    return {"concept": concept, "example": example}


def _concept(sentence: str) -> str:
    text = _plain(sentence)
    pair = _split_pair(text)
    if pair and len(pair[0].split()) >= 6:
        text = pair[0]
    refers = re.search(r"\brefers to\s+(.+)", text, flags=re.I)
    if refers and 3 <= len(refers.group(1).split()) <= 14:
        text = refers.group(1)
    text = _clause(text, 16)
    return _finish(text)


def _example(sentences: list[str], concept: str) -> str:
    for sentence in sentences:
        phrase = _picture(sentence)
        if phrase and _overlap(phrase, concept) < 0.55:
            return _finish(_balanced(phrase))
        follow = _plain(sentence)
        pair = _split_pair(follow)
        if pair and _overlap(pair[1], concept) < 0.55 and len(pair[1].split()) >= 2:
            return _finish(_clause(pair[1], 16))
    if len(sentences) > 1:
        follow = _plain(sentences[1])
        if _overlap(follow, concept) < 0.55:
            return _finish(_clause(follow, 16))
    pieces = [piece.strip(" ,;") for piece in re.split(r",\s+|;\s+", _plain(sentences[0]))]
    if len(pieces) > 1:
        tail = ", ".join(pieces[1:])
        tail = re.sub(r"^(?:(?:or|and|that|which)\s+)+", "", tail, flags=re.I)
        tail = re.sub(r",\s+that\s+", " that ", tail, flags=re.I)
        if _overlap(tail, concept) < 0.55 and len(tail.split()) >= 3:
            return _finish(_clause(tail, 16))
    return _finish(_clause(_plain(sentences[-1]), 16))


def _picture(sentence: str) -> str:
    patterns = (
        r"\bsuch as\s+(.+)",
        r"\bfor example,?\s+(.+)",
        r"\bone example of\b.{0,70}?\bis\s+(.+)",
        r"\bfound that\s+(.+)",
        r"\b(technology we use today)\b",
        r'\bin the ["“](.+?)["”] course\b',
        r"\b(graphical interpretations of [A-Za-z0-9, ]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, sentence, flags=re.I)
        if not match:
            continue
        phrase = match.group(1).strip(" .;:")
        phrase = re.split(r"\.\s+", phrase)[0]
        if "course" in pattern and phrase and not phrase.lower().endswith("course"):
            phrase = f"{phrase} course"
        if phrase:
            return phrase
    notes = [note for note in re.findall(r"\(([^)]+)\)", sentence) if len(note.split()) >= 3]
    if notes:
        return "; ".join(notes)
    return ""


def _plain(sentence: str) -> str:
    text = _bare(sentence)
    text = text.replace("“", "").replace("”", "").replace('"', "")
    for pattern in (
        r"^In this blog,\s*",
        r"^Just as\s+",
        r"^For example,\s*",
        r"^Among the basic discoveries was the realization that\s+",
        r"^The aim is to achieve\s+",
        r"^A common misconception is that\s+",
        r"^It aims to\s+",
    ):
        text = re.sub(pattern, "", text, flags=re.I)
    text = re.sub(r"\binstead\b", "", text, flags=re.I)
    text = re.sub(r"^.*?is the field of \w+ that explains how\s+", "", text, count=1, flags=re.I)
    which = re.search(r"\bwhich is\s+(.+)", text, flags=re.I)
    if which and _overlap(text[: which.start()], which.group(1)) > 0.25:
        text = which.group(1)
    return re.sub(r"\s+", " ", text).strip(" .")


def _split_pair(sentence: str) -> tuple[str, str] | None:
    match = re.search(
        r"^(?P<head>.+?)\s+(?P<tail>(?:such as|caused by|achieved through|whereas|quantified by|used by)\s+.+)$",
        sentence,
        flags=re.I,
    )
    if not match:
        return None
    head = re.sub(r"\s*\([^)]*\)", "", match.group("head")).strip(" ,;:")
    tail = match.group("tail").strip(" .")
    if len(head.split()) < 4 or len(tail.split()) < 2:
        return None
    return head, tail


def _clause(text: str, count: int) -> str:
    plain = re.sub(r"\s*\([^)]*\)", "", text)
    plain = re.sub(r"\s+", " ", plain).strip(" .")
    comma = re.search(r",\s+", plain)
    if comma:
        head = plain[: comma.start()].strip()
        if 6 <= len(head.split()) <= count:
            plain = head
    return _clip(plain, count)


def _pad_steps(steps: list[dict], text: str) -> list[dict]:
    """A thin paper still has to show its own clauses, not a borrowed topic."""
    spare = _claims(text)
    for sentence in spare:
        step = _step_from([sentence])
        if any(step["concept"] == item["concept"] for item in steps):
            continue
        steps.append(step)
        if len(steps) >= 5:
            break
    return steps


def _balanced(text: str) -> str:
    pair = _split_pair(text)
    if pair:
        tail = re.sub(r"^(?:whereas|such as)\s+", "", pair[1], flags=re.I)
        return _clause(pair[0], 12) + "; " + _clause(tail, 12)
    return _clause(text, 16)


def _finish(text: str) -> str:
    cleaned = text.strip(" ,;:")
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def _clip(text: str, count: int) -> str:
    words = [word for word in text.split() if word]
    dangling = {
        "of", "the", "a", "an", "as", "that", "and", "with", "to", "for", "or", "in",
        "on", "by", "their", "who", "from", "into", "than", "this", "these", "those",
        "which", "whereas", "such", "about", "between", "within", "without", "given",
        "any", "more", "most", "both", "have", "has", "was", "were", "are", "being",
        "typically", "only", "might", "before", "each", "instead",
    }
    if len(words) > count:
        words = words[:count]
    while len(words) > 4 and words[-1].lower().strip(",;:") in dangling:
        words.pop()
    return " ".join(words).rstrip(",;:")


def _overlap(left: str, right: str) -> float:
    a = set(re.findall(r"[a-z]{4,}", left.lower()))
    b = set(re.findall(r"[a-z]{4,}", right.lower()))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a)


def _draw(content: dict) -> Image.Image:
    title_font = _font(_SERIF_BOLD, 48)
    concept_font = _font(_SERIF_BOLD, 28)
    example_font = _font(_SERIF_ITALIC, 24)
    label_font = _font(_SANS_BOLD, 15)
    number_font = _font(_SERIF_BOLD, 28)
    margin = 64
    text_width = _WIDTH - margin * 2 - 92
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    title_lines = _wrap(probe, content["title"], title_font, _WIDTH - margin * 2)
    blocks = []
    for step in content["steps"]:
        concept_lines = _wrap(probe, step["concept"], concept_font, text_width)[:3]
        example_lines = _wrap(probe, step["example"], example_font, text_width)[:3]
        height = 28 + len(concept_lines) * 36 + 26 + len(example_lines) * 32 + 22
        blocks.append((concept_lines, example_lines, max(height, 168)))
    height = 48 + 28 + len(title_lines) * 58 + 28 + sum(block[2] + 18 for block in blocks) + 36
    image = Image.new("RGB", (_WIDTH, height), _CREAM)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, _WIDTH, 14), fill=_RED)
    y = 42
    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=_INK)
        y += 58
    y += 8
    draw.line((margin, y, _WIDTH - margin, y), fill=_RULE, width=2)
    y += 26
    rail_x = margin + 26
    for index, (concept_lines, example_lines, block_height) in enumerate(blocks, start=1):
        top = y
        bottom = y + block_height
        if index < len(blocks):
            draw.line((rail_x, top + 54, rail_x, bottom + 18), fill=_RULE, width=4)
        draw.ellipse((rail_x - 26, top + 8, rail_x + 26, top + 60), fill=_RED)
        numeral = str(index)
        numeral_width = draw.textlength(numeral, font=number_font)
        draw.text((rail_x - numeral_width / 2, top + 14), numeral, font=number_font, fill=_CARD)
        card_left = margin + 78
        draw.rounded_rectangle(
            (card_left, top, _WIDTH - margin, bottom),
            radius=10,
            fill=_CARD,
            outline=_RULE,
        )
        text_x = card_left + 22
        cursor = top + 16
        for line in concept_lines:
            draw.text((text_x, cursor), line, font=concept_font, fill=_INK)
            cursor += 36
        cursor += 4
        draw.text((text_x, cursor), "EXAMPLE", font=label_font, fill=_GREEN)
        cursor += 24
        for line in example_lines:
            draw.text((text_x, cursor), line, font=example_font, fill=_MUTED)
            cursor += 32
        y = bottom + 18
    draw.rectangle((0, height - 14, _WIDTH, height), fill=_GREEN)
    return image


def _wrap(draw, text, font, width) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _font(path: str, size: int):
    if Path(path).exists():
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()
