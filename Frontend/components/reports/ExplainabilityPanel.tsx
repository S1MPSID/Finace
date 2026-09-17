"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, BrainCircuit } from "lucide-react";

type XaiFeature = { feature?: string; label?: string; weight?: number; shap_value?: number; direction?: string; active?: boolean };
type XaiPayload = {
  observed_score?: number;
  observed_risk?: string;
  lime?: { features?: XaiFeature[] };
  shap?: { features?: XaiFeature[] };
};

type Factor = { id: string; label: string; influence: number; supports: boolean };

function assessment(score: number) {
  if (score >= 80) return { label: "Good", tone: "text-emerald-300 border-emerald-400/30 bg-emerald-500/10" };
  if (score >= 60) return { label: "Fair", tone: "text-amber-300 border-amber-400/30 bg-amber-500/10" };
  if (score >= 40) return { label: "Needs improvement", tone: "text-orange-300 border-orange-400/30 bg-orange-500/10" };
  return { label: "Poor", tone: "text-rose-300 border-rose-400/30 bg-rose-500/10" };
}

/**
 * SHAP values are score-unit contributions, not percentages.  We preserve them
 * in the payload and show users each factor's share of the total absolute
 * contribution for this response. This is a bounded, response-specific
 * "influence" percentage rather than a fabricated quality score.
 */
function toFactors(features: XaiFeature[] | undefined): Factor[] {
  const values = (features || []).slice(0, 6).map((feature) => ({ feature, value: Number(feature.shap_value ?? 0) }));
  const total = values.reduce((sum, item) => sum + Math.abs(item.value), 0);
  return values.map(({ feature, value }, index) => ({
    id: `${feature.feature || feature.label || "factor"}-${index}`,
    label: feature.label || feature.feature || "Assessment factor",
    influence: total > 0 ? Math.round((Math.abs(value) / total) * 100) : 0,
    supports: value >= 0,
  }));
}

function influenceLabel(value: number) {
  if (value >= 50) return "High influence";
  if (value >= 25) return "Meaningful influence";
  return "Limited influence";
}

function FactorList({ factors }: { factors: Factor[] }) {
  return <div className="space-y-2">{factors.map((factor) => {
    const tone = factor.supports ? "border-emerald-400/15 bg-emerald-500/[0.04]" : "border-rose-400/15 bg-rose-500/[0.04]";
    return <div key={factor.id} className={`border px-3 py-2.5 ${tone}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 gap-2"><span className={factor.supports ? "text-emerald-300" : "text-rose-300"}>{factor.supports ? <ArrowUpRight className="mt-0.5 h-4 w-4" /> : <ArrowDownRight className="mt-0.5 h-4 w-4" />}</span><div><p className="text-sm text-white/85">{factor.label}</p><p className="mt-0.5 text-xs text-white/50">{factor.supports ? "Supports the compliance assessment." : "Weakens the compliance assessment."}</p></div></div>
        <div className="shrink-0 text-right"><p className={factor.supports ? "text-sm font-semibold text-emerald-300" : "text-sm font-semibold text-rose-300"}>{factor.influence}%</p><p className="text-[10px] text-white/45">{influenceLabel(factor.influence)}</p></div>
      </div>
    </div>;
  })}</div>;
}

export function ExplainabilityPanel({ xai, compact = false }: { xai?: XaiPayload | null; compact?: boolean }) {
  if (!xai || !xai.shap?.features?.length) return null;
  const score = Math.max(0, Math.min(100, Math.round(Number(xai.observed_score ?? 0))));
  const result = assessment(score);
  const factors = toFactors(xai.shap.features);
  const body = <><div className="flex items-center justify-between gap-3 border-b border-white/10 pb-3"><div className="flex items-center gap-2"><BrainCircuit className="h-4 w-4 text-accent" /><div><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">Response evaluation</p><p className="text-xs text-white/55">How this submitted response performed</p></div></div><div className="text-right"><p className="text-2xl font-semibold text-white">{score}%</p><span className={`inline-flex border px-2 py-0.5 text-[10px] font-bold uppercase ${result.tone}`}>{result.label}</span></div></div><div><p className="mb-2 text-sm font-medium text-white">Why this result?</p><FactorList factors={factors} /><p className="mt-3 text-[11px] leading-5 text-white/40">Each percentage shows that factor’s relative influence on this response’s assessment. It is not a separate compliance score.</p></div></>;
  if (compact) return <div className="space-y-3 rounded-2xl border border-white/10 bg-[#2a2a2a] p-4">{body}</div>;
  return <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-5 border border-white/10 bg-[#0c1211] p-6 md:p-8">{body}</motion.section>;
}
