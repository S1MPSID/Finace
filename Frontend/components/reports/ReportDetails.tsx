import { Info, ShieldAlert, CheckCircle2, FileText, ExternalLink, ListOrdered } from "lucide-react";
import { motion } from "framer-motion";
import { ExplainabilityPanel } from "@/components/reports/ExplainabilityPanel";
import { MLRiskPanel } from "@/components/reports/MLRiskPanel";
import { EvidenceScopeNotice } from "@/components/reports/EvidenceScopeNotice";
import { RuleImpactPanel } from "@/components/reports/RuleImpactPanel";
import { isPdfSourcePath, resolvePublicDocUrl } from "@/lib/docs/publicDocUrl";
import { useDocCatalog } from "@/hooks/useDocCatalog";
import { resolveDocPath } from "@/lib/docs/docCatalog";
import { toDisplayHtml, toDisplayText } from "@/lib/text/renderRich";

export function ReportDetails({ report }: { report: any }) {
  const { catalog } = useDocCatalog();

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="glass rounded-[2rem] p-8 border-white/10"
      >
        <div className="flex items-center gap-2 mb-5">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <Info className="w-4 h-4 text-blue-400" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Executive Summary</h3>
        </div>
        <div
          className="text-white/80 leading-relaxed text-base prose-custom [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_h2]:mt-4 [&_h3]:text-base [&_h3]:font-semibold [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-1"
          dangerouslySetInnerHTML={{ __html: toDisplayHtml(report.explanation || "") }}
        />
      </motion.div>

      <ExplainabilityPanel xai={report.xai} />

      <MLRiskPanel mlRisk={report.ml_risk} />

      <EvidenceScopeNotice scope={report.evidence_scope} />
      <RuleImpactPanel assessments={report.rule_assessments} />

      {!!report.reasoning_steps?.length && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-[2rem] p-6 border-white/10"
        >
          <div className="flex items-center gap-2 mb-5">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <ListOrdered className="w-4 h-4 text-amber-300" />
            </div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Decision Path</h3>
          </div>
          <ol className="space-y-3">
            {report.reasoning_steps.map((step: string, i: number) => (
              <li key={`${step}-${i}`} className="flex gap-3 text-sm text-white/70 leading-6">
                <span className="shrink-0 w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[11px] text-accent">
                  {i + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.14 }}
          className="glass rounded-[2rem] p-6 border-white/10 flex flex-col min-h-[220px]"
        >
          <div className="flex items-center gap-2 mb-5">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            </div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Risk Flags</h3>
          </div>
          <ul className="space-y-3 flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {(report.risk_flags || []).map((flag: string, i: number) => (
              <li key={i} className="flex gap-3 items-start text-sm text-white/70 leading-6">
                <span className="shrink-0 h-1.5 w-1.5 rounded-full bg-rose-400 mt-2.5" />
                <span>{toDisplayText(flag)}</span>
              </li>
            ))}
            {(!report.risk_flags || report.risk_flags.length === 0) && (
              <p className="text-white/30 text-sm italic">No risk flags detected.</p>
            )}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18 }}
          className="glass rounded-[2rem] p-6 border-white/10 flex flex-col min-h-[220px]"
        >
          <div className="flex items-center gap-2 mb-5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Recommendations</h3>
          </div>
          <ul className="space-y-3 flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {(report.recommendations || []).map((rec: string, i: number) => (
              <li key={i} className="flex gap-3 items-start text-sm text-white/70 leading-6">
                <span className="shrink-0 h-1.5 w-1.5 rounded-full bg-emerald-400 mt-2.5" />
                <span>{toDisplayText(rec)}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.22 }}
        className="glass rounded-[2rem] p-8 border-white/10"
      >
        <div className="flex items-center gap-2 mb-7">
          <div className="p-2 rounded-lg bg-accent/10 border border-accent/20">
            <FileText className="w-4 h-4 text-accent" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">Legal Citations</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-6">
          {(report.applicable_clauses || []).map((clause: any, i: number) => {
            const source = clause.source || clause.document_name || "";
            const resolvedPath =
              clause.document_path ||
              resolveDocPath(clause.document_name || "", catalog) ||
              (isPdfSourcePath(source) ? source : resolveDocPath(source, catalog));
            const docUrl = resolvedPath ? resolvePublicDocUrl(resolvedPath) : null;
            const displayName =
              clause.document_name ||
              (resolvedPath ? resolvedPath.split("/").pop()?.replace(/\.pdf$/i, "") : "") ||
              source ||
              "Legal Reference";

            return (
              <div
                key={i}
                className="group relative border-l-2 border-accent/20 pl-5 py-3 transition-all duration-300 hover:border-accent hover:bg-white/[0.03] rounded-r-2xl"
              >
                <div className="flex items-center justify-between mb-2 gap-2">
                  {docUrl ? (
                    <a
                      href={docUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1.5 text-[10px] font-mono text-accent/80 hover:text-accent transition-colors underline-offset-2 hover:underline"
                    >
                      <FileText className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate max-w-[220px]">{displayName}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  ) : (
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-accent/60">
                      <FileText className="w-3.5 h-3.5" />
                      <span className="truncate max-w-[220px]">{displayName}</span>
                    </div>
                  )}
                </div>

                <h4 className="text-white font-semibold text-sm mb-2 group-hover:text-accent transition-colors">
                  {toDisplayText(clause.title || "Compliance Clause")}
                </h4>

                <div className="relative overflow-hidden transition-all duration-500 ease-in-out max-h-20 group-hover:max-h-[500px]">
                  <p className="text-xs text-white/45 leading-relaxed italic group-hover:text-white/70 transition-colors">
                    &quot;{toDisplayText(clause.text || "")}&quot;
                  </p>
                  <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-[#0d1413] to-transparent group-hover:opacity-0 transition-opacity duration-300" />
                </div>
              </div>
            );
          })}
          {(!report.applicable_clauses || report.applicable_clauses.length === 0) && (
            <div className="col-span-2 text-center py-10 opacity-30">
              <FileText className="w-10 h-10 mx-auto mb-2" />
              <p>No clauses linked.</p>
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
}
