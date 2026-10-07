# **Code added by Cursor**
# RAG Agent.txt describes a comparison against indexed texts and then stops.
# The upload lists the documents but does not fetch them. This module indexes
# only what each URL actually returns in public form. Paywalled full text is
# not retrieved. A source that cannot be read is kept in the index with a reason.

from __future__ import annotations

import json
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = _ROOT / "data" / "rag-cache" / "index.json"
_LOCK = threading.Lock()
_DOCS: list[dict] | None = None

USER_AGENT = "ResearchDesk/1.0 (local academic index; public documents only)"

SOURCES = [
    {
        "id": "lincoln-addresses",
        "title": "Abraham Lincoln: First and Second Inaugural Addresses, July 5 1861 message, Emancipation Proclamation, and Gettysburg Address",
        "url": "https://tile.loc.gov/storage-services/public/gdcmassbookdig/firstsecondinaug01linc/firstsecondinaug01linc.pdf",
        "kind": "pdf",
    },
    {
        "id": "king-dream-essay",
        "title": "I Have a Dream",
        "url": "https://kinginstitute.stanford.edu/i-have-dream",
        "kind": "html",
    },
    {
        "id": "lincoln-second-manuscript",
        "title": "Abraham Lincoln, Second Inaugural Address, March 4, 1865 (manuscript transcription)",
        "url": "https://tile.loc.gov/storage-services/service/mss/mal/436/4361300/4361300.pdf",
        "kind": "pdf",
    },
    {
        "id": "gernsbacher-empirical",
        "title": "Writing Empirical Articles: Transparency, Reproducibility, Clarity, and Memorability",
        "url": "https://journals.sagepub.com/doi/10.1177/2515245918754485",
        "kind": "sage",
        "doi": "10.1177/2515245918754485",
    },
    {
        "id": "pinker-turgid-prose",
        "title": "Piled Modifiers, Buried Verbs, and Other Turgid Prose in the American Political Science Review",
        "url": "https://www.cambridge.org/core/journals/ps-political-science-and-politics/article/abs/piled-modifiers-buried-verbs-and-other-turgid-prose-in-the-american-political-science-review/A69D5F1A3CB222EFA4DCAE8993FACC72",
        "kind": "cambridge",
    },
    {
        "id": "tandf-style-manifesto",
        "title": "Writing higher education differently: a manifesto on style",
        "url": "https://www.tandfonline.com/doi/abs/10.1080/03075070802597101",
        "kind": "tandf",
        "doi": "10.1080/03075070802597101",
    },
    {
        "id": "hyland-persuasion",
        "title": "Persuasion, interaction and the construction of knowledge: representing self and others in research writing",
        "url": "https://revistas.um.es/ijes/article/view/49151",
        "kind": "ijes",
    },
    {
        "id": "pubmed-28873054",
        "title": "PubMed 28873054",
        "url": "https://pubmed.ncbi.nlm.nih.gov/28873054/",
        "kind": "pubmed",
        "pmid": "28873054",
    },
    {
        "id": "pubmed-34512473",
        "title": "PubMed 34512473",
        "url": "https://pubmed.ncbi.nlm.nih.gov/34512473/",
        "kind": "pubmed",
        "pmid": "34512473",
    },
    {
        "id": "pubmed-38008266",
        "title": "PubMed 38008266",
        "url": "https://pubmed.ncbi.nlm.nih.gov/38008266/",
        "kind": "pubmed",
        "pmid": "38008266",
    },
]


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        if tag in {"p", "div", "h1", "h2", "li", "br"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def documents() -> list[dict]:
    global _DOCS
    with _LOCK:
        if _DOCS is None:
            _DOCS = _load_or_build()
        return _DOCS


def public_status() -> list[dict]:
    rows = []
    for doc in documents():
        rows.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "url": doc["url"],
                "status": doc["status"],
                "reason": doc["reason"],
            }
        )
    return rows


def _load_or_build() -> list[dict]:
    if CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list) and len(data) == len(SOURCES):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    built = [retrieve(source) for source in SOURCES]
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(built, indent=2), encoding="utf-8")
    return built


def retrieve(source: dict) -> dict:
    kind = source["kind"]
    try:
        if kind == "pdf":
            return _from_pdf(source)
        if kind == "html":
            return _from_king(source)
        if kind == "sage":
            return _from_sage(source)
        if kind == "cambridge":
            return _from_cambridge(source)
        if kind == "tandf":
            return _from_tandf(source)
        if kind == "ijes":
            return _from_ijes(source)
        if kind == "pubmed":
            return _from_pubmed(source)
    except Exception as exc:  # retrieval must record the failure, not crash the desk
        return _record(source, "unavailable", f"Retrieval failed ({exc.__class__.__name__}).", "")
    return _record(source, "unavailable", "No retrieval method for this source.", "")


def _from_pdf(source: dict) -> dict:
    data = _get_bytes(source["url"])
    text = _pdf_text(data)
    if len(re.findall(r"[A-Za-z]", text)) < 400:
        return _record(
            source,
            "unavailable",
            "The PDF was public, but almost no text could be extracted from it.",
            "",
        )
    return _record(source, "indexed", "Public PDF text was extracted.", text)


def _from_king(source: dict) -> dict:
    html = _get_text(source["url"])
    chunks = re.findall(
        r'class="su-wysiwyg-text paragraph stanford-wysiwyg[^"]*"[^>]*>(.*?)</div>',
        html,
        flags=re.I | re.S,
    )
    text = _html_to_text("\n".join(chunks)) if chunks else ""
    if len(text) < 400:
        text = _html_to_text(html)
    text = _trim_king(text)
    if len(text) < 400:
        return _record(source, "unavailable", "The page responded, but the article text was not found.", "")
    return _record(
        source,
        "indexed",
        "Indexed the public encyclopedia article. The page discusses the speech; it is not a complete transcript.",
        text,
    )


def _from_sage(source: dict) -> dict:
    page = _probe(source["url"])
    abstract = _crossref_abstract(source["doi"])
    if page["status"] == 200 and len(page["text"]) > 800 and "cf-mitigated" not in page["headers"]:
        return _record(source, "indexed", "Publisher page text was public.", page["text"][:12000])
    if abstract:
        return _record(
            source,
            "partial",
            "The publisher page returned an access challenge. The public Crossref abstract was indexed. The full article was not retrieved.",
            abstract,
        )
    return _record(
        source,
        "unavailable",
        "The publisher page returned an access challenge, and no public abstract was found. The full article was not retrieved.",
        "",
    )


def _from_cambridge(source: dict) -> dict:
    html = _get_text(source["url"])
    plain = _html_to_text(html)
    abstract = _slice_between(plain, "Abstract", "Information Type")
    if not abstract or len(abstract) < 80:
        abstract = _slice_between(plain, "Abstract", "Get access")
    if abstract and len(abstract) > 80:
        return _record(
            source,
            "partial",
            "The public abstract page was retrieved. The full article is behind an access wall and was not retrieved.",
            abstract,
        )
    return _record(
        source,
        "unavailable",
        "The article page did not yield a public abstract, and the full text was not retrieved.",
        "",
    )


def _from_tandf(source: dict) -> dict:
    page = _probe(source["url"])
    if page["status"] == 200 and "cf-mitigated" not in page["headers"] and len(page["text"]) > 500:
        return _record(source, "indexed", "Publisher page text was public.", page["text"][:12000])
    meta = _crossref_message(source["doi"])
    title = ""
    if meta:
        titles = meta.get("title") or []
        title = titles[0] if titles else ""
    reason = (
        "The publisher page returned an access challenge. "
        "The public Crossref record has a title"
        + (f" ({title})" if title else "")
        + " but no abstract. The full text was not retrieved."
    )
    record = _record(source, "unavailable", reason, "")
    if title:
        record["title"] = title
    return record


def _from_ijes(source: dict) -> dict:
    html = _get_text(source["url"])
    landing = _html_to_text(html)
    abstract = _slice_between(landing, "Abstract", "Downloads")
    pdf_url = _ijes_pdf_url(html, source["url"])
    text = ""
    if pdf_url:
        data = _get_bytes(pdf_url)
        if data[:5] == b"%PDF-":
            text = _pdf_text(data)
    if len(re.findall(r"[A-Za-z]", text)) > 800:
        return _record(
            source,
            "indexed",
            "Indexed the open PDF linked from the public article page.",
            text,
        )
    if abstract and len(abstract) > 80:
        return _record(
            source,
            "partial",
            "The public abstract was indexed. The open PDF link did not return extractable text.",
            abstract,
        )
    return _record(source, "unavailable", "The journal page did not yield readable article text.", "")


def _ijes_pdf_url(html: str, page_url: str) -> str:
    direct = re.search(r'href="(https://revistas\.um\.es/ijes/article/download/[^"]+)"', html)
    if direct:
        return direct.group(1)
    galleys = re.findall(r'href="(https://revistas\.um\.es/ijes/article/view/\d+/\d+)"', html)
    for galley in galleys:
        if galley.rstrip("/") == page_url.rstrip("/"):
            continue
        try:
            galley_html = _get_text(galley)
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
        linked = re.search(r'href="(https://revistas\.um\.es/ijes/article/download/[^"]+)"', galley_html)
        if linked:
            return linked.group(1)
    return ""


def _from_pubmed(source: dict) -> dict:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={source['pmid']}&retmode=xml"
    )
    xml_text = _get_text(url)
    root = ET.fromstring(xml_text)
    title = _first(root, ".//ArticleTitle") or source["title"]
    authors = []
    for author in root.findall(".//Author"):
        fore = _first(author, "ForeName")
        last = _first(author, "LastName")
        collective = _first(author, "CollectiveName")
        name = " ".join(part for part in (fore, last) if part) or collective
        if name:
            authors.append(name)
    abstract_bits = []
    for node in root.findall(".//AbstractText"):
        label = node.attrib.get("Label")
        piece = "".join(node.itertext()).strip()
        if not piece:
            continue
        abstract_bits.append(f"{label}: {piece}" if label else piece)
    abstract = " ".join(abstract_bits)
    journal = _first(root, ".//Journal/Title") or "PubMed"
    year = _first(root, ".//PubDate/Year") or ""
    if not abstract:
        return _record(source, "unavailable", "NCBI returned no public abstract for this record.", "")
    record = _record(
        source,
        "partial",
        "Indexed the public PubMed abstract through NCBI E-utilities. The publisher full text was not retrieved.",
        abstract,
    )
    record["title"] = title
    record["authors"] = authors[:8]
    record["venue"] = journal
    record["year"] = year
    return record


def _record(source: dict, status: str, reason: str, text: str) -> dict:
    cleaned = _clean(text)
    stats = _style_stats(cleaned) if cleaned else {}
    return {
        "id": source["id"],
        "title": source["title"],
        "url": source["url"],
        "status": status,
        "reason": reason,
        "text": cleaned[:20000],
        "authors": source.get("authors", []),
        "venue": source.get("venue", ""),
        "year": source.get("year", ""),
        "stats": stats,
        "exemplars": _exemplars(cleaned),
    }


def _get_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _get_text(url: str) -> str:
    return _get_bytes(url).decode("utf-8", errors="replace")


def _probe(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(20000)
            headers = " ".join(f"{k}:{v}" for k, v in response.headers.items()).lower()
            return {
                "status": response.status,
                "headers": headers,
                "text": _html_to_text(raw.decode("utf-8", errors="replace")),
            }
    except urllib.error.HTTPError as exc:
        headers = " ".join(f"{k}:{v}" for k, v in exc.headers.items()).lower() if exc.headers else ""
        return {"status": exc.code, "headers": headers, "text": ""}


def _pdf_text(data: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    pages = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        letters = len(re.findall(r"[A-Za-z]", extracted))
        if letters >= 200:
            pages.append(extracted)
    return "\n\n".join(pages)


def _crossref_message(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    try:
        payload = json.loads(_get_text(url))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None
    message = payload.get("message")
    return message if isinstance(message, dict) else None


def _crossref_abstract(doi: str) -> str:
    message = _crossref_message(doi) or {}
    abstract = message.get("abstract") or ""
    if not abstract:
        return ""
    return _html_to_text(abstract)


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return _clean(text)


def _clean(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _trim_king(text: str) -> str:
    start = text.find("On 28 Aug")
    if start < 0:
        start = text.lower().find("i have a dream")
    if start > 0:
        text = text[start:]
    for marker in ("Related Links", "Footer menu", "SU Footer"):
        end = text.find(marker)
        if end > 400:
            text = text[:end]
    return text.strip()


def _slice_between(text: str, start: str, end: str) -> str:
    begin = text.lower().find(start.lower())
    if begin < 0:
        return ""
    begin += len(start)
    stop = text.lower().find(end.lower(), begin)
    chunk = text[begin:stop if stop > begin else begin + 1600]
    return " ".join(chunk.split())


def _first(node, path: str) -> str:
    found = node.find(path)
    if found is None:
        return ""
    return " ".join("".join(found.itertext()).split())


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    cleaned = []
    for part in parts:
        sentence = " ".join(part.split())
        words = sentence.split()
        if 6 <= len(words) <= 80:
            cleaned.append(sentence)
    return cleaned


def _style_stats(text: str) -> dict:
    found = sentences(text)
    lengths = [len(sentence.split()) for sentence in found]
    if not lengths:
        return {}
    long_share = sum(1 for n in lengths if n >= 35) / len(lengths)
    return {
        "sentences": len(lengths),
        "mean_sentence_words": round(sum(lengths) / len(lengths), 1),
        "long_sentence_share": round(long_share, 2),
    }


def _exemplars(text: str) -> list[str]:
    picked = []
    for sentence in sentences(text):
        words = sentence.split()
        if 8 <= len(words) <= 28:
            picked.append(sentence)
        if len(picked) == 2:
            break
    return picked


if __name__ == "__main__":
    rows = documents()
    for row in rows:
        print(f"{row['status']:12} {row['id']:28} chars={len(row['text']):5} {row['reason'][:90]}")
