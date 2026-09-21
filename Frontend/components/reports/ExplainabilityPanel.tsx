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

export function ExplainabilityPanel({
  xai,
  compact = false,
}: {
  xai?: XaiPayload | null;
  compact?: boolean;
}) {
  // The old xai payload is a rule-engine surrogate. It is retained for API and
  // historical report compatibility, but it must not be presented as SHAP for
  // the ML model. The ML Risk Prediction panel is the user-facing explanation.
  if (
    !xai ||
    xai.method === "hybrid_surrogate_shap_lime" ||
    (!xai.shap?.features?.length && !xai.lime?.features?.length)
  ) {
    return null;
  }

  const shapRows = toChartRows(xai.shap?.features, "shap_value");
  const drivers = xai.top_drivers || [];

  if (compact) {
    return (
      <div className="border border-white/10 bg-[#2a2a2a] p-4 space-y-3 rounded-2xl">
        <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-accent" />
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">Why this score</p>
              <p className="text-xs text-white/55">Surrogate SHAP drivers of the rule-engine score</p>
            </div>
          </div>
          <span className={`border px-2 py-1 text-[10px] font-bold uppercase tracking-wider ${riskTone(xai.observed_risk)}`}>
            {xai.observed_risk || "--"} · {xai.observed_score ?? "--"}
          </span>
        </div>

        <div className="space-y-1.5">
          {drivers.slice(0, 4).map((driver) => {
            const up = driver.includes("raised") || driver.includes("supported") || driver.includes("+");
            return (
              <div key={driver} className="flex gap-2 items-start border border-white/5 px-2.5 py-2">
                {up ? (
                  <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-300" />
                ) : (
                  <ArrowDownRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-300" />
                )}
                <p className="text-xs leading-5 text-white/70">{driver}</p>
              </div>
            );
          })}
        </div>

        <div className="h-40 border border-white/5 bg-black/20 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={shapRows} layout="vertical" margin={{ left: 4, right: 12, top: 4, bottom: 4 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                width={108}
                tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: "rgba(74, 222, 128, 0.06)" }}
                content={<XaiTooltip />}
                wrapperStyle={{ outline: "none", zIndex: 50 }}
              />
              <Bar dataKey="value" radius={[0, 0, 0, 0]} barSize={12}>
                {shapRows.map((row) => (
                  <Cell key={row.name} fill={row.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <p className="text-[10px] leading-4 text-white/35">
          Attribution units follow the surrogate model output (log-odds), not calibrated probability.
          The ML risk prediction with probability-space SHAP is shown in the ML Risk Prediction panel. Calibration was evaluated separately; these outputs are not calibrated confidence.
        </p>
      </div>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="border border-white/10 bg-[#0c1211] p-6 md:p-8 space-y-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <BrainCircuit className="h-5 w-5 text-accent" />
          <div>
            <h3 className="text-sm font-semibold text-white">Explainable AI</h3>
            <p className="text-xs text-white/45">
              Surrogate SHAP/LIME drivers behind the hybrid rule-engine score (does not explain the ML risk model)
            </p>
          </div>
        </div>
        <span className={`border px-3 py-1 text-[11px] font-bold uppercase tracking-wider ${riskTone(xai.observed_risk)}`}>
          {xai.observed_risk || "--"} · {xai.observed_score ?? "--"}
        </span>
      </div>

      <div className="grid gap-2 md:grid-cols-2">
        {drivers.slice(0, 6).map((driver) => (
          <div key={driver} className="border border-white/8 bg-white/[0.02] px-4 py-3 text-sm leading-6 text-white/70">
            {driver}
          </div>
        ))}
      </div>

      <div className="h-72 border border-white/8 bg-[#0b1211] p-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={shapRows} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
            <XAxis type="number" stroke="rgba(255,255,255,0.2)" tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={130} tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 11 }} />
            <Tooltip
              cursor={{ fill: "rgba(74, 222, 128, 0.06)" }}
              content={<XaiTooltip />}
              wrapperStyle={{ outline: "none", zIndex: 50 }}
            />
            <Bar dataKey="value" radius={[0, 0, 0, 0]}>
              {shapRows.map((row) => (
                <Cell key={row.name} fill={row.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <details className="group">
        <summary className="flex cursor-pointer items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-white/40 hover:text-white/70">
          Technical notes &amp; units
        </summary>
        <div className="mt-2 space-y-1.5 border-l border-white/10 pl-3">
          {(xai.notes || []).map((note) => (
            <p key={note} className="text-[11px] leading-5 text-white/50">
              {note}
            </p>
          ))}
          <p className="text-[11px] leading-5 text-white/50">
            These attributions describe the hybrid rule-engine surrogate, not the ML risk model.
            The ML model's exact probability-SHAP is shown in the ML Risk Prediction panel.
          </p>
        </div>
      </details>
    </motion.section>
  );
}
