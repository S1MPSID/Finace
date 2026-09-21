import crypto from "crypto";
import path from "node:path";
import { Report } from "../models/Report.js";
import { ChatSession } from "../models/ChatSession.js";
import { env } from "../config/env.js";
import { postJson } from "../services/httpClient.js";
import { getBlockchainDeployment } from "../services/blockchainService.js";
import { generateAndSignReport, generateReportPdf } from "../services/reportPdfService.js";
import { loadChatContext } from "../utils/chatContext.js";
import { resolveCalibrationFrozenForChat } from "../services/calibrationService.js";
import { clearReportPdfFiles, resolveReportPdfPath } from "../utils/reportPdfPaths.js";
import { buildEvaluationLogEntry } from "../utils/evaluationLog.js";

export async function generateReport(req, res) {
  const { workflow_text, regulator, chat_id } = req.body;
  const user_id = req.user?.user_id || req.body.user_id || "system";

  if (!workflow_text) {
    return res.status(400).json({ ok: false, error: "workflow_text is required" });
  }

  const chatContext = await loadChatContext(chat_id, user_id);
  const calibrationFrozen =
    chatContext.calibration_frozen ||
    (await resolveCalibrationFrozenForChat(chat_id, user_id));
  const result = await postJson(
    `${env.fastApiBaseUrl}/analyze`,
    {
      call_type: "new_report",
      workflow_text,
      regulator: regulator || "RBI",
      top_k: 5,
      active_categories: chatContext.selected_categories || [],
      enable_xai: true,
      chat_id: chat_id || undefined,
      calibration_frozen: calibrationFrozen || undefined,
    },
    { timeoutMs: env.fastApiTimeoutMs }
  );

  const analysis = result?.analysis || {};
  const report_id = `rep-${crypto.randomBytes(4).toString("hex")}`;
  const compliance_score =
    typeof analysis.compliance_score === "number" ? analysis.compliance_score : 55;

  const report = await Report.create({
    report_id,
    user_id,
    chat_id: chat_id || undefined,
    workflow_input: { text: workflow_text, regulator },
    risk_level: analysis.risk_level || "MEDIUM",
    risk_flags: analysis.risk_flags || [],
    applicable_clauses: Array.isArray(analysis.applicable_clauses) ? analysis.applicable_clauses : [],
    explanation: analysis.explanation || "Automated analysis completed.",
    recommendations: analysis.recommendations || [],
    compliance_score,
    reasoning_steps: analysis.reasoning_steps || [],
    xai: result?.xai || {},
    ml_risk: result?.ml_risk || {},
    evidence_scope: result?.evidence_scope || {},
    rule_assessments: result?.rule_assessments || [],
    trust_stats: chatContext.trust_stats,
    conversation_snapshots: chatContext.conversation_snapshots,
    status: "pending",
    proof_status: "none",
  });

  if (chat_id) {
    await ChatSession.updateOne({ session_id: chat_id, user_id }, { $set: { report_id } });
  }

  res.json({ ok: true, report_id: report.report_id, report });
}

export async function updateReport(req, res) {
  const { report_id, workflow_text, regulator } = req.body;
  if (!report_id) return res.status(400).json({ ok: false, error: "report_id is required" });

  const existing = await Report.findOne({ report_id });
  if (!existing) return res.status(404).json({ ok: false, error: "Report not found" });

  const existingReportText = [
    `Risk Level: ${existing.risk_level}`,
    `Explanation: ${existing.explanation || ""}`,
    `Recommendations: ${(existing.recommendations || []).join("; ")}`,
    `Compliance Score: ${existing.compliance_score}`,
  ].join("\n");

  const timestamp = new Date().toISOString();
  const simulatedRemediation = `[AI-IMPROVED WORKFLOW - ${timestamp}]: Mandatory e-KYC, 2FA, AES-256 encryption, AML monitoring, FEMA reporting, and grievance redressal are now in place.`;
  const queryWorkflow = workflow_text || simulatedRemediation;

  const result = await postJson(
    `${env.fastApiBaseUrl}/analyze`,
    {
      call_type: "update_report",
      workflow_text: queryWorkflow,
      existing_report_text: existingReportText,
      top_k: 5,
    },
    { timeoutMs: env.fastApiTimeoutMs }
  );

  const analysis = result?.analysis || {};
  const aiLog = buildEvaluationLogEntry({
    action: "ai_refresh",
    actor: { name: "Finace AI Engine", role: "system", id: "system" },
    comment: "AI re-assessment (compliance upgrade cycle)",
    changes: [
      {
        field: "compliance_score",
        old_value: existing.compliance_score,
        new_value:
          typeof analysis.compliance_score === "number"
            ? analysis.compliance_score
            : existing.compliance_score,
      },
      { field: "risk_level", old_value: existing.risk_level, new_value: analysis.risk_level || existing.risk_level },
    ],
  });

  const updated = await Report.findOneAndUpdate(
    { report_id },
    {
      workflow_input: {
        text: queryWorkflow,
        regulator: regulator || existing.workflow_input?.regulator || "RBI",
      },
      risk_level: analysis.risk_level || existing.risk_level,
      risk_flags: analysis.risk_flags || existing.risk_flags,
      applicable_clauses: analysis.applicable_clauses || existing.applicable_clauses,
      explanation: analysis.explanation || existing.explanation,
      recommendations: analysis.recommendations || existing.recommendations,
      compliance_score:
        typeof analysis.compliance_score === "number"
          ? analysis.compliance_score
          : existing.compliance_score,
      reasoning_steps: analysis.reasoning_steps || existing.reasoning_steps,
      xai: result?.xai || existing.xai || {},
      ml_risk: result?.ml_risk || existing.ml_risk || {},
      evidence_scope: result?.evidence_scope || existing.evidence_scope || {},
      rule_assessments: result?.rule_assessments || existing.rule_assessments || [],
      status: "pending",
      proof_status: "none",
      signed_pdf_path: undefined,
      document_hash: undefined,
      is_digitally_signed: false,
      pdf_signature: {},
      $push: {
        evaluation_logs: aiLog,
        "evaluation_metadata.update_history": {
          updated_at: new Date(),
          superseded_references: analysis.superseded_references || [],
          change_notes: analysis.superseded_change_notes || [],
        },
      },
    },
    { new: true }
  );

  res.json({ ok: true, report_id, report: updated, raw_analysis: analysis });
}

async function signPdfForReport(report, orgName, signer) {
  return generateAndSignReport(report, signer, orgName);
}

export async function signReport(req, res) {
  const report = await Report.findOne({ report_id: req.params.id });
  if (!report) return res.status(404).json({ ok: false, error: "Report not found" });
  if (report.status !== "verified") {
    return res.status(400).json({ ok: false, error: "Report must be verified before signing" });
  }

  const orgName = req.body.org_name || "Finace Organization";
  const signer = {
    name: report.evaluation_metadata?.evaluator_name || req.user?.name || "Authorized Evaluator",
    role: req.user?.role === "evaluator" ? "Compliance Evaluator" : "Compliance Reviewer",
    remarks: report.evaluator_remarks || "",
  };

  const signed = await signPdfForReport(report, orgName, signer);
  const updated = await Report.findOneAndUpdate(
    { report_id: report.report_id },
    {
      pdf_path: signed.pdfPath,
      signed_pdf_path: signed.signedPdfPath || signed.pdfPath,
      document_hash: signed.documentHash,
      pdf_signature: signed.pdfSignature,
      is_digitally_signed: true,
      proof_status: "signed",
    },
    { new: true }
  );

  res.json({
    ok: true,
    report: updated,
    pdf_path: signed.signedPdfPath || signed.pdfPath,
    document_hash: signed.documentHash,
  });
}

async function ensureReportPdfFile(report, { forceRefresh = false } = {}) {
  let filePath = forceRefresh ? null : resolveReportPdfPath(report);

  if (!filePath || forceRefresh) {
    if (forceRefresh) {
      clearReportPdfFiles(report);
      await Report.updateOne(
        { report_id: report.report_id },
        {
          $unset: { pdf_path: 1, signed_pdf_path: 1 },
          $set: {
            is_digitally_signed: false,
            proof_status: report.proof_status === "anchored" ? "anchored" : "none",
          },
        }
      );
    }

    const orgName =
      report.workflow_input?.org_name ||
      report.evaluation_metadata?.org_name ||
      "Finace Organization";
    const generated = await generateReportPdf(report, orgName);
    const pdfPath = generated?.pdf_path;
    if (pdfPath) {
      await Report.updateOne(
        { report_id: report.report_id },
        {
          pdf_path: pdfPath,
          proof_status: report.proof_status === "none" ? "pdf_ready" : report.proof_status,
        }
      );
      filePath = pdfPath;
    }
  }

  return filePath;
}

export async function downloadReportPdf(req, res) {
  const filter = { report_id: req.params.id };
  if (req.user?.role === "user") filter.user_id = req.user.user_id;

  const report = await Report.findOne(filter);
  if (!report) return res.status(404).json({ ok: false, error: "Report not found" });

  const forceRefresh =
    String(req.query.refresh || "").toLowerCase() === "1" ||
    String(req.query.regenerate || "").toLowerCase() === "1";

  let filePath;
  try {
    filePath = await ensureReportPdfFile(report, { forceRefresh });
  } catch (genErr) {
    const detail =
      genErr?.message?.includes("fetch failed") || genErr?.code === "ECONNREFUSED"
        ? "Python RAG service is not reachable. Start it on port 8000 and wait for 'Application startup complete'."
        : genErr?.message || "PDF generation failed";
    console.warn("On-demand PDF generation failed:", detail);
    return res.status(503).json({ ok: false, error: detail });
  }

  if (!filePath) return res.status(404).json({ ok: false, error: "PDF not generated yet" });

  const filename = `${report.report_id}${report.is_digitally_signed ? ".signed" : ""}.pdf`;
  const inline = String(req.query.disposition || "").toLowerCase() === "inline";
  res.setHeader("Content-Type", "application/pdf");
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
  res.setHeader(
    "Content-Disposition",
    `${inline ? "inline" : "attachment"}; filename="${filename}"`
  );
  if (report.document_hash) res.setHeader("X-Document-Hash", report.document_hash);
  res.sendFile(path.resolve(filePath));
}

export async function regenerateReportPdf(req, res) {
  req.query = { ...req.query, refresh: "1" };
  return downloadReportPdf(req, res);
}

export async function prepareProof(req, res) {
  const { report_id, org_name } = req.body;
  if (!report_id) return res.status(400).json({ ok: false, error: "report_id is required" });
  if (!org_name) return res.status(400).json({ ok: false, error: "org_name is required" });

  const report = await Report.findOne({ report_id });
  if (!report) return res.status(404).json({ ok: false, error: "Report not found" });

  let pdfPath = resolveReportPdfPath(report);
  let documentHash = report.document_hash;

  if (!pdfPath || !report.is_digitally_signed) {
    const signer = {
      name: report.evaluation_metadata?.evaluator_name || "Authorized Evaluator",
      role: "Compliance Evaluator",
      remarks: report.evaluator_remarks || "",
    };
    const signed = await signPdfForReport(report, org_name, signer);
    pdfPath = signed.signedPdfPath || signed.pdfPath;
    documentHash = signed.documentHash;
    await Report.updateOne(
      { report_id },
      {
        pdf_path: signed.pdfPath,
        signed_pdf_path: signed.signedPdfPath || signed.pdfPath,
        document_hash: documentHash,
        pdf_signature: signed.pdfSignature,
        is_digitally_signed: true,
        proof_status: "signed",
      }
    );
  }

  if (!documentHash && pdfPath) {
    const hashResult = await postJson(
      `${env.fastApiBaseUrl}/report/hash`,
      { file_path: pdfPath },
      { timeoutMs: 30000 }
    );
    documentHash = hashResult?.document_hash;
  }

  let ipfsCid = report.ipfs_cid;
  if (!ipfsCid && pdfPath) {
    const ipfsResult = await postJson(
      `${env.fastApiBaseUrl}/ipfs`,
      { file_path: pdfPath },
      { timeoutMs: 120000 }
    );
    ipfsCid = ipfsResult?.ipfs_cid || null;
  }

  if (!ipfsCid) return res.status(422).json({ ok: false, error: "IPFS CID required for proof" });

  const deployment = getBlockchainDeployment();
  res.status(200).json({
    ok: true,
    report_id,
    ipfs_cid: ipfsCid,
    document_hash: documentHash,
    org_name,
    risk_level: report.risk_level || "MEDIUM",
    contract_address: deployment.address,
    pdf_path: pdfPath,
    is_digitally_signed: true,
  });
}

export async function anchorProof(req, res) {
  const { report_id, tx_hash, ipfs_cid, pdf_path } = req.body;
  if (!report_id || !tx_hash) {
    return res.status(400).json({ ok: false, error: "report_id and tx_hash are required" });
  }

  const updated = await Report.findOneAndUpdate(
    { report_id },
    { tx_hash, ipfs_cid: ipfs_cid || undefined, pdf_path: pdf_path || undefined, proof_status: "anchored" },
    { new: true }
  );

  res.json({ ok: true, report: updated });
}
