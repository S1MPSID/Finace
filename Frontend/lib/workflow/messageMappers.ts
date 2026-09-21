import type { WorkflowMessage } from "./types";

export function toPersistableMessages(messages: WorkflowMessage[]) {
  return messages.map((m) => ({
    role: m.role,
    content: m.content,
    sources: m.sources || [],
    risk_level: m.data?.risk_level,
    risk_flags: m.data?.risk_flags || [],
    compliance_score: m.data?.compliance_score,
    reasoning_steps: m.data?.reasoning_steps || [],
    xai: m.data?.xai || {},
    ml_risk: m.data?.ml_risk || {},
    analysis: m.data?.analysis || {},
    evidence_scope: m.data?.evidence_scope || {},
    rule_assessments: m.data?.rule_assessments || [],
  }));
}

export function fromPersistedMessages(raw: any[]): WorkflowMessage[] {
  return (raw || []).map((m) => ({
    role: m.role === "user" ? "user" : "ai",
    content: m.content || "",
    sources: m.sources || [],
    data:
      m.role === "ai"
        ? {
            risk_flags: m.risk_flags || [],
            compliance_score: m.compliance_score,
            risk_level: m.risk_level,
            xai: m.xai || {},
            ml_risk: m.ml_risk || {},
            reasoning_steps: m.reasoning_steps || [],
            analysis: m.analysis || {},
            evidence_scope: m.evidence_scope || {},
            rule_assessments: m.rule_assessments || [],
          }
        : undefined,
  }));
}

export function mapRagResponseToMessage(data: any): WorkflowMessage {
  return {
    role: "ai",
    content:
      data.answer ||
      data.analysis?.explanation ||
      "I've analyzed your workflow. Does this match your intended logic?",
    sources: data.sources || data.analysis?.applicable_clauses || [],
    data: {
      ...(data.analysis || {}),
      risk_flags: data.riskFlags || data.analysis?.risk_flags || [],
      compliance_score: data.complianceScore ?? data.analysis?.compliance_score,
      risk_level: data.riskLevel || data.analysis?.risk_level,
      xai: data.xai || {},
      ml_risk: data.ml_risk || {},
      evidence_scope: data.evidence_scope || {},
      rule_assessments: data.rule_assessments || [],
      reasoning_steps: data.reasoningSteps || data.analysis?.reasoning_steps || [],
      analysis: data.analysis || {},
    },
  };
}
