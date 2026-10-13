import React, { useState, useEffect } from "https://esm.sh/react@18.2.0";
import { api } from "../services/api.js";

export function DocumentVisualizerModal({ target, onClose }) {
  const [docData, setDocData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(target?.page || 1);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!target?.filename) return;
    setLoading(true);
    api.viewDocument(target.filename)
      .then((data) => {
        setDocData(data);
        setCurrentPage(target.page || 1);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [target]);

  const totalPages = docData?.total_pages || 1;
  const pageContent = docData?.pages?.[currentPage - 1]?.text || docData?.content || "No page content available.";

  // Highlight target clause
  const renderHighlightedContent = () => {
    let text = pageContent;
    const highlightTarget = (target?.highlightClause || searchTerm || "").trim();

    if (!highlightTarget) {
      return <pre className="visualizer-raw-text">{text}</pre>;
    }

    const regex = new RegExp(`(${highlightTarget.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
    const parts = text.split(regex);

    return (
      <pre className="visualizer-raw-text">
        {parts.map((part, i) =>
          regex.test(part) ? (
            <mark key={i} className="cited-clause-mark">
              <span className="mark-label">📍 CITED IN ANSWER</span>
              {part}
            </mark>
          ) : (
            part
          )
        )}
      </pre>
    );
  };

  return (
    <div className="modal-backdrop-blur">
      <div className="visualizer-modal-dialog">
        {/* Visualizer Top Bar */}
        <div className="visualizer-header">
          <div className="visualizer-file-meta">
            <span className="visualizer-icon">📑</span>
            <div>
              <div className="visualizer-filename">{target.filename}</div>
              <div className="visualizer-doc-meta">
                Format: {docData?.format?.toUpperCase() || "DOCUMENT"} • {totalPages} {totalPages === 1 ? "Page" : "Pages"}
              </div>
            </div>
          </div>

          <div className="visualizer-toolbar">
            {/* Page Controls */}
            {totalPages > 1 && (
              <div className="toolbar-page-group">
                <button
                  className="toolbar-btn"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                >
                  ◀
                </button>
                <span className="page-indicator">Page {currentPage} of {totalPages}</span>
                <button
                  className="toolbar-btn"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                >
                  ▶
                </button>
              </div>
            )}

            {/* Zoom Controls */}
            <div className="toolbar-zoom-group">
              <button
                className="toolbar-btn"
                onClick={() => setZoomLevel((z) => Math.max(70, z - 10))}
              >
                -
              </button>
              <span className="zoom-indicator">{zoomLevel}%</span>
              <button
                className="toolbar-btn"
                onClick={() => setZoomLevel((z) => Math.min(150, z + 10))}
              >
                +
              </button>
            </div>

            {/* In-Doc Search */}
            <input
              type="text"
              className="toolbar-search-input"
              placeholder="Search in document..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <button className="visualizer-close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="visualizer-content-scroll" style={{ fontSize: `${(zoomLevel / 100) * 14}px` }}>
          {loading ? (
            <div className="visualizer-loading-state">Rendering document pages...</div>
          ) : error ? (
            <div className="visualizer-error-state">⚠️ {error}</div>
          ) : (
            renderHighlightedContent()
          )}
        </div>
      </div>
    </div>
  );
}
