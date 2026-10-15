/* imPress v2.2 dashboards: a grid of widgets that each person arranges (add, remove, drag, resize), saved with their
 * preferences. Several kinds of widget show the same data in different ways (a number, a ring, bars, a list).
 * Administrators with advanced mode on see more detail and a few extra widgets. */

// ── Small charts (SVG, no library) ───────────────────────────────────

const Charts = {
  ring(pct, { size = 84, stroke = 9, label = null, color = 'var(--primary)' } = {}) {
    const r = (size - stroke) / 2, c = 2 * Math.PI * r, p = Math.max(0, Math.min(100, pct || 0));
    return `<svg class="ring" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="${p}%">
      <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="var(--surface-3)" stroke-width="${stroke}"/>
      <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="${color}" stroke-width="${stroke}" stroke-linecap="round"
        stroke-dasharray="${(c * p) / 100} ${c}" transform="rotate(-90 ${size / 2} ${size / 2})" style="transition:stroke-dasharray .8s var(--ease-spatial-slow,ease)"/>
      <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central">${label ?? p + '%'}</text></svg>`;
  },
  donut(parts, size = 96) {
    const total = parts.reduce((n, p) => n + p.value, 0) || 1, r = 34, c = 2 * Math.PI * r;
    let off = 0;
    const arcs = parts.filter(p => p.value > 0).map(p => {
      const len = (p.value / total) * c, el = `<circle cx="50" cy="50" r="${r}" fill="none" stroke="${p.color}" stroke-width="14" stroke-dasharray="${len} ${c - len}" stroke-dashoffset="${-off}" transform="rotate(-90 50 50)"/>`;
      off += len;
      return el;
    }).join('');
    return `<svg width="${size}" height="${size}" viewBox="0 0 100 100" role="img" aria-label="Breakdown"><circle cx="50" cy="50" r="${r}" fill="none" stroke="var(--surface-3)" stroke-width="14"/>${arcs}</svg>`;
  },
  spark(values, color = 'var(--primary)') {
    if (!values || values.length < 2) return '';
    const w = 200, h = 44, max = Math.max(...values, 1), step = w / (values.length - 1);
    const pts = values.map((v, i) => [i * step, h - 4 - (v / max) * (h - 10)]);
    const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><path d="${line} L${w} ${h} L0 ${h}Z" fill="${color}" opacity=".1"/>
      <path d="${line}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>`;
  },
  hbars(rows, max = null) {
    const m = max || Math.max(...rows.map(r => r.value), 1);
    return `<div class="hbars">${rows.map(r => `<div><span class="t" title="${escHtml(r.label)}">${escHtml(r.label)}</span><span class="b"><i style="width:${Math.max(3, (r.value / m) * 100)}%;${r.color ? `background:${r.color}` : ''}"></i></span><span class="n">${Prefs.number(r.value)}</span></div>`).join('')}</div>`;
  },
  legend(parts) { return `<div class="mini-list">${parts.map(p => `<div><span style="width:9px;height:9px;border-radius:3px;background:${p.color};flex:none"></span><span class="grow">${escHtml(p.label)}</span><b>${Prefs.number(p.value)}</b></div>`).join('')}</div>`; },
};

// ── Widgets ──────────────────────────────────────────────────────────
// roles: who may add it. needs: what to fetch. render(ctx, advanced) returns the body HTML.

const num = (n) => Prefs.number(n);
const todays = (ctx) => {
  const { day } = istNow();
  return ctx.classes.filter(c => c.is_active || (c.meeting_schedule || []).some(s => s.day === day))
    .sort((a, b) => ((a.meeting_schedule || []).find(s => s.day === day)?.start || '00') > ((b.meeting_schedule || []).find(s => s.day === day)?.start || '00') ? 1 : -1);
};
const classLabel = (c) => c.course_name || c.name;
const TONES = ['#5b4ee5', '#13955a', '#d97706', '#2563eb', '#e11d48', '#0d9488'];

const WIDGETS = {
  'classes-number': { title: 'Classrooms', icon: 'school', size: 'sm', roles: ['teacher', 'admin'], group: 'Classrooms', blurb: 'How many classrooms you have',
    render: (c, adv) => `<div class="big">${num(c.classes.length)}</div><div class="sub">${c.classes.filter(x => (x.meeting_schedule || []).length).length} with a timetable</div>${adv ? `<div class="sub">${c.classes.filter(x => x.is_active).length} live · ${c.classes.reduce((n, x) => n + (x.quiz_count || 0) + (x.poll_count || 0), 0)} quizzes and polls in total</div>` : ''}` },
  'classes-status': { title: 'Classroom status', icon: 'school', size: 'lg', roles: ['teacher', 'admin'], group: 'Classrooms', blurb: 'Live, upcoming, scheduled and inactive',
    render: (c) => {
      const k = { live: 0, upcoming: 0, scheduled: 0, inactive: 0 };
      c.classes.forEach(x => { k[classStatus(x)[0]] = (k[classStatus(x)[0]] || 0) + 1; });
      const parts = [{ label: 'Live now', value: k.live, color: 'var(--success)' }, { label: 'Upcoming today', value: k.upcoming, color: 'var(--primary)' },
        { label: 'Scheduled', value: k.scheduled, color: 'var(--warning)' }, { label: 'Inactive', value: k.inactive, color: 'var(--border-strong)' }];
      return `<div class="ring-wrap">${Charts.donut(parts)}${Charts.legend(parts)}</div>`;
    } },
  'live-now': { title: 'Live now', icon: 'zap', size: 'sm', roles: ['teacher', 'admin'], group: 'Classrooms', blurb: 'Classes in session',
    render: (c) => { const l = c.classes.filter(x => x.is_active); return `<div class="big" style="color:${l.length ? 'var(--success)' : 'inherit'}">${l.length}</div><div class="sub">${l.length ? escHtml(l.map(classLabel).slice(0, 2).join(', ')) : 'No class in session'}</div>`; } },
  'today': { title: 'Today', icon: 'calendar', size: 'lg', roles: ['teacher', 'admin'], group: 'Classrooms', blurb: 'Classes with a slot today, or live',
    render: (c, adv) => {
      const { day } = istNow(), list = todays(c).slice(0, adv ? 8 : 5);
      return list.length ? list.map(x => { const [k, t] = classStatus(x), slot = (x.meeting_schedule || []).find(s => s.day === day);
        return `<div class="feed-item">${classGlyph(x)}<div class="feed-body"><b>${escHtml(classLabel(x))}</b><span>${escHtml(x.code)}${slot ? ` · ${slot.start}–${slot.end}` : ''}${adv ? ` · ${num(x.student_count || 0)} students` : ''}</span></div>
          ${statusPill(k, t)}<a href="#/class?id=${x.id}" class="btn btn-sm ${x.is_active ? 'btn-primary' : 'btn-outline'}">${x.is_active ? 'Open live' : 'Open'}</a></div>`; }).join('')
        : emptyState('Nothing on today', 'Classes with a slot today, or activated, appear here.', 'calendar');
    } },
  'students-number': { title: 'Students', icon: 'users', size: 'sm', roles: ['teacher', 'admin'], group: 'Students', blurb: 'Enrolled students',
    render: (c, adv) => { const n = c.students ? c.students.length : c.classes.reduce((a, x) => a + (x.student_count || 0), 0);
      return `<div class="big">${num(n)}</div><div class="sub">across ${c.classes.length} classroom${c.classes.length === 1 ? '' : 's'}</div>${adv ? `<div class="sub">${Math.round(n / Math.max(1, c.classes.length))} per classroom on average</div>` : ''}`; } },
  'students-bars': { title: 'Students per classroom', icon: 'users', size: 'lg', roles: ['teacher', 'admin'], group: 'Students', blurb: 'Enrolment by classroom, as bars',
    render: (c) => { const rows = [...c.classes].sort((a, b) => (b.student_count || 0) - (a.student_count || 0)).slice(0, 6).map(x => ({ label: classLabel(x), value: x.student_count || 0 }));
      return rows.length ? Charts.hbars(rows) : emptyState('No classrooms yet', '', 'users'); } },
  'students-ring': { title: 'Where students are', icon: 'pie', size: 'lg', roles: ['teacher', 'admin'], group: 'Students', blurb: 'Share of enrolment, as a ring',
    render: (c) => { const top = [...c.classes].sort((a, b) => (b.student_count || 0) - (a.student_count || 0)).slice(0, 5);
      const parts = top.map((x, i) => ({ label: classLabel(x), value: x.student_count || 0, color: TONES[i % TONES.length] }));
      return parts.some(p => p.value) ? `<div class="ring-wrap">${Charts.donut(parts)}${Charts.legend(parts)}</div>` : emptyState('No students enrolled yet', '', 'users'); } },
  'quizzes-number': { title: 'Quizzes run', icon: 'clipboard', size: 'sm', roles: ['teacher', 'admin'], group: 'Quizzes & polls', blurb: 'Completed quizzes',
    render: (c, adv) => { const o = c.overview || { quizzes: [], polls: [] }; const done = o.quizzes.filter(q => q.status === 'completed').length;
      return `<div class="big">${num(done)}</div><div class="sub">${o.quizzes.length} in total · ${o.polls.length} polls</div>${adv ? `<div class="sub">${num(o.quizzes.reduce((n, q) => n + q.answers, 0))} answers received</div>` : ''}`; } },
  'quiz-status': { title: 'Quizzes and polls', icon: 'poll', size: 'lg', roles: ['teacher', 'admin'], group: 'Quizzes & polls', blurb: 'Status of all sessions, as a ring',
    render: (c) => { const o = c.overview || { quizzes: [], polls: [] }, all = [...o.quizzes, ...o.polls];
      const cnt = (s) => all.filter(x => x.status === s).length;
      const parts = [{ label: 'Live', value: cnt('active'), color: 'var(--success)' }, { label: 'Completed', value: cnt('completed') + cnt('closed'), color: 'var(--primary)' }, { label: 'Draft', value: cnt('draft'), color: 'var(--border-strong)' }];
      return all.length ? `<div class="ring-wrap">${Charts.donut(parts)}${Charts.legend(parts)}</div>` : emptyState('No quizzes or polls yet', 'Create one from a classroom.', 'clipboard'); } },
  'recent-quizzes': { title: 'Recent quizzes', icon: 'clipboard', size: 'lg', roles: ['teacher', 'admin'], group: 'Quizzes & polls', blurb: 'The latest quizzes and their results',
    render: (c, adv) => { const q = (c.overview?.quizzes || []).slice(0, adv ? 6 : 4);
      return q.length ? `<div class="mini-list">${q.map(x => `<div><span class="grow"><b>${escHtml(x.title)}</b><div class="text-sm text-muted">${escHtml(x.class_name)} · ${x.question_count} questions${adv ? ` · ${x.answers} answers` : ''}</div></span>${statusPill(x.status === 'active' ? 'live' : x.status === 'completed' ? 'ok' : 'off', x.status === 'active' ? 'Live' : x.status)}</div>`).join('')}</div>`
        : emptyState('No quizzes yet', 'Create one from a classroom.', 'clipboard'); } },
  'quick-actions': { title: 'Quick actions', icon: 'zap', size: 'md', roles: ['teacher', 'admin'], group: 'Shortcuts', blurb: 'Start something with one click',
    render: (c, adv, user) => `<div style="display:grid;gap:8px"><a class="btn btn-primary" href="#/sessions">${icon('plus', 'sm')} New quiz or poll</a>
      <a class="btn btn-outline" href="${isAdminUser(user) ? '#/admin/classes' : '#/classes'}">${icon('school', 'sm')} Open classrooms</a>
      ${isAdminUser(user) ? `<a class="btn btn-outline" href="#/admin/classes/new">${icon('plus', 'sm')} New classroom</a>` : ''}</div>` },

  'devices-number': { title: 'Devices online', icon: 'radio', size: 'sm', roles: ['admin'], group: 'Devices', blurb: 'Modules and gateways reachable now', needs: ['devices'],
    render: (c) => { const on = c.devices.filter(d => d.is_connected).length; return `<div class="big">${on}<small class="text-muted" style="font-size:17px"> / ${c.devices.length}</small></div><div class="sub">${c.devices.length - on ? `<b class="down" style="color:var(--danger)">${c.devices.length - on}</b> offline` : 'all reachable'}</div>`; } },
  'devices-ring': { title: 'Device health', icon: 'radio', size: 'lg', roles: ['admin'], group: 'Devices', blurb: 'Online share, as a ring', needs: ['devices'],
    render: (c) => { const on = c.devices.filter(d => d.is_connected).length, p = c.devices.length ? Math.round(on * 100 / c.devices.length) : 0;
      return `<div class="ring-wrap">${Charts.ring(p, { color: p >= 90 ? 'var(--success)' : p >= 60 ? 'var(--warning)' : 'var(--danger)' })}<div><b>${on} of ${c.devices.length}</b><div class="sub">devices online</div><a href="#/admin/modules" class="btn btn-sm btn-outline mt-1">Open devices</a></div></div>`; } },
  'accounts-number': { title: 'Accounts', icon: 'userCog', size: 'sm', roles: ['admin'], group: 'Accounts', blurb: 'People with access', needs: ['users'],
    render: (c, adv) => `<div class="big">${num(c.users.length)}</div><div class="sub">${c.users.filter(u => u.signed_in).length} signed in now</div>${adv ? `<div class="sub">${c.users.filter(u => u.status === 'pending_setup').length} pending setup · ${c.users.filter(u => !u.is_active).length} disabled</div>` : ''}` },
  'accounts-roles': { title: 'Accounts by role', icon: 'users', size: 'lg', roles: ['admin'], group: 'Accounts', blurb: 'Super admins, administrators, faculty and TAs', needs: ['users'],
    render: (c) => { const k = (f) => c.users.filter(f).length;
      return Charts.hbars([{ label: 'Super admins', value: k(u => u.role === 'super_admin') }, { label: 'Administrators', value: k(u => u.role === 'admin') },
        { label: 'Faculty', value: k(u => u.role === 'teacher' && u.designation !== 'ta') }, { label: 'Teaching assistants', value: k(u => u.role === 'teacher' && u.designation === 'ta') }]); } },
  'active-users': { title: 'Active now', icon: 'activity', size: 'lg', roles: ['admin'], group: 'Accounts', blurb: 'Who is signed in, and when they last did something', needs: ['presence'],
    render: (c, adv) => { const a = c.presence?.active || [];
      return a.length ? `<div class="mini-list">${a.slice(0, adv ? 8 : 5).map(u => `<div>${avatar(u.name || u.username, 'sm')}<span class="grow"><b>${escHtml(u.name || u.username)}</b><div class="text-sm text-muted">${escHtml(roleTitle(u))}${adv && u.ip ? ' · ' + escHtml(u.ip) : ''}</div></span><span class="text-sm text-muted">${timeAgo(istParseToEpoch(u.last_active_at))}</span></div>`).join('')}</div>`
        : emptyState('Nobody else is signed in', '', 'users'); } },
  'activity': { title: 'Recent activity', icon: 'history', size: 'lg', roles: ['admin'], group: 'System', blurb: 'Sign-ins, changes and system events', needs: ['activity'],
    render: (c, adv) => (c.activity.length ? c.activity.slice(0, adv ? 8 : 5).map(activityItem).join('') : emptyState('No activity yet')) + `<div style="margin-top:8px"><a href="#/admin/activity" class="btn btn-sm btn-outline">View all</a></div>` },
  'system-health': { title: 'System health', icon: 'database', size: 'lg', roles: ['admin'], group: 'System', blurb: 'Database, test mode and backups', needs: ['integrity'],
    render: (c, adv) => { const i = c.integrity, db = i?.db || 'ok', lv = i?.last_verification;
      return `<div class="feed-item"><span class="feed-icon ${db === 'ok' ? 'green' : 'red'}">${icon('database', 'sm')}</span><div class="feed-body"><b>Database</b><span>${db === 'ok' ? 'Verified' : 'Restored automatically'}${lv?.verified_at ? ' · checked ' + timeAgo(istParseToEpoch(lv.verified_at)) : ''}</span></div>${statusPill(db === 'ok' ? 'ok' : 'bad', db === 'ok' ? 'Healthy' : 'Review')}</div>
        <div class="feed-item"><span class="feed-icon ${System.test_mode ? 'amber' : 'grey'}">${icon('flask', 'sm')}</span><div class="feed-body"><b>Test mode</b><span>${System.test_mode ? 'On: working on test data' : 'Off: real data'}</span></div></div>
        ${adv ? `<div class="feed-item"><span class="feed-icon">${icon('archive', 'sm')}</span><div class="feed-body"><b>Backups</b><span>${(i?.backups || []).map(b => `${b.name.replace('.db', '')} ${timeAgo(istParseToEpoch(b.modified))}`).join(' · ') || 'none yet'}</span></div></div>` : ''}`; } },
  'classrooms-table': { title: 'Classrooms today', icon: 'school', size: 'xl', roles: ['admin'], group: 'Classrooms', blurb: 'A table of today’s timetable',
    render: (c) => { const { day } = istNow(), list = todays(c).slice(0, 8);
      return list.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Classroom</th><th>Time</th><th>Status</th><th>Students</th><th>Faculty</th><th></th></tr></thead><tbody>${list.map(x => { const [k, t] = classStatus(x), s = (x.meeting_schedule || []).find(z => z.day === day);
        return `<tr><td><div class="cell-person">${classGlyph(x)}<div><b>${escHtml(classLabel(x))}</b><span>${escHtml(x.code)}${x.classroom_code ? ` · ${escHtml(x.classroom_code)}` : ''}</span></div></div></td><td class="nowrap">${s ? `${s.start}–${s.end}` : '—'}</td><td>${statusPill(k, t)}</td><td>${num(x.student_count || 0)}</td><td class="text-sm">${escHtml(facultyText(x))}</td><td><a href="#/class?id=${x.id}" class="btn btn-sm btn-outline">Open</a></td></tr>`; }).join('')}</tbody></table></div>`
        : emptyState('No classes today', 'Timetabled and activated classrooms appear here.', 'calendar'); } },
  'risk-summary': { title: 'Account safety', icon: 'shieldCheck', size: 'lg', roles: ['admin'], group: 'Security', blurb: 'Accounts by safety badge (advanced mode)', needs: ['risk'], advanced: true,
    render: (c) => { const r = Object.values(c.risk || {}); const n = (l) => r.filter(x => x.label === l).length;
      const parts = [{ label: 'Safe', value: n('Safe'), color: 'var(--success)' }, { label: 'Potentially Unsafe', value: n('Potentially Unsafe'), color: 'var(--warning)' }, { label: 'Likely Compromised', value: n('Likely Compromised'), color: 'var(--danger)' }];
      return r.length ? `<div class="ring-wrap">${Charts.donut(parts)}${Charts.legend(parts)}</div>` : emptyState('No data yet', '', 'shield'); } },
  'traffic': { title: 'Unusual traffic', icon: 'gauge', size: 'lg', roles: ['admin'], group: 'Security', blurb: 'Alerts about request rates (advanced mode)', needs: ['traffic'], advanced: true,
    render: (c) => { const a = c.traffic?.alerts || [];
      return a.length ? `<div class="mini-list">${a.slice(0, 4).map(x => `<div><span class="feed-icon red" style="width:28px;height:28px">${icon('alert', 'sm')}</span><span class="grow"><b>${escHtml(x.type)} · ${escHtml(x.endpoint_kind)}</b><div class="text-sm text-muted">${escHtml(x.origin)}${x.username ? ' · ' + escHtml(x.username) : ''} · ${x.requests_per_minute}/min</div></span></div>`).join('')}</div>`
        : `<div class="big" style="color:var(--success)">Quiet</div><div class="sub">No unusual traffic. The monitor only alerts: it never blocks anyone.</div>`; } },
};

const DEFAULT_LAYOUT = {
  teacher: ['classes-number', 'live-now', 'students-number', 'quizzes-number', 'today', 'recent-quizzes', 'students-bars', 'quiz-status'],
  admin: ['classes-number', 'students-number', 'devices-number', 'accounts-number', 'classrooms-table', 'system-health', 'activity', 'active-users'],
};

function layoutFor(user) {
  const saved = Prefs.cur.dashboard;
  const adv = Prefs.advanced();
  if (Array.isArray(saved) && saved.length) return saved.filter(w => WIDGETS[w.kind]);
  const role = isAdminUser(user) ? 'admin' : 'teacher';
  return [...DEFAULT_LAYOUT[role], ...(role === 'admin' && adv ? ['risk-summary', 'traffic'] : [])].map((kind, i) => ({ id: `w${i + 1}`, kind, size: WIDGETS[kind].size }));
}

function greeting() {
  const h = +new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', hourCycle: 'h23' }).format(new Date());
  return h < 5 ? 'Good evening' : h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
}

const Dash = { layout: [], ctx: null, user: null, editing: false, hash: '#/dashboard' };

function widgetHtml(w) {
  const def = WIDGETS[w.kind];
  let body;
  try { body = def.render(Dash.ctx, Prefs.advanced(), Dash.user); } catch (e) { body = `<div class="text-muted text-sm">This widget could not be drawn.</div>`; console.error(e); }
  return `<section class="widget sz-${w.size || def.size}" data-wid="${escHtml(w.id)}" draggable="${Dash.editing}" aria-label="${escHtml(def.title)}">
    <div class="widget-head"><h3>${icon(def.icon)} ${escHtml(def.title)}</h3>
      <div class="widget-tools"><button type="button" data-w="size" title="Change size" aria-label="Change size of ${escHtml(def.title)}">${icon('maximize', 'sm')}</button>
        <button type="button" data-w="rm" class="rm" title="Remove" aria-label="Remove ${escHtml(def.title)}">${icon('x', 'sm')}</button></div></div>
    <div class="widget-body">${body}</div></section>`;
}

function drawWidgets() {
  const host = document.getElementById('widgets');
  if (!host) return;
  host.classList.toggle('editing', Dash.editing);
  host.innerHTML = Dash.layout.map(widgetHtml).join('') + (Dash.editing ? `<button type="button" class="add-widget" data-w="add">${icon('plus')}<span>Add widget</span></button>` : '');
  document.getElementById('edit-bar')?.classList.toggle('hidden', !Dash.editing);
  const btn = document.getElementById('dash-customise');
  if (btn) btn.innerHTML = Dash.editing ? `${icon('check', 'sm')} Done` : `${icon('layout', 'sm')} Customise`;
}

function saveLayout() { Prefs.save({ dashboard: Dash.layout.map(({ id, kind, size }) => ({ id, kind, size })) }); }

async function dashboardData(user) {
  const admin = isAdminUser(user), adv = Prefs.advanced(), f = System.feature_flags || {};
  const need = new Set(layoutFor(user).flatMap(w => WIDGETS[w.kind].needs || []));
  const get = (key, fn, dflt) => need.has(key) || key === 'core' ? fn().catch(() => dflt) : Promise.resolve(dflt);
  const [classes, overview, users, activity, devices, students, integrity, presence, risk, traffic] = await Promise.all([
    admin ? adminApi.listClasses() : classesApi.list(),
    quizzesApi.overview().catch(() => ({ quizzes: [], polls: [] })),
    get('users', () => adminApi.listUsers(), []), get('activity', () => adminApi.activityLogs(10), []),
    get('devices', () => modulesApi.list(''), []), admin ? studentsApi.list('').catch(() => null) : Promise.resolve(null),
    get('integrity', () => systemApi.integrity(), null),
    get('presence', () => (f.presence === false ? Promise.resolve(null) : adminApi.presence()), null),
    adv && need.has('risk') && f.risk_scores !== false ? adminApi.risk().catch(() => ({})) : Promise.resolve({}),
    adv && need.has('traffic') ? adminApi.traffic().catch(() => null) : Promise.resolve(null),
  ]);
  return { classes, overview, users, activity, devices, students, integrity, presence, risk, traffic };
}

async function renderWidgetDashboard(app, user, hash) {
  Dash.user = user; Dash.hash = hash; Dash.editing = false;
  Dash.layout = layoutFor(user);
  app.innerHTML = `${renderNavbar(user, hash)}<div class="container"><div class="page-skeleton"><div class="skeleton" style="height:34px;width:280px"></div>
    <div class="widgets">${Dash.layout.slice(0, 8).map(w => `<div class="widget sz-${w.size || 'md'}"><div class="skeleton" style="height:16px;width:50%;margin-bottom:12px"></div><div class="skeleton" style="height:48px"></div></div>`).join('')}</div></div></div>`;
  Dash.ctx = await dashboardData(user);
  Shell.counts.classes = Dash.ctx.classes.length;
  const first = (user.name || user.username || '').replace(/^(Dr|Prof)\.?\s+/i, '').split(/\s+/)[0];
  const adv = Prefs.advanced(), admin = isAdminUser(user), f = System.feature_flags || {};
  app.innerHTML = `${renderNavbar(user, hash)}
    <div class="container">
      <div class="dash-hero"><div><div class="dash-eyebrow">${escHtml(todayLabel())}</div>
        <h1 class="dash-title">${greeting()}, ${escHtml(first)}</h1>
        <p class="dash-sub">${admin ? 'A live snapshot of classrooms, devices, accounts and the system.' : 'Your classes today, live sessions and recent results.'}${admin && adv ? ' <span class="badge badge-primary badge-sm">Advanced mode</span>' : ''}</p></div>
        <div class="dash-hero-side">
          ${f.dashboard_widgets !== false ? `<button class="btn btn-outline" id="dash-customise" data-action="dash-edit">${icon('layout', 'sm')} Customise</button>` : ''}
          ${admin ? `<a href="#/admin/classes/new" class="btn btn-primary">${icon('plus', 'sm')} New classroom</a>` : `<a href="#/sessions" class="btn btn-primary">${icon('plus', 'sm')} New quiz or poll</a>`}</div></div>
      <div id="edit-bar" class="edit-bar hidden" role="status">${icon('grip', 'sm')} Drag widgets to rearrange them. Use the corner buttons to resize or remove.
        <span style="flex:1"></span><button class="btn btn-sm btn-outline" data-action="dash-reset">Reset to default</button></div>
      <div id="widgets" class="widgets"></div>
    </div>`;
  drawWidgets();
  wireDashboard();
}

function wireDashboard() {
  const host = document.getElementById('widgets');
  let dragId = null;
  host.addEventListener('click', (e) => {
    const b = e.target.closest('[data-w]');
    if (!b) return;
    const sec = b.closest('.widget'), id = sec?.dataset.wid, w = Dash.layout.find(x => x.id === id);
    if (b.dataset.w === 'rm') { Dash.layout = Dash.layout.filter(x => x.id !== id); saveLayout(); drawWidgets(); }
    else if (b.dataset.w === 'size' && w) { const order = ['sm', 'md', 'lg', 'xl']; w.size = order[(order.indexOf(w.size || WIDGETS[w.kind].size) + 1) % 4]; saveLayout(); drawWidgets(); }
    else if (b.dataset.w === 'add') openWidgetGallery();
  });
  host.addEventListener('dragstart', (e) => { const s = e.target.closest('.widget'); if (!Dash.editing || !s) return; dragId = s.dataset.wid; s.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', dragId); });
  host.addEventListener('dragend', () => { host.querySelectorAll('.dragging, .over').forEach(x => x.classList.remove('dragging', 'over')); dragId = null; });
  host.addEventListener('dragover', (e) => { if (!dragId) return; e.preventDefault(); host.querySelectorAll('.over').forEach(x => x.classList.remove('over')); e.target.closest('.widget')?.classList.add('over'); });
  host.addEventListener('drop', (e) => {
    const t = e.target.closest('.widget');
    if (!dragId || !t || t.dataset.wid === dragId) return;
    e.preventDefault();
    const from = Dash.layout.findIndex(x => x.id === dragId), to = Dash.layout.findIndex(x => x.id === t.dataset.wid);
    Dash.layout.splice(to, 0, Dash.layout.splice(from, 1)[0]);
    saveLayout(); drawWidgets();
  });
}

function openWidgetGallery() {
  const admin = isAdminUser(Dash.user), adv = Prefs.advanced();
  const kinds = Object.entries(WIDGETS).filter(([, d]) => (admin ? d.roles.includes('admin') || d.roles.includes('teacher') : d.roles.includes('teacher')) && (!d.advanced || (admin && adv)));
  const groups = [...new Set(kinds.map(([, d]) => d.group))];
  const m = document.createElement('div');
  m.className = 'modal';
  m.innerHTML = `<div class="modal-backdrop"></div><div class="modal-content card" role="dialog" aria-modal="true" aria-label="Add a widget" style="max-width:720px">
    <div class="flex-between"><h2>Add a widget</h2><button class="btn btn-ghost btn-icon" data-close aria-label="Close">${icon('x')}</button></div>
    <p class="text-muted mb-1">Several widgets can show the same information in different ways.</p>
    ${groups.map(g => `<h3 class="mt-1 mb-1" style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint)">${escHtml(g)}</h3><div class="gallery">${kinds.filter(([, d]) => d.group === g).map(([k, d]) =>
      `<button type="button" data-kind="${k}"><b>${icon(d.icon, 'sm')} ${escHtml(d.title)}</b><span>${escHtml(d.blurb)}</span></button>`).join('')}</div>`).join('')}</div>`;
  document.body.appendChild(m);
  const close = () => m.remove();
  m.querySelector('.modal-backdrop').onclick = close;
  m.addEventListener('click', async (e) => {
    if (e.target.closest('[data-close]')) return close();
    const b = e.target.closest('[data-kind]');
    if (!b) return;
    const kind = b.dataset.kind, id = `w${Date.now().toString(36)}`;
    Dash.layout.push({ id, kind, size: WIDGETS[kind].size });
    if (WIDGETS[kind].needs && Dash.ctx) { // fetch what the new widget needs, once
      const extra = await dashboardData(Dash.user).catch(() => null);
      if (extra) Dash.ctx = { ...Dash.ctx, ...extra };
    }
    saveLayout(); drawWidgets(); close();
  });
  m.querySelector('button[data-kind]')?.focus();
}

Object.assign(Actions, {
  'dash-edit': () => { Dash.editing = !Dash.editing; drawWidgets(); },
  'dash-reset': () => { Prefs.save({ dashboard: [] }).then(() => { Dash.layout = layoutFor(Dash.user); drawWidgets(); }); },
});

async function renderDashboard(app) {
  const user = await authApi.me();
  if (isAdminUser(user)) { navigate('#/admin'); return; }
  return renderWidgetDashboard(app, user, '#/dashboard');
}

async function renderAdminDashboard(app) {
  const user = await authApi.me();
  return renderWidgetDashboard(app, user, '#/admin');
}
