import mongoose from "mongoose";
import { runGeneralQuery, runRegulationSearch, uploadPdfForOcr } from "../services/ragService.js";
import { resolveCalibrationFrozenForChat } from "../services/calibrationService.js";

/**
 * Maps the complex RAG result into a clean format for the frontend chat.
 * Deduplicates sources and enriches them with actual file paths from MongoDB.
 */
async function toChatResponse(result) {
  const analysis = result?.analysis ?? {};
  
  const rawHits = Array.isArray(result.retrieval_hits) ? result.retrieval_hits : [];

  // Deduplicate by document_id — keep only unique documents
  const seen = new Set();
  const uniqueHits = rawHits.filter(hit => {
    const id = hit.document_id || "";
    if (!id || seen.has(id)) return false;
    seen.add(id);
    return true;
  });

  // Look up actual file paths from the documents collection in MongoDB
  const docIds = uniqueHits.map(h => h.document_id).filter(Boolean);
  let docLookup = {};
  if (docIds.length > 0) {
    try {
      const db = mongoose.connection.db;
      const docs = await db.collection("documents")
        .find({ regulation_id: { $in: docIds } }, { projection: { regulation_id: 1, relative_path: 1, source: 1 } })
        .toArray();
      for (const d of docs) {
        docLookup[d.regulation_id] = {
          relative_path: d.relative_path || "",
          source_file: d.source || "",
        };
      }
    } catch (err) {
      console.error("Document lookup failed:", err.message);
    }
  }

  const applicableClauses = Array.isArray(analysis.applicable_clauses)
    ? analysis.applicable_clauses
    : [];
  const citationHits = applicableClauses.length > 0 ? applicableClauses : [];
  const sources = citationHits.map(hit => {
    const lookup = docLookup[hit.document_id] || {};
    return {
      document_id: hit.document_id || "Regulation",
      section: hit.section || hit.title || "General",
      text: hit.text || hit.content || "",
      relative_path: lookup.relative_path || hit.relative_path || hit.metadata?.relative_path || "",
      source_file: lookup.source_file || hit.source || hit.metadata?.source || "",
      basis: hit.basis || "direct",
      applicability_note: hit.applicability_note || "",
    };
  });

  const answer = analysis.explanation
    || analysis.summary
    || (Array.isArray(analysis.reasoning_steps) && analysis.reasoning_steps.length
      ? analysis.reasoning_steps.join("\n")
      : "")
    || "No detailed explanation provided by AI.";

  return {
    ok: true,
    answer,
    sources,
    riskLevel: analysis.risk_level || "LOW",
    riskFlags: analysis.risk_flags || [],
    recommendations: analysis.recommendations || [],
    complianceScore:
      analysis.compliance_score === null || analysis.compliance_score === undefined
        ? undefined
        : analysis.compliance_score,
    reasoningSteps: analysis.reasoning_steps || [],
    xai: result?.xai || {},
    ml_risk: result?.ml_risk || {},
    evidence_scope: result?.evidence_scope || {},
    rule_assessments: result?.rule_assessments || [],
    analysis,
    raw: analysis
  };
}

function getQueryUserId(req) {
  return req.user?.user_id || req.user?.id || req.user?.sub || null;
}

export async function askGeneralQuery(req, res) {
  try {
    const { chatId, ...rest } = req.validated;
    const userId = getQueryUserId(req);
    const calibrationFrozen = await resolveCalibrationFrozenForChat(chatId, userId);
    const result = await runGeneralQuery({
      ...rest,
      chatId,
      calibrationFrozen,
    });
    const response = await toChatResponse(result);
    res.json(response);
  } catch (error) {
    const status = error.statusCode && error.statusCode >= 400 && error.statusCode < 600 ? error.statusCode : 500;
    res.status(status).json({
      ok: false,
      error: error.message || "RAG query failed",
      code: error.code,
      details: error.details,
    });
  }
}

export async function searchRegulations(req, res) {
  const { q, regulator, topK } = req.query;
  
  if (!q || q.trim() === "") {
    return res.json({ ok: true, data: [] });
  }

  try {
    const result = await runRegulationSearch({
      query: q,
      regulator,
      topK: topK ? parseInt(topK, 10) : 10,
    });
    res.json({
      ok: true,
      data: result.results || [],
    });
  } catch (error) {
    const status = error.statusCode && error.statusCode >= 400 && error.statusCode < 600 ? error.statusCode : 500;
    res.status(status).json({
      ok: false,
      error: error.message || "Regulation search failed",
      code: error.code,
      details: error.details,
    });
  }
}

export async function uploadPdfDocument(req, res) {
  if (!req.file) {
    return res.status(400).json({ ok: false, error: "No file uploaded" });
  }

  const { ingest } = req.query ?? {};
  const parseIngest = String(ingest ?? "0") === "1" || String(ingest ?? "0") === "true";

  try {
    const result = await uploadPdfForOcr(req.file.buffer, {
      filename: req.file.originalname || "document.pdf",
      ingest: parseIngest,
    });
    res.json({ ok: true, ...result });
  } catch (error) {
    const status = error.statusCode && error.statusCode >= 400 && error.statusCode < 600 ? error.statusCode : 500;
    res.status(status).json({
      ok: false,
      error: error.message || "PDF upload / OCR failed",
      code: error.code,
      details: error.details,
    });
  }
}
