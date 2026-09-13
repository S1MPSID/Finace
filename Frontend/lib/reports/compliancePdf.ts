import { reportsApi } from "@/services/api";

/** Tracks blob URLs opened for in-browser PDF preview (revoked on download). */
const previewUrls = new Map<string, string>();

function writePdfLoadingTab(tab: Window, reportId: string) {
  tab.document.open();
  tab.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Compliance Report — ${reportId}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      font-family: system-ui, -apple-system, sans-serif;
      background: #0a0f0e;
      color: #e8f5ef;
    }
    .spinner {
      width: 40px; height: 40px;
      border: 3px solid rgba(52, 211, 153, 0.2);
      border-top-color: #34d399;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    p { font-size: 14px; opacity: 0.75; }
  </style>
</head>
<body>
  <div class="spinner"></div>
  <p>Generating compliance PDF for <strong>${reportId}</strong>…</p>
</body>
</html>`);
  tab.document.close();
}

function writePdfErrorTab(tab: Window, message: string) {
  tab.document.open();
  tab.document.write(`<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8" /><title>PDF Error</title>
<style>body{font-family:system-ui,sans-serif;background:#1a0a0a;color:#fecaca;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:2rem;text-align:center;}</style>
</head><body><p>${message}</p></body></html>`);
  tab.document.close();
}

/** Open PDF in a new browser tab (sync window open avoids pop-up blockers). */
export async function openCompliancePdfInNewTab(
  reportId: string,
  options?: { refresh?: boolean }
): Promise<void> {
  const tab = window.open("", "_blank");
  if (!tab) {
    throw new Error("Could not open a new tab. Allow pop-ups for this site.");
  }

  writePdfLoadingTab(tab, reportId);

  try {
    const blob = await reportsApi.fetchPdf(reportId, "inline", { refresh: options?.refresh ?? true });
    const existing = previewUrls.get(reportId);
    if (existing) URL.revokeObjectURL(existing);

    const url = URL.createObjectURL(blob);
    previewUrls.set(reportId, url);
    tab.location.href = url;
  } catch (err: any) {
    const message = err?.message || "Could not load PDF. Ensure Python RAG is running on port 8000.";
    writePdfErrorTab(tab, message);
    throw err;
  }
}

export async function downloadCompliancePdf(
  reportId: string,
  filename: string,
  options?: { refresh?: boolean }
): Promise<void> {
  const blob = await reportsApi.fetchPdf(reportId, "attachment", options);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);

  const preview = previewUrls.get(reportId);
  if (preview) {
    URL.revokeObjectURL(preview);
    previewUrls.delete(reportId);
  }
}

export function revokeCompliancePdfPreview(reportId: string) {
  const preview = previewUrls.get(reportId);
  if (preview) {
    URL.revokeObjectURL(preview);
    previewUrls.delete(reportId);
  }
}
