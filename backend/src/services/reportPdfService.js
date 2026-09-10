import { postJson } from "./httpClient.js";
import { env } from "../config/env.js";

export async function generateReportPdf(report, orgName = "Finace Organization") {
  const doc = typeof report.toObject === "function" ? report.toObject() : report;
  const isUpgrade = Array.isArray(doc.evaluation_metadata?.update_history) &&
    doc.evaluation_metadata.update_history.length > 0;
  const analysisPayload = {
    ...doc,
    call_type: doc.call_type || (isUpgrade ? "update_report" : "new_report"),
    trust_stats: doc.trust_stats || report.trust_stats || {},
    conversation_snapshots: doc.conversation_snapshots || report.conversation_snapshots || [],
    evaluation_logs: doc.evaluation_logs || report.evaluation_logs || [],
    evaluator_references: doc.evaluator_references || report.evaluator_references || [],
  };

  return postJson(
    `${env.fastApiBaseUrl}/report`,
    { report_id: report.report_id, org_name: orgName, analysis: analysisPayload },
    { timeoutMs: 120000 }
  );
}

export async function signReportPdf(report, signer, orgName = "Finace Organization") {
  let pdfPath = report.pdf_path;

  if (!pdfPath) {
    const generated = await generateReportPdf(report, orgName);
    pdfPath = generated?.pdf_path;
  }

  if (!pdfPath) {
    throw new Error("PDF generation failed");
  }

  return postJson(
    `${env.fastApiBaseUrl}/report/sign`,
    {
      pdf_path: pdfPath,
      report_id: report.report_id,
      signer_name: signer.name,
      signer_role: signer.role,
      remarks: signer.remarks || "",
    },
    { timeoutMs: 120000 }
  );
}

export async function generateAndSignReport(report, signer, orgName = "Finace Organization") {
  const generated = await generateReportPdf(report, orgName);
  const pdfPath = generated?.pdf_path;
  if (!pdfPath) throw new Error("PDF generation failed");

  const signResult = await postJson(
    `${env.fastApiBaseUrl}/report/sign`,
    {
      pdf_path: pdfPath,
      report_id: report.report_id,
      signer_name: signer.name,
      signer_role: signer.role,
      remarks: signer.remarks || "",
    },
    { timeoutMs: 120000 }
  );

  return {
    pdfPath: signResult?.signed_pdf_path || pdfPath,
    signedPdfPath: signResult?.signed_pdf_path || pdfPath,
    documentHash: signResult?.document_hash || null,
    pdfSignature: signResult?.pdf_signature || {},
  };
}
