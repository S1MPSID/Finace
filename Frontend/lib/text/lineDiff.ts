import { htmlToPlainText } from "@/lib/text/htmlToPlain";

export type DiffLine =
  | { type: "remove"; line: string; oldNum: number }
  | { type: "add"; line: string; newNum: number };

const FIELD_LABELS: Record<string, string> = {
  compliance_score: "Compliance score",
  risk_level: "Risk level",
  explanation: "Determination summary",
  recommendations: "Required actions",
  risk_flags: "Risk flags",
};

export function fieldLabel(field: string): string {
  return FIELD_LABELS[field] || field.replace(/_/g, " ");
}

/** Normalize any stored field value to plain lines for diffing. */
export function fieldToLines(value: unknown): string[] {
  if (value == null) return [];
  if (typeof value === "number" || typeof value === "boolean") {
    return [String(value)];
  }
  if (Array.isArray(value)) {
    return value
      .flatMap((item) => htmlToPlainText(String(item)).split("\n"))
      .map((l) => l.trim())
      .filter(Boolean);
  }
  const plain = htmlToPlainText(String(value));
  if (!plain.includes("\n")) {
    const one = plain.trim();
    return one ? [one] : [];
  }
  return plain
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

/** Line-level diff — returns only added (+) and removed (-) lines. */
export function diffLines(oldLines: string[], newLines: string[]): DiffLine[] {
  const m = oldLines.length;
  const n = newLines.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
      else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  const raw: DiffLine[] = [];
  let i = m;
  let j = n;

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      raw.unshift({ type: "add", line: newLines[j - 1], newNum: j });
      j--;
    } else if (i > 0) {
      raw.unshift({ type: "remove", line: oldLines[i - 1], oldNum: i });
      i--;
    }
  }

  return raw;
}

export function diffFieldValues(oldVal: unknown, newVal: unknown): DiffLine[] {
  const oldLines = fieldToLines(oldVal);
  const newLines = fieldToLines(newVal);

  if (oldLines.length === 1 && newLines.length === 1 && oldLines[0] !== newLines[0]) {
    return [
      { type: "remove", line: oldLines[0], oldNum: 1 },
      { type: "add", line: newLines[0], newNum: 1 },
    ];
  }

  return diffLines(oldLines, newLines);
}
