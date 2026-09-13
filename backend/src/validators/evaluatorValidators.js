import {
  ensureEnum,
  ensureObject,
  ensureOptionalString,
  ensureString,
} from "../utils/validation.js";
import { HttpError } from "../utils/httpError.js";

const riskLevels = ["LOW", "MEDIUM", "HIGH"];

function ensureStringArray(value, field, { required = false, maxItems = 20 } = {}) {
  if (value == null) {
    if (required) {
      throw new HttpError(400, "validation_error", `${field} is required`);
    }
    return [];
  }

  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new HttpError(400, "validation_error", `${field} must be an array of strings`);
  }

  return value.map((item) => item.trim()).filter(Boolean).slice(0, maxItems);
}

function ensureCitationArray(value, field) {
  if (value == null) {
    return [];
  }

  if (!Array.isArray(value)) {
    throw new HttpError(400, "validation_error", `${field} must be an array`);
  }

  return value.slice(0, 10).map((entry, index) => {
    ensureObject(entry, `${field}[${index}]`);
    return {
      title: ensureOptionalString(entry.title, `${field}[${index}].title`, { maxLength: 200 }) ?? "",
      source:
        ensureOptionalString(entry.source, `${field}[${index}].source`, { maxLength: 200 }) ?? "",
      text: ensureOptionalString(entry.text, `${field}[${index}].text`, { maxLength: 2000 }) ?? "",
    };
  });
}

export function validateEvaluateRequest(req) {
  ensureObject(req.body, "body");

  return {
    answer: ensureString(req.body.answer, "answer", { minLength: 10, maxLength: 12000 }),
    riskLevel: ensureEnum(req.body.riskLevel, "riskLevel", riskLevels, { required: true }),
    riskFlags: ensureStringArray(req.body.riskFlags, "riskFlags"),
    recommendations: ensureStringArray(req.body.recommendations, "recommendations"),
    reasoningSteps: ensureStringArray(req.body.reasoningSteps, "reasoningSteps"),
    citations: ensureCitationArray(req.body.citations, "citations"),
    callType:
      ensureOptionalString(req.body.callType, "callType", {
        maxLength: 60,
      }) ?? "general_query",
  };
}
