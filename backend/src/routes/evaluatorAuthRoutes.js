import { Router } from "express";
import bcrypt from "bcryptjs";
import crypto from "crypto";
import { Evaluator } from "../models/Evaluator.js";
import { signToken } from "../utils/jwtHelper.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import { requireEvaluatorAuth } from "../middlewares/requireEvaluatorAuth.js";

const router = Router();

// POST /api/v1/evaluator/auth/register
router.post(
  "/register",
  asyncHandler(async (req, res) => {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ ok: false, error: "name, email, and password are required" });
    }

    if (password.length < 6) {
      return res.status(400).json({ ok: false, error: "Password must be at least 6 characters" });
    }

    const existing = await Evaluator.findOne({ email: email.toLowerCase().trim() });
    if (existing) {
      return res.status(409).json({ ok: false, error: "An evaluator with this email already exists" });
    }

    const password_hash = await bcrypt.hash(password, 10);
    const evaluator_id = `eval_${crypto.randomBytes(4).toString("hex")}`;

    const evaluator = await Evaluator.create({
      evaluator_id,
      name: name.trim(),
      email: email.toLowerCase().trim(),
      password_hash,
      role: "evaluator",
    });

    const token = signToken({
      evaluator_id: evaluator.evaluator_id,
      email: evaluator.email,
      name: evaluator.name,
      role: "evaluator",
    });

    res.status(201).json({
      ok: true,
      token,
      evaluator: {
        evaluator_id: evaluator.evaluator_id,
        name: evaluator.name,
        email: evaluator.email,
        role: evaluator.role,
      },
    });
  })
);

// POST /api/v1/evaluator/auth/login
router.post(
  "/login",
  asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ ok: false, error: "email and password are required" });
    }

    const evaluator = await Evaluator.findOne({ email: email.toLowerCase().trim() });
    if (!evaluator) {
      return res.status(401).json({ ok: false, error: "Invalid email or password" });
    }

    const valid = await bcrypt.compare(password, evaluator.password_hash);
    if (!valid) {
      return res.status(401).json({ ok: false, error: "Invalid email or password" });
    }

    const token = signToken({
      evaluator_id: evaluator.evaluator_id,
      email: evaluator.email,
      name: evaluator.name,
      role: "evaluator",
    });

    res.json({
      ok: true,
      token,
      evaluator: {
        evaluator_id: evaluator.evaluator_id,
        name: evaluator.name,
        email: evaluator.email,
        role: evaluator.role,
      },
    });
  })
);

// GET /api/v1/evaluator/auth/me — restore evaluator session from Bearer token
router.get(
  "/me",
  requireEvaluatorAuth,
  asyncHandler(async (req, res) => {
    const payload = req.evaluator || {};
    res.json({
      ok: true,
      user: {
        id: payload.evaluator_id || payload.id,
        name: payload.name || payload.email || "Evaluator",
        email: payload.email,
        role: "evaluator",
      },
    });
  })
);

export default router;
