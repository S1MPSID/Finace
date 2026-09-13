export function formatXaiStats(xai: any | undefined): string {
  if (!xai || typeof xai !== "object" || Object.keys(xai).length === 0) {
    return "(none)";
  }

  const lines: string[] = [];
  const observed = xai.observed_score ?? xai.surrogate_score;
  const risk = xai.observed_risk;
  if (observed !== undefined && observed !== null) {
    lines.push(`observed_score=${observed}${risk ? `; observed_risk=${risk}` : ""}`);
  }
  if (xai.method) lines.push(`method=${xai.method}`);

  if (xai.top_drivers?.length) {
    lines.push("TOP_DRIVERS:");
    for (const d of xai.top_drivers) lines.push(`- ${d}`);
  }

  appendFeatureBlock(lines, "SHAP_FEATURES (label | shap_value | active):", xai.shap?.features, 12, "shap_value");
  appendFeatureBlock(lines, "LIME_FEATURES (label | weight | active):", xai.lime?.features, 8, "weight");

  const fv = xai.feature_values;
  if (fv && typeof fv === "object") {
    lines.push("FEATURE_VALUES:");
    for (const [k, v] of Object.entries(fv).slice(0, 16)) {
      lines.push(`- ${k}=${v}`);
    }
  }

  return lines.join("\n") || "(none)";
}

function appendFeatureBlock(
  lines: string[],
  header: string,
  features: any[] | undefined,
  limit: number,
  valueKey: string
) {
  if (!Array.isArray(features) || !features.length) return;
  lines.push(header);
  for (const f of features.slice(0, limit)) {
    const label = f.label || f.feature || "feature";
    const val = f[valueKey] ?? f.coefficient ?? f.value ?? 0;
    const active = f.active === undefined ? "?" : f.active ? "yes" : "no";
    lines.push(`- ${label} | ${val} | active=${active}`);
  }
}
