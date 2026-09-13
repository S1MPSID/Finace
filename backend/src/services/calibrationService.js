import { env } from "../config/env.js";
import { ChatSession } from "../models/ChatSession.js";
import { getJson } from "./httpClient.js";

export async function fetchCurrentCalibration() {
  return getJson(`${env.fastApiBaseUrl}/calibration/current`, {
    timeoutMs: env.fastApiTimeoutMs,
  });
}

export function calibrationFieldsFromApi(cal) {
  return {
    calibration_phi0_seed: cal.phi0_seed,
    calibration_phi0_live: cal.phi0_live,
    calibration_phi0_blended: cal.phi0_blended,
    calibration_frozen_at: new Date(),
  };
}

export function buildCalibrationFrozenPayload(session) {
  if (!session || session.calibration_phi0_blended == null) return null;
  return {
    phi0_seed: session.calibration_phi0_seed,
    phi0_live: session.calibration_phi0_live,
    phi0_blended: session.calibration_phi0_blended,
    frozen_at: session.calibration_frozen_at,
  };
}

export async function freezeCalibrationFields() {
  const cal = await fetchCurrentCalibration();
  return calibrationFieldsFromApi(cal);
}

/** Ensure session has frozen φ₀; returns payload for python-rag or null if no chat. */
export async function resolveCalibrationFrozenForChat(chatId, userId) {
  if (!chatId || !userId) return null;

  let session = await ChatSession.findOne({ session_id: chatId, user_id: userId }).lean();
  if (!session) return null;

  if (session.calibration_phi0_blended == null) {
    const fields = await freezeCalibrationFields();
    await ChatSession.updateOne({ session_id: chatId, user_id: userId }, { $set: fields });
    session = { ...session, ...fields };
  }

  return buildCalibrationFrozenPayload(session);
}
