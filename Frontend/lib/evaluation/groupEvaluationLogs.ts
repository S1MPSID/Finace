/** Merge amendment + reference_added logs from the same save into one entry. */
export function groupEvaluationLogs(logs: any[]): any[] {
  const asc = [...(logs || [])].sort(
    (a, b) => new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
  );
  const merged: any[] = [];
  const skip = new Set<string>();

  const sameBatch = (a: any, b: any) =>
    a.actor_name === b.actor_name &&
    Math.abs(new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()) < 5000;

  for (let i = 0; i < asc.length; i++) {
    const cur = asc[i];
    if (skip.has(cur.log_id)) continue;

    const next = asc[i + 1];
    if (cur.action === "amendment" && next && !skip.has(next.log_id) && next.action === "reference_added" && sameBatch(cur, next)) {
      merged.push({ ...cur, reference: next.reference || cur.reference });
      skip.add(next.log_id);
      continue;
    }

    if (cur.action === "reference_added" && next && !skip.has(next.log_id) && next.action === "amendment" && sameBatch(cur, next)) {
      merged.push({ ...next, reference: cur.reference });
      skip.add(next.log_id);
      continue;
    }

    merged.push(cur);
  }

  return merged.sort(
    (a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  );
}
