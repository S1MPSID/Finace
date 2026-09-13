const riskWeights = {
  LOW: 6,
  MEDIUM: 10,
  HIGH: 14,
};

export function evaluateResponse(payload) {
  const answerLength = payload.answer.trim().length;
  const citationCount = payload.citations.length;
  const recommendationCount = payload.recommendations.length;
  const riskFlagCount = payload.riskFlags.length;
  const reasoningCount = payload.reasoningSteps.length;

  const completenessScore =
    scorePresence(answerLength >= 80, 30) +
    scorePresence(recommendationCount >= 1, 20) +
    scorePresence(riskFlagCount >= 1, 15) +
    scorePresence(reasoningCount >= 1, 10);

  const evidenceScore =
    Math.min(citationCount, 4) * 10 +
    scorePresence(payload.citations.some((citation) => Boolean(citation.source)), 10);

  const consistencyScore =
    scorePresence(hasRiskAlignedNarrative(payload), 20) +
    scorePresence(recommendationCount >= minimumRecommendations(payload.riskLevel), 10) +
    scorePresence(riskFlagCount >= minimumRiskFlags(payload.riskLevel), 10);

  const totalScore = clamp(
    completenessScore + evidenceScore + consistencyScore,
    0,
    100
  );

  return {
    qualityScore: totalScore,
    grade: toGrade(totalScore),
    status: totalScore >= 75 ? "accepted" : totalScore >= 55 ? "review_required" : "weak",
    dimensions: {
      completeness: clamp(completenessScore, 0, 75),
      evidence: clamp(evidenceScore, 0, 50),
      consistency: clamp(consistencyScore, 0, 40),
    },
    summary: buildSummary({
      totalScore,
      citationCount,
      recommendationCount,
      riskFlagCount,
      reasoningCount,
      riskLevel: payload.riskLevel,
    }),
    improvementAreas: buildImprovementAreas(payload, {
      answerLength,
      citationCount,
      recommendationCount,
      riskFlagCount,
      reasoningCount,
    }),
    metadata: {
      callType: payload.callType,
      riskLevel: payload.riskLevel,
      evaluatedAt: new Date().toISOString(),
    },
  };
}

function hasRiskAlignedNarrative(payload) {
  const answer = payload.answer.toLowerCase();
  const weight = riskWeights[payload.riskLevel] ?? 0;
  if (payload.riskLevel === "HIGH") {
    return weight > 0 && /(high|urgent|critical|immediate|severe|material)/.test(answer);
  }
  if (payload.riskLevel === "MEDIUM") {
    return /(medium|moderate|attention|monitor|control)/.test(answer) || payload.riskFlags.length > 0;
  }
  return /(low|minor|limited|monitor)/.test(answer) || payload.recommendations.length > 0;
}

function minimumRecommendations(riskLevel) {
  if (riskLevel === "HIGH") return 2;
  if (riskLevel === "MEDIUM") return 1;
  return 1;
}

function minimumRiskFlags(riskLevel) {
  if (riskLevel === "HIGH") return 2;
  if (riskLevel === "MEDIUM") return 1;
  return 0;
}

function buildSummary({
  totalScore,
  citationCount,
  recommendationCount,
  riskFlagCount,
  reasoningCount,
  riskLevel,
}) {
  return `Evaluator scored this ${riskLevel.toLowerCase()}-risk response at ${totalScore}/100 based on answer completeness, supporting citations, and actionability. It includes ${citationCount} citation(s), ${recommendationCount} recommendation(s), ${riskFlagCount} risk flag(s), and ${reasoningCount} reasoning step(s).`;
}

function buildImprovementAreas(payload, stats) {
  const issues = [];

  if (stats.answerLength < 80) {
    issues.push("Expand the explanation so the response is not just a terse conclusion.");
  }
  if (stats.citationCount === 0) {
    issues.push("Add at least one source-backed citation to support the compliance conclusion.");
  }
  if (stats.recommendationCount < minimumRecommendations(payload.riskLevel)) {
    issues.push("Provide clearer remediation steps that match the stated risk level.");
  }
  if (stats.reasoningCount === 0) {
    issues.push("Include at least one reasoning step to make the answer easier to audit.");
  }
  if (payload.riskLevel === "HIGH" && stats.riskFlagCount < 2) {
    issues.push("High-risk findings should surface multiple explicit risk flags.");
  }

  return issues;
}

function toGrade(score) {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

function scorePresence(condition, points) {
  return condition ? points : 0;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
