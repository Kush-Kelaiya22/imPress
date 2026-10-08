/* imPress — API client (REST + WebSocket) */

const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('impress_token');
}

function setToken(token) {
  localStorage.setItem('impress_token', token);
}

function clearToken() {
  localStorage.removeItem('impress_token');
}

function isLoggedIn() {
  return !!getToken();
}

async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.hash = '#/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
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
    const token = getToken();
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
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
    setToken(res.access_token);
    return res;
  },
  async me() {
    return apiRequest('/auth/me');
  },
  async updateProfile(fullName) {
    return apiRequest('/auth/me', {
      method: 'PUT',
      body: JSON.stringify({ full_name: fullName }),
    });
  },
  async changePassword(currentPassword, newPassword) {
    return apiRequest('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  },
  logout() {
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
      headers: { Authorization: `Bearer ${getToken()}` },
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
  async updateUser(userId, data) {
    return apiRequest(`/admin/users/${userId}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  async deactivateUser(userId) {
    return apiRequest(`/admin/users/${userId}/deactivate`, { method: 'POST' });
  },
  async deleteUser(userId) {
    return apiRequest(`/admin/users/${userId}`, { method: 'DELETE' });
  },
  async resetPassword(userId, newPassword) {
    return apiRequest(`/admin/users/${userId}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    });
  },
  async importUsersCsv(file) {
    const form = new FormData();
    form.append('file', file);
    const token = getToken();
    const headers = { Authorization: `Bearer ${token}` };
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
    const token = getToken();
    const headers = { Authorization: `Bearer ${token}` };
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

const modulesApi = {
  async list(deviceType = '') {
    return apiRequest(`/admin/modules${deviceType ? `?device_type=${deviceType}` : ''}`);
  },
  async get(deviceId) {
    return apiRequest(`/admin/modules/${deviceId}`);
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
    const token = getToken();
    const headers = { Authorization: `Bearer ${token}` };
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

const quizzesApi = {
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
    const token = encodeURIComponent(getToken() || '');
    const url = `${protocol}//${window.location.host}/ws/class/${classId}?role=teacher&token=${token}`;

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

    this.ws.onclose = () => {
      this._emit('disconnected', {});
      this._scheduleReconnect();
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
