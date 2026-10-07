import { getJson } from "../services/httpClient.js";
import { env } from "../config/env.js";

export async function getDashboard(req, res) {
  const data = await getJson(`${env.fastApiBaseUrl}/ml-validation/dashboard`, {
    timeoutMs: env.fastApiTimeoutMs,
  });
  res.json({ ok: true, ...data });
}

export async function listCases(req, res) {
  const set = String(req.query.set || "robustness");
  const limit = Number(req.query.limit || 20);
  const offset = Number(req.query.offset || 0);
  const predict = req.query.predict === "0" || req.query.predict === "false" ? false : true;
  const qs = new URLSearchParams({
    set,
    limit: String(Number.isFinite(limit) ? limit : 20),
    offset: String(Number.isFinite(offset) ? offset : 0),
    predict: predict ? "true" : "false",
  });
  const data = await getJson(`${env.fastApiBaseUrl}/ml-validation/cases?${qs}`, {
    timeoutMs: Math.max(env.fastApiTimeoutMs, 120000),
  });
  res.json({ ok: true, ...data });
}

export async function getCase(req, res) {
  const caseId = encodeURIComponent(req.params.caseId);
  const data = await getJson(`${env.fastApiBaseUrl}/ml-validation/cases/${caseId}`, {
    timeoutMs: Math.max(env.fastApiTimeoutMs, 60000),
  });
  res.json({ ok: true, ...data });
}
