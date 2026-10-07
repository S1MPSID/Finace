import { Router } from "express";
import { asyncHandler } from "../utils/asyncHandler.js";
import { getCase, getDashboard, listCases } from "../controllers/mlValidationController.js";
import { requireAuth } from "../middlewares/requireEvaluatorAuth.js";

const router = Router();

router.get("/dashboard", requireAuth, asyncHandler(getDashboard));
router.get("/cases", requireAuth, asyncHandler(listCases));
router.get("/cases/:caseId", requireAuth, asyncHandler(getCase));

export default router;
