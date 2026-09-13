"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Check, FilePenLine, FilePlus, MessageCircle, Plus } from "lucide-react";
import {
  DEFAULT_CHAT_CONFIG,
  PAYMENT_CATEGORIES,
  type ChatSessionConfig,
  type ChatType,
  defaultShapForChatType,
  defaultSemanticMlForChatType,
} from "@/lib/workflow/categories";

const CHAT_TYPES: { id: ChatType; title: string; desc: string; icon: typeof MessageCircle }[] = [
  {
    id: "general_query",
    title: "General query",
    desc: "Simple Q&A with RAG. No compliance score unless you enable SHAP in settings.",
    icon: MessageCircle,
  },
  {
    id: "new_report",
    title: "New compliance report",
    desc: "Build a report with rule-based score and SHAP drivers.",
    icon: FilePlus,
  },
  {
    id: "update_report",
    title: "Update existing report",
    desc: "Amend an existing compliance document with full scoring and XAI.",
    icon: FilePenLine,
  },
];

const STEPS = ["Conversation type", "Payment topics", "Settings"] as const;

type Props = {
  open: boolean;
  onComplete: (config: ChatSessionConfig) => void;
};

export function NewChatOnboardingModal({ open, onComplete }: Props) {
  const [chatType, setChatType] = useState<ChatType>(DEFAULT_CHAT_CONFIG.chatType);
  const [selected, setSelected] = useState<string[]>([]);
  const [mode, setMode] = useState<"selected" | "unsure" | "none">("unsure");
  const [shapEnabled, setShapEnabled] = useState(defaultShapForChatType(DEFAULT_CHAT_CONFIG.chatType));
  const [semanticMlEnabled, setSemanticMlEnabled] = useState(defaultSemanticMlForChatType(DEFAULT_CHAT_CONFIG.chatType));

  const toggleCategory = (id: string) => {
    setMode("selected");
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const chooseChatType = (nextType: ChatType) => {
    setChatType(nextType);
    setShapEnabled(defaultShapForChatType(nextType));
    setSemanticMlEnabled(defaultSemanticMlForChatType(nextType));
  };

  const finish = () => {
    const config: ChatSessionConfig = {
      chatType,
      selectedCategories: mode === "selected" ? selected : [],
      shapEnabled,
      semanticMlEnabled,
      categoryMode: mode,
    };
    onComplete(config);
    setChatType("general_query");
    setSelected([]);
    setMode("unsure");
    setShapEnabled(defaultShapForChatType("general_query"));
    setSemanticMlEnabled(defaultSemanticMlForChatType("general_query"));
  };

  const canStart = useMemo(() => {
    if (mode === "selected") return selected.length > 0;
    return mode === "unsure" || mode === "none";
  }, [mode, selected]);

  if (!open) return null;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-4xl px-4 py-8">
        <div>
          <p className="text-[11px] uppercase tracking-wider text-accent/75">Compliance Studio</p>
          <h1 className="mt-1 max-w-2xl text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            Let&apos;s configure this conversation first
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/55">
            Choose what type of conversation this is, which payment topics it should cover, and whether to
            turn on SHAP and semantic model reasoning. The prompt box opens only after you continue.
          </p>
        </div>

        <ol className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2">
          {STEPS.map((label, index) => (
            <li key={label} className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/15 text-[11px] font-semibold text-accent">
                {index + 1}
              </span>
              <span className="text-xs font-medium text-white/70">{label}</span>
              {index < STEPS.length - 1 && <span className="mx-1 h-px w-6 bg-white/15" aria-hidden />}
            </li>
          ))}
        </ol>

        <div className="mt-4 rounded-2xl border border-white/10 bg-[#0e1613]/85 p-5 shadow-2xl backdrop-blur-xl">
          <div className="space-y-6">
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-white/45">
                1. What type of conversation is this?
              </h2>
              <div className="grid gap-3 md:grid-cols-3">
                {CHAT_TYPES.map((type) => {
                  const Icon = type.icon;
                  const active = chatType === type.id;
                  return (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => chooseChatType(type.id)}
                      className={`min-h-[126px] rounded-xl border p-4 text-left transition ${
                        active ? "border-accent/55 bg-accent/12" : "border-white/10 bg-white/[0.025] hover:border-white/25"
                      }`}
                    >
                      <Icon className={`h-5 w-5 ${active ? "text-accent" : "text-white/45"}`} />
                      <p className="mt-3 font-medium text-white">{type.title}</p>
                      <p className="mt-1 text-sm leading-5 text-white/55">{type.desc}</p>
                    </button>
                  );
                })}
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-white/45">
                2. Which payment topics should we focus on?
              </h2>
              <div className="flex flex-wrap gap-2">
                {PAYMENT_CATEGORIES.map((category) => {
                  const on = selected.includes(category.id);
                  return (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => toggleCategory(category.id)}
                      className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm transition ${
                        on
                          ? "border-accent bg-accent text-ink"
                          : "border-white/15 bg-white/[0.025] text-white/78 hover:border-white/30"
                      }`}
                    >
                      <span>{category.label}</span>
                      {on ? (
                        <Check className="h-3.5 w-3.5 shrink-0 text-ink" strokeWidth={2.5} aria-hidden />
                      ) : (
                        <Plus className="h-3.5 w-3.5 shrink-0 opacity-80" strokeWidth={2} aria-hidden />
                      )}
                    </button>
                  );
                })}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setMode("unsure");
                    setSelected([]);
                  }}
                  className={`rounded-full border px-3 py-1.5 text-xs ${
                    mode === "unsure" ? "border-accent text-accent" : "border-white/15 text-white/60"
                  }`}
                >
                  I&apos;m not sure
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMode("none");
                    setSelected([]);
                  }}
                  className={`rounded-full border px-3 py-1.5 text-xs ${
                    mode === "none" ? "border-accent text-accent" : "border-white/15 text-white/60"
                  }`}
                >
                  None of these
                </button>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-white/45">
                3. Settings
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex cursor-pointer items-center justify-between gap-4 rounded-xl border border-white/10 bg-white/[0.025] p-4 text-sm text-white/80">
                  <span>
                    <span className="block font-medium text-white">Enable SHAP</span>
                    <span className="mt-1 block text-xs leading-5 text-white/45">
                      Shows why the score moved using official driver bars.
                    </span>
                  </span>
                  <input
                    type="checkbox"
                    checked={shapEnabled}
                    onChange={(event) => setShapEnabled(event.target.checked)}
                    className="h-4 w-4 shrink-0 accent-emerald-400"
                  />
                </label>
                <label className="flex cursor-pointer items-center justify-between gap-4 rounded-xl border border-white/10 bg-white/[0.025] p-4 text-sm text-white/80">
                  <span>
                    <span className="block font-medium text-white">Enable semantic model reasoning</span>
                    <span className="mt-1 block text-xs leading-5 text-white/45">
                      Runs category control checks trained from the regulation corpus.
                    </span>
                  </span>
                  <input
                    type="checkbox"
                    checked={semanticMlEnabled}
                    onChange={(event) => setSemanticMlEnabled(event.target.checked)}
                    className="h-4 w-4 shrink-0 accent-emerald-400"
                  />
                </label>
              </div>
              <p className="mt-3 text-xs leading-5 text-white/45">
                Nothing here is locked. You can change the categories, SHAP, and semantic model reasoning
                anytime from the settings (gear) icon beside the prompt box — mid-conversation or later.
              </p>
            </section>
          </div>

          <div className="flex justify-end border-t border-white/10 pt-4">
            <button
              type="button"
              disabled={!canStart}
              onClick={finish}
              className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-accent/90 disabled:opacity-40"
            >
              Continue to prompt
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}