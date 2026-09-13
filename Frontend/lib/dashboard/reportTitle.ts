/** Pick a human-readable title from a report's workflow text. */
export function reportDisplayTitle(report: {
  report_id?: string;
  workflow_input?: { text?: string };
  workflow_text?: string;
}): string {
  const raw = report?.workflow_input?.text || report?.workflow_text || "";
  if (!raw.trim()) return report?.report_id ? `Report ${report.report_id}` : "Untitled workflow";

  const current = raw.match(/### CURRENT USER MESSAGE\s*\n+([\s\S]+?)(?:\n\n###|\s*$)/i);
  if (current?.[1]?.trim()) return clipTitle(stripHtml(current[1].trim()));

  const lines = raw
    .split("\n")
    .map((l) => l.trim())
    .filter(
      (l) =>
        l &&
        !l.startsWith("You are continuing") &&
        !l.startsWith("=====") &&
        !l.startsWith("###") &&
        !l.startsWith("Do not ignore") &&
        !l.startsWith("When the user asks")
    );

  if (lines[0]) return clipTitle(stripHtml(lines[0]));
  return report?.report_id ? `Report ${report.report_id}` : "Compliance workflow";
}

function stripHtml(text: string): string {
  return text.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function clipTitle(text: string, max = 72): string {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > max ? `${clean.slice(0, max - 1)}…` : clean;
}

export function riskTone(level?: string) {
  const r = (level || "").toUpperCase();
  if (r === "HIGH") return "bg-rose-500/12 text-rose-300 ring-rose-400/20";
  if (r === "MEDIUM") return "bg-amber-500/12 text-amber-300 ring-amber-400/20";
  return "bg-emerald-500/12 text-emerald-300 ring-emerald-400/20";
}

export function statusTone(status?: string) {
  const s = (status || "").toLowerCase();
  if (s === "verified") return "bg-emerald-500/12 text-emerald-300 ring-emerald-400/20";
  if (s === "rejected") return "bg-rose-500/12 text-rose-300 ring-rose-400/20";
  return "bg-amber-500/12 text-amber-300 ring-amber-400/20";
}
