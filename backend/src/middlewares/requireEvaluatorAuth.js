import { verifyToken } from "../utils/jwtHelper.js";
import { HttpError } from "../utils/httpError.js";

/**
 * requireAuth - Allows any authenticated user (Company or Evaluator)
 */
export function requireAuth(req, _res, next) {
  const header = req.header("Authorization");
  if (!header || !header.startsWith("Bearer ")) {
    return next(new HttpError(401, "unauthorized", "Missing or invalid Authorization header"));
  }

  const token = header.slice(7);
  try {
    const decoded = verifyToken(token);
    // Attach user/evaluator info to request
    req.user = decoded; 
    next();
  } catch (err) {
    next(new HttpError(401, "unauthorized", "Invalid or expired token"));
  }
}

/**
 * requireEvaluatorAuth - Strict check for Evaluator role only
 * (Used only for specific review actions if needed)
 */
export function requireEvaluatorAuth(req, _res, next) {
  const header = req.header("Authorization");
  if (!header || !header.startsWith("Bearer ")) {
    return next(new HttpError(401, "unauthorized", "Missing or invalid Authorization header"));
  }

  const token = header.slice(7);
  try {
    const decoded = verifyToken(token);
    if (decoded.role !== "evaluator") {
      return next(new HttpError(403, "forbidden", "Evaluator role required for this action"));
    }
    req.evaluator = decoded;
    next();
  } catch (err) {
    next(new HttpError(401, "unauthorized", "Invalid or expired token"));
  }
}
