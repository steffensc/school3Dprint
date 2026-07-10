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
