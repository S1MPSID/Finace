export function sourceLabel(source: any): string {  const rel = source?.relative_path || source?.source_file || "";
  if (rel) return String(rel).split(/[/\\]/).pop() || rel;
  return source?.document_id || source?.section || "Regulation";
}

export function formatSourcesBlock(sources: any[] | undefined): string {
  if (!sources?.length) return "(none)";
  return sources
    .map((s, i) => {
      const name = sourceLabel(s);
      const section = s.section ? ` | section=${s.section}` : "";
      const snippet = (s.text || s.snippet || "").toString().replace(/\s+/g, " ").slice(0, 220);
      return `${i + 1}. ${name}${section}${snippet ? `\n   Excerpt: ${snippet}` : ""}`;
    })
    .join("\n");
}

export function getBackendDocsBase(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1").replace(
    /\/api\/v1\/?$/,
    ""
  );
}
