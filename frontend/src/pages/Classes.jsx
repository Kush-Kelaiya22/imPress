import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { classesApi } from '../api/client.js'

export default function Classes() {
  const [classes, setClasses] = useState([])
  const [newClassName, setNewClassName] = useState('')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState('')

  useEffect(() => {
    loadClasses()
  }, [])

  const loadClasses = async () => {
    try {
      const res = await classesApi.list()
      setClasses(res.data)
    } catch (err) {
      console.error('Failed to load classes:', err)
    } finally {
      setLoading(false)
    }
  }

  const createClass = async (e) => {
    e.preventDefault()
    if (!newClassName.trim()) return

    try {
      const res = await classesApi.create(newClassName.trim())
      showToast(`Class created with code: ${res.data.code}`)
      setNewClassName('')
      loadClasses()
    } catch (err) {
      console.error('Failed to create class:', err)
    }
  }

  const showToast = (text) => {
    setToast(text)
    setTimeout(() => setToast(''), 4000)
  }

  return (
    <div>
      {toast && <div className="toast">{toast}</div>}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Classes</h1>

        <form onSubmit={createClass} style={{ display: 'flex', gap: 8 }}>
          <input
            className="form-control"
            placeholder="New class name..."
            value={newClassName}
            onChange={(e) => setNewClassName(e.target.value)}
            style={{ width: 220 }}
          />
          <button className="btn btn-primary" type="submit">
            + Create Class
          </button>
        </form>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
      ) : classes.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '60px' }}>
          <h2 style={{ marginBottom: 12 }}>No classes yet</h2>
          <p>Create your first class to start collecting participation data.</p>
        </div>
      ) : (
        <div className="grid grid-3">
          {classes.map((cls) => (
            <div key={cls.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
                <div>
                  <h3 style={{ marginBottom: 4 }}>{cls.name}</h3>
                  <span className="badge badge-info">{cls.code}</span>
                </div>
                {cls.is_active ? (
                  <span className="badge badge-online">● LIVE</span>
                ) : (
                  <span className="badge badge-offline">Inactive</span>
                )}
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                {cls.student_count} students enrolled
                <br />
                Created {new Date(cls.created_at).toLocaleDateString()}
              </div>

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Link to={`/classes/${cls.id}/quiz`} className="btn btn-outline btn-sm">
                  📝 Quiz
                </Link>
                <Link to={`/classes/${cls.id}/poll`} className="btn btn-outline btn-sm">
                  📊 Poll
                </Link>
                <Link to={`/classes/${cls.id}/devices`} className="btn btn-outline btn-sm">
                  🌳 Device Tree
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}