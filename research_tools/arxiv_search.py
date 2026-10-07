# **Code added by Cursor**
# The arXiv schema in tools.txt names arxiv_search and a query string.
# That is the right shape. There was no function behind the schema, so a
# tool call could not return papers. This calls the public arXiv API only.

import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

_STOP = {
    "about", "after", "again", "because", "been", "before", "being",
    "between", "could", "does", "from", "have", "into", "more", "most",
    "only", "other", "over", "same", "some", "such", "than", "that",
    "their", "them", "then", "there", "these", "they", "this", "what",
    "when", "where", "which", "while", "with", "would", "your", "does",
    "have", "been", "were", "will", "shall", "should", "make", "makes",
}

_ATOM = {"a": "http://www.w3.org/2005/Atom"}


def arxiv_search(query: str, max_results: int = 5) -> dict:
    phrase = " ".join(str(query or "").split())
    if not phrase:
        return {"source": "arxiv", "query": "", "results": [], "note": "Empty query."}

    quoted = phrase.replace('"', "")
    try:
        results = _entries(_fetch(f'all:"{quoted}"', max_results))
        note = None
        if not results:
            words = [
                word
                for word in re.findall(r"[A-Za-z0-9]+", quoted)
                if len(word) > 3 and word.lower() not in _STOP
            ]
            if words:
                loose = " AND ".join(f"all:{word}" for word in words[:3])
                results = _entries(_fetch(loose, max_results))
                note = "The exact question matched nothing on arXiv. A shorter keyword search was used."
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "source": "arxiv",
            "query": phrase,
            "results": [],
            "note": f"arXiv could not be reached ({exc.__class__.__name__}).",
        }

    if not results and note is None:
        note = "arXiv returned no matching papers."
    return {"source": "arxiv", "query": phrase, "results": results, "note": note}


def _fetch(search_query: str, max_results: int) -> bytes:
    params = urllib.parse.urlencode(
        {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "ResearchDesk/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def _entries(payload: bytes) -> list[dict]:
    root = ET.fromstring(payload)
    results = []
    for entry in root.findall("a:entry", _ATOM):
        title = _text(entry.find("a:title", _ATOM))
        if title == "Error":
            continue
        summary = _text(entry.find("a:summary", _ATOM))
        published = _text(entry.find("a:published", _ATOM))[:10]
        authors = [
            _text(name)
            for name in entry.findall("a:author/a:name", _ATOM)
            if _text(name)
        ]
        link = ""
        for candidate in entry.findall("a:link", _ATOM):
            href = candidate.attrib.get("href", "")
            if candidate.attrib.get("rel") == "alternate" or "abs" in href:
                link = href
                break
        if not link:
            entry_id = _text(entry.find("a:id", _ATOM))
            link = entry_id
        results.append(
            {
                "title": title,
                "authors": authors,
                "published": published,
                "url": link,
                "summary": " ".join(summary.split()),
                "venue": "arXiv",
            }
        )
    return results


def _text(node) -> str:
    if node is None or node.text is None:
        return ""
    return " ".join(node.text.split())
