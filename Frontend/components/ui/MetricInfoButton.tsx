"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import { MetricHelpModal, type MetricHelpContext } from "@/components/ui/MetricHelpModal";
import type { MetricHelpId } from "@/lib/help/metricHelp";

const DEFAULT_HOVER = "View score explanation";

export function MetricInfoButton({
  helpId,
  className = "",
  label = "How this is calculated",
  hoverText = DEFAULT_HOVER,
  context,
}: {
  helpId: MetricHelpId;
  className?: string;
  label?: string;
  hoverText?: string;
  context?: MetricHelpContext;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <span className={`group relative inline-flex align-middle ${className}`}>
        <button
          type="button"
          aria-label={label}
          aria-haspopup="dialog"
          aria-expanded={open}
          title={hoverText}
          onClick={(e) => {
            e.stopPropagation();
            setOpen(true);
          }}
          className="inline-flex h-7 w-7 shrink-0 cursor-pointer items-center justify-center rounded-full border border-transparent text-white/45 transition hover:border-accent/40 hover:bg-accent/15 hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          <Info className="h-4 w-4" strokeWidth={2} />
        </button>
        <span
          role="tooltip"
          className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 hidden -translate-x-1/2 whitespace-nowrap rounded-md border border-white/15 bg-[#1a2220] px-2.5 py-1.5 text-[11px] font-medium text-white/90 shadow-lg group-hover:block group-focus-within:block"
        >
          {hoverText}
        </span>
      </span>
      <MetricHelpModal
        open={open}
        onClose={() => setOpen(false)}
        helpId={helpId}
        context={context}
      />
    </>
  );
}
