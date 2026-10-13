import React, { useState, useEffect } from "https://esm.sh/react@18.2.0";
import { Header } from "./Header.jsx";
import { Sidebar } from "./Sidebar.jsx";
import { ChatScreen } from "./ChatScreen.jsx";
import { VaultScreen } from "./VaultScreen.jsx";
import { DiffMatrixScreen } from "./DiffMatrixScreen.jsx";
import { BenchmarkScreen } from "./BenchmarkScreen.jsx";
import { HistoryScreen } from "./HistoryScreen.jsx";
import { DocumentVisualizerModal } from "./DocumentVisualizerModal.jsx";
import { ProfileModal } from "./ProfileModal.jsx";
import { AuthGateModal } from "./AuthGateModal.jsx";
import { CitationDrawer } from "./CitationDrawer.jsx";

import { useAuth } from "../hooks/useAuth.js";
import { useChat } from "../hooks/useChat.js";
import { useVault } from "../hooks/useVault.js";
import { useContradiction } from "../hooks/useContradiction.js";
import { useBenchmark } from "../hooks/useBenchmark.js";
import { api } from "../services/api.js";

export function AppShell() {
  const [theme, setTheme] = useState(() => localStorage.getItem("axiom_theme") || "light");
  const [activeTab, setActiveTab] = useState("chat");
  const [modelProvider, setModelProvider] = useState("gemini");

  // Modals & Drawers state
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [visualizerTarget, setVisualizerTarget] = useState(null);

  // Sync theme attribute
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("axiom_theme", theme);
  }, [theme]);

  // Hooks
  const auth = useAuth();
  const chat = useChat({
    activeTenant: auth.activeTenant,
    user: auth.user,
    modelProvider,
  });
  const vault = useVault(auth.activeTenant);
  const contradiction = useContradiction(auth.activeTenant, modelProvider);
  const benchmark = useBenchmark();

  // Export helper
  const handleExportCert = async (msg, format = "pdf") => {
    try {
      const blob = await api.exportCertificate({
        query: chat.messages[chat.messages.length - 2]?.content || "Enterprise Legal Query",
        generation: msg.content,
        citations: msg.citations || [],
        tenantId: auth.activeTenant,
        sessionId: chat.sessionId,
        format,
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AXIOM_AUDIT_REPORT_${Date.now()}.${format === "excel" ? "xlsx" : format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Export failed: " + err.message);
    }
  };

  return (
    <div className="axiom-app-root">
      {/* 1. AUTH GATE MODAL */}
      {!auth.user && (
        <AuthGateModal
          onLogin={auth.login}
          onRegister={auth.register}
        />
      )}

      {/* 2. SIDEBAR */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={auth.user}
        onOpenProfile={() => setShowProfileModal(true)}
        onLogout={auth.logout}
      />

      {/* 3. MAIN WORKSPACE CONTAINER */}
      <div className="axiom-main-workspace">
        <Header
          activeTab={activeTab}
          activeTenant={auth.activeTenant}
          setActiveTenant={auth.setActiveTenant}
          theme={theme}
          setTheme={setTheme}
          modelProvider={modelProvider}
          setModelProvider={setModelProvider}
          user={auth.user}
          onOpenProfile={() => setShowProfileModal(true)}
          isProcessing={chat.isProcessing}
        />

        {/* 4. ACTIVE SCREEN VIEWPORT (FLUID & SPACIOUS) */}
        <main className="axiom-screen-viewport">
          {activeTab === "chat" && (
            <ChatScreen
              messages={chat.messages}
              isProcessing={chat.isProcessing}
              activeStep={chat.activeStep}
              loopCount={chat.loopCount}
              onSend={chat.sendQuery}
              onReset={chat.resetChat}
              onSelectCitation={setSelectedCitation}
              onExportCert={handleExportCert}
            />
          )}

          {activeTab === "vault" && (
            <VaultScreen
              vaultDocs={vault.vaultDocs}
              loading={vault.loading}
              uploadStatus={vault.uploadStatus}
              onUpload={vault.uploadFile}
              onDelete={vault.deleteFile}
              onOpenVisualizer={setVisualizerTarget}
              activeTenant={auth.activeTenant}
            />
          )}

          {activeTab === "contradiction" && (
            <DiffMatrixScreen
              contractA={contradiction.contractA}
              setContractA={contradiction.setContractA}
              contractB={contradiction.contractB}
              setContractB={contradiction.setContractB}
              analysisResult={contradiction.analysisResult}
              loading={contradiction.loading}
              error={contradiction.error}
              onLoadDemo={contradiction.loadDemoContracts}
              onRunAnalysis={contradiction.runAnalysis}
              onOpenVisualizer={setVisualizerTarget}
            />
          )}

          {activeTab === "benchmark" && (
            <BenchmarkScreen
              summary={benchmark.summary}
              testCases={benchmark.testCases}
              isRunning={benchmark.isRunning}
              error={benchmark.error}
              onRunLive={benchmark.runLive}
            />
          )}

          {activeTab === "history" && (
            <HistoryScreen
              activeTenant={auth.activeTenant}
              onSelectQuery={(q) => {
                setActiveTab("chat");
                chat.sendQuery(q);
              }}
              onExportCert={handleExportCert}
            />
          )}
        </main>
      </div>

      {/* 5. CITATION SLIDE-OVER DRAWER */}
      <CitationDrawer
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
        onOpenVisualizer={setVisualizerTarget}
      />

      {/* 6. DOCUMENT VISUALIZER MODAL */}
      {visualizerTarget && (
        <DocumentVisualizerModal
          target={visualizerTarget}
          onClose={() => setVisualizerTarget(null)}
        />
      )}

      {/* 7. PROFILE & SETTINGS MODAL */}
      {showProfileModal && auth.user && (
        <ProfileModal
          user={auth.user}
          onClose={() => setShowProfileModal(false)}
          onUpdateProfile={auth.updateProfile}
          onChangePassword={auth.changePassword}
          onLogout={() => {
            auth.logout();
            setShowProfileModal(false);
          }}
        />
      )}
    </div>
  );
}
