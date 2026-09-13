import { Router } from "express";

import { createProof, getDeployment } from "../controllers/blockchainController.js";
import { requireApiKey } from "../middlewares/requireApiKey.js";
import { validateRequest } from "../middlewares/validateRequest.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import { validateStoreProofRequest } from "../validators/blockchainValidators.js";

const router = Router();

router.get("/deployment", requireApiKey, asyncHandler(getDeployment));
router.post("/proofs", requireApiKey, validateRequest(validateStoreProofRequest), asyncHandler(createProof));

export default router;
