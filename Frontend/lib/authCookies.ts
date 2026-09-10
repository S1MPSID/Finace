/** Auth lives in document.cookie only (DevTools → Application → Cookies). */

export const TOKEN_KEY = "finace_token";
export const USER_KEY = "finace_user";

function isBrowser() {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

function maxAgeSeconds(days: number) {
  return Math.max(60, Math.floor(days * 24 * 60 * 60));
}

export function setCookie(name: string, value: string, days = 7) {
  if (!isBrowser()) return;
  // Keep attributes simple — Max-Age alone is enough and avoids Expires comma parsing quirks
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds(days)}; SameSite=Lax`;
}

export function getCookie(name: string): string | null {
  if (!isBrowser()) return null;
  const parts = document.cookie ? document.cookie.split(/;\s*/) : [];
  const prefix = `${name}=`;
  for (const part of parts) {
    if (!part.startsWith(prefix)) continue;
    const raw = part.slice(prefix.length);
    try {
      return decodeURIComponent(raw);
    } catch {
      return raw;
    }
  }
  return null;
}

export function deleteCookie(name: string) {
  if (!isBrowser()) return;
  // Clear on current host with matching Path
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
  document.cookie = `${name}=; Path=/; Max-Age=0`;
}

function stripLegacyStorage() {
  try {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("finace_token");
    localStorage.removeItem("finace_user");
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
  } catch {
    /* ignore */
  }
}

export type AuthUser = {
  id: string;
  name: string;
  role: "admin" | "evaluator" | "user";
  company_name?: string;
  email?: string;
};

/** Decode JWT payload (no verify) for session restore. */
export function userFromToken(token: string): AuthUser | null {
  try {
    const segment = token.split(".")[1];
    if (!segment) return null;
    const b64 = segment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = b64 + "=".repeat((4 - (b64.length % 4)) % 4);
    const json = JSON.parse(atob(padded));
    if (json.exp && Number(json.exp) * 1000 < Date.now()) {
      return null; // expired
    }
    const role = (json.role || "user") as AuthUser["role"];
    return {
      id: String(json.user_id || json.evaluator_id || json.id || json.sub || "unknown"),
      name: String(json.username || json.name || json.email || "User"),
      role,
      company_name: json.company_name ? String(json.company_name) : undefined,
      email: json.email ? String(json.email) : undefined,
    };
  } catch {
    return null;
  }
}

export function setAuthCookies(token: string, user?: unknown, days = 7) {
  if (!token || !isBrowser()) return;
  setCookie(TOKEN_KEY, token, days);
  // Optional profile cookie (UI niceties); session restore uses JWT if this is missing
  const profile = user ?? userFromToken(token);
  if (profile != null) {
    setCookie(USER_KEY, JSON.stringify(profile), days);
  }
  stripLegacyStorage();
}

export function clearAuthCookies() {
  deleteCookie(TOKEN_KEY);
  deleteCookie(USER_KEY);
  stripLegacyStorage();
}

export function getAuthToken(): string | null {
  if (!isBrowser()) return null;

  const fromCookie = getCookie(TOKEN_KEY);
  if (fromCookie) return fromCookie;

  // Legacy cookie name some older builds used
  const legacyCookie = getCookie("token");
  if (legacyCookie) {
    const user = userFromToken(legacyCookie);
    setAuthCookies(legacyCookie, user);
    deleteCookie("token");
    return legacyCookie;
  }

  // One-time migrate from old localStorage sessions into cookies
  try {
    const legacy = localStorage.getItem("token");
    if (legacy) {
      let user: unknown = null;
      try {
        const raw = localStorage.getItem("user");
        user = raw ? JSON.parse(raw) : userFromToken(legacy);
      } catch {
        user = userFromToken(legacy);
      }
      setAuthCookies(legacy, user);
      return legacy;
    }
  } catch {
    /* ignore */
  }
  return null;
}

export function getAuthUser<T = AuthUser>(): T | null {
  const raw = getCookie(USER_KEY);
  if (raw) {
    try {
      return JSON.parse(raw) as T;
    } catch {
      /* fall through */
    }
  }

  const token = getAuthToken();
  if (token) {
    const fromJwt = userFromToken(token);
    if (fromJwt) return fromJwt as T;
  }
  return null;
}

export function hasValidSession(): boolean {
  const token = getAuthToken();
  if (!token) return false;
  return !!userFromToken(token);
}

export const AUTH_COOKIE_KEYS = { TOKEN_KEY, USER_KEY } as const;
