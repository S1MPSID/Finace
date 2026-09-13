"use client";

import { useState } from "react";
import { Download, Eye, Loader2, RefreshCw } from "lucide-react";
import { downloadCompliancePdf, openCompliancePdfInNewTab } from "@/lib/reports/compliancePdf";

type Props = {
  reportId: string;
  isSigned?: boolean;
  size?: "sm" | "md";
  /** Shorter labels for dense table rows */
  compact?: boolean;
};

export function CompliancePdfActions({ reportId, isSigned, size = "md", compact = false }: Props) {
  const [viewing, setViewing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const pad = size === "sm" ? "px-3 py-1.5 text-xs" : "px-5 py-2 text-sm";
  const filename = isSigned ? `${reportId}.signed.pdf` : `${reportId}.pdf`;

  const handleView = async () => {
    setViewing(true);
    try {
      await openCompliancePdfInNewTab(reportId, { refresh: true });
    } catch (err: any) {
      if (!err?.message?.includes("Could not open a new tab")) {
        /* error already shown in the new tab */
      }
    } finally {
      setViewing(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await openCompliancePdfInNewTab(reportId, { refresh: true });
    } catch {
      /* error shown in tab */
    } finally {
      setRegenerating(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadCompliancePdf(reportId, filename, { refresh: false });
    } catch (err: any) {
      alert(err?.message || "Could not download PDF.");
    } finally {
      setDownloading(false);
    }
  };

  const busy = viewing || downloading || regenerating;
  const viewLabel = compact ? "View" : "View PDF";
  const downloadLabel = compact ? "Download" : isSigned ? "Download Signed PDF" : "Download PDF";

  return (
    <div className="inline-flex flex-nowrap items-center justify-end gap-2">
      <button
        type="button"
        onClick={handleView}
        disabled={busy}
        className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border border-white/15 bg-white/5 font-semibold text-white/80 transition hover:bg-white/10 hover:text-white disabled:opacity-50 whitespace-nowrap ${pad}`}
      >
        {viewing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Eye className="h-3.5 w-3.5" />}
        {viewLabel}
      </button>
      {!compact && (
        <button
          type="button"
          onClick={handleRegenerate}
          disabled={busy}
          title="Regenerate PDF from latest report data"
          className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border border-white/15 bg-white/5 font-semibold text-white/70 transition hover:bg-white/10 hover:text-white disabled:opacity-50 whitespace-nowrap ${pad}`}
        >
          {regenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
          Regenerate
        </button>
      )}
      <button
        type="button"
        onClick={handleDownload}
        disabled={busy}
        className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 font-bold text-accent transition hover:bg-accent/20 disabled:opacity-50 whitespace-nowrap ${pad}`}
      >
        {downloading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
        {downloadLabel}
      </button>
    </div>
  );
}
