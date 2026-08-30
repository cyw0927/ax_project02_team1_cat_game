export const state = {
  apiBase: localStorage.getItem('catGameApiBase') || 'http://127.0.0.1:8000',
  userId: localStorage.getItem('catGameApiUserId') || '',
  cats: [{ user_cat_id: 'local-starter', cat_id: 1, name: '주황 고양이', rarity: 'STARTER' }],
  concepts: [],
  tasks: [],
  currentTask: null,
  usedHint: false,
  lastAttemptId: null,
  pendingPurchases: {},
  inventory: [],
  house: null,
  gachaInfo: null,
  pendingGachaRequest: null,
};

export function setUser(apiBase, userId) {
  state.apiBase = apiBase.replace(/\/$/, '');
  state.userId = userId.trim();
  localStorage.setItem('catGameApiBase', state.apiBase);
  if (state.userId) localStorage.setItem('catGameApiUserId', state.userId);
  else localStorage.removeItem('catGameApiUserId');
}
