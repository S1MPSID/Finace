import { motion } from "framer-motion";
import { Activity, ChartColumnIncreasing, Scale, ShieldCheck } from "lucide-react";
import { trustBand } from "@/lib/trust/buildAnalytics";
import type { TrustAnalytics } from "@/lib/trust/types";

export function TrustSummaryHeader({ stats }: { stats: TrustAnalytics }) {
  const band = trustBand(stats.trustIndex);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Model trust dashboard
          </p>
          <h2 className="mt-1 text-2xl font-medium text-white">Is this AI trustworthy?</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/55">
            Built from this session&apos;s hybrid engine outputs: retrieval evidence, rule/control
            signals, SHAP/LIME explainability, and score movement across turns.
          </p>
        </div>
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-wider text-white/40">Trust index</p>
          <p className="text-5xl font-semibold text-accent tabular-nums">{stats.trustIndex}</p>
          <span className={`mt-2 inline-flex border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${band.tone}`}>
            {band.label}
          </span>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { icon: Activity, label: "AI turns", value: String(stats.turns) },
          { icon: ChartColumnIncreasing, label: "Latest score", value: stats.latestScore != null ? String(stats.latestScore) : "—" },
          { icon: Scale, label: "Score Δ", value: `${stats.delta >= 0 ? "+" : ""}${stats.delta}` },
          { icon: ShieldCheck, label: "Latest risk", value: stats.latestRisk },
        ].map((card) => (
          <div key={card.label} className="panel-inset px-3 py-3">
            <div className="flex items-center gap-1.5 text-white/40">
              <card.icon className="h-3.5 w-3.5" />
              <span className="text-[10px] uppercase tracking-wider">{card.label}</span>
            </div>
            <p className="mt-1 text-xl font-medium text-white tabular-nums">{card.value}</p>
          </div>
        ))}
      </div>
      </div>
    </motion.div>
  );
}
