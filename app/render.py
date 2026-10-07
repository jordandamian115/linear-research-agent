# **Code added by Cursor**
# The upload asks for an HTML download of the final paper. None of the agent
# files render HTML. This turns the desk's plain-text paper into one document.

import html
import re


def paper_document(text: str, title: str | None = None) -> str:
    article, page_title = fragment(text)
    heading = title or page_title or "Research paper"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(heading)}</title>
  <style>
    body {{ margin: 0; background: #f4efe6; color: #1c1915; font-family: Georgia, "Liberation Serif", serif; }}
    article {{ max-width: 42rem; margin: 0 auto; padding: 3rem 1.25rem 4rem; }}
    h1 {{ font-size: 2rem; line-height: 1.2; font-weight: 600; }}
    h2 {{ font-size: 1.25rem; margin-top: 2rem; }}
    p {{ line-height: 1.6; }}
    a {{ color: #8c3a2f; }}
    .notes {{ border-top: 1px solid #d9cbb8; margin-top: 2.5rem; padding-top: 1rem; }}
    .notes li {{ margin: 0.6rem 0; }}
  </style>
</head>
<body>
{article}
</body>
</html>
"""


def fragment(text: str) -> tuple[str, str]:
    lines = text.replace("\r\n", "\n").split("\n")
    title = "Research paper"
    body: list[str] = []
    notes: list[tuple[str, str]] = []
    paragraph: list[str] = []

    def flush():
        if not paragraph:
            return
        joined = " ".join(part.strip() for part in paragraph if part.strip())
        paragraph.clear()
        if joined:
            body.append(f"<p>{_inline(joined)}</p>")

    for line in lines:
        stripped = line.strip()
        note = re.match(r"^\[\^(\d+)\]:\s*(.*)$", stripped)
        if note:
            flush()
            notes.append((note.group(1), note.group(2)))
            continue
        if not stripped:
            flush()
            continue
        if stripped.startswith("# "):
            flush()
            title = stripped[2:].strip()
            body.append(f"<h1>{_inline(title)}</h1>")
            continue
        if stripped.startswith("## "):
            flush()
            body.append(f"<h2>{_inline(stripped[3:].strip())}</h2>")
            continue
        if stripped.startswith("### "):
            flush()
            body.append(f"<h3>{_inline(stripped[4:].strip())}</h3>")
            continue
        paragraph.append(stripped)
    flush()

    notes_html = ""
    if notes:
        items = "".join(
            f'<li id="fn-{html.escape(number)}">{_inline(copy)}</li>'
            for number, copy in notes
        )
        notes_html = f'<ol class="notes">{items}</ol>'
    article = "<article>\n" + "\n".join(body) + "\n" + notes_html + "\n</article>"
    return article, title


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r"\[\^(\d+)\]",
        lambda match: f'<sup><a href="#fn-{match.group(1)}">{match.group(1)}</a></sup>',
        escaped,
    )
    return escaped


def footnotes_in(text: str) -> list[dict]:
    found = []
    for number, copy in re.findall(r"^\[\^(\d+)\]:\s*(.+)$", text, flags=re.M):
        found.append({"id": number, "text": copy.strip()})
    return found
