/* imPress v2.2 pages: overview, classrooms, quizzes & polls, user access and
 * activity, system (database integrity), test data. Loaded after app.js;
 * these definitions replace the v2.1 versions of the same pages. */

// ── Shared helpers ────────────────────────────────────────────────────

const WEEKDAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function istNow() {
  const day = istFormat(Date.now(), { weekday: 'long' });
  const hm = istFormat(Date.now(), { hour: '2-digit', minute: '2-digit', hour12: false });
  return { day, hm };
}

function classStatus(c) {
  if (c.is_active) return ['live', 'Live now'];
  const { day, hm } = istNow();
  const slots = c.meeting_schedule || [];
  if (slots.some(s => s.day === day && s.end > hm)) return ['upcoming', 'Upcoming'];
  if (slots.length) return ['scheduled', 'Scheduled'];
  return ['inactive', 'Inactive'];
}

function classGlyph(c) {
  const n = `${c.course_name || c.name}`.toLowerCase();
  const ic = /program|software|code/.test(n) ? 'code' : /data|algorithm|statist/.test(n) ? 'chart'
    : /system|architect|embedded|micro/.test(n) ? 'cpu' : /database/.test(n) ? 'database'
    : /network|communic|signal/.test(n) ? 'hub' : /machine|intellig/.test(n) ? 'sparkles'
    : /physic|mechanic|thermo|fluid/.test(n) ? 'zap' : /math|calculus|algebra/.test(n) ? 'activity' : 'book';
  let h = 0;
  for (const ch of n) h = (h * 33 + ch.charCodeAt(0)) >>> 0;
  return `<span class="class-glyph g${(h % 6) + 1}">${icon(ic)}</span>`;
}

function slotText(c) {
  const s = c.meeting_schedule || [];
  if (!s.length) return 'No timetable yet';
  const days = [...new Set(s.map(x => x.day.slice(0, 3)))].join(', ');
  return `${days} · ${s[0].start}–${s[0].end}`;
}

function facultyText(c) {
  return (c.faculty_names && c.faculty_names.length)
    ? c.faculty_names.map(f => f.full_name || f.username).join(', ') : (c.teacher_name || 'Unassigned');
}

function pct(n) { return n == null ? '—' : `${n}%`; }
function barTone(n) { return n == null ? '' : n >= 85 ? 'green' : n >= 70 ? '' : n >= 50 ? 'amber' : 'red'; }
function bar(n) {
  return n == null ? '<span class="text-muted">—</span>'
    : `<div class="bar-cell"><span>${n}%</span><div class="bar ${barTone(n)}"><i style="width:${Math.max(2, n)}%"></i></div></div>`;
}

function paginate(rows, page, size) {
  const pages = Math.max(1, Math.ceil(rows.length / size));
  const p = Math.min(Math.max(1, page), pages);
  return { rows: rows.slice((p - 1) * size, p * size), page: p, pages };
}

function pagerHtml(state, total, size, onPage) {
  const pages = Math.max(1, Math.ceil(total / size));
  if (pages <= 1) return '';
  const nums = [];
  for (let i = 1; i <= pages; i++) {
    if (i === 1 || i === pages || Math.abs(i - state.page) <= 1) nums.push(i);
    else if (nums[nums.length - 1] !== '…') nums.push('…');
  }
  return `<div class="pager">
    <button ${state.page <= 1 ? 'disabled' : ''} onclick="${onPage}(${state.page - 1})" aria-label="Previous page">${icon('chevronLeft', 'sm')}</button>
    ${nums.map(n => n === '…' ? '<button disabled>…</button>'
      : `<button class="${n === state.page ? 'active' : ''}" onclick="${onPage}(${n})">${n}</button>`).join('')}
    <button ${state.page >= pages ? 'disabled' : ''} onclick="${onPage}(${state.page + 1})" aria-label="Next page">${icon('chevronRight', 'sm')}</button></div>`;
}

function downloadCsv(name, header, rows) {
  const esc = v => {
    let s = v == null ? '' : String(v);
    if (/^[=+\-@]/.test(s)) s = `'${s}`;                  // spreadsheet formula injection
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const text = [header, ...rows].map(r => r.map(esc).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv' }));
  const a = Object.assign(document.createElement('a'), { href: url, download: name });
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

// ── Overview ──────────────────────────────────────────────────────────

async function renderDashboard(app) {
  const user = await authApi.me();
  if (isAdminUser(user)) { navigate('#/admin'); return; }
  const [classes, overview] = await Promise.all([classesApi.list(), quizzesApi.overview().catch(() => ({ quizzes: [], polls: [] }))]);
  Shell.counts.classes = classes.length;
  const { day } = istNow();
  const today = classes.filter(c => c.is_active || (c.meeting_schedule || []).some(s => s.day === day))
    .sort((a, b) => ((a.meeting_schedule || []).find(s => s.day === day)?.start || '00') > ((b.meeting_schedule || []).find(s => s.day === day)?.start || '00') ? 1 : -1);
  const students = classes.reduce((n, c) => n + (c.student_count || 0), 0);
  const live = classes.filter(c => c.is_active);
  const done = overview.quizzes.filter(q => q.status === 'completed');
  const first = (user.full_name || user.username).replace(/^(Dr|Prof)\.?\s+/i, '').split(/\s+/)[0];
  app.innerHTML = `
    ${renderNavbar(user, '#/dashboard')}
    <div class="container">
      ${pageHeader(`Good day, ${first}`, 'Your classes today, live sessions and recent results.', `<a href="#/sessions" class="btn btn-primary">${icon('plus')} New quiz or poll</a>`, todayLabel())}
      <div class="stats-grid">
        ${statCard('My classrooms', classes.length, `${classes.filter(c => (c.meeting_schedule || []).length).length} with a timetable`, 'school')}
        ${statCard('Live now', live.length, live.length ? escHtml(live.map(c => c.name).slice(0, 2).join(', ')) : 'No class in session', 'zap', live.length ? 'green' : '')}
        ${statCard('Students', students, 'enrolled across your classes', 'users', 'blue')}
        ${statCard('Quizzes run', done.length, `${overview.quizzes.length} in total · ${overview.polls.length} polls`, 'clipboard', 'amber')}
      </div>
      <div class="grid-main">
        <div class="card">
          <div class="card-header"><div><h2>Today</h2><div class="card-sub">${escHtml(day)}: your classes and their state</div></div>
            <a href="#/classes" class="btn btn-sm btn-outline">All classrooms</a></div>
          ${today.length ? today.map(c => {
            const [k, t] = classStatus(c);
            const slot = (c.meeting_schedule || []).find(s => s.day === day);
            return `<div class="feed-item">${classGlyph(c)}
              <div class="feed-body"><b>${escHtml(c.course_name || c.name)}</b><span>${escHtml(c.code)}${c.classroom_code ? ' · ' + escHtml(c.classroom_code) : ''}${slot ? ` · ${slot.start}–${slot.end}` : ''}</span></div>
              ${statusPill(k, t)}<a href="#/class?id=${c.id}" class="btn btn-sm ${c.is_active ? 'btn-primary' : 'btn-outline'}">${c.is_active ? 'Open live' : 'Open'}</a></div>`;
          }).join('') : emptyState('Nothing on today', 'Classes with a slot today, or activated, appear here.', 'calendar')}
        </div>
        <div class="card">
          <div class="card-header"><h2>Recent quizzes</h2><a href="#/sessions" class="btn btn-sm btn-outline">View all</a></div>
          ${overview.quizzes.slice(0, 6).map(q => `<div class="feed-item"><span class="feed-icon">${icon('clipboard', 'sm')}</span>
            <div class="feed-body"><b>${escHtml(q.title)}</b><span>${escHtml(q.class_name)} · ${q.question_count} questions · ${q.answers} answers</span></div>
            ${statusPill(q.status === 'active' ? 'live' : q.status === 'completed' ? 'ok' : 'off', q.status === 'active' ? 'Live' : q.status)}</div>`).join('')
            || emptyState('No quizzes yet', 'Create one from a classroom.', 'clipboard')}
        </div>
      </div>
    </div>`;
}

async function renderAdminDashboard(app) {
  const user = await authApi.me();
  const [classes, users, activity, devices, students, integrity] = await Promise.all([
    adminApi.listClasses(), adminApi.listUsers(), adminApi.activityLogs(8),
    modulesApi.list('').catch(() => []), studentsApi.list('').catch(() => []),
    systemApi.integrity().catch(() => null),
  ]);
  Shell.counts.classes = classes.length;
  const live = classes.filter(c => c.is_active);
  const { day } = istNow();
  const todays = classes.filter(c => c.is_active || (c.meeting_schedule || []).some(s => s.day === day)).slice(0, 8);
  const online = devices.filter(d => d.is_connected).length;
  const signedIn = users.filter(u => u.signed_in).length;
  const first = (user.full_name || user.username || '').split(/\s+/)[0] || 'Admin';
  const db = integrity?.db || 'ok';
  const lastVer = integrity?.last_verification;
  app.innerHTML = `
    ${renderNavbar(user, '#/admin')}
    <div class="container">
      <div class="dash-hero"><div><div class="dash-eyebrow">${escHtml(todayLabel())}</div>
        <h1 class="dash-title">Good day, ${escHtml(first)}</h1>
        <p class="dash-sub">Live snapshot of classrooms, devices, accounts and the system.</p></div>
        <div class="dash-hero-side"><a href="#/admin/classes/new" class="btn btn-primary">${icon('plus')} Create classroom</a></div></div>
      <div class="stats-grid">
        ${statCard('Live classrooms', `${live.length}<small> / ${classes.length}</small>`, `${todays.length} on today's timetable`, 'school')}
        ${statCard('Students', students.length, `across ${classes.length} classrooms`, 'users', 'green')}
        ${statCard('Devices online', `${online}<small> / ${devices.length}</small>`, devices.length - online ? `<b class="down">${devices.length - online}</b> offline` : 'all reachable', 'radio', devices.length - online ? 'amber' : 'green')}
        ${statCard('Accounts', users.length, `${signedIn} signed in now`, 'userCog', 'blue')}
      </div>
      <div class="grid-main">
        <div>
          <div class="card">
            <div class="card-header"><div><h2>Classrooms today</h2><div class="card-sub">Activated now, or with a slot today</div></div>
              <a href="#/admin/classes" class="btn btn-sm btn-outline">All classrooms</a></div>
            ${todays.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Classroom</th><th>Room</th><th>Time</th><th>Status</th><th>Students</th><th>Faculty</th><th></th></tr></thead><tbody>
              ${todays.map(c => { const [k, t] = classStatus(c); const s = (c.meeting_schedule || []).find(x => x.day === day);
                return `<tr><td><div class="cell-person">${classGlyph(c)}<div><b>${escHtml(c.course_name || c.name)}</b><span>${escHtml(c.code)}</span></div></div></td>
                <td class="nowrap">${escHtml(c.classroom_code || '—')}</td><td class="nowrap">${s ? `${s.start}–${s.end}` : '—'}</td><td>${statusPill(k, t)}</td>
                <td>${c.student_count || 0}</td><td class="text-sm">${escHtml(facultyText(c))}</td>
                <td><a href="#/class?id=${c.id}" class="btn btn-sm btn-outline">Open</a></td></tr>`; }).join('')}
              </tbody></table></div>` : emptyState('No classes today', 'Timetabled and activated classrooms appear here.', 'calendar')}
          </div>
          <div class="card">
            <div class="card-header"><div><h2>Recent activity</h2><div class="card-sub">Sign-ins, changes and system events</div></div>
              <a href="#/admin/activity" class="btn btn-sm btn-outline">View all</a></div>
            ${activity.length ? activity.map(activityItem).join('') : emptyState('No activity yet')}
          </div>
        </div>
        <div>
          <div class="card">
            <div class="card-header"><h2>System health</h2><a href="#/admin/system" class="btn btn-sm btn-outline">Details</a></div>
            <div class="feed-item"><span class="feed-icon ${db === 'ok' ? 'green' : 'red'}">${icon('database', 'sm')}</span>
              <div class="feed-body"><b>Database</b><span>${db === 'ok' ? 'Verified' : 'Degraded: restored automatically'}${lastVer?.verified_at ? ' · checked ' + timeAgo(istParseToEpoch(lastVer.verified_at)) : ''}</span></div>
              ${statusPill(db === 'ok' ? 'ok' : 'bad', db === 'ok' ? 'Healthy' : 'Degraded')}</div>
            <div class="feed-item"><span class="feed-icon ${System.test_mode ? 'amber' : 'grey'}">${icon('flask', 'sm')}</span>
              <div class="feed-body"><b>Debug mode</b><span>${System.test_mode ? 'On: working on test data' : 'Off: real data'}</span></div>
              ${statusPill(System.test_mode ? 'warn' : 'off', System.test_mode ? 'On' : 'Off')}</div>
            <div class="feed-item"><span class="feed-icon ${online === devices.length ? 'green' : 'amber'}">${icon('radio', 'sm')}</span>
              <div class="feed-body"><b>Classroom devices</b><span>${online} of ${devices.length} online</span></div></div>
            <div class="feed-item"><span class="feed-icon">${icon('shieldCheck', 'sm')}</span>
              <div class="feed-body"><b>Backups</b><span>${(integrity?.backups || []).map(b => `${b.name.replace('.db', '')} ${timeAgo(istParseToEpoch(b.modified))}`).join(' · ') || 'none yet'}</span></div></div>
          </div>
          <div class="card">
            <div class="card-header"><h2>Accounts</h2><a href="#/admin/users" class="btn btn-sm btn-outline">Manage</a></div>
            <div class="dash-people">${users.slice(0, 6).map(u => `<a href="#/admin/users" class="dash-person">${avatar(u.full_name || u.username, 'sm')}
              <span class="dash-person-body"><span class="dash-person-name">${escHtml(u.full_name || u.username)}</span>
              <span class="dash-person-meta">@${escHtml(u.username)} · ${escHtml(roleName(u.role))}</span></span>
              <span class="dash-person-status ${u.signed_in ? 'on' : ''}" title="${u.signed_in ? 'Signed in' : 'Not signed in'}"></span></a>`).join('')}</div>
          </div>
        </div>
      </div>
    </div>`;
}

function roleName(r) { return { super_admin: 'Super admin', admin: 'Admin', teacher: 'Teacher' }[r] || r; }

// ── Activity entries ──────────────────────────────────────────────────

const ACTIVITY_KINDS = {
  accounts: { label: 'Accounts', test: a => /^user\./.test(a.action), icon: 'userPlus' },
  signins: { label: 'Sign-ins', test: a => /^auth\./.test(a.action), icon: 'login' },
  classes: { label: 'Classrooms', test: a => /^(class|student|course|schedule)/.test(a.action), icon: 'school' },
  sessions: { label: 'Quizzes & polls', test: a => /^(quiz|poll)/.test(a.action), icon: 'clipboard' },
  devices: { label: 'Devices & firmware', test: a => /^(device|module|firmware|deploy|ota)/.test(a.action), icon: 'cpu' },
  system: { label: 'System & security', test: a => /^(system|db)\./.test(a.action), icon: 'database' },
};

function activityKind(a) {
  return Object.entries(ACTIVITY_KINDS).find(([, k]) => k.test(a))?.[0] || 'other';
}

const VERBS = {
  'auth.login': 'signed in', 'auth.logout': 'signed out', 'auth.second_sign_in_blocked': 'second sign-in blocked',
  'auth.change_password': 'changed their password', 'auth.update_profile': 'updated their profile',
  'user.create': 'created an account', 'user.deactivate': 'deactivated an account', 'user.reactivate': 'reactivated an account',
  'user.delete': 'deleted an account', 'user.reset_password': 'reset a password', 'user.role_change': 'changed a role',
  'user.end_sessions': 'ended a user\'s sessions', 'class.activate': 'started a class session', 'class.deactivate': 'ended a class session',
  'quiz.start': 'started a quiz', 'quiz.stop': 'ended a quiz', 'quiz.create': 'created a quiz', 'poll.create': 'created a poll',
  'system.db_degraded': 'database changed outside imPress: restored', 'db.write_refused': 'database gateway refused a write',
  'system.test_mode_on': 'turned debug mode on', 'system.test_mode_off': 'turned debug mode off',
  'system.clear_class_data': 'cleared class data', 'system.clear_everything': 'reset the database',
  'system.test_data_import': 'imported test data', 'system.db_acknowledged': 'acknowledged the database state',
};

function activityTitle(a) {
  const who = a.username || 'System';
  return `${who} ${VERBS[a.action] || a.action.replace(/[._]/g, ' ')}`;
}

function activityDetail(a) {
  const d = a.details || {};
  const bits = [];
  if (d.message) bits.push(d.message);
  if (d.ip) bits.push(`from ${d.ip}`);
  if (d.signed_in_from) bits.push(`already signed in from ${d.signed_in_from}`);
  if (d.table) bits.push(`table ${d.table}${d.why ? ': ' + d.why : ''}`);
  if (d.name) bits.push(d.name);
  if (d.title) bits.push(`"${d.title}"`);
  if (!bits.length && a.entity_type) bits.push(`${a.entity_type}${a.entity_id ? ' #' + a.entity_id : ''}`);
  return bits.join(' · ');
}

function activityItem(a) {
  const flagged = (a.details || {}).flag;
  const kind = ACTIVITY_KINDS[activityKind(a)];
  const tone = flagged ? 'red' : a.action.startsWith('auth.') ? 'green' : a.action.startsWith('system') ? 'amber' : '';
  return `<div class="feed-item${flagged ? ' flagged' : ''}"><span class="feed-icon ${tone}">${icon(flagged ? 'alert' : kind?.icon || 'activity', 'sm')}</span>
    <div class="feed-body"><b>${escHtml(activityTitle(a))}${flagged ? ' <span class="badge badge-danger badge-sm">Flagged</span>' : ''}</b><span>${escHtml(activityDetail(a))}</span></div>
    <span class="feed-time">${a.timestamp ? istDateTime(istParseToEpoch(a.timestamp)) : ''}</span></div>`;
}

// ── Classrooms (admins and faculty) ───────────────────────────────────

const ClassView = { filter: 'all', q: '', sort: 'name' };

async function renderAdminClasses(app) { return renderClassrooms(app, true); }
async function renderClasses(app) { return renderClassrooms(app, false); }

async function renderClassrooms(app, adminView) {
  const user = await authApi.me();
  const classes = adminView ? await adminApi.listClasses() : await classesApi.list();
  Shell.counts.classes = classes.length;
  const hash = adminView ? '#/admin/classes' : '#/classes';
  const canManage = isAdminUser(user);
  app.innerHTML = `
    ${renderNavbar(user, hash)}
    <div class="container">
      ${pageHeader('Classrooms', adminView ? 'Manage classrooms, timetables and faculty, and monitor live participation.' : 'Your classrooms: open one to run quizzes and polls.',
        canManage ? `<button class="btn btn-outline" id="btn-classes-import">${icon('upload')} Import CSV</button>
          <button class="btn btn-outline" id="btn-classes-export">${icon('download')} Export CSV</button>
          <a href="#/admin/classes/new" class="btn btn-primary">${icon('plus')} Create classroom</a>` : '', todayLabel())}
      ${canManage ? classImportCard() : ''}
      <div class="toolbar">
        <div class="filter-chips" role="tablist">
          ${[['all', 'All classrooms'], ['live', 'Active now'], ['scheduled', 'Scheduled'], ['inactive', 'Inactive']].map(([k, t]) =>
            `<button class="filter-chip ${ClassView.filter === k ? 'active' : ''}" data-cf="${k}" role="tab" aria-selected="${ClassView.filter === k}">${k === 'live' ? '<span class="status live" style="padding:0;background:none"></span>' : ''}${t}</button>`).join('')}
        </div>
        <span class="grow"></span>
        <h2 id="class-count" class="text-muted" style="font-size:13.5px;font-weight:600">${classes.length} Classroom${classes.length !== 1 ? 's' : ''}</h2>
        <label class="searchbox">${icon('search', 'sm')}<input id="class-q" type="search" placeholder="Search classrooms…" value="${escHtml(ClassView.q)}" data-live="1"></label>
        <select id="class-sort" class="input-sm" style="width:auto" aria-label="Sort">
          ${[['name', 'Sort: Name A–Z'], ['room', 'Sort: Room'], ['students', 'Sort: Students']].map(([k, t]) => `<option value="${k}" ${ClassView.sort === k ? 'selected' : ''}>${t}</option>`).join('')}
        </select>
      </div>
      <div id="class-grid"></div>
    </div>`;
  const draw = () => {
    const q = ClassView.q.toLowerCase();
    let list = classes.filter(c => {
      const [k] = classStatus(c);
      if (ClassView.filter === 'live' && k !== 'live') return false;
      if (ClassView.filter === 'scheduled' && !['upcoming', 'scheduled'].includes(k)) return false;
      if (ClassView.filter === 'inactive' && k !== 'inactive') return false;
      return !q || `${c.name} ${c.course_name || ''} ${c.code} ${c.course_code || ''} ${c.classroom_code || ''} ${facultyText(c)}`.toLowerCase().includes(q);
    });
    const key = { name: c => (c.course_name || c.name).toLowerCase(), room: c => c.classroom_code || '~', students: c => -(c.student_count || 0) }[ClassView.sort];
    list = list.sort((a, b) => (key(a) > key(b) ? 1 : key(a) < key(b) ? -1 : 0));
    document.getElementById('class-grid').innerHTML = list.length ? `<div class="class-grid">${list.map(c => classCard(c, canManage)).join('')}</div>`
      : (classes.length ? emptyState('No classrooms match', 'Change the filter or the search.', 'search')
        : emptyState('No classrooms yet', canManage ? 'Create one, or import courses and sections from a CSV file.' : 'Ask an administrator to assign you to a class.', 'school'));
    document.getElementById('class-count').textContent = `${classes.length} Classroom${classes.length !== 1 ? 's' : ''}`;
    const foot = document.getElementById('class-foot');
    if (foot) foot.textContent = `Showing ${list.length} of ${classes.length} classrooms`;
  };
  document.querySelectorAll('[data-cf]').forEach(b => b.onclick = () => {
    ClassView.filter = b.dataset.cf;
    document.querySelectorAll('[data-cf]').forEach(x => { x.classList.toggle('active', x === b); x.setAttribute('aria-selected', x === b); });
    draw();
  });
  document.getElementById('class-q').oninput = (e) => { ClassView.q = e.target.value; e.target.defaultValue = e.target.value; draw(); };
  document.getElementById('class-sort').onchange = (e) => { ClassView.sort = e.target.value; draw(); };
  document.getElementById('class-grid').insertAdjacentHTML('afterend', `<div class="table-foot"><span id="class-foot"></span></div>`);
  draw();
  if (canManage) wireClassCsvImport(app);
}

function classCard(c, canManage) {
  const [k, t] = classStatus(c);
  return `<article class="class-card" data-class="${c.id}">
    <div class="class-card-head">${classGlyph(c)}
      <div style="min-width:0"><h3>${escHtml(c.course_name || c.name)}</h3>
        <div class="text-sm">${escHtml(c.course_code || c.code)}${c.course_section ? ` · Section ${escHtml(c.course_section)}` : ''}</div></div>
      ${statusPill(k, t)}</div>
    <div class="class-meta">
      <div>${icon('pin', 'sm')}${escHtml(c.location || (c.classroom_code ? `Room ${c.classroom_code}` : 'No room'))}${c.classroom_code ? ` <span class="badge badge-sm">${escHtml(c.classroom_code)}</span>` : ''}</div>
      <div>${icon('calendar', 'sm')}${escHtml(slotText(c))}</div>
      <div>${icon('user', 'sm')}${escHtml(facultyText(c))}</div>
      ${(c.warnings || []).length ? `<div class="warn-line">${icon('alert', 'sm')}${escHtml(c.warnings[0].message)}</div>` : ''}
    </div>
    <div class="class-nums">
      <div class="class-num">${icon('users')}<div><b>${c.student_count || 0}</b><span>Students enrolled</span></div></div>
      <div class="class-num">${icon('clipboard')}<div><b>${(c.quiz_count || 0) + (c.poll_count || 0)}</b><span>Quizzes &amp; polls</span></div></div>
    </div>
    <div class="actions">
      <a href="#/class?id=${c.id}" class="btn btn-outline btn-sm">${icon('external', 'sm')} Open</a>
      ${c.is_active
        ? `<button class="btn btn-danger-soft btn-sm" style="flex:1" onclick="classSession(${c.id}, false)">${icon('stop', 'sm')} End session</button>`
        : `<button class="btn btn-primary btn-sm" onclick="classSession(${c.id}, true)">${icon('play', 'sm')} Start session</button>`}
      ${canManage ? `<a href="#/admin/classes/new?id=${c.id}" class="btn btn-outline btn-sm btn-icon" title="Edit" aria-label="Edit ${escHtml(c.name)}">${icon('edit', 'sm')}</a>
        <button class="btn btn-outline btn-sm btn-icon text-danger" title="Delete" aria-label="Delete ${escHtml(c.name)}" onclick="deleteClass(${c.id}, '${escHtml(c.name).replace(/'/g, "\\'")}')">${icon('trash', 'sm')}</button>` : ''}
    </div></article>`;
}

window.classSession = async function (id, on) {
  try {
    if (on) await classesApi.activate(id); else await classesApi.deactivate(id);
    showToast(on ? 'Class session started' : 'Class session ended', 'success');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

function classImportCard() {
  return `<div class="card hidden" id="classes-import">
    <div class="card-header"><div><h2>${icon('upload')} Import courses and sections</h2>
      <div class="card-sub">One row per section. Nothing is stored until you confirm, and a file with any invalid row stores nothing.</div></div>
      <a class="btn btn-sm btn-outline" href="${adminApi.classTemplateUrl}" download>${icon('download', 'sm')} Download template</a></div>
    <p class="form-hint">Columns: <b>course_code</b>, <b>course_name</b>, <b>section</b>, <b>class_code</b> (the join code), <b>teacher_username</b>;
      optional class_name, classroom_code (room), term, year, capacity, location. Courses are created when new and matched by code otherwise.</p>
    <div class="form-group" style="max-width:420px"><label for="classes-import-mode">Existing sections</label>
      <select id="classes-import-mode"><option value="create">Skip them: only create new sections</option>
        <option value="update">Update them with the values in the file</option></select></div>
    <div class="csv-drop" id="classes-csv-drop" role="button" tabindex="0" aria-label="Choose a CSV file of courses and sections">
      ${icon('upload', 'lg')}<p style="margin:6px 0">Drop a CSV file here or click to browse</p>
      <input type="file" id="classes-csv-file" accept=".csv,text/csv" class="sr-only" />
      <button type="button" class="btn btn-sm btn-outline" id="classes-csv-browse">Choose file</button></div>
    <progress id="classes-csv-progress" class="hidden" max="100" value="0" style="width:100%;margin-top:8px"></progress>
    <div id="classes-csv-result" class="mt-1" aria-live="polite"></div></div>`;
}

// ── Quizzes & polls ───────────────────────────────────────────────────

const SessionView = { tab: 'quizzes', q: '', status: 'all' };

async function renderSessions(app) {
  const user = await authApi.me();
  const [data, classes] = await Promise.all([quizzesApi.overview(), isAdminUser(user) ? adminApi.listClasses() : classesApi.list()]);
  Shell.counts.classes = classes.length;
  const liveQ = data.quizzes.filter(q => q.status === 'active').length;
  const livePolls = data.polls.filter(p => p.status === 'active').length;
  const answers = data.quizzes.reduce((n, q) => n + q.answers, 0);
  app.innerHTML = `
    ${renderNavbar(user, '#/sessions')}
    <div class="container">
      ${pageHeader('Quizzes & polls', 'Every quiz and poll of your classrooms: run them from the classroom, read the results here.',
        `<button class="btn btn-primary" onclick="newSession()">${icon('plus')} Create session</button>`)}
      <div class="stats-grid">
        ${statCard('Quizzes', data.quizzes.length, `${data.quizzes.filter(q => q.status === 'completed').length} completed`, 'clipboard')}
        ${statCard('Live now', liveQ + livePolls, `${liveQ} quiz${liveQ === 1 ? '' : 'zes'} · ${livePolls} poll${livePolls === 1 ? '' : 's'}`, 'zap', liveQ + livePolls ? 'green' : '')}
        ${statCard('Answers received', answers, 'across all quizzes', 'checkCircle', 'blue')}
        ${statCard('Polls', data.polls.length, `${data.polls.reduce((n, p) => n + p.votes, 0)} votes`, 'poll', 'amber')}
      </div>
      <div class="card">
        <div class="tabs" role="tablist">
          <button class="tab ${SessionView.tab === 'quizzes' ? 'active' : ''}" data-st="quizzes" role="tab">${icon('clipboard', 'sm')} Quizzes</button>
          <button class="tab ${SessionView.tab === 'polls' ? 'active' : ''}" data-st="polls" role="tab">${icon('poll', 'sm')} Polls</button>
        </div>
        <div class="toolbar"><label class="searchbox">${icon('search', 'sm')}<input id="ses-q" type="search" placeholder="Search by title or classroom…" value="${escHtml(SessionView.q)}" data-live="1"></label>
          <select id="ses-status" class="input-sm" style="width:auto" aria-label="Status">
            ${[['all', 'All statuses'], ['active', 'Live'], ['draft', 'Draft'], ['completed', 'Completed'], ['closed', 'Closed']].map(([k, t]) => `<option value="${k}" ${SessionView.status === k ? 'selected' : ''}>${t}</option>`).join('')}
          </select></div>
        <div id="ses-table"></div>
      </div>
    </div>
    <div id="new-session-modal" class="modal hidden"><div class="modal-backdrop" onclick="this.parentElement.classList.add('hidden')"></div>
      <div class="modal-content card"><h2>Create a session</h2>
        <div class="form-group"><label for="ns-class">Classroom</label><select id="ns-class">${classes.map(c => `<option value="${c.id}">${escHtml(c.course_name || c.name)} · ${escHtml(c.code)}</option>`).join('')}</select></div>
        <div class="choice-grid"><label class="choice"><input type="radio" name="ns-type" value="quiz" checked><div><b>Quiz</b><span>Graded questions</span></div></label>
          <label class="choice"><input type="radio" name="ns-type" value="poll"><div><b>Poll</b><span>Live opinions</span></div></label></div>
        <div class="modal-actions"><button class="btn btn-outline" onclick="document.getElementById('new-session-modal').classList.add('hidden')">Cancel</button>
          <button class="btn btn-primary" onclick="goNewSession()">${icon('arrowRight', 'sm')} Continue</button></div></div></div>`;
  const draw = () => {
    const q = SessionView.q.toLowerCase();
    const rows = (SessionView.tab === 'quizzes' ? data.quizzes : data.polls).filter(r =>
      (SessionView.status === 'all' || r.status === SessionView.status) && (!q || `${r.title} ${r.class_name} ${r.class_code}`.toLowerCase().includes(q)));
    const pill = r => statusPill(r.status === 'active' ? 'live' : ['completed', 'closed'].includes(r.status) ? 'ok' : 'off',
      r.status === 'active' ? 'Live' : r.status[0].toUpperCase() + r.status.slice(1));
    document.getElementById('ses-table').innerHTML = rows.length ? `<div class="table-wrap"><table class="table"><thead><tr>
      <th>Title</th><th>Classroom</th><th>${SessionView.tab === 'quizzes' ? 'Questions' : 'Options'}</th><th>Responses</th><th>Status</th><th>Created</th><th></th></tr></thead><tbody>
      ${rows.map(r => `<tr><td><b>${escHtml(r.title)}</b>${r.timing_mode && r.timing_mode !== 'manual' ? `<div class="text-sm text-muted">${escHtml(r.timing_mode.replace('_', ' '))}</div>` : ''}</td>
        <td><a href="#/class?id=${r.class_id}">${escHtml(r.class_name)}</a><div class="text-sm text-muted">${escHtml(r.class_code)}</div></td>
        <td>${SessionView.tab === 'quizzes' ? r.question_count : (r.options || []).length}</td>
        <td>${SessionView.tab === 'quizzes' ? r.answers : r.votes}</td><td>${pill(r)}</td>
        <td class="text-sm">${r.created_at ? istFormat(istParseToEpoch(r.created_at), { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}</td>
        <td class="nowrap"><a class="btn btn-sm btn-outline" href="#/${SessionView.tab === 'quizzes' ? 'quiz' : 'poll'}-results?id=${r.id}">${icon('chart', 'sm')} Results</a>
          <a class="btn btn-sm btn-ghost" href="#/class?id=${r.class_id}">${icon('external', 'sm')}</a></td></tr>`).join('')}
      </tbody></table></div>` : emptyState(`No ${SessionView.tab} match`, 'Create one, or change the filters.', SessionView.tab === 'quizzes' ? 'clipboard' : 'poll');
  };
  document.querySelectorAll('[data-st]').forEach(b => b.onclick = () => {
    SessionView.tab = b.dataset.st;
    document.querySelectorAll('[data-st]').forEach(x => x.classList.toggle('active', x === b));
    draw();
  });
  document.getElementById('ses-q').oninput = (e) => { SessionView.q = e.target.value; e.target.defaultValue = e.target.value; draw(); };
  document.getElementById('ses-status').onchange = (e) => { SessionView.status = e.target.value; draw(); };
  draw();
}

window.newSession = function () { document.getElementById('new-session-modal').classList.remove('hidden'); };
window.goNewSession = function () {
  const cid = document.getElementById('ns-class').value;
  if (!cid) { showToast('Create a classroom first', 'error'); return; }
  const type = document.querySelector('input[name=ns-type]:checked').value;
  navigate(`#/${type}?class_id=${cid}`);
};

// ── User access & activity log ────────────────────────────────────────

const UserView = { q: '', role: 'all', page: 1, tab: 'users', act: { kind: 'all', user: 'all', days: '7' } };

async function renderAdminActivity(app) { UserView.tab = 'activity'; return renderUserAccess(app, '#/admin/activity'); }
async function renderAdminUsers(app) { if (getRoute() === '#/admin/users') UserView.tab = 'users'; return renderUserAccess(app, '#/admin/users'); }

async function renderUserAccess(app, hash) {
  const user = await authApi.me();
  const [users, activity] = await Promise.all([adminApi.listUsers(), adminApi.activityLogs(200)]);
  const isSuper = user.role === 'super_admin';
  app.innerHTML = `
    ${renderNavbar(user, hash)}
    <div class="container">
      ${pageHeader('User access & activity log', 'Manage who can use imPress and review everything that happens in the workspace.', '', 'Administration')}
      <div class="tabs" role="tablist">
        <button class="tab ${UserView.tab === 'users' ? 'active' : ''}" onclick="location.hash='#/admin/users'" role="tab">${icon('user', 'sm')} Users</button>
        <button class="tab ${UserView.tab === 'activity' ? 'active' : ''}" onclick="location.hash='#/admin/activity'" role="tab">${icon('history', 'sm')} Activity log</button>
      </div>
      ${UserView.tab === 'users' ? usersPanel(users, user) : ''}
      ${activityPanel(activity, users, UserView.tab === 'users')}
    </div>
    ${UserView.tab === 'users' ? userModals(isSuper) : ''}`;
  if (UserView.tab === 'users') wireUsers(app, users, user);
  wireActivity(activity);
}

function usersPanel(users, me) {
  return `<div class="card">
    <div class="card-header"><div><h2>Workspace users</h2><div class="card-sub">Accounts, roles and access (${users.length} users)</div></div>
      <div class="page-actions">
        <label class="searchbox">${icon('search', 'sm')}<input id="usr-q" type="search" placeholder="Search users by name or e-mail…" value="${escHtml(UserView.q)}" data-live="1"></label>
        <select id="usr-role" class="input-sm" style="width:auto" aria-label="Filter by role">
          ${[['all', 'All roles'], ['super_admin', 'Super admins'], ['admin', 'Admins'], ['teacher', 'Teachers'], ['inactive', 'Inactive']].map(([k, t]) => `<option value="${k}" ${UserView.role === k ? 'selected' : ''}>${t}</option>`).join('')}
        </select>
        <button class="btn btn-outline" id="btn-import-users-csv">${icon('upload', 'sm')} Import CSV</button>
        <button class="btn btn-primary" onclick="document.getElementById('create-user-modal').classList.remove('hidden')">${icon('plus')} Invite user</button>
      </div></div>
    <div class="card hidden" id="users-csv-card" style="box-shadow:none;background:var(--surface-2)">
      <div class="card-header"><h2>Import users from CSV</h2><button class="btn btn-sm btn-ghost btn-icon" aria-label="Close" onclick="document.getElementById('users-csv-card').classList.add('hidden')">${icon('x', 'sm')}</button></div>
      <p class="form-hint">Every row needs all five columns: <b>username</b> (3–64 letters, digits, _ .), <b>email</b>, <b>password</b> (at least 10 characters, not common, not the username), <b>full_name</b>, <b>role</b> (teacher or admin; admin needs a super admin).</p>
      <div class="csv-drop" id="users-csv-drop">${icon('upload', 'lg')}<p style="margin:6px 0">Drop a CSV file here or click to browse</p>
        <input type="file" id="users-csv-file" accept=".csv" style="display:none" /><button class="btn btn-sm btn-outline" id="users-csv-browse">Choose file</button></div>
      <div id="users-csv-result" class="mt-1"></div>
      <div class="mt-1"><button class="btn btn-primary" id="users-csv-upload" disabled>Upload &amp; import</button></div>
    </div>
    <div id="usr-table"></div>
  </div>`;
}

function userRow(u, me) {
  const a = new Set(u.allowed_actions || []);
  const name = escHtml(u.username).replace(/'/g, "\\'");
  const roleIcon = { super_admin: 'crown', admin: 'shield', teacher: 'users' }[u.role] || 'user';
  const btns = [
    a.has('edit') && `<button class="btn btn-sm btn-outline btn-icon" title="Edit" aria-label="Edit ${escHtml(u.username)}" onclick="editUser(${u.id})">${icon('edit', 'sm')}</button>`,
    u.signed_in && a.has('deactivate') && `<button class="btn btn-sm btn-outline btn-icon" title="End sessions" onclick="endUserSessions(${u.id}, '${name}')">${icon('logout', 'sm')}<span class="sr-only">End sessions</span></button>`,
    a.has('deactivate') && `<button class="btn btn-sm btn-outline" onclick="setUserActive(${u.id}, '${name}', false)">Deactivate</button>`,
    a.has('reactivate') && `<button class="btn btn-sm btn-outline" onclick="setUserActive(${u.id}, '${name}', true)">Reactivate</button>`,
    a.has('reset_password') && `<button class="btn btn-sm btn-outline btn-icon" title="Reset password" onclick="resetUserPassword(${u.id}, '${name}')">${icon('key', 'sm')}<span class="sr-only">Reset pwd</span></button>`,
    a.has('delete') && `<button class="btn btn-sm btn-danger-ghost btn-icon" title="Delete permanently" onclick="deleteUser(${u.id}, '${name}')">${icon('trash', 'sm')}<span class="sr-only">Delete permanently</span></button>`,
  ].filter(Boolean).join('');
  return `<tr data-user="${u.id}">
    <td><div class="cell-person">${avatar(u.full_name || u.username)}<div><b>${escHtml(u.full_name || u.username)}</b><span>${escHtml(u.email)} · @${escHtml(u.username)}</span></div></div></td>
    <td><span class="role ${escHtml(u.role)}">${icon(roleIcon, 'sm')} ${escHtml(roleName(u.role))}</span></td>
    <td class="nowrap">${u.role === 'teacher' ? `${u.class_count} classroom${u.class_count === 1 ? '' : 's'}` : 'All classrooms'}</td>
    <td>${u.is_active ? statusPill('active', 'Active') : statusPill('inactive', 'Inactive')}${u.signed_in ? ' <span class="badge badge-sm badge-info">Signed in</span>' : ''}</td>
    <td class="text-sm nowrap">${u.last_active_at ? timeAgo(istParseToEpoch(u.last_active_at)) : 'Never'}</td>
    <td><div class="row-actions">${u.id === me.id ? '<span class="text-muted text-sm">You</span>' : ''}${btns}</div></td></tr>`;
}

function wireUsers(app, users, me) {
  const draw = () => {
    const q = UserView.q.toLowerCase();
    const rows = users.filter(u => (UserView.role === 'all' || (UserView.role === 'inactive' ? !u.is_active : u.role === UserView.role))
      && (!q || `${u.username} ${u.full_name || ''} ${u.email}`.toLowerCase().includes(q)));
    const pg = paginate(rows, UserView.page, 10);
    UserView.page = pg.page;
    document.getElementById('usr-table').innerHTML = rows.length ? `<div class="table-wrap"><table class="table">
      <thead><tr><th>User</th><th>Role</th><th>Classrooms</th><th>Status</th><th>Last active</th><th>Actions</th></tr></thead>
      <tbody>${pg.rows.map(u => userRow(u, me)).join('')}</tbody></table></div>
      <div class="table-foot"><span>Showing ${(pg.page - 1) * 10 + 1}–${(pg.page - 1) * 10 + pg.rows.length} of ${rows.length} users</span>${pagerHtml(pg, rows.length, 10, 'usersPage')}</div>`
      : emptyState('No users match', 'Change the search or the role filter.', 'users');
  };
  window.usersPage = (p) => { UserView.page = p; draw(); };
  document.getElementById('usr-q').oninput = (e) => { UserView.q = e.target.value; e.target.defaultValue = e.target.value; UserView.page = 1; draw(); };
  document.getElementById('usr-role').onchange = (e) => { UserView.role = e.target.value; UserView.page = 1; draw(); };
  draw();
  wireUserForms(app);
}

window.endUserSessions = async function (id, name) {
  if (!confirm(`Sign "${name}" out on every device? They can sign in again straight away.`)) return;
  try {
    await adminApi.endSessions(id);
    showToast(`"${name}" was signed out everywhere`, 'success');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

function userModals(isSuper) {
  return `
    <div id="create-user-modal" class="modal hidden"><div class="modal-backdrop" onclick="this.parentElement.classList.add('hidden')"></div>
      <div class="modal-content card"><h2>Invite a user</h2>
        <form id="create-user-form">
          <div class="form-grid-2">
            <div class="form-group"><label for="new-username">Username</label><input type="text" id="new-username" required minlength="3" autocomplete="off" /></div>
            <div class="form-group"><label for="new-fullname">Full name</label><input type="text" id="new-fullname" /></div>
          </div>
          <div class="form-group"><label for="new-email">E-mail</label><input type="email" id="new-email" required /></div>
          <div class="form-group"><label for="new-password">First password</label><input type="password" id="new-password" required minlength="10" autocomplete="new-password" />
            <span class="form-hint">At least 10 characters, not a common password, not the username. Hand it over in person.</span></div>
          <div class="form-group"><label for="new-role">Role</label><select id="new-role"><option value="teacher">Teacher</option>${isSuper ? '<option value="admin">Admin</option>' : ''}</select></div>
          <div class="modal-actions"><button type="button" class="btn btn-outline" onclick="document.getElementById('create-user-modal').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Create</button></div>
        </form></div></div>
    <div id="edit-user-modal" class="modal hidden"><div class="modal-backdrop" onclick="this.parentElement.classList.add('hidden')"></div>
      <div class="modal-content card"><h2>Edit user</h2>
        <form id="edit-user-form"><input type="hidden" id="edit-user-id" />
          <div class="form-group"><label for="edit-username">Username</label><input type="text" id="edit-username" disabled /></div>
          <div class="form-group"><label for="edit-fullname">Full name</label><input type="text" id="edit-fullname" /></div>
          <div class="form-group"><label for="edit-email">E-mail</label><input type="email" id="edit-email" required /></div>
          <div class="form-group" id="edit-role-group"><label for="edit-role">Role</label>
            <select id="edit-role"><option value="teacher">Teacher</option><option value="admin">Admin</option><option value="super_admin">Super admin</option></select>
            <span class="form-hint">Changing the role signs the user out.</span></div>
          <div class="modal-actions"><button type="button" class="btn btn-outline" onclick="document.getElementById('edit-user-modal').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Save</button></div>
        </form></div></div>`;
}

function wireUserForms(app) {
  document.getElementById('create-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await adminApi.createUser({
        username: document.getElementById('new-username').value.trim(),
        full_name: document.getElementById('new-fullname').value.trim(),
        email: document.getElementById('new-email').value.trim(),
        password: document.getElementById('new-password').value,
        role: document.getElementById('new-role').value,
      });
      showToast('User created', 'success');
      renderAdminUsers(app);
    } catch (err) { showToast(err.message, 'error'); }
  });
  const card = document.getElementById('users-csv-card');
  const drop = document.getElementById('users-csv-drop');
  const file = document.getElementById('users-csv-file');
  const upload = document.getElementById('users-csv-upload');
  const result = document.getElementById('users-csv-result');
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
      showToast(`${r.inserted} user(s) imported${r.skipped.length ? `, ${r.skipped.length} skipped` : ''}`, r.skipped.length ? 'warning' : 'success');
      if (!r.skipped.length) { renderAdminUsers(app); return; }
      result.innerHTML = `<p class="warn-line">${r.inserted} inserted, ${r.skipped.length} skipped:</p><div class="table-wrap"><table class="table">
        <thead><tr><th>Row</th><th>Username</th><th>Error</th></tr></thead>
        <tbody>${r.skipped.map(e => `<tr><td>${e.row}</td><td><code>${escHtml(e.roll_number)}</code></td><td class="text-sm">${escHtml(e.error)}</td></tr>`).join('')}</tbody></table></div>`;
    } catch (err) { result.innerHTML = ''; showToast(err.message, 'error'); } finally { upload.disabled = false; }
  };
}

function activityPanel(activity, users, compact) {
  const A = UserView.act;
  return `<div class="card">
    <div class="card-header"><div><h2>${compact ? 'Recent activity' : 'Activity log'}</h2><div class="card-sub">Track the important actions in your workspace. Flagged entries need attention.</div></div>
      <div class="page-actions">
        <select id="act-kind" class="input-sm" style="width:auto" aria-label="Kind of activity">
          <option value="all">All activity</option>${Object.entries(ACTIVITY_KINDS).map(([k, v]) => `<option value="${k}" ${A.kind === k ? 'selected' : ''}>${v.label}</option>`).join('')}
          <option value="flagged" ${A.kind === 'flagged' ? 'selected' : ''}>Flagged only</option></select>
        <select id="act-user" class="input-sm" style="width:auto" aria-label="User"><option value="all">All users</option>
          ${users.map(u => `<option value="${escHtml(u.username)}" ${A.user === u.username ? 'selected' : ''}>${escHtml(u.full_name || u.username)}</option>`).join('')}
          <option value="system" ${A.user === 'system' ? 'selected' : ''}>System</option></select>
        <select id="act-days" class="input-sm" style="width:auto" aria-label="Period">
          ${[['1', 'Last 24 hours'], ['7', 'Last 7 days'], ['30', 'Last 30 days'], ['all', 'All time']].map(([k, t]) => `<option value="${k}" ${A.days === k ? 'selected' : ''}>${t}</option>`).join('')}</select>
        <button class="btn btn-outline btn-sm" id="act-export">${icon('download', 'sm')} Export</button>
      </div></div>
    <div id="act-list" data-compact="${compact ? 1 : 0}"></div></div>`;
}

function wireActivity(activity) {
  const A = UserView.act;
  const filtered = () => activity.filter(a => {
    if (A.kind === 'flagged' && !(a.details || {}).flag) return false;
    if (!['all', 'flagged'].includes(A.kind) && activityKind(a) !== A.kind) return false;
    if (A.user !== 'all' && (A.user === 'system' ? a.username : a.username !== A.user)) return false;
    if (A.days !== 'all' && a.timestamp && Date.now() - istParseToEpoch(a.timestamp) > Number(A.days) * 86400000) return false;
    return true;
  });
  const draw = () => {
    const list = document.getElementById('act-list');
    const rows = filtered();
    const shown = list.dataset.compact === '1' ? rows.slice(0, 6) : rows;
    list.innerHTML = shown.length ? shown.map(activityItem).join('') : emptyState('No activity in this view', 'Change the filters.', 'history');
  };
  ['act-kind', 'act-user', 'act-days'].forEach(id => {
    document.getElementById(id).onchange = (e) => { A[{ 'act-kind': 'kind', 'act-user': 'user', 'act-days': 'days' }[id]] = e.target.value; draw(); };
  });
  document.getElementById('act-export').onclick = () => downloadCsv(`impress-activity-${new Date().toISOString().slice(0, 10)}.csv`,
    ['time (IST)', 'user', 'action', 'entity', 'entity_id', 'flagged', 'details'],
    filtered().map(a => [a.timestamp, a.username || 'system', a.action, a.entity_type, a.entity_id ?? '', (a.details || {}).flag ? 'yes' : '', JSON.stringify(a.details || {})]));
  draw();
}

// ── System: database integrity, clearing data ─────────────────────────

async function renderSystem(app) {
  const user = await authApi.me();
  const isSuper = user.role === 'super_admin';
  const [info, clear] = await Promise.all([systemApi.integrity(), isSuper ? systemApi.clearOptions().catch(() => null) : null]);
  System.db = info.db;
  const lv = info.last_verification || {};
  const deg = info.degraded;
  app.innerHTML = `
    ${renderNavbar(user, '#/admin/system')}
    <div class="container">
      ${pageHeader('System', 'Database integrity, temporary backups and the controlled ways to reset data.', '', 'Administration')}
      <div class="stats-grid">
        ${statCard('Database', info.db === 'ok' ? 'Verified' : 'Degraded', info.db === 'ok' ? 'every row matches its seal' : 'restored automatically, needs review', 'database', info.db === 'ok' ? 'green' : 'red')}
        ${statCard('Rows checked', (lv.rows || 0).toLocaleString('en-IN'), lv.verified_at ? `last check ${timeAgo(istParseToEpoch(lv.verified_at))}` : 'not checked yet', 'shieldCheck', 'blue')}
        ${statCard('Check interval', `${Math.round(info.interval_s / 60)}<small> min</small>`, 'verification and rolling backup', 'clock')}
        ${statCard('Debug mode', System.test_mode ? 'On' : 'Off', System.test_mode ? 'working on test data' : 'real data', 'flask', System.test_mode ? 'amber' : '')}
      </div>
      ${deg ? `<div class="callout danger mb-2" role="alert"><b>${icon('alert', 'sm')} Database degraded since ${istDateTime(istParseToEpoch(deg.since))}.</b>
        <div style="margin-top:6px">${escHtml(deg.message)}</div>
        <div class="flex gap-1 mt-1"><button class="btn btn-sm btn-outline" onclick="sysAck(false)">${icon('check', 'sm')} Acknowledge</button>
        ${isSuper ? `<button class="btn btn-sm btn-danger-soft" onclick="sysAck(true)">Accept the current state as correct</button>` : ''}</div></div>` : ''}
      <div class="grid-2">
        <div class="card">
          <div class="card-header"><div><h2>${icon('shieldCheck')} Database integrity</h2><div class="card-sub">Every change goes through the database gateway; changes made outside imPress are found and repaired.</div></div>
            <button class="btn btn-sm btn-primary" id="sys-verify">${icon('refresh', 'sm')} Verify now</button></div>
          <dl class="kv">
            <dt>State</dt><dd>${info.db === 'ok' ? statusPill('ok', 'Verified') : statusPill('bad', 'Degraded')}</dd>
            <dt>Last verification</dt><dd>${lv.verified_at ? istDateTime(istParseToEpoch(lv.verified_at)) : '—'}</dd>
            <dt>Result</dt><dd>${escHtml(lv.summary || '—')}</dd>
            <dt>Backup folder</dt><dd><code>${escHtml(info.backup_dir)}</code></dd>
          </dl>
          <h3 class="mt-2 mb-1">Temporary backups</h3>
          ${info.backups.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Backup</th><th>Taken</th><th>Size</th></tr></thead><tbody>
            ${info.backups.map(b => `<tr><td><b>${b.name === 'startup.db' ? 'Start-up' : 'Rolling (last good)'}</b><div class="text-sm text-muted">${escHtml(b.name)}</div></td>
              <td>${istDateTime(istParseToEpoch(b.modified))}</td><td>${(b.size / 1024).toFixed(0)} KB</td></tr>`).join('')}</tbody></table></div>`
            : emptyState('No backups yet')}
        </div>
        <div class="card">
          <div class="card-header"><div><h2>${icon('trash')} Clear or reset data</h2><div class="card-sub">The only way to clear the database. A backup is taken first.</div></div></div>
          ${isSuper && clear ? `
            <div class="choice-grid" style="grid-template-columns:1fr">
              ${Object.entries(clear).map(([k, v], i) => `<label class="choice"><input type="radio" name="clr-scope" value="${k}" ${i === 0 ? 'checked' : ''}>
                <div><b>${k === 'class_data' ? 'Clear class data' : 'Reset everything'}</b><span>${escHtml(v.description)}</span></div></label>`).join('')}
            </div>
            <div class="form-group mt-1"><label for="clr-confirm">Type <code id="clr-phrase">${escHtml(Object.values(clear)[0].confirm)}</code> to confirm</label>
              <input id="clr-confirm" autocomplete="off"></div>
            <button class="btn btn-danger" id="clr-go" disabled>${icon('trash', 'sm')} Clear data</button>`
            : `<p class="text-muted">Only a super admin can clear or reset data.</p>`}
        </div>
      </div>
    </div>`;
  document.getElementById('sys-verify').onclick = async (e) => {
    e.target.disabled = true;
    try {
      const st = await systemApi.verify();
      showToast(st.db === 'ok' ? 'The database verifies' : 'The database did not verify: it was restored', st.db === 'ok' ? 'success' : 'error');
      router();
    } catch (err) { showToast(err.message, 'error'); e.target.disabled = false; }
  };
  if (isSuper && clear) {
    const phrase = () => clear[document.querySelector('input[name=clr-scope]:checked').value].confirm;
    const check = () => { document.getElementById('clr-go').disabled = document.getElementById('clr-confirm').value.trim() !== phrase(); };
    document.querySelectorAll('input[name=clr-scope]').forEach(r => r.onchange = () => { document.getElementById('clr-phrase').textContent = phrase(); check(); });
    document.getElementById('clr-confirm').oninput = check;
    document.getElementById('clr-go').onclick = async () => {
      const scope = document.querySelector('input[name=clr-scope]:checked').value;
      try {
        const r = await systemApi.clear(scope, document.getElementById('clr-confirm').value.trim());
        showToast(`Done. A copy was saved first (${r.backup}).`, 'success');
        router();
      } catch (err) { showToast(err.message, 'error'); }
    };
  }
}

window.sysAck = async function (accept) {
  if (accept && !confirm('Accept the database exactly as it is now? It will be re-sealed and treated as correct from now on.')) return;
  try {
    await systemApi.acknowledge(accept);
    System.db = 'ok';
    renderBanners();
    showToast('Acknowledged', 'success');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

// ── Students: richer table (attendance, participation, classes) ────────

window._studentSummary = {};

function _renderStudentTable(students) {
  if (!students.length) return emptyState('No students found', 'Register a student, import a CSV file, or change the search.', 'users');
  const S = window._studentSummary;
  return `<div class="table-wrap"><table class="table">
    <thead><tr><th>Student</th><th>Enrollment no.</th><th>Classes</th><th>Module</th><th>Attendance</th><th>Participation</th><th>Status</th><th></th></tr></thead>
    <tbody>${students.map(s => { const m = S[s.id] || {}; return `<tr>
      <td><div class="cell-person">${avatar(s.student_name)}<div><b>${escHtml(s.student_name)}</b><span>${escHtml([s.program, s.email].filter(Boolean).join(' · ') || '—')}</span></div></div></td>
      <td><code>${escHtml(s.roll_number)}</code></td>
      <td>${(m.classes || []).length ? `<div class="chips" title="${escHtml(m.classes.join(', '))}">${m.classes.slice(0, 1).map(c => `<span class="chip">${escHtml(c)}</span>`).join('')}${m.classes.length > 1 ? `<span class="chip">+${m.classes.length - 1}</span>` : ''}</div>` : '<span class="text-muted">—</span>'}</td>
      <td>${m.module_linked ? `<span class="badge badge-success">${icon('check', 'sm')} Linked</span>` : `<span class="badge badge-warning">${icon('alert', 'sm')} Not linked</span>`}</td>
      <td style="min-width:130px">${bar(m.attendance_pct)}</td><td style="min-width:130px">${bar(m.participation_pct)}</td>
      <td>${s.is_active ? statusPill('active', 'Active') : statusPill('inactive', 'Inactive')}</td>
      <td><div class="row-actions"><a class="btn btn-sm btn-ghost btn-icon" href="#/student?id=${s.id}" title="View" aria-label="View ${escHtml(s.student_name)}">${icon('eye', 'sm')}</a>
        <button class="btn btn-sm btn-ghost btn-icon" title="Edit" aria-label="Edit" onclick="window._editStudent(${s.id})">${icon('edit', 'sm')}</button>
        ${s.is_active ? `<button class="btn btn-sm btn-ghost btn-icon" title="Deactivate" aria-label="Deactivate" onclick="window._deactivateStudent(${s.id})">${icon('pause', 'sm')}</button>`
          : `<button class="btn btn-sm btn-ghost btn-icon" title="Reactivate" aria-label="Reactivate" onclick="window._reactivateStudent(${s.id})">${icon('play', 'sm')}</button>`}
        <button class="btn btn-sm btn-ghost btn-icon text-danger" title="Delete permanently" aria-label="Delete permanently" onclick="window._hardDeleteStudent(${s.id}, '${escHtml(s.student_name).replace(/'/g, "\\'")}')">${icon('trash', 'sm')}</button></div></td>
    </tr>`; }).join('')}</tbody></table></div>`;
}

function studentOverview(students) {
  const S = window._studentSummary;
  const total = students.length;
  const linked = students.filter(s => (S[s.id] || {}).module_linked).length;
  const enrolled = students.filter(s => ((S[s.id] || {}).classes || []).length).length;
  const att = students.map(s => (S[s.id] || {}).attendance_pct).filter(v => v != null);
  const avg = att.length ? Math.round(att.reduce((a, b) => a + b, 0) / att.length) : null;
  const dist = {};
  students.forEach(s => ((S[s.id] || {}).classes || []).forEach(c => { dist[c] = (dist[c] || 0) + 1; }));
  const top = Object.entries(dist).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const p = total ? Math.round(100 * linked / total) : 0;
  return {
    stats: `<div class="stats-grid">
      ${statCard('Total students', total, `${students.filter(s => s.is_active).length} active`, 'users')}
      ${statCard('Enrolled', enrolled, total ? `<b class="up">${Math.round(100 * enrolled / total)}%</b> in at least one class` : '', 'checkCircle', 'green')}
      ${statCard('Not in a class', total - enrolled, 'registered, no enrolment yet', 'clock', 'amber')}
      ${statCard('Module linked', linked, total ? `<b class="up">${p}%</b> have a module` : '', 'module', 'blue')}
    </div>`,
    side: `<div class="card"><div class="card-header"><h2>Student overview</h2><span class="text-sm text-muted">This term</span></div>
      <div class="flex gap-2" style="align-items:center">
        <div class="donut" style="--p:${p}"><div><b>${total}</b><span>Students</span></div></div>
        <div class="legend">
          <div><i style="background:var(--success)"></i>Module linked<b>${linked}</b><span>${p}%</span></div>
          <div><i style="background:var(--surface-3)"></i>No module<b>${total - linked}</b><span>${100 - p}%</span></div>
          <div><i style="background:var(--primary)"></i>Avg. attendance<b>${avg == null ? '—' : avg + '%'}</b><span></span></div>
        </div></div></div>
      <div class="card"><div class="card-header"><h2>Class distribution</h2></div>
        ${top.length ? top.map(([c, n]) => `<div class="feed-item" style="align-items:center"><span class="feed-icon">${icon('school', 'sm')}</span>
          <div class="feed-body"><b>${escHtml(c)}</b></div><b>${n}</b><div class="bar" style="width:90px"><i style="width:${Math.round(100 * n / Math.max(1, total))}%"></i></div></div>`).join('')
          : emptyState('No enrolments yet')}</div>`,
  };
}
