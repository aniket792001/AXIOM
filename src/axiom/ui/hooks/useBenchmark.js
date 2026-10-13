import { useState, useEffect, useCallback } from "https://esm.sh/react@18.2.0";
import { api } from "../services/api.js";

export function useBenchmark() {
  const [summary, setSummary] = useState(null);
  const [testCases, setTestCases] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [sumData, casesData] = await Promise.all([
        api.getBenchmarkSummary(),
        api.getBenchmarkCases(),
      ]);
      setSummary(sumData);
      setTestCases(casesData.test_cases || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const runLive = useCallback(async () => {
    setIsRunning(true);
    setError(null);
    try {
      const res = await api.runBenchmarkLive();
      setSummary(res);
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  }, [loadData]);

  return {
    summary,
    testCases,
    isRunning,
    error,
    runLive,
    refresh: loadData,
  };
}
