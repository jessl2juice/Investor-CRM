/**
 * BetterMind CRM - API Client
 * Token management and fetch wrapper for the REST API.
 */

const API = "/api";

export function getToken() { return localStorage.getItem("bm_token"); }
export function setToken(t) { if (t) localStorage.setItem("bm_token", t); else localStorage.removeItem("bm_token"); }

export async function api(path, opts = {}) {
  const token = getToken();
  const { headers: customHeaders, ...restOpts } = opts;
  const r = await fetch(`${API}${path}`, {
    ...restOpts,
    headers: { "Content-Type": "application/json", ...customHeaders, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (r.status === 401) { setToken(null); window.location.reload(); throw new Error("Unauthorized"); }
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}
