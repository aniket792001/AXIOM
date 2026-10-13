import { useState, useEffect, useCallback } from "https://esm.sh/react@18.2.0";
import { api } from "../services/api.js";

export function useVault(activeTenant) {
  const [vaultDocs, setVaultDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const fetchVaultDocs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getVaultDocuments(activeTenant);
      setVaultDocs(data.documents || []);
    } catch {
      setVaultDocs([]);
    } finally {
      setLoading(false);
    }
  }, [activeTenant]);

  useEffect(() => {
    fetchVaultDocs();
  }, [fetchVaultDocs]);

  const uploadFile = useCallback(async (file) => {
    if (!file) return;
    setUploadStatus({ loading: true, name: file.name, text: `Indexing ${file.name} into partition...` });
    try {
      const res = await api.uploadDocument(file, activeTenant);
      setUploadStatus({
        loading: false,
        name: file.name,
        text: `✓ Ingested '${file.name}' (${res.ingested_chunks} chunks). Grounded & ready.`,
      });
      fetchVaultDocs();
      return res;
    } catch (err) {
      setUploadStatus({ loading: false, error: true, text: `Upload failed: ${err.message}` });
      throw err;
    }
  }, [activeTenant, fetchVaultDocs]);

  const deleteFile = useCallback(async (filename) => {
    try {
      await api.deleteDocument(filename, activeTenant);
      fetchVaultDocs();
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  }, [activeTenant, fetchVaultDocs]);

  return {
    vaultDocs,
    loading,
    uploadStatus,
    setUploadStatus,
    fetchVaultDocs,
    uploadFile,
    deleteFile,
  };
}
