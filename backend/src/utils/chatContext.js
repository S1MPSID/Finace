import { ChatSession } from "../models/ChatSession.js";
import { buildConversationSnapshots, buildTrustStats } from "./trustAnalytics.js";

export async function loadChatContext(chatId, userId) {
  if (!chatId) {
    return { trust_stats: {}, conversation_snapshots: [], messages: [] };
  }

  const session = await ChatSession.findOne({ session_id: chatId, user_id: userId }).lean();
  if (!session) {
    return { trust_stats: {}, conversation_snapshots: [], messages: [] };
  }

  const trust_stats = session.trust_stats?.trust_index
    ? session.trust_stats
    : buildTrustStats(session.messages || []);

  return {
    trust_stats,
    conversation_snapshots: buildConversationSnapshots(session.messages || []),
    messages: session.messages || [],
    chat_type: session.chat_type || "general_query",
    selected_categories: session.selected_categories || [],
    shap_enabled: Boolean(session.shap_enabled),
    semantic_ml_enabled: Boolean(session.semantic_ml_enabled),
    calibration_frozen: session.calibration_phi0_blended != null
      ? {
          phi0_seed: session.calibration_phi0_seed,
          phi0_live: session.calibration_phi0_live,
          phi0_blended: session.calibration_phi0_blended,
          frozen_at: session.calibration_frozen_at,
        }
      : null,
  };
}
