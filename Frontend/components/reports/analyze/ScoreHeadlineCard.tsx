"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { trustBand } from "@/lib/trust/buildAnalytics";
import type { OfficialAnalytics } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

export function ScoreHeadlineCard({ stats }: { stats: OfficialAnalytics }) {
  const score = stats.officialScore;
  const baseline = stats.baselineScore;
  const delta = stats.delta;
  const band = score != null ? trustBand(score) : null;

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
              Compliance score
            </p>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-5xl font-semibold text-white tabular-nums">
                {score != null ? score : "—"}
              </span>
              <span className="text-lg text-white/40">/100</span>
            </div>
            {band && (
              <span className={`mt-2 inline-flex border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${band.tone}`}>
                {band.label}
              </span>
            )}
          </div>
          <div className="text-right">
            <div className="space-y-2">
              <div>
                <p className="flex items-center justify-end gap-1 text-[11px] uppercase tracking-wider text-white/40">
                  Baseline (φ₀)
                  <MetricInfoButton helpId="analyze_baseline" />
                </p>
                <p className="text-2xl font-medium text-white/70 tabular-nums">
                  {baseline != null ? baseline : "—"}
                </p>
              </div>
              <div>
                <p className="flex items-center justify-end gap-1 text-[11px] uppercase tracking-wider text-white/40">
                  Change from baseline
                </p>
                <p className={`flex items-center justify-end gap-1 text-2xl font-medium tabular-nums ${
                  delta > 0 ? "text-emerald-400" : delta < 0 ? "text-rose-400" : "text-white/50"
                }`}>
                  {delta > 0 ? <TrendingUp className="h-4 w-4" /> : delta < 0 ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />}
                  {delta >= 0 ? "+" : ""}{delta}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
