import { FileCheck, Mic, RefreshCw, Send, Sparkles } from "lucide-react";

interface Props {
  input: string;
  loading: boolean;
  finalizing: boolean;
  hasMessages: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onFinalize: () => void;
}

export function WorkflowComposer({
  input,
  loading,
  finalizing,
  hasMessages,
  onInputChange,
  onSend,
  onFinalize,
}: Props) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4">
      <div className="flex flex-col rounded-[28px] border border-white/10 bg-white/[0.04] backdrop-blur-xl shadow-glow focus-within:border-accent/35 transition">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="Ask anything"
          className="w-full resize-none bg-transparent px-5 pt-4 pb-2 text-[15px] text-white/90 placeholder:text-white/35 focus:outline-none min-h-[52px] max-h-40"
          rows={Math.min(4, Math.max(1, input.split("\n").length))}
        />
        <div className="flex items-center justify-between px-3 pb-3 pt-1">
          <div className="flex items-center gap-2">
            {hasMessages && (
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
            <span className="hidden sm:inline-flex items-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-2.5 py-1 text-[10px] uppercase tracking-wider text-accent">
              <Sparkles className="h-3 w-3" />
              XAI
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-full text-white/25">
              <Mic className="h-4 w-4" />
            </span>
            <button
              type="button"
              onClick={onSend}
              disabled={loading || !input.trim()}
              className={`flex h-9 w-9 items-center justify-center rounded-full transition ${
                input.trim() ? "bg-accent text-ink" : "bg-white/10 text-white/25"
              }`}
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
      <p className="mt-3 text-center text-[11px] text-white/30">
        Finace can make mistakes. Verify against primary regulations before acting.
      </p>
    </div>
  );
}
