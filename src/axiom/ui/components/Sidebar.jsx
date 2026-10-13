import React, { useState } from "https://esm.sh/react@18.2.0";

export function Sidebar({ activeTab, setActiveTab, user, onOpenProfile, onLogout }) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { id: "chat", icon: "💬", label: "Reasoning Chat", badge: null },
    { id: "vault", icon: "📚", label: "Knowledge Vault", badge: null },
    { id: "contradiction", icon: "⚖️", label: "Contract Diff", badge: "M&A" },
    { id: "benchmark", icon: "📊", label: "RAG Benchmarks", badge: "98%" },
    { id: "history", icon: "📜", label: "Audit History", badge: null },
  ];

  return (
    <aside className={`axiom-sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-logo-mark">A</div>
        {!collapsed && (
          <div className="brand-titles">
            <div className="brand-name">AXIOM</div>
            <div className="brand-edition">SCORE ENGINE v1.2</div>
          </div>
        )}
        <button
          className="collapse-toggle-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? "▶" : "◀"}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item-btn ${activeTab === item.id ? "active" : ""}`}
            onClick={() => setActiveTab(item.id)}
            title={item.label}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span className="nav-label">{item.label}</span>}
            {!collapsed && item.badge && <span className="nav-pill-badge">{item.badge}</span>}
          </button>
        ))}
      </nav>

      {/* User Footer Card */}
      {user && (
        <div className="sidebar-footer">
          <div className="user-summary-card" onClick={onOpenProfile}>
            <div className="user-avatar-badge">{user.avatar || "U"}</div>
            {!collapsed && (
              <div className="user-info-text">
                <div className="user-display-name">{user.name}</div>
                <div className="user-role-tag">{user.role?.toUpperCase()}</div>
              </div>
            )}
            {!collapsed && (
              <button
                className="user-exit-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onLogout();
                }}
                title="Sign Out"
              >
                ⎋
              </button>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
