import { useState, useCallback, useRef } from "https://esm.sh/react@18.2.0";
import { api } from "../services/api.js";

export function useChat({ activeTenant, user, modelProvider }) {
  const [sessionId, setSessionId] = useState(() => "session_" + Math.random().toString(36).substring(2, 9));
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStep, setActiveStep] = useState(null); // 'router', 'retriever', 'grader', 'generator', 'audit'
  const [loopCount, setLoopCount] = useState(0);
  const chatScrollRef = useRef(null);

  const resetChat = useCallback(() => {
    setMessages([]);
    setSessionId("session_" + Math.random().toString(36).substring(2, 9));
    setActiveStep(null);
    setLoopCount(0);
  }, []);

  const sendQuery = useCallback(async (queryText) => {
    const q = (queryText || "").trim();
    if (!q || isProcessing) return;

    setIsProcessing(true);
    setActiveStep("router");
    setLoopCount(0);

    const userMsgId = Date.now();
    const assistantMsgId = userMsgId + 1;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: q, id: userMsgId },
      {
        role: "assistant",
        content: "",
        citations: [],
        trace: [],
        id: assistantMsgId,
        isStreaming: true,
      },
    ]);

    let accumulatedContent = "";
    let accumulatedCitations = [];

    await api.streamQuery({
      query: q,
      tenantId: activeTenant,
      sessionId,
      userId: user?.email || "guest",
      provider: modelProvider || "gemini",
      onStatus: (statusData) => {
        const node = statusData.node || statusData.phase;
        if (statusData.loop_count !== undefined) setLoopCount(statusData.loop_count);
        if (node === "router") setActiveStep("router");
        else if (node === "retriever") setActiveStep("retriever");
        else if (node === "grader") setActiveStep("grader");
        else if (node === "generator") setActiveStep("generator");
        else if (node === "hallucination_grader" || node === "audit") setActiveStep("audit");
      },
      onToken: (token) => {
        accumulatedContent += token;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: accumulatedContent, isStreaming: true }
              : m
          )
        );
      },
      onAnswer: (answerData) => {
        if (answerData.generation) accumulatedContent = answerData.generation;
        if (answerData.citations) accumulatedCitations = answerData.citations;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedContent,
                  citations: accumulatedCitations,
                  isStreaming: false,
                }
              : m
          )
        );
      },
      onFallback: (fallbackData) => {
        if (fallbackData.generation) accumulatedContent = fallbackData.generation;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedContent,
                  isFallback: true,
                  isStreaming: false,
                }
              : m
          )
        );
      },
      onError: (errText) => {
        accumulatedContent = `⚠️ SCORE Engine Notice: ${errText}`;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedContent,
                  isStreaming: false,
                }
              : m
          )
        );
      },
      onDone: (doneData) => {
        if (doneData.final_generation && !accumulatedContent) {
          accumulatedContent = doneData.final_generation;
        }
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedContent || "Verified response completed.",
                  citations: accumulatedCitations,
                  isStreaming: false,
                }
              : m
          )
        );
        setActiveStep("audit");
        setIsProcessing(false);
      },
    });

    setIsProcessing(false);
  }, [isProcessing, activeTenant, sessionId, user, modelProvider]);

  return {
    sessionId,
    setSessionId,
    messages,
    setMessages,
    isProcessing,
    activeStep,
    loopCount,
    sendQuery,
    resetChat,
    chatScrollRef,
  };
}
