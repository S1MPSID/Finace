/**
 * Public links for RBI source PDFs.
 *
 * Local dev: serves from backend `/docs/...`
 * Production: set NEXT_PUBLIC_RBI_DOCS_DRIVE_URL to your shared Drive folder, e.g.
 * https://drive.google.com/drive/folders/1VTUcHvGI8zYMh4YoliWcTVSuJ0d2Qych
 *
 * Note: keep python-rag `RBI_DOCS_DIR` as a local folder path for ingestion only.
 */

export function extractGoogleDriveFolderId(url: string): string | null {
  const match = url.match(/\/folders\/([a-zA-Z0-9_-]+)/);
  return match?.[1] ?? null;
}

function getBackendDocsBase(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:5000/api/v1").replace(
    /\/api\/v1\/?$/,
    ""
  );
}

/** Build a clickable URL for a regulation PDF (Drive search or backend static file). */
export function resolvePublicDocUrl(relativePath: string): string | null {
  const normalized = String(relativePath || "").trim().replace(/\\/g, "/");
  if (!normalized) return null;

  const fileName = normalized.split("/").pop() || normalized;
  const driveRoot = process.env.NEXT_PUBLIC_RBI_DOCS_DRIVE_URL?.trim();

  if (driveRoot) {
    const folderId = extractGoogleDriveFolderId(driveRoot);
    if (folderId) {
      // Search inside the shared RBI DOCS folder by PDF filename.
      const query = `parent:${folderId} ${fileName}`;
      return `https://drive.google.com/drive/search?q=${encodeURIComponent(query)}`;
    }
  }

  return `${getBackendDocsBase()}/docs/${encodeURI(normalized)}`;
}

export function isPdfSourcePath(value: string): boolean {
  const v = value.trim();
  if (!v) return false;
  return v.endsWith(".pdf") || v.includes("/") || v.includes("\\");
}
