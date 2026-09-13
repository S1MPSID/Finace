"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { MetricHelpBody, ScoreCalculationDeepDive, METRIC_HELP, type MetricHelpId } from "@/lib/help/metricHelp";

export type MetricHelpContext = {
  baselineScore?: number | null;
  observedScore?: number | null;
  semanticEvaluation?: Array<{
    display_name?: string;
    label?: string;
    status?: string;
    penalty_points?: number;
    confidence?: number;
    model_source?: string;
  }>;
};

type Props = {
  open: boolean;
  onClose: () => void;
  helpId: MetricHelpId;
  context?: MetricHelpContext;
};

export function MetricHelpModal({ open, onClose, helpId, context }: Props) {
  const [portalReady, setPortalReady] = useState(false);

  useEffect(() => {
    setPortalReady(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open || !portalReady) return null;

  const title = METRIC_HELP[helpId]?.title ?? "How this is calculated";
  const showDeep =
    helpId === "shap_drivers" || helpId === "compliance_score" || helpId === "baseline_phi";

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="metric-help-title"
    >
      {/* Backdrop */}
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 bg-black/90"
        onClick={onClose}
      />

      {/* Centered panel */}
      <div
        className="relative z-10 flex max-h-[min(90vh,760px)] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-white/20 bg-[#121a18] shadow-[0_24px_80px_rgba(0,0,0,0.65)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-white/10 px-5 py-4">
          <p id="metric-help-title" className="text-base font-semibold text-white">
            {title}
          </p>
          <p className="mt-0.5 text-xs text-white/45">Score, φ₀ baseline, and driver bars</p>
        </div>

        <div className="scrollbar-hide flex-1 overflow-y-auto px-5 py-4 space-y-4 text-[13px]">
          <MetricHelpBody id={helpId} />
          {showDeep && (
            <ScoreCalculationDeepDive
              baselineScore={context?.baselineScore}
              observedScore={context?.observedScore}
              semanticEvaluation={context?.semanticEvaluation}
            />
          )}
        </div>

        <div className="border-t border-white/10 px-5 py-4">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-full bg-accent py-2.5 text-sm font-semibold text-ink transition hover:bg-accent/90"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
