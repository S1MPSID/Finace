import { ACCENT_HEX } from "@/lib/theme/colors";
import {
  CONTROL_KEYS,
  RISK_COLORS,
  type OfficialAnalytics,
  type RequirementRow,
  type RuleCheckRow,
  type ScoreBreakdownRow,
  type SemanticItem,
  type TrajectoryPoint,
  type TrustAnalytics,
  type TrustChatMessage,
} from "./types";

export function trustBand(score: number) {
  if (score >= 80) return { label: "High compliance", tone: "text-emerald-300 border-emerald-400/30 bg-emerald-500/10" };
  if (score >= 60) return { label: "Moderate compliance", tone: "text-amber-300 border-amber-400/30 bg-amber-500/10" };
  return { label: "Building compliance", tone: "text-rose-300 border-rose-400/30 bg-rose-500/10" };
}

function _num(v: unknown, fallback = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function _buildWaterfallFromBreakdown(breakdown: ScoreBreakdownRow[]): ScoreBreakdownRow[] {
  return breakdown.map((row) => ({
    ...row,
    label: row.label || row.feature,
    contribution: _num(row.contribution, row.shap_value ?? 0),
  }));
}

function _buildRequirements(
  breakdown: ScoreBreakdownRow[],
  semanticItems: SemanticItem[]
): RequirementRow[] {
  const byReqId = new Map<string, RequirementRow>();

  for (const item of semanticItems) {
    const id = item.requirement_id || item.category || "";
    if (!id) continue;
    const existing = byReqId.get(id);
    if (existing) continue;
    byReqId.set(id, {
      id,
      requirement: item.display_name || item.label || id,
      status: (item.status || "UNKNOWN") as RequirementRow["status"],
      confidence: _num(item.confidence),
      penalty: _num(item.penalty_points),
      contribution: 0,
      modelSource: item.model_source || "heuristic",
    });
  }

  for (const row of breakdown) {
    if (!row.feature.startsWith("semantic:")) continue;
    const reqId = row.feature.replace("semantic:", "");
    const existing = byReqId.get(reqId);
    if (existing) {
      existing.contribution = _num(row.contribution, row.shap_value ?? 0);
    } else {
      byReqId.set(reqId, {
        id: reqId,
        requirement: row.label || reqId,
        status: (row.status || "UNKNOWN") as RequirementRow["status"],
        confidence: _num(row.confidence),
        penalty: Math.abs(_num(row.contribution, row.shap_value ?? 0)),
        contribution: _num(row.contribution, row.shap_value ?? 0),
        modelSource: row.model_source || "ml",
      });
    }
  }

  return Array.from(byReqId.values()).sort(
    (a, b) => a.contribution - b.contribution
  );
}

function _buildRuleChecks(breakdown: ScoreBreakdownRow[]): RuleCheckRow[] {
  return breakdown
    .filter((row) => row.feature.startsWith("rule:"))
    .map((row) => ({
      id: row.feature.replace("rule:", ""),
      label: row.label || row.feature,
      contribution: _num(row.contribution, row.shap_value ?? 0),
      riskLevel: row.risk_level || "MEDIUM",
    }))
    .sort((a, b) => a.contribution - b.contribution);
}

export function buildOfficialAnalytics(messages: TrustChatMessage[]): OfficialAnalytics {
  const aiTurns = messages.filter((m) => m.role === "ai" && m.data);

  const trajectory: TrajectoryPoint[] = aiTurns.map((m, i) => {
    const xai = m.data?.xai || {};
    const score = _num(m.data?.compliance_score ?? xai.observed_score);
    const baseline = _num(xai.baseline_score);
    return { turn: `T${i + 1}`, score, baseline };
  });

  const latest = aiTurns[aiTurns.length - 1];
  const latestXai = latest?.data?.xai || {};
  const breakdownRaw: ScoreBreakdownRow[] = latestXai.score_breakdown || [];
  const breakdown = _buildWaterfallFromBreakdown(breakdownRaw);
  const semanticItems: SemanticItem[] = latestXai.semantic_evaluation || [];
  const requirements = _buildRequirements(breakdown, semanticItems);
  const ruleChecks = _buildRuleChecks(breakdown);
  const ragEvidence = (latest?.sources || []).map((s: any) => ({
    documentId: s.document_id || "",
    section: s.section || "",
    text: s.text || "",
    relativePath: s.relative_path || "",
    sourceFile: s.source_file || "",
  }));
  const latestLimeFeatures = (latestXai.lime?.features || []).slice(0, 8);

  const officialScore = latest ? _num(latestXai.observed_score ?? latest.data?.compliance_score) : null;
  const baselineScore = latest ? _num(latestXai.baseline_score) : null;

  return {
    turns: aiTurns.length,
    officialScore,
    baselineScore,
    delta: officialScore != null && baselineScore != null ? Math.round((officialScore - baselineScore) * 10) / 10 : 0,
    trajectory,
    waterfall: breakdown,
    requirements,
    ruleChecks,
    semanticItems,
    ragEvidence,
    latestLimeFeatures,
  };
}

export function buildTrustAnalytics(messages: TrustChatMessage[]): TrustAnalytics {
  const aiTurns = messages.filter((m) => m.role === "ai" && m.data);

  const scoreSeries = aiTurns.map((m, i) => {
    const xai = m.data?.xai || {};
    const score = Number(m.data?.compliance_score ?? xai.observed_score ?? 0);
    const surrogate = Number(xai.surrogate_score ?? score);
    return {
      turn: `T${i + 1}`,
      score,
      surrogate,
      risk: (m.data?.risk_level || xai.observed_risk || "UNKNOWN").toUpperCase(),
      sources: m.sources?.length || 0,
      flags: m.data?.risk_flags?.length || 0,
      drivers: xai.top_drivers?.length || 0,
    };
  });

  const riskCounts: Record<string, number> = {};
  for (const row of scoreSeries) {
    riskCounts[row.risk] = (riskCounts[row.risk] || 0) + 1;
  }
  const riskPie = Object.entries(riskCounts).map(([name, value]) => ({
    name,
    value,
    fill: RISK_COLORS[name] || RISK_COLORS.UNKNOWN,
  }));

  const latest = aiTurns[aiTurns.length - 1];
  const latestXai = latest?.data?.xai || {};

  const shapBars = (latestXai.shap?.features || []).slice(0, 8).map((f: any) => {
    const label = f.label || f.feature || "feature";
    const value = Number(f.shap_value ?? 0);
    return {
      name: label.length > 18 ? `${label.slice(0, 16)}…` : label,
      full: label,
      value,
      fill: value >= 0 ? "#34d399" : "#fb7185",
    };
  }).reverse();

  const featureValues = latestXai.feature_values || {};
  const controlBars = CONTROL_KEYS.map((key) => ({
    name: key.replace(" present", "").replace(" controls", "").replace(" process", ""),
    full: key,
    value: Number(featureValues[key] ?? 0) >= 0.5 ? 1 : 0,
    fill: Number(featureValues[key] ?? 0) >= 0.5 ? ACCENT_HEX : "#475569",
  }));

  const retrievalBars = [
    { name: "Hit coverage", value: Number(featureValues["Number of matching regulations"] ?? 0) * 100 },
    { name: "Top match", value: Number(featureValues["Top regulation match strength"] ?? 0) * 100 },
    { name: "Avg match", value: Number(featureValues["Average regulation match strength"] ?? 0) * 100 },
    { name: "Detail", value: Number(featureValues["Workflow detail completeness"] ?? 0) * 100 },
  ];

  const avgSources = scoreSeries.length
    ? scoreSeries.reduce((s, r) => s + r.sources, 0) / scoreSeries.length
    : 0;
  const evidenceScore = Math.min(100, (avgSources / 5) * 100);

  const fidelityScore = scoreSeries.length
    ? scoreSeries
        .map((r) => Math.max(0, 100 - Math.abs(r.score - r.surrogate) * 2.5))
        .reduce((a, b) => a + b, 0) / scoreSeries.length
    : 50;

  const controlsOn = controlBars.filter((c) => c.value === 1).length;
  const controlScore = (controlsOn / Math.max(controlBars.length, 1)) * 100;

  const transparencyScore = latest
    ? Math.min(
        100,
        ((latestXai.top_drivers?.length || 0) / 5) * 40 +
          ((latestXai.shap?.features?.length || 0) / 8) * 40 +
          (latest.data?.reasoning_steps?.length ? 20 : 0)
      )
    : 40;

  let improvementScore = 55;
  if (scoreSeries.length >= 2) {
    const delta = scoreSeries[scoreSeries.length - 1].score - scoreSeries[0].score;
    improvementScore = Math.max(0, Math.min(100, 55 + delta));
  } else if (scoreSeries.length === 1) {
    improvementScore = Math.min(100, 40 + scoreSeries[0].score * 0.4);
  }

  const trustIndex = Math.round(
    evidenceScore * 0.22 +
      fidelityScore * 0.28 +
      controlScore * 0.18 +
      transparencyScore * 0.2 +
      improvementScore * 0.12
  );

  const factorRadar = [
    { name: "Evidence", score: Math.round(evidenceScore) },
    { name: "Fidelity", score: Math.round(fidelityScore) },
    { name: "Controls", score: Math.round(controlScore) },
    { name: "XAI", score: Math.round(transparencyScore) },
    { name: "Progress", score: Math.round(improvementScore) },
  ];

  const firstScore = scoreSeries[0]?.score ?? null;
  const lastScore = scoreSeries[scoreSeries.length - 1]?.score ?? null;
  const delta = firstScore != null && lastScore != null ? lastScore - firstScore : 0;

  return {
    scoreSeries,
    riskPie,
    shapBars,
    controlBars,
    retrievalBars,
    factorRadar,
    trustIndex,
    delta,
    turns: aiTurns.length,
    latestRisk: scoreSeries[scoreSeries.length - 1]?.risk || "—",
    latestScore: lastScore,
  };
}
