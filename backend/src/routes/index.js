import { Router } from "express";

import blockchainRoutes from "./blockchainRoutes.js";
import evaluatorAuthRoutes from "./evaluatorAuthRoutes.js";
import userAuthRoutes from "./userAuthRoutes.js";
import evaluatorRoutes from "./evaluatorRoutes.js";
import healthRoutes from "./healthRoutes.js";
import ragRoutes from "./ragRoutes.js";
import reportRoutes from "./reportRoutes.js";
import docsRoutes from "./docsRoutes.js";
import chatHistoryRoutes from "./chatHistoryRoutes.js";

const router = Router();

router.use("/health", healthRoutes);
router.use("/docs", docsRoutes);
router.use("/rag", ragRoutes);
router.use("/blockchain", blockchainRoutes);
router.use("/auth", userAuthRoutes);
router.use("/evaluator/auth", evaluatorAuthRoutes);
router.use("/evaluator", evaluatorRoutes);
router.use("/reports", reportRoutes);
router.use("/chats", chatHistoryRoutes);
router.use("/regulations", ragRoutes); // Alias for frontend compatibility

export default router;
