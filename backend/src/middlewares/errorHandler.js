import { env } from "../config/env.js";

export function notFoundHandler(req, res) {
  res.status(404).json({
    error: "not_found",
    message: "Route not found",
    requestId: req.requestId,
  });
}

export function errorHandler(err, req, res, _next) {
  const statusCode = err.statusCode || 500;
  const code = err.code || "internal_error";
  const message = err.message || "Unexpected server error";

  // Graceful logging:
  // Only log full stack traces for 500 errors.
  // For 4xx errors, just log a clean one-liner.
  if (statusCode >= 500) {
    console.error(`[${req.requestId}] CRITICAL ERROR: ${req.method} ${req.url} -`, err);
  } else if (statusCode >= 400) {
    console.warn(`[${req.requestId}] Client Error (${statusCode}): ${req.method} ${req.url} - ${message}`);
  }

  res.status(statusCode).json({
    error: code,
    message,
    requestId: req.requestId,
    details: err.details ?? undefined,
    stack: env.nodeEnv === "production" || statusCode < 500 ? undefined : err.stack,
  });
}
