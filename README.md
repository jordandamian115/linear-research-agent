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

## Downloads

When a run finishes, the page offers the final paper as HTML and Agent 6's picture as JPEG.
