"use client";

import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { OfficialAnalytics, ScoreBreakdownRow } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";
import { ChartTip } from "./ChartTip";

function WaterfallTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const data = payload[0]?.payload;
  if (!data) return null;
  return (
    <ChartTip>
      <p className="text-[11px] font-medium text-white">{data.label}</p>
      <p className="text-[11px] text-white/70">
        Contribution:{" "}
        <span className={`font-medium ${data.contribution >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
          {data.contribution >= 0 ? "+" : ""}{data.contribution}
        </span>
      </p>
    </ChartTip>
  );
}

interface WaterfallBar {
  label: string;
  base: number;
  value: number;
  fill: string;
}

function _buildWaterfallBars(breakdown: ScoreBreakdownRow[], baseline: number): WaterfallBar[] {
  const bars: WaterfallBar[] = [];
  let running = baseline;

  bars.push({
    label: `φ₀ = ${baseline}`,
    base: 0,
    value: baseline,
    fill: "rgba(148,163,184,0.55)",
  });

  for (const row of breakdown) {
    const contribution = Number(row.contribution ?? row.shap_value ?? 0);
    if (Math.abs(contribution) < 0.01) continue;
    const start = contribution >= 0 ? running : running + contribution;
    bars.push({
      label: row.label || row.feature,
      base: start,
      value: Math.abs(contribution),
      fill: contribution >= 0 ? "#34d399" : "#fb7185",
    });
    running += contribution;
  }

  bars.push({
    label: `Score = ${Math.round(Math.max(0, Math.min(100, running)) * 10) / 10}`,
    base: 0,
    value: Math.max(0, Math.min(100, running)),
    fill: "rgba(167,139,250,0.75)",
  });

  return bars;
}

export function WaterfallChart({ stats }: { stats: OfficialAnalytics }) {
  if (stats.waterfall.length === 0 || stats.baselineScore == null) return null;
  const waterfallData = _buildWaterfallBars(stats.waterfall, stats.baselineScore);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Why this score?
          </p>
          <MetricInfoButton helpId="analyze_waterfall" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          Waterfall from baseline φ₀ through each factor to the official score.
        </p>
        <div className="mt-4 h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={waterfallData}
              layout="vertical"
              margin={{ top: 5, right: 20, bottom: 0, left: 10 }}
              barCategoryGap="18%"
            >
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: "rgba(255,255,255,0.35)" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={160}
                tick={{ fontSize: 10, fill: "rgba(255,255,255,0.5)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<WaterfallTooltip />} />
              <Bar dataKey="base" stackId="waterfall" fill="transparent" radius={0} />
              <Bar dataKey="value" stackId="waterfall" radius={[0, 4, 4, 0]}>
                {waterfallData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  );
}
