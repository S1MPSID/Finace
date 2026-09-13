import { motion } from "framer-motion";
import { ExternalLink, ShieldAlert, User as UserIcon } from "lucide-react";
import { ExplainabilityPanel } from "@/components/reports/ExplainabilityPanel";
import { resolvePublicDocUrl, isPdfSourcePath } from "@/lib/docs/publicDocUrl";
import { sourceLabel } from "@/lib/workflow/sourceUtils";
import type { WorkflowMessage } from "@/lib/workflow/types";

function formatMessageHtml(content: string) {
  return content
    .replace(/<h[1-6]>/gi, "<br/><br/><strong class='text-accent uppercase tracking-wider block mb-2 text-[12px]'>")
    .replace(/<\/h[1-6]>/gi, "</strong>")
    .replace(/<p>/gi, "<div class='mb-2'>")
    .replace(/<\/p>/gi, "</div>");
}

interface Props {
  messages: WorkflowMessage[];
  loading: boolean;
  scrollRef: React.RefObject<HTMLDivElement | null>;
}

export function WorkflowMessageList({ messages, loading, scrollRef }: Props) {
  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-3 pb-4 pt-16"
      style={{ scrollbarWidth: "thin" }}
    >
      <div className="mx-auto w-full max-w-3xl space-y-6">
        {messages.map((m, i) => (
          <motion.div
            key={`${m.role}-${i}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}
          >
            {m.role === "ai" && (
              <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15">
                <ShieldAlert className="h-3.5 w-3.5 text-accent" />
              </div>
            )}
            <div className={`max-w-[92%] space-y-3 ${m.role === "user" ? "" : "min-w-0 flex-1"}`}>
              <div
                className={`px-4 py-3 text-[15px] leading-7 ${
                  m.role === "user"
                    ? "rounded-[22px] border border-white/10 bg-white/[0.06] backdrop-blur-sm text-white/90"
                    : "text-white/80"
                }`}
                dangerouslySetInnerHTML={{ __html: formatMessageHtml(m.content) }}
              />

              {m.role === "ai" && m.sources && m.sources.length > 0 && (
                <SourceList sources={m.sources} />
              )}

              {m.data?.risk_flags && m.data.risk_flags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {m.data.risk_flags.map((flag, fi) => (
                    <span
                      key={fi}
                      className="rounded-full border border-rose-400/20 bg-rose-500/10 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-rose-300"
                    >
                      {flag}
                    </span>
                  ))}
                </div>
              )}

              {m.role === "ai" && m.data?.xai && (
                <ExplainabilityPanel xai={m.data.xai} compact />
              )}
            </div>
            {m.role === "user" && (
              <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/10">
                <UserIcon className="h-3.5 w-3.5 text-white/50" />
              </div>
            )}
          </motion.div>
        ))}

        {loading && <TypingIndicator />}
      </div>
    </div>
  );
}

function SourceList({ sources }: { sources: any[] }) {
  return (
    <div className="space-y-1 border-l-2 border-white/10 pl-3">
      <p className="text-[11px] font-medium uppercase tracking-wider text-white/35">Sources</p>
      {sources.map((source, si) => {
        const relPath = source.relative_path || source.source_file || source.document_id || "";
        const docUrl = isPdfSourcePath(relPath) ? resolvePublicDocUrl(relPath) : null;
        const fileName = sourceLabel(source);

        return docUrl ? (
          <a
            key={si}
            href={docUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-[13px] text-accent/90 hover:text-accent"
          >
            <span className="truncate">{fileName}</span>
            <ExternalLink className="h-3 w-3 shrink-0 opacity-50" />
          </a>
        ) : (
          <p key={si} className="truncate text-[13px] text-white/40">
            {fileName}
          </p>
        );
      })}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/15">
        <ShieldAlert className="h-3.5 w-3.5 animate-pulse text-accent" />
      </div>
      <div className="flex items-center gap-1.5 py-2">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40 [animation-delay:0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/40 [animation-delay:0.3s]" />
      </div>
    </div>
  );
}
