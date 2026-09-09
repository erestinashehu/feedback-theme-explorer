const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json();
}

export const api = {
  ingestBulk: (entries) =>
    request("/feedback/bulk", {
      method: "POST",
      body: JSON.stringify({ entries }),
    }),
  listFeedback: (limit = 100) => request(`/feedback?limit=${limit}`),
  listThemes: () => request("/themes"),
  themeTrend: (themeId, granularity) =>
    request(`/themes/${themeId}/trend?granularity=${granularity}`),
  ask: (question, date_from, date_to, top_k = 8) =>
    request("/query", {
      method: "POST",
      body: JSON.stringify({ question, date_from, date_to, top_k }),
    }),
};