import { HttpError } from "./httpError.js";

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function ensureObject(value, field) {
  if (!isPlainObject(value)) {
    throw new HttpError(400, "validation_error", `${field} must be an object`);
  }
}

export function ensureString(value, field, { required = true, minLength = 1, maxLength = 5000 } = {}) {
  if (value == null || value === "") {
    if (required) {
      throw new HttpError(400, "validation_error", `${field} is required`);
    }
    return undefined;
  }
  if (typeof value !== "string") {
    throw new HttpError(400, "validation_error", `${field} must be a string`);
  }

  const trimmed = value.trim();
  if (trimmed.length < minLength) {
    throw new HttpError(400, "validation_error", `${field} must be at least ${minLength} characters`);
  }
  if (trimmed.length > maxLength) {
    throw new HttpError(400, "validation_error", `${field} must be at most ${maxLength} characters`);
  }
  return trimmed;
}

export function ensureOptionalString(value, field, options = {}) {
  return ensureString(value, field, { ...options, required: false });
}

export function ensureInteger(value, field, { required = false, min = Number.MIN_SAFE_INTEGER, max = Number.MAX_SAFE_INTEGER } = {}) {
  if (value == null || value === "") {
    if (required) {
      throw new HttpError(400, "validation_error", `${field} is required`);
    }
    return undefined;
  }
  if (!Number.isInteger(value)) {
    throw new HttpError(400, "validation_error", `${field} must be an integer`);
  }
  if (value < min || value > max) {
    throw new HttpError(400, "validation_error", `${field} must be between ${min} and ${max}`);
  }
  return value;
}

export function ensureEnum(value, field, allowedValues, { required = false } = {}) {
  if (value == null || value === "") {
    if (required) {
      throw new HttpError(400, "validation_error", `${field} is required`);
    }
    return undefined;
  }
  if (!allowedValues.includes(value)) {
    throw new HttpError(
      400,
      "validation_error",
      `${field} must be one of: ${allowedValues.join(", ")}`
    );
  }
  return value;
}
