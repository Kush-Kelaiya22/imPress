import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach auth token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ── Auth API ──

export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  sessionStatus: () => api.get('/auth/session-status'),
  activity: () => api.post('/auth/activity'),
}

// ── Classes API ──

export const classesApi = {
  list: () => api.get('/classes'),
  get: (id) => api.get(`/classes/${id}`),
  create: (name) => api.post('/classes', { name }),
  activate: (id) => api.post(`/classes/${id}/activate`),
  deactivate: (id) => api.post(`/classes/${id}/deactivate`),
  deviceTree: (id) => api.get(`/devices/tree?class_id=${id}`),
}

// ── Device Tree API ──

export const deviceTreeApi = {
  get: (classId) => api.get(`/devices/tree?class_id=${classId}`),
}

// ── Quizzes API ──

export const quizzesApi = {
  create: (data) => api.post('/quizzes', data),
  list: (classId) => api.get(`/quizzes/class/${classId}`),
  start: (id) => api.post(`/quizzes/${id}/start`),
  next: (id) => api.post(`/quizzes/${id}/next`),
  stop: (id) => api.post(`/quizzes/${id}/stop`),
  results: (id) => api.get(`/quizzes/${id}/results`),
}

// ── Polls API ──

export const pollsApi = {
  create: (data) => api.post('/polls', data),
  list: (classId) => api.get(`/polls/class/${classId}`),
  start: (id) => api.post(`/polls/${id}/start`),
  end: (id) => api.post(`/polls/${id}/end`),
}

export default api