import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAppDispatch } from "@/store/hooks";
import { upsertChatSession, toSessionRow } from "@/store/slices/chatSessionsSlice";
import { buildSessionRowFromMessages } from "@/lib/chat/sessionRow";
import { workflowApi, queryCompliance, chatHistoryApi, uploadApi } from "@/services/api";
import { buildFullConversationPrompt } from "@/lib/workflow/conversationPrompt";
import {
  fromPersistedMessages,
  mapRagResponseToMessage,
  toPersistableMessages,
} from "@/lib/workflow/messageMappers";
import {
  DEFAULT_CHAT_CONFIG,
  type ChatSessionConfig,
  defaultShapForChatType,
  defaultSemanticMlForChatType,
} from "@/lib/workflow/categories";

const XAI_PROMPT_STORAGE_KEY = "finace_general_xai_prompt_seen";
import type { StudioMode, WorkflowMessage } from "@/lib/workflow/types";

function configFromSession(session: any): ChatSessionConfig {
  const chatType = session?.chat_type || DEFAULT_CHAT_CONFIG.chatType;
  return {
    chatType,
    selectedCategories: session?.selected_categories || [],
    shapEnabled: session?.shap_enabled ?? defaultShapForChatType(chatType),
    semanticMlEnabled: session?.semantic_ml_enabled ?? defaultSemanticMlForChatType(chatType),
    categoryMode: session?.selected_categories?.length ? "selected" : "unsure",
  };
}

export function useWorkflowChat() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const dispatch = useAppDispatch();

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<WorkflowMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [studioMode, setStudioMode] = useState<StudioMode>("chat");
  const [chatConfig, setChatConfig] = useState<ChatSessionConfig>(DEFAULT_CHAT_CONFIG);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showGeneralXaiPrompt, setShowGeneralXaiPrompt] = useState(false);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  const [settingsHint, setSettingsHint] = useState<string | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [pdfUploadError, setPdfUploadError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const savingRef = useRef(false);
  const loadedChatRef = useRef<string | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  useEffect(() => {
    const chatId = searchParams.get("chat");
    const isNew = searchParams.get("new") === "1";

    if (isNew) {
      setShowOnboarding(true);
      setMessages([]);
      setSessionId(null);
      loadedChatRef.current = null;
      setChatConfig(DEFAULT_CHAT_CONFIG);
      return;
    }

    if (!chatId) {
      if (!loadedChatRef.current) {
        loadedChatRef.current = "__fresh__";
        setShowOnboarding(true);
        setMessages([]);
        setSessionId(null);
        setChatConfig(DEFAULT_CHAT_CONFIG);
      }
      return;
    }

    if (chatId === loadedChatRef.current) return;

    loadedChatRef.current = chatId;
    (async () => {
      try {
        const data: any = await chatHistoryApi.get(chatId);
        const session = data.session;
        setSessionId(session?.session_id || chatId);
        setMessages(fromPersistedMessages(session?.messages || []));
        setChatConfig(configFromSession(session));
        setShowOnboarding(false);
        if (session?.session_id) {
          dispatch(upsertChatSession(toSessionRow(session)));
        }
      } catch (err) {
        console.error(err);
      }
    })();
  }, [searchParams, dispatch]);

  const persistSession = useCallback(
    async (nextMessages: WorkflowMessage[], existingId: string | null) => {
      if (!existingId && !nextMessages.length) return existingId;

      while (savingRef.current) {
        await new Promise((r) => setTimeout(r, 40));
      }

      savingRef.current = true;
      try {
        const payload: Record<string, unknown> = {
          messages: toPersistableMessages(nextMessages),
          chat_type: chatConfig.chatType,
          selected_categories: chatConfig.selectedCategories,
          shap_enabled: chatConfig.shapEnabled,
          semantic_ml_enabled: chatConfig.semanticMlEnabled,
        };

        if (existingId) {
          dispatch(upsertChatSession(buildSessionRowFromMessages(existingId, nextMessages)));
          const data: any = await chatHistoryApi.save(existingId, payload);
          if (data.session) dispatch(upsertChatSession(toSessionRow(data.session)));
          return data.session?.session_id || existingId;
        }

        const data: any = await chatHistoryApi.create(payload);
        const id = data.session?.session_id || null;
        if (id) {
          setSessionId(id);
          dispatch(
            upsertChatSession(
              data.session ? toSessionRow(data.session) : buildSessionRowFromMessages(id, nextMessages)
            )
          );
          router.replace(`/dashboard/workflow?chat=${id}`);
        }
        return id;
      } catch (err) {
        console.error("Failed to save chat session", err);
        return existingId;
      } finally {
        savingRef.current = false;
      }
    },
    [router, dispatch, chatConfig]
  );

  const completeOnboarding = async (config: ChatSessionConfig) => {
    setChatConfig(config);
    setShowOnboarding(false);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(XAI_PROMPT_STORAGE_KEY, "1");
    }
    router.replace("/dashboard/workflow");
    try {
      const data: any = await chatHistoryApi.create({
        messages: [],
        chat_type: config.chatType,
        selected_categories: config.selectedCategories,
        shap_enabled: config.shapEnabled,
        semantic_ml_enabled: config.semanticMlEnabled,
      });
      const id = data.session?.session_id;
      if (id) {
        setSessionId(id);
        dispatch(upsertChatSession(toSessionRow(data.session)));
        router.replace(`/dashboard/workflow?chat=${id}`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const runQuery = async (
    userMsg: string,
    prior: WorkflowMessage[],
    cfg: ChatSessionConfig = chatConfig
  ) => {
    const fullPrompt = buildFullConversationPrompt(prior, userMsg);
    const enableXai = true;
    const enableSemanticMl = true;
    const data: any = await queryCompliance({
      prompt: fullPrompt,
      topK: 5,
      callType: cfg.chatType,
      activeCategories: cfg.selectedCategories,
      enableXai,
      enableSemanticMl,
      chatId: sessionId,
    });
    return data;
  };

  const handleSendMessage = async (override?: string) => {
    const userMsg = (override ?? input).trim();
    if (!userMsg || loading) return;

    const isGeneral = chatConfig.chatType === "general_query";
    const promptSeen =
      typeof window !== "undefined" && window.localStorage.getItem(XAI_PROMPT_STORAGE_KEY) === "1";
    if (isGeneral && !promptSeen) {
      setPendingUserMessage(userMsg);
      setInput("");
      setShowGeneralXaiPrompt(true);
      return;
    }

    setInput("");
    const prior = messages;
    const withUser: WorkflowMessage[] = [...prior, { role: "user", content: userMsg }];
    setMessages(withUser);
    setLoading(true);

    try {
      const data = await runQuery(userMsg, prior, chatConfig);
      const nextMessages = [...withUser, mapRagResponseToMessage(data)];
      setMessages(nextMessages);

      const id = await persistSession(nextMessages, sessionId);
      if (id && !sessionId) setSessionId(id);
    } catch (err) {
      console.error(err);
      const body = (err as any)?.response?.data;
      const msg =
        body?.error ||
        body?.message ||
        "Sorry, I encountered an error during analysis. Please try again.";
      setMessages((prev) => [...prev, { role: "ai", content: msg }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalizeReport = async () => {
    if (chatConfig.chatType === "general_query") return;
    setFinalizing(true);
    try {
      const fullContext = buildFullConversationPrompt(
        messages,
        "Finalize a structured compliance report from the full conversation above."
      );
      const data: any = await workflowApi.analyze(fullContext, { chat_id: sessionId || undefined });
      if (data?.report_id) router.push(`/dashboard/evaluator/${data.report_id}`);
    } catch (err) {
      console.error(err);
      alert("Failed to generate final report.");
    } finally {
      setFinalizing(false);
    }
  };

  const setShapEnabled = (enabled: boolean) => {
    setChatConfig((c) => ({ ...c, shapEnabled: enabled }));
    if (sessionId) {
      chatHistoryApi.save(sessionId, { shap_enabled: enabled }).catch(console.error);
    }
  };

  const setSemanticMlEnabled = (enabled: boolean) => {
    setChatConfig((c) => ({ ...c, semanticMlEnabled: enabled }));
    if (sessionId) {
      chatHistoryApi.save(sessionId, { semantic_ml_enabled: enabled }).catch(console.error);
    }
  };

  const setSelectedCategories = (categories: string[]) => {
    setChatConfig((c) => ({
      ...c,
      selectedCategories: categories,
      categoryMode: categories.length ? "selected" : "unsure",
    }));
    if (sessionId) {
      chatHistoryApi
        .save(sessionId, {
          selected_categories: categories,
        })
        .catch(console.error);
    }
  };

  const sendAfterPrompt = async (userMsg: string, cfg: ChatSessionConfig) => {
    const prior = messages;
    const withUser: WorkflowMessage[] = [...prior, { role: "user", content: userMsg }];
    setMessages(withUser);
    setLoading(true);
    try {
      const data = await runQuery(userMsg, prior, cfg);
      const nextMessages = [...withUser, mapRagResponseToMessage(data)];
      setMessages(nextMessages);
      const id = await persistSession(nextMessages, sessionId);
      if (id && !sessionId) setSessionId(id);
    } catch (err) {
      console.error(err);
      const body = (err as any)?.response?.data;
      const msg =
        body?.error ||
        body?.message ||
        "Sorry, I encountered an error during analysis. Please try again.";
      setMessages((prev) => [...prev, { role: "ai", content: msg }]);
    } finally {
      setLoading(false);
    }
  };

  const completeGeneralXaiPrompt = async (shap: boolean, semanticMl: boolean) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(XAI_PROMPT_STORAGE_KEY, "1");
    }
    setShowGeneralXaiPrompt(false);
    const nextConfig = { ...chatConfig, shapEnabled: shap, semanticMlEnabled: semanticMl };
    setChatConfig(nextConfig);
    if (sessionId) {
      chatHistoryApi
        .save(sessionId, { shap_enabled: shap, semantic_ml_enabled: semanticMl })
        .catch(console.error);
    }
    const userMsg = pendingUserMessage;
    setPendingUserMessage(null);
    if (!userMsg) return;
    await sendAfterPrompt(userMsg, nextConfig);
  };

  const handleUploadPdf = async (file: File) => {
    if (!file || loading || uploadingPdf) return;
    setPdfUploadError(null);
    setUploadingPdf(true);
    try {
      const result = await uploadApi.uploadPdf(file, true);
      if (!result.ok) {
        throw new Error(result.warnings?.[0] || "No text could be recognised from this PDF.");
      }
      const docText = (result.text || "").trim();
      const preview = docText.length > 6000 ? `${docText.slice(0, 6000)}\n…` : docText;
      const header =
        `I've attached the document "${result.filename}" for analysis. ` +
        `It was recognised via ${result.method} (${result.page_count} page(s), ` +
        `${result.char_count.toLocaleString()} characters) and indexed for search.\n\n` +
        `Extracted document content:\n${preview || "(no text extracted)"}`;
      await sendAfterPrompt(header, chatConfig);
    } catch (err) {
      console.error(err);
      setPdfUploadError(
        (err as any)?.message || "PDF upload failed. Is the RAG service running?"
      );
    } finally {
      setUploadingPdf(false);
    }
  };

  const declineGeneralXaiPrompt = () => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(XAI_PROMPT_STORAGE_KEY, "1");
    }
    setShowGeneralXaiPrompt(false);
    setSettingsHint(
      "You can turn on SHAP and semantic ML anytime using the settings icon next to Send."
    );
    const userMsg = pendingUserMessage;
    setPendingUserMessage(null);
    if (userMsg) {
      void sendAfterPrompt(userMsg, chatConfig);
    }
  };

  return {
    input,
    setInput,
    messages,
    loading,
    finalizing,
    studioMode,
    setStudioMode,
    scrollRef,
    handleSendMessage,
    handleFinalizeReport,
    empty: messages.length === 0 && !loading && !showOnboarding,
    chatConfig,
    setShapEnabled,
    setSemanticMlEnabled,
    setSelectedCategories,
    settingsHint,
    showGeneralXaiPrompt,
    completeGeneralXaiPrompt,
    declineGeneralXaiPrompt,
    uploadingPdf,
    pdfUploadError,
    handleUploadPdf,
    showOnboarding,
    completeOnboarding,
  };
}
