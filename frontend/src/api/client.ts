/** Typed REST client for the Maestro API. */

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// Planner API
export const planner = {
  createSession: (data: { project_name?: string; project_description?: string; intake_mode?: string }) =>
    request<{ session_id: string }>('/planner/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  listSessions: () => request<Array<{ id: string; project_name: string; has_state: boolean }>>('/planner/sessions'),

  getSession: (id: string) => request<{ id: string; project_name: string; state: Record<string, unknown> }>(
    `/planner/sessions/${id}`,
  ),

  sendMessage: (id: string, content: string) =>
    request<{ state: Record<string, unknown> }>(`/planner/sessions/${id}/message`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  submitReview: (id: string, decision: string, feedback = '') =>
    request<{ state: Record<string, unknown> }>(`/planner/sessions/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ decision, feedback }),
    }),

  exportSession: (id: string, format: string) =>
    request<{ format: string; content: string }>(`/planner/sessions/${id}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
    }),

  deleteSession: (id: string) =>
    request<{ deleted: string }>(`/planner/sessions/${id}`, { method: 'DELETE' }),
};

// Runner API
export const runner = {
  getState: () => request<Record<string, unknown>>('/runner/state'),
  getIssue: (id: string) => request<Record<string, unknown>>(`/runner/issues/${id}`),
  refresh: () => request<{ status: string }>('/runner/refresh', { method: 'POST' }),
};
