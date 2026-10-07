/* **Code added by Cursor**
   The first script opened every draft in one pane and offered two example buttons.
   Jordan's notes do not describe a page. This script reveals one dropdown per
   finished agent, then the full paper, then the graphic, each with its own download. */

const form = document.querySelector("#desk-form");
const queryBox = document.querySelector("#query");
const runButton = document.querySelector("#run");
const hint = document.querySelector("#hint");
const emptyCopy = document.querySelector("#empty-copy");
const errorBox = document.querySelector("#error");
const errorText = document.querySelector("#error-text");
const running = document.querySelector("#running");
const drops = document.querySelector("#drops");
const paper = document.querySelector("#paper");
const paperBody = document.querySelector("#paper-body");
const graphic = document.querySelector("#graphic");
const digest = document.querySelector("#digest");
const downloadHtml = document.querySelector("#download-html");
const downloadJpg = document.querySelector("#download-jpg");
const mode = document.querySelector("#mode");
const shelfList = document.querySelector("#shelf-list");
const sourceMenu = document.querySelector("#source-menu");

const ORDER = [
  ["res_ag", "Agent 1", "Everything gathered"],
  ["rough_draft_ag", "Agent 2", "First draft"],
  ["revise_draft_ag", "Agent 3", "Review"],
  ["rag_ag", "RAG Agent", "Footnotes and comparison"],
  ["final_draft_ag", "Agent 5", "Final draft"],
  ["graphic_ag", "Agent 6", "Graphic note"],
];

const stages = new Map(ORDER.map(([id, label, action]) => [id, { label, action, state: "waiting" }]));
let timer = null;
let started = 0;

sourceMenu.open = false;

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = queryBox.value.trim();
  if (query.length < 8) {
    showError("Write an inquiry of at least a few words.");
    return;
  }
  start(query);
});

loadHealth();
loadShelf();

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    const model = data.model || "local";
    const writing = model === "local"
      ? "Model in use: local composition. Set XAI_API_KEY to turn on Grok, or OPENAI_API_KEY to turn on the OpenAI models named in the notes."
      : `Model in use: ${model}.`;
    const search = data.tavily === "api-key"
      ? "arXiv and web search run on the inquiry you type."
      : "arXiv and web search run on the inquiry you type. Web search uses a keyless request, then an empty fallback if that fails.";
    mode.textContent = `${writing} ${search}`;
  } catch (err) {
    mode.textContent = "The desk did not answer a health check.";
  }
}

async function loadShelf() {
  try {
    const response = await fetch("/api/index");
    if (!response.ok) throw new Error("shelf");
    const data = await response.json();
    shelfList.innerHTML = "";
    (data.documents || []).forEach((doc) => {
      const li = document.createElement("li");
      const status = document.createElement("span");
      status.className = `status ${doc.status}`;
      status.textContent = doc.status;
      const link = document.createElement("a");
      link.href = doc.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = doc.title;
      li.append(status, document.createTextNode(" "), link);
      if (doc.reason) {
        const why = document.createElement("div");
        why.className = "hint";
        why.textContent = doc.reason;
        li.append(why);
      }
      shelfList.append(li);
    });
    if (!shelfList.children.length) {
      shelfList.innerHTML = "<li>No indexed sources yet.</li>";
    }
  } catch (err) {
    shelfList.innerHTML = "<li>The shelf could not be read. You can still enter an inquiry.</li>";
  }
}

async function start(query) {
  clearRun();
  runButton.disabled = true;
  emptyCopy.hidden = true;
  errorBox.hidden = true;
  running.hidden = false;
  running.textContent = "Gathering information… Agent 1 is working.";
  started = Date.now();
  timer = setInterval(() => {
    const seconds = Math.round((Date.now() - started) / 1000);
    const current = [...stages.values()].find((stage) => stage.state === "running");
    if (current) running.textContent = `${current.label} is working · ${seconds}s`;
  }, 500);

  try {
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      const detail = payload.detail;
      throw new Error(typeof detail === "string" ? detail : "The desk rejected the inquiry.");
    }
    await readStream(response);
  } catch (err) {
    showError(err.message || "The desk stopped.");
  } finally {
    runButton.disabled = false;
    clearInterval(timer);
    running.hidden = true;
  }
}

async function readStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop();
    chunks.forEach(handleEvent);
  }
  if (buffer.trim()) handleEvent(buffer);
  if (paper.hidden && errorBox.hidden) {
    showError("The desk closed the stream before the final paper was ready.");
  }
}

function handleEvent(chunk) {
  const line = chunk.split("\n").find((item) => item.startsWith("data:"));
  if (!line) return;
  const event = JSON.parse(line.slice(5).trim());
  if (event.type === "error") {
    showError(event.message || "An agent failed.");
    return;
  }
  if (event.type === "done") {
    hint.textContent = event.composition === "model"
      ? "Finished with a model."
      : "Finished with local composition.";
    return;
  }
  if (event.type !== "step") return;
  const stage = stages.get(event.id);
  if (!stage) return;
  stage.state = event.state;
  if (event.state === "running") {
    running.hidden = false;
    running.textContent = `${stage.label} is working.`;
    return;
  }
  if (event.state !== "done") return;
  addDropdown(event.id, stage, event.html || "");
  if (event.id === "final_draft_ag" && event.html) {
    paperBody.innerHTML = event.html;
    paper.hidden = false;
  }
  if (event.paper_url) downloadHtml.href = event.paper_url;
  if (event.image) {
    digest.src = event.image;
    downloadJpg.href = event.image;
    graphic.hidden = false;
  }
}

function addDropdown(id, stage, html) {
  const existing = drops.querySelector(`[data-id="${id}"]`);
  const details = existing || document.createElement("details");
  details.className = "agent-drop";
  details.dataset.id = id;
  details.open = false;
  const summary = document.createElement("summary");
  summary.textContent = `${stage.label} · ${stage.action}`;
  const body = document.createElement("div");
  body.className = "drop-body";
  body.innerHTML = html || "<p>This agent finished without a document.</p>";
  details.replaceChildren(summary, body);
  if (!existing) drops.append(details);
}

function showError(message) {
  errorBox.hidden = false;
  errorText.textContent = message;
  emptyCopy.hidden = true;
  running.hidden = true;
  hint.textContent = "Stopped.";
}

function clearRun() {
  stages.forEach((stage) => {
    stage.state = "waiting";
  });
  drops.innerHTML = "";
  paper.hidden = true;
  paperBody.innerHTML = "";
  graphic.hidden = true;
  digest.removeAttribute("src");
  downloadHtml.href = "#";
  downloadJpg.href = "#";
  errorBox.hidden = true;
  hint.textContent = "";
}
