import React from "https://esm.sh/react@18.2.0";

export function DiffMatrixScreen({
  contractA,
  setContractA,
  contractB,
  setContractB,
  analysisResult,
  loading,
  error,
  onLoadDemo,
  onRunAnalysis,
  onOpenVisualizer,
}) {
  return (
    <div className="diff-screen-canvas">
      {/* Studio Header */}
      <div className="screen-header-banner">
        <div>
          <h2 className="screen-title">⚖️ Contract Contradiction & Precedence Matrix</h2>
          <p className="screen-desc">
            Compare two versions of an agreement (e.g. Master Agreement vs. Later Amendment). Axiom identifies direct contradictions, modifications, and applies the <strong>Merger Doctrine</strong> to determine legal precedence.
          </p>
        </div>
        <div className="header-action-group">
          <button className="secondary-action-btn" onClick={onLoadDemo}>
            📑 Load Demo M&A Pair
          </button>
          <button
            className="primary-action-btn"
            onClick={onRunAnalysis}
            disabled={loading || !contractA.trim() || !contractB.trim()}
          >
            {loading ? "Analyzing Matrix..." : "Run Contradiction Diff →"}
          </button>
        </div>
      </div>

      {error && <div className="error-alert-bar">⚠️ {error}</div>}

      {/* Side-by-Side Document Textboxes */}
      <div className="diff-input-columns-grid">
        <div className="diff-column-card">
          <div className="column-card-header">
            <span className="card-tag base">Document 1: Original Agreement</span>
            <span className="card-subtitle">Base Master Services Agreement (e.g. 2022)</span>
          </div>
          <textarea
            className="diff-textarea"
            placeholder="Paste original contract text here..."
            value={contractA}
            onChange={(e) => setContractA(e.target.value)}
          />
        </div>

        <div className="diff-column-card">
          <div className="column-card-header">
            <span className="card-tag amendment">Document 2: Superseding Amendment</span>
            <span className="card-subtitle">Later Amendment / Addendum (e.g. 2024)</span>
          </div>
          <textarea
            className="diff-textarea"
            placeholder="Paste later amendment or addendum text here..."
            value={contractB}
            onChange={(e) => setContractB(e.target.value)}
          />
        </div>
      </div>

      {/* Analysis Results View */}
      {analysisResult && (
        <div className="analysis-results-section">
          {/* Executive Ruling Banner */}
          <div className="precedence-ruling-banner">
            <div className="ruling-badge">⚖️ LEGAL PRECEDENCE RULING</div>
            <div className="ruling-headline">{analysisResult.precedence_ruling}</div>
            <div className="ruling-details">{analysisResult.executive_summary}</div>
          </div>

          {/* Clause Diff Grid */}
          <h3 className="section-title">Clause-by-Clause Contradiction Breakdown</h3>
          <div className="contradiction-cards-grid">
            {analysisResult.clause_contradictions?.map((c, idx) => (
              <div key={idx} className={`contradiction-item-card ${c.severity?.toLowerCase() || "moderate"}`}>
                <div className="clause-card-header">
                  <span className="clause-topic">{c.clause_topic || "Contract Term"}</span>
                  <span className={`status-badge ${c.status?.toLowerCase() || "modified"}`}>
                    {c.status || "MODIFIED"}
                  </span>
                </div>

                <div className="clause-comparison-grid">
                  <div className="term-box original">
                    <div className="term-label">Document 1 Term:</div>
                    <div className="term-text">{c.doc_a_term}</div>
                  </div>
                  <div className="term-box superseding">
                    <div className="term-label">Document 2 Term:</div>
                    <div className="term-text">{c.doc_b_term}</div>
                  </div>
                </div>

                <div className="clause-resolution-box">
                  <span className="resolution-label">Precedence Resolution:</span>
                  <span className="resolution-text">{c.legal_resolution}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
