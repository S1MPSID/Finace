import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAppDispatch } from "@/store/hooks";
import { upsertChatSession, toSessionRow } from "@/store/slices/chatSessionsSlice";
import { buildSessionRowFromMessages } from "@/lib/chat/sessionRow";
import { workflowApi, queryCompliance, chatHistoryApi } from "@/services/api";
import { buildFullConversationPrompt } from "@/lib/workflow/conversationPrompt";
import {
  fromPersistedMessages,
  mapRagResponseToMessage,
  toPersistableMessages,
} from "@/lib/workflow/messageMappers";
import type { StudioMode, WorkflowMessage } from "@/lib/workflow/types";

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
      setMessages([]);
      setSessionId(null);
      loadedChatRef.current = null;
      router.replace("/dashboard/workflow");
      return;
    }

    if (!chatId || chatId === loadedChatRef.current) return;

    loadedChatRef.current = chatId;
    (async () => {
      try {
        const data: any = await chatHistoryApi.get(chatId);
        const session = data.session;
        setSessionId(session?.session_id || chatId);
        setMessages(fromPersistedMessages(session?.messages || []));
        if (session?.session_id) {
          dispatch(upsertChatSession(toSessionRow(session)));
        }
      } catch (err) {
        console.error(err);
      }
    })();
  }, [searchParams, router, dispatch]);

  const persistSession = useCallback(
    async (nextMessages: WorkflowMessage[], existingId: string | null) => {
      if (!nextMessages.length) return existingId;

      while (savingRef.current) {
        await new Promise((r) => setTimeout(r, 40));
      }

      savingRef.current = true;
      try {
        const payload = { messages: toPersistableMessages(nextMessages) };

        if (existingId) {
          // 1) Update sidebar immediately from local state
          dispatch(upsertChatSession(buildSessionRowFromMessages(existingId, nextMessages)));
          // 2) Persist to DB
          const data: any = await chatHistoryApi.save(existingId, payload);
          if (data.session) dispatch(upsertChatSession(toSessionRow(data.session)));
          return data.session?.session_id || existingId;
        }

        // New chat — need backend id first, then local + DB are in sync
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
    [router, dispatch]
  );

  const handleSendMessage = async (override?: string) => {
    const userMsg = (override ?? input).trim();
    if (!userMsg || loading) return;

    setInput("");
    const prior = messages;
    const withUser: WorkflowMessage[] = [...prior, { role: "user", content: userMsg }];
    setMessages(withUser);
    setLoading(true);

    try {
      const fullPrompt = buildFullConversationPrompt(prior, userMsg);
      const data: any = await queryCompliance({ prompt: fullPrompt, topK: 5 });
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
    empty: messages.length === 0 && !loading,
  };
}
