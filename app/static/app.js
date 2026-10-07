const form = document.querySelector("#desk-form");
const queryBox = document.querySelector("#query");
const runButton = document.querySelector("#run");
const hint = document.querySelector("#hint");
const rail = document.querySelector("#rail");
const empty = document.querySelector("#empty");
const errorBox = document.querySelector("#error");
const errorText = document.querySelector("#error-text");
const reader = document.querySelector("#reader");
const readerKicker = document.querySelector("#reader-kicker");
const readerBody = document.querySelector("#reader-body");
const notes = document.querySelector("#notes");
const notesList = document.querySelector("#notes-list");
const finish = document.querySelector("#finish");
const digest = document.querySelector("#digest");
const downloadHtml = document.querySelector("#download-html");
const downloadJpg = document.querySelector("#download-jpg");
const mode = document.querySelector("#mode");
const shelfList = document.querySelector("#shelf-list");

const stages = new Map();
let timer = null;
let started = 0;
let selected = "";

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    queryBox.value = button.dataset.example;
    queryBox.focus();
  });
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = queryBox.value.trim();
  if (query.length < 8) {
    showError("Write a research question of at least a few words.");
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
      ? "arXiv and web search run on the question you type."
      : "arXiv and web search run on the question you type. Web search uses a keyless request, then an empty fallback if that fails.";
    mode.textContent = `${writing} ${search}`;
    buildRail(data.stages || []);
  } catch (err) {
    mode.textContent = "The desk did not answer a health check.";
  }
}

function buildRail(items) {
  rail.innerHTML = "";
  stages.clear();
  items.forEach((item, index) => {
    const li = document.createElement("li");
    li.className = "waiting";
    li.dataset.id = item.id;
    li.innerHTML = `<div class="mark">${index + 1}</div><button type="button"><strong></strong><span></span></button>`;
    li.querySelector("strong").textContent = item.label;
    li.querySelector("span").textContent = item.action;
    li.querySelector("button").addEventListener("click", () => showStage(item.id));
    rail.appendChild(li);
    stages.set(item.id, { meta: item, state: "waiting", html: "", footnotes: [], heading: item.label });
  });
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
      li.append(status, link);
      if (doc.reason) {
        const why = document.createElement("div");
        why.className = "hint";
        why.textContent = doc.reason;
        li.append(why);
      }
      shelfList.append(li);
    });
  } catch (err) {
    shelfList.innerHTML = "<li>The shelf could not be read. The desk can still take a question.</li>";
  }
}

async function start(query) {
  clearRun();
  runButton.disabled = true;
  empty.hidden = true;
  errorBox.hidden = true;
  rail.hidden = false;
  hint.textContent = "Agent 1 is starting.";
  started = Date.now();
  timer = setInterval(() => {
    const seconds = Math.round((Date.now() - started) / 1000);
    const current = [...stages.values()].find((stage) => stage.state === "running");
    if (current) hint.textContent = `${current.meta.label} is working · ${seconds}s`;
  }, 500);

  try {
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "The desk rejected the question.");
    }
    await readStream(response);
  } catch (err) {
    showError(err.message || "The desk stopped.");
  } finally {
    runButton.disabled = false;
    clearInterval(timer);
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
  if (finish.hidden && errorBox.hidden) {
    showError("The desk closed the stream before the last agent finished.");
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
    finish.hidden = false;
    return;
  }
  if (event.type !== "step") return;
  const stage = stages.get(event.id);
  if (!stage) return;
  stage.state = event.state;
  if (event.html) stage.html = event.html;
  if (event.heading) stage.heading = event.heading;
  if (event.footnotes) stage.footnotes = event.footnotes;
  if (event.paper_url) {
    downloadHtml.href = event.paper_url;
    finish.hidden = false;
  }
  if (event.image) {
    digest.src = event.image;
    digest.hidden = false;
    downloadJpg.href = event.image;
    finish.hidden = false;
  }
  paintRail();
  if (event.state === "done") showStage(event.id);
  renderNotes();
}

function paintRail() {
  rail.querySelectorAll("li").forEach((li) => {
    const stage = stages.get(li.dataset.id);
    li.className = stage.state;
    const mark = li.querySelector(".mark");
    mark.textContent = stage.state === "done" ? "✓" : stage.state === "running" ? "…" : mark.textContent;
  });
}

function showStage(id) {
  const stage = stages.get(id);
  if (!stage || !stage.html) return;
  selected = id;
  reader.hidden = false;
  readerKicker.textContent = stage.meta.label;
  readerBody.innerHTML = stage.html;
  empty.hidden = true;
}

function renderNotes() {
  notesList.innerHTML = "";
  let count = 0;
  stages.forEach((stage) => {
    (stage.footnotes || []).forEach((note) => {
      count += 1;
      const li = document.createElement("li");
      const who = document.createElement("div");
      who.className = "who";
      who.textContent = `${note.agent || stage.meta.label}${note.criterion ? " · " + note.criterion : ""}`;
      const copy = document.createElement("div");
      copy.textContent = note.text || "";
      li.append(who, copy);
      notesList.append(li);
    });
  });
  notes.hidden = count === 0;
}

function showError(message) {
  errorBox.hidden = false;
  errorText.textContent = message;
  empty.hidden = true;
  hint.textContent = "Stopped.";
}

function clearRun() {
  stages.forEach((stage, id) => {
    stage.state = "waiting";
    stage.html = "";
    stage.footnotes = [];
    stage.heading = stage.meta.label;
    const li = rail.querySelector(`li[data-id="${id}"]`);
    if (li) {
      const index = [...stages.keys()].indexOf(id);
      li.querySelector(".mark").textContent = String(index + 1);
    }
  });
  paintRail();
  reader.hidden = true;
  readerBody.innerHTML = "";
  notes.hidden = true;
  notesList.innerHTML = "";
  finish.hidden = true;
  digest.hidden = true;
  digest.removeAttribute("src");
  errorBox.hidden = true;
}
