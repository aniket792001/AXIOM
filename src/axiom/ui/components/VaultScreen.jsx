import React, { useRef } from "https://esm.sh/react@18.2.0";

export function VaultScreen({
  vaultDocs,
  loading,
  uploadStatus,
  onUpload,
  onDelete,
  onOpenVisualizer,
  activeTenant,
  user,
}) {
  const fileInputRef = useRef(null);

  // RBAC Permission Checks
  const canIngest = user
    ? user.role !== "auditor" && (!user.permissions || user.permissions.includes("ingest"))
    : true;
  const canDelete = user
    ? user.role === "admin" || (user.permissions && user.permissions.includes("delete_docs"))
    : false;

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  };

  const getRoleBadge = () => {
    if (!user) return null;
    if (user.role === "admin") {
      return <span className="role-chip admin">👑 Administrator (Full Control)</span>;
    }
    if (user.role === "auditor") {
      return <span className="role-chip auditor">🛡️ Compliance Auditor (Read-Only)</span>;
    }
    return <span className="role-chip analyst">📊 Analyst (Query & Ingest)</span>;
  };

  return (
    <div className="vault-screen-canvas">
      {/* Vault Header Banner */}
      <div className="screen-header-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <h2 className="screen-title" style={{ margin: 0 }}>
              {user?.role === "admin" ? "Partitioned Knowledge Vault" : "My Private Knowledge Vault"}
            </h2>
            {getRoleBadge()}
          </div>
          <p className="screen-desc">
            {user?.role === "admin" ? (
              <>Enterprise partition: <strong>{activeTenant}</strong>. Admins can inspect partitions and manage indexed knowledge.</>
            ) : (
              <>Private isolated workspace for <strong>{user?.name || "your account"}</strong> ({activeTenant}). Other users and tenants cannot access or query these files.</>
            )}
          </p>
        </div>
        <div className="screen-stats-badge">
          <span className="stats-number">{vaultDocs.length}</span>
          <span className="stats-label">Indexed Documents</span>
        </div>
      </div>

      {/* Upload Zone / Read-Only Notice */}
      {canIngest ? (
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
          <div className="dropzone-text-main">Click to upload contract, document, or book file</div>
          <div className="dropzone-subtext">
            Supports PDF, Markdown, Text, and JSON (automatically chunked & isolated strictly to your workspace)
          </div>

          {uploadStatus && (
            <div className={`upload-status-bar ${uploadStatus.error ? "error" : "success"}`}>
              {uploadStatus.text}
            </div>
          )}
        </div>
      ) : (
        <div className="upload-dropzone-card readonly-audit-mode" title="Auditor accounts are restricted to read-only compliance inspection">
          <div className="dropzone-icon">🛡️</div>
          <div className="dropzone-text-main">SOC-2 Read-Only Compliance Mode</div>
          <div className="dropzone-subtext">
            Document upload and partition modifications are disabled under the Auditor role.
          </div>
        </div>
      )}

      {/* Document Grid */}
      <div className="vault-docs-section">
        <h3 className="section-title">
          {user?.role === "admin" ? `Active Partition Documents (${activeTenant})` : "My Isolated Documents"}
        </h3>

        {loading ? (
          <div className="loading-state-card">Loading vault index...</div>
        ) : vaultDocs.length === 0 ? (
          <div className="empty-vault-card">
            <span className="empty-icon">📭</span>
            <div className="empty-title">No documents in your workspace yet</div>
            <div className="empty-desc">
              {canIngest
                ? "Upload your books, PDFs, or contracts above. Only you will be able to query them."
                : "This workspace is currently empty."}
            </div>
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
                      {doc.chunk_count || 1} chunks • {doc.total_characters ? `${Math.round(doc.total_characters / 1000)}k chars` : "Indexed"}
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

                  {canDelete ? (
                    <button
                      className="doc-action-btn delete"
                      onClick={() => onDelete(doc.filename)}
                      title="Delete from partition"
                    >
                      🗑️ Remove
                    </button>
                  ) : (
                    <div className="doc-protected-badge" title="Deletion restricted to Administrator role">
                      🔒 Protected
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

