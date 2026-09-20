let csrfToken = null;

export async function resetCsrf() {
  csrfToken = null;
}

async function ensureCsrf() {
  if (csrfToken) return;
  const response = await fetch("/api/auth/csrf", {
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error("Unable to prepare a secure session");
  }
  const data = await response.json();
  csrfToken = data.csrf_token;
}

export async function api(path, options = {}) {
  const method = options.method || "GET";
  const changing = !["GET", "HEAD"].includes(method.toUpperCase());

  if (changing) await ensureCsrf();

  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(changing ? { "X-CSRF-Token": csrfToken } : {}),
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}

export function post(path, payload = {}) {
  return api(path, { method: "POST", body: JSON.stringify(payload) });
}

export function patch(path, payload = {}) {
  return api(path, { method: "PATCH", body: JSON.stringify(payload) });
}