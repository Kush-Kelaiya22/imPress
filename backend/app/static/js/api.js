/* imPress — API client (REST + WebSocket) */

const API_BASE = '/api';

/* The session token lives in an HttpOnly cookie that scripts cannot read
 * (v2.2). Page storage only remembers that someone signed in, so the router
 * can show the login page without a round trip; the server decides. */
const SIGNED_IN = 'impress_signed_in';
const CSRF = { 'X-Impress-Request': '1' };   // required on cookie-authenticated changes

function markSignedIn(on) {
  try {
    if (on) localStorage.setItem(SIGNED_IN, '1'); else localStorage.removeItem(SIGNED_IN);
    localStorage.removeItem('impress_token');   // left by v2.1
  } catch { /* storage unavailable */ }
}

function clearToken() { markSignedIn(false); }

function isLoggedIn() {
  try { return localStorage.getItem(SIGNED_IN) === '1'; } catch { return true; }
}

async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...CSRF,
    // live refresh (v2.2): not user activity, unless the user acted since it started
    ...(window.__quiet && !(typeof Live !== 'undefined' && Live.lastUser >= window.__quiet) ? { 'X-Impress-Background': '1' } : {}),
    ...options.headers,
  };

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && path !== '/auth/login') {
    // the server says why the session ended: a disabled account and a restart get a proper notice, not a redirect
    const why = res.headers.get('X-Session-Code');
    if (typeof Overlays !== 'undefined' && (why === 'disabled' || why === 'restart') && !path.startsWith('/auth/login')) {
      Overlays.sessionEnded(why);
      throw new Error('Unauthorized');
    }
    clearToken();
    window.location.hash = '#/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const d = err.detail;
    if (res.status === 403 && d && d.code === 'PASSWORD_CHANGE_REQUIRED' && typeof Onboarding !== 'undefined') {
      Onboarding.required();                 // temporary credentials: the welcome flow, not an error page
      throw new Error('Unauthorized');
    }
    // {"detail": {"code", "message"}} (#116) or FastAPI's string / validation list
    const msg = typeof d === 'string' ? d : (d && d.message) ||
      (Array.isArray(d) ? d.map(v => v.msg).filter(Boolean).join('; ') : '') || 'Request failed';
    const retryAfter = Math.max(0, Number(res.headers.get('Retry-After')) || 0);
    throw Object.assign(new Error(msg), { status: res.status, code: d && d.code, detail: d, retryAfter });
  }

  if (res.status === 204) return null;
  return await res.json();
}

/** Multipart upload with progress (fetch can't report upload progress).
 *  Resolves with the JSON body; rejects with err.status / err.body set. */
function uploadFile(path, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}${path}`);
    xhr.setRequestHeader('X-Impress-Request', '1');
    xhr.upload.onprogress = (e) => {
      if (onProgress && e.lengthComputable) onProgress(Math.round((e.loaded * 100) / e.total));
    };
    xhr.onerror = () => reject(new Error('Network error: the upload did not reach the server'));
    xhr.onload = () => {
      let body;
      try { body = JSON.parse(xhr.responseText); } catch { body = { detail: xhr.statusText }; }
      if (xhr.status === 401) {
        clearToken();
        window.location.hash = '#/login';
        return reject(new Error('Unauthorized'));
      }
      if (xhr.status < 200 || xhr.status >= 300) {
        const d = body.detail;
        const msg = typeof d === 'string' ? d : (d && d.message) || 'Upload failed';
        return reject(Object.assign(new Error(msg), { status: xhr.status, body }));
      }
      resolve(body);
    };
    const form = new FormData();
    form.append('file', file);
    xhr.send(form);
  });
}

// ── Auth ────────────────────────────────────────────────────────

const authApi = {
  async login(username, password) {
    const res = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    markSignedIn(true);
    return res;
  },
  async me() {
    return apiRequest('/auth/me');
  },
  async updateProfile(fullName, displayName) {
    const body = { full_name: fullName };
    if (displayName !== undefined) body.display_name = displayName;
    return apiRequest('/auth/me', { method: 'PUT', body: JSON.stringify(body) });
  },
  async onboard(displayName, theme) {                       // the welcome set-up (v2.2)
    return apiRequest('/auth/onboarding', { method: 'POST', body: JSON.stringify({ display_name: displayName, theme }) });
  },
  async changePassword(currentPassword, newPassword) {
    return apiRequest('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  },
  async logout() {
    try { await fetch(`${API_BASE}/auth/logout`, { method: 'POST', headers: CSRF }); } catch { /* offline: the cookie expires */ }
    clearToken();
  },
};

// ── Admin ───────────────────────────────────────────────────────

const adminApi = {
  classTemplateUrl: `${API_BASE}/admin/classes/import-template.csv`,

  /** Plan (dry_run) or run a course/section CSV import. */
  importClassesCsv(file, { mode = 'create', dryRun = true } = {}, onProgress) {
    return uploadFile(`/admin/classes/import?mode=${mode}&dry_run=${dryRun}`, file, onProgress);
  },

  /** Download every course section as CSV (authenticated, so via a blob). */
  async exportClassesCsv() {
    const res = await fetch(`${API_BASE}/admin/classes/export.csv`, {
      headers: CSRF,
    });
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    const url = URL.createObjectURL(await res.blob());
    const a = Object.assign(document.createElement('a'), { href: url, download: 'impress-classes.csv' });
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return Number(res.headers.get('X-Omitted-Classes') || 0);
  },

  // Users
  async createUser(data) {
    return apiRequest('/admin/users', { method: 'POST', body: JSON.stringify(data) });
  },
  async listUsers(role = '') {
    return apiRequest(`/admin/users${role ? `?role=${role}` : ''}`);
  },
  async updateUser(userId, data) {   // profile only: full_name, email (#119)
    return apiRequest(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) });
  },
  async deactivateUser(userId) {
    return apiRequest(`/admin/users/${userId}/deactivate`, { method: 'POST' });
  },
  async reactivateUser(userId) {
    return apiRequest(`/admin/users/${userId}/reactivate`, { method: 'POST' });
  },
  async changeRole(userId, role) {
    return apiRequest(`/admin/users/${userId}/role`, { method: 'POST', body: JSON.stringify({ role }) });
  },
  async deleteUser(userId) {
    return apiRequest(`/admin/users/${userId}`, { method: 'DELETE' });
  },
  async endSessions(userId) {                     // v2.2: sign a user out everywhere
    return apiRequest(`/admin/users/${userId}/end-sessions`, { method: 'POST' });
  },
  async studentsSummary() { return apiRequest('/admin/students/summary'); },
  async resetPassword(userId, newPassword) {               // no password given: one is generated and returned once
    return apiRequest(`/admin/users/${userId}/reset-password`, {
      method: 'POST',
      body: JSON.stringify(newPassword ? { new_password: newPassword } : {}),
    });
  },
  setDesignation(userId, designation) { return apiRequest(`/admin/users/${userId}/designation`, { method: 'POST', body: JSON.stringify({ designation }) }); },
  presence() { return apiRequest('/admin/presence'); },
  activitySummary(userId, days = 30) { return apiRequest(`/admin/users/${userId}/activity-summary?days=${days}`); },
  trash() { return apiRequest('/admin/users/deleted'); },
  restoreUser(id) { return apiRequest(`/admin/users/deleted/${id}/restore`, { method: 'POST' }); },
  purgeUser(id) { return apiRequest(`/admin/users/deleted/${id}`, { method: 'DELETE' }); },
  risk() { return apiRequest('/admin/risk'); },
  traffic() { return apiRequest('/admin/traffic'); },
  features() { return apiRequest('/admin/features'); },
  setFeature(name, body) { return apiRequest(`/admin/features/${name}`, { method: 'PUT', body: JSON.stringify(body) }); },
  featureLog(flag = '') { return apiRequest(`/admin/features/log${flag ? `?flag=${encodeURIComponent(flag)}` : ''}`); },
  requirements() { return apiRequest('/admin/system/requirements'); },
  backups() { return apiRequest('/admin/backups'); },
  saveBackup(name, note = '') { return apiRequest('/admin/backups', { method: 'POST', body: JSON.stringify({ name, note }) }); },
  describeBackup(id) { return apiRequest(`/admin/backups/${id}`); },
  restoreBackup(id, password, confirm, approvalId = null, code = '') {
    return apiRequest(`/admin/backups/${id}/restore`, { method: 'POST', body: JSON.stringify({ password, code, confirm, approval_id: approvalId }) });
  },
  deleteBackup(id) { return apiRequest(`/admin/backups/${id}`, { method: 'DELETE' }); },
  search(q) { return apiRequest(`/search?q=${encodeURIComponent(q)}`); },
  async importUsersCsv(file) {
    const form = new FormData();
    form.append('file', file);
    const headers = CSRF;
    const res = await fetch(`${API_BASE}/admin/users/import`, { method: 'POST', headers, body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Import failed');
    }
    return res.json();
  },

  // Classes (Classrooms)
  async createClass(data) {
    return apiRequest('/admin/classes', { method: 'POST', body: JSON.stringify(data) });
  },
  async listClasses() {
    return apiRequest('/admin/classes');
  },
  async updateClass(classId, data) {
    return apiRequest(`/admin/classes/${classId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  async deleteClass(classId) {
    return apiRequest(`/admin/classes/${classId}`, { method: 'DELETE' });
  },
  async setFaculty(classId, teacherIds) {
    return apiRequest(`/admin/classes/${classId}/faculty`, {
      method: 'PUT',
      body: JSON.stringify({ teacher_ids: teacherIds }),
    });
  },
  async importClassCsv(classId, file) {
    const form = new FormData();
    form.append('file', file);
    const headers = CSRF;
    const res = await fetch(`${API_BASE}/admin/classes/${classId}/import-students`, { method: 'POST', headers, body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Import failed');
    }
    return res.json();
  },
  async assignTeacher(classId, teacherId) {
    return apiRequest(`/admin/classes/${classId}/assign-teacher`, {
      method: 'POST',
      body: JSON.stringify({ teacher_id: teacherId }),
    });
  },

  // Activity
  async activityLogs(limit = 50, entityType = '') {
    return apiRequest(`/admin/activity?limit=${limit}${entityType ? `&entity_type=${entityType}` : ''}`);
  },
};

// ── Modules / Devices (R7 connectivity, R8 OTA) ───────────────────

const firmwareApi = {
  list(target = '') { return apiRequest(`/admin/firmware${target ? `?target=${target}` : ''}`); },
  detail(id) { return apiRequest(`/admin/firmware/${id}`); },
  upload(file, onProgress) { return uploadFile('/admin/firmware', file, onProgress); },
  approve(id) { return apiRequest(`/admin/firmware/${id}/approve`, { method: 'POST' }); },
  deprecate(id) { return apiRequest(`/admin/firmware/${id}/deprecate`, { method: 'POST' }); },
  update(id, data) { return apiRequest(`/admin/firmware/${id}`, { method: 'PATCH', body: JSON.stringify(data) }); },
  remove(id) { return apiRequest(`/admin/firmware/${id}`, { method: 'DELETE' }); },
};

const deploymentsApi = {
  list() { return apiRequest('/admin/deployments'); },
  get(id) { return apiRequest(`/admin/deployments/${id}`); },
  create(body, dryRun = false) {
    return apiRequest(`/admin/deployments${dryRun ? '?dry_run=true' : ''}`, { method: 'POST', body: JSON.stringify(body) });
  },
  act(id, action) { return apiRequest(`/admin/deployments/${id}/${action}`, { method: 'POST' }); },
};

const modulesApi = {
  async list(deviceType = '') {
    return apiRequest(`/admin/modules${deviceType ? `?device_type=${deviceType}` : ''}`);
  },
  async get(deviceId) {
    return apiRequest(`/admin/modules/${deviceId}`);
  },
  async resetKey(deviceId) {
    return apiRequest(`/admin/modules/${deviceId}/reset-key`, { method: 'POST' });
  },
  async setAccess(deviceId, isActive) {
    return apiRequest(`/admin/modules/${deviceId}/access`, {
      method: 'POST',
      body: JSON.stringify({ is_active: isActive }),
    });
  },
  async pushOta(deviceId, version) {
    return apiRequest(`/admin/modules/${deviceId}/ota`, {
      method: 'POST',
      body: JSON.stringify({ version }),
    });
  },
  async verify(deviceId) {
    return apiRequest(`/admin/modules/${deviceId}/verify`, { method: 'POST' });
  },
  async linkDevice(nodeId, deviceId) {
    return apiRequest(`/admin/modules/${nodeId}/link-device`, {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId }),
    });
  },
  async unlink(deviceId) {
    return apiRequest(`/admin/modules/${deviceId}/unlink`, { method: 'POST' });
  },
  async classDevices(classId) {
    return apiRequest(`/admin/classes/${classId}/devices`);
  },
};

// ── Devices (live presence — teacher dashboard) ────────────────────

const studentModulesApi = {
  async list() {
    return apiRequest('/admin/student-modules');
  },
};

const devicesApi = {
  async live(classId) {
    return apiRequest(`/devices/live?class_id=${classId}`);
  },
};

// ── Courses (universal catalog) ───────────────────────────────────

const coursesApi = {
  async create(data) {
    return apiRequest('/courses/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async list() {
    return apiRequest('/courses/');
  },
  async get(courseId) {
    return apiRequest(`/courses/${courseId}`);
  },
  async update(courseId, data) {
    return apiRequest(`/courses/${courseId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  async delete(courseId) {
    return apiRequest(`/courses/${courseId}`, { method: 'DELETE' });
  },
};


// ── Students (universal registry) ─────────────────────────────────

const studentsApi = {
  async create(data) {
    return apiRequest('/students/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async bulkCreate(data) {
    return apiRequest('/students/bulk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async list(search = '') {
    return apiRequest(`/students/${search ? `?search=${encodeURIComponent(search)}` : ''}`);
  },
  async get(studentId) {
    return apiRequest(`/students/${studentId}`);
  },
  async update(studentId, data) {
    return apiRequest(`/students/${studentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  async deactivate(studentId) {
    return apiRequest(`/students/${studentId}`, { method: 'DELETE' });
  },
  async hardDelete(studentId) {
    return apiRequest(`/students/${studentId}/hard-delete`, { method: 'DELETE' });
  },
  async classes(studentId) {
    return apiRequest(`/students/${studentId}/classes`);
  },
  async enroll(classId, studentId) {
    return apiRequest(`/admin/classes/${classId}/enroll`, {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId }),
    });
  },
  async enrollBulk(classId, studentIds) {
    return apiRequest(`/admin/classes/${classId}/enroll-bulk`, {
      method: 'POST',
      body: JSON.stringify({ student_ids: studentIds }),
    });
  },
  async unenroll(classId, studentId) {
    return apiRequest(`/admin/classes/${classId}/unenroll/${studentId}`, { method: 'DELETE' });
  },
  async listClassStudents(classId) {
    return apiRequest(`/admin/students/class/${classId}`);
  },
  async studentParticipation(studentId) {
    return apiRequest(`/admin/students/${studentId}/participation`);
  },
  async importCsv(file, classSessionId = null) {
    const form = new FormData();
    form.append('file', file);
    if (classSessionId) form.append('class_session_id', classSessionId);
    const headers = CSRF;
    const res = await fetch(`${API_BASE}/students/import`, { method: 'POST', headers, body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Import failed');
    }
    return res.json();
  },
};


// ── Classes ─────────────────────────────────────────────────────

const classesApi = {
  async exceptions(classId) { return apiRequest(`/classes/${classId}/exceptions`); },          // #126
  async addException(classId, body) {
    return apiRequest(`/classes/${classId}/exceptions`, { method: 'POST', body: JSON.stringify(body) });
  },
  async removeException(classId, id) { return apiRequest(`/classes/${classId}/exceptions/${id}`, { method: 'DELETE' }); },
  async list() {
    return apiRequest('/classes/');
  },
  async create(data) {
    return apiRequest('/classes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async get(classId) {
    return apiRequest(`/classes/${classId}`);
  },
  async activate(classId) {
    return apiRequest(`/classes/${classId}/activate`, { method: 'POST' });
  },
  async deactivate(classId) {
    return apiRequest(`/classes/${classId}/deactivate`, { method: 'POST' });
  },
  async join(code) {
    return apiRequest('/classes/join', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  },
  async delete(classId) {
    return apiRequest(`/classes/${classId}`, { method: 'DELETE' });
  },
};

// ── Quizzes ─────────────────────────────────────────────────────

// ── System, database integrity, debug (test) mode (v2.2) ─────────

const systemApi = {
  status() { return apiRequest('/system/status'); },
  integrity() { return apiRequest('/admin/system/integrity'); },
  verify() { return apiRequest('/admin/system/integrity/verify', { method: 'POST' }); },
  acknowledge(acceptCurrent = false, approvalId = null) {
    return apiRequest('/admin/system/integrity/acknowledge', { method: 'POST', body: JSON.stringify({ accept_current: acceptCurrent, approval_id: approvalId }) });
  },
  clearOptions() { return apiRequest('/admin/system/clear'); },
  clear(scope, confirm, approvalId) {
    return apiRequest('/admin/system/clear', { method: 'POST', body: JSON.stringify({ scope, confirm, approval_id: approvalId }) });
  },
  policy() { return apiRequest('/admin/system/policy'); },
};

// Two-step verification for super admins (v2.2, #211)
const mfaApi = {
  status() { return apiRequest('/auth/mfa'); },
  setup(password) { return apiRequest('/auth/mfa/setup', { method: 'POST', body: JSON.stringify({ password }) }); },
  enable(code) { return apiRequest('/auth/mfa/enable', { method: 'POST', body: JSON.stringify({ code }) }); },
  disable(password, code) { return apiRequest('/auth/mfa/disable', { method: 'POST', body: JSON.stringify({ password, code }) }); },
  recovery(password, code) { return apiRequest('/auth/mfa/recovery-codes', { method: 'POST', body: JSON.stringify({ password, code }) }); },
};

// Dual control: a second super admin approves dangerous actions (v2.2)
const approvalsApi = {
  list() { return apiRequest('/admin/approvals'); },
  request(action, password, code = '') { return apiRequest('/admin/approvals', { method: 'POST', body: JSON.stringify({ action, params: {}, password, code }) }); },
  approve(id, password, code = '') { return apiRequest(`/admin/approvals/${id}/approve`, { method: 'POST', body: JSON.stringify({ password, code }) }); },
  deny(id) { return apiRequest(`/admin/approvals/${id}/deny`, { method: 'POST' }); },
};

const testModeApi = {
  state() { return apiRequest('/admin/test-mode'); },
  enable(dataset = null) { return apiRequest('/admin/test-mode/enable', { method: 'POST', body: JSON.stringify({ dataset }) }); },
  disable() { return apiRequest('/admin/test-mode/disable', { method: 'POST' }); },
  decide(id, action, name = '') {
    return apiRequest(`/admin/test-mode/pending/${encodeURIComponent(id)}`, { method: 'POST', body: JSON.stringify({ action, name }) });
  },
  async download(kind, id) {
    const res = await fetch(`${API_BASE}/admin/test-mode/${kind}/${encodeURIComponent(id)}/export.zip`, { headers: CSRF });
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    const url = URL.createObjectURL(await res.blob());
    const a = Object.assign(document.createElement('a'), { href: url, download: `impress-test-data-${id}.zip` });
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  },
  deleteDataset(name) { return apiRequest(`/admin/test-mode/datasets/${encodeURIComponent(name)}`, { method: 'DELETE' }); },
  schema() { return apiRequest('/admin/test-data/schema'); },
  generate(seed, counts) { return apiRequest('/admin/test-data/generate', { method: 'POST', body: JSON.stringify({ seed, counts }) }); },
  validate(sheets) { return apiRequest('/admin/test-data/validate', { method: 'POST', body: JSON.stringify({ sheets }) }); },
  async import(sheets, simulate, seed) {
    return apiRequest('/admin/test-data/import', { method: 'POST', body: JSON.stringify({ sheets, simulate_activity: simulate, seed }) });
  },
};

const quizzesApi = {
  overview() { return apiRequest('/quizzes/overview'); },
  templateUrl: `${API_BASE}/quizzes/questions/template.csv`,

  /** Validate a question CSV; returns a per-row report, stores nothing. */
  parseCsv(file, onProgress) {
    return uploadFile('/quizzes/questions/parse', file, onProgress);
  },

  async create(data) {
    return apiRequest('/quizzes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async list(classId) {
    return apiRequest(`/quizzes/class/${classId}`);
  },
  async get(quizId) {
    return apiRequest(`/quizzes/${quizId}`);
  },
  async start(quizId) {
    return apiRequest(`/quizzes/${quizId}/start`, { method: 'POST' });
  },
  async stop(quizId) {
    return apiRequest(`/quizzes/${quizId}/stop`, { method: 'POST' });
  },
  async nextQuestion(quizId) {
    return apiRequest(`/quizzes/${quizId}/next`, { method: 'POST' });
  },
  async results(quizId) {
    return apiRequest(`/quizzes/${quizId}/results`);
  },
};

// ── Polls ───────────────────────────────────────────────────────

const pollsApi = {
  async create(data) {
    return apiRequest('/polls/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async list(classId) {
    return apiRequest(`/polls/class/${classId}`);
  },
  async get(pollId) {
    return apiRequest(`/polls/${pollId}`);
  },
  async start(pollId) {
    return apiRequest(`/polls/${pollId}/start`, { method: 'POST' });
  },
  async end(pollId) {
    return apiRequest(`/polls/${pollId}/end`, { method: 'POST' });
  },
  async results(pollId) {
    return apiRequest(`/polls/${pollId}/results`);
  },
};

// ── WebSocket ───────────────────────────────────────────────────

class ClassSocket {
  constructor() {
    this.ws = null;
    this.classId = null;
    this.listeners = {};
    this.reconnectDelay = 1000;
    this.maxReconnect = 30000;
  }

  connect(classId) {
    this.disconnect();
    this.classId = classId;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // The session cookie authenticates the socket; no token in the URL.
    const url = `${protocol}//${window.location.host}/ws/class/${classId}?role=teacher`;

    try {
      this.ws = new WebSocket(url);
    } catch (e) {
      this._emit('error', { message: 'WebSocket connection failed' });
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this._emit('connected', {});
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this._emit(data.type || 'message', data);
      } catch (e) {
        this._emit('message', { raw: event.data });
      }
    };

    this.ws.onclose = (ev) => {
      this._emit('disconnected', { code: ev.code });
      // The server closed it on purpose (#160): retrying would fail forever.
      if (ev.code === 4401) {                      // session revoked or expired (#118)
        this.classId = null;
        const leave = () => {
          clearToken();
          if (typeof showToast === 'function') showToast('Your session ended. Please log in again.', 'error');
          window.location.hash = '#/login';
        };
        // ask why: a disabled account or a restart gets its notice, not just the sign-in page
        fetch(`${API_BASE}/auth/me`, { headers: CSRF }).then((r) => {
          const why = r.headers.get('X-Session-Code');
          if (typeof Overlays !== 'undefined' && (why === 'disabled' || why === 'restart')) Overlays.sessionEnded(why); else leave();
        }).catch(leave);
        return;
      }
      if (ev.code === 4403 || ev.code === 4404) {  // no access to this class, or HTTPS required (#121, #152)
        this.classId = null;
        this._emit('forbidden', { code: ev.code, reason: ev.reason });
        return;
      }
      this._scheduleReconnect();                   // network trouble, server restart: try again
    };

    this.ws.onerror = () => {
      this._emit('error', { message: 'WebSocket error' });
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
    this.classId = null;
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
    return () => {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    };
  }

  _emit(event, data) {
    (this.listeners[event] || []).forEach(cb => cb(data));
  }

  _scheduleReconnect() {
    if (!this.classId) return;
    setTimeout(() => {
      if (this.classId) this.connect(this.classId);
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnect);
  }
}

const classSocket = new ClassSocket();
