import mongoose from "mongoose";

const reportSchema = new mongoose.Schema(
  {
    report_id: {
      type: String,
      required: true,
      unique: true,
    },
    user_id: {
      type: String,
      required: false,
    },
    workflow_input: {
      type: Object,
      default: {},
    },
    risk_level: {
      type: String,
      enum: ["HIGH", "MEDIUM", "LOW"],
    },
    risk_flags: [String],
    applicable_clauses: [Object],
    explanation: String,
    recommendations: [String],
    compliance_score: {
      type: Number,
      min: 0,
      max: 100,
    },
    pdf_path: String,
    ipfs_cid: String,
    tx_hash: String,
    status: {
      type: String,
      enum: ["pending", "verified", "rejected"],
      default: "pending",
    },
    evaluator_remarks: String,
    evaluation_metadata: {
      type: Object,
    },
    reasoning_steps: [String],
    xai: {
      type: Object,
      default: {},
    },
    ml_risk: {
      type: Object,
      default: {},
    },
    evidence_scope: {
      type: Object,
      default: {},
    },
    rule_assessments: {
      type: [Object],
      default: [],
    },
    chat_id: String,
    trust_stats: { type: Object, default: {} },
    conversation_snapshots: { type: [Object], default: [] },
    signed_pdf_path: String,
    document_hash: String,
    pdf_signature: { type: Object, default: {} },
    is_digitally_signed: { type: Boolean, default: false },
    proof_status: {
      type: String,
      enum: ["none", "pdf_ready", "signed", "anchored"],
      default: "none",
    },
    evaluation_logs: {
      type: [Object],
      default: [],
    },
    evaluator_references: {
      type: [Object],
      default: [],
    },
  },
  {
    timestamps: { createdAt: "created_at", updatedAt: "updated_at" },
    collection: "reports",
  }
);

export const Report = mongoose.model("Report", reportSchema);
