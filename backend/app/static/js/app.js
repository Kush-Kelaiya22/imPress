/* imPress — SPA router + page renderers */

// ── Router ─────────────────────────────────────────────────────

const routes = {
  '#/login': renderLogin,
  '#/dashboard': renderDashboard,
  '#/admin': renderAdminDashboard,
  '#/admin/users': renderAdminUsers,
  '#/admin/courses': renderAdminCourses,
  '#/admin/classes': renderAdminClasses,
  '#/admin/classes/new': renderAdminClassForm,
  '#/admin/students': renderAdminStudents,
  '#/admin/activity': renderAdminActivity,
  '#/classes': renderClasses,
  '#/class': renderClassDetail,
  '#/admin/modules': renderAdminModules,
  '#/settings': renderSettings,
  '#/quiz': renderQuizCreate,
  '#/poll': renderPollCreate,
  '#/quiz-results': renderQuizResults,
  '#/poll-results': renderPollResults,
  '#/student': renderStudentDetail,
};

window.toggleClassStudentForm = function () {
  document.getElementById('class-add-student').classList.toggle('hidden');
};

window.toggleClassCsvImport = function () {
  document.getElementById('class-csv-import').classList.toggle('hidden');
};

// Lightweight roster refresh after enroll — no full page re-render (keeps
// WebSocket + page state intact), so the enroll button no longer "breaks".
window.refreshClassRoster = async function (classId) {
  try {
    const roster = await studentsApi.listClassStudents(classId);
    const tbody = document.getElementById('roster-tbody');
    if (tbody) {
      tbody.innerHTML = roster.map(s => `
        <tr>
          <td><strong>${escHtml(s.student_name)}</strong></td>
          <td>${escHtml(s.roll_number || '—')}</td>
          <td class="text-muted">${escHtml(s.email || '—')}</td>
          <td>${s.device_mac ? `<code>${escHtml(s.device_mac)}</code>` : '<span class="text-muted">Not linked</span>'}</td>
          <td><a href="#/student?id=${s.id}&class=${classId}" class="btn btn-sm btn-outline">View</a></td>
          <td><button class="btn btn-sm btn-danger-ghost" onclick="unenrollStudent(${classId}, ${s.id})">Unenroll</button></td>
        </tr>
      `).join('');
    }
    const countEl = document.querySelector('.page-header h1, .card-header h2');
    const headerEl = Array.from(document.querySelectorAll('.card-header h2'))
      .find(h => h.textContent.includes('Students'));
    if (headerEl) headerEl.textContent = `🎓 Students (${roster.length})`;
    window._rosterNames = Object.fromEntries(roster.map(s => [s.id, s.student_name]));
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.unenrollStudent = async function (classId, studentId) {
  const name = window._rosterNames?.[studentId];
  if (!confirm(`Remove ${name || 'this student'} from the class roster? They will remain in the universal registry.`)) return;
  try {
    await studentsApi.unenroll(classId, studentId);
    showToast('Student unenrolled', 'success');
    renderClassDetail(document.getElementById('app'), { id: String(classId) });
  } catch (err) { showToast(err.message, 'error'); }
};

function navigate(hash) {
  window.location.hash = hash;
}

function getRoute() {
  const hash = window.location.hash || '#/login';
  const path = hash.split('?')[0];
  return path;
}

function getParams() {
  const hash = window.location.hash || '';
  const qs = hash.split('?')[1] || '';
  return new URLSearchParams(qs);
}

/* Each navigation renders through its own guarded view of #app. If the user
 * has moved on before a slow page finished loading, that page's late write
 * throws StaleRender instead of painting over the newer page (#51). A wrapper
 * element would also work, but the CSS relies on `#app > .container`. */
let routeSeq = 0;
class StaleRender extends Error {}

function viewFor(seq) {
  const el = document.getElementById('app');
  return new Proxy(el, {
    set(target, prop, value) {
      if (seq !== routeSeq) throw new StaleRender();
      target[prop] = value;
      return true;
    },
    get(target, prop) {
      const v = Reflect.get(target, prop);
      return typeof v === 'function' ? v.bind(target) : v;
    },
  });
}

// A superseded page's in-flight work may still reject with StaleRender.
window.addEventListener('unhandledrejection', (e) => {
  if (e.reason instanceof StaleRender) e.preventDefault();
});

async function router() {
  const seq = ++routeSeq;
  const app = viewFor(seq);
  const path = getRoute();
  const handler = routes[path];

  // Drop any stale class-form listeners before rendering a new route
  if (window.formFacultyOutsideClick) {
    document.removeEventListener('click', window.formFacultyOutsideClick);
    window.formFacultyOutsideClick = null;
  }

  if (!handler) {
    app.innerHTML = `<div class="container mt-2"><div class="card"><h1>404</h1><p>Page not found.</p><a href="#/dashboard" class="btn btn-primary mt-1">Go Home</a></div></div>`;
    return;
  }

  // Auth guard
  if (path !== '#/login' && !isLoggedIn()) {
    navigate('#/login');
    return;
  }

  try {
    await handler(app, getParams());
  } catch (err) {
    if (err instanceof StaleRender || seq !== routeSeq) return;   // superseded navigation
    if (err.message === 'Unauthorized') return;
    app.innerHTML = `<div class="container mt-2"><div class="card"><h1>Error</h1><p>${escHtml(err.message)}</p><a href="#/dashboard" class="btn btn-primary mt-1">Go Home</a></div></div>`;
  }
}

window.addEventListener('hashchange', router);
window.addEventListener('load', router);

// ── Toast ──────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── Navbar ─────────────────────────────────────────────────────

function renderNavbar(user, currentHash) {
  const role = user.role || 'teacher';
  const isAdmin = role === 'admin' || role === 'super_admin';
  const links = [];

  if (isAdmin) {
    links.push({ href: '#/admin', label: '🏠 Admin', active: currentHash === '#/admin' });
    links.push({ href: '#/admin/courses', label: '📘 Courses', active: currentHash === '#/admin/courses' });
    links.push({ href: '#/admin/students', label: '🎓 Students', active: currentHash === '#/admin/students' });
    links.push({ href: '#/admin/classes', label: '🏫 Classrooms', active: currentHash === '#/admin/classes' });
    links.push({ href: '#/admin/modules', label: '📡 Modules', active: currentHash === '#/admin/modules' });
    links.push({ href: '#/admin/users', label: '👥 Users', active: currentHash === '#/admin/users' });
    links.push({ href: '#/admin/activity', label: '📋 Activity', active: currentHash === '#/admin/activity' });
  } else {
    // Teachers: My Classes (admins manage classes via /admin/classes, R2)
    links.push({ href: '#/classes', label: '📖 My Classes', active: currentHash === '#/classes' });
  }

  const navItems = links.map(l =>
    `<a href="${l.href}" class="nav-link${l.active ? ' active' : ''}">${l.label}</a>`
  ).join('');

  return `
    <nav class="navbar">
      <div class="container nav-inner">
        <a href="#/dashboard" class="nav-brand">📚 imPress</a>
        <div class="nav-links">${navItems}</div>
        <div class="nav-right">
          <button class="btn btn-sm btn-outline theme-toggle" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle theme">
            <span id="theme-icon">🌙</span>
          </button>
          <a href="#/settings" class="btn btn-sm btn-outline nav-settings-btn" title="Settings">⚙️ Settings</a>
          <span class="badge">${escHtml(user.full_name || user.username)}</span>
          <button class="btn btn-sm btn-outline" onclick="handleLogout()">Logout</button>
        </div>
      </div>
    </nav>
  `;
}

window.handleLogout = function () {
  authApi.logout();
  navigate('#/login');
};

// ── Login ──────────────────────────────────────────────────────

async function renderLogin(app) {
  app.innerHTML = `
    <div class="login-page">
      <button class="theme-fab" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle theme">
        <span class="icon-moon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></span>
        <span class="icon-sun"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg></span>
      </button>
      <div class="login-card card">
        <div class="login-header">
          <span class="login-icon">📚</span>
          <h1>imPress</h1>
          <p class="text-muted">Classroom Participation System</p>
        </div>
        <form id="login-form">
          <div class="form-group">
            <label>Username</label>
            <input type="text" id="login-user" required autocomplete="username" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" id="login-pass" required autocomplete="current-password" />
          </div>
          <button type="submit" class="btn btn-primary btn-block">Sign In</button>
          <p id="login-error" class="text-danger text-center mt-1" style="display:none"></p>
        </form>
      </div>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('login-error');
    errEl.style.display = 'none';
    try {
      const username = document.getElementById('login-user').value.trim();
      const password = document.getElementById('login-pass').value;
      await authApi.login(username, password);
      navigate('#/dashboard');
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
    }
  });
}

// ── Settings (change password) ──────────────────────────────────

async function renderSettings(app) {
  const user = await authApi.me();
  app.innerHTML = `
    ${renderNavbar(user, '#/settings')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>⚙️ Settings</h1>
      </div>

      <div class="card card-form" style="max-width:480px">
        <div class="card-header">
          <h2>Account</h2>
        </div>
        <div class="form-grid">
          <label>Username
            <input type="text" value="${escHtml(user.username)}" disabled>
          </label>
          <label>Role
            <input type="text" value="${escHtml(user.role)}" disabled>
          </label>
        </div>
        <form id="settings-name-form">
          <div class="form-grid">
            <label>Full name
              <input type="text" id="settings-name" value="${escHtml(user.full_name || '')}" required maxlength="128">
            </label>
          </div>
          <p id="settings-name-error" class="text-danger" style="display:none"></p>
          <button type="submit" class="btn btn-primary mt-1">Update name</button>
        </form>
      </div>

      <div class="card card-form" style="max-width:480px">
        <div class="card-header">
          <h2>Change password</h2>
        </div>
        <form id="settings-password-form">
          <div class="form-grid">
            <label>Current password
              <input type="password" id="settings-current" required autocomplete="current-password">
            </label>
            <label>New password
              <input type="password" id="settings-new" required minlength="6" autocomplete="new-password">
            </label>
            <label>Confirm new password
              <input type="password" id="settings-confirm" required minlength="6" autocomplete="new-password">
            </label>
          </div>
          <p id="settings-error" class="text-danger" style="display:none"></p>
          <button type="submit" class="btn btn-primary mt-1">Update password</button>
        </form>
      </div>
    </div>
  `;

  document.getElementById('settings-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('settings-error');
    errEl.style.display = 'none';
    const current = document.getElementById('settings-current').value;
    const next = document.getElementById('settings-new').value;
    const confirm = document.getElementById('settings-confirm').value;
    if (next !== confirm) {
      errEl.textContent = 'New passwords do not match';
      errEl.style.display = 'block';
      return;
    }
    if (next.length < 6) {
      errEl.textContent = 'New password must be at least 6 characters';
      errEl.style.display = 'block';
      return;
    }
    try {
      await authApi.changePassword(current, next);
      showToast('Password updated', 'success');
      document.getElementById('settings-password-form').reset();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
    }
  });

  document.getElementById('settings-name-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('settings-name-error');
    errEl.style.display = 'none';
    const name = document.getElementById('settings-name').value.trim();
    if (!name) {
      errEl.textContent = 'Full name cannot be blank';
      errEl.style.display = 'block';
      return;
    }
    try {
      const updated = await authApi.updateProfile(name);
      showToast('Name updated', 'success');
      const badge = document.querySelector('.navbar .badge');
      if (badge) badge.textContent = updated.full_name || updated.username;
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
    }
  });
}

// ── Dashboard ──────────────────────────────────────────────────

async function renderDashboard(app) {
  const user = await authApi.me();
  const isAdmin = user.role === 'admin' || user.role === 'super_admin';

  if (isAdmin) {
    navigate('#/admin');
    return;
  }

  const classes = await classesApi.list();
  const activeClasses = classes.filter(c => c.is_active);

  app.innerHTML = `
    ${renderNavbar(user, '#/dashboard')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>Welcome back, ${escHtml(user.full_name || user.username)}</h1>
        <p class="text-muted">Faculty Dashboard</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-icon">📖</span>
          <div class="stat-value">${classes.length}</div>
          <div class="stat-label">My Classes</div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">🟢</span>
          <div class="stat-value">${activeClasses.length}</div>
          <div class="stat-label">Active Now</div>
        </div>
      </div>

      <div class="card mt-2">
        <div class="card-header">
          <h2>My Classes</h2>
          <a href="#/classes" class="btn btn-sm btn-primary">View All</a>
        </div>
        ${classes.length === 0 ? '<p class="text-muted" style="padding:1rem">No classes assigned yet. Contact your admin.</p>' : ''}
        ${classes.slice(0, 5).map(c => `
          <a href="#/class?id=${c.id}" class="list-item">
            <div>
              <strong>${escHtml(c.course_name || c.name)}</strong>
              <span class="badge badge-sm ${c.is_active ? 'badge-success' : 'badge-outline'}">${c.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            <div class="text-muted text-sm">${c.course_code ? `${escHtml(c.course_code)} · ` : ''}${c.student_count || 0} students · ${c.quiz_count || 0} quizzes · ${c.poll_count || 0} polls${c.term ? ` · ${escHtml(c.term)} ${c.year || ''}` : ''}</div>
          </a>
        `).join('')}
      </div>
    </div>
  `;
}

// ── Admin Dashboard ────────────────────────────────────────────

async function renderAdminDashboard(app) {
  const user = await authApi.me();
  const [classes, users, activity, modules, students] = await Promise.all([
    adminApi.listClasses(),
    adminApi.listUsers(),
    adminApi.activityLogs(10),
    modulesApi.list('').catch(() => []),
    studentsApi.list('').catch(() => []),
  ]);

  const teachers = users.filter(u => u.role === 'teacher');
  const admins = users.filter(u => u.role === 'admin' || u.role === 'super_admin');
  const activeClasses = classes.filter(c => c.is_active);
  const devicesOnline = modules.filter(m => m.is_connected).length;
  const totalStudents = students.length || classes.reduce((n, c) => n + (c.student_count || 0), 0);
  const firstName = (user.full_name || user.username || '').trim().split(/\s+/)[0] || 'Admin';
  const todayStr = istFormat(Date.now(), { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  const nodeRows = classes.slice(0, 15).map(c => {
    const fac = (c.faculty_names && c.faculty_names.length)
      ? c.faculty_names.map(f => f.full_name || f.username || '—').slice(0, 2).join(', ')
      : (c.teacher_name || '—');
    return `
      <tr>
        <td>
          <strong>${escHtml(c.name)}</strong>
          ${c.code ? `<div class="text-muted text-sm">${escHtml(c.code)}</div>` : ''}
        </td>
        <td>${c.classroom_code ? `<span class="text-muted text-sm">${escHtml(c.classroom_code)}</span>` : '<span class="text-muted text-sm">—</span>'}</td>
        <td><span class="badge ${c.is_active ? 'badge-success' : 'badge-outline'}">${c.is_active ? 'Active' : 'Inactive'}</span></td>
        <td>${c.student_count || 0}</td>
        <td class="text-muted text-sm">${escHtml(fac)}</td>
        <td><a href="#/class?id=${c.id}" class="btn btn-sm btn-outline">Open</a></td>
      </tr>
    `;
  }).join('');

  const userRows = users.slice(0, 7).map(u => {
    const initials = (u.full_name || u.username || '?').trim().charAt(0).toUpperCase();
    return `
      <a href="#/admin/users" class="dash-person">
        <span class="dash-avatar">${escHtml(initials)}</span>
        <span class="dash-person-body">
          <span class="dash-person-name">${escHtml(u.full_name || u.username)}</span>
          <span class="dash-person-meta">@${escHtml(u.username)} · ${u.role}</span>
        </span>
        <span class="dash-person-status ${u.is_active ? 'on' : 'off'}" title="${u.is_active ? 'Active' : 'Disabled'}"></span>
      </a>
    `;
  }).join('');

  const eventRows = activity.slice(0, 7).map(a => `
    <div class="dash-event">
      <div class="dash-event-dot"></div>
      <div class="dash-event-body">
        <div class="dash-event-main">${escHtml(a.action)}<span class="dash-event-tag">${escHtml(a.entity_type || '')}</span></div>
        <div class="dash-event-meta">${a.username ? escHtml(a.username) : 'system'} · ${a.timestamp ? istDateTime(istParseToEpoch(a.timestamp)) : ''}</div>
      </div>
    </div>
  `).join('');

  app.innerHTML = `
    ${renderNavbar(user, '#/admin')}
    <div class="container mt-2">

      <div class="dash-hero">
        <div>
          <div class="dash-eyebrow">Operations Overview</div>
          <h1 class="dash-title">Good day, ${escHtml(firstName)}</h1>
          <p class="dash-sub">Live snapshot of your platform — users, classrooms, devices and activity.</p>
        </div>
        <div class="dash-hero-side">
          <div class="dash-date">${todayStr}</div>
          <span class="dash-live"><span class="dash-dot"></span>System online</span>
        </div>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon">👥</div>
          <div class="kpi-body">
            <div class="kpi-label">Total Users</div>
            <div class="kpi-value">${users.length}</div>
            <div class="kpi-sub">${admins.length} admins · ${teachers.length} faculty</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon">🏫</div>
          <div class="kpi-body">
            <div class="kpi-label">Active Classes</div>
            <div class="kpi-value">${activeClasses.length}<span class="kpi-unit"> / ${classes.length}</span></div>
            <div class="kpi-sub">${classes.length - activeClasses.length} inactive</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon">🎓</div>
          <div class="kpi-body">
            <div class="kpi-label">Students</div>
            <div class="kpi-value">${totalStudents}</div>
            <div class="kpi-sub">Across ${classes.length} classrooms</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon">📡</div>
          <div class="kpi-body">
            <div class="kpi-label">Devices Online</div>
            <div class="kpi-value">${devicesOnline}<span class="kpi-unit"> / ${modules.length}</span></div>
            <div class="kpi-sub">${modules.length - devicesOnline} offline</div>
          </div>
        </div>
      </div>

      <div class="metric-strip">
        <span class="metric-chip">Faculty <b>${teachers.length}</b></span>
        <span class="metric-chip">Admins <b>${admins.length}</b></span>
        <span class="metric-chip">Classrooms <b>${classes.length}</b></span>
        <span class="metric-chip">Recent Events <b>${activity.length}</b></span>
      </div>

      <div class="card mt-2 dash-panel">
        <div class="card-header">
          <h2>Live Classroom Nodes</h2>
          <a href="#/admin/classes" class="btn btn-sm btn-outline">Manage</a>
        </div>
        ${classes.length === 0
          ? '<p class="text-muted" style="padding:1rem">No classrooms yet. <a href="#/admin/classes/new">Create one</a>.</p>'
          : `<div class="table-responsive">
              <table class="table">
                <thead>
                  <tr>
                    <th>Classroom</th>
                    <th>Room</th>
                    <th>Status</th>
                    <th>Students</th>
                    <th>Faculty</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>${nodeRows}</tbody>
              </table>
            </div>`}
      </div>

      <div class="grid-2 mt-2">
        <div class="card">
          <div class="card-header">
            <h2>Recent Activity</h2>
            <a href="#/admin/activity" class="btn btn-sm btn-outline">View All</a>
          </div>
          ${activity.length === 0
            ? '<p class="text-muted" style="padding:1rem">No activity yet.</p>'
            : `<div class="dash-events">${eventRows}</div>`}
        </div>

        <div class="card">
          <div class="card-header">
            <h2>User Accounts</h2>
            <a href="#/admin/users" class="btn btn-sm btn-outline">Manage</a>
          </div>
          ${users.length === 0
            ? '<p class="text-muted" style="padding:1rem">No users yet.</p>'
            : `<div class="dash-people">${userRows}</div>`}
        </div>
      </div>
    </div>
  `;
}

// ── Admin: User Management ────────────────────────────────────

async function renderAdminUsers(app) {
  const user = await authApi.me();
  const users = await adminApi.listUsers();
  const isSuperAdmin = user.role === 'super_admin';

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/users')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>User Management</h1>
        <div style="display:flex;gap:0.5rem">
          <button class="btn btn-outline" id="btn-import-users-csv">⬆ Import CSV</button>
          <button class="btn btn-primary" onclick="document.getElementById('create-user-modal').classList.remove('hidden')">+ New User</button>
        </div>
      </div>

      <!-- Bulk User CSV Import -->
      <div class="card hidden" id="users-csv-card" style="margin-top:1rem">
        <div class="card-header">
          <h2>Import Users from CSV</h2>
          <button class="btn btn-sm btn-outline" onclick="document.getElementById('users-csv-card').classList.add('hidden')">✕</button>
        </div>
        <div style="padding:1rem">
          <p class="form-hint" style="margin-top:0;margin-bottom:0.75rem">
            All 5 columns below are <strong>compulsory</strong> in every row — no extra columns:
            <strong>username</strong> (3–64 letters/digits/_ .), <strong>email</strong>, <strong>password</strong> (min 6 chars),
            <strong>full_name</strong>, <strong>role</strong> (teacher or admin). Admin accounts require super-admin rights.
          </p>
          <div class="csv-drop" id="users-csv-drop">
            <p style="margin:0 0 0.5rem">Drop CSV file here or click to browse</p>
            <input type="file" id="users-csv-file" accept=".csv" style="display:none" />
            <button class="btn btn-sm btn-outline" id="users-csv-browse">Choose File</button>
          </div>
          <div id="users-csv-result" class="mt-1"></div>
          <div class="mt-1"><button class="btn btn-primary" id="users-csv-upload" disabled>Upload & Import</button></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><h2>All Users (${users.length})</h2></div>
        <div class="table-responsive">
          <table class="table">
            <thead><tr><th>Username</th><th>Full Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              ${users.map(u => `
                <tr>
                  <td><strong>${escHtml(u.username)}</strong></td>
                  <td>${escHtml(u.full_name || '—')}</td>
                  <td class="text-muted">${escHtml(u.email)}</td>
                  <td><span class="badge ${u.role === 'super_admin' ? 'badge-primary' : u.role === 'admin' ? 'badge-success' : 'badge-outline'}">${u.role}</span></td>
                  <td><span class="badge ${u.is_active ? 'badge-success' : 'badge-danger'}">${u.is_active ? 'Active' : 'Disabled'}</span></td>
                  <td>
                    ${u.id !== user.id ? `
                      <button class="btn btn-sm btn-outline" onclick="editUser(${u.id})">✏️ Edit</button>
                      <button class="btn btn-sm btn-outline" onclick="toggleUserActive(${u.id}, ${u.is_active})">
                        ${u.is_active ? 'Disable' : 'Enable'}
                      </button>
                      <button class="btn btn-sm btn-outline" onclick="resetUserPassword(${u.id}, '${escHtml(u.username).replace(/'/g, "\\'")}')">Reset pwd</button>
                      <button class="btn btn-sm btn-outline text-danger" onclick="deleteUser(${u.id}, '${escHtml(u.username).replace(/'/g, "\\'")}')">🗑</button>
                    ` : '<span class="text-muted text-sm">You</span>'}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Create User Modal -->
      <div id="create-user-modal" class="modal hidden">
        <div class="modal-backdrop" onclick="this.parentElement.classList.add('hidden')"></div>
        <div class="modal-content card">
          <h2>Create New User</h2>
          <form id="create-user-form">
            <div class="form-group">
              <label>Username</label>
              <input type="text" id="new-username" required minlength="3" />
            </div>
            <div class="form-group">
              <label>Full Name</label>
              <input type="text" id="new-fullname" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input type="email" id="new-email" required />
            </div>
            <div class="form-group">
              <label>Password</label>
              <input type="password" id="new-password" required minlength="6" />
            </div>
            <div class="form-group">
              <label>Role</label>
              <select id="new-role">
                <option value="teacher">Teacher</option>
                ${isSuperAdmin ? '<option value="admin">Admin</option>' : ''}
              </select>
            </div>
            <div class="flex gap-1">
              <button type="submit" class="btn btn-primary">Create</button>
              <button type="button" class="btn btn-outline" onclick="document.getElementById('create-user-modal').classList.add('hidden')">Cancel</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Edit User Modal -->
      <div id="edit-user-modal" class="modal hidden">
        <div class="modal-backdrop" onclick="this.parentElement.classList.add('hidden')"></div>
        <div class="modal-content card">
          <h2>Edit User</h2>
          <form id="edit-user-form">
            <input type="hidden" id="edit-user-id" />
            <div class="form-group">
              <label>Username</label>
              <input type="text" id="edit-username" disabled />
            </div>
            <div class="form-group">
              <label>Full Name</label>
              <input type="text" id="edit-fullname" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input type="email" id="edit-email" required />
            </div>
            <div class="form-group">
              <label>Role</label>
              <select id="edit-role">
                <option value="teacher">Teacher</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div class="flex gap-1">
              <button type="submit" class="btn btn-primary">Save</button>
              <button type="button" class="btn btn-outline" onclick="document.getElementById('edit-user-modal').classList.add('hidden')">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

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
      showToast('User created!', 'success');
      renderAdminUsers(app);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // ── Bulk user CSV import ─────────────────────────────────────
  const usersCsvCard = document.getElementById('users-csv-card');
  const usersCsvDrop = document.getElementById('users-csv-drop');
  const usersCsvFile = document.getElementById('users-csv-file');
  const usersCsvUpload = document.getElementById('users-csv-upload');
  const usersCsvResult = document.getElementById('users-csv-result');
  let selectedUsersCsv = null;

  document.getElementById('btn-import-users-csv').onclick = () => {
    usersCsvCard.classList.toggle('hidden');
    if (!usersCsvCard.classList.contains('hidden')) usersCsvCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  };

  document.getElementById('users-csv-browse').onclick = (e) => { e.stopPropagation(); usersCsvFile.click(); };
  usersCsvDrop.onclick = () => usersCsvFile.click();
  usersCsvDrop.ondragover = (e) => { e.preventDefault(); usersCsvDrop.style.borderColor = 'var(--primary)'; };
  usersCsvDrop.ondragleave = () => { usersCsvDrop.style.borderColor = ''; };
  usersCsvDrop.ondrop = (e) => {
    e.preventDefault();
    usersCsvDrop.style.borderColor = '';
    if (e.dataTransfer.files.length) {
      usersCsvFile.files = e.dataTransfer.files;
      usersCsvFile.dispatchEvent(new Event('change'));
    }
  };

  usersCsvFile.addEventListener('change', () => {
    const f = usersCsvFile.files[0];
    if (!f) { selectedUsersCsv = null; usersCsvUpload.disabled = true; return; }
    if (!f.name.toLowerCase().endsWith('.csv')) {
      showToast('Please choose a .csv file', 'error');
      usersCsvFile.value = '';
      selectedUsersCsv = null;
      usersCsvUpload.disabled = true;
      return;
    }
    selectedUsersCsv = f;
    usersCsvUpload.disabled = false;
    usersCsvResult.innerHTML = `<p class="text-muted text-sm">Ready: ${escHtml(f.name)}</p>`;
  });

  usersCsvUpload.onclick = async () => {
    if (!selectedUsersCsv) return;
    usersCsvUpload.disabled = true;
    usersCsvResult.innerHTML = '<p class="text-muted text-sm">Importing…</p>';
    try {
      const result = await adminApi.importUsersCsv(selectedUsersCsv);
      if (result.skipped.length) {
        usersCsvResult.innerHTML = `
          <p style="color:var(--warning)">${result.inserted} inserted, ${result.skipped.length} skipped:</p>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Row</th><th>Username</th><th>Error</th></tr></thead>
            <tbody>${result.skipped.map(e => `<tr><td>${e.row}</td><td><code>${escHtml(e.roll_number)}</code></td><td class="text-sm">${escHtml(e.error)}</td></tr>`).join('')}</tbody>
          </table></div>`;
      } else {
        usersCsvResult.innerHTML = `<p style="color:var(--success)">✓ ${result.inserted} user(s) imported</p>`;
      }
      showToast(`${result.inserted} user(s) imported`, 'success');
      renderAdminUsers(app);
    } catch (err) {
      usersCsvResult.innerHTML = '';
      showToast(err.message, 'error');
    } finally {
      usersCsvUpload.disabled = false;
    }
  };
}

window.toggleUserActive = async function (userId, currentActive) {
  try {
    await adminApi.updateUser(userId, { is_active: !currentActive });
    showToast(currentActive ? 'User disabled' : 'User enabled', 'success');
    const app = document.getElementById('app');
    renderAdminUsers(app);
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.resetUserPassword = async function (userId, username) {
  const newPassword = prompt(`Set a new password for ${username || `user #${userId}`} (min 6 chars):`);
  if (!newPassword || newPassword.trim().length < 6) {
    showToast('Password must be at least 6 characters', 'error');
    return;
  }
  try {
    await adminApi.resetPassword(userId, newPassword.trim());
    showToast(`Password reset for ${username || `user #${userId}`}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.editUser = async function (userId) {
  const modal = document.getElementById('edit-user-modal');
  if (!modal) return;
  try {
    const users = await adminApi.listUsers();
    const u = users.find((x) => x.id === userId);
    if (!u) return;
    document.getElementById('edit-user-id').value = u.id;
    document.getElementById('edit-username').value = u.username;
    document.getElementById('edit-fullname').value = u.full_name || '';
    document.getElementById('edit-email').value = u.email || '';
    const roleSel = document.getElementById('edit-role');
    roleSel.value = u.role === 'admin' ? 'admin' : 'teacher';
    roleSel.disabled = u.role === 'super_admin';  // never change super admin
    modal.classList.remove('hidden');
    document.getElementById('edit-user-form').onsubmit = async (e) => {
      e.preventDefault();
      try {
        await adminApi.updateUser(u.id, {
          full_name: document.getElementById('edit-fullname').value.trim(),
          email: document.getElementById('edit-email').value.trim(),
          role: document.getElementById('edit-role').value,
        });
        showToast('User updated!', 'success');
        modal.classList.add('hidden');
        renderAdminUsers(document.getElementById('app'));
      } catch (err) {
        showToast(err.message, 'error');
      }
    };
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.deleteUser = async function (userId, username) {
  if (!confirm(`Delete user "${username || userId}"? They will be deactivated, not removed from history.`)) return;
  try {
    await adminApi.deleteUser(userId);
    showToast('User deleted', 'success');
    renderAdminUsers(document.getElementById('app'));
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ── Admin: Course Catalog ─────────────────────────────────────

async function renderAdminCourses(app) {
  const user = await authApi.me();
  const courses = await coursesApi.list();

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/courses')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>Course Catalog</h1>
        <button class="btn btn-primary" id="btn-new-course">+ New Course</button>
      </div>

      <div class="card hidden" id="course-form-card">
        <div class="card-header">
          <h2 id="course-form-title">New Course</h2>
          <button class="btn btn-sm btn-outline" onclick="this.closest('.card').classList.add('hidden')">✕</button>
        </div>
        <form id="course-form" style="padding:1rem">
          <div class="form-section">
            <div class="form-section-title">Course Details</div>
            <div class="form-grid-3">
              <div class="form-group">
                <label>Course Code *</label>
                <input type="text" id="cf-code" required maxlength="16" placeholder="e.g. CS101" />
              </div>
              <div class="form-group">
                <label>Course Name *</label>
                <input type="text" id="cf-name" required maxlength="128" placeholder="e.g. Intro to CS" />
              </div>
              <div class="form-group">
                <label>Credits</label>
                <input type="number" id="cf-credits" min="0" max="12" value="3" />
              </div>
            </div>
            <div class="form-grid-2" style="margin-top:0.75rem">
              <div class="form-group">
                <label>Department</label>
                <input type="text" id="cf-dept" maxlength="64" placeholder="e.g. Computer Science" />
              </div>
              <div class="form-group">
                <label>Description</label>
                <input type="text" id="cf-desc" maxlength="256" placeholder="Optional" />
              </div>
            </div>
          </div>
          <div class="form-section">
            <div class="form-section-title">End-Sem Exam Schedule</div>
            <p class="form-hint" style="margin-top:-0.5rem;margin-bottom:0.75rem">Applies to all sections of this course.</p>
            <div class="form-grid-3">
              <div class="form-group">
                <label>Exam Date</label>
                <input type="date" id="cf-exam-date" />
              </div>
              <div class="form-group">
                <label>Start Time</label>
                <input type="time" id="cf-exam-start-time" />
              </div>
              <div class="form-group">
                <label>End Time</label>
                <input type="time" id="cf-exam-end-time" />
              </div>
            </div>
          </div>
          <input type="hidden" id="cf-edit-id" value="" />
          <div class="mt-1" style="display:flex;gap:0.5rem">
            <button type="submit" class="btn btn-primary" id="cf-submit">Create Course</button>
            <button type="button" class="btn btn-outline" onclick="document.getElementById('course-form-card').classList.add('hidden')">Cancel</button>
          </div>
        </form>
      </div>

      <div class="card mt-2">
        <div class="card-header">
          <h2>${courses.length} Course${courses.length !== 1 ? 's' : ''}</h2>
        </div>
        ${courses.length === 0
          ? '<p style="padding:1.5rem;text-align:center" class="text-muted">No courses yet. Create one to get started.</p>'
          : `<div class="table-wrap">
              <table class="table">
                <thead><tr>
                  <th>Code</th><th>Name</th><th>Credits</th><th>Department</th><th>Exam</th><th>Status</th><th></th>
                </tr></thead>
                <tbody>
                  ${courses.map(c => {
                    const examInfo = c.exam_date
                      ? `${c.exam_date}${c.exam_start_time ? ' · ' + c.exam_start_time : ''}${c.exam_end_time ? '–' + c.exam_end_time : ''}`
                      : '—';
                    return `
                    <tr>
                      <td><span class="badge badge-primary">${escHtml(c.code)}</span></td>
                      <td>${escHtml(c.name)}</td>
                      <td>${c.credits || '—'}</td>
                      <td class="text-muted">${escHtml(c.department || '—')}</td>
                      <td class="text-muted" style="font-size:0.85rem">${escHtml(examInfo)}</td>
                      <td>${c.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-outline">Inactive</span>'}</td>
                      <td>
                        <button class="btn btn-sm btn-outline" onclick="window._editCourse(${c.id})">✏️</button>
                        <button class="btn btn-sm btn-outline text-danger" onclick="window._deleteCourse(${c.id})">🗑</button>
                      </td>
                    </tr>
                  `}).join('')}
                </tbody>
              </table>
            </div>`
        }
      </div>
    </div>
  `;

  // show form for new course
  document.getElementById('btn-new-course').onclick = () => {
    document.getElementById('cf-edit-id').value = '';
    document.getElementById('course-form-title').textContent = 'New Course';
    document.getElementById('cf-submit').textContent = 'Create Course';
    document.getElementById('cf-code').value = '';
    document.getElementById('cf-name').value = '';
    document.getElementById('cf-credits').value = '3';
    document.getElementById('cf-dept').value = '';
    document.getElementById('cf-desc').value = '';
    document.getElementById('cf-exam-date').value = '';
    document.getElementById('cf-exam-start-time').value = '';
    document.getElementById('cf-exam-end-time').value = '';
    document.getElementById('course-form-card').classList.remove('hidden');
  };

  // submit form (create or update)
  document.getElementById('course-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const editId = document.getElementById('cf-edit-id').value;
    const data = {
      code: document.getElementById('cf-code').value.trim(),
      name: document.getElementById('cf-name').value.trim(),
      credits: parseInt(document.getElementById('cf-credits').value) || 0,
      department: document.getElementById('cf-dept').value.trim(),
      description: document.getElementById('cf-desc').value.trim(),
      exam_date: document.getElementById('cf-exam-date').value || null,
      exam_start_time: document.getElementById('cf-exam-start-time').value || null,
      exam_end_time: document.getElementById('cf-exam-end-time').value || null,
    };
    try {
      if (editId) {
        await coursesApi.update(parseInt(editId), data);
        showToast('Course updated', 'success');
      } else {
        await coursesApi.create(data);
        showToast('Course created', 'success');
      }
      renderAdminCourses(app);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // edit handler
  window._editCourse = async function (id) {
    try {
      const c = await coursesApi.get(id);
      document.getElementById('cf-edit-id').value = c.id;
      document.getElementById('course-form-title').textContent = 'Edit Course';
      document.getElementById('cf-submit').textContent = 'Save Changes';
      document.getElementById('cf-code').value = c.code;
      document.getElementById('cf-name').value = c.name;
      document.getElementById('cf-credits').value = c.credits || 0;
      document.getElementById('cf-dept').value = c.department || '';
      document.getElementById('cf-desc').value = c.description || '';
      document.getElementById('cf-exam-date').value = c.exam_date || '';
      document.getElementById('cf-exam-start-time').value = c.exam_start_time || '';
      document.getElementById('cf-exam-end-time').value = c.exam_end_time || '';
      document.getElementById('course-form-card').classList.remove('hidden');
      document.getElementById('course-form-card').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // delete handler
  window._deleteCourse = async function (id) {
    if (!confirm('Deactivate this course?')) return;
    try {
      await coursesApi.delete(id);
      showToast('Course deactivated', 'success');
      renderAdminCourses(app);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };
}

// ── Admin: Class Management (Classrooms) ──────────────────────

async function renderAdminClassForm(app, params) {
  const user = await authApi.me();
  const editId = params.get('id') ? parseInt(params.get('id'), 10) : 0;
  const [users, courses] = await Promise.all([
    adminApi.listUsers('teacher'),
    coursesApi.list(),
  ]);

  let cls = null;
  if (editId) {
    const all = await adminApi.listClasses();
    cls = all.find(c => c.id === editId);
    if (!cls) { navigate('#/admin/classes'); return; }
  }

  const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  const scheduleInitial = cls ? (cls.meeting_schedule || []).map(s => ({ day: s.day, start: s.start, end: s.end })) : [];

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/classes')}
    <div class="container mt-2">
      <a href="#/admin/classes" class="btn btn-sm btn-outline mb-1">← Back to Classrooms</a>
      <div class="page-header">
        <h1>${editId ? `Edit Classroom — ${escHtml(cls.name)}` : 'New Classroom'}</h1>
      </div>

      <div class="card mt-2">
        <form id="class-form" style="padding:1rem">
          <div class="form-section">
            <div class="form-section-title">Classroom Details</div>
            <div class="form-grid-3">
              <div class="form-group">
                <label>Classroom Name *</label>
                <input type="text" id="cls-name" required maxlength="128" placeholder="e.g. CS101 Sec A" value="${cls ? escHtml(cls.name) : ''}" />
              </div>
              <div class="form-group">
                <label>Classroom Code *</label>
                <input type="text" id="cls-code" required maxlength="32" placeholder="e.g. CS101-A" value="${cls ? escHtml(cls.code) : ''}" />
              </div>
              <div class="form-group">
                <label>Room Label (device code)</label>
                <input type="text" id="cls-room-label" maxlength="32" placeholder="e.g. RM-201" title="Physical room label the C6 node reports; enables auto-assignment" value="${cls ? escHtml(cls.classroom_code || '') : ''}" />
              </div>
            </div>
            <div class="form-grid-2">
              <div class="form-group">
                <label>Location</label>
                <input type="text" id="cls-location" maxlength="64" placeholder="e.g. Room 301, Block B" value="${cls ? escHtml(cls.location || '') : ''}" />
              </div>
              <div class="form-group">
                <label>Capacity</label>
                <input type="number" id="cls-capacity" min="0" max="9999" value="${cls ? (cls.capacity || 0) : 0}" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="form-section-title">Course & Term</div>
            <div class="form-grid-3">
              <div class="form-group">
                <label>Course</label>
                <select id="cls-course">
                  <option value="">— Select Course —</option>
                  ${courses.map(c => `<option value="${c.id}" ${cls && cls.course_id === c.id ? 'selected' : ''}>${escHtml(c.code)} — ${escHtml(c.name)}</option>`).join('')}
                </select>
                <p class="form-hint">Exam date/time come from the selected course.</p>
              </div>
              <div class="form-group">
                <label>Section</label>
                <input type="text" id="cls-section" maxlength="8" placeholder="e.g. A" value="${cls ? escHtml(cls.course_section || '') : ''}" />
              </div>
              <div class="form-group">
                <label>Semester (Academic calendar)</label>
                <select id="cls-term">
                  <option value="">— Select —</option>
                  <option value="Monsoon" ${cls && cls.term === 'Monsoon' ? 'selected' : ''}>Monsoon</option>
                  <option value="Winter" ${cls && cls.term === 'Winter' ? 'selected' : ''}>Winter</option>
                  <option value="Summer" ${cls && cls.term === 'Summer' ? 'selected' : ''}>Summer</option>
                </select>
              </div>
            </div>
            <div class="form-grid-3">
              <div class="form-group">
                <label>Year</label>
                <input type="number" id="cls-year" min="2020" max="2099" value="${cls ? (cls.year || 2026) : 2026}" />
              </div>
              <div class="form-group">
                <label>Class Start Date</label>
                <input type="date" id="cls-start-date" value="${cls ? (cls.start_date || '') : ''}" />
              </div>
              <div class="form-group">
                <label>Class End Date</label>
                <input type="date" id="cls-end-date" value="${cls ? (cls.end_date || '') : ''}" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="form-section-title">Faculty</div>
            <div class="form-group">
              <div id="cls-faculty"></div>
              <p class="form-hint">Select all teachers teaching this room. First selected becomes primary.</p>
            </div>
          </div>

          <div class="form-section">
            <div class="form-section-title">Meeting Schedule</div>
            <div class="form-group">
              <div id="schedule-rows"></div>
              <button type="button" class="btn btn-sm btn-outline mt-1" id="btn-add-schedule">+ Add Time Slot</button>
            </div>
          </div>

          <div class="mt-1" style="display:flex;gap:0.5rem">
            <button type="submit" class="btn btn-primary" id="cls-submit-btn">${editId ? 'Save Changes' : 'Create Classroom'}</button>
            <a href="#/admin/classes" class="btn btn-outline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `;

  // schedule row management
  const scheduleSlots = scheduleInitial;
  function renderScheduleRows() {
    const container = document.getElementById('schedule-rows');
    if (!container) return;
    container.innerHTML = scheduleSlots.map((s, i) => `
      <div class="schedule-row-input" style="margin-bottom:0.4rem">
        <select class="input-sm" onchange="window.formScheduleSlots[${i}].day=this.value">
          ${DAYS.map(d => `<option value="${d}" ${s.day === d ? 'selected' : ''}>${d}</option>`).join('')}
        </select>
        <input type="time" class="input-sm" value="${s.start || '09:00'}" onchange="window.formScheduleSlots[${i}].start=this.value" />
        <span class="text-muted">to</span>
        <input type="time" class="input-sm" value="${s.end || '10:00'}" onchange="window.formScheduleSlots[${i}].end=this.value" />
        <button type="button" class="btn btn-sm btn-outline text-danger" onclick="window.formScheduleSlots.splice(${i},1);window.formRenderScheduleRows()">✕</button>
      </div>
    `).join('');
  }
  window.formScheduleSlots = scheduleSlots;
  window.formRenderScheduleRows = renderScheduleRows;
  renderScheduleRows();

  // Faculty multi-select (many-to-many)
  const facultySel = new Set((cls && (cls.teacher_ids || [])) || []);
  window.formFacultySel = facultySel;

  function renderFacultyDropdown() {
    const picker = document.getElementById('cls-faculty');
    const search = picker && picker.querySelector('.faculty-search');
    const drop = picker && picker.querySelector('.faculty-dropdown');
    if (!drop) return;
    const q = (search ? search.value : '').trim().toLowerCase();
    const matches = users.filter(t => {
      if (!q) return true;
      return (t.full_name || '').toLowerCase().includes(q) || (t.username || '').toLowerCase().includes(q);
    });
    drop.innerHTML = matches.length === 0
      ? '<div class="faculty-empty">No matching teachers</div>'
      : matches.map(t => {
          const sel = facultySel.has(t.id);
          const uname = (t.username && t.username !== t.full_name)
            ? `<span class="faculty-option-sub">${escHtml(t.username)}</span>` : '';
          return `<div class="faculty-option${sel ? ' pick' : ''}" data-id="${t.id}">
            <span class="faculty-option-name">${escHtml(t.full_name || t.username)}${uname}</span>
            ${sel ? '<span class="faculty-option-check">✓</span>' : ''}
          </div>`;
        }).join('');
    drop.querySelectorAll('.faculty-option').forEach(opt => {
      opt.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = Number(opt.dataset.id);
        if (facultySel.has(id)) facultySel.delete(id);
        else facultySel.add(id);
        renderFacultyDropdown();
        renderFacultyChips();
        const fs = picker && picker.querySelector('.faculty-search');
        if (fs) fs.focus();
      });
    });
  }

  function renderFacultyChips() {
    const picker = document.getElementById('cls-faculty');
    const chips = picker && picker.querySelector('.faculty-chips');
    if (!chips) return;
    chips.innerHTML = users.filter(t => facultySel.has(t.id)).map(t => `
      <span class="faculty-chip">
        ${escHtml(t.full_name || t.username)}
        <button type="button" class="faculty-chip-x" data-id="${t.id}" aria-label="Remove ${escHtml(t.full_name || t.username)}">×</button>
      </span>
    `).join('');
    chips.querySelectorAll('.faculty-chip-x').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        facultySel.delete(Number(btn.dataset.id));
        renderFacultyDropdown();
        renderFacultyChips();
      });
    });
  }

  window.formRenderFacultyPicker = function () {
    const box = document.getElementById('cls-faculty');
    if (!box) return;
    if (users.length === 0) {
      box.innerHTML = '<span class="text-muted text-sm">No teachers exist yet — create one in Users first.</span>';
      return;
    }
    box.innerHTML = `
      <div class="faculty-picker">
        <input type="text" class="faculty-search" placeholder="Search faculty…" autocomplete="off" />
        <div class="faculty-dropdown"></div>
        <div class="faculty-chips"></div>
      </div>
    `;
    const search = box.querySelector('.faculty-search');
    const drop = box.querySelector('.faculty-dropdown');
    search.addEventListener('input', () => {
      renderFacultyDropdown();
      drop.classList.add('open');
    });
    search.addEventListener('focus', () => {
      renderFacultyDropdown();
      drop.classList.add('open');
    });
    search.addEventListener('blur', () => {
      setTimeout(() => {
        if (box.contains(document.activeElement)) return;
        drop.classList.remove('open');
      }, 120);
    });
    renderFacultyDropdown();
    renderFacultyChips();
  };
  window.formRenderFacultyPicker();

  // hide the dropdown on a click outside the picker
  if (window.formFacultyOutsideClick) {
    document.removeEventListener('click', window.formFacultyOutsideClick);
  }
  window.formFacultyOutsideClick = function (e) {
    if (e.target.closest('.faculty-picker')) return;
    const drop = document.getElementById('cls-faculty') && document.querySelector('#cls-faculty .faculty-dropdown');
    if (drop) drop.classList.remove('open');
  };
  document.addEventListener('click', window.formFacultyOutsideClick);

  document.getElementById('btn-add-schedule').onclick = () => {
    scheduleSlots.push({ day: 'Monday', start: '09:00', end: '10:00' });
    renderScheduleRows();
  };

  document.getElementById('class-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: document.getElementById('cls-name').value.trim(),
        code: document.getElementById('cls-code').value.trim(),
        classroom_code: document.getElementById('cls-room-label').value.trim(),
        course_id: parseInt(document.getElementById('cls-course').value) || null,
        course_section: document.getElementById('cls-section').value.trim(),
        term: document.getElementById('cls-term').value,
        year: parseInt(document.getElementById('cls-year').value) || null,
        teacher_ids: Array.from(facultySel),
        start_date: document.getElementById('cls-start-date').value || null,
        end_date: document.getElementById('cls-end-date').value || null,
        location: document.getElementById('cls-location').value.trim(),
        capacity: parseInt(document.getElementById('cls-capacity').value) || 0,
        meeting_schedule: scheduleSlots.map(s => ({ day: s.day, start: s.start, end: s.end })),
      };
      if (editId) {
        await adminApi.updateClass(editId, payload);
        showToast('Classroom updated!', 'success');
      } else {
        const created = await adminApi.createClass(payload);
        const warnings = created.warnings || [];
        if (warnings.length > 0) showToast('Classroom created — ' + warnings.length + ' schedule clash warning(s)', 'warning');
        else showToast('Classroom created!', 'success');
      }
      navigate('#/admin/classes');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// ├── Admin: Class listing (create/edit live on a dedicated page) ───

async function renderAdminClasses(app) {
  const user = await authApi.me();
  const classes = await adminApi.listClasses();

  function scheduleChips(schedule) {
    if (!schedule || schedule.length === 0) return '<span class="text-muted">No schedule</span>';
    return schedule.map(s =>
      `<span class="badge badge-outline schedule-chip">${escHtml(s.day)} ${escHtml(s.start)}–${escHtml(s.end)}</span>`
    ).join(' ');
  }

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/classes')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>Classrooms</h1>
        <a href="#/admin/classes/new" class="btn btn-primary">+ New Classroom</a>
      </div>

      <div class="card mt-2">
        <div class="card-header">
          <h2>${classes.length} Classroom${classes.length !== 1 ? 's' : ''}</h2>
        </div>
        ${classes.length === 0
          ? '<p style="padding:1.5rem;text-align:center" class="text-muted">No classrooms yet. Click "+ New Classroom" to create one.</p>'
          : `<div class="table-wrap">
              <table class="table">
                <thead><tr>
                  <th>Course</th><th>Section</th><th>Semester</th><th>Faculty</th>
                  <th>Schedule</th><th>Location / Room</th><th>Students</th><th>Status</th><th></th>
                </tr></thead>
                <tbody>
                  ${classes.map(c => `
                    <tr>
                      <td>
                        <strong>${escHtml(c.course_name || c.name)}</strong>
                        ${c.course_code ? `<br><span class="text-muted text-sm">${escHtml(c.course_code)}</span>` : ''}
                      </td>
                      <td>${c.course_section ? `<span class="badge badge-primary">${escHtml(c.course_section)}</span>` : '—'}</td>
                      <td class="text-sm">
                        ${c.term ? `${escHtml(c.term)} ${c.year || ''}` : '<span class="text-muted">—</span>'}
                        ${c.start_date ? `<br><span class="text-muted">${escHtml(c.start_date)} → ${escHtml(c.end_date || '?')}</span>` : ''}
                        ${c.exam_date ? `<br><span class="text-muted">Exam: ${escHtml(c.exam_date)}${c.exam_start_time ? ' · ' + escHtml(c.exam_start_time) : ''}</span>` : ''}
                      </td>
                      <td>
                        ${(c.faculty_names || []).map(f =>
                          `<span class="badge badge-outline" title="Faculty">${escHtml(f.full_name)}</span>`
                        ).join(' ') || '<span class="text-muted">—</span>'}
                      </td>
                      <td>${scheduleChips(c.meeting_schedule)}${renderScheduleWarnings(c.warnings)}</td>
                      <td class="text-muted">
                        ${escHtml(c.location || '—')}
                        ${c.classroom_code ? `<br><span class="badge badge-primary" title="Physical room label">${escHtml(c.classroom_code)}</span>` : ''}
                      </td>
                      <td>${c.student_count || 0}${c.capacity ? ` / ${c.capacity}` : ''}</td>
                      <td><span class="badge ${c.is_active ? 'badge-success' : 'badge-outline'}">${c.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td style="white-space:nowrap">
                        <a href="#/class?id=${c.id}" class="btn btn-sm btn-outline">Open</a>
                        <a href="#/admin/classes/new?id=${c.id}" class="btn btn-sm btn-outline">✏️ Edit</a>
                        <button class="btn btn-sm btn-outline text-danger" onclick="deleteClass(${c.id}, '${escHtml(c.name).replace(/'/g, "\\'")}')">🗑</button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>`
        }
      </div>
    </div>
  `;
}

window.renderScheduleWarnings = function (warnings) {
  if (!warnings || warnings.length === 0) return '';
  return `
    <div class="warn-box">
      ${warnings.map(w => `<div class="warn-line">⚠️ ${escHtml(w.message)}</div>`).join('')}
    </div>`;
}

window.assignTeacherToClass = async function (classId, teacherId) {
  try {
    await adminApi.assignTeacher(classId, parseInt(teacherId));
    showToast('Teacher assigned!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.editClass = function (classId) {
  navigate(`#/admin/classes/new?id=${classId}`);
};

window.deleteClass = async function (classId, name) {
  if (!confirm(`Delete classroom "${name || classId}"? This also removes its quizzes, polls, attendance and enrollments.`)) return;
  try {
    await adminApi.deleteClass(classId);
    showToast('Classroom deleted', 'success');
    renderAdminClasses(document.getElementById('app'));
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ── Admin: Student Management (Universal Registry) ────────────

async function renderAdminStudents(app) {
  const user = await authApi.me();
  const students = await studentsApi.list();

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/students')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>Student Registry</h1>
        <div style="display:flex;gap:0.5rem">
          <input type="text" id="stu-search" class="input-sm" placeholder="Search name / roll…" style="min-width:200px" />
          <button class="btn btn-outline" id="btn-import-csv">⬆ Import CSV</button>
          <button class="btn btn-primary" id="btn-new-student">+ New Student</button>
        </div>
      </div>

      <!-- CSV Import Card -->
      <div class="card hidden" id="csv-import-card">
        <div class="card-header">
          <h2>Import Students from CSV</h2>
          <button class="btn btn-sm btn-outline" onclick="document.getElementById('csv-import-card').classList.add('hidden')">✕</button>
        </div>
        <div style="padding:1rem">
          <p class="form-hint" style="margin-top:0;margin-bottom:0.75rem">
            All 7 columns below are <strong>compulsory</strong> — every row must fill them, no extra columns:
            <strong>roll_number</strong> (10 alphanumeric), <strong>student_name</strong>, <strong>email</strong>,
            <strong>phone</strong>, <strong>program</strong>, <strong>enrollment_year</strong>, <strong>graduation_year</strong>.
          </p>
          <div class="csv-drop" id="csv-drop-zone">
            <p style="margin:0 0 0.5rem">Drop CSV file here or click to browse</p>
            <input type="file" id="csv-file-input" accept=".csv" style="display:none" />
            <button class="btn btn-sm btn-outline" id="csv-browse-btn">Choose File</button>
            <p id="csv-file-name" class="text-muted" style="font-size:0.8rem;margin:0.5rem 0 0"></p>
          </div>
          <div id="csv-preview" class="hidden" style="margin-top:1rem"></div>
          <div class="mt-1" style="display:flex;gap:0.5rem;align-items:center">
            <button class="btn btn-primary" id="csv-upload-btn" disabled>Upload & Import</button>
            <span id="csv-import-status" class="text-muted text-sm"></span>
          </div>
        </div>
      </div>

      <!-- Manual Student Form -->
      <div class="card hidden" id="student-form-card">
        <div class="card-header">
          <h2 id="student-form-title">New Student</h2>
          <button class="btn btn-sm btn-outline" onclick="this.closest('.card').classList.add('hidden')">✕</button>
        </div>
        <form id="student-form" style="padding:1rem">
          <div class="form-section" style="margin-top:0;padding-top:0;border-top:none">
            <div class="form-section-title">Identity</div>
            <div class="form-grid-3">
              <div class="form-group">
                <label>Enrollment Number *</label>
                <input type="text" id="sf-roll" required maxlength="10" minlength="10" pattern="[A-Za-z0-9]{10}" placeholder="e.g. 23CS200001" title="Exactly 10 alphanumeric characters" />
              </div>
              <div class="form-group">
                <label>Student Name *</label>
                <input type="text" id="sf-name" required maxlength="128" />
              </div>
              <div class="form-group">
                <label>Program</label>
                <input type="text" id="sf-program" maxlength="64" placeholder="e.g. B.Tech CS" />
              </div>
            </div>
          </div>
          <div class="form-section">
            <div class="form-section-title">Contact</div>
            <div class="form-grid-2">
              <div class="form-group">
                <label>Email</label>
                <input type="email" id="sf-email" maxlength="128" />
              </div>
              <div class="form-group">
                <label>Phone</label>
                <input type="text" id="sf-phone" maxlength="16" />
              </div>
            </div>
          </div>
          <div class="form-section">
            <div class="form-section-title">Academic Years</div>
            <div class="form-grid-2">
              <div class="form-group">
                <label>Enrollment Year</label>
                <input type="number" id="sf-enroll-year" min="2000" max="2099" />
              </div>
              <div class="form-group">
                <label>Graduation Year</label>
                <input type="number" id="sf-grad-year" min="2000" max="2099" />
              </div>
            </div>
          </div>
          <input type="hidden" id="sf-edit-id" value="" />
          <div class="mt-1" style="display:flex;gap:0.5rem">
            <button type="submit" class="btn btn-primary" id="sf-submit">Register Student</button>
            <button type="button" class="btn btn-outline" onclick="document.getElementById('student-form-card').classList.add('hidden')">Cancel</button>
          </div>
        </form>
      </div>

      <div class="card mt-2">
        <div class="card-header">
          <h2 id="student-count">${students.length} Student${students.length !== 1 ? 's' : ''}</h2>
        </div>
        <div id="student-table-area">
          ${_renderStudentTable(students)}
        </div>
      </div>
    </div>
  `;

  // search
  let searchTimeout;
  document.getElementById('stu-search').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      const q = e.target.value.trim();
      const results = await studentsApi.list(q);
      document.getElementById('student-table-area').innerHTML = _renderStudentTable(results);
      document.getElementById('student-count').textContent = `${results.length} Student${results.length !== 1 ? 's' : ''}`;
    }, 300);
  });

  // show form for new student
  document.getElementById('btn-new-student').onclick = () => {
    document.getElementById('sf-edit-id').value = '';
    document.getElementById('student-form-title').textContent = 'New Student';
    document.getElementById('sf-submit').textContent = 'Register Student';
    ['sf-roll','sf-name','sf-program','sf-email','sf-phone','sf-enroll-year','sf-grad-year'].forEach(id => {
      document.getElementById(id).value = '';
    });
    document.getElementById('student-form-card').classList.remove('hidden');
  };

  // ── CSV import wiring ────────────────────────────────────
  const importCard = document.getElementById('csv-import-card');
  const dropZone = document.getElementById('csv-drop-zone');
  const fileInput = document.getElementById('csv-file-input');
  const uploadBtn = document.getElementById('csv-upload-btn');
  let selectedCsv = null;

  document.getElementById('btn-import-csv').onclick = () => {
    importCard.classList.toggle('hidden');
    if (!importCard.classList.contains('hidden')) {
      importCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  document.getElementById('csv-browse-btn').onclick = (e) => { e.stopPropagation(); fileInput.click(); };
  dropZone.onclick = () => fileInput.click();
  dropZone.ondragover = (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--primary)'; };
  dropZone.ondragleave = () => { dropZone.style.borderColor = ''; };
  dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '';
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      handleCsvFileSelect();
    }
  };

  fileInput.addEventListener('change', handleCsvFileSelect);

  function handleCsvFileSelect() {
    const f = fileInput.files[0];
    if (!f) { selectedCsv = null; uploadBtn.disabled = true; return; }
    if (!f.name.toLowerCase().endsWith('.csv')) {
      showToast('Please choose a .csv file', 'error');
      fileInput.value = '';
      selectedCsv = null;
      uploadBtn.disabled = true;
      return;
    }
    selectedCsv = f;
    document.getElementById('csv-file-name').textContent = `${f.name} (${(f.size / 1024).toFixed(1)} KB)`;
    uploadBtn.disabled = false;
    document.getElementById('csv-import-status').textContent = '';

    // Preview first 3 data rows
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target.result;
      const lines = text.split(/\r?\n/).filter(l => l.trim());
      const preview = document.getElementById('csv-preview');
      if (lines.length < 2) {
        preview.innerHTML = '<p class="form-hint" style="color:var(--danger)">CSV appears empty — need a header + at least one data row.</p>';
        preview.classList.remove('hidden');
        return;
      }
      const headers = lines[0].split(',').map(h => h.trim());
      const rows = lines.slice(1, 4).map(line => line.split(',').map(c => c.trim()));
      preview.innerHTML = `
        <div class="form-section">
          <div class="form-section-title">Preview — ${headers.length} column(s), ${lines.length - 1} row(s)</div>
          <div class="table-wrap"><table class="table">
            <thead><tr>${headers.map(h => `<th>${escHtml(h)}</th>`).join('')}</tr></thead>
            <tbody>${rows.map(r => `<tr>${headers.map((_, i) => `<td class="text-sm">${escHtml(r[i] || '')}</td>`).join('')}</tr>`).join('')}</tbody>
          </table></div>
        </div>`;
      preview.classList.remove('hidden');
    };
    reader.readAsText(f);
  }

  uploadBtn.onclick = async () => {
    if (!selectedCsv) return;
    const statusEl = document.getElementById('csv-import-status');
    uploadBtn.disabled = true;
    statusEl.textContent = 'Importing…';
    try {
      const result = await studentsApi.importCsv(selectedCsv);
      statusEl.textContent = `✓ ${result.inserted} inserted, ${result.skipped.length} skipped`;
      if (result.skipped.length) {
        const r = result.skipped;
        document.getElementById('csv-preview').innerHTML = `
          <p class="form-hint" style="color:var(--warning)">
            ${r.length} row(s) skipped — fix and re-upload:
          </p>
          <div class="table-wrap"><table class="table">
            <thead><tr><th>Row</th><th>Roll</th><th>Error</th></tr></thead>
            <tbody>${r.map(e => `<tr><td>${e.row}</td><td><code>${escHtml(e.roll_number)}</code></td><td class="text-sm">${escHtml(e.error)}</td></tr>`).join('')}</tbody>
          </table></div>`;
      }
      showToast(`${result.inserted} student(s) imported`, 'success');
      // refresh table
      const students = await studentsApi.list();
      document.getElementById('student-table-area').innerHTML = _renderStudentTable(students);
      document.getElementById('student-count').textContent = `${students.length} Student${students.length !== 1 ? 's' : ''}`;
      if (result.skipped.length === 0) { importCard.classList.add('hidden'); }
    } catch (err) {
      statusEl.textContent = '';
      showToast(err.message, 'error');
    } finally {
      uploadBtn.disabled = false;
    }
  };

  // submit form
  document.getElementById('student-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const editId = document.getElementById('sf-edit-id').value;
    const data = {
      roll_number: document.getElementById('sf-roll').value.trim(),
      student_name: document.getElementById('sf-name').value.trim(),
      program: document.getElementById('sf-program').value.trim(),
      email: document.getElementById('sf-email').value.trim(),
      phone: document.getElementById('sf-phone').value.trim(),
      enrollment_year: parseInt(document.getElementById('sf-enroll-year').value) || null,
      graduation_year: parseInt(document.getElementById('sf-grad-year').value) || null,
    };
    try {
      if (editId) {
        await studentsApi.update(parseInt(editId), data);
        showToast('Student updated', 'success');
      } else {
        await studentsApi.create(data);
        showToast('Student registered', 'success');
      }
      renderAdminStudents(app);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

function _renderStudentTable(students) {
  if (students.length === 0) return '<p style="padding:1.5rem;text-align:center" class="text-muted">No students found.</p>';
  return `
    <div class="table-wrap">
      <table class="table">
        <thead><tr>
          <th>Roll #</th><th>Name</th><th>Program</th><th>Email</th><th>Device</th><th>Status</th><th></th>
        </tr></thead>
        <tbody>
          ${students.map(s => `
            <tr>
              <td><span class="badge badge-primary">${escHtml(s.roll_number)}</span></td>
              <td><strong>${escHtml(s.student_name)}</strong></td>
              <td class="text-muted">${escHtml(s.program || '—')}</td>
              <td class="text-muted text-sm">${escHtml(s.email || '—')}</td>
              <td>${s.device_mac ? `<code class="text-sm">${escHtml(s.device_mac)}</code>` : '<span class="text-muted">—</span>'}</td>
              <td>${s.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-outline">Inactive</span>'}</td>
              <td>
                <button class="btn btn-sm btn-outline" onclick="window._editStudent(${s.id})">✏️</button>
                ${s.is_active
                  ? `<button class="btn btn-sm btn-outline" title="Deactivate" onclick="window._deactivateStudent(${s.id})">⏸</button>`
                  : `<button class="btn btn-sm btn-outline" title="Reactivate" onclick="window._reactivateStudent(${s.id})">▶</button>`}
                <button class="btn btn-sm btn-outline text-danger" title="Delete record permanently" onclick="window._hardDeleteStudent(${s.id}, '${escHtml(s.student_name).replace(/'/g, "\\'")}')">🗑</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

window._editStudent = async function (id) {
  try {
    const s = await studentsApi.get(id);
    document.getElementById('sf-edit-id').value = s.id;
    document.getElementById('student-form-title').textContent = 'Edit Student';
    document.getElementById('sf-submit').textContent = 'Save Changes';
    document.getElementById('sf-roll').value = s.roll_number;
    document.getElementById('sf-name').value = s.student_name;
    document.getElementById('sf-program').value = s.program || '';
    document.getElementById('sf-email').value = s.email || '';
    document.getElementById('sf-phone').value = s.phone || '';
    document.getElementById('sf-enroll-year').value = s.enrollment_year || '';
    document.getElementById('sf-grad-year').value = s.graduation_year || '';
    document.getElementById('student-form-card').classList.remove('hidden');
    document.getElementById('student-form-card').scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window._deactivateStudent = async function (id) {
  if (!confirm('Deactivate this student?')) return;
  try {
    await studentsApi.deactivate(id);
    showToast('Student deactivated', 'success');
    const students = await studentsApi.list();
    document.getElementById('student-table-area').innerHTML = _renderStudentTable(students);
    document.getElementById('student-count').textContent = `${students.length} Student${students.length !== 1 ? 's' : ''}`;
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window._reactivateStudent = async function (id) {
  try {
    await studentsApi.update(id, { is_active: true });
    showToast('Student reactivated', 'success');
    const students = await studentsApi.list();
    document.getElementById('student-table-area').innerHTML = _renderStudentTable(students);
    document.getElementById('student-count').textContent = `${students.length} Student${students.length !== 1 ? 's' : ''}`;
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window._hardDeleteStudent = async function (id, name) {
  if (!confirm(`⚠️ Permanently delete student "${name || id}"?\n\nThis removes the record, its course enrollments and attendance history. This cannot be undone.`)) return;
  if (!confirm('Are you absolutely sure? This action is irreversible.')) return;
  try {
    await studentsApi.hardDelete(id);
    showToast('Student record permanently deleted', 'success');
    const students = await studentsApi.list();
    document.getElementById('student-table-area').innerHTML = _renderStudentTable(students);
    document.getElementById('student-count').textContent = `${students.length} Student${students.length !== 1 ? 's' : ''}`;
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// ── Admin: Activity Logs ──────────────────────────────────────

async function renderAdminActivity(app) {
  const user = await authApi.me();
  const activity = await adminApi.activityLogs(100);

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/activity')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>Activity Logs</h1>
        <p class="text-muted">${activity.length} entries</p>
      </div>

      <div class="card">
        ${activity.length === 0 ? '<p class="text-muted" style="padding:1rem">No activity recorded yet.</p>' : ''}
        <div class="table-responsive">
          <table class="table">
            <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead>
            <tbody>
              ${activity.map(a => `
                <tr>
                  <td class="text-muted text-sm">${a.timestamp ? istDateTime(istParseToEpoch(a.timestamp)) : '—'}</td>
                  <td>${escHtml(a.username || 'system')}</td>
                  <td><span class="badge badge-outline">${escHtml(a.action)}</span></td>
                  <td>${a.entity_type ? `${a.entity_type} #${a.entity_id || '?'}` : '—'}</td>
                  <td class="text-sm">${a.details && Object.keys(a.details).length > 0 ? escHtml(JSON.stringify(a.details)) : '—'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// ── Admin: Modules & Devices (R7 connectivity, R8 OTA) ──────────

async function renderAdminModules(app) {
  const user = await authApi.me();
  const devices = await modulesApi.list();

  const connected = devices.filter(d => d.is_connected).length;
  const otaPending = devices.filter(d => d.ota_status === 'downloading').length;

  app.innerHTML = `
    ${renderNavbar(user, '#/admin/modules')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>📡 Classroom Nodes & Student Modules</h1>
        <p class="text-muted">${devices.length} registered devices — monitoring (telemetry) + OTA push</p>
      </div>

      <div class="stats-grid">
        <div class="card stat-card"><span class="stat-icon">📟</span><div class="stat-value">${devices.length}</div><div class="stat-label">Total devices</div></div>
        <div class="card stat-card"><span class="stat-icon">🟢</span><div class="stat-value">${connected}</div><div class="stat-label">Connected</div></div>
        <div class="card stat-card"><span class="stat-icon">🔄</span><div class="stat-value">${otaPending}</div><div class="stat-label">OTA pending</div></div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>All devices (C6 nodes + student modules)</h2>
        </div>
        ${devices.length === 0 ? '<p class="text-muted" style="padding:1rem">No devices have registered yet. Devices report on first boot via /api/device/register.</p>' : ''}
        <div class="table-responsive">
          <table class="table">
            <thead><tr>
              <th>Device</th><th>Type</th><th>Connected</th><th>Firmware</th><th>OTA</th><th>Assigned class</th>
              <th>Students (C6)</th><th>RAM free</th><th>Flash total</th><th>Actions</th>
            </tr></thead>
            <tbody>
              ${devices.map(d => `
                <tr>
                  <td>
                    <strong>${escHtml(d.device_name || d.mac_address)}</strong><br>
                    <span class="text-muted text-sm">${escHtml(d.mac_address)}</span>
                  </td>
                  <td><span class="badge badge-outline">${escHtml(d.device_type)}</span></td>
                  <td>
                    <span class="badge ${d.is_connected ? 'badge-success' : ''}">${d.is_connected ? 'connected' : 'offline'}</span>
                    ${d.is_active ? '' : '<span class="badge badge-danger">disabled</span>'}
                  </td>
                  <td class="text-sm">
                    v${escHtml(d.firmware_version || '0.0.0')}
                    ${d.verified_at ? '<br><span class="text-success text-sm">✓ verified</span>' : ''}
                  </td>
                  <td class="text-sm">
                    ${d.pending_version ? `→ v${escHtml(d.pending_version)} <span class="badge badge-outline">${escHtml(d.ota_status)}</span>` : '<span class="text-muted">up to date</span>'}
                  </td>
                  <td class="text-sm">${d.class_code ? `${escHtml(d.class_code)} · ${escHtml(d.class_name)}` : '—'}</td>
                  <td class="text-sm text-center">${d.device_type === 'c6' ? (d.student_count || 0) : '—'}</td>
                  <td class="text-sm text-center">${d.free_heap ? formatBytes(d.free_heap) : '—'}</td>
                  <td class="text-sm text-center">${d.total_flash ? formatBytes(d.total_flash) : '—'}</td>
                  <td class="nowrap">
                    <button class="btn btn-xs btn-outline" onclick="window._pushOta(${d.id}, '${escHtml(d.device_name || d.mac_address).replace(/'/g, "\\'")}')">Push OTA</button>
                    ${d.is_active && !d.verified_at ? `<button class="btn btn-xs btn-outline" onclick="window._verifyModule(${d.id})">Verify</button>` : ''}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// Helpers
function formatBytes(bytes) {
  if (bytes === undefined || bytes === null) return '—';
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  if (bytes >= 1024) return (bytes / 1024).toFixed(0) + ' KB';
  return bytes + ' B';
}

window._verifyModule = async function (deviceId) {
  try {
    await modulesApi.verify(deviceId);
    showToast('Module verified', 'success');
    renderAdminModules(document.getElementById('app'));
  } catch (err) { showToast(err.message, 'error'); }
};

window._pushOta = async function (deviceId, name) {
  const version = prompt(`Push firmware version to ${name || `device #${deviceId}`}:`, '1.0.0');
  if (!version) return;
  try {
    await modulesApi.pushOta(deviceId, version.trim());
    showToast(`OTA v${version.trim()} queued`, 'success');
    renderAdminModules(document.getElementById('app'));
  } catch (err) { showToast(err.message, 'error'); }
};

// ── Faculty: Class List ───────────────────────────────────────

async function renderClasses(app) {
  const user = await authApi.me();
  const classes = await classesApi.list();

  function _schedChips(schedule) {
    if (!schedule || schedule.length === 0) return '';
    return schedule.map(s =>
      `<span class="badge badge-outline schedule-chip">${escHtml(s.day)} ${escHtml(s.start)}–${escHtml(s.end)}</span>`
    ).join(' ');
  }

  app.innerHTML = `
    ${renderNavbar(user, '#/classes')}
    <div class="container mt-2">
      <div class="page-header">
        <h1>My Classes</h1>
      </div>

      ${classes.length === 0 ? `
        <div class="card">
          <p class="text-muted" style="padding:1.5rem">No classes assigned yet. Contact your admin to get classes assigned to you.</p>
        </div>
      ` : `
        <div class="grid-2">
          ${classes.map(c => `
            <a href="#/class?id=${c.id}" class="card card-hover class-card" style="text-decoration:none;color:inherit">
              <div class="flex-between gap-2">
                <h2 style="margin:0;min-width:0;overflow-wrap:anywhere">${escHtml(c.course_name || c.name)}</h2>
                <span class="badge ${c.is_active ? 'badge-success' : 'badge-outline'}">${c.is_active ? 'Active' : 'Inactive'}</span>
              </div>
              ${c.course_code ? `<p class="text-muted mt-1">${escHtml(c.course_code)}${c.course_section ? ` — Section ${escHtml(c.course_section)}` : ''}${c.code && c.code !== c.course_code ? ` · Room code ${escHtml(c.code)}` : ''}</p>` : ''}
              <div class="text-sm text-muted mt-1">
                🧑‍🏫
                ${(c.faculty_names && c.faculty_names.length)
                  ? c.faculty_names.map(f => escHtml(f.full_name)).join(', ')
                  : escHtml(c.teacher_name || 'Unassigned')}
              </div>
              <div class="class-meta">
                ${c.classroom_code ? `<span class="chip">🏫 ${escHtml(c.classroom_code)}</span>` : ''}
                ${c.term ? `<span class="chip">🗓 ${escHtml(c.term)} ${c.year || ''}</span>` : ''}
                ${c.start_date ? `<span class="chip">${escHtml(c.start_date)} → ${escHtml(c.end_date || '?')}</span>` : ''}
                ${c.exam_start_date ? `<span class="chip">Exams ${escHtml(c.exam_start_date)} → ${escHtml(c.exam_end_date || '?')}</span>` : ''}
              </div>
              ${c.location ? `<div class="text-sm text-muted">📍 ${escHtml(c.location)}</div>` : ''}
              <div class="mt-1">${_schedChips(c.meeting_schedule) || '<span class="text-muted text-sm">No schedule set</span>'}</div>
              <div class="flex gap-2 mt-1 text-sm text-muted">
                <span>🎓 ${c.student_count || 0} students</span>
                <span>📝 ${c.quiz_count || 0} quizzes</span>
                <span>📊 ${c.poll_count || 0} polls</span>
              </div>
            </a>
          `).join('')}
        </div>
      `}
    </div>
  `;
}

// ── Live device presence (poll every 5s + WS push) ─────────────

let liveDevicesTimer = null;

function stopLiveDevicesPolling() {
  if (liveDevicesTimer) {
    clearInterval(liveDevicesTimer);
    liveDevicesTimer = null;
  }
}

function _liveDeviceTile(d) {
  const online = !!d.online;
  const lastSeenStr = d.last_seen_ms ? istTime(d.last_seen_ms) : 'never';
  const agoStr = d.last_seen_ago_s != null ? `${d.last_seen_ago_s}s ago` : '—';
  return `
    <div class="device-tile ${online ? 'tile-on' : 'tile-off'}" title="${escHtml(d.device_type)} · ${escHtml(d.mac_address)}">
      <div class="device-tile-head">
        <span class="dot ${online ? 'dot-on' : 'dot-off'}"></span>
        <strong>${escHtml(d.device_name || d.mac_address)}</strong>
      </div>
      <div class="text-sm text-muted">${escHtml(d.device_type)} · ${escHtml(d.mac_address)}</div>
      <div class="text-sm ${online ? 'text-good' : 'text-muted'}">${online ? '● Online' : '○ Offline'}</div>
      <div class="text-sm text-muted">Last seen ${lastSeenStr} · ${agoStr}</div>
      <div class="text-sm text-muted">🔋 ${d.battery_pct != null ? d.battery_pct : '—'}% · 📶 ${d.rssi != null ? d.rssi : '—'} dBm</div>
    </div>`;
}

function renderLiveDevices(snap) {
  const grid = document.getElementById('live-devices-grid');
  if (!grid) return;
  const countEl = document.getElementById('live-devices-count');
  const updatedEl = document.getElementById('live-devices-updated');
  if (!snap || !Array.isArray(snap.devices) || snap.devices.length === 0) {
    grid.innerHTML = '<p class="text-muted" style="padding:1rem">No class node linked yet — devices will appear once the gateway is registered and linked.</p>';
    if (countEl) { countEl.textContent = '0 online'; countEl.className = 'badge badge-outline'; }
    return;
  }
  grid.innerHTML = snap.devices.map(_liveDeviceTile).join('');
  if (countEl) {
    countEl.textContent = `${snap.online_count || 0}/${snap.total_count || snap.devices.length} online`;
    countEl.className = `badge ${snap.online_count ? 'badge-success' : 'badge-outline'}`;
  }
  if (updatedEl && snap.server_time_ms) {
    updatedEl.textContent = `updated ${istTime(snap.server_time_ms)}`;
  }
}

function startLiveDevicesPolling(classId) {
  stopLiveDevicesPolling();
  const poll = async () => {
    try {
      const snap = await devicesApi.live(parseInt(classId));
      renderLiveDevices(snap);
    } catch (err) {
      const grid = document.getElementById('live-devices-grid');
      if (grid && grid.dataset.errored !== '1') {
        grid.innerHTML = `<p class="text-muted" style="padding:1rem">Live devices unavailable: ${escHtml(err.message)}</p>`;
        grid.dataset.errored = '1';
      }
    }
  };
  poll(); // immediate first render, then every 5s
  liveDevicesTimer = setInterval(poll, 5000);
}

// ── Faculty: Class Detail ─────────────────────────────────────

async function renderClassDetail(app, params) {
  const user = await authApi.me();
  const classId = params.get('id');
  if (!classId) { navigate('#/classes'); return; }

  stopLiveDevicesPolling(); // avoid stale timers across class navigations

  const cls = await classesApi.get(classId);
  const isAdmin = user.role === 'admin' || user.role === 'super_admin';
  const [quizzes, polls, students, classDevices] = await Promise.all([
    quizzesApi.list(classId),
    pollsApi.list(classId),
    studentsApi.listClassStudents(classId),
    isAdmin ? modulesApi.classDevices(classId).catch(() => null) : Promise.resolve(null),
  ]);
  window._rosterNames = Object.fromEntries(students.map(s => [s.id, s.student_name]));

  // Connect WebSocket
  classSocket.connect(classId);

  app.innerHTML = `
    ${renderNavbar(user, '#/classes')}
    <div class="container mt-2">
      <div class="page-header flex-between">
        <div>
          <h1>${escHtml(cls.course_name || cls.name)}</h1>
          ${cls.course_code ? `<p class="text-muted">${escHtml(cls.course_code)}${cls.course_section ? ` — Section ${escHtml(cls.course_section)}` : ''}</p>` : ''}
          <div class="class-meta mt-1">
            ${cls.term ? `<span class="chip">🗓 ${escHtml(cls.term)} ${cls.year || ''}</span>` : ''}
            ${cls.start_date ? `<span class="chip">📅 ${escHtml(cls.start_date)} → ${escHtml(cls.end_date || '?')}</span>` : ''}
            ${cls.exam_date ? `<span class="chip">🧾 Exam ${escHtml(cls.exam_date)}${cls.exam_start_time ? ` · ${escHtml(cls.exam_start_time)}${cls.exam_end_time ? `–${escHtml(cls.exam_end_time)}` : ''}` : ''}</span>` : ''}
            ${cls.location ? `<span class="chip">📍 ${escHtml(cls.location)}</span>` : ''}
            ${cls.capacity ? `<span class="chip">👥 Capacity: ${cls.capacity}</span>` : ''}
          </div>
          <div class="flex gap-2 text-sm text-muted mt-1" style="flex-wrap:wrap">
            <span>🎓 ${cls.student_count || 0} students</span>
            <span>
              🧑‍🏫
              ${(cls.faculty_names && cls.faculty_names.length)
                ? cls.faculty_names.map(f => escHtml(f.full_name)).join(', ')
                : escHtml(cls.teacher_name || 'Unassigned')}
              ${isAdmin ? `<button class="btn btn-sm btn-outline ml-1" onclick="openManageFaculty(${classId})">Manage Faculty</button>` : ''}
            </span>
            <span>Code: <code>${escHtml(cls.code)}</code>${cls.classroom_code ? `${cls.code !== cls.classroom_code ? ` · Room ${escHtml(cls.classroom_code)}` : ''}` : ''}</span>
          </div>
          ${cls.meeting_schedule && cls.meeting_schedule.length > 0 ? `
            <div class="mt-1" style="display:flex;gap:0.4rem;flex-wrap:wrap">
              ${cls.meeting_schedule.map(s => `<span class="badge badge-outline schedule-chip">${escHtml(s.day)} ${escHtml(s.start)}–${escHtml(s.end)}</span>`).join('')}
            </div>
          ` : ''}
          ${renderScheduleWarnings(cls.warnings)}
        </div>
        <div class="flex gap-1">
          ${cls.is_active
            ? `<button class="btn btn-danger" onclick="deactivateClass('${classId}')">Deactivate</button>`
            : `<button class="btn btn-success" onclick="activateClass('${classId}')">Activate</button>`
          }
        </div>
      </div>

      <div class="grid-2 mt-2">
        <!-- Quizzes -->
        <div class="card">
          <div class="card-header">
            <h2>Quizzes</h2>
            <a href="#/quiz?class_id=${classId}" class="btn btn-sm btn-primary">+ New Quiz</a>
          </div>
          ${quizzes.length === 0 ? '<p class="text-muted" style="padding:1rem">No quizzes yet.</p>' : ''}
          <div class="list-compact">
            ${quizzes.map(q => `
              <div class="list-item flex-between">
                <div>
                  <strong>${escHtml(q.title)}</strong>
                  <div class="text-sm text-muted">
                    <span class="badge badge-sm ${q.quiz_mode === 'impromptu' ? 'badge-warning' : 'badge-outline'}">${q.quiz_mode}</span>
                    <span class="badge badge-sm ${q.timing_mode === 'manual' ? 'badge-outline' : 'badge-info'}">${q.timing_mode.replace('_', ' ')}</span>
                    <span class="badge badge-sm ${q.status === 'active' ? 'badge-success' : q.status === 'completed' ? 'badge-primary' : 'badge-outline'}">${q.status}</span>
                  </div>
                </div>
                <div class="flex gap-1">
                  ${q.status === 'draft' ? `<button class="btn btn-sm btn-success" onclick="startQuiz(${q.id})">▶ Start</button>` : ''}
                  ${q.status === 'active' ? `
                    ${q.timing_mode === 'manual' ? `<button class="btn btn-sm btn-primary" onclick="nextQuestion(${q.id})">Next →</button>` : ''}
                    <button class="btn btn-sm btn-danger" onclick="stopQuiz(${q.id})">⏹ Stop</button>
                  ` : ''}
                  ${q.status === 'completed' ? `<a href="#/quiz-results?id=${q.id}" class="btn btn-sm btn-outline">Results</a>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Polls -->
        <div class="card">
          <div class="card-header">
            <h2>Polls</h2>
            <a href="#/poll?class_id=${classId}" class="btn btn-sm btn-primary">+ New Poll</a>
          </div>
          ${polls.length === 0 ? '<p class="text-muted" style="padding:1rem">No polls yet.</p>' : ''}
          <div class="list-compact">
            ${polls.map(p => `
              <div class="list-item flex-between">
                <div>
                  <strong>${escHtml(p.title)}</strong>
                  <div class="text-sm text-muted">
                    <span class="badge badge-sm ${p.poll_mode === 'planned' ? 'badge-outline' : 'badge-info'}">${p.poll_mode}</span>
                    <span class="badge badge-sm ${p.status === 'active' ? 'badge-success' : p.status === 'closed' ? 'badge-primary' : 'badge-outline'}">${p.status}</span>
                    <span class="text-sm">${p.total_votes} votes</span>
                  </div>
                </div>
                <div class="flex gap-1">
                  ${p.status === 'draft' ? `<button class="btn btn-sm btn-success" onclick="startPoll(${p.id})">▶ Start</button>` : ''}
                  ${p.status === 'active' ? `<button class="btn btn-sm btn-danger" onclick="endPoll(${p.id})">⏹ End</button>` : ''}
                  ${p.status === 'closed' ? `<a href="#/poll-results?id=${p.id}" class="btn btn-sm btn-outline">Results</a>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>

      <!-- Live Devices (teacher dashboard — polling every 5s) -->
      <div class="card mt-2">
        <div class="card-header flex-between">
          <h2>📡 Live Devices <span id="live-devices-count" class="badge badge-outline">…</span></h2>
          <span id="live-devices-updated" class="badge badge-outline">polling 5s</span>
        </div>
        <div id="live-devices-grid" class="device-grid">
          <p class="text-muted" style="padding:1rem">Loading devices…</p>
        </div>
      </div>

      <!-- Students -->
      <div class="card mt-2">
        <div class="card-header">
          <h2>🎓 Students (${students.length})</h2>
          <div class="flex gap-1" style="flex-wrap:wrap">
            <button class="btn btn-sm btn-outline" onclick="toggleClassCsvImport()">⬆ Import CSV</button>
            <button class="btn btn-sm btn-primary" onclick="toggleClassStudentForm()">+ Enroll Student</button>
          </div>
        </div>

        <div id="class-add-student" class="hidden" style="padding:1rem;border-bottom:1px solid var(--border)">
          <div class="form-group" style="position:relative">
            <label>Search Universal Student Registry</label>
            <input type="text" id="cs-search" placeholder="Search by name or roll number…" autocomplete="off" />
            <div id="cs-search-results" class="student-search-results hidden"></div>
          </div>
          <p class="text-muted" style="margin-top:0.5rem;font-size:0.85rem">Type to search students in the universal registry, then click Enroll to add them to this class.</p>
        </div>

        <div id="class-csv-import" class="hidden" style="padding:1rem;border-bottom:1px solid var(--border)">
          <p class="form-hint" style="margin-top:0;margin-bottom:0.75rem">
            Add students to this classroom from CSV — creates them in the universal registry and enrolls them here.
            All 7 columns are <strong>compulsory</strong>: <strong>roll_number</strong> (10 alphanumeric), <strong>student_name</strong>,
            <strong>email</strong>, <strong>phone</strong>, <strong>program</strong>, <strong>enrollment_year</strong>, <strong>graduation_year</strong>.
          </p>
          <div class="csv-drop" id="class-csv-drop">
            <p style="margin:0 0 0.5rem">Drop CSV file here or click to browse</p>
            <input type="file" id="class-csv-file" accept=".csv" style="display:none" />
            <button class="btn btn-sm btn-outline" id="class-csv-browse">Choose File</button>
          </div>
          <div id="class-csv-status" class="text-muted text-sm mt-1"></div>
        </div>

        ${students.length === 0 ? '<p class="text-muted" style="padding:1rem">No students registered yet. Add them here or in the admin dashboard.</p>' : ''}
        <div class="table-responsive">
          <table class="table">
            <thead><tr><th>Name</th><th>Roll #</th><th>Email</th><th>Device</th><th>Participation</th><th></th></tr></thead>
            <tbody id="roster-tbody">
              ${students.map(s => `
                <tr>
                  <td><strong>${escHtml(s.student_name)}</strong></td>
                  <td>${escHtml(s.roll_number || '—')}</td>
                  <td class="text-muted">${escHtml(s.email || '—')}</td>
                  <td>${s.device_mac ? `<code>${escHtml(s.device_mac)}</code>` : '<span class="text-muted">Not linked</span>'}</td>
                  <td>
                    <a href="#/student?id=${s.id}&class=${classId}" class="btn btn-sm btn-outline">View</a>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-danger-ghost" onclick="unenrollStudent(${classId}, ${s.id})">Unenroll</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Class devices (R8, admin only) -->
      ${isAdmin ? `
      <div class="card mt-2">
        <div class="card-header">
          <h2>📡 Class Devices</h2>
          <a href="#/admin/modules" class="btn btn-sm btn-outline">Manage modules</a>
        </div>
        <div class="table-responsive">
          <table class="table">
            <thead><tr><th>Device</th><th>Type</th><th>Status</th><th>Firmware</th></tr></thead>
            <tbody>
              ${classDevices && classDevices.node ? `
                <tr>
                  <td><strong>${escHtml(classDevices.node.device_name || classDevices.node.mac_address)}</strong><br>
                  <span class="text-muted text-sm">${escHtml(classDevices.node.mac_address)}</span></td>
                  <td><span class="badge badge-primary">${escHtml(classDevices.node.device_type)}</span></td>
                  <td><span class="badge ${classDevices.node.is_connected ? 'badge-success' : ''}">${classDevices.node.is_connected ? 'connected' : 'offline'}</span></td>
                  <td class="text-sm">v${escHtml(classDevices.node.firmware_version || '0.0.0')}</td>
                </tr>
              ` : '<tr><td colspan="4" class="text-muted">No class node assigned to this classroom yet.</td></tr>'}
              ${(classDevices && classDevices.student_devices || []).map(d => `
                <tr>
                  <td><strong>${escHtml(d.device_name || d.mac_address)}</strong><br>
                  <span class="text-muted text-sm">${escHtml(d.mac_address)}</span></td>
                  <td><span class="badge badge-outline">${escHtml(d.device_type)}</span></td>
                  <td><span class="badge ${d.is_connected ? 'badge-success' : ''}">${d.is_connected ? 'linked' : 'offline'}</span></td>
                  <td class="text-sm">v${escHtml(d.firmware_version || '0.0.0')}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
      ` : ''}

      <!-- Live Feed -->
      <div class="card mt-2">
        <div class="card-header">
          <h2>📡 Live Feed</h2>
          <span id="ws-status" class="badge badge-outline">Connecting...</span>
        </div>
        <div id="live-feed" class="live-feed"></div>
      </div>

      <!-- Manage Faculty Modal -->
      <div id="faculty-modal" class="modal hidden">
        <div class="modal-backdrop" onclick="this.parentElement.classList.add('hidden')"></div>
        <div class="modal-content card">
          <h2>Manage Faculty for ${escHtml(cls.name)}</h2>
          <p class="text-muted text-sm">Select every teacher assigned to this classroom. The primary owner is shown first.</p>
          <div id="faculty-list" class="mt-1">
            <p class="text-muted">Loading teachers…</p>
          </div>
          <div class="flex gap-1 mt-2">
            <button class="btn btn-primary" onclick="saveClassFaculty(${classId})">Save Faculty</button>
            <button class="btn btn-outline" onclick="document.getElementById('faculty-modal').classList.add('hidden')">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Wire up student search-and-enroll
  const csSearch = document.getElementById('cs-search');
  const csResults = document.getElementById('cs-search-results');
  if (csSearch && csResults) {
    let debounce = null;
    const enrolledIds = new Set(students.map(s => s.id));

    csSearch.addEventListener('input', () => {
      clearTimeout(debounce);
      const q = csSearch.value.trim();
      if (q.length < 2) { csResults.classList.add('hidden'); return; }
      debounce = setTimeout(async () => {
        try {
          const all = await studentsApi.list(q);
          const matches = all.filter(s => !enrolledIds.has(s.id)).slice(0, 10);
          if (!matches.length) {
            csResults.innerHTML = '<div class="student-search-item text-muted">No un-enrolled students found</div>';
            csResults.classList.remove('hidden');
            return;
          }
          csResults.innerHTML = matches.map(s => `
            <div class="student-search-item">
              <div>
                <strong>${escHtml(s.student_name)}</strong>
                <span class="text-muted">${escHtml(s.roll_number)}</span>
                ${s.email ? `<span class="text-muted" style="margin-left:0.5rem">${escHtml(s.email)}</span>` : ''}
              </div>
              <button class="btn btn-xs btn-primary" data-enroll="${s.id}">Enroll</button>
            </div>
          `).join('');
          csResults.classList.remove('hidden');
          csResults.querySelectorAll('[data-enroll]').forEach(btn => {
            btn.addEventListener('click', async () => {
              const sid = parseInt(btn.dataset.enroll);
              btn.disabled = true; btn.textContent = 'Enrolling…';
              try {
                await studentsApi.enroll(parseInt(classId), sid);
                enrolledIds.add(sid);
                btn.textContent = '✓ Enrolled';
                btn.className = 'btn btn-xs';
                showToast('Student enrolled!', 'success');
                await refreshClassRoster(parseInt(classId));
              } catch (err) { showToast(err.message, 'error'); btn.disabled = false; btn.textContent = 'Enroll'; }
            });
          });
        } catch (err) { csResults.classList.add('hidden'); }
      }, 300);
    });

    csSearch.addEventListener('blur', () => {
      setTimeout(() => csResults.classList.add('hidden'), 200);
    });
    csSearch.addEventListener('focus', () => {
      if (csSearch.value.trim().length >= 2) csResults.classList.remove('hidden');
    });
  }

  // ── Class-level CSV import ──────────────────────────────────
  const classCsvDrop = document.getElementById('class-csv-drop');
  const classCsvFile = document.getElementById('class-csv-file');
  if (classCsvDrop && classCsvFile) {
    const classCsvStatus = document.getElementById('class-csv-status');
    classCsvDrop.onclick = () => classCsvFile.click();
    document.getElementById('class-csv-browse').onclick = (e) => { e.stopPropagation(); classCsvFile.click(); };
    classCsvDrop.ondragover = (e) => { e.preventDefault(); classCsvDrop.style.borderColor = 'var(--primary)'; };
    classCsvDrop.ondragleave = () => { classCsvDrop.style.borderColor = ''; };
    classCsvDrop.ondrop = (e) => {
      e.preventDefault();
      classCsvDrop.style.borderColor = '';
      if (e.dataTransfer.files.length) {
        classCsvFile.files = e.dataTransfer.files;
        classCsvFile.dispatchEvent(new Event('change'));
      }
    };
    classCsvFile.addEventListener('change', async () => {
      const f = classCsvFile.files[0];
      if (!f) return;
      if (!f.name.toLowerCase().endsWith('.csv')) { showToast('Please choose a .csv file', 'error'); return; }
      classCsvStatus.textContent = `Importing ${f.name}…`;
      try {
        const result = await adminApi.importClassCsv(parseInt(classId), f);
        classCsvStatus.innerHTML = `<span style="color:var(--success)">✓ ${result.inserted} imported</span>` +
          (result.skipped.length ? ` · <span style="color:var(--warning)">${result.skipped.length} skipped</span>`
            + ` — ${result.skipped.map(e => `row ${e.row} (${escHtml(e.roll_number)}): ${escHtml(e.error)}`).join('; ')}` : '');
        showToast(`${result.inserted} student(s) imported into this class`, 'success');
        await refreshClassRoster(parseInt(classId));
        classCsvFile.value = '';
      } catch (err) {
        classCsvStatus.textContent = '';
        showToast(err.message, 'error');
      }
    });
  }

  // Wire live feed
  classSocket.on('connected', () => {
    document.getElementById('ws-status').textContent = 'Connected';
    document.getElementById('ws-status').className = 'badge badge-success';
  });
  classSocket.on('disconnected', () => {
    document.getElementById('ws-status').textContent = 'Disconnected';
    document.getElementById('ws-status').className = 'badge badge-danger';
  });
  classSocket.on('quiz_question', (data) => {
    const feed = document.getElementById('live-feed');
    if (feed) {
      const line = document.createElement('p');
      line.innerHTML = `<span class="text-muted">[${istTime(Date.now())}]</span> 📝 Quiz: <strong>${escHtml(data.title)}</strong> — Q${(data.question_order || 0) + 1}/${data.total_questions}: ${escHtml(data.question_text)}`;
      feed.prepend(line);
    }
  });
  classSocket.on('quiz_answer', (data) => {
    const feed = document.getElementById('live-feed');
    if (feed) {
      const line = document.createElement('p');
      line.innerHTML = `<span class="text-muted">[${istTime(Date.now())}]</span> ✅ Answer received — total: ${data.total_answers}`;
      feed.prepend(line);
    }
  });
  classSocket.on('quiz_ended', (data) => {
    const feed = document.getElementById('live-feed');
    if (feed) {
      const line = document.createElement('p');
      line.innerHTML = `<span class="text-muted">[${istTime(Date.now())}]</span> 🏁 Quiz ended: <strong>${escHtml(data.title)}</strong>`;
      feed.prepend(line);
    }
  });
  classSocket.on('poll_started', (data) => {
    const feed = document.getElementById('live-feed');
    if (feed) {
      const line = document.createElement('p');
      line.innerHTML = `<span class="text-muted">[${istTime(Date.now())}]</span> 📊 Poll live: <strong>${escHtml(data.title)}</strong>`;
      feed.prepend(line);
    }
  });
  classSocket.on('poll_vote', (data) => {
    const feed = document.getElementById('live-feed');
    if (feed) {
      const line = document.createElement('p');
      line.innerHTML = `<span class="text-muted">[${istTime(Date.now())}]</span> 🗳 Vote — total: ${data.total_votes}`;
      feed.prepend(line);
    }
  });
  classSocket.on('poll_ended', (data) => {
    const feed = document.getElementById('live-feed');
    if (feed) {
      const line = document.createElement('p');
      line.innerHTML = `<span class="text-muted">[${istTime(Date.now())}]</span> 📊 Poll ended: <strong>${escHtml(data.title)}</strong> — ${data.total_votes} votes`;
      feed.prepend(line);
    }
  });
}

window.activateClass = async function (classId) {
  try {
    await classesApi.activate(classId);
    showToast('Class activated!', 'success');
    renderClassDetail(document.getElementById('app'), new URLSearchParams(`id=${classId}`));
  } catch (err) { showToast(err.message, 'error'); }
};

window.openManageFaculty = async function (classId) {
  const modal = document.getElementById('faculty-modal');
  if (!modal) return;
  const list = document.getElementById('faculty-list');
  list.innerHTML = '<p class="text-muted">Loading teachers…</p>';
  modal.classList.remove('hidden');
  try {
    const [cls, teachers] = await Promise.all([
      classesApi.get(classId),
      adminApi.listUsers('teacher'),
    ]);
    const current = new Set((cls.faculty_names || []).map(f => f.id));
    list.innerHTML = teachers.map(t => `
      <label class="faculty-option flex gap-2" style="align-items:center;padding:0.4rem 0;border-bottom:1px solid var(--border)">
        <input type="checkbox" value="${t.id}" ${current.has(t.id) ? 'checked' : ''} />
        <span><strong>${escHtml(t.full_name || t.username)}</strong> <span class="text-muted text-sm">${t.id === cls.teacher_id ? '(owner)' : ''}</span></span>
      </label>
    `).join('') || '<p class="text-muted">No teachers available. Create teacher accounts first.</p>';
  } catch (err) {
    list.innerHTML = '<p class="text-danger">Failed to load teachers.</p>';
    showToast(err.message, 'error');
  }
};

window.saveClassFaculty = async function (classId) {
  const boxes = Array.from(document.querySelectorAll('#faculty-list input[type=checkbox]:checked'));
  const teacherIds = boxes.map(b => parseInt(b.value));
  try {
    await adminApi.setFaculty(classId, teacherIds);
    showToast('Faculty updated!', 'success');
    document.getElementById('faculty-modal').classList.add('hidden');
    renderClassDetail(document.getElementById('app'), new URLSearchParams(`id=${classId}`));
  } catch (err) { showToast(err.message, 'error'); }
};

window.deactivateClass = async function (classId) {
  try {
    await classesApi.deactivate(classId);
    showToast('Class deactivated', 'info');
    renderClassDetail(document.getElementById('app'), new URLSearchParams(`id=${classId}`));
  } catch (err) { showToast(err.message, 'error'); }
};

window.startQuiz = async function (quizId) {
  try {
    await quizzesApi.start(quizId);
    showToast('Quiz started!', 'success');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

window.stopQuiz = async function (quizId) {
  try {
    await quizzesApi.stop(quizId);
    showToast('Quiz stopped', 'info');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

window.nextQuestion = async function (quizId) {
  try {
    await quizzesApi.nextQuestion(quizId);
    showToast('Next question sent', 'success');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

window.startPoll = async function (pollId) {
  try {
    await pollsApi.start(pollId);
    showToast('Poll started!', 'success');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

window.endPoll = async function (pollId) {
  try {
    await pollsApi.end(pollId);
    showToast('Poll ended', 'info');
    router();
  } catch (err) { showToast(err.message, 'error'); }
};

// ── Quiz Create ────────────────────────────────────────────────

async function renderQuizCreate(app, params) {
  const user = await authApi.me();
  const classId = params.get('class_id');
  if (!classId) { navigate('#/classes'); return; }

  let questionIndex = 0;

  function renderQuizForm() {
    app.innerHTML = `
      ${renderNavbar(user, window.location.hash)}
      <div class="container" style="max-width:750px">
        <a href="#/class?id=${classId}" class="text-muted" style="font-size:0.9rem">← Back to Class</a>
        <div class="card mt-1">
          <h1>Create Quiz</h1>
          <form id="quiz-form">
            <div class="form-group">
              <label>Quiz Title</label>
              <input type="text" id="quiz-title" placeholder="Chapter 5 Review" required />
            </div>

            <div class="grid-2">
              <div class="form-group">
                <label>Quiz Mode</label>
                <select id="quiz-mode">
                  <option value="planned">Planned — start when ready</option>
                  <option value="impromptu">Impromptu — start immediately</option>
                </select>
                <small class="text-muted">Planned quizzes wait for you to press Start. Impromptu quizzes go live on creation.</small>
              </div>
              <div class="form-group">
                <label>Timing Mode</label>
                <select id="timing-mode">
                  <option value="manual">Manual — advance questions yourself</option>
                  <option value="per_question">Per-Question Timer</option>
                  <option value="total">Total Time Limit</option>
                </select>
              </div>
            </div>

            <div id="timing-options" class="hidden">
              <div class="form-group" id="pq-time-group" style="display:none">
                <label>Seconds per Question</label>
                <input type="number" id="question-time" min="5" max="300" value="30" />
              </div>
              <div class="form-group" id="total-time-group" style="display:none">
                <label>Total Time (seconds)</label>
                <input type="number" id="total-time" min="10" max="3600" value="300" />
              </div>
            </div>

            <div id="questions-container">
              <div class="card" style="background:var(--input);margin-bottom:1rem" data-qi="0">
                <h2 style="font-size:1rem">Question 1</h2>
                <div class="form-group">
                  <label>Question Text</label>
                  <input type="text" class="q-text" placeholder="What is 2+2?" required />
                </div>
                <div class="form-group">
                  <label>Options (2–4, one per line; prefix the correct one with *)</label>
                  <textarea class="q-options" rows="4" placeholder="*4&#10;3&#10;5&#10;2+2" required></textarea>
                </div>
              </div>
            </div>

            <button type="button" class="btn btn-outline mb-2" onclick="addQuizQuestion()">+ Add Question</button>

            <div class="flex gap-1">
              <button type="submit" class="btn btn-primary">Create Quiz</button>
              <a href="#/class?id=${classId}" class="btn btn-outline">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  renderQuizForm();

  // Toggle timing options
  document.getElementById('timing-mode').addEventListener('change', (e) => {
    const timingOpts = document.getElementById('timing-options');
    const pqGroup = document.getElementById('pq-time-group');
    const totalGroup = document.getElementById('total-time-group');
    timingOpts.classList.toggle('hidden', e.target.value === 'manual');
    pqGroup.style.display = e.target.value === 'per_question' ? 'block' : 'none';
    totalGroup.style.display = e.target.value === 'total' ? 'block' : 'none';
  });

  document.getElementById('quiz-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const questions = [];
    const cards = document.querySelectorAll('[data-qi]');
    for (const card of cards) {
      const text = card.querySelector('.q-text').value.trim();
      const raw = card.querySelector('.q-options').value.trim().split('\n').map(l => l.trim()).filter(Boolean);
      if (!text || raw.length < 2 || raw.length > 4) {
        showToast('Each question needs text and 2–4 options (student modules have 4 buttons)', 'error');
        return;
      }
      let correctIdx = 0;
      const options = raw.map((opt, i) => {
        if (opt.startsWith('*')) { correctIdx = i; return opt.slice(1).trim(); }
        return opt;
      });
      questions.push({ question_text: text, options, correct_option: correctIdx });
    }

    if (questions.length === 0) {
      showToast('Add at least one question', 'error');
      return;
    }

    try {
      const timingMode = document.getElementById('timing-mode').value;
      const data = {
        class_session_id: parseInt(classId),
        title: document.getElementById('quiz-title').value.trim(),
        questions,
        quiz_mode: document.getElementById('quiz-mode').value,
        timing_mode: timingMode,
        question_time_limit: timingMode === 'per_question' ? parseInt(document.getElementById('question-time').value) || 30 : 0,
        total_time_limit: timingMode === 'total' ? parseInt(document.getElementById('total-time').value) || 300 : 0,
      };
      const quiz = await quizzesApi.create(data);
      showToast('Quiz created!', 'success');
      (quiz.warnings || []).forEach(w => showToast(w, 'info'));   // text the modules will truncate
      navigate(`#/class?id=${classId}`);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

window.addQuizQuestion = function () {
  const container = document.getElementById('questions-container');
  const qi = container.children.length;
  const div = document.createElement('div');
  div.className = 'card';
  div.style.cssText = 'background:var(--input);margin-bottom:1rem';
  div.dataset.qi = qi;
  div.innerHTML = `
    <div class="flex-between">
      <h2 style="font-size:1rem">Question ${qi + 1}</h2>
      <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('[data-qi]').remove()">✕</button>
    </div>
    <div class="form-group">
      <label>Question Text</label>
      <input type="text" class="q-text" placeholder="Question..." required />
    </div>
    <div class="form-group">
      <label>Options (2–4, one per line; prefix the correct one with *)</label>
      <textarea class="q-options" rows="4" placeholder="*Correct&#10;Wrong 1&#10;Wrong 2&#10;Wrong 3" required></textarea>
    </div>
  `;
  container.appendChild(div);
};

// ── Poll Create ────────────────────────────────────────────────

async function renderPollCreate(app, params) {
  const user = await authApi.me();
  const classId = params.get('class_id');
  if (!classId) { navigate('#/classes'); return; }

  app.innerHTML = `
    ${renderNavbar(user, window.location.hash)}
    <div class="container" style="max-width:600px">
      <a href="#/class?id=${classId}" class="text-muted" style="font-size:0.9rem">← Back to Class</a>
      <div class="card mt-1">
        <h1>Create Poll</h1>
        <form id="poll-form">
          <div class="form-group">
            <label>Question</label>
            <input type="text" id="poll-question" placeholder="Which topic should we review?" required />
          </div>

          <div class="form-group">
            <label>Poll Mode</label>
            <select id="poll-mode">
              <option value="live">Live — start immediately</option>
              <option value="planned">Planned — start when ready</option>
            </select>
            <small class="text-muted">Live polls are visible to students immediately. Planned polls wait for you to start them.</small>
          </div>

          <div class="form-group">
            <label>Options (2–4, one per line)</label>
            <textarea id="poll-options" rows="4" placeholder="Option 1&#10;Option 2&#10;Option 3&#10;Option 4" required></textarea>
          </div>

          <div class="flex gap-1">
            <button type="submit" class="btn btn-primary">Create Poll</button>
            <a href="#/class?id=${classId}" class="btn btn-outline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `;

  document.getElementById('poll-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('poll-question').value.trim();
    const lines = document.getElementById('poll-options').value.trim().split('\n').map(l => l.trim()).filter(Boolean);

    if (lines.length < 2 || lines.length > 4) {
      showToast('Provide 2–4 options (student modules have 4 buttons)', 'error');
      return;
    }

    try {
      const poll = await pollsApi.create({
        class_session_id: parseInt(classId),
        title,
        options: lines,
        poll_mode: document.getElementById('poll-mode').value,
      });
      showToast('Poll created!', 'success');
      (poll.warnings || []).forEach(w => showToast(w, 'info'));
      navigate(`#/class?id=${classId}`);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// ── Quiz Results ───────────────────────────────────────────────

async function renderQuizResults(app, params) {
  const user = await authApi.me();
  const quizId = params.get('id');
  if (!quizId) { navigate('#/classes'); return; }

  const results = await quizzesApi.results(quizId);

  app.innerHTML = `
    ${renderNavbar(user, window.location.hash)}
    <div class="container" style="max-width:800px">
      <a href="javascript:history.back()" class="text-muted" style="font-size:0.9rem">← Back</a>
      <div class="card mt-1">
        <h1>📊 ${escHtml(results.title)}</h1>
        <p class="text-muted">${results.status} · ${results.quiz_mode} · ${results.timing_mode}</p>

        ${results.results.map((q, i) => `
          <div class="card mt-1" style="background:var(--input)">
            <h2 style="font-size:1rem">Q${i + 1}: ${escHtml(q.question_text)}</h2>
            <p class="text-sm text-muted">${q.total_answers} answers</p>
            <div class="results-bars">
              ${q.options.map((opt, j) => {
                const count = q.option_counts[j] || 0;
                const pct = q.total_answers > 0 ? Math.round(count / q.total_answers * 100) : 0;
                return `
                  <div class="result-bar-row">
                    <span class="text-sm" style="min-width:120px">${j === q.correct_option ? '✅ ' : ''}${escHtml(opt)}</span>
                    <div class="result-bar-bg">
                      <div class="result-bar-fill" style="width:${pct}%"></div>
                    </div>
                    <span class="text-sm text-muted" style="min-width:50px;text-align:right">${count} (${pct}%)</span>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// ── Poll Results ───────────────────────────────────────────────

async function renderPollResults(app, params) {
  const user = await authApi.me();
  const pollId = params.get('id');
  if (!pollId) { navigate('#/classes'); return; }

  const results = await pollsApi.results(pollId);

  app.innerHTML = `
    ${renderNavbar(user, window.location.hash)}
    <div class="container" style="max-width:600px">
      <a href="javascript:history.back()" class="text-muted" style="font-size:0.9rem">← Back</a>
      <div class="card mt-1">
        <h1>📊 ${escHtml(results.title)}</h1>
        <p class="text-muted">${results.status} · ${results.total_votes} votes · ${results.poll_mode}</p>

        <div class="results-bars mt-1">
          ${results.options.map((opt, i) => {
            const count = results.option_counts[i] || 0;
            const pct = results.total_votes > 0 ? Math.round(count / results.total_votes * 100) : 0;
            return `
              <div class="result-bar-row">
                <span class="text-sm" style="min-width:120px">${escHtml(opt)}</span>
                <div class="result-bar-bg">
                  <div class="result-bar-fill" style="width:${pct}%"></div>
                </div>
                <span class="text-sm text-muted" style="min-width:50px;text-align:right">${count} (${pct}%)</span>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    </div>
  `;
}

// ── Student Detail ─────────────────────────────────────────────

async function renderStudentDetail(app, params) {
  const user = await authApi.me();
  const studentId = params.get('id');
  const classId = params.get('class');
  if (!studentId) { navigate('#/classes'); return; }

  let data;
  try {
    data = await studentsApi.studentParticipation(studentId);
  } catch (err) {
    app.innerHTML = `
      ${renderNavbar(user, window.location.hash)}
      <div class="container"><div class="card"><h1>Error</h1><p>${escHtml(err.message)}</p><a href="#/class?id=${classId}" class="btn btn-primary mt-1">Back to Class</a></div></div>
    `;
    return;
  }

  const stu = data.student;
  app.innerHTML = `
    ${renderNavbar(user, window.location.hash)}
    <div class="container" style="max-width:760px">
      <a href="#/class?id=${classId}" class="text-muted" style="font-size:0.9rem">← Back to Class</a>
      <div class="card mt-1">
        <h1>🎓 ${escHtml(stu.name)}</h1>
        <p class="text-muted">${stu.roll_number ? `Roll #${escHtml(stu.roll_number)} · ` : ''}Student participation summary</p>

        <div class="stats-grid mt-1">
          <div class="stat-card">
            <span class="stat-icon">📝</span>
            <div><div class="stat-value">${data.quizzes_answered}</div><div class="stat-label">Quizzes Attempted</div></div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">🗳️</span>
            <div><div class="stat-value">${data.polls_voted}</div><div class="stat-label">Polls Voted</div></div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">✅</span>
            <div><div class="stat-value">${data.attendance_count}</div><div class="stat-label">Classes Attended</div></div>
          </div>
        </div>

        <div class="grid-2">
          <div class="card" style="box-shadow:none;border:1px solid var(--border)">
            <h2 style="font-size:0.95rem">Quiz Answers (${data.quiz_details.length})</h2>
            ${data.quiz_details.length === 0 ? '<p class="text-muted text-sm mt-1">No quiz answers yet.</p>' : ''}
            <div class="list-compact mt-1">
              ${data.quiz_details.map(q => `
                <div class="list-item text-sm" style="padding:0.4rem 0.6rem">
                  <span>${escHtml(q.quiz_title)}</span>
                  <span class="text-muted">Q${q.question_order + 1} → opt ${q.selected_option}</span>
                </div>
              `).join('')}
            </div>
          </div>
          <div class="card" style="box-shadow:none;border:1px solid var(--border)">
            <h2 style="font-size:0.95rem">Poll Votes (${data.poll_details.length})</h2>
            ${data.poll_details.length === 0 ? '<p class="text-muted text-sm mt-1">No poll votes yet.</p>' : ''}
            <div class="list-compact mt-1">
              ${data.poll_details.map(p => `
                <div class="list-item text-sm" style="padding:0.4rem 0.6rem">
                  <span>${escHtml(p.poll_title)}</span>
                  <span class="text-muted">→ opt ${p.selected_option}</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ── Theme Toggle ──────────────────────────────────────────────

function toggleTheme() {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme');
  let next;
  if (!current) {
    // system default — detect current scheme
    next = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'light' : 'dark';
  } else {
    next = current === 'dark' ? 'light' : 'dark';
  }
  root.setAttribute('data-theme', next);
  localStorage.setItem('impress_theme', next);
  // update icon in navbar if present
  const icon = document.getElementById('theme-icon');
  if (icon) icon.textContent = next === 'dark' ? '☀️' : '🌙';
}

// Apply saved theme on load
(function () {
  const saved = localStorage.getItem('impress_theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    document.addEventListener('DOMContentLoaded', () => {
      const icon = document.getElementById('theme-icon');
      if (icon) icon.textContent = saved === 'dark' ? '☀️' : '🌙';
    });
  }
})();

// ── Helpers ────────────────────────────────────────────────────

function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

// ── Indian Standard Time (Asia/Kolkata, UTC+05:30) ─────────────────────
// The backend stores & serves all timestamps as IST (naive "YYYY-MM-DD HH:MM:SS"
// strings, or epoch-millis). Render everything on the website as IST so an
// admin sees Indian wall-clock time regardless of their browser timezone.

const IST_TZ = 'Asia/Kolkata';
const IST_OFFSET_MIN = 5 * 60 + 30; // +05:30

// Parse a naive-IST datetime string from the server into real epoch millis.
// Interprets the wall-clock components as IST even though they carry no offset.
function istParseToEpoch(s) {
  if (!s) return null;
  const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?/);
  if (!m) return null;
  const ms = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0));
  return ms - IST_OFFSET_MIN * 60 * 1000;
}

// Format an epoch/Date for display in Indian Standard Time.
function istFormat(value, opts) {
  const epoch = value instanceof Date ? value.getTime() : (value ?? null);
  if (epoch === null || Number.isNaN(epoch)) return '—';
  const o = Object.assign({ timeZone: IST_TZ }, opts);
  return new Intl.DateTimeFormat('en-IN', o).format(new Date(epoch));
}

// Ready-made IST formatters used across the SPA.
const istTime = (v) => istFormat(v, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
const istDateTime = (v) => istFormat(v, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
