const apiInput = document.getElementById("apiBaseUrl");
const saveApiUrlBtn = document.getElementById("saveApiUrl");
const healthBtn = document.getElementById("healthCheckBtn");
const healthStatus = document.getElementById("healthStatus");
const ingestBtn = document.getElementById("ingestBtn");
const ingestOutput = document.getElementById("ingestOutput");
const queryBtn = document.getElementById("queryBtn");
const answerText = document.getElementById("answerText");
const answerMeta = document.getElementById("answerMeta");

const filePathInput = document.getElementById("filePath");
const questionInput = document.getElementById("question");

const STORAGE_KEY = "swiggy-rag-api-url";

function getApiBaseUrl() {
  const value = apiInput.value.trim();
  return value.replace(/\/$/, "");
}

function setStatus(text, className = "") {
  healthStatus.textContent = text;
  healthStatus.className = `status-pill ${className}`.trim();
}

function showIngestOutput(value, isError = false) {
  ingestOutput.textContent = value;
  ingestOutput.classList.toggle("error", isError);
}

function showAnswer(text, meta = "", isError = false) {
  answerText.textContent = text;
  answerText.classList.toggle("error", isError);
  answerMeta.textContent = meta;
}

async function callApi(path, payload) {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("Set API Base URL first.");
  }

  const res = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }
  return body;
}

saveApiUrlBtn.addEventListener("click", () => {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    setStatus("Set valid URL", "error");
    return;
  }
  localStorage.setItem(STORAGE_KEY, baseUrl);
  setStatus("Saved", "ok");
});

healthBtn.addEventListener("click", async () => {
  try {
    setStatus("Checking...");
    const baseUrl = getApiBaseUrl();
    if (!baseUrl) {
      throw new Error("Set API Base URL first.");
    }
    const res = await fetch(`${baseUrl}/health`);
    const body = await res.json();
    if (res.ok && body.status === "ok") {
      setStatus("Healthy", "ok");
    } else {
      setStatus("Unhealthy", "error");
    }
  } catch (err) {
    setStatus(err.message, "error");
  }
});

ingestBtn.addEventListener("click", async () => {
  const filePath = filePathInput.value.trim();
  if (!filePath) {
    showIngestOutput("Provide a file path.", true);
    return;
  }

  try {
    showIngestOutput("Ingesting...");
    const result = await callApi("/ingest", { file_path: filePath });
    showIngestOutput(JSON.stringify(result, null, 2));
  } catch (err) {
    showIngestOutput(err.message, true);
  }
});

queryBtn.addEventListener("click", async () => {
  const question = questionInput.value.trim();
  if (!question) {
    showAnswer("Question cannot be empty.", "", true);
    return;
  }

  try {
    showAnswer("Thinking...", "");
    const result = await callApi("/query", { question });
    const answer = result.answer?.text || "No answer returned.";
    const confidence = result.answer?.confidence;
    const chunks = result.retrieved_chunks || 0;
    showAnswer(
      answer,
      `Confidence: ${confidence ?? "n/a"} | Retrieved chunks: ${chunks}`,
      false,
    );
  } catch (err) {
    showAnswer(err.message, "", true);
  }
});

(function init() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    apiInput.value = saved;
  }
})();
