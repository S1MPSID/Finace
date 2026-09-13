import type { WorkflowMessage } from "./types";
import { formatSourcesBlock } from "./sourceUtils";
import { formatXaiStats } from "./xaiFormatting";

/**
 * Default 5800 fits Python RAG's legacy 6000 cap.
 * After restarting Python RAG (32k limit), set in Frontend/.env.local:
 *   NEXT_PUBLIC_RAG_PROMPT_MAX_CHARS=30000
 */
export const MAX_PROMPT_CHARS = Number(
  process.env.NEXT_PUBLIC_RAG_PROMPT_MAX_CHARS || 5800
);

const INSTRUCTIONS = [
  "You are continuing an existing compliance analysis. Use the conversation below and prior XAI drivers.",
  "When the user asks to improve the score, treat XAI top_drivers as the checklist. If they add remediations (KYC, AML, FEMA, grievance, etc.), raise compliance_score toward 90-98 and set risk_level LOW when gaps are closed.",
  "Never freeze the score when the latest user message addresses prior XAI drivers.",
].join("\n");

function stripHtml(text: string): string {
  return text
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function clip(text: string, max: number): string {
  const clean = stripHtml(text);
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max)}…`;
}

function formatAssistantTurn(m: WorkflowMessage, idx: number, mode: "full" | "compact" | "minimal"): string {
  const flags = m.data?.risk_flags?.length ? m.data.risk_flags.join(", ") : "none";
  const score =
    m.data?.compliance_score !== undefined && m.data?.compliance_score !== null
      ? String(m.data.compliance_score)
      : "n/a";
  const risk = m.data?.risk_level || "n/a";
  const turn = Math.ceil(idx / 2);
  const drivers = m.data?.xai?.top_drivers?.slice(0, 5).join("; ") || "none";

  if (mode === "minimal") {
    return `### ASSISTANT TURN ${turn} (brief)\nscore=${score}; risk=${risk}; drivers=${drivers}`;
  }

  if (mode === "compact") {
    return [
      `### ASSISTANT TURN ${turn}`,
      clip(m.content, 350),
      `CONTEXT: risk=${risk}; score=${score}; flags=${flags}; drivers=${drivers}`,
    ].join("\n");
  }

  return [
    `### ASSISTANT TURN ${turn}`,
    clip(m.content, 900),
    "",
    "SOURCES:",
    formatSourcesBlock(m.sources?.slice(0, 2)),
    "",
    `CONTEXT: risk_level=${risk}; compliance_score=${score}; risk_flags=${flags}`,
    "XAI:",
    formatXaiStats(m.data?.xai),
  ].join("\n");
}

function formatTurn(m: WorkflowMessage, idx: number, mode: "full" | "compact" | "minimal"): string {
  if (m.role === "user") {
    return `### USER TURN ${Math.floor(idx / 2) + 1}\n${clip(m.content, 400)}`;
  }
  return formatAssistantTurn(m, idx, mode);
}

function assistantMode(idx: number, prior: WorkflowMessage[], lastAiIdx: number): "full" | "compact" | "minimal" {
  if (idx === lastAiIdx) return "full";
  if (idx === lastAiIdx - 2 && prior[lastAiIdx - 2]?.role === "ai") return "compact";
  return "minimal";
}

function buildPromptBody(prior: WorkflowMessage[]): string {
  const lastAiIdx = prior.reduce((acc, m, i) => (m.role === "ai" ? i : acc), -1);
  const turns = prior
    .map((m, idx) => formatTurn(m, idx, m.role === "user" ? "compact" : assistantMode(idx, prior, lastAiIdx)))
    .join("\n\n---\n\n");

  return ["===== CONVERSATION =====", turns, "===== END ====="].join("\n");
}

function assemblePrompt(historyBlock: string, currentUserMsg: string): string {
  return [INSTRUCTIONS, "", historyBlock, "", "### CURRENT USER MESSAGE", currentUserMsg].join("\n");
}

export function buildFullConversationPrompt(
  prior: WorkflowMessage[],
  currentUserMsg: string
): string {
  if (prior.length === 0) return clip(currentUserMsg, MAX_PROMPT_CHARS);

  let trimmed = [...prior];
  let prompt = assemblePrompt(buildPromptBody(trimmed), currentUserMsg);

  while (prompt.length > MAX_PROMPT_CHARS && trimmed.length > 2) {
    trimmed = trimmed.slice(2);
    prompt = assemblePrompt(buildPromptBody(trimmed), currentUserMsg);
  }

  if (prompt.length > MAX_PROMPT_CHARS) {
    const footer = `\n\n### CURRENT USER MESSAGE\n${currentUserMsg}`;
    const headBudget = MAX_PROMPT_CHARS - footer.length - 120;
    const briefHistory = [
      "===== CONVERSATION =====",
      "(earlier turns omitted)",
      trimmed.length
        ? formatTurn(trimmed[trimmed.length - 1], trimmed.length - 1, "minimal")
        : "",
      "===== END =====",
    ].join("\n");
    prompt = `${INSTRUCTIONS}\n\n${briefHistory.slice(0, Math.max(0, headBudget))}${footer}`;
  }

  return prompt.slice(0, MAX_PROMPT_CHARS);
}
