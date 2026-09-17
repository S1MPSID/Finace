"use client";

import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, XCircle, HelpCircle } from "lucide-react";
import type { OfficialAnalytics, RequirementRow } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; bg: string }> = {
  COMPLIANT: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  PARTIAL: { icon: AlertCircle, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  MISSING: { icon: XCircle, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  UNKNOWN: { icon: HelpCircle, color: "text-slate-400", bg: "bg-slate-500/10 border-slate-500/20" },
};

function RequirementRowView({ row }: { row: RequirementRow }) {
  const config = STATUS_CONFIG[row.status] || STATUS_CONFIG.UNKNOWN;
  const Icon = config.icon;
  return (
    <tr className="border-b border-white/5 last:border-0">
      <td className="py-2.5 pr-3 text-[12px] text-white/70">{row.requirement}</td>
      <td className="py-2.5 pr-3">
        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${config.bg}`}>
          <Icon className={`h-3 w-3 ${config.color}`} />
          {row.status}
        </span>
      </td>
      <td className="py-2.5 pr-3 text-right tabular-nums text-[11px] text-white/60">
        {row.confidence > 0 ? `${Math.round(row.confidence * 100)}%` : "—"}
      </td>
      <td className={`py-2.5 text-right tabular-nums text-[11px] font-medium ${
        row.contribution >= 0 ? "text-emerald-400" : "text-rose-400"
      }`}>
        {row.contribution >= 0 ? "+" : ""}{row.contribution}
      </td>
    </tr>
  );
}

export function RequirementsTable({ stats }: { stats: OfficialAnalytics }) {
  if (stats.requirements.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Compliance requirements breakdown
          </p>
          <MetricInfoButton helpId="analyze_requirements" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          Per-requirement status and contribution to the official score.
        </p>
        <table className="mt-4 w-full text-left">
          <thead>
            <tr className="border-b border-white/10 text-[10px] uppercase tracking-wider text-white/40">
              <th className="pb-2 pr-3 font-medium">Requirement</th>
              <th className="pb-2 pr-3 font-medium">Status</th>
              <th className="pb-2 pr-3 text-right font-medium">Confidence</th>
              <th className="pb-2 text-right font-medium">Impact</th>
            </tr>
          </thead>
          <tbody>
            {stats.requirements.map((row) => (
              <RequirementRowView key={row.id} row={row} />
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
