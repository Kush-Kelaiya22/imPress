import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { classesApi } from '../api/client.js'
import { useAuth } from '../auth.jsx'
import { classSocket } from '../api/websocket.js'
import StudentGrid from '../components/StudentGrid.jsx'

export default function Dashboard() {
  const { user } = useAuth()
  const [classes, setClasses] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeClass, setActiveClass] = useState(null)
  const [students, setStudents] = useState({})  // device_id → status
  const [liveEvents, setLiveEvents] = useState([])

  useEffect(() => {
    loadClasses()
  }, [])

  useEffect(() => {
    // Connect to active class WebSocket
    if (activeClass) {
      classSocket.connect(activeClass.id, 'teacher')

      classSocket.on('student_data', handleStudentData)
      classSocket.on('quiz_question', handleQuizQuestion)
      classSocket.on('poll_start', handlePollStart)
      classSocket.on('poll_vote_received', handlePollVote)
      classSocket.on('answer_received', handleAnswer)

      return () => {
        classSocket.off('student_data', handleStudentData)
        classSocket.off('quiz_question', handleQuizQuestion)
        classSocket.off('poll_start', handlePollStart)
        classSocket.off('poll_vote_received', handlePollVote)
        classSocket.off('answer_received', handleAnswer)
      }
    }
  }, [activeClass])

  const loadClasses = async () => {
    try {
      const res = await classesApi.list()
      setClasses(res.data)
      const active = res.data.find((c) => c.is_active)
      if (active) setActiveClass(active)
    } catch (err) {
      console.error('Failed to load classes:', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleClass = async (cls) => {
    if (cls.is_active) {
      await classesApi.deactivate(cls.id)
      setActiveClass(null)
    } else {
      await classesApi.activate(cls.id)
      setActiveClass(cls)
    }
    loadClasses()
  }

  const handleStudentData = (data) => {
    const { device_id, status } = data.data || {}
    if (device_id) {
      setStudents((prev) => ({
        ...prev,
        [device_id]: { ...prev[device_id], ...status, lastSeen: Date.now() },
      }))
    }
  }

  const handleQuizQuestion = (data) => {
    addLiveEvent(`📝 Quiz Q${data.question_num + 1}: ${data.question_text}`)
  }

  const handlePollStart = (data) => {
    addLiveEvent(`📊 Poll started: ${data.title}`)
  }

  const handlePollVote = (data) => {
    addLiveEvent(`🗳️ Vote received (${data.total_votes} total)`)
  }

  const handleAnswer = (data) => {
    addLiveEvent(`✅ Answer received (${data.total_answers} total)`)
  }

  const addLiveEvent = (text) => {
    setLiveEvents((prev) => [
      { id: Date.now(), text, time: new Date().toLocaleTimeString() },
      ...prev,
    ].slice(0, 10))
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Welcome, {user?.full_name || user?.username}! 👋</h1>

      {/* ── Stats overview ── */}
      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="stat-tile">
          <div className="stat-value">{classes.length}</div>
          <div className="stat-label">Total Classes</div>
        </div>
        <div className="stat-tile">
          <div className="stat-value">{classes.filter((c) => c.is_active).length}</div>
          <div className="stat-label">Active Now</div>
        </div>
        <div className="stat-tile">
          <div className="stat-value">
            {activeClass ? (
              <span className="badge badge-active">{activeClass.code}</span>
            ) : (
              '—'
            )}
          </div>
          <div className="stat-label">Active Join Code</div>
        </div>
      </div>

      <div className="grid grid-2">
        {/* ── Classes list ── */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <h2>My Classes</h2>
            <Link to="/classes" className="btn btn-outline btn-sm">
              Manage Classes
            </Link>
          </div>

          {classes.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
              No classes yet. Create one to get started.
            </div>
          ) : (
            <div className="grid" style={{ gridTemplateColumns: '1fr' }}>
              {classes.map((cls) => (
                <div key={cls.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{cls.name}</strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Code: <span className="badge badge-info">{cls.code}</span>
                      {' · '}{cls.student_count} students
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {cls.is_active && <span className="badge badge-online">● LIVE</span>}
                    <button
                      className={`btn btn-sm ${cls.is_active ? 'btn-danger' : 'btn-success'}`}
                      onClick={() => toggleClass(cls)}
                    >
                      {cls.is_active ? 'End' : 'Start'}
                    </button>
                    {cls.is_active && (
                      <>
                        <Link to={`/classes/${cls.id}/quiz`} className="btn btn-primary btn-sm">
                          Quiz
                        </Link>
                        <Link to={`/classes/${cls.id}/poll`} className="btn btn-outline btn-sm">
                          Poll
                        </Link>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Live class panel ── */}
        <div>
          <h2 style={{ marginBottom: 16 }}>
            Live Class{' '}
            {activeClass && <span className="badge badge-online">● CONNECTED</span>}
          </h2>

          {!activeClass ? (
            <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
              Start a class to see live participation
            </div>
          ) : (
            <>
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title">
                  {activeClass.name}{' '}
                  <span className="badge badge-info">{activeClass.code}</span>
                </div>
                <StudentGrid students={students} />
              </div>

              {/* Live activity feed */}
              <div className="card">
                <div className="card-title">Activity Feed</div>
                {liveEvents.length === 0 ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Waiting for student activity...
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: 8 }}>
                    {liveEvents.map((event) => (
                      <div
                        key={event.id}
                        style={{
                          padding: '8px 12px',
                          background: 'var(--bg)',
                          borderRadius: 8,
                          fontSize: '0.85rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span>{event.text}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                          {event.time}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}