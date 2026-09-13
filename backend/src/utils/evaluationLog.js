import crypto from "crypto";

export function newLogId() {
  return `log_${crypto.randomBytes(4).toString("hex")}`;
}

/**
 * @param {object} params
 * @param {string} params.action
 * @param {object} params.actor
 * @param {string} [params.comment]
 * @param {Array<{field:string,old_value:unknown,new_value:unknown}>} [params.changes]
 * @param {object} [params.reference]
 */
export function buildEvaluationLogEntry({
  action,
  actor,
  comment = "",
  changes = [],
  reference = null,
}) {
  return {
    log_id: newLogId(),
    action,
    actor_id: actor.evaluator_id || actor.user_id || actor.id || "system",
    actor_name: actor.name || actor.email || "System",
    actor_role: actor.role || "evaluator",
    comment: String(comment || "").trim(),
    changes,
    reference: reference || undefined,
    created_at: new Date(),
  };
}

export function diffField(field, oldVal, newVal) {
  const o = oldVal ?? null;
  const n = newVal ?? null;
  if (JSON.stringify(o) === JSON.stringify(n)) return null;
  return { field, old_value: o, new_value: n };
}
