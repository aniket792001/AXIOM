import React, { useState, useRef, useEffect } from "https://esm.sh/react@18.2.0";

export function ChatScreen({
  messages,
  isProcessing,
  activeStep,
  loopCount,
  onSend,
  onReset,
  onSelectCitation,
  onExportCert,
}) {
  const [inputQuery, setInputQuery] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || isProcessing) return;
    onSend(inputQuery);
    setInputQuery("");
  };

  const presets = [
    {
      icon: "⚖️",
      title: "Contract Amendment Trap",
      desc: "Resolves conflicting terms across superseding 2024 addendum vs 2022 MSA.",
      query: "What is the liability cap and termination notice period for Tier 2 enterprise customers?",
    },
    {
      icon: "📑",
      title: "Multi-Hop Cross Reference",
      desc: "Traverses separated document definitions and executive equity cliffs.",
      query: "What is the vesting schedule cliff for Group C executives under the equity plan?",
    },
    {
      icon: "📊",
      title: "Financial Table & Footnote Audit",
      desc: "Synthesizes fine-print operating metrics without separating footnote disclosures.",
      query: "What was the recurring operational operating income in Q3 2023 excluding one-off divestitures?",
    },
    {
      icon: "🛡️",
      title: "Epistemic Humility (Zero Bluff)",
      desc: "Tests self-correction by refusing to hallucinate when context is absent.",
      query: "What is the penalty fee if the vendor fails SOC-2 compliance in Q4?",
    },
  ];

  return (
    <div className="chat-screen-canvas">
      {/* Messages Scroll Container */}
      <div className="chat-messages-scroll">
        {messages.length === 0 ? (
          <div className="chat-empty-hero">
            <div className="hero-kicker-badge">⚡ Self-Correcting Reasoning Engine (SCORE)</div>
            <h1 className="hero-heading">High-Stakes Contract & Financial Truth.</h1>
            <p className="hero-description">
              Ask complex multi-document questions. Every claim is verified by dual grading loops, backed by clause-level citations, and governed by epistemic humility.
            </p>

            <div className="hero-presets-grid">
              {presets.map((p, idx) => (
                <div
                  key={idx}
                  className="preset-card"
                  onClick={() => onSend(p.query)}
                >
                  <div className="preset-card-header">
                    <span className="preset-icon">{p.icon}</span>
                    <span className="preset-title">{p.title}</span>
                  </div>
                  <p className="preset-desc">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-thread-container">
            {messages.map((m) => (
              <div key={m.id} className={`chat-message-bubble ${m.role}`}>
                <div className="message-header-line">
                  <div className="author-badge">
                    {m.role === "assistant" ? "🤖 AXIOM SCORE" : "👤 You"}
                  </div>
                  {m.role === "assistant" && !m.isStreaming && (
                    <div className="message-export-actions">
                      <button
                        className="export-chip-btn"
                        onClick={() => onExportCert(m, "pdf")}
                        title="Download SEC Rule 17a-4 PDF Certificate"
                      >
                        📄 PDF Audit
                      </button>
                      <button
                        className="export-chip-btn"
                        onClick={() => onExportCert(m, "excel")}
                        title="Download Multi-Tab Excel Workbook"
                      >
                        📊 Excel
                      </button>
                    </div>
                  )}
                </div>

                {m.content ? (
                  <div className="message-content-text">
                    {m.content}
                  </div>
                ) : m.isStreaming ? (
                  <div className="message-streaming-loader">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="streaming-label">SCORE engine retrieving & verifying clauses...</span>
                  </div>
                ) : null}

                {m.isFallback && (
                  <div className="fallback-humility-badge">
                    🛡️ Epistemic Humility: Zero-hallucination refusal active (insufficient verified context)
                  </div>
                )}

                {/* Grounded Citation Chips */}
                {m.citations && m.citations.length > 0 && (
                  <div className="message-citations-tray">
                    <span className="citations-label">Grounded Evidence:</span>
                    <div className="citations-chips-wrap">
                      {m.citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          className="citation-chip-btn"
                          onClick={() => onSelectCitation(c)}
                        >
                          <span className="citation-chip-icon">📍</span>
                          <span>{c.source_document || c.document_id || c.doc_id || `Source [${cIdx + 1}]`}</span>
                          {(c.page || c.chunk_id) && (
                            <span className="citation-chip-page">
                              {c.page ? `p.${c.page}` : c.chunk_id.split(":").pop()}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Active Reasoning Stepper / Loader */}
            {isProcessing && (
              <div className="reasoning-stepper-card">
                <div className="stepper-header">
                  <div className="stepper-pulse-dot" />
                  <span className="stepper-title">SCORE Reasoning Loop: Phase {activeStep?.toUpperCase() || "ANALYZING"}</span>
                  <span className="stepper-loop-tag">Loop {loopCount} / 3</span>
                </div>
                <div className="stepper-progress-track">
                  <div className={`stepper-node ${activeStep === "router" ? "active" : "done"}`}>1. Router</div>
                  <div className={`stepper-node ${activeStep === "retriever" ? "active" : activeStep && activeStep !== "router" ? "done" : ""}`}>2. Hybrid Retrieval</div>
                  <div className={`stepper-node ${activeStep === "grader" ? "active" : ["generator", "audit"].includes(activeStep) ? "done" : ""}`}>3. DocGrader</div>
                  <div className={`stepper-node ${activeStep === "generator" ? "active" : activeStep === "audit" ? "done" : ""}`}>4. Synthesis</div>
                  <div className={`stepper-node ${activeStep === "audit" ? "active" : ""}`}>5. Grounding Audit</div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Query Input Dock */}
      <div className="chat-input-dock">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-text-input"
            placeholder="Ask a contractual or financial contradiction query..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isProcessing}
          />
          <button
            type="submit"
            className="chat-submit-btn"
            disabled={!inputQuery.trim() || isProcessing}
          >
            {isProcessing ? "Reasoning..." : "Send Query →"}
          </button>
          {messages.length > 0 && (
            <button
              type="button"
              className="chat-reset-btn"
              onClick={onReset}
              title="Reset conversation"
            >
              Clear
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
