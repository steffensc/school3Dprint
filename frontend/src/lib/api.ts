import axios from "axios";

/**
 * Central API client. Cookies (the HTTP-only session cookie set by the
 * backend) are sent automatically via `withCredentials`; we deliberately
 * never store a token in localStorage (Section 15).
 */
export const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

const SAFE_METHODS = new Set(["get", "head", "options"]);

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

// Double-submit-cookie CSRF protection (Section 15): the backend sets a
// readable `schoolprint_csrf` cookie on login; we echo it back as a
// header on every state-changing request so the backend's
// `CSRFMiddleware` can verify the request actually came from our own
// origin's JavaScript (a cross-site attacker can't read the cookie).
api.interceptors.request.use((config) => {
  const method = (config.method ?? "get").toLowerCase();
  if (!SAFE_METHODS.has(method)) {
    const token = readCookie("schoolprint_csrf");
    if (token) {
      config.headers.set("X-CSRF-Token", token);
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail;
    if (typeof detail === "string") {
      error.message = detail;
    }
    return Promise.reject(error);
  },
);
