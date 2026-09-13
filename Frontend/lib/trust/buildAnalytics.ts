import { ACCENT_HEX } from "@/lib/theme/colors";
import { CONTROL_KEYS, RISK_COLORS, type TrustAnalytics, type TrustChatMessage } from "./types";

export function trustBand(score: number) {
  if (score >= 80) return { label: "High trust", tone: "text-emerald-300 border-emerald-400/30 bg-emerald-500/10" };
  if (score >= 60) return { label: "Moderate trust", tone: "text-amber-300 border-amber-400/30 bg-amber-500/10" };
  return { label: "Building trust", tone: "text-rose-300 border-rose-400/30 bg-rose-500/10" };
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
    { name: "Hit count", value: Number(featureValues["Number of matching regulations"] ?? 0) * 100 },
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
