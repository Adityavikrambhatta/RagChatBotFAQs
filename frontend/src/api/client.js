import { resolveApiBase } from "../utils/appRuntime";

export const API_BASE = resolveApiBase();

export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
}
