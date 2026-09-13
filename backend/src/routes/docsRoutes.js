import { Router } from "express";
import { getDocsTree } from "../controllers/docsController.js";
import { asyncHandler } from "../utils/asyncHandler.js";

const router = Router();

// GET /api/v1/docs/tree
router.get("/tree", asyncHandler(getDocsTree));

export default router;
