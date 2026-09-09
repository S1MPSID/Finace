import fs from "node:fs";
import path from "node:path";
import { pythonRagDir, repoRoot } from "../config/paths.js";

export function listReportPdfCandidates(report) {
  return [
    report.signed_pdf_path,
    report.pdf_path,
    path.join(repoRoot, "data", "reports", `${report.report_id}.signed.pdf`),
    path.join(repoRoot, "data", "reports", `${report.report_id}.pdf`),
    path.join(pythonRagDir, "data", "reports", `${report.report_id}.signed.pdf`),
    path.join(pythonRagDir, "data", "reports", `${report.report_id}.pdf`),
  ].filter(Boolean);
}

export function clearReportPdfFiles(report) {
  for (const candidate of listReportPdfCandidates(report)) {
    try {
      if (fs.existsSync(candidate)) fs.unlinkSync(candidate);
    } catch {
      /* ignore */
    }
  }
}

export function resolveReportPdfPath(report) {
  for (const candidate of listReportPdfCandidates(report)) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}
