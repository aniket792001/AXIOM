import React, { useState } from "https://esm.sh/react@18.2.0";
import { PRESET_PERSONAS } from "../hooks/useAuth.js";

export function AuthGateModal({ onLogin, onRegister }) {
  const [authTab, setAuthTab] = useState("personas"); // 'personas' | 'login' | 'register'
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("analyst");
  const [title, setTitle] = useState("Enterprise User");
  const [tenant, setTenant] = useState("default_tenant");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePersonaSelect = async (p) => {
    setLoading(true);
    setError(null);
    const res = await onLogin({
      email: p.email,
      password: "",
      role: p.role,
      tenant: p.tenant,
    });
    setLoading(false);
    if (!res.success) {
      setError(res.error);
    }
  };

  const handleManualLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await onLogin({
      email: email.trim(),
      password,
    });
    setLoading(false);
    if (!res.success) {
      setError(res.error);
    }
  };

  const handleManualRegister = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    const res = await onRegister({
      email: email.trim(),
      name: name.trim(),
      password,
      role,
      title,
      default_tenant: tenant,
    });
    setLoading(false);
    if (!res.success) {
      setError(res.error);
    }
  };

  return (
    <div className="modal-backdrop-blur">
      <div className="auth-modal-dialog">
        <div className="auth-header">
          <div className="auth-brand-mark">A</div>
          <h2 className="auth-title">Axiom Enterprise Access</h2>
          <p className="auth-desc">Select an authenticated corporate persona or enter credentials.</p>
        </div>

        {/* Tab Controls */}
        <div className="auth-tabs-row">
          <button
            className={`auth-tab-btn ${authTab === "personas" ? "active" : ""}`}
            onClick={() => { setAuthTab("personas"); setError(null); }}
          >
            Demo Personas
          </button>
          <button
            className={`auth-tab-btn ${authTab === "login" ? "active" : ""}`}
            onClick={() => { setAuthTab("login"); setError(null); }}
          >
            Sign In
          </button>
          <button
            className={`auth-tab-btn ${authTab === "register" ? "active" : ""}`}
            onClick={() => { setAuthTab("register"); setError(null); }}
          >
            Create Account
          </button>
        </div>

        {error && <div className="auth-error-alert">⚠️ {error}</div>}

        <div className="auth-body">
          {authTab === "personas" && (
            <div className="personas-list">
              {PRESET_PERSONAS.map((p) => (
                <div
                  key={p.role}
                  className="persona-card-item"
                  onClick={() => handlePersonaSelect(p)}
                >
                  <div className="persona-avatar">{p.avatar}</div>
                  <div className="persona-info">
                    <div className="persona-name-line">
                      <span className="persona-name">{p.name}</span>
                      <span className="persona-badge">{p.badgeLabel}</span>
                    </div>
                    <div className="persona-title">{p.title}</div>
                    <div className="persona-desc">{p.desc}</div>
                  </div>
                  <button className="persona-select-btn" disabled={loading}>
                    {loading ? "..." : "Launch →"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {authTab === "login" && (
            <form onSubmit={handleManualLogin} className="auth-form">
              <div className="form-group">
                <label className="form-label">Corporate Email</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="analyst@axiom.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Account Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? "Authenticating..." : "Authenticate Session →"}
              </button>
            </form>
          )}

          {authTab === "register" && (
            <form onSubmit={handleManualRegister} className="auth-form">
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Jordan Smith"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Corporate Email</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="jordan@enterprise.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password (Bcrypt Salted)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Minimum 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group-row">
                <div className="form-group flex-1">
                  <label className="form-label">Role</label>
                  <select
                    className="form-select"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                  >
                    <option value="analyst">Analyst</option>
                    <option value="auditor">Auditor</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">Default Partition</label>
                  <select
                    className="form-select"
                    value={tenant}
                    onChange={(e) => setTenant(e.target.value)}
                  >
                    <option value="default_tenant">Master Vault</option>
                    <option value="legal_contracts">Legal Vault</option>
                    <option value="financial_filings">Financial Filings</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? "Creating..." : "Create Account →"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
