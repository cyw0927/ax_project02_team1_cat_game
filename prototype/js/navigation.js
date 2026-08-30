import { state, setUser } from './state.js';
import { api } from './api.js';
import { renderCats } from './cat.js';

const $ = (selector) => document.querySelector(selector);
const toast = $('#toast');
const log = $('#debugLog');
const demoCats = [
  { name: '주황 고양이', rarity: 'STARTER', asset: 'assets/cats/cat_1_orange_walk.webp' },
  { name: '검정 고양이', rarity: 'DEMO', asset: 'assets/cats/cat_2_black_walk.webp' },
  { name: '흰 고양이', rarity: 'DEMO', asset: 'assets/cats/cat_3_white_walk.webp' },
];
let toastTimer;
let pulling = false;
let learningLoadedForUser = null;

function message(text) {
  clearTimeout(toastTimer);
  toast.textContent = text;
  toast.classList.add('show');
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}

function debug(text) {
  log.textContent = `${new Date().toLocaleTimeString()} ${text}\n${log.textContent}`;
}

function setLearningStatus(text, tone = '') {
  const element = $('#attemptState');
  element.textContent = text;
  element.dataset.tone = tone;
}

function requireUser() {
  if (state.userId) return true;
  message('우측 아래 설정에서 개발용 사용자 UUID를 연결하세요.');
  setLearningStatus('사용자 연결 후 학습 데이터를 불러올 수 있습니다.', 'error');
  return false;
}

function go(id) {
  if (!document.getElementById(id)) id = 'home';
  document.querySelectorAll('.screen').forEach((screen) => {
    screen.classList.toggle('active', screen.id === id);
  });
  history.replaceState(null, '', `#${id}`);
  if (id === 'learn' && learningLoadedForUser !== state.userId) loadConcepts();
  if (id === 'shop') loadItems();
  if (id === 'house' && state.userId) loadHouse();
}

async function connect() {
  setUser($('#apiBase').value, $('#userId').value);
  learningLoadedForUser = null;
  if (!state.userId) {
    state.cats = [{ user_cat_id: 'local-starter', cat_id: 1, name: '주황 고양이', rarity: 'STARTER' }];
    renderCats(state.cats);
    debug('로컬 스타터 모드');
    return;
  }
  try {
    await api.starter(state.userId);
    state.cats = await api.cats(state.userId);
    const user = await api.user(state.userId);
    $('#balance').textContent = Number(user.soft_balance ?? user.balance ?? 0).toLocaleString();
    renderCats(state.cats);
    debug(`DB 고양이 ${state.cats.length}마리 로드`);
    message('사용자 데이터를 불러왔어요.');
    if ($('#learn').classList.contains('active')) loadConcepts();
  } catch (error) {
    debug(`연결 실패: ${error.code || ''} ${error.message}`);
    message('연결 실패 · Debug를 확인하세요.');
  }
}

function renderConcepts() {
  $('#conceptSelect').innerHTML = state.concepts.length
    ? state.concepts.map((concept) => `<option value="${concept.id}">${concept.name}</option>`).join('')
    : '<option value="">등록된 개념이 없습니다</option>';
}

async function loadConcepts() {
  if (!requireUser()) return;
  const button = $('#loadConcepts');
  button.disabled = true;
  $('#conceptSelect').innerHTML = '<option>개념을 불러오는 중…</option>';
  try {
    state.concepts = await api.concepts();
    renderConcepts();
    learningLoadedForUser = state.userId;
    debug(`GET /concepts · ${state.concepts.length}개`);
    if (state.concepts.length) await loadTasks();
    else {
      state.tasks = [];
      renderTasks();
      $('#taskInfo').textContent = '아직 등록된 학습 개념이 없습니다.';
    }
  } catch (error) {
    $('#conceptSelect').innerHTML = '<option value="">개념 조회 실패</option>';
    setLearningStatus(`${error.message} 다시 시도해 주세요.`, 'error');
    debug(`GET /concepts 실패 · ${error.code} · ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

function renderTasks() {
  $('#taskSelect').innerHTML = state.tasks.length
    ? state.tasks.map((task) => `<option value="${task.id}" ${task.is_locked ? 'disabled' : ''}>${task.is_locked ? '🔒 ' : ''}${task.title} · ${task.difficulty}</option>`).join('')
    : '<option value="">풀 수 있는 문제가 없습니다</option>';
}

async function loadTasks() {
  if (!requireUser()) return;
  const conceptId = $('#conceptSelect').value;
  if (!conceptId) return;
  $('#taskSelect').innerHTML = '<option>문제를 불러오는 중…</option>';
  clearTask();
  try {
    state.tasks = await api.conceptTasks(conceptId);
    renderTasks();
    debug(`GET /concepts/${conceptId}/tasks · ${state.tasks.length}개`);
    const firstUnlocked = state.tasks.find((task) => !task.is_locked);
    if (firstUnlocked) {
      $('#taskSelect').value = firstUnlocked.id;
      await loadTaskDetail();
    } else {
      $('#taskInfo').textContent = state.tasks.length
        ? '현재 숙련도에서는 모든 문제가 잠겨 있습니다.'
        : '이 개념에는 활성 문제가 없습니다.';
    }
  } catch (error) {
    state.tasks = [];
    renderTasks();
    setLearningStatus(`${error.message} 문제 목록을 다시 불러오세요.`, 'error');
    debug(`문제 목록 실패 · ${error.code} · ${error.message}`);
  }
}

function clearTask() {
  state.currentTask = null;
  state.usedHint = false;
  state.lastAttemptId = null;
  $('#taskTitle').textContent = '문제를 선택하세요';
  $('#taskDescription').textContent = '문제 상세 설명이 여기에 표시됩니다.';
  $('#taskInfo').textContent = '';
  $('#codeEditor').value = '';
  $('#hintText').hidden = true;
  $('#useHint').disabled = true;
  $('#submitAttempt').disabled = true;
  $('#retryAttempt').hidden = true;
  setLearningStatus('문제를 선택하면 코드를 작성할 수 있습니다.');
}

async function loadTaskDetail() {
  const taskId = $('#taskSelect').value;
  const summary = state.tasks.find((task) => task.id === taskId);
  if (!taskId || summary?.is_locked) return clearTask();
  $('#taskInfo').textContent = '문제 상세를 불러오는 중…';
  try {
    state.currentTask = await api.task(taskId);
    state.usedHint = false;
    state.lastAttemptId = null;
    $('#taskTitle').textContent = state.currentTask.title;
    $('#taskDescription').textContent = state.currentTask.description;
    $('#taskInfo').textContent = `${state.currentTask.type} · 난이도 ${state.currentTask.difficulty}`;
    $('#codeEditor').value = state.currentTask.template_code || '';
    $('#hintText').hidden = true;
    $('#useHint').disabled = false;
    $('#submitAttempt').disabled = false;
    $('#retryAttempt').hidden = true;
    setLearningStatus('코드를 작성하고 제출해 보세요.');
    debug(`GET /tasks/${taskId}`);
  } catch (error) {
    clearTask();
    setLearningStatus(`${error.message} 문제를 다시 선택하세요.`, 'error');
    debug(`문제 상세 실패 · ${error.code} · ${error.message}`);
  }
}

async function useHint() {
  if (!state.currentTask) return;
  const button = $('#useHint');
  button.disabled = true;
  try {
    const result = await api.hint(state.currentTask.id);
    state.usedHint = result.used_hint;
    $('#hintText').textContent = `💡 ${result.hint_text}`;
    $('#hintText').hidden = false;
    message('힌트를 사용하면 보상이 절반으로 줄어요.');
    debug(`POST /tasks/${state.currentTask.id}/hint`);
  } catch (error) {
    button.disabled = false;
    message(`힌트 조회 실패: ${error.message}`);
    debug(`힌트 실패 · ${error.code} · ${error.message}`);
  }
}

async function refreshLearningRewards() {
  try {
    const [user, proficiency] = await Promise.all([
      api.user(state.userId),
      api.proficiency(state.userId),
    ]);
    $('#balance').textContent = Number(user.soft_balance ?? user.balance ?? 0).toLocaleString();
    const current = proficiency.find((row) => row.concept_id === state.currentTask?.concept_id);
    $('#proficiencyState').textContent = current
      ? `${current.concept_name} 숙련도 ${current.proficiency_level} / 100`
      : '숙련도 정보를 불러왔습니다.';
  } catch (error) {
    debug(`보상 화면 갱신 실패 · ${error.code} · ${error.message}`);
  }
}

async function pollAttempt(attemptId) {
  state.lastAttemptId = attemptId;
  $('#retryAttempt').hidden = true;
  for (let count = 0; count < 16; count += 1) {
    const result = await api.attempt(attemptId);
    if (result.status === 'SUCCESS') {
      setLearningStatus(
        result.is_correct ? '정답입니다! 보상과 숙련도를 확인하세요. 🎉' : '아쉽지만 오답입니다. 코드를 고쳐 다시 제출해 보세요.',
        result.is_correct ? 'success' : 'wrong',
      );
      await refreshLearningRewards();
      return result;
    }
    if (result.status === 'FAILED') {
      setLearningStatus('채점 처리에 실패했습니다. 잠시 후 다시 제출해 주세요.', 'error');
      $('#retryAttempt').hidden = false;
      return result;
    }
    setLearningStatus(result.status === 'RUNNING' ? '코드를 실행하고 있어요…' : '채점 순서를 기다리고 있어요…', 'loading');
    await new Promise((resolve) => setTimeout(resolve, 750));
  }
  setLearningStatus('채점이 평소보다 오래 걸리고 있습니다. 결과 확인을 다시 눌러 주세요.', 'loading');
  $('#retryAttempt').hidden = false;
  return null;
}

async function submit() {
  if (!requireUser() || !state.currentTask) return;
  const code = $('#codeEditor').value;
  if (!code.trim()) return message('코드를 입력해 주세요.');
  const button = $('#submitAttempt');
  button.disabled = true;
  $('#useHint').disabled = true;
  setLearningStatus('제출을 접수하고 있어요…', 'loading');
  try {
    const result = await api.submitAttempt({
      task_id: state.currentTask.id,
      context_type: 'LEARNING',
      submitted_code: code,
      used_hint: state.usedHint,
    });
    debug(`POST /attempts · ${result.status}`);
    await pollAttempt(result.attempt_id);
  } catch (error) {
    setLearningStatus(`${error.message} 다시 시도해 주세요.`, 'error');
    $('#retryAttempt').hidden = !state.lastAttemptId;
    debug(`제출/채점 실패 · ${error.code} · ${error.message}`);
  } finally {
    button.disabled = false;
    $('#useHint').disabled = state.usedHint;
  }
}

async function retryAttemptResult() {
  if (!state.lastAttemptId) return submit();
  const button = $('#retryAttempt');
  button.disabled = true;
  try {
    await pollAttempt(state.lastAttemptId);
  } catch (error) {
    setLearningStatus(`${error.message} 결과 확인을 다시 시도해 주세요.`, 'error');
    debug(`결과 재조회 실패 · ${error.code} · ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

async function loadItems() {
  try {
    const [items, inventory] = await Promise.all([
      api.items(),
      state.userId ? api.inventory(state.userId) : Promise.resolve([]),
    ]);
    state.inventory = inventory;
    const quantities = new Map(inventory.map((row) => [row.item_id, row.quantity]));
    $('#shopItems').innerHTML = items.map((item) => {
      const quantity = quantities.get(item.id) || 0;
      return `<article class="item"><small class="surface">${item.category}</small><b>${item.name}</b><span>🪙 ${Number(item.price).toLocaleString()}</span><small>보유 ${quantity}개</small><button class="primary" data-buy="${item.id}">구매</button></article>`;
    }).join('') || '<p>등록된 상품이 없습니다.</p>';
    debug(`GET /items · ${items.length}개`);
  } catch (error) {
    $('#shopItems').innerHTML = '<p>FastAPI를 실행하면 실제 상품이 표시됩니다.</p>';
    debug(error.message);
  }
}

async function buy(button) {
  if (!state.userId) return message('구매하려면 사용자 UUID를 연결하세요.');
  const itemId = Number(button.dataset.buy);
  const requestId = state.pendingPurchases[itemId] || crypto.randomUUID();
  state.pendingPurchases[itemId] = requestId;
  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = '구매 처리 중…';
  try {
    const result = await api.buy(itemId, requestId);
    delete state.pendingPurchases[itemId];
    $('#balance').textContent = Number(result.current_soft_balance).toLocaleString();
    const quantityLabel = button.parentElement.querySelector('small:last-of-type');
    if (quantityLabel) quantityLabel.textContent = `보유 ${result.quantity}개`;
    message(`${result.item_name} ${result.replayed ? '구매 결과 확인' : '구매 완료'}`);
    debug(`POST /shop/buy · item ${itemId}`);
  } catch (error) {
    if (error.status > 0 && error.status < 500) delete state.pendingPurchases[itemId];
    message(`구매 실패: ${error.message}`);
    debug(`구매 실패 · ${error.code} · ${error.message}`);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

async function loadHouse() {
  if (!state.userId) return message('로컬 모드에서는 기본 하우스를 사용합니다.');
  try {
    state.house = await api.house(state.userId);
    $('#houseStatus').textContent = `하우스 Lv.${state.house.house_level} · 배치 ${state.house.placed_objects.length}개`;
    $('#placedItems').innerHTML = state.house.placed_objects.map((object) => `<div class="placed">${object.name} <small>${JSON.stringify(object.position_data)}</small></div>`).join('') || '<p>배치된 가구가 없습니다.</p>';
    debug('GET /users/{id}/house');
  } catch (error) {
    message('하우스 조회 실패');
    debug(error.message);
  }
}

async function demoPull() {
  if (pulling) return;
  pulling = true;
  const button = $('#demoPull');
  const machine = $('#gachaMachine');
  const result = $('#gachaResult');
  button.disabled = true;
  result.hidden = true;
  machine.classList.add('pulling');
  $('#gachaMessage').textContent = '새 친구가 오는 중…';
  await new Promise((resolve) => setTimeout(resolve, 1200));
  const cat = demoCats[Math.floor(Math.random() * demoCats.length)];
  $('#gachaCat').src = cat.asset;
  $('#gachaCat').alt = cat.name;
  $('#gachaName').textContent = cat.name;
  $('#gachaRarity').textContent = cat.rarity;
  result.hidden = false;
  machine.classList.remove('pulling');
  $('#gachaMessage').textContent = '연출 미리보기 결과입니다. 실제 보유 목록에는 추가되지 않았어요.';
  button.textContent = 'DEMO 다시 보기';
  button.disabled = false;
  pulling = false;
  debug(`가챠 DEMO 결과 · ${cat.name} · 저장 없음`);
}

document.addEventListener('click', (event) => {
  const nav = event.target.closest('[data-go]');
  if (nav) return go(nav.dataset.go);
  const demo = event.target.closest('[data-demo]');
  if (demo) return message('DEMO 흐름입니다 · 실제 재화는 변하지 않아요.');
  const product = event.target.closest('[data-buy]');
  if (product) return buy(product);
});
addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !$('#debugPanel').open) go('home');
});
$('#debugToggle').onclick = () => $('#debugPanel').showModal();
$('#connectUser').onclick = connect;
$('#disconnectUser').onclick = () => { $('#userId').value = ''; connect(); };
$('#loadConcepts').onclick = loadConcepts;
$('#conceptSelect').onchange = loadTasks;
$('#taskSelect').onchange = loadTaskDetail;
$('#useHint').onclick = useHint;
$('#submitAttempt').onclick = submit;
$('#retryAttempt').onclick = retryAttemptResult;
$('#loadItems').onclick = loadItems;
$('#loadHouse').onclick = loadHouse;
$('#demoPull').onclick = demoPull;
$('#apiBase').value = state.apiBase;
$('#userId').value = state.userId;
renderCats(state.cats);
if (state.userId) connect();
const hash = location.hash.slice(1);
if (hash) go(hash);
