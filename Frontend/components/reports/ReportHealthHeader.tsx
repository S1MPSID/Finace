import { motion } from "framer-motion";

export function ReportHealthHeader({ report }: { report: any }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.06 }}
      className="glass rounded-[2rem] p-6 border-white/10"
    >
      <div className="flex flex-wrap items-center gap-6">
        {/* Big score */}
        <div className="flex items-end gap-2">
          <span className="text-6xl font-bold text-white leading-none">{report.compliance_score ?? "--"}</span>
          <span className="text-white/30 text-xl mb-1">/ 100</span>
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-14 bg-white/10" />

        {/* Risk badge */}
        <div className="flex flex-col gap-1">
          <span className="text-[10px] uppercase tracking-widest text-white/30">Risk Level</span>
          <span className={`inline-flex rounded-full px-4 py-1.5 text-sm font-bold border w-fit ${report.risk_level === "HIGH"
            ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
            : report.risk_level === "MEDIUM"
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            }`}>
            {report.risk_level}
          </span>
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-14 bg-white/10" />

        {/* Meta chips */}
        <div className="flex flex-wrap gap-3 flex-1">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-widest text-white/30">Status</span>
            <span className={`text-sm font-semibold capitalize ${report.status === "verified" ? "text-emerald-400"
              : report.status === "rejected" ? "text-rose-400"
                : "text-amber-400"
              }`}>{report.status}</span>
          </div>
          <div className="hidden sm:block w-px h-10 bg-white/10 self-center" />
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-widest text-white/30">Regulator</span>
            <span className="text-sm text-white/80 font-medium">{report.workflow_input?.regulator || "RBI"}</span>
          </div>
          <div className="hidden sm:block w-px h-10 bg-white/10 self-center" />
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-widest text-white/30">Created</span>
            <span className="text-sm text-white/80 font-medium">{new Date(report.created_at).toLocaleDateString()}</span>
          </div>
          {report.evaluation_metadata?.evaluator_name && (
            <>
              <div className="hidden sm:block w-px h-10 bg-white/10 self-center" />
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] uppercase tracking-widest text-white/30">Reviewed by</span>
                <span className="text-sm text-white/80 font-medium">{report.evaluation_metadata.evaluator_name}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}
