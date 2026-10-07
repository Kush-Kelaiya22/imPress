import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client.js'
import { useAuth } from '../auth.jsx'

// How often the authoritative /auth/session-status poll runs.
const POLL_INTERVAL_MS = 15000

function fmtClock(totalSec) {
  const s = Math.max(0, Math.floor(totalSec))
  const m = Math.floor(s / 60)
  return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

function fmtTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleTimeString()
}

/**
 * Session persistence guard — mount inside authenticated routes.
 *
 * - Polls /api/auth/session-status (light, does NOT refresh the idle timer).
 * - Shows a warning banner during the final 5 minutes before the 6-hour hard
 *   limit with a live countdown and timestamps.
 * - Auto-logs out when the hard limit is reached. Idle expiration surfaces as
 *   a 401 from the backend, which the axios interceptor turns into a logout.
 */
export default function SessionGuard() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [status, setStatus] = useState(null)
  const [left, setLeft] = useState({ idle: 0, hard: 0 })
  const expiredRef = useRef(false)

  // Authoritative poll (re-syncs remaining seconds with the server).
  useEffect(() => {
    let cancelled = false
    let timer = null

    const poll = async () => {
      try {
        const res = await authApi.sessionStatus()
        if (cancelled) return
        setStatus(res.data)
        setLeft({
          idle: res.data.idle_seconds_remaining,
          hard: res.data.hard_seconds_remaining,
        })
      } catch (err) {
        // 401 means the backend already expired this session (idle or hard).
        // The axios interceptor clears storage and redirects to /login, so stop polling.
        if (!cancelled && err.response?.status === 401) {
          if (timer) clearInterval(timer)
        }
      }
    }

    poll()
    timer = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      if (timer) clearInterval(timer)
    }
  }, [])

  // Smooth live countdown between polls.
  useEffect(() => {
    const tick = setInterval(() => {
      setLeft((prev) => ({
        idle: Math.max(0, prev.idle - 1),
        hard: Math.max(0, prev.hard - 1),
      }))
    }, 1000)
    return () => clearInterval(tick)
  }, [])

  // Auto-logout on hard limit. Idle expiry is enforced by the server (401).
  useEffect(() => {
    if (status && left.hard === 0 && !expiredRef.current) {
      expiredRef.current = true
      logout()
      navigate('/login', { replace: true })
    }
  }, [status, left.hard, logout, navigate])

  if (!status) return null

  const warningActive = status.warning_active && left.hard > 0
  const danger = warningActive && left.hard <= 60

  if (!warningActive) return null

  return (
    <div className={`session-warning${danger ? ' session-warning-danger' : ''}`}>
      <strong>⚠️ Session ending soon.</strong>{' '}
      Hard limit in <b>{fmtClock(left.hard)}</b> — auto-logout at{' '}
      <b>{fmtTime(status.expires_at)}</b>. Idle auto-logout in{' '}
      {fmtClock(left.idle)} (last activity {fmtTime(status.last_activity_at)}).{' '}
      Save your work.
    </div>
  )
}