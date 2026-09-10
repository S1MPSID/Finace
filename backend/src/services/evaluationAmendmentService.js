import crypto from "crypto";
import path from "node:path";
import { Report } from "../models/Report.js";
import { HttpError } from "../utils/httpError.js";
import { buildEvaluationLogEntry, diffField } from "../utils/evaluationLog.js";

const EDITABLE_FIELDS = [
  "compliance_score",
  "risk_level",
  "explanation",
  "recommendations",
  "risk_flags",
];

function parseList(value) {
  if (Array.isArray(value)) return value.map(String).map((s) => s.trim()).filter(Boolean);
  if (typeof value === "string") {
    return value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
  }
  return [];
}

function validateAmendmentPayload(body) {
  const hasFieldEdits = EDITABLE_FIELDS.some((f) => body[f] !== undefined && body[f] !== null);
  const hasReference =
    body.reference &&
    String(body.reference.document_name || "").trim() &&
    String(body.reference.reference_text || "").trim();

  if (!hasFieldEdits && !hasReference) {
    throw new HttpError(400, "bad_request", "Provide field changes or a regulatory reference");
  }

  if (hasFieldEdits && !String(body.comment || "").trim()) {
    throw new HttpError(400, "bad_request", "Comment is required when changing compliance fields");
  }

  if (body.compliance_score !== undefined) {
    const score = Number(body.compliance_score);
    if (!Number.isFinite(score) || score < 0 || score > 100) {
      throw new HttpError(400, "bad_request", "compliance_score must be between 0 and 100");
    }
  }

  if (body.risk_level !== undefined) {
    const risk = String(body.risk_level).toUpperCase();
    if (!["HIGH", "MEDIUM", "LOW"].includes(risk)) {
      throw new HttpError(400, "bad_request", "risk_level must be HIGH, MEDIUM, or LOW");
    }
  }
}

export async function applyReportAmendments(reportId, body, actor) {
  validateAmendmentPayload(body);

  const report = await Report.findOne({ report_id: reportId });
  if (!report) throw new HttpError(404, "not_found", "Report not found");

  if (report.tx_hash && report.ipfs_cid) {
    throw new HttpError(409, "conflict", "Cannot amend a report that is already anchored on-chain");
  }

  const updates = {};
  const changes = [];

  if (body.compliance_score !== undefined) {
    const score = Math.round(Number(body.compliance_score));
    const diff = diffField("compliance_score", report.compliance_score, score);
    if (diff) {
      changes.push(diff);
      updates.compliance_score = score;
    }
  }

  if (body.risk_level !== undefined) {
    const risk = String(body.risk_level).toUpperCase();
    const diff = diffField("risk_level", report.risk_level, risk);
    if (diff) {
      changes.push(diff);
      updates.risk_level = risk;
    }
  }

  if (body.explanation !== undefined) {
    const text = String(body.explanation).trim();
    const diff = diffField("explanation", report.explanation, text);
    if (diff) {
      changes.push(diff);
      updates.explanation = text;
    }
  }

  if (body.recommendations !== undefined) {
    const recs = parseList(body.recommendations);
    const diff = diffField("recommendations", report.recommendations, recs);
    if (diff) {
      changes.push(diff);
      updates.recommendations = recs;
    }
  }

  if (body.risk_flags !== undefined) {
    const flags = parseList(body.risk_flags);
    const diff = diffField("risk_flags", report.risk_flags, flags);
    if (diff) {
      changes.push(diff);
      updates.risk_flags = flags;
    }
  }

  let referenceRecord = null;
  if (body.reference) {
    const docPath = String(body.reference.document_name).trim();
    const docLabel = path.basename(docPath).replace(/\.pdf$/i, "");
    const refText = String(body.reference.reference_text).trim();
    const refComment = String(body.reference.comment || body.comment || "").trim();

    referenceRecord = {
      reference_id: `ref_${crypto.randomBytes(4).toString("hex")}`,
      document_name: docLabel,
      document_path: docPath,
      reference_text: refText,
      comment: refComment,
      added_by: actor.name || actor.email || "Evaluator",
      added_at: new Date(),
    };

    const clause = {
      title: "Evaluator Citation",
      text: refText,
      source: docPath,
      document_name: docLabel,
      document_path: docPath,
      evaluator_sourced: true,
    };

    updates._referenceClause = clause;
  }

  const logEntries = [];

  if (changes.length > 0) {
    logEntries.push(
      buildEvaluationLogEntry({
        action: "amendment",
        actor: { ...actor, role: "evaluator" },
        comment: String(body.comment || "").trim(),
        changes,
        reference: referenceRecord || undefined,
      })
    );
  } else if (referenceRecord) {
    logEntries.push(
      buildEvaluationLogEntry({
        action: "reference_added",
        actor: { ...actor, role: "evaluator" },
        comment: referenceRecord.comment,
        reference: referenceRecord,
      })
    );
  }

  if (logEntries.length === 0) {
    throw new HttpError(400, "bad_request", "No changes detected");
  }

  const setPayload = {
    compliance_score: updates.compliance_score,
    risk_level: updates.risk_level,
    explanation: updates.explanation,
    recommendations: updates.recommendations,
    risk_flags: updates.risk_flags,
    is_digitally_signed: false,
    signed_pdf_path: undefined,
    proof_status: report.proof_status === "anchored" ? "anchored" : "none",
  };
  Object.keys(setPayload).forEach((k) => setPayload[k] === undefined && delete setPayload[k]);

  const pushPayload = {
    evaluation_logs: { $each: logEntries },
  };
  if (referenceRecord) {
    pushPayload.evaluator_references = referenceRecord;
    pushPayload.applicable_clauses = updates._referenceClause;
  }

  const updateDoc = {
    $set: setPayload,
    $push: pushPayload,
  };

  const updated = await Report.findOneAndUpdate({ report_id: reportId }, updateDoc, { new: true });
  return updated;
}

export async function getReportEvaluationLogs(reportId, user) {
  const filter = { report_id: reportId };
  if (user.role === "user") filter.user_id = user.user_id;

  const report = await Report.findOne(filter).lean();
  if (!report) throw new HttpError(404, "not_found", "Report not found or access denied");

  return {
    report_id: report.report_id,
    logs: report.evaluation_logs || [],
    references: report.evaluator_references || [],
  };
}
