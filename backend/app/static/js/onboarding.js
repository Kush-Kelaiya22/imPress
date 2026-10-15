/* imPress v2.2 first sign-in: choose a password (when the account started with a temporary one), say what to call you,
 * pick a look, and be offered a short guided tour. The tour can be taken again at any time from the Help button. */

const Onboarding = {
  active: false, user: null, step: 0, steps: [], data: {},

  required() { if (!this.active) this.run(null); },      // the server answered 403 PASSWORD_CHANGE_REQUIRED
  maybeAfterShell() {
    const u = Shell.user;
    if (!u || this.active || this.checked === u.id) return;
    this.checked = u.id;
    if ((u.must_change_password || (!u.onboarded && System.feature_flags?.onboarding !== false))) this.run(u);
    else if (u.onboarded && !Prefs.cur.tutorial_done && this.offerTour && System.feature_flags?.tutorial !== false) { this.offerTour = false; setTimeout(() => Tour.start(), 600); }
  },

  async run(user) {
    this.active = true;
    try { this.user = user || await authApi.me(); } catch { this.active = false; return; }
    const u = this.user;
    this.data = { name: u.display_name || u.full_name || u.username, theme: Prefs.cur.theme };
    this.steps = [];
    if (u.must_change_password) this.steps.push('password');
    if (!u.onboarded && System.feature_flags?.onboarding !== false) this.steps.push('name', 'look', 'done');
    this.step = 0;
    document.body.classList.remove('shell');
    const el = document.createElement('div');
    el.className = 'onb';
    el.id = 'onb';
    document.body.appendChild(el);
    el.addEventListener('click', (e) => this.click(e));
    el.addEventListener('submit', (e) => { e.preventDefault(); this.next(); });
    this.draw();
  },

  draw(dir = 1) {
    const el = document.getElementById('onb');
    if (!el) return;
    const kind = this.steps[this.step], u = this.user;
    const bars = this.steps.map((_, i) => `<i class="${i < this.step ? 'done' : i === this.step ? 'now' : ''}"></i>`).join('');
    const isLast = this.step === this.steps.length - 1;
    const panes = {
      password: `<h1>Choose your own password</h1>
        <p class="lead">Your account started with a temporary password. Choose one only you know to finish setting it up.</p>
        <div class="form-group"><label for="onb-cur">Temporary password</label><input id="onb-cur" type="password" autocomplete="current-password" required></div>
        <div class="form-group"><label for="onb-new">New password</label><input id="onb-new" type="password" autocomplete="new-password" required>
          ${passwordMeterHtml('onb-new')}
          <div class="pw-rules" id="onb-rules">${u.role === 'super_admin' ? '<span>10 or more characters</span>' : ['8 or more characters', 'a lower-case letter', 'an upper-case letter', 'a number', 'a special character'].map(r => `<span data-r="${r}">${icon('check', 'sm')}${r}</span>`).join('')}</div></div>
        <div class="form-group"><label for="onb-again">Type it again</label><input id="onb-again" type="password" autocomplete="new-password" required></div>
        <p id="onb-err" class="callout danger hidden" role="alert"></p>`,
      name: `<h1>Welcome${this.data.name ? ', ' + escHtml(String(this.data.name).split(' ')[0]) : ''}</h1>
        <p class="lead">What should imPress call you? This is the name other people see. You keep signing in as <b>@${escHtml(u.username)}</b>.</p>
        <div class="form-group"><label for="onb-name">Display name</label><input id="onb-name" type="text" maxlength="64" value="${escHtml(this.data.name)}" autocomplete="name" required></div>`,
      look: `<h1>Pick your look</h1><p class="lead">You can change this at any time in Settings. Try one: it applies straight away.</p>
        <div class="theme-choices">${[['light', 'Light'], ['dark', 'Dark'], ['system', 'Match my device']].map(([k, t]) =>
          `<button type="button" class="theme-choice ${Prefs.cur.theme === k ? 'active' : ''}" data-theme-pick="${k}"><div class="sw ${k}"></div>${t}</button>`).join('')}</div>
        <div class="mt-2"><label>Accent colour</label><div class="swatches mt-1">${Object.entries(Prefs.ACCENTS).map(([k, v]) =>
          `<button type="button" class="swatch ${Prefs.cur.accent === k ? 'active' : ''}" style="background:${v}" data-accent-pick="${k}" aria-label="${k}"></button>`).join('')}</div></div>`,
      done: `<div class="big-ic info" style="width:54px;height:54px;border-radius:16px;display:grid;place-items:center;background:var(--primary-soft);color:var(--primary);margin-bottom:14px">${icon('sparkles', 'lg')}</div>
        <h1>You are all set</h1><p class="lead">Would you like a quick tour? It takes about a minute and shows where things are. You can take it later from the help button.</p>`,
    };
    const actions = kind === 'done'
      ? `<button type="button" class="btn btn-ghost" data-onb="skip-tour">Skip for now</button><button type="submit" class="btn btn-primary">${icon('compass', 'sm')} Start the tour</button>`
      : `${this.step > 0 && kind !== 'password' ? `<button type="button" class="btn btn-ghost" data-onb="back">${icon('arrowLeft', 'sm')} Back</button>` : '<span></span>'}
         <button type="submit" class="btn btn-primary">${isLast ? 'Finish' : 'Continue'} ${icon('arrowRight', 'sm')}</button>`;
    el.innerHTML = `<form class="onb-card" novalidate><div class="login-brand">${brandMark()}<span>imPress</span></div>
      <div class="onb-steps" aria-hidden="true">${bars}</div>
      <div class="onb-pane" style="animation-direction:${dir > 0 ? 'normal' : 'reverse'}">${panes[kind] || ''}</div>
      <div class="onb-actions">${actions}</div></form>`;
    if (kind === 'password') {
      const nu = document.getElementById('onb-new');
      wirePasswordMeter(nu, 'onb-new', u.username, u.role);
      nu.addEventListener('input', () => {
        const r = passwordStrength(nu.value, u.username);
        document.querySelectorAll('#onb-rules [data-r]').forEach(s => s.classList.toggle('ok', !r.missing.includes(s.dataset.r)));
      });
    }
    el.querySelector('input')?.focus();
  },

  async next() {
    const kind = this.steps[this.step];
    const err = (m) => { const e = document.getElementById('onb-err'); if (e) { e.textContent = m; e.classList.remove('hidden'); } else showToast(m, 'error'); };
    if (kind === 'password') {
      const cur = document.getElementById('onb-cur').value, pw = document.getElementById('onb-new').value, again = document.getElementById('onb-again').value;
      const why = passwordProblem(pw, this.user.username, this.user.role);
      if (!cur) return err('Enter the temporary password you were given.');
      if (why) return err(`That password ${why}.`);
      if (pw !== again) return err('The two passwords do not match.');
      try {
        await authApi.changePassword(cur, pw);
        this.user.must_change_password = false;
        showToast('Your password has been set.', 'success');
      } catch (e) { return err(e.message); }
    } else if (kind === 'name') {
      this.data.name = document.getElementById('onb-name').value.trim();
      if (!this.data.name) return;
    } else if (kind === 'done') {
      return this.finish(true);
    }
    if (this.step >= this.steps.length - 1) return this.finish(false);
    this.step += 1;
    this.draw(1);
  },

  click(e) {
    const t = e.target.closest('[data-theme-pick], [data-accent-pick], [data-onb]');
    if (!t) return;
    if (t.dataset.themePick) { Prefs.save({ theme: t.dataset.themePick }, e); this.data.theme = t.dataset.themePick; this.draw(0); }
    else if (t.dataset.accentPick) { Prefs.save({ accent: t.dataset.accentPick, accent_custom: '' }, e); this.draw(0); }
    else if (t.dataset.onb === 'back') { this.step = Math.max(0, this.step - 1); this.draw(-1); }
    else if (t.dataset.onb === 'skip-tour') this.finish(false);
  },

  async finish(tour) {
    try {
      if (!this.user.onboarded && this.steps.includes('name')) await authApi.onboard(this.data.name, Prefs.cur.theme === 'system' ? 'system' : Prefs.cur.theme);
      await Prefs.load();
    } catch (e) { showToast(e.message, 'error'); }
    document.getElementById('onb')?.remove();
    this.active = false;
    this.checked = null;
    if (Shell.user) Shell.user.onboarded = true;
    navigate('#/dashboard');
    router();
    if (tour) this.offerTour = true; else Prefs.save({ tutorial_done: true });
    if (tour) setTimeout(() => Tour.start(), 700);
  },
};

// ── The guided tour ────────────────────────────────────────────────────

const Tour = {
  i: 0, steps: [], hole: null, pop: null,
  build() {
    const admin = isAdminUser(Shell.user);
    const s = [
      { title: 'Welcome to imPress', text: 'A short tour of where things are. Use the arrow keys, or press Esc to leave at any time.', icon: 'sparkles' },
      { sel: '.app-sidebar nav', side: 'right', title: 'Everything is in the sidebar', text: `Classrooms, quizzes and polls${admin ? ', students, devices, accounts and the system' : ' and your students'}. Collapse it to icons with the button at its bottom.`, icon: 'panelLeft' },
      { sel: '.search-trigger', side: 'bottom', title: 'Search anything', text: 'Press Ctrl K (or /) to find classes, students and pages, and to change settings without leaving what you are doing.', icon: 'search' },
      { sel: '[data-action="toggle-notices"]', side: 'bottom', title: 'Notifications', text: 'Alerts from your classrooms and the system arrive here, newest first.', icon: 'bell' },
      { sel: '[data-theme-icon]', side: 'bottom', title: 'Make it yours', text: 'Switch between light and dark. Settings has accent colours, text size, colour-vision modes and more.', icon: 'palette' },
    ];
    if (document.querySelector('#dash-customise')) s.push({ sel: '#dash-customise', side: 'bottom', title: 'Your dashboard, your way', text: 'Customise lets you add, remove and drag widgets into the order you like.', icon: 'layout' });
    s.push(admin
      ? { sel: 'a[href="#/admin/users"]', side: 'right', title: 'Accounts and activity', text: 'Add faculty and administrators, see who is signed in, and review what happened.', icon: 'userCog' }
      : { sel: 'a[href="#/classes"]', side: 'right', title: 'Run a class', text: 'Open a classroom, start its session, then launch a quiz or a poll for the room.', icon: 'school' });
    s.push({ title: 'That is it', text: 'You can take this tour again from the help button in the top bar.', icon: 'checkCircle' });
    return s;
  },
  start() {
    if (this.pop || !Shell.user) return;
    document.getElementById('onb')?.remove();
    this.steps = this.build();
    this.i = 0;
    this.hole = document.createElement('div'); this.hole.className = 'tour-hole';
    this.pop = document.createElement('div'); this.pop.className = 'tour-pop'; this.pop.setAttribute('role', 'dialog'); this.pop.setAttribute('aria-label', 'Guided tour');
    this.dim = document.createElement('div'); this.dim.className = 'tour-dim';
    document.body.append(this.dim, this.hole, this.pop);
    this.key = (e) => { if (e.key === 'Escape') this.end(); else if (e.key === 'ArrowRight' || e.key === 'Enter') this.go(1); else if (e.key === 'ArrowLeft') this.go(-1); };
    document.addEventListener('keydown', this.key);
    this.pop.addEventListener('click', (e) => { const a = e.target.closest('[data-tour]')?.dataset.tour; if (a === 'next') this.go(1); else if (a === 'back') this.go(-1); else if (a === 'end') this.end(); });
    window.addEventListener('resize', this.place = () => this.show());
    this.show();
  },
  go(d) { if (this.i + d >= this.steps.length) return this.end(); this.i = Math.max(0, this.i + d); this.show(); },
  show() {
    const st = this.steps[this.i];
    let el = st.sel ? document.querySelector(st.sel) : null;
    if (el && !el.offsetParent && getComputedStyle(el).position !== 'fixed') el = null;
    el?.scrollIntoView?.({ block: 'nearest' });
    const r = el ? el.getBoundingClientRect() : null, pad = 6;
    if (r) Object.assign(this.hole.style, { left: `${r.left - pad}px`, top: `${r.top - pad}px`, width: `${r.width + pad * 2}px`, height: `${r.height + pad * 2}px`, opacity: 1 });
    else Object.assign(this.hole.style, { left: '50%', top: '40%', width: '0px', height: '0px', opacity: 1 });
    const last = this.i === this.steps.length - 1;
    this.pop.innerHTML = `<h3>${icon(st.icon || 'info', 'sm')} ${escHtml(st.title)}</h3><p>${escHtml(st.text)}</p>
      <div class="tour-foot"><div class="tour-dots">${this.steps.map((_, k) => `<i class="${k === this.i ? 'now' : ''}"></i>`).join('')}</div>
      ${this.i > 0 ? '<button class="btn btn-ghost btn-sm" data-tour="back">Back</button>' : '<button class="btn btn-ghost btn-sm" data-tour="end">Skip</button>'}
      <button class="btn btn-primary btn-sm" data-tour="next">${last ? 'Done' : 'Next'}</button></div>`;
    const pw = Math.min(320, innerWidth - 24), ph = this.pop.offsetHeight || 150;
    let x, y;
    if (!r) { x = (innerWidth - pw) / 2; y = Math.max(60, innerHeight * 0.3); }
    else if (st.side === 'right' && r.right + pw + 24 < innerWidth) { x = r.right + 18; y = Math.min(Math.max(12, r.top), innerHeight - ph - 12); }
    else { x = Math.min(Math.max(12, r.left + r.width / 2 - pw / 2), innerWidth - pw - 12); y = r.bottom + 16; if (y + ph > innerHeight - 12) y = Math.max(12, r.top - ph - 16); }
    Object.assign(this.pop.style, { left: `${x}px`, top: `${y}px` });
    this.pop.querySelector('[data-tour="next"]').focus();
  },
  end() {
    document.removeEventListener('keydown', this.key);
    window.removeEventListener('resize', this.place);
    [this.dim, this.hole, this.pop].forEach(n => n?.remove());
    this.pop = null;
    Prefs.save({ tutorial_done: true });
  },
};
