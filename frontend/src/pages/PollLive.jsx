import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { pollsApi } from '../api/client.js'
import { classSocket } from '../api/websocket.js'

export default function PollLive() {
  const { classId } = useParams()
  const [title, setTitle] = useState('')
  const [options, setOptions] = useState(['', ''])
  const [activePoll, setActivePoll] = useState(null)
  const [voteCounts, setVoteCounts] = useState([])
  const [polls, setPolls] = useState([])
  const [view, setView] = useState('editor')  // 'editor' | 'live' | 'results'
  const [toast, setToast] = useState('')

  useEffect(() => {
    loadPolls()
    classSocket.on('poll_start', handlePollStart)
    classSocket.on('poll_vote_received', handleVote)
    classSocket.on('poll_end', handlePollEnd)
    return () => {
      classSocket.off('poll_start', handlePollStart)
      classSocket.off('poll_vote_received', handleVote)
      classSocket.off('poll_end', handlePollEnd)
    }
  }, [])

  const showToast = (text) => {
    setToast(text)
    setTimeout(() => setToast(''), 4000)
  }

  const loadPolls = async () => {
    try {
      const res = await pollsApi.list(Number(classId))
      setPolls(res.data)
    } catch (err) {
      console.error('Failed to load polls:', err)
    }
  }

  const handlePollStart = (data) => {
    setActivePoll(data)
    setVoteCounts(new Array((data.options || []).length).fill(0))
    setView('live')
  }

  const handleVote = (data) => {
    if (data.poll_id !== activePoll?.poll_id) return
    setVoteCounts((prev) => {
      const next = [...prev]
      next[data.selected_option] = (next[data.selected_option] || 0) + 1
      return next
    })
  }

  const handlePollEnd = (data) => {
    if (data.poll_id !== activePoll?.poll_id) return
    if (data.vote_counts) setVoteCounts(data.vote_counts)
    showToast('Poll closed! Results below.')
    setView('results')
    setActivePoll(null)
    loadPolls()
  }

  const addOption = () => {
    if (options.length >= 4) {
      showToast('Maximum 4 options (student modules have 4 buttons)')
      return
    }
    setOptions((prev) => [...prev, ''])
  }

  const updateOption = (i, value) => {
    setOptions((prev) => prev.map((o, oi) => (oi === i ? value : o)))
  }

  const createPoll = async () => {
    if (!title.trim()) {
      showToast('Please enter a poll title')
      return
    }
    const validOptions = options.filter((o) => o.trim())
    if (validOptions.length < 2) {
      showToast('Add at least 2 options')
      return
    }

    try {
      const res = await pollsApi.create({
        title,
        class_session_id: Number(classId),
        options: validOptions,
      })
      setActivePoll({
        poll_id: res.data.id,
        title: res.data.title,
        options: res.data.options,
      })
      setVoteCounts(new Array(validOptions.length).fill(0))
      setView('live')
      loadPolls()
    } catch (err) {
      showToast('Failed to create poll')
    }
  }

  const startPoll = async () => {
    if (!activePoll) return
    await pollsApi.start(activePoll.poll_id)
    showToast('Poll started! Students can now vote.')
  }

  const endPoll = async () => {
    if (!activePoll) return
    await pollsApi.end(activePoll.poll_id)
  }

  // ── Editor ──
  if (view === 'editor') {
    return (
      <div>
        {toast && <div className="toast">{toast}</div>}
        <div style={{ marginBottom: 24 }}>
          <Link to="/classes" className="btn btn-outline btn-sm">← Back</Link>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h1>Create Poll</h1>
          <button className="btn btn-primary" onClick={createPoll}>
            Create Poll
          </button>
        </div>

        <div className="card" style={{ maxWidth: 600, marginBottom: 24 }}>
          <div className="form-group">
            <label>Poll Question</label>
            <input
              className="form-control"
              placeholder="e.g. Which topic should we review?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Options</label>
            {options.map((opt, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <span
                  style={{
                    width: 28,
                    height: 28,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 6,
                    background: '#eef2ff',
                    color: 'var(--primary)',
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    flexShrink: 0,
                    alignSelf: 'center',
                  }}
                >
                  {i + 1}
                </span>
                <input
                  className="form-control"
                  placeholder={`Option ${i + 1}`}
                  value={opt}
                  onChange={(e) => updateOption(i, e.target.value)}
                />
                {options.length > 2 && (
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => setOptions((prev) => prev.filter((_, oi) => oi !== i))}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          <button className="btn btn-outline btn-sm" onClick={addOption}>
            + Add Option
          </button>
        </div>

        {/* Past polls */}
        {polls.length > 0 && (
          <div>
            <h2 style={{ marginBottom: 16 }}>Recent Polls</h2>
            <div className="grid">
              {polls.slice(0, 5).map((poll) => (
                <div key={poll.id} className="card">
                  <h3 style={{ marginBottom: 8 }}>{poll.title}</h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 12 }}>
                    Status: <span className="badge badge-info">{poll.status}</span>
                  </div>
                  <button className="btn btn-success btn-sm" onClick={() => {
                    setActivePoll({ poll_id: poll.id, title: poll.title, options: poll.options })
                    setView('live')
                  }}>
                    ▶ Re-run
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── Live poll ──
  if (view === 'live') {
    const hasStarted = activePoll?.started
    return (
      <div>
        {toast && <div className="toast">{toast}</div>}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h1 style={{ marginBottom: 4 }}>{activePoll?.title}</h1>
            <span className="badge badge-active">LIVE POLL</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={startPoll} disabled={hasStarted}>
              ▶ {hasStarted ? 'Started' : 'Start Poll'}
            </button>
            <button className="btn btn-danger" onClick={endPoll}>
              ■ Close Poll
            </button>
          </div>
        </div>

        <div className="quiz-question">
          <h3 style={{ marginBottom: 24, textAlign: 'center', fontSize: '1.3rem' }}>
            {activePoll?.title}
          </h3>

          <div className="option-list">
            {(activePoll?.options || []).map((opt, i) => {
              const total = voteCounts.reduce((a, b) => a + b, 0)
              const count = voteCounts[i] || 0
              const pct = total > 0 ? Math.round((count / total) * 100) : 0

              return (
                <div key={i} className="option-item" style={{ position: 'relative', overflow: 'hidden' }}>
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      bottom: 0,
                      width: `${pct}%`,
                      background: 'rgba(79, 70, 229, 0.08)',
                      transition: 'width 0.3s ease',
                    }}
                  />
                  <span className="option-letter">{i + 1}</span>
                  {opt}
                  <span className="option-count">
                    {count} vote{count !== 1 ? 's' : ''} ({pct}%)
                  </span>
                </div>
              )
            })}
          </div>

          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {voteCounts.reduce((a, b) => a + b, 0)} total votes | Live results
          </div>
        </div>
      </div>
    )
  }

  // ── Results ──
  const total = voteCounts.reduce((a, b) => a + b, 0)
  const winner = total > 0 ? voteCounts.indexOf(Math.max(...voteCounts)) : -1

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Poll Results</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-outline btn-sm" onClick={() => setView('editor')}>
            Create New Poll
          </button>
          <Link to="/classes" className="btn btn-outline btn-sm">
            Back to Classes
          </Link>
        </div>
      </div>

      <div className="quiz-question">
        <h3 style={{ marginBottom: 24, textAlign: 'center' }}>{activePoll?.title || 'Poll Results'}</h3>

        <div className="option-list">
          {(activePoll?.options || []).map((opt, i) => {
            const count = voteCounts[i] || 0
            const pct = total > 0 ? Math.round((count / total) * 100) : 0
            const isWinner = i === winner

            return (
              <div
                key={i}
                className="option-item"
                style={{
                  borderColor: isWinner && total > 0 ? 'var(--success)' : 'var(--border)',
                }}
              >
                <span
                  className="option-letter"
                  style={{
                    background: isWinner && total > 0 ? 'var(--success)' : '#eef2ff',
                    color: isWinner && total > 0 ? 'white' : 'var(--primary)',
                  }}
                >
                  {i + 1}
                </span>
                {opt} {isWinner && total > 0 && ' 🏆'}
                <span className="option-count">
                  {count} ({pct}%)
                </span>
              </div>
            )
          })}
        </div>

        <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {total} total votes
        </div>
      </div>
    </div>
  )
}