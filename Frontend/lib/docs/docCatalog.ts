import { resolvePublicDocUrl } from "@/lib/docs/publicDocUrl";

export type DocEntry = {
  label: string;
  path: string;
  category: string;
};

export function flattenDocsTree(tree: { category: string; files: { name: string; path: string }[] }[]): DocEntry[] {
  return (tree || []).flatMap((cat) =>
    (cat.files || []).map((file) => ({
      label: file.name.replace(/\.pdf$/i, ""),
      path: file.path,
      category: cat.category,
    }))
  );
}

function norm(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

/** Resolve a human document name to a catalog path. */
export function resolveDocPath(name: string, catalog: DocEntry[]): string | null {
  const raw = String(name || "").trim();
  if (!raw) return null;

  const exact = catalog.find(
    (d) => d.path === raw || d.path.toLowerCase() === raw.toLowerCase() || d.label.toLowerCase() === raw.toLowerCase()
  );
  if (exact) return exact.path;

  const n = norm(raw);
  const fuzzy = catalog.find((d) => norm(d.label).includes(n) || norm(d.path).includes(n) || n.includes(norm(d.label)));
  return fuzzy?.path || null;
}

export function openDocPdf(pathOrName: string, catalog: DocEntry[] = []): void {
  const path = pathOrName.includes("/") || pathOrName.endsWith(".pdf")
    ? pathOrName
    : resolveDocPath(pathOrName, catalog) || pathOrName;
  const url = resolvePublicDocUrl(path);
  if (url) window.open(url, "_blank", "noopener,noreferrer");
}
