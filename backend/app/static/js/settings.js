/* imPress v2.2 settings: profile, appearance, accessibility, dates and times, dashboard, advanced mode, security.
 * Every control applies the moment it changes and is saved to the account (Prefs.save). Replaces renderSettings in app.js. */

const SECTIONS = [
  ['profile', 'Profile', 'user'], ['appearance', 'Appearance', 'palette', 'personalization'], ['accessibility', 'Accessibility', 'accessibility', 'accessibility'],
  ['datetime', 'Date and time', 'calendar', 'personalization'], ['dashboard', 'Dashboard', 'layout', 'dashboard_widgets'],
  ['advanced', 'Advanced mode', 'sliders', 'advanced_mode', 'admin'], ['security', 'Security', 'shield'],
];

function setRow(title, sub, control, id = '') {
  return `<div class="set-row"${id ? ` id="${id}"` : ''}><div class="pt"><b>${escHtml(title)}</b>${sub ? `<span>${escHtml(sub)}</span>` : ''}</div>${control}</div>`;
}
const seg = (key, options, current) => `<div class="segmented" role="radiogroup">${options.map(([v, t]) => `<button type="button" role="radio" aria-checked="${String(current) === String(v)}" class="${String(current) === String(v) ? 'active' : ''}" data-action="pref-pick" data-key="${key}" data-v="${v}">${t}</button>`).join('')}</div>`;
const sw = (key, on, onV = true, offV = false, label = '') => `<label class="switch"><input type="checkbox" role="switch" data-change="pref" data-key="${key}" data-on="${onV}" data-off="${offV}" ${on ? 'checked' : ''} aria-label="${escHtml(label || key)}"><i></i></label>`;
const sel = (key, options, current) => `<select class="input-sm" style="width:auto" data-change="pref" data-key="${key}" aria-label="${escHtml(key)}">${options.map(([v, t]) => `<option value="${v}" ${String(current) === String(v) ? 'selected' : ''}>${t}</option>`).join('')}</select>`;

function settingsSections(user) {
  const p = Prefs.cur, f = System.feature_flags || {}, admin = isAdminUser(user), s = Prefs.sample();
  const show = (flag) => !flag || f[flag] !== false;
  const out = {};
  out.profile = `<div class="card" id="sec-profile"><div class="card-header"><div><h2>${icon('user')} Profile</h2><div class="card-sub">How you appear to other people.</div></div></div>
    <form id="profile-form" class="form-grid" novalidate>
      <label>Username<input type="text" value="${escHtml(user.username)}" disabled><span class="form-hint">You sign in with this. An administrator can change it.</span></label>
      <label>Display name<input type="text" id="set-display" maxlength="64" value="${escHtml(user.display_name || '')}" placeholder="${escHtml(user.full_name || user.username)}"><span class="form-hint">Shown in the app. Leave empty to use your full name.</span></label>
      <label>Full name<input type="text" id="set-full" value="${escHtml(user.full_name || '')}"></label>
      <label>E-mail<input type="email" value="${escHtml(user.email)}" disabled></label>
      <div class="flex gap-1"><button class="btn btn-primary" type="submit">${icon('check', 'sm')} Save profile</button><span class="badge badge-primary">${escHtml(roleTitle(user))}</span></div>
    </form></div>`;
  out.appearance = `<div class="card" id="sec-appearance"><div class="card-header"><div><h2>${icon('palette')} Appearance</h2><div class="card-sub">Colours and layout. Changes apply straight away.</div></div></div>
    ${setRow('Theme', 'Light, dark, or follow your device', `<div class="theme-choices" style="width:min(330px,100%)">${[['light', 'Light'], ['dark', 'Dark'], ['system', 'Auto']].map(([k, t]) =>
      `<button type="button" class="theme-choice ${p.theme === k ? 'active' : ''}" data-action="pref-pick" data-key="theme" data-v="${k}"><div class="sw ${k}"></div>${t}</button>`).join('')}</div>`)}
    ${setRow('Accent colour', 'Buttons, links and highlights', `<div><div class="swatches">${Object.entries(Prefs.ACCENTS).map(([k, v]) => `<button type="button" class="swatch ${p.accent === k && !p.accent_custom ? 'active' : ''}" style="background:${v}" data-action="pref-pick" data-key="accent" data-v="${k}" aria-label="${k}" title="${k}"></button>`).join('')}
      <label class="swatch" style="background:conic-gradient(red,yellow,lime,aqua,blue,magenta,red);overflow:hidden" title="Choose any colour"><input type="color" value="${p.accent_custom || Prefs.ACCENTS[p.accent] || '#5b4ee5'}" data-change="pref-color" style="opacity:0;width:100%;height:100%;cursor:pointer" aria-label="Custom accent colour"></label></div></div>`)}
    ${setRow('Density', 'How much room there is between things', seg('density', [['comfortable', 'Comfortable'], ['compact', 'Compact']], p.density))}
    ${setRow('Collapse the sidebar', 'Show only icons (press [ to toggle)', sw('sidebar_collapsed', p.sidebar_collapsed, true, false, 'Collapse the sidebar'))}
    <div class="preview-strip mt-1"><button class="btn btn-primary btn-sm">Primary</button><button class="btn btn-outline btn-sm">Secondary</button>${statusPill('ok', 'Healthy')}${statusPill('warn', 'Attention')}${statusPill('bad', 'Problem')}<span class="badge badge-primary">Badge</span></div></div>`;
  out.accessibility = `<div class="card" id="sec-accessibility"><div class="card-header"><div><h2>${icon('accessibility')} Accessibility</h2><div class="card-sub">imPress works with screen readers and the keyboard. These settings help further.</div></div></div>
    ${setRow('Reduce motion', 'Turns animations and transitions off', sw('motion', p.motion === 'reduce', 'reduce', 'system', 'Reduce motion'))}
    ${setRow('Increase contrast', 'Stronger text, borders and focus outlines', sw('contrast', p.contrast === 'high', 'high', 'normal', 'Increase contrast'))}
    ${setRow('Text size', 'Makes everything smaller or larger', seg('scale', [['small', 'Smaller'], ['default', 'Default'], ['large', 'Larger'], ['xlarge', 'Largest']], p.scale))}
    ${setRow('Colour vision', 'Uses colours that are easier to tell apart. Statuses also carry a shape.', sel('vision', [['none', 'Standard'], ['protanopia', 'Protanopia (red-weak)'], ['deuteranopia', 'Deuteranopia (green-weak)'], ['tritanopia', 'Tritanopia (blue-weak)'], ['monochrome', 'Monochrome']], p.vision))}
    <div class="trash-note mt-1" style="margin-bottom:0">${icon('info', 'sm')}<span>For screen readers: pages have landmarks and headings, controls have labels, dialogs trap focus and updates are announced. Press <kbd>?</kbd> for the keyboard shortcuts.</span></div></div>`;
  out.datetime = `<div class="card" id="sec-datetime"><div class="card-header"><div><h2>${icon('calendar')} Date and time</h2><div class="card-sub">Times are shown in Indian Standard Time. Choose how they are written.</div></div></div>
    ${setRow('Date format', 'How dates are written', sel('date_format', [['dmy', '31/12/2026'], ['mdy', '12/31/2026'], ['ymd', '2026/12/31'], ['long', '31 Dec 2026'], ['iso', '2026-12-31']], p.date_format))}
    ${setRow('Time format', '24-hour or 12-hour clock', seg('time_format', [['24h', '24-hour'], ['12h', '12-hour']], p.time_format))}
    ${setRow('Show seconds', 'Add seconds to times', sw('show_seconds', p.show_seconds, true, false, 'Show seconds'))}
    ${setRow('Week starts on', 'Used in timetables', sel('week_start', [['monday', 'Monday'], ['sunday', 'Sunday'], ['saturday', 'Saturday']], p.week_start))}
    ${setRow('Numbers', 'Thousands and decimal separators', sel('number_format', [['1,234.5', '1,234.5'], ['1.234,5', '1.234,5'], ['1 234,5', '1 234,5']], p.number_format))}
    ${setRow('Relative times', 'Show "5 min ago" instead of the exact time', sw('relative_times', p.relative_times, true, false, 'Relative times'))}
    ${setRow('Start page', 'Where you land after signing in', sel('landing', [['overview', 'Overview'], ['classrooms', 'Classrooms'], ...(admin ? [['students', 'Students']] : [])], p.landing))}
    <div class="preview-strip mt-1" id="dt-preview"><span class="chip">${icon('calendar', 'sm')} ${escHtml(s.date)}</span><span class="chip">${icon('clock', 'sm')} ${escHtml(s.time)}</span><span class="chip">${icon('hash' in ICONS ? 'hash' : 'chart', 'sm')} ${escHtml(s.number)}</span></div></div>`;
  out.dashboard = `<div class="card" id="sec-dashboard"><div class="card-header"><div><h2>${icon('layout')} Dashboard</h2><div class="card-sub">Add, remove, resize and move widgets on your overview page.</div></div></div>
    ${setRow('Edit your dashboard', 'Opens the overview in edit mode', `<a class="btn btn-outline btn-sm" href="${admin ? '#/admin' : '#/dashboard'}" data-action="dash-edit-soon">${icon('layout', 'sm')} Customise</a>`)}
    ${setRow('Reset to the default layout', 'Removes your changes', `<button class="btn btn-outline btn-sm" data-action="dash-reset-settings">${icon('undo', 'sm')} Reset</button>`)}</div>`;
  out.advanced = `<div class="card" id="sec-advanced"><div class="card-header"><div><h2>${icon('sliders')} Advanced mode</h2><div class="card-sub">For administrators who want the detail.</div></div></div>
    ${setRow('Advanced mode', 'Shows detailed statistics on the dashboard (extra figures, account safety, unusual traffic). Off keeps it simple. Saved for your account only.', sw('advanced', p.advanced, true, false, 'Advanced mode'))}</div>`;
  out.security = `<div class="card" id="sec-security"><div class="card-header"><div><h2>${icon('shield')} Security</h2><div class="card-sub">Your password and this sign-in.</div></div></div>
    <form id="pw-form" class="form-grid" novalidate style="max-width:420px">
      <label>Current password<input type="password" id="pw-cur" autocomplete="current-password" required></label>
      <label>New password<input type="password" id="pw-new" autocomplete="new-password" required>${passwordMeterHtml('pw-new')}</label>
      <label>Type it again<input type="password" id="pw-again" autocomplete="new-password" required></label>
      <p id="pw-err" class="callout danger hidden" role="alert"></p>
      <div><button class="btn btn-primary" type="submit">${icon('lock', 'sm')} Change password</button></div></form>
    ${user.role === 'super_admin' ? `<h3 class="mt-2 mb-1">Two-step verification</h3><div id="mfa-box" class="text-muted">Loading…</div>` : ''}
    <h3 class="mt-2 mb-1">This sign-in</h3><dl class="kv" id="sess-info"><dt>Session</dt><dd>Loading…</dd></dl></div>`;
  return SECTIONS.filter(([id, , , flag, perm]) => show(flag) && (perm !== 'admin' || admin)).map(([id]) => out[id]).join('');
}

async function renderSettings(app, params) {
  const user = await authApi.me();
  Shell.user = user;
  const admin = isAdminUser(user), f = System.feature_flags || {};
  const nav = SECTIONS.filter(([, , , flag, perm]) => (!flag || f[flag] !== false) && (perm !== 'admin' || admin));
  app.innerHTML = `${renderNavbar(user, '#/settings')}
    <div class="container">
      ${pageHeader('Settings', 'Make imPress comfortable for you. Everything here applies at once and follows your account.', '', 'Account')}
      <div class="settings-layout">
        <nav class="settings-nav" aria-label="Settings sections">${nav.map(([id, t, ic], i) => `<a href="#sec-${id}" data-action="settings-jump" data-id="${id}" class="${i === 0 ? 'active' : ''}">${icon(ic, 'sm')} ${t}</a>`).join('')}</nav>
        <div id="settings-body">${settingsSections(user)}</div>
      </div></div>`;
  wireSettings(user);
  apiRequest('/auth/session').then(si => {
    const el = document.getElementById('sess-info');
    if (!el) return;
    el.innerHTML = `<dt>Signed in</dt><dd>${istDateTime(istParseToEpoch(si.created_at))}</dd><dt>Idle sign-out after</dt><dd>${Math.round(si.idle_timeout_s / 60)} minutes</dd>
      <dt>Session ID (1PSID)</dt><dd><code>${escHtml(si.psid)}</code> <span class="text-muted text-sm">changes every time the server restarts</span></dd><dt>Server run</dt><dd><code>${escHtml(si.server_run)}</code></dd>`;
  }).catch(() => {});
}

function refreshSettingsPreview() {
  const s = Prefs.sample(), el = document.getElementById('dt-preview');
  if (el) el.innerHTML = `<span class="chip">${icon('calendar', 'sm')} ${escHtml(s.date)}</span><span class="chip">${icon('clock', 'sm')} ${escHtml(s.time)}</span><span class="chip">${icon('chart', 'sm')} ${escHtml(s.number)}</span>`;
}

function parsePref(raw) { return raw === 'true' ? true : raw === 'false' ? false : raw; }

Object.assign(Actions, {
  'pref-pick': async (el, e) => {
    const patch = { [el.dataset.key]: parsePref(el.dataset.v) };
    if (el.dataset.key === 'accent') patch.accent_custom = '';
    await Prefs.save(patch, e);
    rerenderSettings();
  },
  'settings-jump': (el, e) => {
    e.preventDefault();
    document.querySelectorAll('.settings-nav a').forEach(a => a.classList.toggle('active', a === el));
    document.getElementById(`sec-${el.dataset.id}`)?.scrollIntoView({ behavior: Prefs.reduced() ? 'auto' : 'smooth', block: 'start' });
  },
  'dash-reset-settings': async () => { await Prefs.save({ dashboard: [] }); showToast('Your dashboard is back to the default layout.', 'success'); },
  'dash-edit-soon': () => { setTimeout(() => { if (typeof Dash !== 'undefined') Actions['dash-edit'](); }, 700); },
});
Actions['pref'] = async (el, e) => {
  const key = el.dataset.key;
  const v = el.type === 'checkbox' ? parsePref(el.checked ? el.dataset.on : el.dataset.off) : parsePref(el.value);
  await Prefs.save({ [key]: v }, e);
  if (['date_format', 'time_format', 'show_seconds', 'number_format'].includes(key)) refreshSettingsPreview();
  if (key === 'vision' || key === 'sidebar_collapsed') rerenderSettings();
};
Actions['pref-color'] = (el, e) => Prefs.save({ accent_custom: el.value }, e);

function rerenderSettings() {
  if (getRoute() !== '#/settings') return;
  const y = window.scrollY;
  const body = document.getElementById('settings-body');
  if (body && Shell.user) { body.innerHTML = settingsSections(Shell.user); wireSettings(Shell.user); window.scrollTo(0, y); }
}

function wireSettings(user) {
  const profile = document.getElementById('profile-form');
  profile?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const me = await authApi.updateProfile(document.getElementById('set-full').value.trim(), document.getElementById('set-display').value.trim());
      Shell.user = { ...user, ...me };
      showToast('Profile saved', 'success');
    } catch (err) { showToast(err.message, 'error'); }
  });
  if (document.getElementById('mfa-box')) renderMfa();
  const nu = document.getElementById('pw-new');
  if (nu) wirePasswordMeter(nu, 'pw-new', user.username, user.role);
  document.getElementById('pw-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const err = document.getElementById('pw-err'), cur = document.getElementById('pw-cur').value, pw = nu.value, again = document.getElementById('pw-again').value;
    const bad = (m) => { err.textContent = m; err.classList.remove('hidden'); };
    err.classList.add('hidden');
    const why = passwordProblem(pw, user.username, user.role);
    if (!cur) return bad('Enter your current password.');
    if (why) return bad(`That password ${why}.`);
    if (pw !== again) return bad('The two passwords do not match.');
    try {
      await authApi.changePassword(cur, pw);
      showToast('Password changed. Your other sessions were signed out.', 'success');
      e.target.reset();
      wirePasswordMeter(nu, 'pw-new', user.username, user.role);
    } catch (ex) { bad(ex.message); }
  });
}

// ── Two-step verification (#211): set up an authenticator app, recovery codes, turn off ──
async function renderMfa() {
  const box = document.getElementById('mfa-box');
  if (!box) return;
  let m;
  try { m = await mfaApi.status(); } catch (e) { box.textContent = 'Not available.'; return; }
  box.innerHTML = m.enrolled
    ? `<p>${statusPill('ok', 'On')} Every approval asks for a code from your app as well as your password. ${m.recovery_codes_left} recovery code${m.recovery_codes_left === 1 ? '' : 's'} left.</p>
       <button class="btn btn-outline btn-sm" data-action="mfa-codes">${icon('refresh', 'sm')} New recovery codes</button>
       ${m.required ? '<span class="text-muted text-sm"> Required by policy: it cannot be turned off.</span>' : `<button class="btn btn-outline btn-sm" data-action="mfa-off">${icon('x', 'sm')} Turn off</button>`}`
    : `<p>${statusPill('warn', 'Off')} ${m.required ? 'Policy requires it: you cannot request or approve dangerous actions until you set it up.' : 'Adds a code from an authenticator app to every approval.'}</p>
       <button class="btn btn-primary btn-sm" data-action="mfa-setup">${icon('shield', 'sm')} Set up</button>`;
}
function showRecoveryCodes(codes) {
  return askDialog({ title: 'Your recovery codes', confirm: 'I have saved them', cancel: '',
    body: `<p>Each works once, if you lose your phone. They are shown <b>only now</b>: keep them somewhere safe.</p><pre class="mono" style="user-select:all">${codes.map(escHtml).join('\n')}</pre>`, fields: [] });
}
Object.assign(Actions, {
  'mfa-setup': async () => {
    const v = await askDialog({ title: 'Set up two-step verification', confirm: 'Continue', body: 'Enter your password to start.',
      fields: [{ name: 'password', label: 'Your password', type: 'password', autocomplete: 'current-password' }], validate: (x) => x.password.length > 0 });
    if (!v) return;
    try {
      const s = await mfaApi.setup(v.password);
      const c = await askDialog({ title: 'Add it to your app', confirm: 'Turn on',
        body: `<p>In an authenticator app (any that supports TOTP), add an account by <b>entering this key</b>:</p><p><code style="user-select:all;word-break:break-all">${escHtml(s.secret)}</code></p><p class="text-muted text-sm">Or open this link on the phone: <a href="${escHtml(s.uri)}">${escHtml(s.uri.slice(0, 40))}…</a></p><p>Then type the 6-digit code it shows.</p>`,
        fields: [{ name: 'code', label: 'Code', type: 'text', autocomplete: 'one-time-code' }], validate: (x) => x.code.trim().length >= 6 });
      if (!c) return;
      const r = await mfaApi.enable(c.code);
      await showRecoveryCodes(r.recovery_codes);
      showToast('Two-step verification is on', 'success'); renderMfa();
    } catch (err) { showToast(err.message, 'error'); }
  },
  'mfa-off': async () => {
    const v = await askDialog({ title: 'Turn off two-step verification', confirm: 'Turn off', body: 'Enter your password and a code.',
      fields: [{ name: 'password', label: 'Your password', type: 'password', autocomplete: 'current-password' }, CODE_FIELD], validate: (x) => x.password && x.code });
    if (!v) return;
    try { await mfaApi.disable(v.password, v.code); showToast('Turned off', 'success'); renderMfa(); } catch (err) { showToast(err.message, 'error'); }
  },
  'mfa-codes': async () => {
    const v = await askDialog({ title: 'New recovery codes', confirm: 'Make new codes', body: 'The old codes stop working.',
      fields: [{ name: 'password', label: 'Your password', type: 'password', autocomplete: 'current-password' }, CODE_FIELD], validate: (x) => x.password && x.code });
    if (!v) return;
    try { const r = await mfaApi.recovery(v.password, v.code); await showRecoveryCodes(r.recovery_codes); renderMfa(); } catch (err) { showToast(err.message, 'error'); }
  },
});
