import mongoose from "mongoose";
import { ChatSession } from "../models/ChatSession.js";
import { Report } from "../models/Report.js";
import { clearReportPdfFiles } from "../utils/reportPdfPaths.js";

/**
 * Delete chat session and all Mongo-linked artifacts (reports, calibration snapshots, PDFs).
 */
export async function deleteChatAndLinkedData(sessionId, userId) {
  const session = await ChatSession.findOne({ session_id: sessionId, user_id: userId });
  if (!session) return null;

  const reportQuery = {
    user_id: userId,
    $or: [{ chat_id: sessionId }, ...(session.report_id ? [{ report_id: session.report_id }] : [])],
  };
  const reports = await Report.find(reportQuery).lean();

  for (const report of reports) {
    clearReportPdfFiles(report);
  }
  await Report.deleteMany(reportQuery);

  try {
    const db = mongoose.connection.db;
    if (db) {
      await db.collection("calibration_snapshots").deleteMany({ chat_id: sessionId });
    }
  } catch (err) {
    console.warn("calibration_snapshots cleanup:", err.message);
  }

  await ChatSession.deleteOne({ session_id: sessionId, user_id: userId });
  return { session_id: sessionId, reports_removed: reports.length };
}
