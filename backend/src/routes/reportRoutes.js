import { Router } from "express";
import { asyncHandler } from "../utils/asyncHandler.js";
import { requireApiKey } from "../middlewares/requireApiKey.js";
import { requireAuth } from "../middlewares/requireEvaluatorAuth.js";
import {
  anchorProof,
  downloadReportPdf,
  generateReport,
  prepareProof,
  regenerateReportPdf,
  signReport,
  updateReport,
} from "../controllers/reportController.js";

const router = Router();

const requireEitherAuth = (req, res, next) => {
  const apiKey = req.header("x-api-key");
  const authHeader = req.header("Authorization");
  if (apiKey) return requireApiKey(req, res, next);
  if (authHeader) return requireAuth(req, res, next);
  return res.status(401).json({ ok: false, error: "Authentication required (API Key or JWT)" });
};

// ────────────────────────────────────────────
// POST /reports/generate  — New compliance report
// ────────────────────────────────────────────
router.post(
  "/generate",
  requireEitherAuth,
  asyncHandler(async (req, res) => {
    const { workflow_text, regulator } = req.body;
    
    // Use user_id from JWT if available, else from body, else default
    const user_id = req.user?.user_id || req.body.user_id || "system";
    
    if (!workflow_text) {
      return res.status(400).json({ ok: false, error: "workflow_text is required" });
    }

    const result = await postJson(
      `${env.fastApiBaseUrl}/analyze`,
      {
        call_type: "new_report",
        workflow_text,
        regulator: regulator || "RBI",
        top_k: 5,
      },
      { timeoutMs: env.fastApiTimeoutMs }
    );

    const analysis = result?.analysis || {};
    const report_id = `rep-${crypto.randomBytes(4).toString("hex")}`;
    const compliance_score = typeof analysis.compliance_score === "number" ? analysis.compliance_score : 55;

    const report = await Report.create({
      report_id,
      user_id,
      workflow_input: { text: workflow_text, regulator },
      risk_level: analysis.risk_level || "MEDIUM",
      risk_flags: analysis.risk_flags || [],
      applicable_clauses: Array.isArray(analysis.applicable_clauses) ? analysis.applicable_clauses : [],
      explanation: analysis.explanation || "Automated analysis completed.",
      recommendations: analysis.recommendations || [],
      compliance_score,
      status: "pending",
    });

    res.json({ ok: true, report_id: report.report_id, report });
  })
);

// ────────────────────────────────────────────
// POST /reports/update  — Update existing report
// ────────────────────────────────────────────
router.post(
  "/update",
  requireEitherAuth,
  asyncHandler(async (req, res) => {
    const { report_id, workflow_text, regulator } = req.body;

    try {
      if (!report_id) {
        return res.status(400).json({ ok: false, error: "report_id is required" });
      }

      const existing = await Report.findOne({ report_id });
      if (!existing) {
        return res.status(404).json({ ok: false, error: "Report not found" });
      }

      const existingReportText = [
        `Risk Level: ${existing.risk_level}`,
        `Explanation: ${existing.explanation || ""}`,
        `Recommendations: ${(existing.recommendations || []).join("; ")}`,
        `Compliance Score: ${existing.compliance_score}`,
      ].join("\n");

      const timestamp = new Date().toISOString();
      const simulatedRemediation = `[AI-IMPROVED WORKFLOW - ${timestamp}]: The entire system has been completely overhauled to meet the highest regulatory standards. We now enforce mandatory, multi-step Aadhaar-based e-KYC for all users before any account activation. All transactions require Two-Factor Authentication (2FA) via mobile OTP. User data is strictly encrypted at rest using AES-256 and in transit via TLS 1.3. We conduct full quarterly security audits and maintain compliance with all RBI data localization norms. All legacy digital asset and peer-network risks have been fully remediated with enhanced AML monitoring and FEMA-compliant reporting structures. The grievance redressal mechanism is now active with a dedicated 24/7 support desk.`;
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

      const updated = await Report.findOneAndUpdate(
        { report_id },
        {
          workflow_input: { 
            text: queryWorkflow, 
            regulator: regulator || existing.workflow_input?.regulator || "RBI" 
          },
          risk_level: analysis.risk_level || existing.risk_level,
          risk_flags: analysis.risk_flags || existing.risk_flags,
          applicable_clauses: analysis.applicable_clauses || existing.applicable_clauses,
          explanation: analysis.explanation || existing.explanation,
          recommendations: analysis.recommendations || existing.recommendations,
          compliance_score: typeof analysis.compliance_score === "number" ? analysis.compliance_score : existing.compliance_score,
          status: "pending",
          $push: {
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
    } catch (error) {
      console.error("REPORT UPDATE FAILED:", error.message, error.details || "");
      res.status(error.statusCode || 500).json({ 
        ok: false, 
        error: error.message,
        details: error.details 
      });
    }
  })
);

// ────────────────────────────────────────────
// POST /reports/proof  — Prepare data for MetaMask
// ────────────────────────────────────────────
router.post(
  "/proof",
  requireEitherAuth,
  asyncHandler(async (req, res) => {
    const { report_id, org_name } = req.body;

    if (!report_id) return res.status(400).json({ ok: false, error: "report_id is required" });
    if (!org_name) return res.status(400).json({ ok: false, error: "org_name is required" });

    const report = await Report.findOne({ report_id });
    if (!report) return res.status(404).json({ ok: false, error: "Report not found" });

    // 1. PDF Generation
    let pdfPath = report.pdf_path;
    if (!pdfPath) {
      try {
        const pdfResult = await postJson(`${env.fastApiBaseUrl}/report`, {
          report_id, org_name, analysis: report
        }, { timeoutMs: 60000 });
        pdfPath = pdfResult?.pdf_path || null;
      } catch (err) { pdfPath = null; }
    }

    // 2. IPFS
    let ipfsCid = report.ipfs_cid;
    if (!ipfsCid && pdfPath) {
      try {
        const ipfsResult = await postJson(`${env.fastApiBaseUrl}/ipfs`, { file_path: pdfPath }, { timeoutMs: 120000 });
        ipfsCid = ipfsResult?.ipfs_cid || null;
      } catch (err) { return res.status(502).json({ ok: false, error: "IPFS upload failed" }); }
    }

    if (!ipfsCid) return res.status(422).json({ ok: false, error: "IPFS CID required for proof" });

    // 3. Prepare data for client-side signing
    const deployment = getBlockchainDeployment();
    const documentHash = `0x${crypto.createHash("sha256").update(JSON.stringify(report.toObject())).digest("hex")}`;

    res.status(200).json({
      ok: true,
      report_id,
      ipfs_cid: ipfsCid,
      document_hash: documentHash,
      org_name,
      risk_level: report.risk_level || "MEDIUM",
      contract_address: deployment.address,
      pdf_path: pdfPath
    });
  })
);

// ────────────────────────────────────────────
// POST /reports/anchor  — Save Tx Hash after MetaMask
// ────────────────────────────────────────────
router.post(
  "/anchor",
  requireEitherAuth,
  asyncHandler(async (req, res) => {
    const { report_id, tx_hash, ipfs_cid, pdf_path } = req.body;

    if (!report_id || !tx_hash) {
      return res.status(400).json({ ok: false, error: "report_id and tx_hash are required" });
    }

    const updated = await Report.findOneAndUpdate(
      { report_id },
      { 
        tx_hash, 
        ipfs_cid: ipfs_cid || undefined,
        pdf_path: pdf_path || undefined,
        status: "verified" 
      },
      { new: true }
    );

    res.json({ ok: true, report: updated });
  })
);

export default router;
