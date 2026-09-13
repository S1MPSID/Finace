"use client";

import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, XCircle, HelpCircle } from "lucide-react";
import type { OfficialAnalytics } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; bg: string }> = {
  COMPLIANT: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  PARTIAL: { icon: AlertCircle, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  MISSING: { icon: XCircle, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  UNKNOWN: { icon: HelpCircle, color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/20" },
};

export function SemanticMLPanel({ stats }: { stats: OfficialAnalytics }) {
  if (stats.semanticItems.length === 0) return null;

  const avgConfidence =
    stats.semanticItems.reduce((sum, item) => sum + (item.confidence || 0), 0) /
    Math.max(stats.semanticItems.length, 1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Semantic ML evaluation
          </p>
          <MetricInfoButton helpId="analyze_semantic_ml" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          ML model status per requirement (trained on labelled compliance examples).
        </p>
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-black/20 px-3 py-2">
          <span className="text-[11px] text-white/50">Overall semantic confidence:</span>
          <span className="text-[12px] font-medium text-white tabular-nums">
            {Math.round(avgConfidence * 100)}%
          </span>
        </div>
        <ul className="mt-3 space-y-2">
          {stats.semanticItems.map((item) => {
            const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.UNKNOWN;
            const Icon = config.icon;
            return (
              <li
                key={item.requirement_id}
                className="flex items-center justify-between rounded-lg bg-black/20 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${config.bg}`}>
                    <Icon className={`h-3 w-3 ${config.color}`} />
                    {item.status}
                  </span>
                  <span className="text-[12px] text-white/70">
                    {item.display_name || item.label || item.requirement_id}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="tabular-nums text-white/50">
                    {Math.round(item.confidence * 100)}%
                  </span>
                  <span className="text-[9px] uppercase tracking-wider text-white/30">
                    {item.model_source || "ml"}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </motion.div>
  );
}
