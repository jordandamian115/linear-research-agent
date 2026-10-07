# Linear Research Desk

Jordan Damian's agentic research desk. Six agents run once, in order, and do not call back:

1. **Agent 1** (`res_ag`) gathers sources with the arXiv and web-search tools.
2. **Agent 2** (`rough_draft_ag`) writes a first academic draft.
3. **Agent 3** (`revise_draft_ag`) reflects and revises that draft.
4. **RAG Agent** (`rag_ag`) compares the revision with a shelf of public documents and writes footnotes.
5. **Agent 5** (`final_draft_ag`) applies those footnotes and checks spelling, grammar, and tone.
6. **Agent 6** (`graphic_ag`) turns the final paper into one JPEG for a visual reader.

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

- `OPENAI_API_KEY` — Agents 1, 2, 3, and 5 call a model. Without it, those steps are composed locally from the text the tools return. They do not invent citations.
- `TAVILY_API_KEY` — web search uses the key. Without it, search sends a keyless request. If that fails, the tool returns an empty local fallback and says so. It does not invent pages.

## Downloads

When a run finishes, the page offers the final paper as HTML and Agent 6's picture as JPEG.
