import {
  ensureInteger,
  ensureObject,
  ensureOptionalString,
  ensureString,
} from "../utils/validation.js";

export function validateRagQueryRequest(req) {
  ensureObject(req.body, "body");

  const callType = req.body.call_type || req.body.callType || "general_query";
  const activeCategories = Array.isArray(req.body.active_categories)
    ? req.body.active_categories
    : Array.isArray(req.body.activeCategories)
      ? req.body.activeCategories
      : [];

  return {
    prompt: ensureString(req.body.prompt, "prompt", { minLength: 3, maxLength: 32000 }),
    topK: ensureInteger(req.body.topK ?? 5, "topK", { min: 1, max: 20 }),
    regulator: ensureOptionalString(req.body.regulator, "regulator", { maxLength: 120 }) ?? null,
    category: ensureOptionalString(req.body.category, "category", { maxLength: 120 }) ?? null,
    callType: ["general_query", "new_report", "update_report"].includes(callType)
      ? callType
      : "general_query",
    activeCategories: activeCategories.map((c) => String(c)).slice(0, 20),
    enableXai: Boolean(req.body.enable_xai ?? req.body.enableXai),
    enableSemanticMl: Boolean(
      req.body.enable_semantic_ml ?? req.body.enableSemanticMl ?? false
    ),
    chatId:
      ensureOptionalString(req.body.chat_id ?? req.body.chatId, "chatId", { maxLength: 120 }) ??
      null,
  };
}
