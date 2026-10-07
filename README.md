# Linear Research Desk

Jordan Damian's agentic research desk. Six agents run once, in order, and do not call back.

The original notes in `Agent1.txt`, `Agent2.txt`, `Agent 3.txt`, `RAG Agent.txt`, `Agent 5.txt`, `Agent 6.txt`, `tools.txt`, `prompt.txt`, and `Planned structure.txt` are unchanged. The running code is the glue around them.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.server:app --host 0.0.0.0 --port 8741
```

Open [http://127.0.0.1:8741](http://127.0.0.1:8741).

The first launch builds a local index of the public documents. That can take a minute. Later launches reuse `data/rag-cache/`.

## Keys

Copy `.env.example` to `.env` if you have keys. `.env` is not committed.

Agent 1 searches arXiv and the web for the question you type. The reference shelf is only for the later prose comparison.

- `XAI_API_KEY` — turns on Grok for Agents 1, 2, 3, and 5. The default model id is `grok-3-mini` (override with `XAI_MODEL`).
- `OPENAI_API_KEY` — turns on the OpenAI models named in the notes (`gpt-4o`, `gpt-4o-mini`).
- With neither key, those steps are composed locally from the records the searches return. They do not invent citations.
- `TAVILY_API_KEY` — web search uses the key. Without it, search sends a keyless request. If that fails, the tool returns an empty local fallback and says so. It does not invent pages.

## CI/CD (continuous integration and development)

Refinements after the first desk, in the order they were made:

- Live Tavily and arXiv for any topic. Writers stay on local composition until `XAI_API_KEY` (`grok-3-mini`, or `XAI_MODEL`) or `OPENAI_API_KEY` (`gpt-4o` / `gpt-4o-mini`). Grok 4o mini and `gpt-4l-mini` were placeholders, not runnable model ids.
- UI: their agent intro, placeholder “enter your inquiry here”, one “Gather information” button, collapsed left menu of indexed sources, “Results”, a dropdown per finished agent, then the full paper with Download HTML, then the graphic with Download JPEG.
- This pass: coherent basic academic report, basics first, points leading into points, tested on “quantum physics”.
- This pass: longer papers for a conversational overview, and a per-agent README.
- This pass: any ordinary topic with public records gets a paper. A physics-only sentence filter had dropped “hypertrophy in bodybuilding” after the search returned pages. If the tools return nothing, the page says so.

## Downloads

When a run finishes, the page offers the final paper as HTML and Agent 6's picture as JPEG.

## The pipeline

`app/pipeline.py` calls each agent once, in the order below. `app/server.py` serves the page and the downloads. The layout is `app/static/index.html`, `app/static/app.js`, and `app/static/styles.css`.

Search tools live in `research_tools/`. The prose shelf lives in `rag/`. The local paper writer lives in `app/compose.py`. With a model key, Agents 2, 3, and 5 call `app/llm.py` and still have to follow the same teaching order.

## Agent 1

Gathers sources for the inquiry you typed. It calls `arxiv_search` and `tavily_search` once each. It does not search the reference shelf.

- Code: `agents/res_ag.py`
- Tools: `research_tools/arxiv_search.py`, `research_tools/tavily_search.py` (schemas loaded from `tools.txt`)
- Brief: `app/compose.py` (`research_brief`)
- On the desk: a dropdown, “Agent 1 / Everything gathered”

## Agent 2

Writes the first academic draft from that brief. The draft starts with what the subject is, then the contrast, then the ideas that follow, and it develops each step with the next explanatory sentence from the records.

- Code: `agents/rough_draft_ag.py`
- Local writing: `app/compose.py` (`first_draft`)
- On the desk: a dropdown, “Agent 2 / First draft”

## Agent 3

Reads the first draft, notes strengths and limits, and revises it. It does not search again and it does not call Agent 2.

- Code: `agents/revise_draft_ag.py`
- Local revision: `app/compose.py` (`revised_report`)
- On the desk: a dropdown, “Agent 3 / Review”

## RAG Agent

Compares the revised paper with the public texts that could be indexed. It writes footnotes on sentence length and piled modifiers. Texts that could not be fetched are named and not quoted.

- Code: `agents/rag_ag.py`
- Shelf: `rag/index.py`
- On the desk: a dropdown, “RAG Agent / Footnotes and comparison”. The indexed sources sit in the collapsed left menu.

## Agent 5

Applies those footnotes, checks spelling and a few grammar issues, and returns one document.

- Code: `agents/final_draft_ag.py`
- Local edit: `app/compose.py` (`apply_editorial`)
- HTML: `app/render.py`
- On the desk: a dropdown, “Agent 5 / Final draft”, then the full paper with Download HTML

## Agent 6

Draws one JPEG from the final paper: the title, two claims, and one limit. It is not a second essay, and it does not talk to the earlier agents.

- Code: `agents/graphic_ag.py`
- On the desk: a dropdown, “Agent 6 / Graphic note”, then the graphic with Download JPEG
