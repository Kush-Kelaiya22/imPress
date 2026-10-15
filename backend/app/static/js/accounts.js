/* imPress v2.2 accounts: add (generated or typed first password), temporary credentials shown once, display names, teaching
 * assistants, role changes with confirmation, disable / enable, a 30-day trash, who is active now, and a per-account
 * activity history with charts. Replaces the v2.1 user pages in pages.js and the user actions in app.js. */

Object.assign(UserView, { sub: 'people' });
const RISK_CLASS = { 'Safe': 'safe', 'Potentially Unsafe': 'potentially', 'Likely Compromised': 'compromised' };
let _risk = {};

function userStatus(u) {
  if (!u.is_active) return statusPill('off', 'Disabled');
  if (u.status === 'pending_setup') return statusPill('pending', 'Pending setup');
  return statusPill('active', 'Active');
}

function roleBadge(u) {
  const ic = { super_admin: 'crown', admin: 'shield', teacher: u.designation === 'ta' ? 'userCheck' : 'users' }[u.role] || 'user';
  return `<span class="role ${escHtml(u.role)}${u.designation === 'ta' ? ' ta' : ''}">${icon(ic, 'sm')} ${escHtml(roleTitle(u))}</span>`;
}

function riskBadge(id) {
  const r = _risk[id];
  if (!r) return '<span class="text-muted">—</span>';
  return `<span class="risk ${RISK_CLASS[r.label] || 'safe'}" tabindex="0" role="note" aria-label="${escHtml(r.label)}, score ${r.score}">${icon(r.label === 'Safe' ? 'shieldCheck' : 'alert', 'sm')} ${escHtml(r.label)}
    <span class="tip" role="tooltip"><b>Score ${r.score} of 100</b><br>${r.reasons.map(escHtml).join('<br>')}</span></span>`;
}

// ── Page ───────────────────────────────────────────────────────────

async function renderAdminActivity(app) { UserView.tab = 'activity'; return renderUserAccess(app, '#/admin/activity'); }
async function renderAdminUsers(app) { if (getRoute() === '#/admin/users') UserView.tab = 'users'; return renderUserAccess(app, '#/admin/users'); }

async function renderUserAccess(app, hash) {
  const user = await authApi.me();
  const f = System.feature_flags || {};
  const sub = UserView.tab === 'users' ? UserView.sub : 'activity';
  const [users, activity, risk, presence, trash] = await Promise.all([
    adminApi.listUsers(), UserView.tab === 'activity' || sub === 'people' ? adminApi.activityLogs(200) : Promise.resolve([]),
    f.risk_scores === false ? Promise.resolve({}) : adminApi.risk().catch(() => ({})),
    sub === 'active' && f.presence !== false ? adminApi.presence().catch(() => null) : Promise.resolve(null),
    sub === 'deleted' && f.trash !== false ? adminApi.trash().catch(() => null) : Promise.resolve(null),
  ]);
  _risk = risk || {};
  const isSuper = user.role === 'super_admin';
  const tabs = [['people', 'Accounts', 'users', '#/admin/users'], ['active', 'Active now', 'activity', '#/admin/users', f.presence !== false],
    ['deleted', 'Deleted', 'trash', '#/admin/users', f.trash !== false], ['activity', 'Activity log', 'history', '#/admin/activity']].filter(t => t[4] !== false);
  app.innerHTML = `
    ${renderNavbar(user, hash)}
    <div class="container">
      ${pageHeader('User access', 'Add and manage accounts, see who is signed in, and review what happens in the workspace.', '', 'Administration')}
      <div class="tabs" role="tablist">${tabs.map(([k, t, ic, href]) => `<button class="tab ${sub === k ? 'active' : ''}" role="tab" aria-selected="${sub === k}" data-action="usr-sub" data-sub="${k}" data-href="${href}">${icon(ic, 'sm')} ${t}</button>`).join('')}</div>
      ${sub === 'people' ? peoplePanel(users, user) : sub === 'active' ? activePanel(presence, users) : sub === 'deleted' ? deletedPanel(trash) : ''}
      ${sub === 'people' ? activityPanel(activity, users, true) : sub === 'activity' ? activityPanel(activity, users, false) : ''}
    </div>
    ${sub === 'people' ? userModals(isSuper, user) : ''}`;
  if (sub === 'people') { wireUsers(app, users, user); wireActivity(activity); wireUserForms(app, user); }
  else if (sub === 'activity') wireActivity(activity);
}

Actions['usr-sub'] = (el) => {
  if (el.dataset.sub === 'activity') { navigate('#/admin/activity'); return; }
  UserView.tab = 'users'; UserView.sub = el.dataset.sub;
  if (getRoute() !== '#/admin/users') navigate('#/admin/users'); else router();
};

function peoplePanel(users, me) {
  const counts = { pending: users.filter(u => u.status === 'pending_setup').length };
  return `<div class="card">
    <div class="card-header"><div><h2>Accounts</h2><div class="card-sub">${users.length} accounts${counts.pending ? ` · ${counts.pending} waiting to finish setting up` : ''}</div></div>
      <div class="page-actions">
        <label class="searchbox" style="width:230px">${icon('search', 'sm')}<span class="sr-only">Search accounts</span><input id="usr-q" type="search" placeholder="Search accounts" value="${escHtml(UserView.q)}" data-live="1"></label>
        <select id="usr-role" class="input-sm" style="width:auto" aria-label="Filter accounts">
          ${[['all', 'Everyone'], ['super_admin', 'Super admins'], ['admin', 'Administrators'], ['teacher', 'Faculty'], ['ta', 'Teaching assistants'], ['pending', 'Pending setup'], ['inactive', 'Disabled']].map(([k, t]) => `<option value="${k}" ${UserView.role === k ? 'selected' : ''}>${t}</option>`).join('')}
        </select>
        <button class="btn btn-outline btn-sm" id="btn-import-users-csv">${icon('upload', 'sm')} Import CSV</button>
        <button class="btn btn-primary btn-sm" data-action="show" data-target="#create-user-modal">${icon('userPlus', 'sm')} Add account</button>
      </div></div>
    <div class="card hidden" id="users-csv-card" style="box-shadow:none;background:var(--surface-2)">
      <div class="card-header"><h2>Import accounts from CSV</h2><button class="btn btn-sm btn-ghost btn-icon" aria-label="Close" data-action="hide" data-target="#users-csv-card">${icon('x', 'sm')}</button></div>
      <p class="form-hint">Every row needs all five columns: <b>username</b> (3–64 letters, digits, _ .), <b>email</b>, <b>password</b> (8+ characters with upper and lower case, a number and a special character), <b>full_name</b>, <b>role</b> (teacher or admin; admin needs a super admin). Imported accounts must choose their own password at first sign-in.</p>
      <div class="csv-drop" id="users-csv-drop">${icon('upload', 'lg')}<p style="margin:6px 0">Drop a CSV file here or click to browse</p>
        <input type="file" id="users-csv-file" accept=".csv" style="display:none" /><button class="btn btn-sm btn-outline" id="users-csv-browse">Choose file</button></div>
      <div id="users-csv-result" class="mt-1"></div>
      <div class="mt-1"><button class="btn btn-primary btn-sm" id="users-csv-upload" disabled>Upload &amp; import</button></div>
    </div>
    <div id="usr-table"></div>
  </div>`;
}

function userRow(u, me) {
  const a = new Set(u.allowed_actions || []);
  const f = System.feature_flags || {};
  const isSuper = me.role === 'super_admin';
  const items = [
    a.has('edit') && `<button role="menuitem" data-action="usr-edit" data-id="${u.id}">${icon('edit', 'sm')} Edit details</button>`,
    f.activity_charts !== false && `<button role="menuitem" data-action="usr-activity" data-id="${u.id}">${icon('chart', 'sm')} Activity history</button>`,
    a.has('change_role') && u.role !== 'super_admin' && `<button role="menuitem" data-action="usr-role" data-id="${u.id}">${icon('swap', 'sm')} ${u.role === 'admin' ? 'Make faculty' : 'Make administrator'}</button>`,
    a.has('edit') && u.role === 'teacher' && f.ta_designation !== false && `<button role="menuitem" data-action="usr-ta" data-id="${u.id}">${icon('userCheck', 'sm')} ${u.designation === 'ta' ? 'Make faculty' : 'Make teaching assistant'}</button>`,
    a.has('reset_password') && `<button role="menuitem" data-action="usr-reset" data-id="${u.id}">${icon('key', 'sm')} Reset password</button>`,
    isSuper && u.signed_in && u.id !== me.id && `<button role="menuitem" data-action="usr-end" data-id="${u.id}">${icon('logout', 'sm')} Sign out everywhere</button>`,
    a.has('delete') && `<hr><button role="menuitem" class="danger" data-action="usr-delete" data-id="${u.id}">${icon('trash', 'sm')} Delete account</button>`,
  ].filter(Boolean).join('');
  const toggle = a.has('deactivate') ? `<button class="btn btn-sm btn-outline btn-icon" title="Disable" aria-label="Disable ${escHtml(u.username)}" data-action="usr-active" data-id="${u.id}" data-active="false">${icon('userX', 'sm')}</button>`
    : a.has('reactivate') ? `<button class="btn btn-sm btn-outline btn-icon" title="Enable" aria-label="Enable ${escHtml(u.username)}" data-action="usr-active" data-id="${u.id}" data-active="true">${icon('userCheck', 'sm')}</button>` : '';
  return `<tr data-user="${u.id}">
    <td><div class="cell-person">${avatar(u.name || u.username)}<div><b>${escHtml(u.name || u.username)}${u.signed_in ? ' <span class="pres-dot" title="Signed in now"></span>' : ''}</b><span>${escHtml(u.email)} · @${escHtml(u.username)}</span></div></div></td>
    <td>${roleBadge(u)}</td>
    <td class="nowrap col-wide">${u.role === 'teacher' ? `${u.class_count} classroom${u.class_count === 1 ? '' : 's'}` : 'All classrooms'}</td>
    <td>${userStatus(u)}</td>
    ${f.risk_scores !== false ? `<td>${riskBadge(u.id)}</td>` : ''}
    <td class="text-sm nowrap">${u.last_active_at ? timeAgo(istParseToEpoch(u.last_active_at)) : 'Never'}</td>
    <td><div class="row-actions">${u.id === me.id ? '<span class="text-muted text-sm">You</span>' : ''}${toggle}
      ${items ? `<div class="menu-wrap kebab"><button class="btn btn-sm btn-ghost btn-icon" data-action="toggle-menu" data-menu="um-${u.id}" aria-haspopup="menu" aria-label="More actions for ${escHtml(u.username)}">${icon('more', 'sm')}</button>
        <div id="um-${u.id}" class="menu hidden" role="menu">${items}</div></div>` : ''}</div></td></tr>`;
}

function wireUsers(app, users, me) {
  const f = System.feature_flags || {};
  const draw = () => {
    const q = UserView.q.toLowerCase();
    const match = (u) => ({ all: true, inactive: !u.is_active, pending: u.status === 'pending_setup', ta: u.designation === 'ta', teacher: u.role === 'teacher' && u.designation !== 'ta' }[UserView.role] ?? u.role === UserView.role);
    const rows = users.filter(u => match(u) && (!q || `${u.username} ${u.name || ''} ${u.full_name || ''} ${u.email}`.toLowerCase().includes(q)));
    const pg = paginate(rows, UserView.page, 10);
    UserView.page = pg.page;
    document.getElementById('usr-table').innerHTML = rows.length ? `<div class="table-wrap"><table class="table">
      <thead><tr><th>Person</th><th>Role</th><th class="col-wide">Classrooms</th><th>Status</th>${f.risk_scores !== false ? '<th>Safety</th>' : ''}<th>Last active</th><th></th></tr></thead>
      <tbody>${pg.rows.map(u => userRow(u, me)).join('')}</tbody></table></div>
      <div class="table-foot"><span>Showing ${(pg.page - 1) * 10 + 1}–${(pg.page - 1) * 10 + pg.rows.length} of ${rows.length}</span>${pagerHtml(pg, rows.length, 10, 'usersPage')}</div>`
      : emptyState('No accounts match', 'Change the search or the filter.', 'users');
  };
  window.usersPage = (p) => { UserView.page = p; draw(); };
  document.getElementById('usr-q').oninput = (e) => { UserView.q = e.target.value; e.target.defaultValue = e.target.value; UserView.page = 1; draw(); };
  document.getElementById('usr-role').onchange = (e) => { UserView.role = e.target.value; UserView.page = 1; draw(); };
  draw();
  window._users = users;
}

const userById = (id) => (window._users || []).find(u => String(u.id) === String(id));
const reloadUsers = () => renderUserAccess(document.getElementById('app'), getRoute());

// ── Temporary credentials: shown once ─────────────────────────────

function showCredentials({ title, name, username, password, note }) {
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class="modal-backdrop"></div><div class="modal-content card" role="dialog" aria-modal="true" aria-label="${escHtml(title)}">
    <div class="big-ic info" style="width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:var(--success-soft);color:var(--success);margin-bottom:10px">${icon('checkCircle', 'lg')}</div>
    <h2>${escHtml(title)}</h2>
    <p class="text-muted">${escHtml(name)} (@${escHtml(username)}) signs in with this temporary password and then chooses their own. ${escHtml(note || '')}</p>
    <div class="copy-box"><span id="cred-pw">${escHtml(password)}</span><button class="btn btn-sm btn-outline" id="cred-copy">${icon('copy', 'sm')} Copy</button></div>
    <div class="confirm-warn">${icon('alert', 'sm')}<span>This is the only time it is shown. Hand it over in person or through a private channel.</span></div>
    <div class="modal-actions"><button class="btn btn-primary" id="cred-done">Done</button></div></div>`;
  document.body.appendChild(m);
  const done = () => { m.remove(); };
  m.querySelector('#cred-done').onclick = done;
  m.querySelector('#cred-copy').onclick = async (e) => {
    try { await navigator.clipboard.writeText(password); e.currentTarget.innerHTML = `${icon('check', 'sm')} Copied`; } catch { showToast('Select the password and copy it.', 'warning'); }
  };
  m.querySelector('#cred-done').focus();
}

// ── Add and edit ───────────────────────────────────────────────────

function userModals(isSuper, me) {
  return `
    <div id="create-user-modal" class="modal hidden"><div class="modal-backdrop" data-action="hide-parent"></div>
      <div class="modal-content card" role="dialog" aria-modal="true" aria-label="Add an account" style="max-width:560px"><h2>Add an account</h2>
        <p class="text-muted mb-1">They sign in with a temporary password and choose their own the first time.</p>
        <form id="create-user-form" novalidate>
          <div class="form-grid-2">
            <div class="form-group"><label for="new-fullname">Full name</label><input type="text" id="new-fullname" autocomplete="off" /></div>
            <div class="form-group"><label for="new-display">Display name <span class="text-muted">(optional)</span></label><input type="text" id="new-display" maxlength="64" autocomplete="off" /></div>
            <div class="form-group"><label for="new-username">Username</label><input type="text" id="new-username" required minlength="3" autocomplete="off" autocapitalize="none" spellcheck="false" /></div>
            <div class="form-group"><label for="new-email">E-mail</label><input type="email" id="new-email" required autocomplete="off" /></div>
          </div>
          <div class="form-grid-2">
            <div class="form-group"><label for="new-role">Role</label><select id="new-role"><option value="teacher">Faculty</option>${isSuper ? '<option value="admin">Administrator</option>' : ''}</select></div>
            <div class="form-group" id="new-desig-group"><label for="new-desig">Shown as</label><select id="new-desig"><option value="faculty">Faculty</option>${(System.feature_flags?.ta_designation !== false) ? '<option value="ta">Teaching assistant</option>' : ''}</select></div>
          </div>
          <div class="form-group"><label>First password</label>
            <div class="segmented" role="radiogroup" style="align-self:flex-start"><button type="button" class="active" data-pwmode="generate" role="radio" aria-checked="true">${icon('sparkles', 'sm')} Generate for me</button><button type="button" data-pwmode="manual" role="radio" aria-checked="false">${icon('key', 'sm')} I will type one</button></div>
            <div id="new-pw-wrap" class="hidden mt-1"><input type="password" id="new-password" autocomplete="new-password" placeholder="Temporary password">${passwordMeterHtml('new-password')}
              <span class="form-hint">8+ characters with upper and lower case, a number and a special character.</span></div>
            <span class="form-hint" id="new-pw-hint">A strong password is generated and shown once, after you add the account.</span></div>
          <p id="create-err" class="callout danger hidden" role="alert"></p>
          <div class="modal-actions"><button type="button" class="btn btn-outline" data-action="hide" data-target="#create-user-modal">Cancel</button>
            <button type="submit" class="btn btn-primary">Add account</button></div>
        </form></div></div>
    <div id="edit-user-modal" class="modal hidden"><div class="modal-backdrop" data-action="hide-parent"></div>
      <div class="modal-content card" role="dialog" aria-modal="true" aria-label="Edit account"><h2>Edit account</h2>
        <form id="edit-user-form"><input type="hidden" id="edit-user-id" />
          <div class="form-group"><label for="edit-username">Username</label><input type="text" id="edit-username" disabled /></div>
          <div class="form-grid-2"><div class="form-group"><label for="edit-fullname">Full name</label><input type="text" id="edit-fullname" /></div>
            <div class="form-group"><label for="edit-display">Display name</label><input type="text" id="edit-display" maxlength="64" /></div></div>
          <div class="form-group"><label for="edit-email">E-mail</label><input type="email" id="edit-email" required /></div>
          <div class="modal-actions"><button type="button" class="btn btn-outline" data-action="hide" data-target="#edit-user-modal">Cancel</button>
            <button type="submit" class="btn btn-primary">Save</button></div>
        </form></div></div>`;
}

function wireUserForms(app, me) {
  const form = document.getElementById('create-user-form');
  let mode = 'generate';
  const role = document.getElementById('new-role'), desigGroup = document.getElementById('new-desig-group'), pwWrap = document.getElementById('new-pw-wrap');
  const sync = () => desigGroup.classList.toggle('hidden', role.value !== 'teacher');
  role.onchange = sync; sync();
  wirePasswordMeter(document.getElementById('new-password'), 'new-password', () => document.getElementById('new-username').value, 'teacher');
  form.querySelectorAll('[data-pwmode]').forEach(b => b.onclick = () => {
    mode = b.dataset.pwmode;
    form.querySelectorAll('[data-pwmode]').forEach(x => { x.classList.toggle('active', x === b); x.setAttribute('aria-checked', x === b); });
    pwWrap.classList.toggle('hidden', mode !== 'manual');
    document.getElementById('new-pw-hint').classList.toggle('hidden', mode === 'manual');
    if (mode === 'manual') document.getElementById('new-password').focus();
  });
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const err = document.getElementById('create-err'), bad = (m) => { err.textContent = m; err.classList.remove('hidden'); };
    err.classList.add('hidden');
    const body = { username: document.getElementById('new-username').value.trim(), full_name: document.getElementById('new-fullname').value.trim(),
      display_name: document.getElementById('new-display').value.trim(), email: document.getElementById('new-email').value.trim(), role: role.value,
      designation: role.value === 'teacher' ? document.getElementById('new-desig').value : 'faculty' };
    if (!body.username || !body.email) return bad('Enter a username and an e-mail address.');
    if (mode === 'manual') {
      body.password = document.getElementById('new-password').value;
      const why = passwordProblem(body.password, body.username, body.role);
      if (why) return bad(`That password ${why}.`);
    }
    try {
      const r = await adminApi.createUser(body);
      document.getElementById('create-user-modal').classList.add('hidden');
      if (r.temporary_password) showCredentials({ title: 'Account added', name: r.name || r.username, username: r.username, password: r.temporary_password });
      else showToast(`${r.name || r.username} was added. They choose their own password at first sign-in.`, 'success');
      reloadUsers();
    } catch (ex) { bad(ex.message); }
  });
  // CSV import (unchanged from v2.1)
  const card = document.getElementById('users-csv-card'), drop = document.getElementById('users-csv-drop'), file = document.getElementById('users-csv-file');
  const upload = document.getElementById('users-csv-upload'), result = document.getElementById('users-csv-result');
  let chosen = null;
  document.getElementById('btn-import-users-csv').onclick = () => card.classList.toggle('hidden');
  document.getElementById('users-csv-browse').onclick = (e) => { e.stopPropagation(); file.click(); };
  drop.onclick = () => file.click();
  drop.ondragover = (e) => { e.preventDefault(); drop.style.borderColor = 'var(--primary)'; };
  drop.ondragleave = () => { drop.style.borderColor = ''; };
  drop.ondrop = (e) => { e.preventDefault(); drop.style.borderColor = ''; if (e.dataTransfer.files.length) { file.files = e.dataTransfer.files; file.dispatchEvent(new Event('change')); } };
  file.onchange = () => {
    const f = file.files[0];
    chosen = f && f.name.toLowerCase().endsWith('.csv') ? f : null;
    if (f && !chosen) showToast('Choose a .csv file', 'error');
    upload.disabled = !chosen;
    result.innerHTML = chosen ? `<p class="text-muted text-sm">Ready: ${escHtml(chosen.name)}</p>` : '';
  };
  upload.onclick = async () => {
    if (!chosen) return;
    upload.disabled = true;
    result.innerHTML = '<p class="text-muted text-sm">Importing…</p>';
    try {
      const r = await adminApi.importUsersCsv(chosen);
      showToast(`${r.inserted} account(s) imported${r.skipped.length ? `, ${r.skipped.length} skipped` : ''}`, r.skipped.length ? 'warning' : 'success');
      if (!r.skipped.length) { reloadUsers(); return; }
      result.innerHTML = `<p class="warn-line">${r.inserted} added, ${r.skipped.length} skipped:</p><div class="table-wrap"><table class="table">
        <thead><tr><th>Row</th><th>Username</th><th>Error</th></tr></thead>
        <tbody>${r.skipped.map(x => `<tr><td>${x.row}</td><td><code>${escHtml(x.roll_number)}</code></td><td class="text-sm">${escHtml(x.error)}</td></tr>`).join('')}</tbody></table></div>`;
    } catch (err) { result.innerHTML = ''; showToast(err.message, 'error'); } finally { upload.disabled = false; }
  };
}

// ── Row actions ────────────────────────────────────────────────────

const closeMenus = () => document.querySelectorAll('.kebab .menu').forEach(m => m.classList.add('hidden'));

Actions['usr-edit'] = (el) => {
  closeMenus();
  const u = userById(el.dataset.id), modal = document.getElementById('edit-user-modal');
  if (!u || !modal) return;
  document.getElementById('edit-user-id').value = u.id;
  document.getElementById('edit-username').value = u.username;
  document.getElementById('edit-fullname').value = u.full_name || '';
  document.getElementById('edit-display').value = u.display_name || '';
  document.getElementById('edit-email').value = u.email || '';
  modal.classList.remove('hidden');
  document.getElementById('edit-user-form').onsubmit = async (e) => {
    e.preventDefault();
    try {
      await adminApi.updateUser(u.id, { full_name: document.getElementById('edit-fullname').value.trim(), display_name: document.getElementById('edit-display').value.trim(),
        email: document.getElementById('edit-email').value.trim() });
      showToast('Account updated', 'success');
      modal.classList.add('hidden');
      reloadUsers();
    } catch (err) { showToast(err.message, 'error'); }
  };
};
window.editUser = (id) => Actions['usr-edit']({ dataset: { id } });

Actions['usr-active'] = async (el) => {
  const u = userById(el.dataset.id), on = el.dataset.active === 'true';
  if (!u) return;
  const ok = await askDialog({ title: on ? `Enable ${u.name || u.username}?` : `Disable ${u.name || u.username}?`, confirm: on ? 'Enable account' : 'Disable account', danger: !on,
    body: on ? 'They will be able to sign in again.' : 'They are signed out straight away and cannot sign in until the account is enabled again. If they are using imPress now, they will see a notice explaining why.' });
  if (!ok) return;
  try {
    await (on ? adminApi.reactivateUser(u.id) : adminApi.deactivateUser(u.id));
    showToast(`${u.name || u.username} was ${on ? 'enabled' : 'disabled'}.`, 'success');
    reloadUsers();
  } catch (err) { showToast(err.message, 'error'); }
};
window.setUserActive = (id, name, active) => Actions['usr-active']({ dataset: { id, active: String(active) } });

Actions['usr-reset'] = async (el) => {
  closeMenus();
  const u = userById(el.dataset.id);
  if (!u) return;
  const ok = await askDialog({ title: `Reset ${u.name || u.username}'s password?`, confirm: 'Generate a new password',
    body: 'A new temporary password is generated and shown once. They are signed out everywhere and must choose their own password the next time they sign in.' });
  if (!ok) return;
  try {
    const r = await adminApi.resetPassword(u.id);
    showCredentials({ title: 'New temporary password', name: u.name || u.username, username: u.username, password: r.temporary_password });
    reloadUsers();
  } catch (err) { showToast(err.message, 'error'); }
};
window.resetUserPassword = (id) => Actions['usr-reset']({ dataset: { id } });

Actions['usr-end'] = async (el) => {
  closeMenus();
  const u = userById(el.dataset.id);
  if (!u) return;
  const ok = await askDialog({ title: `Sign ${u.name || u.username} out everywhere?`, confirm: 'Sign out', danger: true,
    body: 'Every session of this account ends now. They can sign in again straight away.' });
  if (!ok) return;
  try { await adminApi.endSessions(u.id); showToast(`${u.name || u.username} was signed out everywhere.`, 'success'); reloadUsers(); } catch (err) { showToast(err.message, 'error'); }
};
window.endUserSessions = (id) => Actions['usr-end']({ dataset: { id } });

Actions['usr-role'] = async (el) => {
  closeMenus();
  const u = userById(el.dataset.id);
  if (!u) return;
  const to = u.role === 'admin' ? 'teacher' : 'admin', name = u.name || u.username;
  const ok = await askDialog({ title: `Change ${name}'s role?`, confirm: to === 'admin' ? 'Make administrator' : 'Make faculty', danger: to === 'teacher',
    body: to === 'admin'
      ? `<b>${escHtml(name)}</b> will become an <b>administrator</b>: they will manage accounts, devices and firmware, and see every classroom. They are signed out so the change takes effect.`
      : `<b>${escHtml(name)}</b> will become <b>faculty</b> and see only the classrooms they manage. They lose access to accounts, devices and the system. They are signed out so the change takes effect.` });
  if (!ok) return;
  try { await adminApi.changeRole(u.id, to); showToast(`${name} is now ${to === 'admin' ? 'an administrator' : 'faculty'}.`, 'success'); reloadUsers(); } catch (err) { showToast(err.message, 'error'); }
};

Actions['usr-ta'] = async (el) => {
  closeMenus();
  const u = userById(el.dataset.id);
  if (!u) return;
  const to = u.designation === 'ta' ? 'faculty' : 'ta', name = u.name || u.username;
  const ok = await askDialog({ title: to === 'ta' ? `Show ${name} as a teaching assistant?` : `Show ${name} as faculty?`, confirm: 'Confirm',
    body: `<div class="confirm-warn">${icon('alert', 'sm')}<span>This only changes how the account is shown. A teaching assistant has exactly the same permissions as faculty.</span></div>` });
  if (!ok) return;
  try { await adminApi.setDesignation(u.id, to); showToast(`${name} is shown as ${to === 'ta' ? 'a teaching assistant' : 'faculty'}.`, 'success'); reloadUsers(); } catch (err) { showToast(err.message, 'error'); }
};

Actions['usr-delete'] = async (el) => {
  closeMenus();
  const u = userById(el.dataset.id);
  if (!u) return;
  const ok = await askDialog({ title: `Delete ${u.name || u.username}?`, confirm: 'Delete account', danger: true,
    body: `The account moves to <b>Deleted</b> and can be restored for 30 days. After that it is removed permanently. Records they created stay; the activity log keeps their name.` });
  if (!ok) return;
  try { await adminApi.deleteUser(u.id); showToast(`${u.name || u.username} was deleted. You can restore the account for 30 days.`, 'success'); reloadUsers(); } catch (err) { showToast(err.message, 'error'); }
};
window.deleteUser = (id) => Actions['usr-delete']({ dataset: { id } });

// ── Active now and the trash ───────────────────────────────────────

function activePanel(p, users) {
  if (!p) return `<div class="card">${emptyState('Not available', 'Active users are switched off, or you may not view them.', 'activity')}</div>`;
  const row = (u, live) => `<div class="feed-item"><span style="position:relative">${avatar(u.name || u.username)}${live ? '<span class="pres-dot" style="position:absolute;right:-2px;bottom:-2px;border:2px solid var(--surface)"></span>' : ''}</span>
    <div class="feed-body"><b>${escHtml(u.name || u.username)}</b><span>@${escHtml(u.username)} · ${escHtml(roleTitle(u))}${live && u.ip ? ` · ${escHtml(u.ip)}` : ''}${live ? ` · signed in ${timeAgo(istParseToEpoch(u.signed_in_at))}` : ''}</span></div>
    <span class="feed-time">${live ? 'Active ' : 'Last seen '}${timeAgo(istParseToEpoch(u.last_active_at))}</span>
    ${(System.feature_flags?.activity_charts !== false) ? `<button class="btn btn-sm btn-outline" data-action="usr-activity" data-id="${u.id}">${icon('chart', 'sm')} History</button>` : ''}</div>`;
  return `<div class="grid-main"><div class="card"><div class="card-header"><div><h2>${icon('activity')} Signed in now</h2><div class="card-sub">${p.active.length} of ${p.total_accounts} accounts are active at this moment.</div></div>
      <button class="btn btn-sm btn-outline" data-action="usr-refresh">${icon('refresh', 'sm')} Refresh</button></div>
      ${p.active.length ? p.active.map(u => row(u, true)).join('') : emptyState('Nobody is signed in', '', 'users')}</div>
    <div class="card"><div class="card-header"><div><h2>Active in the last 24 hours</h2><div class="card-sub">Signed out since.</div></div></div>
      ${p.recent.length ? p.recent.map(u => row(u, false)).join('') : emptyState('Nobody else was active', '', 'clock')}</div></div>`;
}
Actions['usr-refresh'] = () => reloadUsers();

function deletedPanel(t) {
  if (!t) return `<div class="card">${emptyState('Not available', 'Deleted accounts are switched off.', 'trash')}</div>`;
  return `<div class="card"><div class="card-header"><div><h2>${icon('trash')} Deleted accounts</h2></div></div>
    <div class="trash-note">${icon('info', 'sm')}<span>Deleted accounts can be restored for ${t.retention_days} days. After that they are removed permanently.</span></div>
    ${t.accounts.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Account</th><th>Role</th><th>Deleted</th><th>Time left</th><th></th></tr></thead><tbody>${t.accounts.map(a => `<tr>
      <td><div class="cell-person">${avatar(a.name || a.username)}<div><b>${escHtml(a.name || a.username)}</b><span>@${escHtml(a.username)}</span></div></div></td>
      <td>${roleBadge(a)}</td><td class="text-sm">${timeAgo(istParseToEpoch(a.deleted_at))}${a.deleted_by ? ` by ${escHtml(a.deleted_by)}` : ''}</td>
      <td>${a.days_left} day${a.days_left === 1 ? '' : 's'}</td>
      <td><div class="row-actions"><button class="btn btn-sm btn-outline" data-action="usr-restore" data-id="${a.id}" data-name="${escHtml(a.name || a.username)}">${icon('undo', 'sm')} Restore</button>
        <button class="btn btn-sm btn-danger-ghost btn-icon" title="Delete forever" aria-label="Delete ${escHtml(a.username)} forever" data-action="usr-purge" data-id="${a.id}" data-name="${escHtml(a.name || a.username)}">${icon('trash', 'sm')}</button></div></td></tr>`).join('')}</tbody></table></div>`
      : emptyState('Nothing here', 'Accounts you delete appear here for 30 days.', 'trash')}</div>`;
}
Actions['usr-restore'] = async (el) => {
  try { await adminApi.restoreUser(el.dataset.id); showToast(`${el.dataset.name} was restored.`, 'success'); reloadUsers(); } catch (err) { showToast(err.message, 'error'); }
};
Actions['usr-purge'] = async (el) => {
  const ok = await askDialog({ title: `Delete ${el.dataset.name} permanently?`, confirm: 'Delete permanently', danger: true, body: 'This cannot be undone.' });
  if (!ok) return;
  try { await adminApi.purgeUser(el.dataset.id); showToast('Removed permanently.', 'success'); reloadUsers(); } catch (err) { showToast(err.message, 'error'); }
};

// ── Per-account activity history ───────────────────────────────────

Actions['usr-activity'] = (el) => { closeMenus(); openActivityDrawer(el.dataset.id, 30); };

async function openActivityDrawer(id, days) {
  document.getElementById('act-drawer')?.remove();
  const wrap = document.createElement('div');
  wrap.id = 'act-drawer';
  wrap.innerHTML = `<div class="drawer-back" data-close></div><aside class="drawer" role="dialog" aria-modal="true" aria-label="Activity history"><div class="skeleton" style="height:40px;margin-bottom:14px"></div><div class="skeleton" style="height:120px"></div></aside>`;
  document.body.appendChild(wrap);
  wrap.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) wrap.remove(); else { const d = e.target.closest('[data-days]'); if (d) openActivityDrawer(id, +d.dataset.days); } });
  let s;
  try { s = await adminApi.activitySummary(id, days); } catch (err) { wrap.remove(); showToast(err.message, 'error'); return; }
  const max = Math.max(...s.daily.map(d => d.count), 1), hmax = Math.max(...s.heatmap.flat(), 1);
  const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const u = s.user;
  wrap.querySelector('.drawer').innerHTML = `
    <div class="flex-between"><div class="cell-person">${avatar(u.name, 'lg')}<div><h2>${escHtml(u.name)}</h2><span class="text-muted">@${escHtml(u.username)} · ${escHtml(roleTitle(u))}</span></div></div>
      <button class="btn btn-ghost btn-icon" data-close aria-label="Close">${icon('x')}</button></div>
    <div class="flex gap-1 mt-1" style="flex-wrap:wrap">${_risk[id] ? riskBadge(id) : ''}<div class="segmented">${[7, 30, 90].map(d => `<button data-days="${d}" class="${d === days ? 'active' : ''}">${d} days</button>`).join('')}</div></div>
    <div class="stats-grid mt-1" style="grid-template-columns:repeat(3,1fr)">${statCard('Sign-ins', Prefs.number(s.logins), `last ${days} days`, 'login')}${statCard('Events', Prefs.number(s.total), 'recorded actions', 'activity', 'blue')}${statCard('Busiest day', Prefs.number(max), 'events in one day', 'trendUp', 'amber')}</div>
    <h3 class="mb-1">Events per day</h3>
    <div class="act-chart" role="img" aria-label="Events per day">${s.daily.map(d => `<i style="height:${Math.max(3, (d.count / max) * 100)}%" title="${escHtml(d.date)}: ${d.count}"></i>`).join('')}</div>
    <div class="flex-between text-sm text-muted mt-1"><span>${escHtml(s.daily[0]?.date || '')}</span><span>${escHtml(s.daily[s.daily.length - 1]?.date || '')}</span></div>
    <h3 class="mt-2 mb-1">When they are active</h3>
    <div class="heat">${s.heatmap.map((row, d) => `<span>${DAYS[d]}</span>${row.map((n, h) => `<i title="${DAYS[d]} ${String(h).padStart(2, '0')}:00 · ${n} events" style="opacity:${n ? 0.15 + 0.85 * (n / hmax) : 0.06}"></i>`).join('')}`).join('')}</div>
    <h3 class="mt-2 mb-1">What they do</h3>${s.by_kind.length ? Charts.hbars(s.by_kind.map(k => ({ label: k.kind, value: k.count }))) : '<p class="text-muted">No activity in this period.</p>'}
    <h3 class="mt-2 mb-1">Latest events</h3>
    ${s.recent.length ? s.recent.map(r => `<div class="feed-item"><span class="feed-icon">${icon('activity', 'sm')}</span><div class="feed-body"><b>${escHtml(VERBS[r.action] || r.action.replace(/[._]/g, ' '))}</b><span>${r.entity_type ? escHtml(r.entity_type) : ''}</span></div><span class="feed-time">${timeAgo(istParseToEpoch(r.at))}</span></div>`).join('') : '<p class="text-muted">Nothing yet.</p>'}`;
  wrap.querySelector('[data-close]')?.focus();
}
