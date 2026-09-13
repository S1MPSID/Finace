import { HttpError } from "../utils/httpError.js";

function formatUpstreamError(payload, status) {
  const raw = typeof payload?.raw === "string" ? payload.raw : "";
  if (raw.includes("301 Moved Permanently") || raw.includes("Moved Permanently")) {
    return (
      "RAG URL uses HTTP but the server redirects to HTTPS (301). " +
      "Set FASTAPI_BASE_URL=https://finace.sambhav-mani-tripathi.tech"
    );
  }
  if (raw.includes("cloudflare") || raw.includes("cf-error")) {
    return (
      "Cloudflare returned an error reaching the RAG server (502/521). " +
      "For server-to-server calls: grey-cloud the finace DNS record (DNS only) " +
      "or set FASTAPI_BASE_URL to http://<EC2-PUBLIC-IP> (port 80 via nginx or :8000 direct)."
    );
  }
  if (Array.isArray(payload?.detail)) {
    const parts = payload.detail.map((item) => {
      const field = Array.isArray(item?.loc) ? item.loc.filter((p) => p !== "body").join(".") : "";
      const msg = item?.msg || item?.message || "validation failed";
      return field ? `${field}: ${msg}` : msg;
    });
    if (parts.length) return parts.join("; ");
  }
  if (typeof payload?.detail === "string") return payload.detail;
  if (payload?.message) return payload.message;
  return `Upstream request failed with status ${status}`;
}

export async function postJson(url, body, { timeoutMs = 30000 } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const text = await response.text();
    const payload = text ? safeJsonParse(text) : null;

    if (!response.ok) {
      throw new HttpError(
        response.status >= 500 ? 502 : response.status,
        "upstream_error",
        formatUpstreamError(payload, response.status),
        payload
      );
    }

    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new HttpError(504, "upstream_timeout", "Upstream request timed out");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}
