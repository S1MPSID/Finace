import { Router } from "express";

import { askGeneralQuery, searchRegulations } from "../controllers/ragController.js";
import { requireApiKey } from "../middlewares/requireApiKey.js";
import { requireAuth } from "../middlewares/requireEvaluatorAuth.js";
import { validateRequest } from "../middlewares/validateRequest.js";
import { validateRagQueryRequest } from "../validators/ragValidators.js";
import { asyncHandler } from "../utils/asyncHandler.js";

const router = Router();

// Middleware to allow either API Key (machines) OR JWT (Company Users in Frontend)
const requireFlexibleAuth = (req, res, next) => {
  if (req.header("x-api-key")) return requireApiKey(req, res, next);
  return requireAuth(req, res, next);
};

// POST /api/v1/rag/query
router.post("/query", requireFlexibleAuth, validateRequest(validateRagQueryRequest), asyncHandler(askGeneralQuery));

// GET /api/v1/rag/search
router.get("/search", requireFlexibleAuth, asyncHandler(searchRegulations));

export default router;
