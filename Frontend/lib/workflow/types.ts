export interface WorkflowMessage {
  role: "user" | "ai";
  content: string;
  sources?: any[];
  data?: {
    risk_flags?: string[];
    compliance_score?: number;
    risk_level?: string;
    xai?: any;
    ml_risk?: any;
    ml_validation?: any;
    evidence_scope?: any;
    rule_assessments?: any[];
    reasoning_steps?: string[];
    analysis?: any;
  };
}

export type StudioMode = "chat" | "analyze";
