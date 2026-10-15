/* imPress v2.2 shell behaviour: the collapsible sidebar, menus, the notification tray, the command palette (global search
 * with settings as live widgets), the help panel, keyboard shortcuts, and the notices that blur the page (account disabled,
 * system updating, session ended). Loaded after ui.js and app.js. */

const ROLE_TITLES = { super_admin: 'Super admin', admin: 'Administrator', teacher: 'Faculty' };
function roleTitle(u) {
  if (!u) return '';
  return u.role === 'teacher' && u.designation === 'ta' ? 'Teaching assistant' : (ROLE_TITLES[u.role] || u.role);
}

// ── Sidebar, menus, tray ──────────────────────────────────────────────

Object.assign(Actions, {
  'sidebar-toggle': (el) => {
    const next = !Prefs.cur.sidebar_collapsed;
    Prefs.save({ sidebar_collapsed: next });
    el.setAttribute('aria-expanded', String(!next));
    const label = el.querySelector('span');
    if (label) label.textContent = next ? 'Expand' : 'Collapse';
  },
  'toggle-menu': (el, e) => {
    e.stopPropagation();
    const menu = document.getElementById(el.dataset.menu);
    document.getElementById('notice-pop')?.classList.add('hidden');
    ['help-menu', 'user-menu'].filter(id => id !== el.dataset.menu).forEach(id => document.getElementById(id)?.classList.add('hidden'));
    menu?.classList.toggle('hidden');
  },
  'tray-tab': (el, e) => { e.stopPropagation(); Tray.tab = el.dataset.tab; Tray.draw(); },
  'tray-read': (el, e) => { e.stopPropagation(); Tray.items.forEach(n => { n.read = true; }); Tray.save(); Tray.badge(); Tray.draw(); },
  'tray-clear': (el, e) => { e.stopPropagation(); Tray.items = []; Tray.save(); Tray.badge(); Tray.draw(); },
  'tray-dismiss': (el, e) => { e.stopPropagation(); Tray.items = Tray.items.filter(n => String(n.id) !== el.dataset.id); Tray.save(); Tray.badge(); Tray.draw(); },
  'open-help': (el, e) => { e.preventDefault(); Help.open(); },
  'open-shortcuts': () => Help.shortcuts(),
  'start-tour': () => { document.querySelectorAll('.menu').forEach(m => m.classList.add('hidden')); if (typeof Tour !== 'undefined') Tour.start(); },
  'open-palette': () => Palette.open(),
});

document.addEventListener('keydown', (e) => {
  const typing = e.target.matches?.('input, textarea, select, [contenteditable]');
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); Palette.open(); return; }
  if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === '/' && document.querySelector('.search-trigger')) { e.preventDefault(); Palette.open(); }
  else if (e.key === '?' ) { Help.shortcuts(); }
  else if (e.key === '[' && document.getElementById('app-sidebar')) Actions['sidebar-toggle'](document.querySelector('.nav-collapse') || document.body);
});

// ── Notices that blur the page ───────────────────────────────────────

const Overlays = {
  shown: null,
  show(kind, { iconName, tone = '', title, text, button, onButton, spin = false, progress = false }) {
    if (this.shown === kind) return;
    this.hide();
    this.shown = kind;
    const el = document.createElement('div');
    el.className = 'notice-overlay';
    el.id = 'notice-overlay';
    el.setAttribute('role', 'alertdialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-labelledby', 'ov-title');
    el.setAttribute('aria-describedby', 'ov-text');
    el.innerHTML = `<div class="notice-card"><div class="big-ic ${tone} ${spin ? 'spin' : ''}">${icon(iconName)}</div>
      <h2 id="ov-title">${escHtml(title)}</h2><p id="ov-text">${escHtml(text)}</p>
      ${progress ? '<div class="notice-progress" role="progressbar" aria-label="Update in progress"><i></i></div>' : ''}
      ${button ? `<button class="btn btn-primary" id="ov-btn">${escHtml(button)}</button>` : ''}</div>`;
    document.body.appendChild(el);
    document.body.classList.add('blurred');
    document.getElementById('ov-btn')?.addEventListener('click', onButton);
    (document.getElementById('ov-btn') || el).focus?.();
  },
  hide() {
    document.getElementById('notice-overlay')?.remove();
    document.body.classList.remove('blurred');
    this.shown = null;
  },
  /** The server says whether an update is running (GET /api/system/status); the page blurs until it is done. */
  refresh() {
    const up = System.updating;
    if (System.feature_flags?.update_overlay === false || !isLoggedIn()) { if (this.shown === 'update') this.hide(); return; }
    // the people running the update keep their controls: administrators on the firmware and device pages are not blurred
    const managing = isAdminUser(Shell.user) && ['#/admin/firmware', '#/admin/modules'].includes(getRoute());
    if (up && up.active && !managing) {
      this.show('update', { iconName: 'refresh', tone: 'info', spin: true, progress: true, title: 'Updating imPress',
        text: 'We are sorry for the interruption. imPress is applying a system update and will be available again in a moment. This page returns by itself as soon as the update has finished.' });
    } else if (this.shown === 'update') {
      this.hide();
      showToast('The update has finished.', 'success');
    }
  },
  sessionEnded(reason) {
    clearToken();
    Live.stop();
    const toLogin = () => { this.hide(); navigate('#/login'); location.reload(); };
    if (reason === 'disabled' && System.feature_flags?.disabled_overlay !== false) {
      this.show('disabled', { iconName: 'userX', title: 'Your account has been disabled',
        text: 'An administrator has disabled this account, so your session has ended. If you think this is a mistake, please contact your administrator.',
        button: 'Return to sign in', onButton: toLogin });
    } else if (reason === 'restart') {
      this.show('restart', { iconName: 'refresh', tone: 'info', title: 'imPress was restarted',
        text: 'For your security every session ends when the server restarts. Please sign in again to continue.', button: 'Sign in', onButton: toLogin });
    } else {
      showToast('Your session has ended. Please sign in again.', 'error');
      navigate('#/login');
    }
  },
};
window.addEventListener('hashchange', () => Overlays.refresh());
setInterval(() => { if (isLoggedIn() && !document.hidden) loadSystemStatus(); }, 20000);

// ── Command palette: search everything, and change settings in place ──

const Palette = {
  el: null, seq: 0, sel: 0, rows: [],
  pages() {
    const admin = isAdminUser(Shell.user), sup = Shell.user?.role === 'super_admin';
    return NAV.filter(n => n.href && (!n.perm || (n.perm === 'admin' && admin) || (n.perm === 'super' && sup)))
      .map(n => ({ kind: 'page', title: n.label, sub: 'Go to page', href: n.href === 'classes' ? (admin ? '#/admin/classes' : '#/classes') : n.href, icon: n.icon }))
      .concat([{ kind: 'page', title: 'Settings', sub: 'Go to page', href: '#/settings', icon: 'settings' }]);
  },
  widgets() {
    const p = Prefs.cur, admin = isAdminUser(Shell.user);
    const f = System.feature_flags || {};
    const list = [
      { id: 'theme', title: 'Theme', sub: 'Light, dark or follow the system', words: 'theme dark light mode appearance night', icon: 'moon',
        ctl: segmented('theme', [['light', 'Light'], ['dark', 'Dark'], ['system', 'Auto']], p.theme) },
      { id: 'accent', title: 'Accent colour', sub: 'The colour of buttons and highlights', words: 'accent colour color theme personalize', icon: 'palette',
        ctl: `<div class="swatches">${Object.entries(Prefs.ACCENTS).map(([k, v]) => `<button class="swatch ${p.accent === k && !p.accent_custom ? 'active' : ''}" style="background:${v}" data-pal-set="accent" data-v="${k}" aria-label="${k}"></button>`).join('')}</div>` },
      { id: 'motion', title: 'Reduce motion', sub: 'Fewer animations and transitions', words: 'reduce motion animation animations transitions accessibility', icon: 'accessibility',
        ctl: toggle('motion', p.motion === 'reduce', 'reduce', 'system') },
      { id: 'contrast', title: 'Increase contrast', sub: 'Stronger text and borders', words: 'contrast high accessibility visibility', icon: 'contrast',
        ctl: toggle('contrast', p.contrast === 'high', 'high', 'normal') },
      { id: 'scale', title: 'Text size', sub: 'Make everything smaller or larger', words: 'text size font zoom bigger larger smaller scale accessibility', icon: 'type',
        ctl: segmented('scale', [['small', 'Smaller'], ['default', 'Default'], ['large', 'Larger'], ['xlarge', 'Largest']], p.scale) },
      { id: 'vision', title: 'Colour vision', sub: 'Colours that are easier to tell apart', words: 'colour color blind vision protanopia deuteranopia tritanopia monochrome accessibility', icon: 'eye',
        ctl: `<select class="input-sm" data-pal-set="vision" aria-label="Colour vision mode">${[['none', 'Standard'], ['protanopia', 'Protanopia'], ['deuteranopia', 'Deuteranopia'], ['tritanopia', 'Tritanopia'], ['monochrome', 'Monochrome']]
          .map(([k, t]) => `<option value="${k}" ${p.vision === k ? 'selected' : ''}>${t}</option>`).join('')}</select>` },
      { id: 'sidebar', title: 'Collapse sidebar', sub: 'Show only icons', words: 'sidebar collapse menu navigation', icon: 'panelLeft', ctl: toggle('sidebar_collapsed', p.sidebar_collapsed, true, false, true) },
      { id: 'timefmt', title: 'Time format', sub: '24-hour or 12-hour clock', words: 'time format clock 24 12 hour date', icon: 'clock', ctl: segmented('time_format', [['24h', '24-hour'], ['12h', '12-hour']], p.time_format) },
      { id: 'datefmt', title: 'Date format', sub: 'How dates are written', words: 'date format day month year', icon: 'calendar',
        ctl: `<select class="input-sm" data-pal-set="date_format" aria-label="Date format">${[['dmy', '31/12/2026'], ['mdy', '12/31/2026'], ['ymd', '2026/12/31'], ['long', '31 Dec 2026'], ['iso', '2026-12-31']]
          .map(([k, t]) => `<option value="${k}" ${p.date_format === k ? 'selected' : ''}>${t}</option>`).join('')}</select>` },
    ];
    if (admin && f.advanced_mode !== false) list.push({ id: 'advanced', title: 'Advanced mode', sub: 'Detailed statistics for administrators', words: 'advanced mode detailed statistics stats admin', icon: 'sliders',
      ctl: toggle('advanced', p.advanced, true, false, true) });
    if (f.personalization === false) return list.filter(w => !['accent', 'timefmt', 'datefmt'].includes(w.id));
    return list;
  },
  open() {
    if (this.el || !Shell.user) return;
    const el = document.createElement('div');
    el.className = 'palette-back';
    el.innerHTML = `<div class="palette" role="dialog" aria-modal="true" aria-label="Search">
      <div class="palette-input">${icon('search')}<input id="palette-input" type="text" autocomplete="off" spellcheck="false" placeholder="Search classes, students, pages and settings…" aria-label="Search" role="combobox" aria-expanded="true" aria-controls="palette-body"><kbd>Esc</kbd></div>
      <div class="palette-body" id="palette-body" role="listbox"></div>
      <div class="palette-foot"><span><kbd>↑</kbd> <kbd>↓</kbd> to move</span><span><kbd>↵</kbd> to open</span><span><kbd>Esc</kbd> to close</span></div></div>`;
    document.body.appendChild(el);
    this.el = el;
    const input = el.querySelector('#palette-input');
    input.focus();
    this.draw('');
    input.addEventListener('input', () => this.query(input.value));
    input.addEventListener('keydown', (e) => this.key(e));
    el.addEventListener('mousedown', (e) => { if (e.target === el) this.close(); });
    el.addEventListener('click', (e) => this.click(e));
    el.addEventListener('change', (e) => this.change(e));
  },
  close() { this.el?.remove(); this.el = null; },
  async query(q) {
    q = q.trim();
    const seq = ++this.seq;
    if (q.length < 2) { this.draw(q); return; }
    let groups = [];
    try { groups = (await apiRequest(`/search?q=${encodeURIComponent(q)}`, { headers: { 'X-Impress-Background': '1' } })).groups; } catch { /* offline: pages and settings still work */ }
    if (seq !== this.seq || !this.el) return;
    this.draw(q, groups);
  },
  draw(q, groups = []) {
    const low = q.toLowerCase();
    const pages = low ? this.pages().filter(p => p.title.toLowerCase().includes(low)) : this.pages().slice(0, 6);
    const widgets = low ? this.widgets().filter(w => `${w.title} ${w.words}`.toLowerCase().includes(low)) : this.widgets().slice(0, 3);
    this.rows = [];
    const row = (r) => { this.rows.push(r); return `<a class="palette-row" role="option" data-i="${this.rows.length - 1}" href="${escHtml(r.href)}"><span class="pi">${icon(r.icon || 'info', 'sm')}</span><span class="pt"><b>${escHtml(r.title)}</b><span>${escHtml(r.sub || '')}</span></span><span class="pk">${escHtml(r.kind === 'page' ? 'Page' : r.tag || '')}</span></a>`; };
    let html = '';
    for (const g of groups) html += `<div class="palette-group">${escHtml(g.label)}</div>` + g.items.map(i => row({ kind: g.type, title: i.title, sub: i.subtitle, href: i.href, icon: i.icon, tag: '' })).join('');
    if (pages.length) html += `<div class="palette-group">Pages</div>` + pages.map(row).join('');
    if (widgets.length) html += `<div class="palette-group">${low ? 'Settings' : 'Quick settings'}</div>` + widgets.map(w => `<div class="palette-widget"><span class="pi" style="width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:var(--primary-soft);color:var(--primary)">${icon(w.icon, 'sm')}</span>
      <span class="pt"><b>${escHtml(w.title)}</b><span>${escHtml(w.sub)}</span></span>${w.ctl}</div>`).join('');
    if (typeof Tour !== 'undefined' && (!low || 'tour tutorial guide help'.includes(low))) {
      this.rows.push({ kind: 'action', run: () => Tour.start() });
      html += `<div class="palette-group">Help</div><a class="palette-row" role="option" data-i="${this.rows.length - 1}" href="#"><span class="pi">${icon('compass', 'sm')}</span><span class="pt"><b>Take the tour</b><span>A short guide to imPress</span></span></a>`;
    }
    if (low.length >= 2 && !groups.length && !pages.length && !widgets.length) html = emptyState('No results', 'Try another word, a roll number or a classroom code.', 'search');
    this.el.querySelector('#palette-body').innerHTML = html || emptyState('Type to search', 'Classes, students, accounts, pages and settings.', 'search');
    this.sel = 0;
    this.mark();
  },
  mark() {
    const rows = [...this.el.querySelectorAll('.palette-row')];
    rows.forEach((r, i) => { r.classList.toggle('sel', i === this.sel); r.setAttribute('aria-selected', i === this.sel); });
    rows[this.sel]?.scrollIntoView({ block: 'nearest' });
  },
  key(e) {
    const rows = this.el.querySelectorAll('.palette-row');
    if (e.key === 'Escape') { e.preventDefault(); this.close(); }
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (rows.length) { this.sel = (this.sel + (e.key === 'ArrowDown' ? 1 : -1) + rows.length) % rows.length; this.mark(); }
    } else if (e.key === 'Enter') { e.preventDefault(); rows[this.sel]?.click(); }
  },
  click(e) {
    const set = e.target.closest('[data-pal-set]');
    if (set) { if (set.tagName === 'BUTTON') this.apply(set.dataset.palSet, set.dataset.v, e); return; }
    const row = e.target.closest('.palette-row');
    if (!row) return;
    e.preventDefault();
    const r = this.rows[Number(row.dataset.i)];
    this.close();
    if (r?.run) r.run(); else if (r?.href) location.hash = r.href;
  },
  change(e) {
    const t = e.target;
    if (!t.matches('[data-pal-set]')) return;
    const v = t.type === 'checkbox' ? (t.checked ? t.dataset.on : t.dataset.off) : t.value;
    this.apply(t.dataset.palSet, v, e);
  },
  apply(key, raw, ev) {
    const v = raw === 'true' ? true : raw === 'false' ? false : raw;
    Prefs.save({ [key]: v }, ev);
    setTimeout(() => this.el && this.draw(this.el.querySelector('#palette-input').value.trim()), 60);
  },
};

function segmented(key, options, current) {
  return `<div class="segmented" role="group">${options.map(([v, t]) => `<button type="button" class="${String(current) === String(v) ? 'active' : ''}" data-pal-set="${key}" data-v="${v}">${t}</button>`).join('')}</div>`;
}
function toggle(key, on, onValue, offValue, bool = false) {
  return `<label class="switch"><input type="checkbox" role="switch" data-pal-set="${key}" data-on="${bool ? 'true' : onValue}" data-off="${bool ? 'false' : offValue}" ${on ? 'checked' : ''} aria-label="${key}"><i></i></label>`;
}

// ── Help panel and shortcuts ─────────────────────────────────────────

const Help = {
  open() {
    this.close();
    const wrap = document.createElement('div');
    wrap.id = 'help-drawer';
    const docs = 'https://github.com/Kush-Kelaiya22/imPress/tree/varun/v2.2/docs';
    wrap.innerHTML = `<div class="drawer-back" data-help-close></div>
      <aside class="drawer" role="dialog" aria-modal="true" aria-label="Help and documentation">
        <div class="flex-between"><h2>${icon('lifebuoy')} Help &amp; documentation</h2><button class="btn btn-ghost btn-icon" data-help-close aria-label="Close">${icon('x')}</button></div>
        <p class="text-muted mt-1">imPress ${escHtml(System.release || System.version || '')}</p>
        <div class="mt-2">
          ${[['book', 'Administrator guide', 'Accounts, classrooms, devices and firmware', `${docs}/guides`],
             ['shield', 'Security and policy', 'The security model, global policy, integrity and backups', `${docs}/design`],
             ['code', 'API reference', 'REST and device endpoints', `${docs}/api`],
             ['terminal', 'Root console and launch flags', 'For whoever runs the server', `${docs}/guides`],
             ['lifebuoy', 'Troubleshooting', 'Common problems and how to fix them', `${docs}/guides`]]
            .map(([ic, t, s, href]) => `<a class="feed-item" href="${href}" target="_blank" rel="noopener"><span class="feed-icon">${icon(ic, 'sm')}</span><div class="feed-body"><b>${t}</b><span>${s}</span></div>${icon('external', 'sm')}</a>`).join('')}
        </div>
        <div class="mt-2 flex gap-1"><button class="btn btn-outline" data-action="start-tour">${icon('compass', 'sm')} Take the tour</button>
          <button class="btn btn-outline" data-action="open-shortcuts">${icon('keyboard', 'sm')} Shortcuts</button></div>
      </aside>`;
    document.body.appendChild(wrap);
    wrap.addEventListener('click', (e) => { if (e.target.closest('[data-help-close]')) this.close(); else if (e.target.closest('[data-action="start-tour"]')) this.close(); });
  },
  close() { document.getElementById('help-drawer')?.remove(); },
  shortcuts() {
    askDialog({ title: 'Keyboard shortcuts', confirm: 'Done', body: `<div class="kv">
      <dt><kbd>${/Mac/.test(navigator.platform) ? '⌘' : 'Ctrl'}</kbd> <kbd>K</kbd></dt><dd>Search, pages and settings</dd>
      <dt><kbd>/</kbd></dt><dd>Search</dd><dt><kbd>[</kbd></dt><dd>Collapse or expand the sidebar</dd>
      <dt><kbd>?</kbd></dt><dd>This list</dd><dt><kbd>Esc</kbd></dt><dd>Close a dialog or the search</dd></div>` });
  },
};
