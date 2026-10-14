/* imPress v2.2 UI layer: icons, the app shell (sidebar, top bar, banners),
 * toasts and notifications, live updates over Server-Sent Events, search.
 * Loaded after api.js and before app.js; pages call these helpers. */

// ── Icons (24×24 stroke icons, Lucide-style) ───────────────────────────
const ICONS = {
  layers: '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  school: '<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
  clipboard: '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  userCog: '<circle cx="10" cy="8" r="4"/><path d="M2 21a8 8 0 0 1 11-7.4"/><circle cx="18" cy="18" r="2.5"/><path d="M18 14v1.5M18 20.5V22M14 18h1.5M20.5 18H22"/>',
  userPlus: '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M19 8v6M16 11h6"/>',
  book: '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2Z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7Z"/>',
  radio: '<circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14"/>',
  cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  flask: '<path d="M9 2h6"/><path d="M10 2v6L4.5 18.5A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.8-2.5L14 8V2"/><path d="M7 15h10"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  help: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
  login: '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  filter: '<path d="M22 3H2l8 9.5V19l4 2v-8.5L22 3Z"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>', chevronRight: '<path d="m9 18 6-6-6-6"/>', chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>', check: '<path d="M20 6 9 17l-5-5"/>',
  checkCircle: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  xCircle: '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
  alert: '<path d="m10.3 3.9-8.4 14.5A2 2 0 0 0 3.6 21h16.8a2 2 0 0 0 1.7-2.6L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  wifi: '<path d="M5 12.6a10 10 0 0 1 14 0"/><path d="M8.5 16.1a5 5 0 0 1 7 0"/><path d="M2 8.8a15 15 0 0 1 20 0"/><path d="M12 20h.01"/>',
  wifiOff: '<path d="m2 2 20 20"/><path d="M8.5 16.4a5 5 0 0 1 7 0"/><path d="M5 12.9a10 10 0 0 1 5.2-2.8"/><path d="M12 20h.01"/>',
  refresh: '<path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
  play: '<path d="m6 4 14 8-14 8Z"/>', stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>', pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="m2 2 20 20"/><path d="M6.7 6.7C3.9 8.5 2 12 2 12s3.5 7 10 7c2 0 3.7-.6 5.2-1.6"/><path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-2.2 3.2"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
  shieldCheck: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  crown: '<path d="m2 18 2-11 5 4 3-6 3 6 5-4 2 11Z"/><path d="M4 21h16"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  pin: '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  chart: '<path d="M3 3v18h18"/><path d="M8 17V10M13 17V6M18 17v-4"/>',
  zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z"/>',
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  server: '<rect x="2" y="3" width="20" height="8" rx="2"/><rect x="2" y="13" width="20" height="8" rx="2"/><path d="M6 7h.01M6 17h.01"/>',
  router: '<rect x="2" y="13" width="20" height="8" rx="2"/><path d="M6 17h.01M10 17h.01"/><path d="M15 13V7"/><path d="M12 7a3 3 0 0 1 6 0"/>',
  hub: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>',
  module: '<rect x="5" y="2" width="14" height="20" rx="3"/><path d="M9 6h6M9 18h6"/><circle cx="12" cy="12" r="2"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>',
  fileCheck: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  more: '<circle cx="12" cy="5" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="19" r="1.4"/>',
  external: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  arrowLeft: '<path d="M19 12H5M12 19l-7-7 7-7"/>', arrowRight: '<path d="M5 12h14M12 5l7 7-7 7"/>',
  battery: '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2"/><path d="M6 11v2"/>',
  code: '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
  poll: '<path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="5"/><rect x="12" y="8" width="3" height="9"/><rect x="17" y="5" width="3" height="12"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  power: '<path d="M18.4 6.6a9 9 0 1 1-12.8 0"/><path d="M12 2v10"/>',
  key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>',
  sparkles: '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2Z"/><path d="M19 3v4M17 5h4"/>',
  table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>',
  save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
};

function icon(name, cls = '') {
  return `<svg class="ic ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
}

// ── Small components ──────────────────────────────────────────────────

function initials(name) {
  const parts = String(name || '?').replace(/^(Dr|Prof|Mr|Ms|Mrs)\.?\s+/i, '').trim().split(/\s+/);
  return ((parts[0] || '?')[0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
}

function avatar(name, size = '') {
  let h = 0;
  for (const ch of String(name || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return `<span class="avatar ${size} c${(h % 6) + 1}" aria-hidden="true">${escHtml(initials(name))}</span>`;
}

function statCard(label, value, sub = '', iconName = 'grid', tone = '') {
  return `<div class="stat-card"><span class="stat-icon ${tone}">${icon(iconName)}</span>
    <div class="stat-label">${escHtml(label)}</div><div class="stat-value">${value}</div>
    ${sub ? `<div class="stat-sub">${sub}</div>` : ''}</div>`;
}

function statusPill(kind, text) {
  return `<span class="status ${kind}">${escHtml(text)}</span>`;
}

function emptyState(title, text = '', iconName = 'info') {
  return `<div class="empty">${icon(iconName)}<b>${escHtml(title)}</b>${text ? `<div>${text}</div>` : ''}</div>`;
}

function pageHeader(title, sub = '', actions = '', eyebrow = '') {
  return `<div class="page-header"><div>${eyebrow ? `<div class="eyebrow">${escHtml(eyebrow)}</div>` : ''}
    <h1>${escHtml(title)}</h1>${sub ? `<div class="page-sub">${sub}</div>` : ''}</div>
    ${actions ? `<div class="page-actions">${actions}</div>` : ''}</div>`;
}

function timeAgo(epoch) {
  if (!epoch) return '—';
  const s = Math.max(0, (Date.now() - epoch) / 1000);
  if (s < 45) return 'just now';
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  if (s < 86400 * 14) return `${Math.round(s / 86400)} d ago`;
  return istFormat(epoch, { day: 'numeric', month: 'short', year: 'numeric' });
}

function todayLabel() {
  return istFormat(Date.now(), { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).toUpperCase();
}

// ── Toasts and notifications ──────────────────────────────────────────

const _notices = [];

function showToast(message, type = 'info', { keep = false } = {}) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
  const ico = { success: 'checkCircle', error: 'xCircle', warning: 'alert' }[type] || 'info';
  toast.innerHTML = `${icon(ico)}<div></div><button aria-label="Dismiss">${icon('x', 'sm')}</button>`;
  toast.querySelector('div').textContent = message;
  const close = () => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 250); };
  toast.querySelector('button').onclick = close;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  if (!keep) setTimeout(close, type === 'error' ? 7000 : 3500);
}

function addNotice(message, level = 'info') {
  _notices.unshift({ message, level, at: Date.now() });
  _notices.length = Math.min(_notices.length, 30);
  const dot = document.getElementById('bell-dot');
  if (dot) dot.classList.remove('hidden');
}

window.toggleNotices = function (ev) {
  ev?.stopPropagation();
  const box = document.getElementById('notice-pop');
  if (!box) return;
  if (!box.classList.contains('hidden')) { box.classList.add('hidden'); return; }
  document.getElementById('bell-dot')?.classList.add('hidden');
  box.querySelector('.popover-body').innerHTML = _notices.length
    ? _notices.map(n => `<div class="notice"><span class="feed-icon ${n.level === 'error' ? 'red' : n.level === 'warning' ? 'amber' : ''}" style="width:30px;height:30px">${icon(n.level === 'error' ? 'xCircle' : n.level === 'warning' ? 'alert' : 'info', 'sm')}</span>
        <div><div>${escHtml(n.message)}</div><time>${timeAgo(n.at)}</time></div></div>`).join('')
    : emptyState('No notifications', 'Alerts from the server appear here.', 'bell');
  box.classList.remove('hidden');
};
document.addEventListener('click', (e) => {
  const box = document.getElementById('notice-pop');
  if (box && !box.contains(e.target)) box.classList.add('hidden');
  const sr = document.getElementById('search-results');
  if (sr && !e.target.closest('.searchbox')) sr.classList.add('hidden');
});

// ── Theme ─────────────────────────────────────────────────────────────

window.toggleTheme = function () {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('impress_theme', next); } catch { /* storage unavailable */ }
  document.querySelectorAll('[data-theme-icon]').forEach(el => { el.innerHTML = icon(next === 'dark' ? 'sun' : 'moon'); });
};

function themeIcon() {
  return icon(document.documentElement.getAttribute('data-theme') === 'dark' ? 'sun' : 'moon');
}

// ── System state: debug-mode banner, database status ──────────────────

const System = { testMode: false, db: 'ok', loaded: false };

async function loadSystemStatus() {
  try {
    const r = await fetch('/api/system/status', { headers: { 'X-Impress-Background': '1' } });
    if (r.ok) Object.assign(System, await r.json(), { loaded: true });
  } catch { /* offline: keep the last state */ }
  renderBanners();
}

function renderBanners() {
  let el = document.getElementById('sys-banners');
  if (!el) {
    el = document.createElement('div');
    el.id = 'sys-banners';
    document.body.prepend(el);
  }
  const parts = [];
  if (System.test_mode || System.testMode) {
    parts.push(`<div class="sys-banner test" role="status">${icon('flask')}
      <span><b>Debug mode is on.</b> This application is under testing: you are working on test data,
      and you may experience degraded performance.</span></div>`);
  }
  if (System.db === 'degraded' && Shell.user && ['admin', 'super_admin'].includes(Shell.user.role)) {
    parts.push(`<div class="sys-banner degraded" role="alert">${icon('alert')}
      <span><b>Database degraded:</b> it was changed outside imPress and restored automatically. <a href="#/admin/system">Review</a></span></div>`);
  }
  el.innerHTML = parts.join('');
  document.body.classList.toggle('has-banner', parts.length > 0);
  document.documentElement.style.setProperty('--banner-h', `${el.offsetHeight}px`);
  const chip = document.getElementById('db-chip');
  if (chip) chip.classList.toggle('hidden', System.db !== 'degraded');
}

// ── Shell: sidebar + top bar ──────────────────────────────────────────

const Shell = { user: null, counts: {} };

const NAV = [
  { section: 'Workspace' },
  { href: '#/dashboard', label: 'Overview', icon: 'grid', match: ['#/dashboard', '#/admin'] },
  { href: 'classes', label: 'Classrooms', icon: 'school', match: ['#/classes', '#/admin/classes', '#/admin/classes/new', '#/class'], count: 'classes' },
  { href: '#/sessions', label: 'Quizzes & polls', icon: 'clipboard', match: ['#/sessions', '#/quiz', '#/poll', '#/quiz-results', '#/poll-results'] },
  { href: '#/admin/students', label: 'Students', icon: 'users', match: ['#/admin/students', '#/student'], perm: 'admin' },
  { href: '#/admin/courses', label: 'Courses', icon: 'book', match: ['#/admin/courses'], perm: 'admin' },
  { section: 'Administration', perm: 'admin' },
  { href: '#/admin/modules', label: 'Devices', icon: 'radio', match: ['#/admin/modules'], perm: 'admin' },
  { href: '#/admin/firmware', label: 'Firmware & OTA', icon: 'cpu', match: ['#/admin/firmware'], perm: 'admin' },
  { href: '#/admin/users', label: 'User access', icon: 'userCog', match: ['#/admin/users'], perm: 'admin' },
  { href: '#/admin/activity', label: 'Activity log', icon: 'history', match: ['#/admin/activity'], perm: 'admin' },
  { href: '#/admin/system', label: 'System', icon: 'database', match: ['#/admin/system'], perm: 'admin', dbChip: true },
  { href: '#/admin/test-data', label: 'Test data', icon: 'flask', match: ['#/admin/test-data'], perm: 'super' },
];

const CRUMBS = {
  '#/dashboard': ['Overview'], '#/admin': ['Overview'], '#/classes': ['Classrooms'], '#/admin/classes': ['Classrooms'],
  '#/admin/classes/new': ['Classrooms', 'Classroom'], '#/class': ['Classrooms', 'Classroom'],
  '#/sessions': ['Quizzes & polls'], '#/quiz': ['Quizzes & polls', 'Create quiz'], '#/poll': ['Quizzes & polls', 'Create poll'],
  '#/quiz-results': ['Quizzes & polls', 'Quiz results'], '#/poll-results': ['Quizzes & polls', 'Poll results'],
  '#/admin/students': ['Students'], '#/student': ['Students', 'Student'], '#/admin/courses': ['Courses'],
  '#/admin/modules': ['Administration', 'Devices'], '#/admin/firmware': ['Administration', 'Firmware & OTA'],
  '#/admin/users': ['Administration', 'User access'], '#/admin/activity': ['Administration', 'Activity log'],
  '#/admin/system': ['Administration', 'System'], '#/admin/test-data': ['Administration', 'Test data'],
  '#/settings': ['Settings'],
};

function isAdminUser(u) { return u && (u.role === 'admin' || u.role === 'super_admin'); }

function renderNavbar(user, currentHash) {
  Shell.user = user;
  const admin = isAdminUser(user);
  const superAdmin = user.role === 'super_admin';
  const items = NAV.filter(n => !n.perm || (n.perm === 'admin' && admin) || (n.perm === 'super' && superAdmin)).map(n => {
    if (n.section) return `<div class="nav-section">${escHtml(n.section)}</div>`;
    const href = n.href === 'classes' ? (admin ? '#/admin/classes' : '#/classes') : n.href;
    const active = n.match.includes(currentHash);
    const count = n.count && Shell.counts[n.count] ? `<span class="count">${String(Shell.counts[n.count]).padStart(2, '0')}</span>` : '';
    const chip = n.dbChip ? `<span id="db-chip" class="badge badge-danger badge-sm ${System.db === 'degraded' ? '' : 'hidden'}" style="margin-left:auto">Degraded</span>` : '';
    return `<a href="${href}" class="nav-item${active ? ' active' : ''}"${active ? ' aria-current="page"' : ''}>${icon(n.icon)}<span>${escHtml(n.label)}</span>${count}${chip}</a>`;
  }).join('');
  const crumbs = ['Workspace', ...(CRUMBS[currentHash] || [])];
  const roleLabel = { super_admin: 'Super admin', admin: 'Administrator', teacher: 'Faculty' }[user.role] || user.role;
  document.body.classList.add('shell');          // #app sits beside the sidebar (CSS)
  setTimeout(afterShell, 0);
  return `
    <div class="app-scrim" onclick="document.body.classList.remove('nav-open')"></div>
    <aside class="app-sidebar" aria-label="Main navigation">
      <a href="#/dashboard" class="brand"><span class="brand-mark">${icon('layers')}</span><span class="brand-name">imPress</span></a>
      <nav>${items}</nav>
      <div class="nav-spacer"></div>
      <div class="nav-foot">
        <a href="#/settings" class="nav-item${currentHash === '#/settings' ? ' active' : ''}">${icon('settings')}<span>Settings</span></a>
        <a href="/graph" target="_blank" rel="noopener" class="nav-item">${icon('help')}<span>Help &amp; documentation</span></a>
        <div class="user-card">${avatar(user.full_name || user.username, 'sm')}
          <div class="who"><b>${escHtml(user.full_name || user.username)}</b><span>${escHtml(roleLabel)}</span></div>
          <button class="btn btn-ghost btn-icon btn-sm" onclick="handleLogout()" title="Sign out" aria-label="Sign out">${icon('logout')}</button>
        </div>
      </div>
    </aside>
    <div class="app-topbar-host">
      <header class="app-topbar">
        <button class="icon-btn menu-toggle" onclick="document.body.classList.toggle('nav-open')" aria-label="Menu">${icon('menu')}</button>
        <nav class="crumbs" aria-label="Breadcrumb">${crumbs.map((c, i) => i === crumbs.length - 1
          ? `<b>${escHtml(c)}</b>` : `<span>${escHtml(c)}</span><span class="sep">/</span>`).join('')}</nav>
        <div class="topbar-right">
          <label class="searchbox">${icon('search', 'sm')}<span class="sr-only">Search</span>
            <input id="global-search" type="search" placeholder="Search classes, students…" autocomplete="off" oninput="globalSearch(this.value)" onkeydown="globalSearchKey(event)">
            <div id="search-results" class="search-results hidden"></div></label>
          <div style="position:relative">
            <button class="icon-btn" onclick="toggleNotices(event)" aria-label="Notifications">${icon('bell')}<span id="bell-dot" class="dot ${_notices.length ? '' : 'hidden'}"></span></button>
            <div id="notice-pop" class="popover hidden"><div class="popover-head"><b>Notifications</b></div><div class="popover-body"></div></div>
          </div>
          <button class="icon-btn" onclick="toggleTheme()" aria-label="Toggle dark mode" data-theme-icon>${themeIcon()}</button>
          <a href="#/settings" title="${escHtml(user.full_name || user.username)}">${avatar(user.full_name || user.username)}</a>
        </div>
      </header>
    </div>`;
}

function afterShell() {
  renderBanners();
  Live.start();
}

window.handleLogout = async function () {
  Live.stop();
  await authApi.logout();
  navigate('#/login');
};

// ── Global search (classes, students, users) ──────────────────────────

let _searchData = null, _searchSeq = 0, _searchSel = -1;
window.globalSearch = async function (q) {
  const box = document.getElementById('search-results');
  if (!box) return;
  q = q.trim().toLowerCase();
  if (q.length < 2) { box.classList.add('hidden'); return; }
  const seq = ++_searchSeq;
  if (!_searchData) {
    const admin = isAdminUser(Shell.user);
    const [classes, students, users] = await Promise.all([
      (admin ? adminApi.listClasses() : classesApi.list()).catch(() => []),
      admin ? studentsApi.list('').catch(() => []) : Promise.resolve([]),
      admin ? adminApi.listUsers().catch(() => []) : Promise.resolve([]),
    ]);
    _searchData = { classes, students, users };
    setTimeout(() => { _searchData = null; }, 60000);
  }
  if (seq !== _searchSeq) return;
  const d = _searchData;
  const hits = [
    ...d.classes.filter(c => `${c.name} ${c.code} ${c.course_code || ''} ${c.classroom_code || ''}`.toLowerCase().includes(q))
      .slice(0, 6).map(c => ({ href: `#/class?id=${c.id}`, label: c.name, sub: c.code, kind: 'Classroom', ic: 'school' })),
    ...d.students.filter(s => `${s.student_name} ${s.roll_number}`.toLowerCase().includes(q))
      .slice(0, 6).map(s => ({ href: `#/student?id=${s.id}`, label: s.student_name, sub: s.roll_number, kind: 'Student', ic: 'user' })),
    ...d.users.filter(u => `${u.full_name || ''} ${u.username}`.toLowerCase().includes(q))
      .slice(0, 4).map(u => ({ href: '#/admin/users', label: u.full_name || u.username, sub: '@' + u.username, kind: 'Account', ic: 'userCog' })),
  ];
  _searchSel = -1;
  box.innerHTML = hits.length ? hits.map(h => `<a href="${h.href}" onclick="document.getElementById('search-results').classList.add('hidden')">${icon(h.ic, 'sm')}<span>${escHtml(h.label)} <span class="text-muted text-sm">${escHtml(h.sub)}</span></span><span class="kind">${h.kind}</span></a>`).join('')
    : `<div class="empty" style="padding:16px">No matches</div>`;
  box.classList.remove('hidden');
};
window.globalSearchKey = function (e) {
  const links = [...document.querySelectorAll('#search-results a')];
  if (!links.length) return;
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault();
    _searchSel = (_searchSel + (e.key === 'ArrowDown' ? 1 : -1) + links.length) % links.length;
    links.forEach((a, i) => a.classList.toggle('sel', i === _searchSel));
  } else if (e.key === 'Enter') {
    (links[_searchSel] || links[0]).click();
    location.hash = (links[_searchSel] || links[0]).getAttribute('href');
  } else if (e.key === 'Escape') {
    document.getElementById('search-results').classList.add('hidden');
  }
};

// ── Live updates (Server-Sent Events) ─────────────────────────────────
/* The server says which tables changed; the page showing them refetches in
 * the background. A refresh never interrupts the user: it waits while a field
 * is focused or edited, a dialog is open, text is selected, or the user
 * interacted in the last few seconds, and retries shortly after. */

const ROUTE_TOPICS = {
  '#/dashboard': ['class_sessions', 'students', 'student_enrollments', 'esp_devices', 'student_modules', 'quizzes', 'polls', 'activity_logs', 'users'],
  '#/admin': ['class_sessions', 'students', 'esp_devices', 'student_modules', 'activity_logs', 'users'],
  '#/classes': ['class_sessions', 'student_enrollments', 'quizzes', 'polls', 'student_modules'],
  '#/admin/classes': ['class_sessions', 'student_enrollments', 'student_modules', 'class_faculty'],
  '#/sessions': ['quizzes', 'polls', 'quiz_answers', 'poll_votes'],
  '#/admin/students': ['students', 'student_enrollments', 'student_modules', 'attendance'],
  '#/admin/courses': ['courses'],
  '#/admin/modules': ['esp_devices', 'student_modules', 'deployment_targets'],
  '#/admin/firmware': ['firmware_artifacts', 'firmware_deployments', 'deployment_targets', 'esp_devices'],
  '#/admin/users': ['users', 'activity_logs', 'class_faculty'],
  '#/admin/activity': ['activity_logs'],
  '#/admin/system': ['activity_logs'],
  '#/quiz-results': ['quiz_answers'], '#/poll-results': ['poll_votes'],
  '#/student': ['students', 'quiz_answers', 'poll_votes', 'attendance', 'student_enrollments'],
};

const Live = {
  es: null, pending: null, lastUser: 0, timer: null, lastRun: 0,
  start() {
    if (this.es || !window.EventSource) return;
    this.es = new EventSource('/api/events');
    this.es.onmessage = (m) => {
      let ev;
      try { ev = JSON.parse(m.data); } catch { return; }
      if (ev.type === 'changed') this.changed(ev.topics || []);
      else if (ev.type === 'alert') { showToast(ev.message, ev.level === 'error' ? 'error' : ev.level, { keep: ev.level === 'error' }); addNotice(ev.message, ev.level); }
      else if (ev.type === 'status') {
        if ('test_mode' in ev) { System.test_mode = ev.test_mode; }
        if ('db' in ev) System.db = ev.db;
        renderBanners();
      } else if (ev.type === 'session_ended') {
        this.stop();
        clearToken();
        showToast('Your session ended. Please sign in again.', 'error');
        navigate('#/login');
      }
    };
    this.es.onerror = () => {               // the browser reconnects by itself; stop if signed out
      if (!isLoggedIn()) this.stop();
    };
  },
  stop() { if (this.es) { this.es.close(); this.es = null; } },
  changed(topics) {
    const want = ROUTE_TOPICS[getRoute()];
    if (!want || !topics.some(t => want.includes(t))) return;
    this.pending = true;
    this.schedule(600);
  },
  schedule(ms) {
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.run(), ms);
  },
  busy() {
    if (Date.now() - this.lastUser < 4000) return true;
    if (document.querySelector('.modal:not(.hidden)')) return true;
    const a = document.activeElement;
    if (a && (a.matches('input, textarea, select, [contenteditable]') && !a.matches('#global-search'))) return true;
    if (String(window.getSelection?.() || '').length) return true;
    return [...document.querySelectorAll('#app input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]), #app textarea')]
      .some(el => el.value !== el.defaultValue && !el.dataset.live);
  },
  async run() {
    if (!this.pending) return;
    if (this.busy() || Date.now() - this.lastRun < 2000) { this.schedule(2500); return; }
    this.pending = false;
    this.lastRun = Date.now();
    await quietRefresh();
  },
};
['pointerdown', 'keydown', 'wheel'].forEach(t => window.addEventListener(t, () => { Live.lastUser = Date.now(); }, { passive: true }));
document.addEventListener('visibilitychange', () => { if (!document.hidden && Live.pending) Live.schedule(200); });


// ── Delegated events (v2.2) ──────────────────────────────────────────────
// Markup carries data-action="name" (also data-change, data-input, data-submit,
// data-keydown) and Actions[name](element, event) runs it. No inline handlers:
// the page's Content-Security-Policy can then forbid them.
const Actions = {};
(function wireDelegatedEvents() {
  const route = (type, attr) => document.addEventListener(type, (e) => {
    const el = e.target && e.target.closest ? e.target.closest(`[${attr}]`) : null;
    const fn = el && Actions[el.getAttribute(attr)];
    if (fn) fn(el, e);
  });
  [['click', 'data-action'], ['change', 'data-change'], ['input', 'data-input'], ['submit', 'data-submit'],
   ['keydown', 'data-keydown']].forEach(([t, a]) => route(t, a));
})();

// A small modal that asks for text (a password, a typed confirmation) and
// resolves with the values, or null when cancelled. Built with the DOM, no inline script.
function askDialog({ title, body = '', fields = [], confirm = 'Confirm', danger = false, validate = null }) {
  return new Promise((resolve) => {
    const m = document.createElement('div');
    m.className = 'modal';
    m.innerHTML = `<div class="modal-backdrop"></div>
      <form class="modal-content card" novalidate role="dialog" aria-modal="true" aria-label="${escHtml(title)}">
        <h2>${escHtml(title)}</h2>
        ${body ? `<p class="text-muted">${body}</p>` : ''}
        ${fields.map((f, i) => `<div class="form-group"><label for="dlg-${i}">${escHtml(f.label)}</label>
          <input id="dlg-${i}" name="${escHtml(f.name)}" type="${escHtml(f.type || 'text')}" autocomplete="${escHtml(f.autocomplete || 'off')}"
            placeholder="${escHtml(f.placeholder || '')}"></div>`).join('')}
        <div class="modal-actions"><button type="button" class="btn btn-outline" data-dlg="cancel">Cancel</button>
          <button type="submit" class="btn ${danger ? 'btn-danger' : 'btn-primary'}" ${validate ? 'disabled' : ''}>${escHtml(confirm)}</button></div>
      </form>`;
    document.body.appendChild(m);
    const form = m.querySelector('form');
    const done = (value) => { m.remove(); document.removeEventListener('keydown', onKey); resolve(value); };
    const values = () => Object.fromEntries(fields.map(f => [f.name, form.elements[f.name].value]));
    const refresh = () => { if (validate) form.querySelector('button[type=submit]').disabled = !validate(values()); };
    const onKey = (e) => { if (e.key === 'Escape') done(null); };
    document.addEventListener('keydown', onKey);
    m.querySelector('.modal-backdrop').addEventListener('click', () => done(null));
    m.querySelector('[data-dlg=cancel]').addEventListener('click', () => done(null));
    form.addEventListener('input', refresh);
    form.addEventListener('submit', (e) => { e.preventDefault(); if (!validate || validate(values())) done(values()); });
    const first = form.querySelector('input'); if (first) first.focus(); else form.querySelector('[type=submit]').focus();
  });
}
