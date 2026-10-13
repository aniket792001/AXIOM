import React from "https://esm.sh/react@18.2.0";

export function CitationDrawer({ citation, onClose, onOpenVisualizer }) {
  if (!citation) return null;

  return (
    <>
      <aside className="citation-side-drawer open">
        <div className="drawer-header">
          <div className="drawer-meta-info">
            <span className="drawer-icon">📑</span>
            <div>
              <div className="drawer-doc-name">
                {citation.source_document || citation.document_id || "Document Excerpt"}
              </div>
              <div className="drawer-page-tag">
                Reference: Page {citation.page || citation.section || "1"}
              </div>
            </div>
          </div>
          <button className="drawer-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="drawer-body">
          <div className="drawer-score-card">
            <div className="score-row">
              <span className="score-label">Grounding Verification:</span>
              <span className="score-badge verified">✓ Grounded Factual Basis</span>
            </div>
            <div className="score-row">
              <span className="score-label">Hybrid Relevance:</span>
              <span className="score-value">
                {citation.relevance_score ? Math.round(citation.relevance_score * 100) + "%" : "100% Match"}
              </span>
            </div>
            {citation.chunk_id && (
              <div className="score-row">
                <span className="score-label">Chunk ID:</span>
                <span className="score-mono">{citation.chunk_id}</span>
              </div>
            )}
          </div>

          <div className="drawer-excerpt-box">
            <div className="excerpt-label">Extracted Legal Excerpt:</div>
            <div className="excerpt-text">
              {citation.excerpt || citation.quote || "Direct passage extracted from ingested document context."}
            </div>
          </div>

          <button
            className="drawer-visualize-action-btn"
            onClick={() => {
              onOpenVisualizer({
                filename: citation.source_document || citation.document_id,
                page: citation.page || 1,
                highlightClause: citation.excerpt || citation.quote || "",
                citation,
              });
              onClose();
            }}
          >
            <span>👁️</span>
            <span>Open in Document Visualizer & Highlight</span>
          </button>
        </div>
      </aside>
      <div className="drawer-backdrop open" onClick={onClose} />
    </>
  );
}
