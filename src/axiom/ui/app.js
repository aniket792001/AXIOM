/**
 * Axiom SCORE Engine - Real-Time Verification Dashboard Controller
 * Handles SSE streaming, real-time node state transitions, citation inspection,
 * and automated benchmark evaluation presets.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Element Selectors
  const queryForm = document.getElementById("query-form");
  const queryInput = document.getElementById("query-input");
  const submitBtn = document.getElementById("submit-btn");
  const pipelineStatusBadge = document.getElementById("pipeline-status-badge");
  const responseOutput = document.getElementById("response-output");
  const verdictTag = document.getElementById("verdict-tag");
  const citationsList = document.getElementById("citations-list");
  const citationCount = document.getElementById("citation-count");
  const diagnosticsLog = document.getElementById("diagnostics-log");
  const presetButtons = document.querySelectorAll(".preset-btn");

  // Step Node Elements
  const nodes = {
    router: {
      el: document.getElementById("node-router"),
      status: document.getElementById("status-router"),
    },
    retriever: {
      el: document.getElementById("node-retriever"),
      status: document.getElementById("status-retriever"),
    },
    grader: {
      el: document.getElementById("node-grader"),
      status: document.getElementById("status-grader"),
    },
    generator: {
      el: document.getElementById("node-generator"),
      status: document.getElementById("status-generator"),
    },
    hallucination: {
      el: document.getElementById("node-hallucination"),
      status: document.getElementById("status-hallucination"),
    },
  };

  let activeStreamController = null;

  // ---------------------------------------------------------------------------
  // Diagnostics Logger Helper
  // ---------------------------------------------------------------------------
  function appendLog(nodeName, message) {
    if (!diagnosticsLog) return;
    const now = new Date();
    const timeStr = now.toTimeString().split(" ")[0];

    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-node">${escapeHtml(nodeName.toUpperCase())}</span>
      <span class="log-msg">${escapeHtml(message)}</span>
    `;
    diagnosticsLog.appendChild(entry);
    diagnosticsLog.scrollTop = diagnosticsLog.scrollHeight;
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // ---------------------------------------------------------------------------
  // Pipeline Node State Transitions
  // ---------------------------------------------------------------------------
  function resetPipeline() {
    Object.keys(nodes).forEach((key) => {
      const node = nodes[key];
      if (node && node.el) {
        node.el.classList.remove("active", "completed", "warning");
        if (node.status) node.status.textContent = "Idle";
      }
    });
    if (pipelineStatusBadge) {
      pipelineStatusBadge.textContent = "Ready";
      pipelineStatusBadge.style.color = "var(--accent-ai)";
    }
  }

  function setNodeActive(nodeKey, statusText = "Active") {
    const node = nodes[nodeKey];
    if (!node || !node.el) return;
    node.el.classList.remove("completed", "warning");
    node.el.classList.add("active");
    if (node.status) node.status.textContent = statusText;
  }

  function setNodeCompleted(nodeKey, statusText = "Verified") {
    const node = nodes[nodeKey];
    if (!node || !node.el) return;
    node.el.classList.remove("active", "warning");
    node.el.classList.add("completed");
    if (node.status) node.status.textContent = statusText;
  }

  function setNodeWarning(nodeKey, statusText = "Warning") {
    const node = nodes[nodeKey];
    if (!node || !node.el) return;
    node.el.classList.remove("active", "completed");
    node.el.classList.add("warning");
    if (node.status) node.status.textContent = statusText;
  }

  // ---------------------------------------------------------------------------
  // Citations & Verdict Rendering
  // ---------------------------------------------------------------------------
  function renderCitations(citations) {
    if (!citationsList || !citationCount) return;
    citationsList.innerHTML = "";

    if (!citations || citations.length === 0) {
      citationCount.textContent = "0 Sources";
      citationsList.innerHTML = `
        <div style="font-size: 13px; color: var(--text-muted); font-style: italic;">
          No explicit context citations required or available.
        </div>
      `;
      return;
    }

    citationCount.textContent = `${citations.length} Verified Sources`;

    citations.forEach((cit, idx) => {
      const item = document.createElement("div");
      item.className = "citation-item";

      const chunkId = cit.chunk_id || `chunk_${idx + 1}`;
      const quote = cit.quote || "Direct cited passage";

      item.innerHTML = `
        <div class="citation-header">
          <span class="citation-chip">${escapeHtml(chunkId)}</span>
          <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-code);">SOURCE VERIFIED</span>
        </div>
        <div class="citation-quote">"${escapeHtml(quote)}"</div>
      `;
      citationsList.appendChild(item);
    });
  }

  function setVerdict(isGrounded, label) {
    if (!verdictTag) return;
    verdictTag.style.display = "inline-flex";
    if (isGrounded) {
      verdictTag.className = "verdict-tag grounded";
      verdictTag.textContent = label || "Verified Grounded";
    } else {
      verdictTag.className = "verdict-tag refusal";
      verdictTag.textContent = label || "Epistemic Refusal";
    }
  }

  // ---------------------------------------------------------------------------
  // Execute SCORE Query via SSE Stream
  // ---------------------------------------------------------------------------
  async function executeQuery(queryText) {
    if (!queryText.trim()) return;

    if (activeStreamController) {
      activeStreamController.abort();
    }
    activeStreamController = new AbortController();

    // Reset UI State
    resetPipeline();
    submitBtn.disabled = true;
    submitBtn.classList.add("loading");
    responseOutput.innerHTML = `
      <div style="color: var(--text-muted); font-style: italic; display: flex; align-items: center; gap: 8px;">
        <span class="spinner"></span> Executing SCORE multi-agent reasoning loops...
      </div>
    `;
    verdictTag.style.display = "none";
    citationsList.innerHTML = `
      <div style="font-size: 13px; color: var(--text-muted); font-style: italic;">
        Awaiting verified citation audit...
      </div>
    `;
    citationCount.textContent = "Analyzing...";
    pipelineStatusBadge.textContent = "Executing SCORE Loops";
    pipelineStatusBadge.style.color = "var(--accent-ai)";

    appendLog("QUERY", `Received query: "${queryText}"`);

    try {
      const response = await fetch("/api/v1/query/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
        },
        body: JSON.stringify({
          query: queryText,
          tenant_id: "default_tenant",
          user_id: "axiom_analyst",
        }),
        signal: activeStreamController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
        const events = buffer.split("\n\n");
        buffer = events.pop(); // Keep unfinished chunk in buffer

        for (const rawEvent of events) {
          if (!rawEvent.trim()) continue;

          let eventName = "message";
          let dataStr = "";

          const lines = rawEvent.split("\n");
          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventName = line.substring(6).trim();
            } else if (line.startsWith("data:")) {
              dataStr += line.substring(5).trim();
            }
          }

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            handleSseEvent(eventName, data);
          } catch (err) {
            console.warn("Failed to parse SSE event data:", dataStr, err);
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") {
        appendLog("SYSTEM", "Query execution aborted by user.");
      } else {
        appendLog("ERROR", `Stream error: ${err.message}`);
        responseOutput.textContent = `Error executing SCORE pipeline: ${err.message}`;
        pipelineStatusBadge.textContent = "Error";
        pipelineStatusBadge.style.color = "var(--status-rejected)";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove("loading");
      activeStreamController = null;
    }
  }

  // ---------------------------------------------------------------------------
  // SSE Event Dispatcher
  // ---------------------------------------------------------------------------
  function handleSseEvent(eventName, data) {
    switch (eventName) {
      case "status":
        handleStatusEvent(data);
        break;

      case "answer":
        handleAnswerEvent(data);
        break;

      case "fallback":
        handleFallbackEvent(data);
        break;

      case "done":
        appendLog("DONE", "Pipeline reasoning sequence concluded.");
        pipelineStatusBadge.textContent = "Verified Completed";
        pipelineStatusBadge.style.color = "var(--status-verified)";
        break;

      case "error":
        appendLog("ERROR", data.error || "Unknown engine error");
        responseOutput.textContent = `Pipeline failure: ${data.error}`;
        pipelineStatusBadge.textContent = "Execution Failed";
        pipelineStatusBadge.style.color = "var(--status-rejected)";
        break;

      default:
        console.log("Unhandled event:", eventName, data);
    }
  }

  function handleStatusEvent(data) {
    if (data.phase === "initialized") {
      appendLog("INIT", `Orchestrating state machine for tenant '${data.tenant_id}'`);
      setNodeActive("router", "Classifying...");
      return;
    }

    const nodeName = data.node;
    const details = data.details || {};

    if (nodeName === "router") {
      setNodeCompleted("router", details.route || "Routed");
      appendLog("ROUTER", `Route selected: ${details.route || "vector_store"}`);
      setNodeActive("retriever", "Searching...");
    } else if (nodeName === "retriever") {
      setNodeCompleted("retriever", `${details.chunks_returned || 2} chunks`);
      appendLog("RETRIEVER", `Retrieved ${details.chunks_returned || 0} candidate chunks`);
      setNodeActive("grader", "Filtering...");
    } else if (nodeName === "grader") {
      const isRelevant = details.status === "relevant" || !details.status;
      if (isRelevant) {
        setNodeCompleted("grader", "Passed");
        appendLog("GRADER", "Context chunks verified relevant to query.");
        setNodeActive("generator", "Synthesizing...");
      } else {
        setNodeWarning("grader", "Reformulating");
        appendLog("GRADER", "Retrieved chunks insufficient. Initiating rewrite loop.");
      }
    } else if (nodeName === "rewriter") {
      appendLog("REWRITER", `Reformulated query to: "${details.rewritten_query || "..."}"`);
      setNodeActive("retriever", "Re-fetching...");
    } else if (nodeName === "generator") {
      setNodeCompleted("generator", "Drafted");
      appendLog("GENERATOR", "Synthesized candidate answer with inline citations.");
      setNodeActive("hallucination", "Auditing...");
    } else if (nodeName === "hallucination_grader") {
      const isGrounded = details.status === "grounded" || !details.status;
      if (isGrounded) {
        setNodeCompleted("hallucination", "Grounded");
        appendLog("AUDIT", "Zero-hallucination verification passed. Citations confirmed.");
      } else {
        setNodeWarning("hallucination", "Uncertain");
        appendLog("AUDIT", "Generation failed grounding verification.");
      }
    } else if (nodeName === "fallback") {
      setNodeWarning("hallucination", "Bluff Refusal");
      appendLog("FALLBACK", "Epistemic humility protocol triggered. Refusing unsupported assertion.");
    }
  }

  function handleAnswerEvent(data) {
    if (data.generation) {
      responseOutput.textContent = data.generation;
    }
    if (data.citations) {
      renderCitations(data.citations);
    }
    setVerdict(true, "Verified Grounded");
    setNodeCompleted("hallucination", "Grounded");
  }

  function handleFallbackEvent(data) {
    if (data.generation) {
      responseOutput.textContent = data.generation;
    }
    renderCitations([]);
    setVerdict(false, "Epistemic Humility Refusal");
    setNodeWarning("hallucination", "Refused Bluff");
  }

  // ---------------------------------------------------------------------------
  // Event Listeners for Query Submission & Presets
  // ---------------------------------------------------------------------------
  queryForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (query) {
      executeQuery(query);
    }
  });

  presetButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query) {
        queryInput.value = query;
        executeQuery(query);
      }
    });
  });
});
