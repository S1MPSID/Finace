"use client";

import { motion } from "framer-motion";
import { Activity, ChevronDown, ArrowUpRight, ArrowDownRight } from "lucide-react";

const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"] as const;

type MlRiskPayload = {
  available?: boolean;
  risk_class?: string;
  probabilities?: Record<string, number>;
  probability_note?: string;
  model_version?: string;
  method?: string;
  control_coverage?: number;
  triggered_rule_counts?: { rule_id: string; name: string; triggered: boolean }[];
  explanation?: {
    method?: string;
    units?: string;
    target?: string;
    baseline?: number;
    predicted_probability?: number;
    top_risk_drivers?: string[];
    features?: {
      feature?: string;
      label?: string;
      value?: number;
      shap_value?: number;
    }[];
    notes?: string[];
  };
};

function riskTone(risk?: string) {
  const r = (risk || "").toUpperCase();
  if (r === "HIGH") return "text-rose-300 border-rose-400/30 bg-rose-500/10";
  if (r === "MEDIUM") return "text-amber-300 border-amber-400/30 bg-amber-500/10";
  return "text-emerald-300 border-emerald-400/30 bg-emerald-500/10";
}

function pct(value: number | undefined) {
  const n = Number(value ?? 0);
  return `${(n * 100).toFixed(1)}%`;
}

function probabilityBars(probabilities: Record<string, number> | undefined) {
  return RISK_LEVELS.map((level) => {
    const value = Number(probabilities?.[level] ?? 0);
    const tones =
      level === "HIGH"
        ? "bg-rose-400/80"
        : level === "MEDIUM"
          ? "bg-amber-400/80"
          : "bg-emerald-400/80";
    return { level, value, tones };
  });
}

export function MLRiskPanel({ mlRisk, compact = false }: { mlRisk?: MlRiskPayload | null; compact?: boolean }) {
  if (!mlRisk || mlRisk.available === false || mlRisk.available === undefined) {
    return null;
  }

  const drivers = mlRisk.explanation?.top_risk_drivers || [];
  const features = mlRisk.explanation?.features || [];
  const notes = mlRisk.explanation?.notes || [];
  const bars = probabilityBars(mlRisk.probabilities);
  const shownDrivers = compact ? drivers.slice(0, 3) : drivers.slice(0, 5);
  const explanationUnits = mlRisk.explanation?.units || "probability";
  const baselineIsProbability = !explanationUnits.includes("log_odds");

  return (
    <div className="border border-white/10 bg-[#2a2a2a] p-4 space-y-3 rounded-2xl">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent" />
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              ML Risk Prediction
            </p>
            <p className="text-xs text-white/55">
              {mlRisk.explanation?.method || "ml"}
              {mlRisk.risk_class ? ` · P(HIGH)=${pct(mlRisk.probabilities?.["HIGH"])}` : ""}
            </p>
          </div>
        </div>
        <span className={`border px-2 py-1 text-[10px] font-bold uppercase tracking-wider ${riskTone(mlRisk.risk_class)}`}>
          {mlRisk.risk_class || "--"}
        </span>
      </div>

      <div className="space-y-1.5">
        {bars.map((bar) => (
          <div key={bar.level} className="flex items-center gap-2">
            <span className="w-16 shrink-0 text-[10px] font-semibold uppercase tracking-wider text-white/40">
              {bar.level}
            </span>
            <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-white/5">
              <div
                className={`h-full rounded-full ${bar.tones}`}
                style={{ width: `${Math.min(100, Math.max(2, bar.value * 100))}%` }}
              />
            </div>
            <span className="w-14 shrink-0 text-right text-[10px] font-mono text-white/50">
              {pct(bar.value)}
            </span>
          </div>
        ))}
      </div>

      {mlRisk.explanation?.baseline !== undefined && (
        <p className="text-[10px] leading-4 text-white/35">
          {baselineIsProbability
            ? `Baseline P(HIGH) over training sample: ${(Number(mlRisk.explanation.baseline) * 100).toFixed(1)}%`
            : `Baseline raw HIGH-class log-odds over training sample: ${Number(mlRisk.explanation.baseline).toFixed(3)}`}
        </p>
      )}

      {shownDrivers.length > 0 && (
        <div className="space-y-1.5">
          {shownDrivers.map((driver) => {
            const up =
              driver.includes("raised") || driver.includes("present and raised") || driver.includes("+");
            return (
              <div key={driver} className="flex gap-2 items-start border border-white/5 px-2.5 py-2">
                {up ? (
                  <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-300" />
                ) : (
                  <ArrowDownRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-300" />
                )}
                <p className="text-xs leading-5 text-white/70">{driver}</p>
              </div>
            );
          })}
        </div>
      )}

      <details className="group space-y-0">
        <summary className="flex cursor-pointer items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-white/40 hover:text-white/70">
          <ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" />
          Technical details
        </summary>
        <div className="mt-2 space-y-2 border-l border-white/10 pl-3">
          {features.slice(0, 6).map((f) => (
            <div key={f.feature} className="flex items-center justify-between gap-2 text-[11px]">
              <span className="min-w-0 truncate text-white/60">{f.label || f.feature}</span>
              <span className="shrink-0 font-mono text-white/45">
                {Number(f.value ?? 0).toFixed(2)} → {Number(f.shap_value ?? 0).toFixed(3)}
              </span>
            </div>
          ))}
          <p className="text-[10px] leading-4 text-white/35">
            {explanationUnits} · model {mlRisk.model_version || "--"}
          </p>
          {mlRisk.probability_note && (
            <p className="text-[10px] leading-4 text-white/35">{mlRisk.probability_note}</p>
          )}
        </div>
      </details>

      {!compact && notes.length > 0 && (
        <p className="text-[10px] leading-4 text-white/35">{notes[0]}</p>
      )}
    </div>
  );
}
