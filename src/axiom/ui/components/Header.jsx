import React from "https://esm.sh/react@18.2.0";

export function Header({
  activeTab,
  activeTenant,
  setActiveTenant,
  theme,
  setTheme,
  modelProvider,
  setModelProvider,
  user,
  onOpenProfile,
  isProcessing,
}) {
  const tabTitles = {
    chat: { title: "Reasoning Chat", subtitle: "SCORE Cyclical Verification Engine" },
    vault: { title: "Knowledge Vault", subtitle: "Partitioned Multi-Tenant Data Room" },
    contradiction: { title: "Contract Contradiction Studio", subtitle: "Merger Doctrine Precedence Resolver" },
    benchmark: { title: "RAGAS Quality Benchmarks", subtitle: "Golden Dataset Evaluation Suite" },
    history: { title: "Customer Audit History", subtitle: "Cryptographic Audit Log & Verification" },
  };

  const currentMeta = tabTitles[activeTab] || tabTitles.chat;

  return (
    <header className="axiom-topbar">
      <div className="topbar-breadcrumb-zone">
        <div className="breadcrumb-nav">
          <span className="breadcrumb-root">Axiom</span>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">{currentMeta.title}</span>
        </div>
        <div className="topbar-subtitle">{currentMeta.subtitle}</div>
      </div>

      <div className="topbar-controls">
        {/* Tenant Partition Selector */}
        <div className="tenant-badge-selector">
          <span className="tenant-icon">🏢</span>
          <select
            className="tenant-select"
            value={activeTenant}
            onChange={(e) => setActiveTenant(e.target.value)}
          >
            <option value="default_tenant">Master Enterprise Vault</option>
            <option value="legal_contracts">Legal & Compliance Vault</option>
            <option value="financial_filings">Financial Filings (10-K/10-Q)</option>
          </select>
        </div>

        {/* Model Provider */}
        <select
          className="model-select"
          value={modelProvider}
          onChange={(e) => setModelProvider(e.target.value)}
        >
          <option value="gemini">Google Gemini 1.5</option>
          <option value="openai">OpenAI GPT-4o</option>
          <option value="anthropic">Claude 3.5 Sonnet</option>
        </select>

        {/* Engine Status Pulse */}
        <div className={`engine-status-chip ${isProcessing ? "active" : "ready"}`}>
          <span className="status-dot" />
          <span>{isProcessing ? "Reasoning & Grading..." : "SCORE Grounded"}</span>
        </div>

        {/* Theme Toggle */}
        <button
          className="theme-btn"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          title="Toggle Light / Dark Mode"
        >
          {theme === "light" ? "🌙 Dark" : "☀️ Light"}
        </button>
      </div>
    </header>
  );
}
