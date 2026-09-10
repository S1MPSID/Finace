import mongoose from "mongoose";

const messageSchema = new mongoose.Schema(
  {
    role: { type: String, enum: ["user", "ai"], required: true },
    content: { type: String, default: "" },
    sources: { type: [Object], default: [] },
    risk_level: String,
    risk_flags: { type: [String], default: [] },
    compliance_score: Number,
    reasoning_steps: { type: [String], default: [] },
    xai: { type: Object, default: {} },
    analysis: { type: Object, default: {} },
  },
  { _id: false }
);

const chatSessionSchema = new mongoose.Schema(
  {
    session_id: { type: String, required: true, unique: true },
    user_id: { type: String, required: true, index: true },
    title: { type: String, default: "New compliance chat" },
    messages: { type: [messageSchema], default: [] },
    last_risk_level: String,
    last_score: Number,
    trust_stats: { type: Object, default: {} },
    report_id: String,
  },
  {
    timestamps: { createdAt: "created_at", updatedAt: "updated_at" },
    collection: "chat_sessions",
  }
);

chatSessionSchema.index({ user_id: 1, updated_at: -1 });

export const ChatSession = mongoose.model("ChatSession", chatSessionSchema);
