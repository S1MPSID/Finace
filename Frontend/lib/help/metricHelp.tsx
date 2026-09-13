import type { ReactNode } from "react";

export type MetricHelpId =
  | "compliance_score"
  | "baseline_phi"
  | "shap_drivers"
  | "analyze_compliance_score"
  | "analyze_baseline"
  | "analyze_trajectory"
  | "analyze_waterfall"
  | "analyze_requirements"
  | "analyze_rules"
  | "analyze_semantic_ml"
  | "analyze_rag_evidence"
  | "analyze_lime_what_if"
  | "analyze_trust_index"
  | "analyze_risk_pie"
  | "analyze_shap_chart"
  | "analyze_trust_factors"
  | "analyze_controls"
  | "analyze_retrieval";

type HelpBlock = { title: string; diagram: string; bullets: string[] };

export const METRIC_HELP: Record<MetricHelpId, HelpBlock> = {
  compliance_score: {
    title: "Compliance index (not “high = bad”)",
    diagram: `φ₀ ≈ 64–68  =  global benchmark (frozen per chat)
        + green factors (e.g. strong regulation match)
        − red factors (rules / ML gaps)
        ↓
   your index (e.g. 70) — compare to φ₀, not to zero`,
    bullets: [
      "70 is not a “high risk number.” It is your compliance index on a 0–100 scale.",
      "φ₀ is the blended average across seed workflows + recent chats — like a class average weight (kg), not a pass mark.",
      "If your index is 70 and φ₀ is ~67, you are slightly above the typical response; green bars show what helped.",
      "“Rules flagged · HIGH” is separate: it means specific rule checks fired, not that the digit 70 is bad.",
      "The LLM does not choose this index.",
    ],
  },
  baseline_phi: {
    title: "Reference average (φ₀)",
    diagram: `30 seed workflows → φ₀_seed
recent scored chats → φ₀_live
        ↓
φ₀ = 0.7×seed + 0.3×live (frozen per chat)`,
    bullets: [
      "Global φ₀ = 0.7 × seed workflows + 0.3 × recent scored chats (seed refreshes ~monthly).",
      "When a chat starts, seed/live/blended φ₀ are frozen for that whole conversation.",
      "Waterfall: frozen φ₀ plus/minus this turn’s factors = your score.",
    ],
  },
  shap_drivers: {
    title: "Why this score (SHAP + semantic ML)",
    diagram: `φ₀ (baseline) ──► rules ──► semantic ML ──► RAG bonus ──► index
     │                    │              │
     └─ green/red SHAP bars (only non-zero point changes)`,
    bullets: [
      "Green/red section = SHAP driver bars from the official compliance engine waterfall (rules, semantic penalties, RAG).",
      "White/neutral section = semantic ML status per category (COMPLIANT = 0 index pts; PARTIAL/MISSING add red bars).",
      "One green bar is normal when only regulation match moved the index; other checks scored 0 change.",
      "Bars are copied from score_breakdown (not LLM guesses). See SHAP_AND_SEMANTIC_TEST_PROMPTS.md for multi-bar examples.",
      "ML control rows show per-category status (COMPLIANT / PARTIAL / MISSING).",
      "Negative bars = penalties; positive = retrieval support.",
    ],
  },
  analyze_trust_index: {
    title: "Trust index (legacy, retired as headline)",
    diagram: `Evidence + Fidelity + Controls
      + XAI depth + Score progress
        ↓ weighted mix → 0–100`,
    bullets: [
      "Legacy formula from early prototype (no longer shown as headline).",
      "Fidelity is vacuous (score ≈ surrogate by construction).",
      "Official compliance score is the single headline now.",
    ],
  },
  analyze_trajectory: {
    title: "Score trajectory",
    diagram: `T1 T2 T3 … → official score per turn
      - - - φ₀ (frozen baseline)`,
    bullets: [
      "Solid line = official compliance score each turn.",
      "Dashed line = frozen baseline φ₀ for this chat.",
      "Compare turns to see improvement over time.",
      "Needs at least one AI reply with score data.",
    ],
  },
  analyze_risk_pie: {
    title: "Risk mix",
    diagram: `Count HIGH / MEDIUM / LOW labels per turn`,
    bullets: ["Pie slices = how often each risk band appeared in the session.", "From stored risk_level on each AI message."],
  },
  analyze_shap_chart: {
    title: "Latest SHAP drivers (Analyze)",
    diagram: `Last turn → copy of main chat SHAP bars`,
    bullets: ["Same meaning as chat drivers.", "Only the most recent AI turn."],
  },
  analyze_trust_factors: {
    title: "Trust factors bars (legacy)",
    diagram: `Evidence | Fidelity | Controls | XAI | Progress`,
    bullets: [
      "Legacy visualization — replaced by the waterfall in new design.",
      "Each bar 0–100 from buildAnalytics.ts rules.",
    ],
  },
  analyze_controls: {
    title: "Control coverage (legacy)",
    diagram: `KYC AML Grievance FEMA 2FA → 0 or 1`,
    bullets: ["Keyword flags from latest XAI feature vector.", "1 = pattern detected in workflow text."],
  },
  analyze_retrieval: {
    title: "Retrieval strength % (legacy)",
    diagram: `Hit count | Top match | Avg match | Detail`,
    bullets: ["Scales latest retrieval features to 0–100% for display.", "Shows how strongly regulations backed the last turn."],
  },
  analyze_compliance_score: {
    title: "Official compliance score",
    diagram: `82/100 — single headline
      = φ₀ + Σ rules + Σ semantic + RAG bonus
      clamped 0–100`,
    bullets: [
      "One official score per turn — the headline number.",
      "Derived from the hybrid engine (rules + RAG + semantic ML), not the LLM.",
      "Compare to φ₀ baseline to see how far above/below the reference average.",
    ],
  },
  analyze_baseline: {
    title: "Baseline prediction (φ₀)",
    diagram: `30 seed workflows → φ₀_seed
recent scored chats → φ₀_live
φ₀ = 0.7×seed + 0.3×live (frozen per chat)`,
    bullets: [
      "Global expected prediction over the reference population.",
      "Frozen at chat start so the baseline doesn't move between messages.",
      "Score moves relative to this baseline — the waterfall shows why.",
    ],
  },
  analyze_waterfall: {
    title: "Why this score? (waterfall)",
    diagram: `φ₀ (baseline)
  + KYC (+12)
  - Grievance (-10)
  + RAG (+4)
  = 82 (official score)`,
    bullets: [
      "Flat baseline bar (φ₀) → stacked factor contributions → final score.",
      "Green bars = positive contributions (strong RAG match, compliant ML status).",
      "Red bars = penalties (rule violations, missing ML status).",
      "This is the exact breakdown — not an approximation.",
    ],
  },
  analyze_requirements: {
    title: "Compliance requirements breakdown",
    diagram: `KYC     COMPLIANT  94%  +12
AML     PARTIAL    72%  -4
Griev.  MISSING    88%  -10
FEMA    COMPLIANT  91%   0
2FA     COMPLIANT  85%  +4`,
    bullets: [
      "Per-requirement: status (COMPLIANT/PARTIAL/MISSING), ML confidence %, and score contribution.",
      "ML confidence reflects the semantic classifier's certainty on that requirement.",
      "Contribution = how much that requirement moved the score (green = bonus, red = penalty).",
    ],
  },
  analyze_rules: {
    title: "Rule engine results",
    diagram: `✓ No explicit KYC violation     LOW
⚠ Grievance partially satisfied  MEDIUM
✗ No AML monitoring              HIGH`,
    bullets: [
      "Deterministic checks from the regex/rule engine — fires on explicit keywords.",
      "HIGH/MEDIUM/LOW reflects the rule's severity (penalty weight).",
      "Rules are one input to the score — they don't override the full evaluation.",
    ],
  },
  analyze_semantic_ml: {
    title: "Semantic ML evaluation",
    diagram: `[UPI] KYC → COMPLIANT  0.94 (ml)
[UPI] Grievance → MISSING  0.88 (ml)
[UPI] AML → PARTIAL  0.72 (ml+heuristic)`,
    bullets: [
      "Per-requirement status from the trained compliance classifier.",
      "Confidence % reflects model certainty (trained on labelled examples, not raw PDFs).",
      "Source: ml (pure classifier), heuristic (keyword fallback), or ml+heuristic (blend for low-confidence).",
      "Overall semantic confidence = mean of all per-requirement confidences.",
    ],
  },
  analyze_rag_evidence: {
    title: "RAG evidence",
    diagram: `Regulation chunk (source PDF)
  → text excerpt
  → similarity score`,
    bullets: [
      "Regulation chunks retrieved by the engine to support this turn's evaluation.",
      "Source PDF and section shown for audit trail.",
      "RAG provides knowledge (what regulations require), not whether you satisfy them.",
    ],
  },
  analyze_lime_what_if: {
    title: "LIME + What-if counterfactual",
    diagram: `LIME: local feature importance near this response
What-if: flip a factor → engine re-score (not LLM guess)`,
    bullets: [
      "LIME shows which factors matter locally around this specific response.",
      "What-if levers: flip a MISSING requirement to COMPLIANT, or disable a rule penalty.",
      "Score re-computation is deterministic (same waterfall arithmetic as the official score).",
      "Useful for demo: 'If we add grievance redressal, score goes from 55 → 62'.",
    ],
  },
};

export function ScoreCalculationDeepDive({
  baselineScore,
  observedScore,
  semanticEvaluation,
}: {
  baselineScore?: number | null;
  observedScore?: number | null;
  semanticEvaluation?: MetricHelpContextSemantic[];
}) {
  return (
    <div className="space-y-4 border-t border-white/10 pt-4">
      <div>
        <p className="text-[12px] font-semibold uppercase tracking-wider text-accent">What φ (phi) means</p>
        <p className="mt-2 text-[12px] leading-relaxed text-white/70">
          <strong className="text-white/90">φ₀</strong> is the <em>reference average</em> compliance index for a
          calibration population (30 seed workflows + recent scored chats, blended 70% / 30%). Use two everyday
          averages: mean <strong className="text-white/90">height</strong> in a group might be about{" "}
          <strong className="text-white/90">164–170&nbsp;cm</strong>; mean <strong className="text-white/90">weight</strong>{" "}
          might be about <strong className="text-white/90">64–68&nbsp;kg</strong>. φ₀ ≈ 64–68 on the compliance scale is
          like that weight average — a typical baseline, not a pass/fail line and not zero. Your workflow is scored as{" "}
          <strong className="text-white/90">φ₀ plus adjustments</strong> from rules, semantic checks, and regulation
          match strength. When this chat started, φ₀ was <strong>frozen</strong> so the baseline does not move between
          messages.
        </p>
      </div>
      <div>
        <p className="text-[12px] font-semibold uppercase tracking-wider text-white/45">Formula (this turn)</p>
        <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-black/50 p-3 text-[11px] leading-relaxed text-emerald-200/90 font-mono">
          {`score = clamp(
  φ₀_anchor
  − Σ rule penalties
  − Σ semantic penalties
  + retrieval bonus,
  0, 100
)`}
        </pre>
      </div>
      {(baselineScore != null || observedScore != null) && (
        <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3 text-[12px] text-white/75">
          {baselineScore != null && <p>φ₀ for this chat: <strong className="text-white">{baselineScore}</strong></p>}
          {observedScore != null && (
            <p className="mt-1">Observed score this turn: <strong className="text-white">{observedScore}</strong></p>
          )}
        </div>
      )}
      {semanticEvaluation && semanticEvaluation.length > 0 && (
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-wider text-white/45">ML control checks (this turn)</p>
          <ul className="mt-2 space-y-2">
            {semanticEvaluation.map((row) => (
              <li
                key={row.label || row.display_name}
                className="rounded-lg border border-white/8 bg-black/30 px-3 py-2 text-[11px] text-white/70"
              >
                <span className="font-medium text-white/90">{row.display_name || row.label}</span>
                {" · "}
                {row.status}
                {row.penalty_points ? ` · −${row.penalty_points} pts` : " · no penalty"}
                {row.confidence != null && ` · confidence ${(row.confidence * 100).toFixed(0)}%`}
                {row.model_source && ` · ${row.model_source}`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

type MetricHelpContextSemantic = {
  display_name?: string;
  label?: string;
  status?: string;
  penalty_points?: number;
  confidence?: number;
  model_source?: string;
};

export function MetricHelpBody({ id }: { id: MetricHelpId }) {
  const h = METRIC_HELP[id];
  return (
    <div className="space-y-3 text-left">
      <p className="text-[13px] font-medium text-white">{h.title}</p>
      <pre className="whitespace-pre-wrap rounded-lg bg-black/40 p-2.5 text-[10px] leading-relaxed text-emerald-200/90 font-mono">
        {h.diagram}
      </pre>
      <ul className="list-disc space-y-1 pl-4 text-[11px] leading-relaxed text-white/65">
        {h.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
    </div>
  );
}
