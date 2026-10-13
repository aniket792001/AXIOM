import { useState, useEffect, useCallback } from "https://esm.sh/react@18.2.0";
import { api } from "../services/api.js";

export const PRESET_PERSONAS = [
  {
    role: "admin",
    name: "Alex Vance",
    email: "admin@axiom.ai",
    title: "Enterprise Administrator",
    avatar: "AV",
    tenant: "default_tenant",
    badgeLabel: "Full Control",
    desc: "Administrative privileges: Partition management, document deletion, and system telemetry.",
    icon: "👑",
  },
  {
    role: "analyst",
    name: "Sarah Chen",
    email: "analyst@axiom.ai",
    title: "Senior Legal & Financial Analyst",
    avatar: "SC",
    tenant: "legal_contracts",
    badgeLabel: "Analysis & Synthesis",
    desc: "Query the SCORE cyclical engine, upload contracts, and inspect citation deep-links.",
    icon: "📊",
  },
  {
    role: "auditor",
    name: "Marcus Stone",
    email: "auditor@axiom.ai",
    title: "SOC-2 Compliance Officer",
    avatar: "MS",
    tenant: "financial_filings",
    badgeLabel: "Read-Only Audit",
    desc: "Verify zero-hallucination proofs and generate cryptographic PDF/Excel certificates.",
    icon: "🛡️",
  },
];

export function useAuth() {
  const [user, setUser] = useState(() => {
    try {
      const saved = sessionStorage.getItem("axiom_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    try {
      return sessionStorage.getItem("axiom_token") || null;
    } catch {
      return null;
    }
  });

  const [activeTenant, setActiveTenant] = useState("default_tenant");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user?.default_tenant) {
      setActiveTenant(user.default_tenant);
    }
  }, [user]);

  const login = useCallback(async ({ email, password, role, tenant }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.login({ email, password, role });
      setUser(data.user);
      setToken(data.token);
      sessionStorage.setItem("axiom_user", JSON.stringify(data.user));
      sessionStorage.setItem("axiom_token", data.token);
      if (tenant) setActiveTenant(tenant);
      else if (data.user?.default_tenant) setActiveTenant(data.user.default_tenant);
      return { success: true, user: data.user };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (userData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.register(userData);
      setUser(data.user);
      setToken(data.token);
      sessionStorage.setItem("axiom_user", JSON.stringify(data.user));
      sessionStorage.setItem("axiom_token", data.token);
      setActiveTenant(data.user.default_tenant || "default_tenant");
      return { success: true, user: data.user };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    sessionStorage.removeItem("axiom_user");
    sessionStorage.removeItem("axiom_token");
  }, []);

  const updateProfile = useCallback(async (profileData) => {
    if (!token) return { success: false, error: "Unauthenticated" };
    try {
      const res = await api.updateProfile(token, profileData);
      setUser(res.user);
      sessionStorage.setItem("axiom_user", JSON.stringify(res.user));
      if (profileData.default_tenant) setActiveTenant(profileData.default_tenant);
      return { success: true, user: res.user };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, [token]);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    if (!token) return { success: false, error: "Unauthenticated" };
    try {
      const res = await api.changePassword(token, currentPassword, newPassword);
      return { success: true, message: res.message };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, [token]);

  return {
    user,
    token,
    activeTenant,
    setActiveTenant,
    loading,
    error,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
  };
}
