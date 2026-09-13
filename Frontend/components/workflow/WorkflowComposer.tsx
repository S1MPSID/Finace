import { useEffect, useRef, useState } from "react";
import { Check, FileCheck, Mic, Plus, RefreshCw, Send, Settings } from "lucide-react";
import { PAYMENT_CATEGORIES, type ChatSessionConfig } from "@/lib/workflow/categories";

interface Props {
  input: string;
  loading: boolean;
  finalizing: boolean;
  hasMessages: boolean;
  chatConfig: ChatSessionConfig;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onFinalize: () => void;
  onShapEnabledChange: (enabled: boolean) => void;
  onSemanticMlEnabledChange: (enabled: boolean) => void;
  onCategoriesChange: (categories: string[]) => void;
  settingsHint?: string | null;
}

export function WorkflowComposer({
  input,
  loading,
  finalizing,
  hasMessages,
  chatConfig,
  onInputChange,
  onSend,
  onFinalize,
  onShapEnabledChange,
  onSemanticMlEnabledChange,
  onCategoriesChange,
  settingsHint,
}: Props) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const showGenerate = chatConfig.chatType !== "general_query";
  const showShapToggle = chatConfig.chatType === "general_query";

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
  }, [input]);

  const toggleCategory = (id: string) => {
    const selected = chatConfig.selectedCategories.includes(id)
      ? chatConfig.selectedCategories.filter((category) => category !== id)
      : [...chatConfig.selectedCategories, id];
    onCategoriesChange(selected);
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4">
      <div className="flex flex-col rounded-[24px] border border-white/10 bg-[#07100d]/88 backdrop-blur-xl shadow-glow focus-within:border-accent/35 transition">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="Ask anything"
          className="min-h-[88px] w-full resize-none overflow-y-auto bg-transparent px-5 pt-4 pb-3 text-[15px] leading-6 text-white/90 placeholder:text-white/35 focus:outline-none"
          rows={3}
          style={{ maxHeight: 220 }}
        />
        <div className="flex items-center justify-between px-3 pb-3 pt-1">
          <div className="flex items-center gap-2">
            {hasMessages && showGenerate && (
              <button
                type="button"
                onClick={onFinalize}
                disabled={finalizing || loading}
                className="inline-flex h-9 items-center gap-1.5 rounded-full bg-accent px-3.5 text-[12px] font-semibold text-ink hover:bg-accent/90 transition disabled:opacity-50"
              >
                {finalizing ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <FileCheck className="h-3.5 w-3.5" />
                )}
                Generate report
              </button>
            )}
            {chatConfig.selectedCategories.length > 0 && (
              <span className="hidden max-w-[240px] truncate text-[11px] text-white/45 sm:inline">
                {chatConfig.selectedCategories.join(", ")}
              </span>
            )}
            {showShapToggle && (chatConfig.shapEnabled || chatConfig.semanticMlEnabled) && (
              <span className="hidden sm:inline-flex items-center gap-2 text-[10px] uppercase tracking-wider text-white/40">
                {chatConfig.shapEnabled && <span className="text-emerald-400/90">SHAP</span>}
                {chatConfig.semanticMlEnabled && <span className="text-sky-300/90">Semantic ML</span>}
              </span>
            )}
          </div>
          <div className="relative flex items-center gap-1.5">
            <>
              <button
                type="button"
                onClick={() => setSettingsOpen((o) => !o)}
                className="flex h-9 w-9 items-center justify-center rounded-full text-white/50 hover:bg-white/10 hover:text-white"
                title="Chat settings"
              >
                <Settings className="h-4 w-4" />
              </button>
              {settingsOpen && (
                <div className="absolute bottom-11 right-0 z-20 max-h-[380px] w-[min(22rem,calc(100vw-2rem))] overflow-y-auto rounded-xl border border-white/10 bg-[#111a17] p-3 shadow-2xl">
                  {showShapToggle && (
                    <>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-white/35">Explainability</p>
                    <label className="mt-2 flex cursor-pointer items-center justify-between gap-2 text-sm text-white/80">
                      Enable SHAP
                      <input
                        type="checkbox"
                        checked={chatConfig.shapEnabled}
                        onChange={(e) => onShapEnabledChange(e.target.checked)}
                        className="accent-emerald-400"
                      />
                    </label>
                    <label className="mt-2 flex cursor-pointer items-center justify-between gap-2 text-sm text-white/80">
                      Enable semantic ML
                      <input
                        type="checkbox"
                        checked={chatConfig.semanticMlEnabled}
                        onChange={(e) => onSemanticMlEnabledChange(e.target.checked)}
                        className="accent-emerald-400"
                      />
                    </label>
                    <p className="mt-2 text-[11px] leading-relaxed text-white/40">
                      Driver bars and ML control checks use the official engine breakdown (not LLM guesses).
                    </p>
                    </>
                  )}
                  <div className={showShapToggle ? "mt-4 border-t border-white/10 pt-3" : ""}>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-white/35">
                      Categories
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {PAYMENT_CATEGORIES.map((category) => {
                        const selected = chatConfig.selectedCategories.includes(category.id);
                        return (
                          <button
                            key={category.id}
                            type="button"
                            onClick={() => toggleCategory(category.id)}
                            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-xs transition ${
                              selected
                                ? "border-accent bg-accent text-ink"
                                : "border-white/12 text-white/70 hover:border-white/25 hover:text-white"
                            }`}
                          >
                            <span>{category.label}</span>
                            {selected ? (
                              <Check className="h-3 w-3 shrink-0" strokeWidth={2.5} />
                            ) : (
                              <Plus className="h-3 w-3 shrink-0 opacity-70" strokeWidth={2} />
                            )}
                          </button>
                        );
                      })}
                    </div>
                    <button
                      type="button"
                      onClick={() => onCategoriesChange([])}
                      className="mt-3 text-xs text-white/45 hover:text-white/75"
                    >
                      Clear categories
                    </button>
                  </div>
                </div>
              )}
            </>
            <span className="flex h-9 w-9 items-center justify-center rounded-full text-white/25">
              <Mic className="h-4 w-4" />
            </span>
            <button
              type="button"
              onClick={onSend}
              disabled={loading || !input.trim()}
              title="Send"
              aria-label="Send message"
              className={`flex h-9 w-9 items-center justify-center rounded-full transition ${
                input.trim() ? "bg-accent text-ink" : "bg-white/10 text-white/25"
              }`}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
      {settingsHint && (
        <p className="mt-2 text-center text-[11px] text-white/45">{settingsHint}</p>
      )}
      <p className="mt-3 text-center text-[11px] text-white/30">
        Finace can make mistakes. Verify against primary regulations before acting.
      </p>
    </div>
  );
}
