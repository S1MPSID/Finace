"use client";

import { BrainCircuit } from "lucide-react";
import { buildOfficialAnalytics } from "@/lib/trust/buildAnalytics";
import type { TrustChatMessage } from "@/lib/trust/types";
import { ScoreHeadlineCard } from "./analyze/ScoreHeadlineCard";
import { ScoreTrajectoryChart } from "./analyze/ScoreTrajectoryChart";
import { WaterfallChart } from "./analyze/WaterfallChart";
import { RequirementsTable } from "./analyze/RequirementsTable";
import { RuleChecksPanel } from "./analyze/RuleChecksPanel";
import { SemanticMLPanel } from "./analyze/SemanticMLPanel";
import { RAGEvidencePanel } from "./analyze/RAGEvidencePanel";
import { LIMEWhatIfPanel } from "./analyze/LIMEWhatIfPanel";

export function AnalyzeTrustDashboard({ messages }: { messages: TrustChatMessage[] }) {
  const stats = buildOfficialAnalytics(messages);

  if (stats.turns === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 pt-16 text-center">
        <BrainCircuit className="mb-4 h-10 w-10 text-accent/70" />
        <h2 className="text-xl font-medium text-white">No analysis yet</h2>
        <p className="mt-2 max-w-md text-sm text-white/50">
          Run at least one Chat prompt first. Analyze turns that conversation into compliance charts for your faculty demo.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-3 pb-8 pt-16" style={{ scrollbarWidth: "thin" }}>
      <div className="mx-auto w-full max-w-5xl space-y-5">
        <ScoreHeadlineCard stats={stats} />
        <ScoreTrajectoryChart stats={stats} />
        <WaterfallChart stats={stats} />
        <RequirementsTable stats={stats} />
        <RuleChecksPanel stats={stats} />
        <SemanticMLPanel stats={stats} />
        <RAGEvidencePanel stats={stats} />
        <LIMEWhatIfPanel stats={stats} />
      </div>
    </div>
  );
}
