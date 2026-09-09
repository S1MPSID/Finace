import { Router } from "express";
import { asyncHandler } from "../utils/asyncHandler.js";
import { requireApiKey } from "../middlewares/requireApiKey.js";
import { requireAuth } from "../middlewares/requireEvaluatorAuth.js";
import {
  anchorProof,
  downloadReportPdf,
  generateReport,
  prepareProof,
  regenerateReportPdf,
  signReport,
  updateReport,
} from "../controllers/reportController.js";

const router = Router();

const requireEitherAuth = (req, res, next) => {
  const apiKey = req.header("x-api-key");
  const authHeader = req.header("Authorization");
  if (apiKey) return requireApiKey(req, res, next);
  if (authHeader) return requireAuth(req, res, next);
  return res.status(401).json({ ok: false, error: "Authentication required (API Key or JWT)" });
};

router.post("/generate", requireEitherAuth, asyncHandler(generateReport));
router.post("/update", requireEitherAuth, asyncHandler(updateReport));
router.post("/:id/sign", requireEitherAuth, asyncHandler(signReport));
router.get("/:id/pdf", requireEitherAuth, asyncHandler(downloadReportPdf));
router.post("/:id/pdf/regenerate", requireEitherAuth, asyncHandler(regenerateReportPdf));
router.post("/proof", requireEitherAuth, asyncHandler(prepareProof));
router.post("/anchor", requireEitherAuth, asyncHandler(anchorProof));

export default router;
