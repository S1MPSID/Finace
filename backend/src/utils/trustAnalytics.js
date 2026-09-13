/**
 * Server-side trust analytics (mirrors Frontend AnalyzeTrustDashboard.buildAnalytics).
 */

const CONTROL_KEYS = [
  "KYC controls present",
  "AML controls present",
  "Grievance process present",
  "FEMA/FX controls present",
  "2FA / OTP controls present",
];

function normalizeMessage(m) {
  return {
    role: m.role,
    sources: m.sources || [],
    data: {
      compliance_score: m.compliance_score ?? m.data?.compliance_score,
      risk_level: m.risk_level ?? m.data?.risk_level,
      risk_flags: m.risk_flags ?? m.data?.risk_flags ?? [],
      xai: m.xai ?? m.data?.xai ?? {},
      reasoning_steps: m.reasoning_steps ?? m.data?.reasoning_steps ?? [],
    },
  };
}

export function buildTrustStats(messages = []) {
  const normalized = (messages || []).map(normalizeMessage);
  const aiTurns = normalized.filter((m) => m.role === "ai");

  const scoreSeries = aiTurns.map((m, i) => {
    const xai = m.data?.xai || {};
    const score = Number(m.data?.compliance_score ?? xai.observed_score ?? 0);
    const surrogate = Number(xai.surrogate_score ?? score);
    return {
      turn: `T${i + 1}`,
      score,
      surrogate,
      risk: String(m.data?.risk_level || xai.observed_risk || "UNKNOWN").toUpperCase(),
      sources: (m.sources || []).length,
      flags: (m.data?.risk_flags || []).length,
      drivers: (xai.top_drivers || []).length,
    };
  });

  const riskCounts = {};
  for (const row of scoreSeries) {
    riskCounts[row.risk] = (riskCounts[row.risk] || 0) + 1;
  }
  const riskPie = Object.entries(riskCounts).map(([name, value]) => ({ name, value }));

  const latest = aiTurns[aiTurns.length - 1];
  const latestXai = latest?.data?.xai || {};

  const shapBars = (latestXai.shap?.features || []).slice(0, 8).map((f) => {
    const label = f.label || f.feature || "feature";
    return {
      name: label.length > 22 ? `${label.slice(0, 20)}…` : label,
      full: label,
      value: Number(f.shap_value ?? 0),
    };
  });

  const featureValues = latestXai.feature_values || {};
  const controlBars = CONTROL_KEYS.map((key) => ({
    name: key.replace(" present", "").replace(" controls", "").replace(" process", ""),
    full: key,
    value: Number(featureValues[key] ?? 0) >= 0.5 ? 1 : 0,
  }));

  const retrievalBars = [
    { name: "Hit count", value: Number(featureValues["Number of matching regulations"] ?? 0) * 100 },
    { name: "Top match", value: Number(featureValues["Top regulation match strength"] ?? 0) * 100 },
    { name: "Avg match", value: Number(featureValues["Average regulation match strength"] ?? 0) * 100 },
    { name: "Detail", value: Number(featureValues["Workflow detail completeness"] ?? 0) * 100 },
  ];

  const avgSources =
    scoreSeries.length > 0
      ? scoreSeries.reduce((s, r) => s + r.sources, 0) / scoreSeries.length
      : 0;
  const evidenceScore = Math.min(100, (avgSources / 5) * 100);

  const fidelityScores = scoreSeries.map((r) => {
    const gap = Math.abs(r.score - r.surrogate);
    return Math.max(0, 100 - gap * 2.5);
  });
  const fidelityScore =
    fidelityScores.length > 0
      ? fidelityScores.reduce((a, b) => a + b, 0) / fidelityScores.length
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
    trust_index: trustIndex,
    factor_radar: factorRadar,
    score_series: scoreSeries,
    risk_pie: riskPie,
    shap_bars: shapBars,
    control_bars: controlBars,
    retrieval_bars: retrievalBars,
    top_drivers: latestXai.top_drivers || [],
    delta,
    turns: aiTurns.length,
    latest_score: lastScore,
    latest_risk: scoreSeries[scoreSeries.length - 1]?.risk || null,
    computed_at: new Date().toISOString(),
  };
}

export function buildConversationSnapshots(messages = []) {
  return (messages || []).map((m, idx) => ({
    index: idx + 1,
    role: m.role,
    content: (m.content || "").slice(0, 4000),
    compliance_score: m.compliance_score ?? m.data?.compliance_score ?? null,
    risk_level: m.risk_level ?? m.data?.risk_level ?? null,
    risk_flags: m.risk_flags ?? m.data?.risk_flags ?? [],
    sources_count: (m.sources || []).length,
    xai_summary: {
      observed_score: m.xai?.observed_score ?? m.data?.xai?.observed_score ?? null,
      observed_risk: m.xai?.observed_risk ?? m.data?.xai?.observed_risk ?? null,
      top_drivers: (m.xai?.top_drivers ?? m.data?.xai?.top_drivers ?? []).slice(0, 5),
    },
  }));
}
