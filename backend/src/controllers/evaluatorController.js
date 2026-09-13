import { evaluateResponse } from "../services/evaluatorService.js";
import { Report } from "../models/Report.js";
import { generateAndSignReport } from "../services/reportPdfService.js";
import {
  applyReportAmendments,
  getReportEvaluationLogs,
} from "../services/evaluationAmendmentService.js";
import { buildEvaluationLogEntry } from "../utils/evaluationLog.js";

// Automated pre-evaluation
export async function evaluateComplianceResponse(req, res) {
  const evaluation = evaluateResponse(req.validated);
  res.json({ ok: true, evaluation });
}

/**
 * getReports - Role-based visibility
 * Companies (user) see ONLY their own reports.
 * Evaluators see ALL reports from all companies.
 */
export async function getReports(req, res) {
  try {
    const { status } = req.query;
    let filter = {};

    // Apply status filter if provided
    if (status) filter.status = status;

    // Apply ownership filter
    // req.user is set by the requireAuth middleware
    if (req.user.role === "user") {
      filter.user_id = req.user.user_id;
    } 
    // If role is 'evaluator', we don't add the user_id filter (they see everything)

    const reports = await Report.find(filter).sort({ created_at: -1 });
    res.json({ ok: true, reports });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
}

export async function getReportById(req, res) {
  try {
    const filter = { report_id: req.params.id };
    
    // Safety: Companies can only fetch their own report
    if (req.user.role === "user") {
      filter.user_id = req.user.user_id;
    }

    const report = await Report.findOne(filter);
    if (!report) return res.status(404).json({ ok: false, error: "Report not found or access denied" });
    res.json({ ok: true, report });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
}

export async function submitReview(req, res) {
  try {
    const { status, evaluator_remarks, remarks } = req.body;
    const finalRemarks = String(evaluator_remarks || remarks || "").trim();
    if (finalRemarks.length < 10) {
      return res.status(400).json({
        ok: false,
        error: "Evaluator remarks are required (minimum 10 characters) for audit compliance",
      });
    }
    const actor = req.evaluator || req.user || {};
    const evaluator_id = actor.evaluator_id || actor.user_id || "unknown";

    if (!["verified", "rejected"].includes(status)) {
      return res.status(400).json({ ok: false, error: "Invalid status" });
    }

    const existing = await Report.findOne({ report_id: req.params.id });
    if (!existing) return res.status(404).json({ ok: false, error: "Report not found" });

    const reviewLog = buildEvaluationLogEntry({
      action: status === "verified" ? "verified" : "rejected",
      actor: { ...actor, role: "evaluator" },
      comment: finalRemarks,
      changes: [{ field: "status", old_value: existing.status, new_value: status }],
    });

    let report = await Report.findOneAndUpdate(
      { report_id: req.params.id },
      {
        status,
        evaluator_remarks: finalRemarks,
        $set: {
          "evaluation_metadata.evaluator_id": evaluator_id,
          "evaluation_metadata.evaluator_name": actor.name || "Legal Expert",
          "evaluation_metadata.evaluated_at": new Date(),
        },
        $push: { evaluation_logs: reviewLog },
      },
      { new: true }
    );

    if (status === "verified") {
      try {
        const signer = {
          name: actor.name || "Authorized Evaluator",
          role: "Compliance Evaluator",
          remarks: finalRemarks,
        };
        const signed = await generateAndSignReport(report, signer);
        await Report.updateOne(
          { report_id: report.report_id },
          {
            pdf_path: signed.pdfPath,
            signed_pdf_path: signed.signedPdfPath,
            document_hash: signed.documentHash,
            pdf_signature: signed.pdfSignature,
            is_digitally_signed: true,
            proof_status: "signed",
          }
        );
        report = await Report.findOne({ report_id: report.report_id });
      } catch (signErr) {
        console.warn("PDF signing deferred to proof step:", signErr.message);
      }
    }

    res.json({ ok: true, report });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
}

export async function amendReport(req, res) {
  try {
    const actor = req.evaluator || req.user || {};
    const report = await applyReportAmendments(req.params.id, req.body, actor);
    res.json({ ok: true, report });
  } catch (error) {
    if (error.statusCode) {
      return res.status(error.statusCode).json({ ok: false, error: error.message });
    }
    res.status(500).json({ ok: false, error: error.message });
  }
}

export async function listEvaluationLogs(req, res) {
  try {
    const data = await getReportEvaluationLogs(req.params.id, req.user || {});
    res.json({ ok: true, ...data });
  } catch (error) {
    if (error.statusCode) {
      return res.status(error.statusCode).json({ ok: false, error: error.message });
    }
    res.status(500).json({ ok: false, error: error.message });
  }
}
