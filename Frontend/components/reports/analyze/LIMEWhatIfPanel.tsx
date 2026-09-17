import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, RotateCcw } from "lucide-react";
import type { OfficialAnalytics } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

interface FlipState {
  [key: string]: string | boolean | number;
}

function _recomputeScore(
  baseline: number,
  breakdown: OfficialAnalytics["waterfall"],
  flips: FlipState
): { score: number; change: number; changes: { label: string; from: number; to: number; delta: number }[] } {
  let current = 0;
  const edits: { label: string; from: number; to: number; delta: number }[] = [];
  let sum = 0;

  for (const row of breakdown) {
    const original = Number(row.contribution ?? 0);
    let newValue = original;

    if (row.feature.startsWith("semantic:") && flips[row.feature] === "COMPLIANT") {
      newValue = 0;
    } else if (row.feature.startsWith("rule:") && flips[row.feature] === false) {
      newValue = 0;
    } else if (row.feature === "retrieval_top_score" && typeof flips.retrieval_top === "number") {
      newValue = 4.0 * flips.retrieval_top;
    }

    current += original;
    sum += newValue;

    if (Math.abs(newValue - original) > 1e-9) {
      edits.push({
        label: row.label || row.feature,
        from: original,
        to: newValue,
        delta: newValue - original,
      });
    }
  }

  const currentScore = Math.max(0, Math.min(100, baseline + current));
  const outcome = Math.max(0, Math.min(100, baseline + sum));

  return {
    score: Math.round(outcome * 10) / 10,
    change: Math.round((outcome - currentScore) * 10) / 10,
    changes: edits,
  };
}

export function LIMEWhatIfPanel({ stats }: { stats: OfficialAnalytics }) {
  const [flips, setFlips] = useState<FlipState>({});

  const hasLime = stats.latestLimeFeatures.length > 0;
  const hasSemantic = stats.requirements.some((r) => r.status !== "COMPLIANT");
  const hasRule = stats.ruleChecks.length > 0;

  if (!hasLime && !hasSemantic && !hasRule) return null;

  const baseline = stats.baselineScore ?? 0;
  const { score: outcome, change, changes: changedFlips } = _recomputeScore(baseline, stats.waterfall, flips);
  const hasChanges = changedFlips.length > 0;

  const toggleSemantic = (feature: string) => {
    setFlips((prev) => {
      const next = { ...prev };
      if (next[feature] === "COMPLIANT") {
        delete next[feature];
      } else {
        next[feature] = "COMPLIANT";
      }
      return next;
    });
  };

  const toggleRule = (feature: string) => {
    setFlips((prev) => {
      const next = { ...prev };
      if (next[feature] === false) {
        delete next[feature];
      } else {
        next[feature] = false;
      }
      return next;
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            LIME &amp; What-if
          </p>
          <MetricInfoButton helpId="analyze_lime_what_if" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          Local feature importance + counterfactual re-score. Toggle levers to see the impact.
        </p>

        {hasLime && (
          <div className="mt-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-white/35">
              Local feature importance
            </p>
            <div className="mt-2 space-y-1.5">
              {stats.latestLimeFeatures.map((f: any, i: number) => {
                const weight = Number(f.shap_value ?? f.weight ?? 0);
                const label = f.label || f.feature || ("feature " + i);
                const abs = Math.min(Math.abs(weight), 10);
                const widthPct = (abs / 10) * 100;
                return (
                  <div key={label + "-" + i} className="flex items-center gap-2 text-[11px]">
                    <span className="w-[140px] shrink-0 truncate text-white/55">{label}</span>
                    <div className="flex-1 h-[6px] rounded-full bg-white/5 overflow-hidden">
                      <div
                        className={"h-full rounded-full " + (weight >= 0 ? "bg-emerald-500/60" : "bg-rose-500/60")}
                        style={{ width: widthPct + "%" }}
                      />
                    </div>
                    <span className={"w-[50px] text-right tabular-nums " + (weight >= 0 ? "text-emerald-400" : "text-rose-400")}>
                      {(weight >= 0 ? "+" : "") + weight.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-5 border-t border-white/10 pt-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-white/35">
            What-if levers
          </p>
          <p className="mt-1 text-[11px] text-white/45">
            Flip a factor and see the score re-compute instantly.
          </p>
          <div className="mt-3 space-y-1.5">
            {stats.requirements.filter((r) => r.status !== "COMPLIANT").map((req) => {
              const key = "semantic:" + req.id;
              const active = flips[key] === "COMPLIANT";
              return (
                <button
                  key={req.id}
                  onClick={() => toggleSemantic(key)}
                  className={
                    "flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-[11px] transition-colors " +
                    (active
                      ? "border-emerald-500/30 bg-emerald-500/10"
                      : "border-white/5 bg-black/20 hover:bg-black/30")
                  }
                >
                  <span className="text-white/70">
                    Flip <span className="font-medium text-white/90">{req.requirement}</span>{" "}to COMPLIANT
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 text-white/30" />
                </button>
              );
            })}
            {stats.ruleChecks.filter((r) => r.contribution < 0).map((rule) => {
              const key = "rule:" + rule.id;
              const active = flips[key] === false;
              return (
                <button
                  key={rule.id}
                  onClick={() => toggleRule(key)}
                  className={
                    "flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-[11px] transition-colors " +
                    (active
                      ? "border-emerald-500/30 bg-emerald-500/10"
                      : "border-white/5 bg-black/20 hover:bg-black/30")
                  }
                >
                  <span className="text-white/70">
                    Disable rule <span className="font-medium text-white/90">{rule.label}</span>
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 text-white/30" />
                </button>
              );
            })}
          </div>
          {hasChanges && (
            <div className="mt-3 rounded-lg border border-accent/20 bg-accent/5 p-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-white/50">If you made these changes:</span>
                <button
                  onClick={() => setFlips({})}
                  className="flex items-center gap-1 text-[10px] text-white/40 hover:text-white/60"
                >
                  <RotateCcw className="h-3 w-3" />
                  Reset
                </button>
              </div>
              <div className="mt-1.5 flex items-baseline gap-2">
                <span className="text-2xl font-semibold text-white tabular-nums">{outcome}</span>
                <span className={"text-sm font-medium " + (change >= 0 ? "text-emerald-400" : "text-rose-400")}>
                  {(change >= 0 ? "+" : "") + change}
                </span>
              </div>
              <ul className="mt-2 space-y-0.5">
                {changedFlips.map((f, i) => (
                  <li key={i} className="text-[10px] text-white/50">
                    {f.label}: {f.from}{" "}to{" "}
                    <span className={f.delta >= 0 ? "text-emerald-400" : "text-rose-400"}>{f.to}</span>
                    {" "}({(f.delta >= 0 ? "+" : "") + f.delta.toFixed(2)})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}