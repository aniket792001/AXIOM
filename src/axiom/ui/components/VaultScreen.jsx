import React, { useRef } from "https://esm.sh/react@18.2.0";

export function VaultScreen({
  vaultDocs,
  loading,
  uploadStatus,
  onUpload,
  onDelete,
  onOpenVisualizer,
  activeTenant,
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  };

  return (
    <div className="vault-screen-canvas">
      {/* Vault Header Banner */}
      <div className="screen-header-banner">
        <div>
          <h2 className="screen-title">Partitioned Knowledge Vault</h2>
          <p className="screen-desc">
            Isolated enterprise data room for <strong>{activeTenant}</strong>. Uploaded files are chunked, densely vector-indexed, and sparse-lexical indexed for hybrid retrieval.
          </p>
        </div>
        <div className="screen-stats-badge">
          <span className="stats-number">{vaultDocs.length}</span>
          <span className="stats-label">Indexed Documents</span>
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        className="upload-dropzone-card"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={handleFileChange}
          accept=".pdf,.txt,.md,.json"
        />
        <div className="dropzone-icon">📁</div>
        <div className="dropzone-text-main">Click to upload contract or data filing</div>
        <div className="dropzone-subtext">Supports PDF, Markdown, Text, and JSON (automatic chunking & metadata extraction)</div>

        {uploadStatus && (
          <div className={`upload-status-bar ${uploadStatus.error ? "error" : "success"}`}>
            {uploadStatus.text}
          </div>
        )}
      </div>

      {/* Document Grid */}
      <div className="vault-docs-section">
        <h3 className="section-title">Active Partition Documents</h3>

        {loading ? (
          <div className="loading-state-card">Loading vault index...</div>
        ) : vaultDocs.length === 0 ? (
          <div className="empty-vault-card">
            <span className="empty-icon">📭</span>
            <div className="empty-title">No documents in this partition yet</div>
            <div className="empty-desc">Upload sample contracts or financial filings above to enable grounded answers.</div>
          </div>
        ) : (
          <div className="docs-cards-grid">
            {vaultDocs.map((doc, idx) => (
              <div key={idx} className="doc-item-card">
                <div className="doc-card-header">
                  <div className="doc-icon-badge">📄</div>
                  <div className="doc-name-group">
                    <div className="doc-filename" title={doc.filename}>{doc.filename}</div>
                    <div className="doc-meta-sub">
                      {doc.chunk_count || 1} chunks • {doc.size_bytes ? Math.round(doc.size_bytes / 1024) + " KB" : "Indexed"}
                    </div>
                  </div>
                </div>

                <div className="doc-card-actions">
                  <button
                    className="doc-action-btn view"
                    onClick={() => onOpenVisualizer({ filename: doc.filename, page: 1 })}
                    title="Open in Document Visualizer"
                  >
                    👁️ Inspect & Highlight
                  </button>
                  <button
                    className="doc-action-btn delete"
                    onClick={() => onDelete(doc.filename)}
                    title="Delete from partition"
                  >
                    🗑️ Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
