/* imPress v2.2 System page: overview and database integrity, features (who switched what, and when), what TrustedInstaller
 * found at start-up, backups (save, view, restore), traffic and account safety, the policy root has set, and approvals.
 * Replaces renderSystem in pages.js (its approval handlers are reused). */

const SysView = { tab: 'overview' };

const RANK_TEXT = { 0: '', 1: 'an administrator', 2: 'a super admin', 3: 'root', 4: 'TrustedInstaller' };
function whoSet(f) {
  if (!f.set_by) return 'Default setting. Nobody has changed it.';
  const when = f.set_at ? istDateTime(istParseToEpoch(f.set_at)) : '';
  if (f.set_rank === 3) return `Set by root${when ? ' at ' + when : ''} (launch flag).`;
  if (f.set_rank === 4) return `Turned off by TrustedInstaller${when ? ' at ' + when : ''} because this server does not meet the minimum requirements.`;
  return `Changed by ${escHtml(f.set_by)}, ${RANK_TEXT[f.set_rank] || 'an administrator'}${when ? ', at ' + when : ''}.`;
}

async function renderSystem(app) {
  const user = await authApi.me();
  const isSuper = user.role === 'super_admin', adv = Prefs.advanced(), f = System.feature_flags || {};
  const tab = SysView.tab;
  const tabs = [['overview', 'Overview', 'database'], ['features', 'Features', 'sliders'], ['requirements', 'Requirements', 'cpu'], ['backups', 'Backups', 'archive', f.backups !== false],
    ['security', 'Security', 'shield', f.traffic_monitor !== false], ['policy', 'Policy', 'lock'], ['approvals', 'Approvals', 'key', isSuper]].filter(t => t[3] !== false);
  const body = await systemTab(tab, user, adv);
  app.innerHTML = `${renderNavbar(user, '#/admin/system')}
    <div class="container">
      ${pageHeader('System', 'Database integrity, features, what this server can carry, backups, and the safeguards root has set.', '', 'Administration')}
      <div class="tabs" role="tablist">${tabs.map(([k, t, ic]) => `<button class="tab ${tab === k ? 'active' : ''}" role="tab" aria-selected="${tab === k}" data-action="sys-tab" data-tab="${k}">${icon(ic, 'sm')} ${t}</button>`).join('')}</div>
      ${body}
    </div>`;
}

Actions['sys-tab'] = (el) => { SysView.tab = el.dataset.tab; router(); };

async function systemTab(tab, user, adv) {
  const isSuper = user.role === 'super_admin';
  if (tab === 'features') return featuresTab(user);
  if (tab === 'requirements') return requirementsTab();
  if (tab === 'backups') return backupsTab();
  if (tab === 'security') return securityTab(user, adv);
  const [info, policy, appr, clear] = await Promise.all([systemApi.integrity(), systemApi.policy().catch(() => null),
    isSuper && tab === 'approvals' ? approvalsApi.list().catch(() => null) : null, isSuper && tab === 'approvals' ? systemApi.clearOptions().catch(() => null) : null]);
  System.db = info.db;
  window._clearOptions = clear;
  const lv = info.last_verification || {}, deg = info.degraded, hardened = policy && policy.profile === 'hardened';
  const backupLabel = (b) => b.kind === 'forensic' ? 'Failed database (kept for investigation)' : b.kind === 'before-clear' ? 'Taken before a clear' : b.name === 'startup.db' ? 'Start-up' : 'Rolling (last good)';
  if (tab === 'policy') return policyCard(policy, hardened);
  if (tab === 'approvals') {
    const actions = appr ? Object.keys(appr.actions).filter(a => a !== 'system.clear.everything' || (clear && clear.scopes.everything)) : [];
    return appr ? `<div class="card"><div class="card-header"><div><h2>${icon('key')} Approvals</h2>
        <div class="card-sub">Accepting a changed database, clearing data or resetting the system needs a second super admin to approve it${policy && policy.flags.find(f => f.name === 'dual_control.delay_minutes').value ? `, then a ${policy.flags.find(f => f.name === 'dual_control.delay_minutes').value}-minute wait` : ''}. Everything here is logged and copied to the audit sink.</div></div></div>
      <div class="flex gap-1 mb-1" style="flex-wrap:wrap">${actions.map(a => `<button class="btn btn-outline btn-sm" data-action="sys-request" data-kind="${escHtml(a)}">${icon((APPROVAL_LABEL[a] || [0, 'key'])[1], 'sm')} ${escHtml((APPROVAL_LABEL[a] || [a])[0])}</button>`).join('')}</div>
      ${appr.requests.length ? appr.requests.map(r => approvalRow(r, user)).join('') : emptyState('No requests yet', 'Dangerous actions start here.', 'key')}</div>` : emptyState('Not available');
  }
  return `
    <div class="stats-grid">
      ${statCard('Database', info.db === 'ok' ? 'Verified' : 'Review', info.db === 'ok' ? 'every row matches its seal' : 'restored automatically', 'database', info.db === 'ok' ? 'green' : 'red')}
      ${statCard('Rows checked', Prefs.number(lv.rows || 0), lv.verified_at ? `last check ${timeAgo(istParseToEpoch(lv.verified_at))}` : 'not checked yet', 'shieldCheck', 'blue')}
      ${statCard('Policy profile', policy ? (hardened ? 'Hardened' : 'Standard') : '—', policy && policy.file ? `signed file, serial ${policy.file.serial}` : 'built-in defaults', 'lock', hardened ? 'green' : 'amber')}
      ${statCard('Test mode', System.test_mode ? 'On' : 'Off', System.test_mode ? (System.test_mode_forced ? 'enabled by root' : 'working on test data') : 'real data', 'flask', System.test_mode ? 'amber' : '')}
    </div>
    ${deg ? `<div class="callout danger mb-2" role="alert"><b>${icon('alert', 'sm')} The database was restored on ${istDateTime(istParseToEpoch(deg.since))}.</b>
      <div style="margin-top:6px">${escHtml(deg.message)}</div>
      <div class="flex gap-1 mt-1"><button class="btn btn-sm btn-outline" data-action="sys-ack">${icon('check', 'sm')} Acknowledge</button>
      ${isSuper ? `<span class="text-sm text-muted">To accept the current state as correct, request it under <b>Approvals</b>.</span>` : ''}</div></div>` : ''}
    ${policy && policy.problems.length ? `<div class="callout danger mb-2" role="alert"><b>${icon('alert', 'sm')} A policy file was refused.</b>${policy.problems.map(p => `<div>${escHtml(p)}</div>`).join('')}</div>` : ''}
    <div class="card"><div class="card-header"><div><h2>${icon('shieldCheck')} Database integrity</h2><div class="card-sub">Every change goes through the database gateway; changes made outside imPress are found and repaired.</div></div>
      <button class="btn btn-sm btn-primary" data-action="sys-verify">${icon('refresh', 'sm')} Verify now</button></div>
      <dl class="kv"><dt>State</dt><dd>${info.db === 'ok' ? statusPill('ok', 'Verified') : statusPill('bad', 'Review')}</dd>
        <dt>Last verification</dt><dd>${lv.verified_at ? istDateTime(istParseToEpoch(lv.verified_at)) : '—'}</dd><dt>Result</dt><dd>${escHtml(lv.summary || '—')}</dd>
        <dt>Backup folder</dt><dd><code>${escHtml(info.backup_dir)}</code></dd></dl>
      <h3 class="mt-2 mb-1">Automatic backups</h3>
      ${info.backups.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Backup</th><th>Taken</th><th>Size</th></tr></thead><tbody>
        ${info.backups.map(b => `<tr><td><b>${backupLabel(b)}</b><div class="text-sm text-muted">${escHtml(b.name)}</div></td><td class="nowrap">${istDateTime(istParseToEpoch(b.modified))}</td><td class="nowrap">${(b.size / 1024).toFixed(0)} KB</td></tr>`).join('')}</tbody></table></div>` : emptyState('No backups yet')}
      <p class="text-sm text-muted mt-1">These live on the same machine and repair tampering. To keep a copy you choose, use the Backups tab.</p></div>`;
}

function policyCard(policy, hardened) {
  return `<div class="card"><div class="card-header"><div><h2>${icon('lock')} Policy</h2><div class="card-sub">Set by root, read-only here. ${hardened ? 'Hardened profile.' : 'Standard profile.'}</div></div>
      ${policy && policy.file ? `<span class="badge badge-outline">serial ${policy.file.serial}</span>` : ''}</div>
    ${policy ? `<div class="table-wrap"><table class="table"><thead><tr><th>Flag</th><th>Value</th><th>From</th></tr></thead><tbody>
      ${policy.flags.map(f => `<tr><td><code>${escHtml(f.name)}</code><div class="text-sm text-muted">${escHtml(f.description)}</div></td><td class="nowrap"><b>${fmtFlag(f.value)}</b></td><td><span class="chip">${escHtml(f.source)}</span></td></tr>`).join('')}</tbody></table></div>
      <dl class="kv mt-1"><dt>Audit sink</dt><dd>${policy.audit.file ? `<code>${escHtml(policy.audit.file)}</code>` : 'not set'}${policy.audit.url ? ' + webhook' : ''}</dd>
        <dt>Code manifest</dt><dd>${!policy.code_manifest.present ? 'not signed' : policy.code_manifest.problems.length ? statusPill('bad', `${policy.code_manifest.problems.length} problem(s)`) : statusPill('ok', 'matches the signed manifest')}</dd></dl>`
      : emptyState('Policy not available')}</div>`;
}

// ── Features ───────────────────────────────────────────────────────

async function featuresTab(user) {
  const r = await adminApi.features();
  const groups = [...new Set(r.features.map(x => x.group))];
  return `<div class="card"><div class="card-header"><div><h2>${icon('sliders')} Features</h2><div class="card-sub">Switch parts of imPress on or off for everyone. A change by someone with more authority cannot be undone by someone with less: the order is administrator, super admin, root, TrustedInstaller. Faculty never see this page.</div></div>
      <button class="btn btn-sm btn-outline" data-action="feat-log">${icon('history', 'sm')} Change log</button></div>
    ${groups.map(g => `<h3 class="mt-1 mb-1" style="font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--faint)">${escHtml(g)}</h3>${r.features.filter(x => x.group === g).map(x => {
      const blocked = r.your_rank < x.set_rank || r.your_rank < x.min_rank;
      const why = r.your_rank < x.set_rank ? `Set by ${RANK_TEXT[x.set_rank]}: it can only be changed by them or someone with more authority.` : r.your_rank < x.min_rank ? `Only ${RANK_TEXT[x.min_rank]} can change this.` : '';
      return `<div class="feature-row"><div class="pt"><b>${escHtml(x.title)} <span data-info tabindex="0" aria-label="Who changed this">${icon('info', 'sm')}<span class="tip" role="tooltip">${whoSet(x)}${x.min_rank > 1 ? `<br>Only ${RANK_TEXT[x.min_rank]} or above can change it.` : ''}</span></span>${x.min_rank > 1 ? `<span class="badge badge-sm" title="Locked">${icon('lock', 'sm')} ${x.min_rank >= 3 ? 'Root' : 'Super admins'}</span>` : ''}</b><span>${escHtml(x.doc)}</span></div>
        ${user.role === 'super_admin' && !blocked ? `<button class="btn btn-sm btn-ghost btn-icon" data-action="feat-lock" data-name="${x.name}" data-lock="${x.min_rank < 2 ? 'true' : 'false'}" title="${x.min_rank < 2 ? 'Only super admins may change this' : 'Let administrators change this'}" aria-label="${x.min_rank < 2 ? 'Lock for super admins' : 'Unlock for administrators'}">${icon(x.min_rank >= 2 ? 'lock' : 'unlock', 'sm')}</button>` : ''}
        <label class="switch" title="${escHtml(why)}"><input type="checkbox" role="switch" data-change="feat-set" data-name="${x.name}" ${x.enabled ? 'checked' : ''} ${blocked ? 'disabled' : ''} aria-label="${escHtml(x.title)}"><i></i></label></div>`;
    }).join('')}`).join('')}</div>`;
}

Actions['feat-set'] = async (el) => {
  try { await adminApi.setFeature(el.dataset.name, { enabled: el.checked }); await loadSystemStatus(); showToast(`${el.checked ? 'Turned on' : 'Turned off'}.`, 'success'); router(); }
  catch (err) { el.checked = !el.checked; showToast(err.message, 'error'); }
};
Actions['feat-lock'] = async (el) => {
  try { await adminApi.setFeature(el.dataset.name, { min_rank: el.dataset.lock === 'true' ? 2 : 1 }); router(); } catch (err) { showToast(err.message, 'error'); }
};
Actions['feat-log'] = async () => {
  const rows = await adminApi.featureLog().catch(() => []);
  const wrap = document.createElement('div');
  wrap.innerHTML = `<div class="drawer-back" data-close></div><aside class="drawer" role="dialog" aria-modal="true" aria-label="Change log"><div class="flex-between"><h2>Change log</h2><button class="btn btn-ghost btn-icon" data-close aria-label="Close">${icon('x')}</button></div>
    <p class="text-muted">Who changed which feature or policy, and when.</p>
    ${rows.length ? rows.map(r => `<div class="feed-item"><span class="feed-icon ${r.actor_role === 'TrustedInstaller' ? 'amber' : r.actor_role === 'root' ? 'red' : ''}">${icon(r.actor_role === 'TrustedInstaller' ? 'cpu' : r.actor_role === 'root' ? 'terminal' : 'userCog', 'sm')}</span>
      <div class="feed-body"><b>${escHtml(r.flag)}: ${escHtml(r.old || '—')} → ${escHtml(r.new)}</b><span>${escHtml(r.actor)} (${escHtml(r.actor_role)})${r.note ? ' · ' + escHtml(r.note) : ''}</span></div><span class="feed-time">${istDateTime(istParseToEpoch(r.at))}</span></div>`).join('') : emptyState('No changes yet', '', 'history')}</aside>`;
  document.body.appendChild(wrap);
  wrap.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) wrap.remove(); });
};

// ── What TrustedInstaller found ───────────────────────────────────

async function requirementsTab() {
  const r = await adminApi.requirements();
  return `<div class="card"><div class="card-header"><div><h2>${icon('cpu')} Requirements</h2><div class="card-sub">At every start, TrustedInstaller checks the host against the minimum a classroom server needs. Features that cannot be supported are switched off until the host meets it.</div></div>
      ${statusPill(r.passed ? 'ok' : 'warn', r.passed ? 'All met' : 'Below minimum')}</div>
    ${r.passed ? '' : `<div class="callout warn mb-1" role="status" style="background:var(--warning-soft);color:var(--warning)">${icon('alert', 'sm')} ${escHtml(r.summary)}</div>`}
    <div class="table-wrap"><table class="table"><thead><tr><th>Check</th><th>Found</th><th>Minimum</th><th></th></tr></thead><tbody>
      ${r.checks.map(c => `<tr><td><b>${escHtml(c.title)}</b>${c.critical ? ' <span class="badge badge-sm">Required</span>' : ''}${c.gates.length && !c.ok ? `<div class="text-sm text-muted">Turned off: ${c.gates.map(g => escHtml(g.replace(/_/g, ' '))).join(', ')}</div>` : ''}</td>
        <td>${escHtml(c.detail)}</td><td>${escHtml(c.minimum)}</td><td>${statusPill(c.ok ? 'ok' : 'bad', c.ok ? 'Met' : 'Not met')}</td></tr>`).join('')}</tbody></table></div>
    <dl class="kv mt-1"><dt>System</dt><dd>${escHtml(r.host.os)} (${escHtml(r.host.machine)})</dd><dt>Python</dt><dd>${escHtml(r.host.python)}</dd><dt>SQLite</dt><dd>${escHtml(r.host.sqlite)}</dd>
      <dt>Running in a container</dt><dd>${r.container ? 'Yes. The separate root console is closed; root uses the console on the container’s own screen.' : 'No'}</dd></dl></div>`;
}

// ── Backups ────────────────────────────────────────────────────────

async function backupsTab() {
  const r = await adminApi.backups();
  const saved = r.backups.filter(b => b.kind === 'saved'), auto = r.backups.filter(b => b.kind !== 'saved');
  const table = (rows, canDelete) => rows.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Backup</th><th>Taken</th><th>Size</th><th></th></tr></thead><tbody>${rows.map(b => `<tr>
    <td><b>${escHtml(b.kind === 'saved' ? b.name : b.label)}</b><div class="text-sm text-muted">${escHtml(b.by ? 'by ' + b.by : b.file)}${b.note ? ' · ' + escHtml(b.note) : ''}</div></td>
    <td class="nowrap">${istDateTime(istParseToEpoch(b.modified))}</td><td class="nowrap">${(b.size / 1024).toFixed(0)} KB</td>
    <td><div class="row-actions"><button class="btn btn-sm btn-outline" data-action="bk-view" data-id="${escHtml(b.id)}">${icon('eye', 'sm')} View</button>
      <button class="btn btn-sm btn-outline" data-action="bk-restore" data-id="${escHtml(b.id)}" data-name="${escHtml(b.name)}">${icon('undo', 'sm')} Restore</button>
      ${canDelete ? `<button class="btn btn-sm btn-danger-ghost btn-icon" data-action="bk-delete" data-id="${escHtml(b.id)}" data-name="${escHtml(b.name)}" aria-label="Delete ${escHtml(b.name)}">${icon('trash', 'sm')}</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div>`
    : emptyState('Nothing here yet', canDelete ? 'Save one to keep a copy of the database and the system state.' : '', 'archive');
  return `<div class="card"><div class="card-header"><div><h2>${icon('archive')} Saved backups</h2><div class="card-sub">A copy of the database and the system state (version, policy, what the tables held). Restoring replaces the live database and signs everyone out.</div></div>
      <button class="btn btn-sm btn-primary" data-action="bk-save">${icon('save', 'sm')} Save a backup now</button></div>${table(saved, true)}
    ${r.restore_needs_approval ? `<p class="text-sm text-muted mt-1">${icon('lock', 'sm')} In this profile a restore also needs a second super admin's approval.</p>` : ''}</div>
    <div class="card"><div class="card-header"><div><h2>Automatic copies</h2><div class="card-sub">Start-up, rolling, and the ones taken before a clear or a restore.</div></div></div>${table(auto, false)}</div>`;
}

Actions['bk-save'] = async () => {
  const v = await askDialog({ title: 'Save a backup', confirm: 'Save backup', body: 'The database is checked first, then copied together with a description of the system state.',
    fields: [{ name: 'name', label: 'Name', placeholder: 'before-term-start' }, { name: 'note', label: 'Note (optional)' }], validate: (x) => x.name.trim().length > 0 });
  if (!v) return;
  try { await adminApi.saveBackup(v.name.trim(), v.note.trim()); showToast('Backup saved.', 'success'); router(); } catch (err) { showToast(err.message, 'error'); }
};
Actions['bk-view'] = async (el) => {
  try {
    const d = await adminApi.describeBackup(el.dataset.id), c = d.counts || {};
    askDialog({ title: d.kind === 'saved' ? d.name : d.label, confirm: 'Close', body: `<dl class="kv"><dt>Taken</dt><dd>${istDateTime(istParseToEpoch(d.modified))}</dd><dt>Size</dt><dd>${(d.size / 1024).toFixed(0)} KB</dd>
      ${d.system ? `<dt>imPress version</dt><dd>${escHtml(d.system.version)}</dd><dt>Profile</dt><dd>${escHtml(d.system.profile)}</dd>` : ''}
      <dt>Accounts</dt><dd>${c.users ?? '—'} (${c.super_admins ?? '—'} active super admins)</dd><dt>Classrooms</dt><dd>${c.class_sessions ?? '—'}</dd><dt>Students</dt><dd>${c.students ?? '—'}</dd>
      <dt>Quizzes and polls</dt><dd>${(c.quizzes ?? 0) + (c.polls ?? 0)}</dd><dt>Devices</dt><dd>${c.esp_devices ?? '—'}</dd><dt>Activity entries</dt><dd>${c.activity_logs ?? '—'}</dd><dt>Schema</dt><dd>${c.schema_version ?? '—'}</dd></dl>` });
  } catch (err) { showToast(err.message, 'error'); }
};
Actions['bk-restore'] = async (el) => {
  const v = await askDialog({ title: `Restore ${el.dataset.name}?`, confirm: 'Restore and sign everyone out', danger: true,
    body: `<div class="confirm-warn">${icon('alert', 'sm')}<span>The live database is replaced by this copy. What is there now is kept as a "before restore" copy. Everyone is signed out, including you.</span></div>Type <code>${escHtml(el.dataset.name)}</code> and your password to continue.`,
    fields: [{ name: 'confirm', label: 'Backup name' }, PASSWORD_FIELD], validate: (x) => x.confirm.trim() === el.dataset.name && x.password.length > 0 });
  if (!v) return;
  try { await adminApi.restoreBackup(el.dataset.id, v.password, v.confirm.trim()); showToast('Restored. Please sign in again.', 'success'); setTimeout(() => { navigate('#/login'); location.reload(); }, 1200); }
  catch (err) { showToast(err.code === 'APPROVAL_REQUIRED' ? 'A second super admin must approve this restore first.' : err.message, 'error'); }
};
Actions['bk-delete'] = async (el) => {
  const ok = await askDialog({ title: `Delete ${el.dataset.name}?`, confirm: 'Delete backup', danger: true, body: 'This copy is removed. The database itself is not touched.' });
  if (!ok) return;
  try { await adminApi.deleteBackup(el.dataset.id); showToast('Backup deleted.', 'success'); router(); } catch (err) { showToast(err.message, 'error'); }
};

// ── Traffic and account safety ────────────────────────────────────

async function securityTab(user, adv) {
  const [t, risk] = await Promise.all([adminApi.traffic().catch(() => null), (System.feature_flags?.risk_scores === false) ? Promise.resolve({}) : adminApi.risk().catch(() => ({}))]);
  if (!t) return emptyState('Not available', 'The traffic monitor is switched off.', 'gauge');
  const counts = { Safe: 0, 'Potentially Unsafe': 0, 'Likely Compromised': 0 };
  Object.values(risk).forEach(r => { counts[r.label] = (counts[r.label] || 0) + 1; });
  return `<div class="stats-grid">${statCard('Traffic alerts', t.alerts.length, t.alerts.length ? 'since the server started' : 'nothing unusual', 'gauge', t.alerts.length ? 'amber' : 'green')}
      ${statCard('Safe accounts', counts.Safe, 'no unusual behaviour', 'shieldCheck', 'green')}${statCard('Need attention', counts['Potentially Unsafe'], 'potentially unsafe', 'alert', counts['Potentially Unsafe'] ? 'amber' : '')}
      ${statCard('Likely compromised', counts['Likely Compromised'], 'review these first', 'shield', counts['Likely Compromised'] ? 'red' : '')}</div>
    <div class="card"><div class="card-header"><div><h2>${icon('gauge')} Unusual traffic</h2><div class="card-sub">Each kind of page has its own limit, set high on purpose. A flag is an alert for you: imPress never blocks anyone. ${user.role === 'super_admin' ? 'You can sign an account out from User access.' : ''}</div></div></div>
      ${t.alerts.length ? t.alerts.map(a => `<div class="feed-item flagged"><span class="feed-icon red">${icon('alert', 'sm')}</span><div class="feed-body"><b>${escHtml(a.type)}: ${a.requests_per_minute} requests a minute to ${escHtml(a.endpoint_kind)} pages (limit ${a.limit_per_minute})</b>
        <span>From ${escHtml(a.origin)}${a.username ? ` · account <b>${escHtml(a.username)}</b>` : ' · not signed in'}${a.pages.length ? ' · mostly ' + a.pages.slice(0, 2).map(p => escHtml(p.path)).join(', ') : ''}</span></div>
        <span class="feed-time">${timeAgo(a.at * 1000)}</span></div>`).join('') : emptyState('All quiet', 'No origin or account went over its limits.', 'shieldCheck')}</div>
    ${adv ? `<div class="grid-2"><div class="card"><div class="card-header"><h2>Busiest origins now</h2></div>${t.busiest.length ? Charts.hbars(t.busiest.map(b => ({ label: `${b.origin} · ${b.kind}`, value: b.requests_per_minute }))) : emptyState('No traffic yet')}</div>
      <div class="card"><div class="card-header"><h2>Limits per minute</h2></div><div class="table-wrap"><table class="table"><thead><tr><th>Pages</th><th>Per origin</th><th>Per account</th></tr></thead><tbody>
        ${Object.entries(t.limits).map(([k, v]) => `<tr><td>${escHtml(k)}</td><td>${Prefs.number(v.per_origin)}</td><td>${Prefs.number(v.per_account)}</td></tr>`).join('')}</tbody></table></div></div></div>`
      : '<p class="text-sm text-muted">Turn on advanced mode in Settings to see the busiest origins and the limits.</p>'}`;
}
