import type { WorkflowMessage } from "@/lib/workflow/types";
import type { ChatSessionRow } from "@/store/slices/chatSessionsSlice";

function titleFromMessages(messages: WorkflowMessage[]): string {
  const firstUser = messages.find((m) => m.role === "user" && m.content?.trim());
  if (!firstUser) return "New compliance chat";
  const text = firstUser.content.trim().replace(/\s+/g, " ");
  return text.length > 64 ? `${text.slice(0, 61)}...` : text;
}

/** Build sidebar row from in-memory messages — no API call. */
export function buildSessionRowFromMessages(
  sessionId: string,
  messages: WorkflowMessage[]
): ChatSessionRow {
  const lastAi = [...messages].reverse().find((m) => m.role === "ai");
  return {
    session_id: sessionId,
    title: titleFromMessages(messages),
    last_risk_level: lastAi?.data?.risk_level,
    last_score: lastAi?.data?.compliance_score,
    updated_at: new Date().toISOString(),
  };
}
