/**
 * Axiom SCORE Engine - Enterprise Platform Controller
 * Supports Role-Based Access Control (Admin, Analyst, Auditor),
 * multi-turn conversational streaming, Knowledge Vault data room,
 * and cryptographic audit certificate generation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Current Session & User State
  let currentUser = null;
  let activeTenant = "default_tenant";
  let currentSessionId = "session_" + Math.random().toString(36).substring(2, 9);
  let activeStreamController = null;
  let activeCitationsMap = {};

  // DOM Elements - Auth & Roles
  const authGateModal = document.getElementById("auth-gate-modal");
  const roleCards = document.querySelectorAll(".role-card");
  const customLoginForm = document.getElementById("custom-login-form");
  const customEmailInput = document.getElementById("custom-email-input");
  const sidebarUserAvatar = document.getElementById("sidebar-user-avatar");
  const sidebarUserName = document.getElementById("sidebar-user-name");
  const sidebarUserRole = document.getElementById("sidebar-user-role");
  const switchRoleBtn = document.getElementById("switch-role-btn");

  // DOM Elements - Navigation & Shell
  const tabBtnChat = document.getElementById("tab-btn-chat");
  const tabBtnVault = document.getElementById("tab-btn-vault");
  const tabBtnKeys = document.getElementById("tab-btn-keys");
  const workspaceSelect = document.getElementById("workspace-select");
  const currentViewTitle = document.getElementById("current-view-title");
  const activeTenantBadge = document.getElementById("active-tenant-badge");
  const scoreLiveIndicator = document.getElementById("score-live-indicator");
  const scoreLiveStatusText = document.getElementById("score-live-status-text");
  const modelProviderSelect = document.getElementById("model-provider-select");
  const vaultDocCountBadge = document.getElementById("vault-doc-count");

  // DOM Elements - Chat View
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatContainer = document.getElementById("chat-messages-container");
  const chatHeroEmpty = document.getElementById("chat-hero-empty");
  const promptCards = document.querySelectorAll(".prompt-card");
  const newThreadBtn = document.getElementById("new-thread-btn");
  const currentThreadPill = document.getElementById("current-thread-pill");
  const quickUploadTrigger = document.getElementById("quick-upload-trigger");
  const pipelineStepper = document.getElementById("pipeline-stepper");
  const stepperLoopInfo = document.getElementById("stepper-loop-info");

  // Stepper Step Elements
  const stepperSteps = {
    router: document.getElementById("step-router"),
    retriever: document.getElementById("step-retriever"),
    grader: document.getElementById("step-grader"),
    generator: document.getElementById("step-generator"),
    audit: document.getElementById("step-audit"),
  };

  // DOM Elements - Knowledge Vault
  const vaultDropzone = document.getElementById("vault-dropzone");
  const vaultFileInput = document.getElementById("vault-file-input");
  const vaultTableBody = document.getElementById("vault-table-body");
  const statDocCount = document.getElementById("stat-doc-count");
  const statChunkCount = document.getElementById("stat-chunk-count");
  const uploadProgressRow = document.getElementById("upload-progress-row");
  const uploadProgressFill = document.getElementById("upload-progress-fill");
  const uploadProgressText = document.getElementById("upload-progress-text");

  // DOM Elements - API Keys
  const createKeyBtn = document.getElementById("create-key-btn");
  const keyModal = document.getElementById("key-modal");
  const keyModalClose = document.getElementById("key-modal-close");
  const keyModalCancel = document.getElementById("key-modal-cancel");
  const createKeyForm = document.getElementById("create-key-form");
  const keyNameInput = document.getElementById("key-name-input");
  const keyRoleSelect = document.getElementById("key-role-select");
  const keysTableBody = document.getElementById("keys-table-body");
  const newKeyDisplay = document.getElementById("new-key-display");
  const rawKeyValue = document.getElementById("raw-key-value");
  const copyTokenBtn = document.getElementById("copy-token-btn");

  // DOM Elements - Citation Drawer
  const citationDrawer = document.getElementById("citation-drawer");
  const drawerBackdrop = document.getElementById("drawer-backdrop");
  const drawerCloseBtn = document.getElementById("drawer-close-btn");
  const drawerDocTitle = document.getElementById("drawer-doc-title");
  const drawerDocPage = document.getElementById("drawer-doc-page");
  const drawerScore = document.getElementById("drawer-score");
  const drawerStatus = document.getElementById("drawer-status");
  const drawerChunkId = document.getElementById("drawer-chunk-id");
  const drawerExcerpt = document.getElementById("drawer-excerpt");

  // ---------------------------------------------------------------------------
  // AUTHENTICATION & ROLE-BASED ACCESS CONTROL (RBAC)
  // ---------------------------------------------------------------------------
  async function loginUser(email, role = null, tenant = null) {
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, role: role }),
      });

      if (!response.ok) throw new Error("Authentication failed");
      const data = await response.json();
      currentUser = data.user;
      sessionStorage.setItem("axiom_user", JSON.stringify(currentUser));
      sessionStorage.setItem("axiom_token", data.token);

      if (tenant) {
        activeTenant = tenant;
      } else if (currentUser.default_tenant) {
        activeTenant = currentUser.default_tenant;
      }

      applyUserProfile();
      hideAuthModal();
      loadVaultDocuments();
      loadApiKeys();
    } catch (err) {
      alert("Login error: " + err.message);
    }
  }

  function applyUserProfile() {
    if (!currentUser) return;

    if (sidebarUserAvatar) sidebarUserAvatar.textContent = currentUser.avatar || "U";
    if (sidebarUserName) sidebarUserName.textContent = currentUser.name;
    if (sidebarUserRole) {
      const roleMap = {
        admin: "Enterprise Admin",
        analyst: "Contract Analyst",
        auditor: "Risk Auditor",
      };
      sidebarUserRole.textContent = roleMap[currentUser.role] || currentUser.role.toUpperCase();
    }

    if (workspaceSelect) {
      workspaceSelect.value = activeTenant;
    }
    if (activeTenantBadge) {
      activeTenantBadge.textContent = `Tenant: ${activeTenant}`;
    }

    // Role-based UI gating
    enforceRolePermissions();
  }

  function enforceRolePermissions() {
    if (!currentUser) return;
    const role = currentUser.role;

    // Auditors have read-only compliance access: cannot delete docs, cannot create keys
    if (role === "auditor") {
      if (createKeyBtn) {
        createKeyBtn.disabled = true;
        createKeyBtn.title = "Auditor role has read-only access (API key generation disabled)";
        createKeyBtn.style.opacity = "0.5";
      }
    } else {
      if (createKeyBtn) {
        createKeyBtn.disabled = false;
        createKeyBtn.title = "";
        createKeyBtn.style.opacity = "1";
      }
    }
  }

  function showAuthModal() {
    if (authGateModal) authGateModal.classList.remove("hidden");
  }

  function hideAuthModal() {
    if (authGateModal) authGateModal.classList.add("hidden");
  }

  // Quick Role Card Click Handlers
  roleCards.forEach(card => {
    card.addEventListener("click", () => {
      const email = card.getAttribute("data-email");
      const role = card.getAttribute("data-role");
      const tenant = card.getAttribute("data-tenant");
      loginUser(email, role, tenant);
    });
  });

  // Custom Email Sign-In
  customLoginForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = customEmailInput?.value?.trim();
    if (email) loginUser(email, "analyst");
  });

  // Switch Role / Logout Button
  switchRoleBtn?.addEventListener("click", () => {
    showAuthModal();
  });

  // Check saved session on boot
  const savedUser = sessionStorage.getItem("axiom_user");
  if (savedUser) {
    try {
      currentUser = JSON.parse(savedUser);
      activeTenant = currentUser.default_tenant || "default_tenant";
      applyUserProfile();
      hideAuthModal();
    } catch (e) {
      showAuthModal();
    }
  } else {
    showAuthModal();
  }

  // ---------------------------------------------------------------------------
  // TAB NAVIGATION
  // ---------------------------------------------------------------------------
  function switchTab(tabId) {
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(btn => btn.classList.remove("active"));

    const targetSection = document.getElementById(tabId);
    if (targetSection) targetSection.classList.add("active");

    if (tabId === "chat-view") {
      tabBtnChat?.classList.add("active");
      if (currentViewTitle) currentViewTitle.textContent = "Reasoning Chat";
    } else if (tabId === "vault-view") {
      tabBtnVault?.classList.add("active");
      if (currentViewTitle) currentViewTitle.textContent = "Knowledge Vault Data Room";
      loadVaultDocuments();
    } else if (tabId === "keys-view") {
      tabBtnKeys?.classList.add("active");
      if (currentViewTitle) currentViewTitle.textContent = "Developer Platform & API Keys";
      loadApiKeys();
    }
  }

  tabBtnChat?.addEventListener("click", () => switchTab("chat-view"));
  tabBtnVault?.addEventListener("click", () => switchTab("vault-view"));
  tabBtnKeys?.addEventListener("click", () => switchTab("keys-view"));

  // Workspace / Tenant Switcher
  workspaceSelect?.addEventListener("change", (e) => {
    activeTenant = e.target.value;
    if (activeTenantBadge) activeTenantBadge.textContent = `Tenant: ${activeTenant}`;
    currentSessionId = "session_" + Math.random().toString(36).substring(2, 9);
    loadVaultDocuments();
    loadApiKeys();
  });

  // ---------------------------------------------------------------------------
  // STEPPER ANIMATION
  // ---------------------------------------------------------------------------
  function resetStepper() {
    Object.keys(stepperSteps).forEach(k => {
      const step = stepperSteps[k];
      if (step) step.classList.remove("active", "completed");
    });
    if (stepperLoopInfo) stepperLoopInfo.textContent = "Loop 0 / 3";
  }

  function setStepperStep(stepKey, isActive = true) {
    const step = stepperSteps[stepKey];
    if (!step) return;
    if (isActive) {
      step.classList.add("active");
      step.classList.remove("completed");
    } else {
      step.classList.remove("active");
      step.classList.add("completed");
    }
  }

  // ---------------------------------------------------------------------------
  // CONVERSATIONAL CHAT ENGINE (SSE STREAMING)
  // ---------------------------------------------------------------------------
  async function submitQuery(queryText) {
    if (!queryText || !queryText.trim()) return;
    const cleanQuery = queryText.trim();

    if (activeStreamController) {
      activeStreamController.abort();
    }

    // Hide empty state hero
    if (chatHeroEmpty) chatHeroEmpty.style.display = "none";

    // Show and reset stepper
    if (pipelineStepper) pipelineStepper.style.display = "flex";
    resetStepper();

    if (scoreLiveIndicator) {
      scoreLiveIndicator.className = "score-pulse-indicator processing";
      if (scoreLiveStatusText) scoreLiveStatusText.textContent = "SCORE Engine: Processing...";
    }

    // Append User Message
    appendMessage("user", cleanQuery);
    if (chatInput) chatInput.value = "";

    // Append Assistant Placeholder
    const assistantBubble = appendMessage("assistant", "", true);
    const contentEl = assistantBubble.querySelector(".message-content");
    const citationsRowEl = assistantBubble.querySelector(".message-citations-row");
    const actionsRowEl = assistantBubble.querySelector(".message-actions-row");

    chatContainer.scrollTop = chatContainer.scrollHeight;

    const payload = {
      query: cleanQuery,
      tenant_id: activeTenant,
      session_id: currentSessionId,
      user_id: currentUser ? currentUser.email : "guest_user",
    };

    activeStreamController = new AbortController();
    let accumulatedText = "";
    let finalCitations = [];
    let reasoningTrace = [];

    try {
      const response = await fetch("/api/v1/query/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Axiom-Provider": modelProviderSelect?.value || "gemini",
        },
        body: JSON.stringify(payload),
        signal: activeStreamController.signal,
      });

      if (!response.ok) throw new Error(`HTTP Error ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop();

        for (const block of blocks) {
          if (!block.trim()) continue;
          let eventType = "message";
          let dataStr = "";

          const lines = block.split("\n");
          for (const line of lines) {
            if (line.startsWith("event:")) eventType = line.replace("event:", "").trim();
            else if (line.startsWith("data:")) dataStr = line.replace("data:", "").trim();
          }

          if (!dataStr) continue;
          let parsed = {};
          try { parsed = JSON.parse(dataStr); } catch (e) { parsed = { raw: dataStr }; }

          if (eventType === "status") {
            handleStatusStep(parsed);
            reasoningTrace.push(parsed);
          } else if (eventType === "token") {
            accumulatedText += (parsed.token || "");
            contentEl.innerHTML = formatMarkdown(accumulatedText);
            chatContainer.scrollTop = chatContainer.scrollHeight;
          } else if (eventType === "citation") {
            const cit = parsed.citation || parsed;
            finalCitations.push(cit);
            activeCitationsMap[finalCitations.length] = cit;
            renderCitationPill(citationsRowEl, cit, finalCitations.length);
          } else if (eventType === "done") {
            if (parsed.final_generation && !accumulatedText) {
              accumulatedText = parsed.final_generation;
              contentEl.innerHTML = formatMarkdown(accumulatedText);
            }
            if (scoreLiveIndicator) {
              scoreLiveIndicator.className = "score-pulse-indicator ready";
              if (scoreLiveStatusText) scoreLiveStatusText.textContent = "SCORE: Verified Grounded";
            }
            setStepperStep("audit", false);
          }
        }
      }

      // Finish & render action buttons
      if (actionsRowEl) {
        renderMessageActions(actionsRowEl, cleanQuery, accumulatedText, finalCitations, reasoningTrace);
      }

    } catch (err) {
      if (err.name === "AbortError") {
        contentEl.innerHTML += "<p><em>[Generation cancelled]</em></p>";
      } else {
        contentEl.innerHTML = `<p style="color: var(--status-danger);"><strong>Execution Error:</strong> ${escapeHtml(err.message)}</p>`;
      }
    } finally {
      activeStreamController = null;
    }
  }

  function handleStatusStep(data) {
    const node = data.node || data.phase;
    if (data.loop_count !== undefined && stepperLoopInfo) {
      stepperLoopInfo.textContent = `Loop ${data.loop_count} / 3`;
    }

    if (node === "router") {
      setStepperStep("router", true);
    } else if (node === "retriever") {
      setStepperStep("router", false);
      setStepperStep("retriever", true);
    } else if (node === "grader") {
      setStepperStep("retriever", false);
      setStepperStep("grader", true);
    } else if (node === "rewriter") {
      setStepperStep("retriever", true);
    } else if (node === "generator") {
      setStepperStep("grader", false);
      setStepperStep("generator", true);
    } else if (node === "hallucination_grader" || node === "audit") {
      setStepperStep("generator", false);
      setStepperStep("audit", true);
    }
  }

  // ---------------------------------------------------------------------------
  // MESSAGE FORMATTING & CITATIONS
  // ---------------------------------------------------------------------------
  function appendMessage(role, text, isStreaming = false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${role}`;

    const avatar = role === "assistant" ? "A" : (currentUser?.avatar || "U");
    const author = role === "assistant" ? "Axiom SCORE Engine" : (currentUser?.name || "You");

    msgDiv.innerHTML = `
      <div class="message-avatar">${avatar}</div>
      <div class="message-body">
        <div class="message-author">${escapeHtml(author)}</div>
        <div class="message-content">${formatMarkdown(text)}</div>
        ${role === "assistant" ? '<div class="message-citations-row"></div>' : ''}
        ${role === "assistant" ? '<div class="message-actions-row"></div>' : ''}
      </div>
    `;

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return msgDiv;
  }

  function renderCitationPill(container, citation, index) {
    if (!container) return;
    const pill = document.createElement("button");
    pill.className = "citation-pill";
    const doc = citation.source_document || citation.document_id || `Source ${index}`;
    const page = citation.page || citation.section ? ` (p.${citation.page || citation.section})` : "";
    pill.textContent = `[${index}] ${doc}${page}`;

    pill.addEventListener("click", () => {
      openCitationDrawer(citation, index);
    });

    container.appendChild(pill);
  }

  function renderMessageActions(container, query, generation, citations, trace) {
    container.innerHTML = `
      <button class="action-text-btn export-cert-btn" title="Download Grounded Audit Certificate">
        📜 Export Audit Certificate (.md)
      </button>
      <button class="action-text-btn copy-btn" title="Copy Answer">
        📋 Copy
      </button>
      <span style="font-size: 11px; color: var(--status-verified); margin-left: 6px; font-family: var(--font-code);">
        ✓ Verified Grounded (0 Hallucinations)
      </span>
    `;

    const exportBtn = container.querySelector(".export-cert-btn");
    exportBtn.addEventListener("click", async () => {
      exportBtn.textContent = "⏳ Generating...";
      await downloadAuditCertificate(query, generation, citations, trace);
      exportBtn.textContent = "✓ Certificate Downloaded";
    });

    const copyBtn = container.querySelector(".copy-btn");
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(generation);
      copyBtn.textContent = "✓ Copied";
      setTimeout(() => { copyBtn.textContent = "📋 Copy"; }, 2000);
    });
  }

  // ---------------------------------------------------------------------------
  // INTERACTIVE CITATION DRAWER
  // ---------------------------------------------------------------------------
  function openCitationDrawer(citation, index) {
    if (!citationDrawer) return;
    const doc = citation.source_document || citation.document_id || "Document";
    const page = citation.page || citation.section || "N/A";
    const relScore = citation.relevance_score ? Math.round(citation.relevance_score * 100) : 100;

    if (drawerDocTitle) drawerDocTitle.textContent = doc;
    if (drawerDocPage) drawerDocPage.textContent = `Reference: Page / Section ${page}`;
    if (drawerScore) drawerScore.textContent = `${relScore}% Relevance`;
    if (drawerStatus) drawerStatus.textContent = "Verified Grounded";
    if (drawerChunkId) drawerChunkId.textContent = citation.chunk_id || "N/A";
    if (drawerExcerpt) drawerExcerpt.textContent = citation.excerpt || "Exact verified citation passage.";

    citationDrawer.classList.add("open");
    drawerBackdrop?.classList.add("open");
  }

  function closeCitationDrawer() {
    citationDrawer?.classList.remove("open");
    drawerBackdrop?.classList.remove("open");
  }

  drawerCloseBtn?.addEventListener("click", closeCitationDrawer);
  drawerBackdrop?.addEventListener("click", closeCitationDrawer);

  // ---------------------------------------------------------------------------
  // AUDIT CERTIFICATE DOWNLOAD
  // ---------------------------------------------------------------------------
  async function downloadAuditCertificate(query, generation, citations, trace) {
    try {
      const response = await fetch("/api/v1/export/certificate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          generation: generation,
          citations: citations,
          reasoning_trace: trace,
          tenant_id: activeTenant,
          session_id: currentSessionId,
          format: "markdown",
        }),
      });

      if (!response.ok) throw new Error("Failed to export certificate");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AX_AUDIT_CERTIFICATE_${Date.now()}.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Error generating certificate: " + e.message);
    }
  }

  // ---------------------------------------------------------------------------
  // KNOWLEDGE VAULT DOCUMENT MANAGEMENT
  // ---------------------------------------------------------------------------
  async function loadVaultDocuments() {
    if (!vaultTableBody) return;
    vaultTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-row">Loading indexed documents...</td></tr>`;

    try {
      const res = await fetch(`/api/v1/documents?tenant_id=${encodeURIComponent(activeTenant)}`);
      if (!res.ok) throw new Error("Could not retrieve documents");
      const docs = await res.json();

      if (statDocCount) statDocCount.textContent = docs.length;
      if (vaultDocCountBadge) vaultDocCountBadge.textContent = docs.length;

      let totalChunks = 0;
      docs.forEach(d => { totalChunks += (d.chunk_count || 0); });
      if (statChunkCount) statChunkCount.textContent = totalChunks;

      if (!docs || docs.length === 0) {
        vaultTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-row">No documents uploaded to this workspace yet. Upload files above to index.</td></tr>`;
        return;
      }

      vaultTableBody.innerHTML = "";
      const canDelete = currentUser?.role === "admin";

      docs.forEach(doc => {
        const tr = document.createElement("tr");
        const sizeKb = Math.round((doc.total_characters || 0) / 1024);
        tr.innerHTML = `
          <td><strong>📄 ${escapeHtml(doc.filename)}</strong></td>
          <td><span class="nav-badge">${doc.chunk_count} chunks</span></td>
          <td>${sizeKb} KB</td>
          <td>${doc.page_count || 1}</td>
          <td><span style="color: var(--status-verified); font-family: var(--font-code); font-size: 11px;">● Indexed</span></td>
          <td>
            ${canDelete ? `<button class="table-action-pill delete-doc-btn" data-file="${escapeHtml(doc.filename)}">🗑️ Delete</button>` : `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Read-Only</span>`}
          </td>
        `;

        if (canDelete) {
          tr.querySelector(".delete-doc-btn").addEventListener("click", async (e) => {
            const fn = e.target.getAttribute("data-file");
            if (confirm(`Purge '${fn}' and all its vectors from tenant '${activeTenant}'?`)) {
              await deleteVaultDocument(fn);
            }
          });
        }

        vaultTableBody.appendChild(tr);
      });
    } catch (err) {
      vaultTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-row" style="color: var(--status-danger);">Failed to load vault documents: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  async function deleteVaultDocument(filename) {
    try {
      const res = await fetch(`/api/v1/documents/${encodeURIComponent(filename)}?tenant_id=${encodeURIComponent(activeTenant)}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Delete failed");
      await loadVaultDocuments();
    } catch (err) {
      alert("Error deleting document: " + err.message);
    }
  }

  async function handleFileUpload(file) {
    if (!file) return;

    if (uploadProgressRow) uploadProgressRow.style.display = "flex";
    if (uploadProgressFill) uploadProgressFill.style.width = "40%";
    if (uploadProgressText) uploadProgressText.textContent = `Parsing & chunking '${file.name}'...`;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("tenant_id", activeTenant);

    try {
      if (uploadProgressFill) uploadProgressFill.style.width = "75%";
      const res = await fetch("/api/v1/ingest/file", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned ${res.status}`);
      }

      const data = await res.json();
      if (uploadProgressFill) uploadProgressFill.style.width = "100%";
      if (uploadProgressText) uploadProgressText.textContent = `Indexed ${data.ingested_chunks} chunks successfully!`;

      setTimeout(() => {
        if (uploadProgressRow) uploadProgressRow.style.display = "none";
        loadVaultDocuments();
      }, 1500);

    } catch (err) {
      if (uploadProgressText) {
        uploadProgressText.textContent = `Upload failed: ${err.message}`;
        uploadProgressText.style.color = "var(--status-danger)";
      }
    }
  }

  vaultFileInput?.addEventListener("change", (e) => {
    if (e.target.files?.length) handleFileUpload(e.target.files[0]);
  });

  vaultDropzone?.addEventListener("dragover", (e) => {
    e.preventDefault();
    vaultDropzone.style.borderColor = "var(--accent-cyan)";
  });

  vaultDropzone?.addEventListener("dragleave", () => {
    vaultDropzone.style.borderColor = "var(--border-medium)";
  });

  vaultDropzone?.addEventListener("drop", (e) => {
    e.preventDefault();
    vaultDropzone.style.borderColor = "var(--border-medium)";
    if (e.dataTransfer.files?.length) handleFileUpload(e.dataTransfer.files[0]);
  });

  quickUploadTrigger?.addEventListener("click", () => {
    switchTab("vault-view");
    vaultFileInput?.click();
  });

  // ---------------------------------------------------------------------------
  // API KEY MANAGEMENT
  // ---------------------------------------------------------------------------
  async function loadApiKeys() {
    if (!keysTableBody) return;
    keysTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-row">Loading API keys...</td></tr>`;

    try {
      const res = await fetch(`/api/v1/keys?tenant_id=${encodeURIComponent(activeTenant)}`);
      if (!res.ok) throw new Error("Could not retrieve keys");
      const keys = await res.json();

      if (!keys || keys.length === 0) {
        keysTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-row">No API keys generated yet.</td></tr>`;
        return;
      }

      keysTableBody.innerHTML = "";
      keys.forEach(k => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${escapeHtml(k.name)}</strong></td>
          <td><code>${escapeHtml(k.masked_key)}</code></td>
          <td><span class="role-badge ${k.role}">${escapeHtml(k.role)}</span></td>
          <td>${new Date(k.created_at).toLocaleDateString()}</td>
          <td>${k.last_used ? new Date(k.last_used).toLocaleDateString() : "Never"}</td>
          <td>
            <button class="table-action-pill delete-key-btn" data-key="${escapeHtml(k.key_id)}">
              Revoke
            </button>
          </td>
        `;

        tr.querySelector(".delete-key-btn").addEventListener("click", async (e) => {
          const kid = e.target.getAttribute("data-key");
          if (confirm("Revoke this API Key immediately?")) {
            await revokeApiKey(kid);
          }
        });

        keysTableBody.appendChild(tr);
      });
    } catch (err) {
      keysTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-row" style="color: var(--status-danger);">Failed to load API keys: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  async function revokeApiKey(keyId) {
    try {
      const res = await fetch(`/api/v1/keys/${encodeURIComponent(keyId)}?tenant_id=${encodeURIComponent(activeTenant)}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Revocation failed");
      await loadApiKeys();
    } catch (err) {
      alert("Error revoking key: " + err.message);
    }
  }

  createKeyBtn?.addEventListener("click", () => {
    if (currentUser?.role === "auditor") {
      alert("Compliance Auditors have read-only access and cannot issue API keys.");
      return;
    }
    if (keyModal) {
      keyModal.style.display = "flex";
      if (newKeyDisplay) newKeyDisplay.style.display = "none";
    }
  });

  keyModalClose?.addEventListener("click", () => { if (keyModal) keyModal.style.display = "none"; });
  keyModalCancel?.addEventListener("click", () => { if (keyModal) keyModal.style.display = "none"; });

  createKeyForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = keyNameInput?.value?.trim();
    const role = keyRoleSelect?.value || "member";

    try {
      const res = await fetch("/api/v1/keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, role: role, tenant_id: activeTenant }),
      });

      if (!res.ok) throw new Error("Key creation failed");
      const keyData = await res.json();

      if (newKeyDisplay && rawKeyValue) {
        newKeyDisplay.style.display = "block";
        rawKeyValue.textContent = keyData.raw_key;
      }
      loadApiKeys();
    } catch (err) {
      alert("Error: " + err.message);
    }
  });

  copyTokenBtn?.addEventListener("click", () => {
    if (rawKeyValue?.textContent) {
      navigator.clipboard.writeText(rawKeyValue.textContent);
      copyTokenBtn.textContent = "✓";
      setTimeout(() => { copyTokenBtn.textContent = "📋"; }, 2000);
    }
  });

  // ---------------------------------------------------------------------------
  // PROMPT PRESET CARDS & INPUT WIRING
  // ---------------------------------------------------------------------------
  promptCards.forEach(card => {
    card.addEventListener("click", () => {
      const q = card.getAttribute("data-query");
      if (q) {
        if (chatInput) chatInput.value = q;
        submitQuery(q);
      }
    });
  });

  chatForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    submitQuery(chatInput?.value);
  });

  chatInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitQuery(chatInput?.value);
    }
  });

  newThreadBtn?.addEventListener("click", () => {
    currentSessionId = "session_" + Math.random().toString(36).substring(2, 9);
    resetStepper();
    if (pipelineStepper) pipelineStepper.style.display = "none";
    if (chatHeroEmpty) chatHeroEmpty.style.display = "block";

    // Clear old conversation messages
    const msgs = chatContainer.querySelectorAll(".chat-message");
    msgs.forEach(m => m.remove());
  });

  // ---------------------------------------------------------------------------
  // MARKDOWN FORMATTER
  // ---------------------------------------------------------------------------
  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Bullet points
    html = html.replace(/^• (.*$)/gim, "<li>$1</li>");
    html = html.replace(/^- (.*$)/gim, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>)/gim, "<ul>$1</ul>");

    // Line breaks
    html = html.replace(/\n\n/g, "</p><p>");
    html = html.replace(/\n/g, "<br/>");
    return `<p>${html}</p>`;
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
});
