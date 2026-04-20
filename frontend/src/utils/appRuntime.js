export function resolveApiBase() {
  const configuredBase = import.meta.env.VITE_API_BASE_URL;
  if (configuredBase) {
    return configuredBase.replace(/\/$/, "");
  }
  const devPorts = new Set(["5173", "5174", "5175"]);
  if (typeof window !== "undefined" && devPorts.has(window.location.port)) {
    return "http://127.0.0.1:8000";
  }
  return "";
}

export function routeFromHash() {
  return typeof window !== "undefined" && window.location.hash === "#/admin" ? "admin" : "chat";
}

export function createSessionId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `session-${Date.now()}`;
}
