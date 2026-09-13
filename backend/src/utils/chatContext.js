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
  };
}
