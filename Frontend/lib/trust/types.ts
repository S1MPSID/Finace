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
