import mongoose from "mongoose";

const evaluatorSchema = new mongoose.Schema(
  {
    evaluator_id: {
      type: String,
      required: true,
      unique: true,
    },
    name: {
      type: String,
      required: true,
      trim: true,
    },
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },
    password_hash: {
      type: String,
      required: true,
    },
    role: {
      type: String,
      default: "evaluator",
    },
  },
  {
    timestamps: { createdAt: "created_at", updatedAt: "updated_at" },
    collection: "evaluators",
  }
);

export const Evaluator = mongoose.model("Evaluator", evaluatorSchema);
