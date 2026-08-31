import { state } from './state.js';

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'NETWORK_ERROR', details = [] } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, options = {}) {
  const { headers = {}, retry = 0, ...fetchOptions } = options;
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...(state.userId ? { 'X-User-ID': state.userId } : {}),
    ...headers,
  };

  try {
    const response = await fetch(state.apiBase + path, {
      ...fetchOptions,
      headers: requestHeaders,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(body?.error?.message || body?.detail || `HTTP ${response.status}`, {
        status: response.status,
        code: body?.error?.code || `HTTP_${response.status}`,
        details: body?.error?.details || [],
      });
    }
    return body;
  } catch (error) {
    if (retry > 0 && !(error instanceof ApiError && error.status < 500)) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      return request(path, { ...options, retry: retry - 1 });
    }
    if (error instanceof ApiError) throw error;
    throw new ApiError('서버에 연결할 수 없습니다. 잠시 후 다시 시도하세요.');
  }
}

export const api = {
  concepts: () => request('/concepts', { retry: 1 }),
  conceptTasks: (conceptId) => request(`/concepts/${conceptId}/tasks`, { retry: 1 }),
  task: (taskId) => request(`/tasks/${taskId}`, { retry: 1 }),
  hint: (taskId) => request(`/tasks/${taskId}/hint`, { method: 'POST' }),
  submitAttempt: (payload) => request('/attempts', { method: 'POST', body: JSON.stringify(payload) }),
  attempt: (id) => request(`/attempts/${id}`, { retry: 1 }),
  proficiency: (id) => request(`/users/${id}/proficiency`, { retry: 1 }),
  weakConcepts: (id) => request(`/users/${id}/weak-concepts`, { retry: 1 }),
  history: (id, limit = 20, offset = 0) => request(`/users/${id}/attempts?limit=${limit}&offset=${offset}`, { retry: 1 }),
  items: () => request('/items', { retry: 1 }),
  item: (id) => request(`/items/${id}`, { retry: 1 }),
  buy: (item_id, purchase_request_id) => request('/shop/buy', {
    method: 'POST',
    body: JSON.stringify({ item_id, purchase_request_id }),
  }),
  inventory: (id) => request(`/users/${id}/inventory`, { retry: 1 }),
  user: (id) => request(`/users/${id}`, { retry: 1 }),
  starter: (id) => request(`/users/${id}/cats/starter`, { method: 'POST' }),
  cats: (id) => request(`/users/${id}/cats`, { retry: 1 }),
  house: (id) => request(`/users/${id}/house`, { retry: 1 }),
  place: (id, item_id, position_data) => request(`/users/${id}/house/objects`, { method: 'POST', body: JSON.stringify({ item_id, position_data }) }),
  move: (id, placedId, position_data) => request(`/users/${id}/house/objects/${placedId}`, { method: 'PATCH', body: JSON.stringify({ position_data }) }),
  remove: (id, placedId) => request(`/users/${id}/house/objects/${placedId}`, { method: 'DELETE' }),
  surface: (id, type, item_id) => request(`/users/${id}/house/${type}`, { method: 'PUT', body: JSON.stringify({ item_id }) }),
  gachaInfo: () => request('/gacha', { retry: 1 }),
  gachaPull: (count, request_id) => request('/gacha/pull', { method: 'POST', body: JSON.stringify({ count, request_id }) }),
  gachaResult: (requestId) => request(`/gacha/results/${requestId}`, { retry: 1 }),
  rooms: () => request('/rooms', { retry: 1 }),
  room: (id) => request(`/rooms/${id}`, { retry: 1 }),
  createRoom: (title, max_participants) => request('/rooms', { method: 'POST', body: JSON.stringify({ title, max_participants }) }),
  joinRoom: (id) => request(`/rooms/${id}/join`, { method: 'POST' }),
  readyRoom: (id, is_ready) => request(`/rooms/${id}/ready`, { method: 'PATCH', body: JSON.stringify({ is_ready }) }),
  startRoom: (id) => request(`/rooms/${id}/start`, { method: 'POST' }),
  roomState: (id) => request(`/rooms/${id}/state`, { retry: 1 }),
};
