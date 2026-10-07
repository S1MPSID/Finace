"use client";

import Link from "next/link";
import type { Route } from "next";
import { BrainCircuit, ArrowUpRight } from "lucide-react";

const ML_VALIDATION_HREF = "/dashboard/ml-validation" as Route;

type MlValidationPayload = {
  available?: boolean;
  compliance_status?: string;
  risk_category?: string;
  status_probabilities?: Record<string, number>;
  notes?: string[];
};

function statusTone(status?: string) {
  const s = (status || "").toUpperCase();
  if (s === "NON_COMPLIANT") return "text-rose-300 border-rose-400/30 bg-rose-500/10";
  if (s === "PARTIAL") return "text-amber-300 border-amber-400/30 bg-amber-500/10";
  if (s === "COMPLIANT") return "text-emerald-300 border-emerald-400/30 bg-emerald-500/10";
  return "text-white/70 border-white/15 bg-white/5";
}

function confidenceOf(payload: MlValidationPayload): string | null {
  const status = payload.compliance_status;
  const probs = payload.status_probabilities || {};
  if (!status || probs[status] == null) return null;
  return `${(Number(probs[status]) * 100).toFixed(1)}%`;
}

export function MLValidationCard({
  mlValidation,
  compact = false,
}: {
  mlValidation?: MlValidationPayload | null;
  compact?: boolean;
}) {
  if (!mlValidation || mlValidation.available === false || !mlValidation.compliance_status) {
    return null;
  }

  const confidence = confidenceOf(mlValidation);

  return (
    <div className="rounded-2xl border border-sky-400/20 bg-sky-500/[0.06] p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-sky-400/25 bg-sky-500/10">
            <BrainCircuit className="h-4 w-4 text-sky-300" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-200/70">
              Independent ML Validation
            </p>
            <p className="text-[11px] text-white/40">Does not override Finace assessment</p>
          </div>
        </div>
        <Link
          href={ML_VALIDATION_HREF}
          className="inline-flex items-center gap-1 rounded-full border border-sky-400/25 bg-sky-500/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-sky-200 hover:bg-sky-500/20 transition"
        >
          View ML Analysis
          <ArrowUpRight className="h-3 w-3" />
        </Link>
      </div>

      <div className={`grid gap-2 ${compact ? "grid-cols-1 sm:grid-cols-3" : "grid-cols-1 sm:grid-cols-3"}`}>
        <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wider text-white/35">Compliance Prediction</p>
          <span
            className={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold ${statusTone(
              mlValidation.compliance_status
            )}`}
          >
            {(mlValidation.compliance_status || "—").replace(/_/g, " ")}
          </span>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wider text-white/35">Risk</p>
          <p className="mt-1 text-sm font-medium text-white/85">
            {mlValidation.risk_category || "—"}
          </p>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wider text-white/35">Confidence</p>
          <p className="mt-1 text-sm font-medium text-white/85">{confidence || "—"}</p>
        </div>
      </div>
    </div>
  );
}
