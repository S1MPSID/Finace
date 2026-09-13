"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { BrainCircuit, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

type XaiFeature = {
  feature?: string;
  label?: string;
  shap_value?: number;
  layer?: string;
  status?: string;
  model_source?: string;
};

type SemanticRow = {
  category?: string;
  display_name?: string;
  label?: string;
  status?: string;
  penalty_points?: number;
  confidence?: number;
  model_source?: string;
};

type BreakdownRow = {
  label?: string;
  contribution?: number;
  shap_value?: number;
  direction?: string;
  layer?: string;
  status?: string;
  model_source?: string;
};

type XaiPayload = {
  observed_score?: number;
  baseline_score?: number;
  observed_risk?: string;
  top_drivers?: string[];
  semantic_evaluation?: SemanticRow[];
  score_breakdown?: BreakdownRow[];
  shap?: { features?: XaiFeature[] };
};

/** Compliance index vs frozen φ₀ — not “high score = bad”. */
function indexVsBenchmark(observed?: number, baseline?: number) {
  if (observed == null || baseline == null) {
    return { delta: null as number | null, label: "Compliance index", detail: "" };
  }
  const delta = observed - baseline;
  const rounded = Math.round(delta * 10) / 10;
  if (rounded > 0.05) {
    return {
      delta: rounded,
      label: `Index ${observed}`,
      detail: `${rounded > 0 ? "+" : ""}${rounded} vs benchmark φ₀ ${baseline}`,
    };
  }
  if (rounded < -0.05) {
    return {
      delta: rounded,
      label: `Index ${observed}`,
      detail: `${rounded} vs benchmark φ₀ ${baseline}`,
    };
  }
  return { delta: 0, label: `Index ${observed}`, detail: `Near benchmark φ₀ ${baseline}` };
}

function indexBadgeClass(delta: number | null) {
  if (delta == null) return "border-white/20 bg-white/[0.06] text-white/85";
  if (delta > 0) return "border-emerald-400/50 bg-emerald-500/20 text-emerald-100";
  if (delta < 0) return "border-amber-400/45 bg-amber-500/15 text-amber-100";
  return "border-sky-400/40 bg-sky-500/15 text-sky-100";
}

function ruleExposureTone(risk?: string) {
  const r = (risk || "").toUpperCase();
  if (r === "HIGH") return "border-rose-400/35 bg-rose-500/10 text-rose-200";
  if (r === "MEDIUM") return "border-amber-400/35 bg-amber-500/10 text-amber-100";
  return "border-white/15 bg-white/[0.04] text-white/55";
}

function cleanDriverText(text: string) {
  return text
    .replace(/semantic:SEM_[A-Z0-9_]+/gi, "")
    .replace(/\bsemantic:/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function toBarRows(features: XaiFeature[] | undefined) {
  return (features || [])
    .map((item) => {
      const value = Number(item.shap_value ?? 0);
      let label = item.label || "Factor";
      if (label.includes("semantic:") || label.startsWith("SEM_")) {
        label = item.label?.includes("·") ? item.label : "Control check";
      }
      return {
        id: item.feature || label,
        label,
        value,
        abs: Math.abs(value),
      };
    })
    .sort((a, b) => b.abs - a.abs)
    .slice(0, 6);
}

function breakdownToBarRows(breakdown: BreakdownRow[] | undefined) {
  return (breakdown || [])
    .map((row, idx) => {
      const value = Number(row.contribution ?? row.shap_value ?? 0);
      return {
        id: `${row.label}-${idx}`,
        label: row.label || "Factor",
        value,
        abs: Math.abs(value),
        layer: row.layer,
        status: row.status,
      };
    })
    .filter((r) => r.abs > 0.001)
    .sort((a, b) => b.abs - a.abs);
}

const DRIVER_GREEN = "#34d399";
const DRIVER_RED = "#f87171";
const DRIVER_GREEN_TEXT = "#6ee7b7";
const DRIVER_RED_TEXT = "#fca5a5";

function DriverBarChart({
  rows,
}: {
  rows: Array<{ id: string; label: string; value: number; abs: number }>;
}) {
  const max = Math.max(...rows.map((r) => r.abs), 0.01);
  return (
    <div className="space-y-2.5 py-1">
      {rows.map((row, idx) => {
        const pct = Math.min(100, (row.abs / max) * 100);
        const barWidth = Math.max(pct, 14);
        const positive = row.value >= 0;
        const accent = positive ? DRIVER_GREEN : DRIVER_RED;
        const textColor = positive ? DRIVER_GREEN_TEXT : DRIVER_RED_TEXT;
        return (
          <div
            key={`${row.id}-${idx}`}
            className="rounded-lg pl-2.5 pr-1 py-2"
            style={{
              borderLeft: `4px solid ${accent}`,
              backgroundColor: positive ? "rgba(52, 211, 153, 0.12)" : "rgba(248, 113, 113, 0.12)",
            }}
          >
            <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)] items-center gap-2">
              <span className="truncate text-[11px] font-medium text-white/85" title={row.label}>
                {row.label}
              </span>
              <div className="flex items-center gap-2">
                <div
                  className="relative h-3 flex-1 overflow-hidden rounded-full"
                  style={{ backgroundColor: "rgba(255,255,255,0.08)" }}
                >
                  <div
                    className="absolute inset-y-0 left-0 rounded-full"
                    style={{ width: `${barWidth}%`, backgroundColor: accent }}
                  />
                </div>
                <span
                  className="w-[4.5rem] shrink-0 text-right text-[10px] font-mono font-bold"
                  style={{ color: textColor }}
                >
                  {row.value >= 0 ? "+" : ""}
                  {row.value.toFixed(2)} pts
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ExplainabilityPanel({
  xai,
  compact = false,
}: {
  xai?: XaiPayload | null;
  compact?: boolean;
}) {
  const barRows = useMemo(() => {
    const official = breakdownToBarRows(xai?.score_breakdown);
    if (official.length) return official;
    return toBarRows(xai?.shap?.features);
  }, [xai?.score_breakdown, xai?.shap?.features]);
  const drivers = useMemo(() => {
    const seen = new Set<string>();
    const out: string[] = [];
    for (const d of xai?.top_drivers || []) {
      const cleaned = cleanDriverText(d);
      if (!cleaned || seen.has(cleaned)) continue;
      seen.add(cleaned);
      out.push(cleaned);
    }
    return out;
  }, [xai?.top_drivers]);
  const semantic = xai?.semantic_evaluation || [];

  const helpContext = useMemo(
    () => ({
      baselineScore: xai?.baseline_score,
      observedScore: xai?.observed_score,
      semanticEvaluation: semantic,
    }),
    [xai?.baseline_score, xai?.observed_score, semantic]
  );

  const hasPanel =
    Boolean(xai) &&
    (barRows.length > 0 || drivers.length > 0 || semantic.length > 0 || (xai?.score_breakdown?.length ?? 0) > 0);
  if (!hasPanel) {
    return null;
  }

  const headerHelp = (
    <MetricInfoButton
      helpId="shap_drivers"
      label="How this score is calculated"
      hoverText="How this score is calculated"
      context={helpContext}
    />
  );

  const benchmark = indexVsBenchmark(xai?.observed_score, xai?.baseline_score);
  const ruleRisk = (xai?.observed_risk || "").toUpperCase();

  if (compact) {
    return (
      <div className="space-y-3 rounded-2xl border border-white/10 bg-[#2a2a2a] p-4">
        <div className="flex items-start justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex min-w-0 items-start gap-2">
            <BrainCircuit className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <div className="min-w-0">
              <div className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
                <span>Why this score</span>
                {headerHelp}
              </div>
              <div className="text-xs leading-relaxed text-white/55">
                Benchmark φ₀ ≈ {xai?.baseline_score ?? "—"} (global average) → this turn{" "}
                <strong className="text-white/80">{xai?.observed_score ?? "—"}</strong>
                {benchmark.delta != null && benchmark.delta > 0 && (
                  <span style={{ color: DRIVER_GREEN_TEXT }}> — above average</span>
                )}
                {benchmark.delta != null && benchmark.delta < 0 && (
                  <span style={{ color: DRIVER_RED_TEXT }}> — below average</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <div className="flex items-center gap-1">
              <span
                className={`border px-2.5 py-1 text-[11px] font-bold tracking-wide ${indexBadgeClass(benchmark.delta)}`}
              >
                {benchmark.label}
              </span>
              <MetricInfoButton helpId="compliance_score" context={helpContext} hoverText="Compliance index" />
            </div>
            {benchmark.detail && (
              <p className="max-w-[11rem] text-right text-[10px] text-white/45">{benchmark.detail}</p>
            )}
            {ruleRisk && ruleRisk !== "LOW" && (
              <span
                className={`border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${ruleExposureTone(ruleRisk)}`}
                title="Separate from the index number: severity of compliance rules that fired on this text"
              >
                Rules flagged · {ruleRisk}
              </span>
            )}
          </div>
        </div>

        {barRows.length > 0 && (
          <div className="rounded-lg border border-white/10 bg-black/25 p-3">
            <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-white/50">
                  SHAP · driver bars
                </span>
                <p className="mt-0.5 text-[10px] text-white/40">
                  Coloured bars = official compliance engine waterfall (rules + semantic penalties + RAG). Same
                  numbers the index uses — not the LLM narrative.
                </p>
              </div>
              <span className="text-[10px] font-medium">
                <span style={{ color: DRIVER_GREEN }}>Green</span>
                <span className="text-white/40"> raises · </span>
                <span style={{ color: DRIVER_RED }}>Red</span>
                <span className="text-white/40"> lowers</span>
              </span>
            </div>
            <DriverBarChart rows={barRows} />
          </div>
        )}

        {semantic.length > 0 && (
          <div className="rounded-lg border border-white/15 bg-white/[0.04] p-2.5">
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-white/55">
                Semantic ML · corpus classifier
              </span>
              <p className="mt-0.5 text-[10px] text-white/40">
                Neutral panel = ML control status per payment category. Penalties appear here and as{" "}
                <span className="text-white/55">red SHAP bars</span> only when status is PARTIAL or MISSING.
                Penalty points scale with model confidence (up to −4 / −10) — so a low-confidence miss costs
                far less than a certain one. COMPLIANT shows <span className="text-white/55">0 pts</span>.
              </p>
            </div>
            <ul className="mt-2 space-y-1.5">
              {semantic.map((row, idx) => {
                const pen = Number(row.penalty_points || 0);
                const status = (row.status || "").toUpperCase();
                const bad = status !== "COMPLIANT";
                const conf =
                  row.confidence != null && !Number.isNaN(Number(row.confidence))
                    ? `${Math.round(Number(row.confidence) * 100)}% conf.`
                    : "";
                return (
                  <li
                    key={`${row.category || "cat"}-${row.status}-${idx}`}
                    className={`flex justify-between gap-2 rounded-md border-l-[3px] px-2 py-1.5 text-[11px] ${
                      bad
                        ? "border-rose-400 bg-rose-500/[0.07] text-white/75"
                        : "border-white/25 bg-white/[0.03] text-white/72"
                    }`}
                  >
                    <span>{row.display_name || row.label}</span>
                    <span className="shrink-0 text-right font-mono text-[10px]">
                      {status}
                      {pen > 0 ? (
                        <span style={{ color: DRIVER_RED_TEXT }}> · −{pen.toFixed(1)} index pts</span>
                      ) : (
                        <span className="text-white/45"> · 0 index pts</span>
                      )}
                      {conf && <span className="text-white/40"> · {conf}</span>}
                      {row.model_source ? <span className="text-white/35"> · {row.model_source}</span> : null}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        <div className="space-y-1.5">
          {drivers.slice(0, 5).map((driver, idx) => {
            const up = driver.includes("raised") || driver.includes("supported") || driver.includes("+");
            return (
              <div
                key={`driver-${idx}-${driver.slice(0, 48)}`}
                className={`flex items-start gap-2 border-l-[3px] px-2.5 py-2 ${
                  up ? "border-emerald-400/90 bg-emerald-500/[0.05]" : "border-rose-400/90 bg-rose-500/[0.05]"
                }`}
              >
                {up ? (
                  <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-300" />
                ) : (
                  <ArrowDownRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-300" />
                )}
                <div className="text-xs leading-5 text-white/70">{driver}</div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5 border border-white/10 bg-[#0c1211] p-6 md:p-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <BrainCircuit className="h-5 w-5 text-accent" />
          <div>
            <div className="flex items-center gap-1 text-sm font-semibold text-white">
              <span>Explainable AI</span>
              {headerHelp}
            </div>
            <div className="text-xs text-white/45">
              φ₀≈{xai?.baseline_score ?? "—"} → factors → {xai?.observed_score ?? "—"}
              <MetricInfoButton helpId="baseline_phi" className="ml-1" context={helpContext} hoverText="What φ₀ means" />
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1">
            <span
              className={`border px-3 py-1 text-[11px] font-bold tracking-wide ${indexBadgeClass(benchmark.delta)}`}
            >
              {benchmark.label}
            </span>
            <MetricInfoButton helpId="compliance_score" context={helpContext} hoverText="Compliance index" />
          </div>
          {benchmark.detail && <p className="text-[10px] text-white/45">{benchmark.detail}</p>}
          {ruleRisk && ruleRisk !== "LOW" && (
            <span className={`border px-2 py-0.5 text-[9px] font-semibold uppercase ${ruleExposureTone(ruleRisk)}`}>
              Rules flagged · {ruleRisk}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-2">
        {drivers.slice(0, 6).map((driver, idx) => (
          <div
            key={`driver-full-${idx}-${driver.slice(0, 48)}`}
            className="border border-white/8 bg-white/[0.02] px-4 py-3 text-sm leading-6 text-white/70"
          >
            {driver}
          </div>
        ))}
      </div>

      <div className="border border-white/8 bg-[#0b1211] p-4">
        <DriverBarChart rows={barRows} />
      </div>
    </motion.section>
  );
}
