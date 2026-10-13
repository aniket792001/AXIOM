import { useState, useCallback } from "https://esm.sh/react@18.2.0";
import { api } from "../services/api.js";

export function useContradiction(activeTenant, modelProvider) {
  const [contractA, setContractA] = useState("");
  const [contractB, setContractB] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDemoContracts = useCallback(async () => {
    try {
      const data = await api.getDemoContractPairs();
      const pair = data.demo_pairs?.[0];
      if (pair) {
        setContractA(pair.contract_a_content || "");
        setContractB(pair.contract_b_content || "");
      }
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const runAnalysis = useCallback(async () => {
    if (!contractA.trim() || !contractB.trim()) {
      setError("Please provide content for both Document A and Document B.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.analyzeContradiction({
        contractA,
        contractB,
        tenantId: activeTenant,
        modelProvider,
      });
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [contractA, contractB, activeTenant, modelProvider]);

  return {
    contractA,
    setContractA,
    contractB,
    setContractB,
    analysisResult,
    loading,
    error,
    loadDemoContracts,
    runAnalysis,
  };
}
