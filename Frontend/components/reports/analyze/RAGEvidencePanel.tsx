"use client";

import { motion } from "framer-motion";
import { FileText } from "lucide-react";
import type { OfficialAnalytics } from "@/lib/trust/types";
import { MetricInfoButton } from "@/components/ui/MetricInfoButton";

export function RAGEvidencePanel({ stats }: { stats: OfficialAnalytics }) {
  if (stats.ragEvidence.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-5"
    >
      <div className="relative z-[1]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            RAG evidence
          </p>
          <MetricInfoButton helpId="analyze_rag_evidence" />
        </div>
        <p className="mt-1 text-sm text-white/55">
          Regulation chunks retrieved to support this turn&apos;s evaluation.
        </p>
        <ul className="mt-3 space-y-2">
          {stats.ragEvidence.map((ev, i) => (
            <li
              key={`${ev.documentId}-${i}`}
              className="rounded-lg bg-black/20 px-3 py-2.5"
            >
              <div className="flex items-center gap-2">
                <FileText className="h-3.5 w-3.5 shrink-0 text-accent/70" />
                <span className="text-[11px] font-medium text-white/80 truncate">
                  {ev.section || ev.documentId}
                </span>
                {ev.sourceFile && (
                  <span className="text-[9px] text-white/30 truncate">{ev.sourceFile}</span>
                )}
              </div>
              <p className="mt-1.5 text-[11px] leading-relaxed text-white/55 line-clamp-3">
                {ev.text?.slice(0, 300) || ""}
                {ev.text && ev.text.length > 300 ? "…" : ""}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
