import crypto from "crypto";
import { ChatSession } from "../models/ChatSession.js";
import { HttpError } from "../utils/httpError.js";
import { buildTrustStats } from "../utils/trustAnalytics.js";

function isEvaluator(req) {
  return req.user?.role === "evaluator";
}

function getUserId(req) {
  if (isEvaluator(req)) return null;
  return req.user?.user_id || req.user?.id || req.user?.sub || null;
}

function requireCompanyUser(req) {
  if (isEvaluator(req)) {
    throw new HttpError(403, "forbidden", "Chat history is not available for evaluator accounts");
  }
  const userId = getUserId(req);
  if (!userId) throw new HttpError(401, "unauthorized", "User id missing from token");
  return userId;
}

function titleFromMessages(messages = []) {
  const firstUser = messages.find((m) => m.role === "user" && m.content?.trim());
  if (!firstUser) return "New compliance chat";
  const text = firstUser.content.trim().replace(/\s+/g, " ");
  return text.length > 64 ? `${text.slice(0, 61)}...` : text;
}

export async function listChatSessions(req, res) {
  if (isEvaluator(req)) {
    return res.json({ ok: true, sessions: [] });
  }
  const userId = requireCompanyUser(req);

  const sessions = await ChatSession.find({ user_id: userId })
    .sort({ updated_at: -1 })
    .select("session_id title last_risk_level last_score created_at updated_at messages")
    .lean();

  res.json({
    ok: true,
    sessions: sessions.map((s) => ({
      session_id: s.session_id,
      title: s.title,
      last_risk_level: s.last_risk_level,
      last_score: s.last_score,
      message_count: Array.isArray(s.messages) ? s.messages.length : 0,
      created_at: s.created_at,
      updated_at: s.updated_at,
      preview: s.messages?.find((m) => m.role === "user")?.content?.slice(0, 120) || "",
    })),
  });
}

export async function getChatSession(req, res) {
  const userId = requireCompanyUser(req);

  const session = await ChatSession.findOne({
    session_id: req.params.id,
    user_id: userId,
  }).lean();

  if (!session) throw new HttpError(404, "not_found", "Chat session not found");
  res.json({ ok: true, session });
}

export async function createChatSession(req, res) {
  const userId = requireCompanyUser(req);

  const messages = Array.isArray(req.body.messages) ? req.body.messages : [];
  const session_id = `chat_${crypto.randomBytes(6).toString("hex")}`;
  const lastAi = [...messages].reverse().find((m) => m.role === "ai");
  const trust_stats = buildTrustStats(messages);

  const session = await ChatSession.create({
    session_id,
    user_id: userId,
    title: req.body.title || titleFromMessages(messages),
    messages,
    last_risk_level: lastAi?.risk_level || lastAi?.data?.risk_level,
    last_score: lastAi?.compliance_score ?? lastAi?.data?.compliance_score,
    trust_stats,
  });

  res.status(201).json({ ok: true, session });
}

export async function upsertChatSession(req, res) {
  const userId = requireCompanyUser(req);

  const messages = Array.isArray(req.body.messages) ? req.body.messages : [];
  const lastAi = [...messages].reverse().find((m) => m.role === "ai");
  const trust_stats = buildTrustStats(messages);
  const payload = {
    title: req.body.title || titleFromMessages(messages),
    messages,
    last_risk_level: lastAi?.risk_level || lastAi?.data?.risk_level,
    last_score: lastAi?.compliance_score ?? lastAi?.data?.compliance_score,
    trust_stats,
  };

  let session;
  if (req.params.id) {
    session = await ChatSession.findOneAndUpdate(
      { session_id: req.params.id, user_id: userId },
      { $set: payload },
      { new: true }
    );
    if (!session) throw new HttpError(404, "not_found", "Chat session not found");
  } else {
    const session_id = `chat_${crypto.randomBytes(6).toString("hex")}`;
    session = await ChatSession.create({
      session_id,
      user_id: userId,
      ...payload,
    });
  }

  res.json({ ok: true, session });
}

export async function deleteChatSession(req, res) {
  const userId = requireCompanyUser(req);

  const deleted = await ChatSession.findOneAndDelete({
    session_id: req.params.id,
    user_id: userId,
  });
  if (!deleted) throw new HttpError(404, "not_found", "Chat session not found");
  res.json({ ok: true, deleted: true });
}
