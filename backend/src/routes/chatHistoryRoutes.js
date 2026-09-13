import { Router } from "express";
import { requireAuth } from "../middlewares/requireEvaluatorAuth.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import {
  listChatSessions,
  getChatSession,
  createChatSession,
  upsertChatSession,
  deleteChatSession,
} from "../controllers/chatHistoryController.js";

const router = Router();

router.get("/", requireAuth, asyncHandler(listChatSessions));
router.post("/", requireAuth, asyncHandler(createChatSession));
router.get("/:id", requireAuth, asyncHandler(getChatSession));
router.put("/:id", requireAuth, asyncHandler(upsertChatSession));
router.delete("/:id", requireAuth, asyncHandler(deleteChatSession));

export default router;
