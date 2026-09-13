export const RISK_COLORS: Record<string, string> = {
  HIGH: "#fb7185",
  MEDIUM: "#fbbf24",
  LOW: "#34d399",
  UNKNOWN: "#94a3b8",
};

export const CONTROL_KEYS = [
  "KYC controls present",
  "AML controls present",
  "Grievance process present",
  "FEMA/FX controls present",
  "2FA / OTP controls present",
];

export type TrustChatMessage = {
  role: "user" | "ai";
  content: string;
  sources?: any[];
  data?: {
    compliance_score?: number;
    risk_level?: string;
    risk_flags?: string[];
    xai?: any;
    reasoning_steps?: string[];
  };
};

export interface TrustAnalytics {
  scoreSeries: any[];
  riskPie: any[];
  shapBars: any[];
  controlBars: any[];
  retrievalBars: any[];
  factorRadar: any[];
  trustIndex: number;
  delta: number;
  turns: number;
  latestRisk: string;
  latestScore: number | null;
}

export interface ScoreBreakdownRow {
  feature: string;
  label?: string;
  contribution: number;
  shap_value?: number;
  active?: boolean;
  direction?: string;
  layer?: string;
  status?: string;
  confidence?: number;
  model_source?: string;
  category?: string;
  risk_level?: string;
}

export interface SemanticItem {
  requirement_id: string;
  category?: string;
  status: string;
  confidence: number;
  penalty_points: number;
  label?: string;
  display_name?: string;
  model_source?: string;
}

export interface RequirementRow {
  id: string;
  requirement: string;
  status: "COMPLIANT" | "PARTIAL" | "MISSING" | "UNKNOWN";
  confidence: number;
  penalty: number;
  contribution: number;
  modelSource: string;
}

export interface RuleCheckRow {
  id: string;
  label: string;
  contribution: number;
  riskLevel: string;
}

export interface TrajectoryPoint {
  turn: string;
  score: number;
  baseline: number;
}

export interface RAGEvidence {
  documentId: string;
  section: string;
  text: string;
  relativePath?: string;
  sourceFile?: string;
}

export interface OfficialAnalytics {
  turns: number;
  officialScore: number | null;
  baselineScore: number | null;
  delta: number;
  trajectory: TrajectoryPoint[];
  waterfall: ScoreBreakdownRow[];
  requirements: RequirementRow[];
  ruleChecks: RuleCheckRow[];
  semanticItems: SemanticItem[];
  ragEvidence: RAGEvidence[];
  latestLimeFeatures: any[];
}
