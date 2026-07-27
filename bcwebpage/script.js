const state = {
  apiBase: localStorage.getItem('panel_api_base') || '',
  adminKey: localStorage.getItem('panel_admin_key') || '',
  users: [],
  stats: null,
  broadcastTimer: null,
  syncTimer: null,
  log: [],
  chat: [],
};

const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function pushLog(message) {
  state.log.unshift({ message, time: new Date().toLocaleTimeString() });
  state.log = state.log.slice(0, 5);
  $('#activityLog').innerHTML = state.log
    .map((item) => `<div class="log-item">[${escapeHtml(item.time)}] ${escapeHtml(item.message)}</div>`)
    .join('');
}

function pushChat(role, message) {
  state.chat.push({ role, message, time: new Date().toLocaleTimeString() });
  state.chat = state.chat.slice(-60);
  $('#chatWindow').innerHTML = state.chat
    .map((item) => `
      <div class="chat-message ${escapeHtml(item.role)}">
        <div class="chat-meta">${escapeHtml(item.role === 'user' ? 'You' : 'Assistant')} · ${escapeHtml(item.time)}</div>
        <div class="chat-bubble">${escapeHtml(item.message)}</div>
      </div>
    `)
    .join('');
  $('#chatWindow').scrollTop = $('#chatWindow').scrollHeight;
}

function setStatus(message, isError = false) {
  const status = $('#actionStatus');
  status.textContent = message;
  status.style.color = isError ? '#ff9494' : 'var(--muted)';
}

function setConnectionStatus(message, isError = false) {
  const status = $('#connectionStatus');
  status.textContent = message;
  status.style.color = isError ? '#ff9494' : 'var(--muted)';
}

function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.style.borderColor = isError ? 'rgba(255, 107, 107, 0.4)' : 'rgba(115, 210, 222, 0.25)';
  toast.classList.add('show');
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => toast.classList.remove('show'), 2400);
}

function getStatsLine(stats = state.stats) {
  if (!stats) return 'No stats loaded yet.';
  return `Users: ${stats.total_users ?? 0}, pending: ${stats.pending_users ?? 0}, verified: ${stats.verified_users ?? 0}, claims: ${stats.total_claims ?? 0}`;
}

function findUidInText(text) {
  const matches = text.match(/\b\d{4,}\b/g);
  return matches ? matches[0] : '';
}

function parseChatIntent(text) {
  const normalized = text.trim().toLowerCase();
  const uid = findUidInText(text);

  if (!normalized) {
    return { type: 'unknown' };
  }

  if (/^(hi|hello|hey|menu|help|start|panel)$/.test(normalized)) {
    return { type: 'menu' };
  }

  if (normalized.includes('show stats') || normalized.includes('stats') || normalized.includes('how many users')) {
    return { type: 'stats' };
  }

  if (normalized.includes('show users') || normalized.includes('list users') || normalized.includes('users')) {
    return { type: 'users' };
  }

  if (normalized.includes('sync') || normalized.includes('refresh all') || normalized.includes('update all users')) {
    return { type: 'sync' };
  }

  if (normalized.includes('broadcast') || normalized.includes('send to everyone') || normalized.includes('announce')) {
    const textAfter = text.replace(/^(broadcast|announce)\s*/i, '').trim();
    return { type: 'broadcast', message: textAfter || text };
  }

  if ((normalized.includes('mark') && normalized.includes('done')) || normalized.includes('complete user')) {
    return { type: 'markdone', uid };
  }

  if (normalized.includes('refresh') || normalized.includes('resync') || normalized.includes('update user')) {
    return { type: 'refresh', uid };
  }

  if (normalized.includes('send message') || normalized.includes('message to') || normalized.includes('dm') || normalized.includes('direct message')) {
    const message = text
      .replace(/^(send message|message to|dm|direct message)\s*/i, '')
      .trim();
    return { type: 'sendmsg', uid, message };
  }

  if (uid && normalized.split(/\s+/).length <= 3) {
    return { type: 'select', uid };
  }

  return { type: 'search', query: text };
}

async function runChatAction(intent, rawText) {
  if (!state.apiBase || !state.adminKey) {
    return 'Connect the panel URL and admin key first.';
  }

  if (intent.type === 'menu') {
    return 'Say things like “show stats”, “refresh 123456”, “broadcast hello”, or “send message to 123456 hello”.';
  }

  if (intent.type === 'stats') {
    await loadDashboard();
    return getStatsLine();
  }

  if (intent.type === 'users') {
    await loadDashboard();
    return `Loaded ${state.users.length} users.`;
  }

  if (intent.type === 'sync') {
    await startSync();
    return 'Sync started.';
  }

  if (intent.type === 'broadcast') {
    $('#broadcastText').value = intent.message;
    await startBroadcast();
    return 'Broadcast started.';
  }

  if (intent.type === 'refresh') {
    if (!intent.uid) return 'Tell me which UID to refresh, like “refresh 123456”.';
    $('#targetUid').value = intent.uid;
    await refreshUser(intent.uid);
    return `Refreshed ${intent.uid}.`;
  }

  if (intent.type === 'markdone') {
    if (!intent.uid) return 'Tell me which UID to mark done, like “mark 123456 done”.';
    $('#targetUid').value = intent.uid;
    await markDone(intent.uid);
    return `Marked ${intent.uid} done.`;
  }

  if (intent.type === 'sendmsg') {
    if (!intent.uid) return 'Tell me which UID to message, like “send message to 123456 hello”.';
    if (!intent.message) return 'Tell me the message text too.';
    $('#targetUid').value = intent.uid;
    $('#directMessage').value = intent.message;
    await sendMessage();
    return `Message sent to ${intent.uid}.`;
  }

  if (intent.type === 'select') {
    $('#targetUid').value = intent.uid;
    return `Selected UID ${intent.uid}.`; 
  }

  if (intent.type === 'search') {
    $('#searchInput').value = intent.query;
    renderUsers(filteredUsers());
    return `Showing users matching “${intent.query}”.`;
  }

  return `I could not understand “${rawText}”. Try “show stats”, “refresh 123456”, or “broadcast hello”.`;
}

async function sendChatMessage(rawText) {
  const text = rawText.trim();
  if (!text) {
    return;
  }

  pushChat('user', text);
  const intent = parseChatIntent(text);

  try {
    const reply = await runChatAction(intent, text);
    pushChat('bot', reply);
    setActionFromChat(reply);
  } catch (error) {
    const message = error.message || 'Command failed.';
    pushChat('bot', message);
    showToast(message, true);
    setStatus(message, true);
  }
}

function setActionFromChat(message) {
  setStatus(message);
  setConnectionStatus(state.apiBase && state.adminKey ? 'Connected' : 'Ready to connect');
}

function saveConfig() {
  state.apiBase = $('#apiBase').value.trim().replace(/\/$/, '');
  state.adminKey = $('#adminKey').value.trim();
  localStorage.setItem('panel_api_base', state.apiBase);
  localStorage.setItem('panel_admin_key', state.adminKey);
}

function apiUrl(path) {
  if (!state.apiBase) {
    throw new Error('Set the admin panel URL first.');
  }
  return `${state.apiBase}${path}`;
}

async function api(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Key': state.adminKey,
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}

function renderMetrics(stats) {
  const cards = [
    ['Total users', stats?.total_users ?? 0, 'All imported users'],
    ['Pending', stats?.pending_users ?? 0, 'Waiting for review'],
    ['Verified', stats?.verified_users ?? 0, 'Eligible accounts'],
    ['Claims', stats?.total_claims ?? 0, 'Claim activity'],
  ];
  $('#metricsGrid').innerHTML = cards
    .map(
      ([label, value, hint]) => `
        <article class="panel metric">
          <div class="label">${escapeHtml(label)}</div>
          <div class="value">${escapeHtml(value)}</div>
          <div class="hint">${escapeHtml(hint)}</div>
        </article>
      `
    )
    .join('');
}

function filteredUsers() {
  const query = $('#searchInput').value.trim().toLowerCase();
  if (!query) return state.users;
  return state.users.filter((user) => {
    const haystack = [user.bc_uid, user.bc_username, user.username, user.telegram_username, user.level_name, user.status]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(query);
  });
}

function renderUsers(users) {
  $('#userCount').textContent = `${users.length} user${users.length === 1 ? '' : 's'} shown`;
  if (!users.length) {
    $('#usersBody').innerHTML = '<tr><td colspan="5" class="empty-state">No users match your search.</td></tr>';
    return;
  }

  $('#usersBody').innerHTML = users
    .map((user) => {
      const name = user.bc_username || user.telegram_username || user.username || 'Unknown';
      const status = user.status || (user.marked_done ? 'done' : 'active');
      return `
        <tr>
          <td><strong>${escapeHtml(user.bc_uid || 'N/A')}</strong></td>
          <td>
            <div>${escapeHtml(name)}</div>
            <div class="filter-hint">${escapeHtml(user.telegram_username || user.telegram_id || '')}</div>
          </td>
          <td>${escapeHtml(user.level_name || user.level || 'N/A')}</td>
          <td>${escapeHtml(status)}</td>
          <td>
            <div class="row-actions">
              <button class="select" data-action="select" data-uid="${escapeHtml(user.bc_uid || '')}">Select</button>
              <button class="refresh" data-action="refresh" data-uid="${escapeHtml(user.bc_uid || '')}">Refresh</button>
              <button class="done" data-action="done" data-uid="${escapeHtml(user.bc_uid || '')}">Done</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join('');
}

async function loadDashboard() {
  saveConfig();
  if (!state.apiBase || !state.adminKey) {
    setConnectionStatus('Add the panel URL and admin key to connect.', true);
    setStatus('Waiting for connection');
    return;
  }

  setConnectionStatus('Connecting...');
  const [statsData, usersData] = await Promise.all([
    api('/api/stats'),
    api('/api/users'),
  ]);

  state.stats = statsData.stats;
  state.users = usersData.users || [];
  renderMetrics(state.stats);
  renderUsers(filteredUsers());
  setConnectionStatus('Connected');
  setStatus(`Loaded ${state.users.length} users`);
  pushLog(`Connected to ${state.apiBase}`);
}

async function refreshAll() {
  setStatus('Refreshing data...');
  await loadDashboard();
}

async function refreshUser(uid) {
  if (!uid) {
    showToast('Select a UID first', true);
    return;
  }
  setStatus(`Refreshing ${uid}...`);
  const data = await api('/api/refresh-user', {
    method: 'POST',
    body: JSON.stringify({ bc_uid: uid }),
  });
  const index = state.users.findIndex((user) => String(user.bc_uid) === String(uid));
  if (index >= 0) state.users[index] = data.user;
  else state.users.unshift(data.user);
  renderUsers(filteredUsers());
  showToast(`Refreshed ${uid}`);
  pushLog(`Refreshed ${uid}`);
  setStatus(`Refreshed ${data.user.bc_username || uid}`);
}

async function markDone(uid = $('#targetUid').value.trim()) {
  if (!uid) {
    showToast('Enter a UID first', true);
    return;
  }
  setStatus(`Marking ${uid} done...`);
  const data = await api('/api/mark-done', {
    method: 'POST',
    body: JSON.stringify({ bc_uid: uid }),
  });
  showToast(data.notified ? `Marked ${uid} and notified` : `Marked ${uid}`);
  pushLog(`Marked done: ${uid}`);
  setStatus(`Done for ${uid}`);
  await loadDashboard();
}

async function sendMessage() {
  const uid = $('#targetUid').value.trim();
  const text = $('#directMessage').value.trim();
  if (!uid || !text) {
    showToast('Add a UID and message first', true);
    return;
  }
  setStatus(`Sending message to ${uid}...`);
  await api('/api/send-message', {
    method: 'POST',
    body: JSON.stringify({ bc_uid: uid, text }),
  });
  $('#directMessage').value = '';
  showToast(`Message sent to ${uid}`);
  pushLog(`Message sent to ${uid}`);
  setStatus(`Message sent to ${uid}`);
}

function renderBroadcastJob(job) {
  if (!job) {
    $('#jobFeed').textContent = 'No job running yet.';
    return;
  }
  const latest = (job.latest_batch || []).slice(-5).map((item) => `• ${item}`).join('\n') || 'Waiting for updates...';
  $('#jobFeed').textContent = [
    `Job: ${job.id}`,
    `Status: ${job.status}`,
    `Sent: ${job.sent}/${job.total}`,
    `Failed: ${job.failed}`,
    '',
    'Latest batch:',
    latest,
  ].join('\n');
}

async function pollBroadcast(jobId) {
  window.clearInterval(state.broadcastTimer);
  state.broadcastTimer = window.setInterval(async () => {
    try {
      const data = await api(`/api/broadcast/${jobId}`);
      renderBroadcastJob(data.job);
      if (data.job.status === 'complete') {
        window.clearInterval(state.broadcastTimer);
        showToast('Broadcast complete');
        pushLog(`Broadcast ${jobId} complete`);
        await loadDashboard();
      }
    } catch (error) {
      window.clearInterval(state.broadcastTimer);
      showToast(error.message, true);
      setStatus(error.message, true);
    }
  }, 1800);
}

async function startBroadcast() {
  const text = $('#broadcastText').value.trim();
  if (!text) {
    showToast('Broadcast message is required', true);
    return;
  }
  setStatus('Starting broadcast...');
  const data = await api('/api/broadcast', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
  renderBroadcastJob(data.job);
  showToast(`Broadcast ${data.job.id} started`);
  pushLog(`Broadcast started: ${data.job.id}`);
  setStatus(`Broadcast ${data.job.id} started`);
  await pollBroadcast(data.job.id);
}

async function startSync() {
  setStatus('Starting sync...');
  const data = await api('/api/sync-users', {
    method: 'POST',
    body: JSON.stringify({}),
  });
  setStatus(`Sync ${data.job.id} started`);
  pushLog(`Sync started: ${data.job.id}`);
  $('#jobFeed').textContent = `Sync job ${data.job.id} started...`;
  window.clearInterval(state.syncTimer);
  state.syncTimer = window.setInterval(async () => {
    try {
      const status = await api(`/api/sync-users/${data.job.id}`);
      const job = status.job;
      $('#jobFeed').textContent = [
        `Sync Job: ${job.id}`,
        `Status: ${job.status}`,
        `Synced: ${job.synced}/${job.total}`,
        `Failed: ${job.failed}`,
        '',
        'Latest refresh:',
        job.latest ? `${job.latest.bc_username || job.latest.bc_uid}: ${job.latest.level_name}` : 'Waiting for refresh...',
      ].join('\n');
      if (job.status === 'complete') {
        window.clearInterval(state.syncTimer);
        showToast('Sync complete');
        pushLog(`Sync ${job.id} complete`);
        await loadDashboard();
      }
    } catch (error) {
      window.clearInterval(state.syncTimer);
      showToast(error.message, true);
      setStatus(error.message, true);
    }
  }, 2200);
}

async function connect() {
  saveConfig();
  try {
    await loadDashboard();
    showToast('Connected');
  } catch (error) {
    setConnectionStatus(error.message, true);
    setStatus(error.message, true);
    showToast(error.message, true);
  }
}

function wireEvents() {
  $('#apiBase').value = state.apiBase;
  $('#adminKey').value = state.adminKey;

  $('#connectButton').addEventListener('click', connect);
  $('#saveButton').addEventListener('click', () => {
    saveConfig();
    setConnectionStatus('Settings saved locally');
    showToast('Settings saved');
  });
  $('#refreshButton').addEventListener('click', () => refreshAll().catch((error) => setStatus(error.message, true)));
  $('#searchButton').addEventListener('click', () => renderUsers(filteredUsers()));
  $('#searchInput').addEventListener('input', () => renderUsers(filteredUsers()));
  $('#sendButton').addEventListener('click', () => sendMessage().catch((error) => {
    setStatus(error.message, true);
    showToast(error.message, true);
  }));
  $('#markDoneButton').addEventListener('click', () => markDone().catch((error) => {
    setStatus(error.message, true);
    showToast(error.message, true);
  }));
  $('#broadcastButton').addEventListener('click', () => startBroadcast().catch((error) => {
    setStatus(error.message, true);
    showToast(error.message, true);
  }));
  $('#syncButton').addEventListener('click', () => startSync().catch((error) => {
    setStatus(error.message, true);
    showToast(error.message, true);
  }));
  $('#chatSendButton').addEventListener('click', () => sendChatMessage($('#chatInput').value).finally(() => {
    $('#chatInput').value = '';
    $('#chatInput').focus();
  }));
  $('#chatInput').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      $('#chatSendButton').click();
    }
  });
  $('#chatSuggestions').addEventListener('click', (event) => {
    const button = event.target.closest('button[data-chat-suggestion]');
    if (!button) return;
    $('#chatInput').value = button.dataset.chatSuggestion;
    $('#chatInput').focus();
  });
  $('#usersBody').addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const uid = button.dataset.uid;
    $('#targetUid').value = uid;
    if (button.dataset.action === 'select') {
      showToast(`Selected ${uid}`);
      pushLog(`Selected ${uid}`);
      return;
    }
    if (button.dataset.action === 'refresh') {
      await refreshUser(uid).catch((error) => {
        setStatus(error.message, true);
        showToast(error.message, true);
      });
      return;
    }
    if (button.dataset.action === 'done') {
      await markDone(uid).catch((error) => {
        setStatus(error.message, true);
        showToast(error.message, true);
      });
    }
  });
}

function bootstrap() {
  wireEvents();
  renderMetrics(null);
  renderUsers([]);
  setConnectionStatus('Ready to connect');
  setStatus('Enter the panel URL and admin key to start');
  pushChat('bot', 'Hello. I can understand common language. Try “show stats”, “refresh 123456”, “send message to 123456 hello”, “broadcast hello everyone”, or “sync all users”.');
  pushLog('Dashboard loaded');
}

bootstrap();
