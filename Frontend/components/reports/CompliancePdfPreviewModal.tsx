"use client";

import { useEffect } from "react";
import { X } from "lucide-react";

type Props = {
  url: string | null;
  title: string;
  onClose: () => void;
};

export function CompliancePdfPreviewModal({ url, title, onClose }: Props) {
  useEffect(() => {
    if (!url) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [url, onClose]);

  if (!url) return null;

  return (
    <div className="fixed inset-0 z-[100] flex flex-col bg-black/85 backdrop-blur-sm">
      <div className="flex shrink-0 items-center justify-between gap-4 border-b border-white/10 bg-[#0d1413] px-4 py-3 sm:px-6">
        <h3 className="truncate text-sm font-semibold text-white sm:text-base">{title}</h3>
        <button
          type="button"
          onClick={onClose}
          className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/80 transition hover:bg-white/10 hover:text-white"
        >
          <X className="h-4 w-4" />
          Close
        </button>
      </div>
      <div className="min-h-0 flex-1 bg-[#1a1a1a] p-2 sm:p-4">
        <embed
          src={`${url}#toolbar=1&navpanes=0`}
          type="application/pdf"
          className="h-full w-full rounded-xl border border-white/10 bg-white"
        />
      </div>
    </div>
  );
}
