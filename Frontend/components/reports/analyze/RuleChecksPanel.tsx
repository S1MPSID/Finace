"use client";

import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import type { OfficialAnalytics } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

const RISK_STYLES: Record<string, string> = {
  HIGH: "text-rose-400",
  MEDIUM: "text-amber-400",
  LOW: "text-emerald-400",
};

export function RuleChecksPanel({ stats }: { stats: OfficialAnalytics }) {
  if (stats.ruleChecks.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Rule engine results
          </p>
          <MetricInfoButton helpId="analyze_rules" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          Deterministic rule checks fired during this turn.
        </p>
        <ul className="mt-3 space-y-1.5">
          {stats.ruleChecks.map((rule) => {
            const riskStyle = RISK_STYLES[rule.riskLevel] || "text-white/50";
            return (
              <li
                key={rule.id}
                className="flex items-start gap-2 rounded-lg bg-black/20 px-3 py-2"
              >
                {rule.contribution < -6 ? (
                  <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-400" />
                ) : rule.contribution < 0 ? (
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
                ) : (
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                )}
                <div className="flex-1">
                  <span className="text-[12px] text-white/80">{rule.label}</span>
                  <span className={`ml-2 text-[10px] font-semibold uppercase tracking-wider ${riskStyle}`}>
                    {rule.riskLevel}
                  </span>
                </div>
                <span className="text-[11px] tabular-nums text-white/50">
                  {rule.contribution}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </motion.div>
  );
}
