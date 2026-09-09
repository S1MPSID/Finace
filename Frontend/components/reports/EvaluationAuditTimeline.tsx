"use client";

import { ClipboardList, ExternalLink, FileText } from "lucide-react";
import { FieldChangeDiff } from "@/components/reports/FieldChangeDiff";
import { useDocCatalog } from "@/hooks/useDocCatalog";
import { openDocPdf } from "@/lib/docs/docCatalog";
import { groupEvaluationLogs } from "@/lib/evaluation/groupEvaluationLogs";
import { htmlToPlainText } from "@/lib/text/htmlToPlain";

const ACTION_LABELS: Record<string, string> = {
  amendment: "Manual amendment",
  reference_added: "Reference added",
  verified: "Report verified",
  rejected: "Report rejected",
  ai_refresh: "AI re-assessment",
};

function ReferenceBlock({ reference, catalog }: { reference: any; catalog: ReturnType<typeof useDocCatalog>["catalog"] }) {
  if (!reference) return null;
  const quote = htmlToPlainText(String(reference.reference_text || ""));
  return (
    <div className="mt-4 rounded-xl border border-accent/40 bg-accent/5 p-4">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-accent/80 mb-2">
        Regulatory reference
      </p>
      <button
        type="button"
        onClick={() => openDocPdf(reference.document_path || reference.document_name, catalog)}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent hover:underline"
      >
        <FileText className="w-3 h-3" />
        {reference.document_name}
        <ExternalLink className="w-3 h-3" />
      </button>
      {quote && (
        <p className="mt-2 text-xs text-white/60 leading-relaxed italic">
          &quot;{quote.length > 400 ? `${quote.slice(0, 400)}…` : quote}&quot;
        </p>
      )}
    </div>
  );
}

export function EvaluationAuditTimeline({ logs = [] }: { logs?: any[]; references?: any[] }) {
  const { catalog } = useDocCatalog();
  const grouped = groupEvaluationLogs(logs);

  if (grouped.length === 0) {
    return (
      <div className="glass rounded-[2rem] p-6 border border-accent/30">
        <p className="text-sm text-white/40">No evaluation changes recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="glass rounded-[2rem] p-6 border border-accent/30 space-y-6">
      <div className="flex items-center gap-2">
        <ClipboardList className="w-4 h-4 text-accent" />
        <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">
          Evaluation Audit Trail
        </h3>
      </div>

      <div className="space-y-5">
        {grouped.map((entry: any) => (
          <div
            key={entry.log_id}
            className="rounded-xl border border-accent/35 bg-white/[0.02] p-4"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold uppercase text-accent/80">
                {ACTION_LABELS[entry.action] || entry.action}
              </span>
              <span className="text-[10px] text-white/35">
                {entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}
              </span>
            </div>
            <p className="text-xs text-white/55 mt-1">
              {entry.actor_name} ({entry.actor_role || "evaluator"})
            </p>
            {entry.comment && (
              <p className="mt-2 text-sm text-white/70 leading-relaxed">{htmlToPlainText(entry.comment)}</p>
            )}

            {Array.isArray(entry.changes) &&
              entry.changes.map((ch: any, i: number) => (
                <FieldChangeDiff key={i} field={ch.field} oldValue={ch.old_value} newValue={ch.new_value} />
              ))}

            <ReferenceBlock reference={entry.reference} catalog={catalog} />
          </div>
        ))}
      </div>
    </div>
  );
}
