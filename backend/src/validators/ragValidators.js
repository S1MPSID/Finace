import {
  ensureInteger,
  ensureObject,
  ensureOptionalString,
  ensureString,
} from "../utils/validation.js";

export function validateRagQueryRequest(req) {
  ensureObject(req.body, "body");

  return {
    prompt: ensureString(req.body.prompt, "prompt", { minLength: 3, maxLength: 32000 }),
    topK: ensureInteger(req.body.topK ?? 5, "topK", { min: 1, max: 20 }),
    regulator: ensureOptionalString(req.body.regulator, "regulator", { maxLength: 120 }) ?? null,
    category: ensureOptionalString(req.body.category, "category", { maxLength: 120 }) ?? null,
  };
}
