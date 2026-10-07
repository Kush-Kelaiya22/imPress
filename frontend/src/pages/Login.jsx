import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client.js'
import { useAuth } from '../auth.jsx'

export default function Login() {
  const [mode, setMode] = useState('login')  // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { login, token } = useAuth()
  const navigate = useNavigate()
  const [checking, setChecking] = useState(false)

  // If a session token exists, verify it against the backend and continue to
  // the home page when it's still active — a normal "already logged in"
  // bounce. /auth/session-status is lightweight (no idle refresh).
  useEffect(() => {
    if (!token) return
    let cancelled = false
    setChecking(true)
    authApi
      .sessionStatus()
      .then(() => {
        if (!cancelled) navigate('/', { replace: true })
      })
      .catch(() => {})  // 401 → interceptor clears the token; network error → stay
      .finally(() => {
        if (!cancelled) setChecking(false)
      })
    return () => {
      cancelled = true
    }
  }, [token, navigate])

  if (checking && token) {
    return (
      <div className="login-page">
        <div className="login-card">
          <p className="login-hint">Checking session…</p>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (mode === 'login') {
        const res = await authApi.login(username, password)
        // Fetch user details
        const token = res.data.access_token
        localStorage.setItem('token', token)
        const me = await authApi.me()
        login(token, me.data)
        navigate('/')
      } else {
        await authApi.register({
          username,
          email,
          password,
          full_name: fullName,
          role: 'teacher',
        })
        // Auto-login after registration
        const res = await authApi.login(username, password)
        const token = res.data.access_token
        const me = await authApi.me()
        login(token, me.data)
        navigate('/')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">⚡ imPress</div>
        <div className="login-subtitle">
          Class Participation System
        </div>

        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          {mode === 'register' && (
            <>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  className="form-control"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  className="form-control"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              className="form-control"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          <button
            className="btn btn-primary"
            style={{ width: '100%' }}
            type="submit"
            disabled={loading}
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>

        <div style={{ marginTop: 16, textAlign: 'center', fontSize: '0.85rem' }}>
          {mode === 'login' ? (
            <a
              href="#"
              style={{ color: 'var(--primary)', textDecoration: 'none' }}
              onClick={(e) => { e.preventDefault(); setMode('register') }}
            >
              Need an account? Register
            </a>
          ) : (
            <a
              href="#"
              style={{ color: 'var(--primary)', textDecoration: 'none' }}
              onClick={(e) => { e.preventDefault(); setMode('login') }}
            >
              Already have an account? Login
            </a>
          )}
        </div>
      </div>
    </div>
  )
}