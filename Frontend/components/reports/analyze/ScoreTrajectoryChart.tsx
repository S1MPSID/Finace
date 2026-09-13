"use client";

import { motion } from "framer-motion";
import {
  ComposedChart,
  Line,
  ReferenceLine,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { OfficialAnalytics } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";
import { ChartTip } from "./ChartTip";

function TrajectoryTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <ChartTip>
      <p className="text-[11px] font-medium text-white">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.name} className="text-[11px] text-white/70">
          {entry.name === "score" ? "Official score" : "Baseline (φ₀)"}:{" "}
          <span className="font-medium text-white">{entry.value}</span>
        </p>
      ))}
    </ChartTip>
  );
}

export function ScoreTrajectoryChart({ stats }: { stats: OfficialAnalytics }) {
  if (stats.trajectory.length === 0) return null;
  const baseline = stats.baselineScore ?? 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Score trajectory
          </p>
          <MetricInfoButton helpId="analyze_trajectory" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          Official compliance score per turn with baseline reference.
        </p>
        <div className="mt-4 h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={stats.trajectory} margin={{ top: 5, right: 10, bottom: 0, left: -10 }}>
              <XAxis
                dataKey="turn"
                tick={{ fontSize: 11, fill: "rgba(255,255,255,0.45)" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: "rgba(255,255,255,0.35)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<TrajectoryTooltip />} />
              <ReferenceLine
                y={baseline}
                stroke="rgba(148,163,184,0.4)"
                strokeDasharray="6 4"
                label={{
                  value: `φ₀ ${baseline}`,
                  position: "right",
                  fill: "rgba(148,163,184,0.6)",
                  fontSize: 10,
                }}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#34d399"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#34d399", strokeWidth: 0 }}
                activeDot={{ r: 6, stroke: "#fff", strokeWidth: 2 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  );
}
