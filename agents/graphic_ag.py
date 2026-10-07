# **Original code commented out**
# Agent 6.txt is empty. There was no design and no line to disable.
#
# **Code added by Cursor**
# The project note asks for a graphic designer for visual learners: one
# picture of the paper, not a second essay, and no conversation with earlier
# agents. This draws a single JPEG broadside. A model is a poor fit for a
# fixed picture, so the layout is drawn from the final paper's title,
# question, and first claims. They had the right outcome in mind and no
# implementation to build on.

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from research_tools.parse_input import parse_input

_WIDTH = 1200
_HEIGHT = 1600
_INK = (30, 26, 22)
_RED = (156, 59, 46)
_CREAM = (246, 241, 231)
_CARD = (255, 250, 244)
_MUTED = (90, 78, 66)
_RULE = (214, 201, 182)
_GREEN = (36, 62, 52)

_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
_SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
_SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


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
        "content": {key: value for key, value in content.items()},
    }


def _extract(paper: str) -> dict:
    title = "Research note"
    for line in paper.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    question = ""
    match = re.search(r"The question guiding this paper is:\s*(.+)", paper)
    if match:
        question = match.group(1).strip()
    sections = re.split(r"\n## ", paper)
    claims = []
    limit = ""
    supported = []
    for section in sections[1:]:
        heading, _, body = section.partition("\n")
        name = heading.strip().lower()
        if name in {"references", "notes", "notes addressed", "abstract"}:
            continue
        sentence = _first_sentence(body)
        if not sentence:
            continue
        if name == "what the records support":
            supported.extend(_support_lines(body))
            continue
        if "limit" in name or "fallthrough" in name:
            limit = sentence
            continue
        if name != "introduction":
            claims.append(sentence)
    if supported:
        claims = supported + claims
    if not claims:
        claims = [_first_sentence(paper)]
    claims = [c for c in claims if c][:2]
    while len(claims) < 2:
        claims.append("The paper stays inside the records it retrieved.")
    if not limit:
        limit = "Read the notes before treating a sentence as a finding."
    citations = len(re.findall(r"\[\d+\]", paper))
    return {
        "title": _words(title, 16),
        "question": _words(question or title, 18),
        "claims": [_words(item, 22) for item in claims],
        "limit": _words(limit, 22),
        "citations": citations,
    }


def _draw(content: dict) -> Image.Image:
    image = Image.new("RGB", (_WIDTH, _HEIGHT), _CREAM)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, _WIDTH, 18), fill=_RED)
    draw.rectangle((0, _HEIGHT - 18, _WIDTH, _HEIGHT), fill=_GREEN)

    label = _font(_SANS_BOLD, 18)
    title_font = _font(_SERIF_BOLD, 54)
    serif = _font(_SERIF, 26)
    sans = _font(_SANS, 20)
    small = _font(_SANS, 16)
    number = _font(_SERIF_BOLD, 42)

    margin = 72
    y = 56
    draw.text((margin, y), "VISUAL DIGEST", font=label, fill=_RED)
    y += 42
    y = _paragraph(draw, content["title"], title_font, margin, y, _WIDTH - margin * 2, _INK, 62)
    y += 8
    draw.line((margin, y, _WIDTH - margin, y), fill=_RULE, width=2)
    y += 22
    subtitle = content["question"]
    if subtitle.strip(" ?.!").lower() == content["title"].strip(" ?.!").lower():
        subtitle = "Two claims from the records, then one limit."
    y = _paragraph(draw, subtitle, serif, margin, y, _WIDTH - margin * 2, _MUTED, 34)
    y += 28

    steps = ["Question", "Records", "Claim", "Limit"]
    span = _WIDTH - margin * 2
    for index, step in enumerate(steps):
        cx = margin + int(span * index / 3)
        draw.ellipse((cx - 16, y, cx + 16, y + 32), fill=_RED if index == 2 else _GREEN)
        draw.text((cx - 16, y + 44), step, font=small, fill=_INK)
        if index < 3:
            nxt = margin + int(span * (index + 1) / 3)
            draw.line((cx + 20, y + 16, nxt - 20, y + 16), fill=_RULE, width=3)
    y += 100

    cards = [
        ("01", "What the records say", content["claims"][0]),
        ("02", "Read beside that", content["claims"][1]),
        ("03", "Do not skip", content["limit"]),
    ]
    for numeral, heading, copy in cards:
        top = y
        draw.rounded_rectangle((margin, top, _WIDTH - margin, top + 210), radius=8, fill=_CARD, outline=_RULE)
        draw.rectangle((margin, top, margin + 10, top + 210), fill=_RED)
        draw.text((margin + 32, top + 22), numeral, font=number, fill=_RED)
        draw.text((margin + 120, top + 28), heading.upper(), font=label, fill=_GREEN)
        _paragraph(draw, copy, serif, margin + 120, top + 70, _WIDTH - margin * 2 - 150, _INK, 34)
        y += 230

    y = max(y + 10, 1420)
    draw.line((margin, y, _WIDTH - margin, y), fill=_RULE, width=2)
    y += 18
    draw.text((margin, y), str(content["citations"]), font=number, fill=_RED)
    draw.text((margin + 90, y + 8), "citation markers in the paper", font=sans, fill=_INK)
    draw.text(
        (margin, y + 58),
        "This picture is a map. The argument and the notes are in the paper.",
        font=small,
        fill=_MUTED,
    )
    return image


def _paragraph(draw, text, font, x, y, width, fill, line_height) -> int:
    words = text.split()
    if not words:
        return y
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
    for line in lines[:4]:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _font(path: str, size: int):
    if Path(path).exists():
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _support_lines(body: str) -> list[str]:
    found = []
    for line in body.splitlines():
        sentence = _first_sentence(line)
        if sentence:
            found.append(sentence)
    return found[:2]


def _first_sentence(text: str) -> str:
    cleaned = " ".join(line.strip() for line in text.splitlines() if line.strip() and not line.startswith("["))
    if not cleaned:
        return ""
    match = re.search(r".+?[.!?](?:\s|$)", cleaned)
    return match.group(0).strip() if match else _words(cleaned, 22)


def _words(text: str, count: int) -> str:
    words = " ".join(text.split())
    parts = words.split()
    if len(parts) <= count:
        return words
    return " ".join(parts[:count]) + "…"
