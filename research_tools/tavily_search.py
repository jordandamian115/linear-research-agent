# **Code added by Cursor**
# tools.txt defines tavily_search as a web search for the research question.
# The schema was close and is loaded unchanged from that file. No function
# was written, and no key is stored in the project. The query sent is the
# question the user typed, not the RAG shelf. When TAVILY_API_KEY is set,
# this calls the search API with that key. Otherwise it sends a keyless
# request. If that also fails, it returns an empty local fallback and says
# so. It does not invent pages.
# The keyless call was already reaching the API. The payload did not keep
# the HTTP status, and a hit with a title but no snippet could disappear
# before Agent 1. A failed keyless response now keeps that status instead
# of looking like a quiet empty success.

import json
import os
import urllib.error
import urllib.request


def tavily_search(query: str, max_results: int = 5) -> dict:
    phrase = " ".join(str(query or "").split())
    if not phrase:
        return _fallback(phrase, "Empty query.")

    key = os.environ.get("TAVILY_API_KEY", "").strip()
    key_present = bool(key)
    body = json.dumps(
        {
            "query": phrase,
            "max_results": max_results,
            "search_depth": "basic",
            "topic": "general",
            "include_answer": False,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    mode = "api-key"
    if key:
        headers["Authorization"] = f"Bearer {key}"
    else:
        headers["X-Tavily-Access-Mode"] = "keyless"
        mode = "keyless"

    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", None)
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:180]
        except Exception:
            detail = ""
        return _fallback(
            phrase,
            f"Tavily returned HTTP {exc.code}. {detail}".strip(),
            key_present=key_present,
            status=exc.code,
        )
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return _fallback(
            phrase,
            f"Tavily could not be reached ({exc.__class__.__name__}). No HTTP status came back.",
            key_present=key_present,
            status=None,
        )

    results = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        title = " ".join(str(item.get("title") or "").split())
        content = " ".join(str(item.get("content") or "").split())
        if not url or not (title or content):
            continue
        results.append(
            {
                "title": title or url,
                "authors": [],
                "published": "",
                "url": url,
                "summary": content,
                "venue": "Tavily",
            }
        )
    note = None
    if not results:
        note = (
            f"Tavily answered HTTP {status} and returned no pages. "
            "No substitute pages were added."
        )
    return {
        "source": "tavily",
        "mode": mode,
        "query": phrase,
        "results": results,
        "note": note,
        "status": status,
        "key_present": key_present,
    }


def _fallback(query: str, reason: str, key_present: bool = False, status: int | None = None) -> dict:
    status_line = f"HTTP {status}." if status is not None else "No HTTP status."
    return {
        "source": "tavily",
        "mode": "local-fallback",
        "query": query,
        "results": [],
        "note": (
            f"Tavily did not return pages. {status_line} "
            "No substitute pages were added. "
            + " ".join(reason.split())
        ),
        "status": status,
        "key_present": key_present,
    }
