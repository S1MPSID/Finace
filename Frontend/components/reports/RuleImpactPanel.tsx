"use client";

type Assessment = {
  rule_id?: string;
  name?: string;
  risk_level?: string;
  triggered?: boolean;
  status?: string;
  impact_rank?: number;
  impact_value?: number;
  impact_units?: string;
  impact_basis?: string;
  evidence_status?: string;
  applicability?: string;
};

function tone(level?: string) {
  if (level === "HIGH") return "text-rose-300 border-rose-400/25 bg-rose-500/10";
  if (level === "MEDIUM") return "text-amber-300 border-amber-400/25 bg-amber-500/10";
  return "text-emerald-300 border-emerald-400/25 bg-emerald-500/10";
}

export function RuleImpactPanel({ assessments }: { assessments?: Assessment[] }) {
  const rows = (assessments || []).filter((row) => row.status !== "not_applicable");
  if (!rows.length) return null;
  const maxImpact = Math.max(...rows.map((row) => Math.abs(Number(row.impact_value || 0))), 0.0001);

  return (
    <section className="rounded-[1.4rem] border border-white/10 bg-[#0c1211] p-5">
      <div className="flex items-start justify-between gap-3 border-b border-white/10 pb-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Applicable rules</p>
          <p className="mt-1 text-xs leading-5 text-white/45">
            Ranked by positive SHAP contribution for this workflow. Values are model units, not percentages.
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wider text-white/35">Rule + ML impact</span>
      </div>
      <div className="mt-4 space-y-3">
        {rows.map((row) => {
          const impact = Number(row.impact_value || 0);
          return (
            <div key={row.rule_id || row.name} className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-white">{row.name || row.rule_id}</p>
                  <p className="mt-1 text-[11px] text-white/40">Rank #{row.impact_rank || "-"} · {row.rule_id}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded border px-2 py-1 text-[10px] font-semibold uppercase ${tone(row.risk_level)}`}>{row.risk_level}</span>
                  <span className={`rounded border px-2 py-1 text-[10px] font-semibold uppercase ${row.triggered ? "border-rose-400/25 bg-rose-500/10 text-rose-300" : "border-white/10 text-white/45"}`}>
                    {row.triggered ? "Triggered" : "Applicable · not triggered"}
                  </span>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                  <div className="h-full rounded-full bg-rose-400/80" style={{ width: `${Math.max(2, Math.min(100, (Math.abs(impact) / maxImpact) * 100))}%` }} />
                </div>
                <span className="w-24 text-right font-mono text-[10px] text-white/55">impact {impact >= 0 ? "+" : ""}{impact.toFixed(4)}</span>
              </div>
              <p className="mt-2 text-[11px] leading-5 text-white/45">{row.impact_basis}</p>
              <div className="mt-2 flex flex-wrap gap-1.5 text-[9px] uppercase tracking-wider">
                <span className="rounded border border-white/10 px-2 py-1 text-white/45">
                  Evidence: {row.evidence_status === "SUPPORTED_IN_RETRIEVED_CONTEXT" ? "Supported in context" : "Insufficient direct evidence"}
                </span>
                <span className="rounded border border-amber-300/20 px-2 py-1 text-amber-200/70">
                  Applicability: {row.applicability === "REQUIRES_ENTITY_SPECIFIC_VALIDATION" ? "Validate entity-specific" : "Not established"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
