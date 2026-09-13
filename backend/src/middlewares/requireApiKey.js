import { env } from "../config/env.js";
import { HttpError } from "../utils/httpError.js";

export function requireApiKey(req, _res, next) {
  if (!env.gatewayApiKey) {
    next();
    return;
  }

  const token = req.header("x-api-key");
  if (token !== env.gatewayApiKey) {
    next(new HttpError(401, "unauthorized", "Invalid API key"));
    return;
  }

  next();
}
