import React, { useState } from "https://esm.sh/react@18.2.0";

export function ProfileModal({ user, onClose, onUpdateProfile, onChangePassword, onLogout }) {
  const [activeTab, setActiveTab] = useState("profile"); // 'profile' | 'password'

  // Profile Form
  const [name, setName] = useState(user?.name || "");
  const [title, setTitle] = useState(user?.title || "");
  const [avatar, setAvatar] = useState(user?.avatar || "U");
  const [defaultTenant, setDefaultTenant] = useState(user?.default_tenant || "default_tenant");

  // Password Form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [statusMessage, setStatusMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage(null);
    const res = await onUpdateProfile({
      name: name.trim(),
      title: title.trim(),
      avatar: avatar.trim().toUpperCase(),
      default_tenant: defaultTenant,
    });
    setLoading(false);
    if (res.success) {
      setStatusMessage({ type: "success", text: "Profile updated successfully." });
    } else {
      setStatusMessage({ type: "error", text: res.error || "Update failed." });
    }
  };

  const handleSavePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setStatusMessage({ type: "error", text: "New passwords do not match." });
      return;
    }
    if (newPassword.length < 6) {
      setStatusMessage({ type: "error", text: "Password must be at least 6 characters." });
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    const res = await onChangePassword(currentPassword, newPassword);
    setLoading(false);
    if (res.success) {
      setStatusMessage({ type: "success", text: "Password updated successfully with Bcrypt." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } else {
      setStatusMessage({ type: "error", text: res.error || "Password change failed." });
    }
  };

  return (
    <div className="modal-backdrop-blur">
      <div className="profile-modal-dialog">
        <div className="profile-modal-header">
          <div className="header-meta">
            <span className="modal-icon">👤</span>
            <div>
              <div className="modal-title">Account Profile & Security</div>
              <div className="modal-sub">SOC-2 Type II Compliance & Session Settings</div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Subtabs */}
        <div className="modal-subtabs">
          <button
            className={`subtab-btn ${activeTab === "profile" ? "active" : ""}`}
            onClick={() => setActiveTab("profile")}
          >
            Profile Information
          </button>
          <button
            className={`subtab-btn ${activeTab === "password" ? "active" : ""}`}
            onClick={() => setActiveTab("password")}
          >
            Change Password
          </button>
        </div>

        {statusMessage && (
          <div className={`modal-status-alert ${statusMessage.type}`}>
            {statusMessage.text}
          </div>
        )}

        <div className="modal-body-scroll">
          {activeTab === "profile" ? (
            <form onSubmit={handleSaveProfile} className="profile-form">
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Professional Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="form-group-row">
                <div className="form-group">
                  <label className="form-label">Avatar Initials</label>
                  <input
                    type="text"
                    maxLength={2}
                    className="form-input avatar-input"
                    value={avatar}
                    onChange={(e) => setAvatar(e.target.value.toUpperCase())}
                  />
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">Assigned Role (RBAC)</label>
                  <div className="readonly-role-badge">{user?.role?.toUpperCase() || "ANALYST"}</div>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Default Partition Vault</label>
                <select
                  className="form-select"
                  value={defaultTenant}
                  onChange={(e) => setDefaultTenant(e.target.value)}
                >
                  <option value="default_tenant">Master Enterprise Vault</option>
                  <option value="legal_contracts">Legal & Compliance Vault</option>
                  <option value="financial_filings">Financial Filings (10-K/10-Q)</option>
                </select>
              </div>

              <div className="form-actions-row">
                <button
                  type="button"
                  className="secondary-action-btn"
                  onClick={onLogout}
                >
                  Sign Out
                </button>
                <button
                  type="submit"
                  className="primary-action-btn"
                  disabled={loading}
                >
                  {loading ? "Saving..." : "Save Profile"}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleSavePassword} className="profile-form">
              <div className="form-group">
                <label className="form-label">Current Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">New Password (Bcrypt Salted)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Minimum 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Confirm New Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Re-enter new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-actions-row right">
                <button
                  type="submit"
                  className="primary-action-btn"
                  disabled={loading}
                >
                  {loading ? "Updating..." : "Update Password"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
