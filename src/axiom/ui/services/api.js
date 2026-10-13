/**
 * Axiom Enterprise API Client
 * Clean, zero-DOM-dependency API layer.
 * 100% portable to React Native / Expo.
 */

const BASE_URL = "";

export const api = {
  // ---------------------------------------------------------------------------
  // AUTHENTICATION & USER PROFILE
  // ---------------------------------------------------------------------------
  async login({ email, password, role }) {
    const res = await fetch(`${BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Authentication failed");
    }
    return res.json();
  },

  async register({ email, name, password, role, title, default_tenant }) {
    const res = await fetch(`${BASE_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        name,
        password,
        role: role || "analyst",
        title: title || "Enterprise User",
        default_tenant: default_tenant || "default_tenant",
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  },

  async getProfile(token) {
    const res = await fetch(`${BASE_URL}/api/v1/auth/me?token=${encodeURIComponent(token || "")}`, {
      headers: { Authorization: `Bearer ${token || ""}` },
    });
    if (!res.ok) throw new Error("Failed to fetch user profile");
    return res.json();
  },

  async updateProfile(token, profileData) {
    const res = await fetch(`${BASE_URL}/api/v1/auth/me?token=${encodeURIComponent(token || "")}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token || ""}`,
      },
      body: JSON.stringify(profileData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Profile update failed");
    }
    return res.json();
  },

  async changePassword(token, currentPassword, newPassword) {
    const res = await fetch(`${BASE_URL}/api/v1/auth/change-password?token=${encodeURIComponent(token || "")}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token || ""}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Password change failed");
    }
    return res.json();
  },

  // ---------------------------------------------------------------------------
  // REAL-TIME SSE QUERY STREAMING
  // ---------------------------------------------------------------------------
  async streamQuery({ query, tenantId, sessionId, userId, provider = "gemini", onStatus, onToken, onAnswer, onFallback, onError, onDone }) {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/query/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Axiom-Provider": provider,
        },
        body: JSON.stringify({
          query,
          tenant_id: tenantId || "default_tenant",
          session_id: sessionId,
          user_id: userId || "analyst@axiom.ai",
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      const dispatchEvent = (eventType, dataStr) => {
        if (!dataStr) return;
        let parsed = {};
        try {
          parsed = JSON.parse(dataStr);
        } catch {
          parsed = { raw: dataStr };
        }

        if (eventType === "status" && onStatus) onStatus(parsed);
        else if (eventType === "token" && onToken) onToken(parsed.token !== undefined ? parsed.token : "");
        else if (eventType === "answer" && onAnswer) onAnswer(parsed);
        else if (eventType === "fallback" && onFallback) onFallback(parsed);
        else if (eventType === "error" && onError) onError(parsed.error || "Reasoning error");
        else if (eventType === "done" && onDone) onDone(parsed);
      };

      const processBlock = (block) => {
        if (!block.trim()) return;
        let eventType = "message";
        const dataLines = [];

        for (const line of block.split("\n")) {
          const trimmed = line.trim();
          if (trimmed.startsWith("event:")) {
            eventType = trimmed.slice(6).trim();
          } else if (trimmed.startsWith("data:")) {
            dataLines.push(trimmed.slice(5).trim());
          }
        }

        const dataStr = dataLines.join("\n");
        dispatchEvent(eventType, dataStr);
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // Normalize CRLF from HTTP/Windows headers to standard LF
        buffer = buffer.replace(/\r\n/g, "\n");
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          processBlock(block);
        }
      }

      // Process any remaining bytes in final buffer after stream closes
      if (buffer && buffer.trim()) {
        processBlock(buffer.trim());
      }
    } catch (err) {
      if (onError) onError(err.message);
    }
  },

  // ---------------------------------------------------------------------------
  // KNOWLEDGE VAULT & DOCUMENTS
  // ---------------------------------------------------------------------------
  async getVaultDocuments(tenantId) {
    const res = await fetch(`${BASE_URL}/api/v1/documents?tenant_id=${encodeURIComponent(tenantId || "default_tenant")}`);
    if (!res.ok) throw new Error("Failed to load vault documents");
    return res.json();
  },

  async uploadDocument(file, tenantId) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("tenant_id", tenantId || "default_tenant");

    const res = await fetch(`${BASE_URL}/api/v1/ingest/file`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Document ingestion failed");
    }
    return res.json();
  },

  async deleteDocument(filename, tenantId) {
    const res = await fetch(`${BASE_URL}/api/v1/documents/${encodeURIComponent(filename)}?tenant_id=${encodeURIComponent(tenantId || "default_tenant")}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return res.json();
  },

  async viewDocument(filename) {
    const res = await fetch(`${BASE_URL}/api/v1/documents/${encodeURIComponent(filename)}/view`);
    if (!res.ok) throw new Error("Document view unavailable");
    return res.json();
  },

  // ---------------------------------------------------------------------------
  // CONTRACT CONTRADICTION & DIFF
  // ---------------------------------------------------------------------------
  async analyzeContradiction({ contractA, contractB, tenantId, modelProvider = "gemini" }) {
    const res = await fetch(`${BASE_URL}/api/v1/contradiction/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Axiom-Provider": modelProvider,
      },
      body: JSON.stringify({
        contract_a: contractA,
        contract_b: contractB,
        tenant_id: tenantId || "default_tenant",
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Contradiction analysis failed");
    }
    return res.json();
  },

  async getDemoContractPairs() {
    const res = await fetch(`${BASE_URL}/api/v1/contradiction/demo-pairs`);
    if (!res.ok) throw new Error("Failed to load demo contracts");
    return res.json();
  },

  // ---------------------------------------------------------------------------
  // RAGAS BENCHMARKS & EVALUATION
  // ---------------------------------------------------------------------------
  async getBenchmarkSummary() {
    const res = await fetch(`${BASE_URL}/api/v1/benchmark/summary`);
    if (!res.ok) throw new Error("Failed to load benchmark summary");
    return res.json();
  },

  async getBenchmarkCases() {
    const res = await fetch(`${BASE_URL}/api/v1/benchmark/cases`);
    if (!res.ok) throw new Error("Failed to load benchmark test cases");
    return res.json();
  },

  async runBenchmarkLive() {
    const res = await fetch(`${BASE_URL}/api/v1/benchmark/run`, { method: "POST" });
    if (!res.ok) throw new Error("Live benchmark evaluation failed");
    return res.json();
  },

  // ---------------------------------------------------------------------------
  // SESSIONS, AUDIT & EXPORT
  // ---------------------------------------------------------------------------
  async getSessions(tenantId) {
    const res = await fetch(`${BASE_URL}/api/v1/sessions?tenant_id=${encodeURIComponent(tenantId || "default_tenant")}`);
    if (!res.ok) return [];
    return res.json();
  },

  async deleteSession(sessionId) {
    const res = await fetch(`${BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE" });
    return res.ok;
  },

  async getAuditHistory(tenantId) {
    const res = await fetch(`${BASE_URL}/api/v1/history/audit?tenant_id=${encodeURIComponent(tenantId || "default_tenant")}`);
    if (!res.ok) return { records: [], total: 0 };
    return res.json();
  },

  async exportCertificate({ query, generation, citations, tenantId, sessionId, format = "pdf" }) {
    let endpoint = `${BASE_URL}/api/v1/export/pdf`;
    if (format === "excel" || format === "xlsx") endpoint = `${BASE_URL}/api/v1/export/excel`;
    else if (format === "markdown") endpoint = `${BASE_URL}/api/v1/export/certificate`;

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        generation,
        citations: citations || [],
        tenant_id: tenantId || "default_tenant",
        session_id: sessionId || "session_export",
        format,
      }),
    });

    if (!res.ok) throw new Error("Certificate export failed");
    return res.blob();
  },

  async verifyCertificate(payload) {
    const res = await fetch(`${BASE_URL}/api/v1/export/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  },
};
