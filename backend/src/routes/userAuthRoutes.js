import { Router } from "express";
import bcrypt from "bcryptjs";
import crypto from "crypto";
import { User } from "../models/User.js";
import { signToken } from "../utils/jwtHelper.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import { requireAuth } from "../middlewares/requireEvaluatorAuth.js";

const router = Router();

// POST /api/v1/auth/register (Company/User Registration)
router.post(
  "/register",
  asyncHandler(async (req, res) => {
    const { company_name, username, password } = req.body;

    if (!company_name || !username || !password) {
      return res.status(400).json({ ok: false, error: "company_name, username, and password are required" });
    }

    const existing = await User.findOne({ username: username.trim() });
    if (existing) {
      return res.status(409).json({ ok: false, error: "Username already taken" });
    }

    const password_hash = await bcrypt.hash(password, 10);
    const user_id = `usr_${crypto.randomBytes(4).toString("hex")}`;

    const user = await User.create({
      user_id,
      company_name: company_name.trim(),
      username: username.trim(),
      password_hash,
      role: "user",
    });

    const token = signToken({
      user_id: user.user_id,
      username: user.username,
      company_name: user.company_name,
      role: "user",
    });

    res.status(201).json({
      ok: true,
      token,
      user: {
        id: user.user_id,
        name: user.username,
        company_name: user.company_name,
        role: user.role,
      },
    });
  })
);

// POST /api/v1/auth/login (Company/User Login)
router.post(
  "/login",
  asyncHandler(async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ ok: false, error: "username and password are required" });
    }

    const user = await User.findOne({ username: username.trim() });
    if (!user) {
      return res.status(401).json({ ok: false, error: "Invalid username or password" });
    }

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      return res.status(401).json({ ok: false, error: "Invalid username or password" });
    }

    const token = signToken({
      user_id: user.user_id,
      username: user.username,
      company_name: user.company_name,
      role: "user",
    });

    res.json({
      ok: true,
      token,
      user: {
        id: user.user_id,
        name: user.username,
        company_name: user.company_name,
        role: user.role,
      },
    });
  })
);

// GET /api/v1/auth/me — restore session from Bearer token
router.get(
  "/me",
  requireAuth,
  asyncHandler(async (req, res) => {
    const payload = req.user || {};

    if (payload.role === "evaluator") {
      return res.json({
        ok: true,
        user: {
          id: payload.evaluator_id || payload.id,
          name: payload.name || payload.email || "Evaluator",
          email: payload.email,
          role: "evaluator",
        },
      });
    }

    const userId = payload.user_id || payload.id;
    if (userId) {
      const user = await User.findOne({ user_id: userId }).lean();
      if (user) {
        return res.json({
          ok: true,
          user: {
            id: user.user_id,
            name: user.username,
            company_name: user.company_name,
            role: user.role || "user",
          },
        });
      }
    }

    return res.json({
      ok: true,
      user: {
        id: userId || "unknown",
        name: payload.username || payload.name || "User",
        company_name: payload.company_name,
        role: payload.role || "user",
      },
    });
  })
);

export default router;
