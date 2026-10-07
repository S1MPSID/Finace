"use client";

type FeatureRow = {
  feature?: string;
  importance?: number;
  share?: number;
};

const FRIENDLY: Record<string, string> = {
  scenario_len_norm: "Scenario length",
  has_shall_must: "Obligation language",
  has_negation: "Negation cues",
  has_kyc: "KYC mentions",
  has_aml: "AML mentions",
  has_grievance: "Grievance mentions",
  has_monitoring: "Monitoring mentions",
  has_audit: "Audit mentions",
  has_partial_language: "Partial-compliance language",
  has_out_of_scope: "Out-of-scope language",
  has_pilot_language: "Pilot language",
  has_multi_gap: "Multiple-gap cues",
  requirement_token_overlap: "Requirement word overlap",
  domain_mentioned: "Domain mentioned",
  exclamation_density: "Exclamation density",
};

export function FeatureImportanceBars({ features }: { features?: FeatureRow[] | null }) {
  if (!features?.length) {
    return (
      <p className="text-sm text-white/45">
        Feature importance is not available from the current model artifacts.
      </p>
    );
  }

  const top = features.slice(0, 8);
  const maxShare = Math.max(...top.map((f) => Number(f.share || 0)), 0.01);

  return (
    <div className="space-y-2.5">
      {top.map((f) => {
        const share = Number(f.share || 0);
        const width = `${Math.max(4, (share / maxShare) * 100)}%`;
        const label = FRIENDLY[f.feature || ""] || (f.feature || "feature").replace(/_/g, " ");
        return (
          <div key={f.feature}>
            <div className="mb-1 flex items-center justify-between gap-3 text-[12px]">
              <span className="text-white/70">{label}</span>
              <span className="tabular-nums text-white/40">{(share * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full rounded-full bg-accent/70" style={{ width }} />
            </div>
          </div>
        );
      })}
      <p className="pt-1 text-[11px] text-white/35">
        Shows which input signals most influence the ML validation model — not regulatory citations.
      </p>
    </div>
  );
}
