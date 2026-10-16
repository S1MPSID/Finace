import { Info, ShieldAlert, CheckCircle2, FileText, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";

export function ReportDetails({ report }: { report: any }) {
  return (
    <>
      {/* Row 2: Executive Summary */}
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
          className="text-white/80 leading-relaxed text-base prose-custom"
          dangerouslySetInnerHTML={{ __html: report.explanation }} 
        />
      </motion.div>

      {/* Row 3: Risk Flags + Recommendations side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risk Flags */}
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
                <span>{flag}</span>
              </li>
            ))}
            {(!report.risk_flags || report.risk_flags.length === 0) && (
              <p className="text-white/30 text-sm italic">No risk flags detected.</p>
            )}
          </ul>
        </motion.div>

        {/* Recommendations */}
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
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      {/* Row 4: Legal Citations — full width */}
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
            const backendBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1").replace(/\/api\/v1\/?$/, "");
            const hasPath = clause.source && (clause.source.endsWith(".pdf") || clause.source.includes("/") || clause.source.includes("\\"));
            const docUrl = hasPath ? `${backendBase}/docs/${clause.source.replace(/\\/g, "/")}` : null;
            return (
              <div key={i} className="border-l-2 border-accent/20 pl-5 py-1">
                {docUrl ? (
                  <a href={docUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs font-mono text-accent mb-1.5 hover:text-white transition group">
                    <FileText className="w-3 h-3 text-accent/60 group-hover:text-white transition" />
                    {clause.source.split(/[/\\]/).pop() || clause.source}
                    <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition" />
                  </a>
                ) : (
                  <p className="text-xs font-mono text-accent mb-1.5">{clause.source || "Regulation"}</p>
                )}
                <h4 className="text-white font-semibold text-sm mb-1.5">{clause.title || "Untitled Clause"}</h4>
                <p className="text-xs text-white/45 leading-relaxed italic line-clamp-3 hover:line-clamp-none transition-all cursor-pointer">&quot;{clause.text}&quot;</p>
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
