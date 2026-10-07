import React from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          ⚡ imPress
        </Link>

        <div className="navbar-links">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/classes" end>
            Classes
          </NavLink>

          <div className="user-badge">
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {user?.full_name || user?.username}
            </span>
            <button
              className="btn btn-outline btn-sm"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}