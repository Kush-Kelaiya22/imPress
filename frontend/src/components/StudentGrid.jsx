import React from 'react'

/**
 * Live grid of student presence status.
 * @param students  Object: device_id → { name, student_id, status, lastSeen }
 */
export default function StudentGrid({ students }) {
  const entries = Object.entries(students).sort((a, b) => {
    return (a[1].student_id || 0) - (b[1].student_id || 0)
  })

  if (entries.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '8px 0' }}>
        No students connected yet. Waiting for ESP32 devices...
      </div>
    )
  }

  const statusClass = (student) => {
    if (student.status === 'answered') return 'student-chip answered'
    if (student.status === 'present') return 'student-chip present'
    return 'student-chip'
  }

  return (
    <div className="student-grid">
      {entries.map(([deviceId, student]) => (
        <div
          key={deviceId}
          className={statusClass(student)}
          title={`Device: ${deviceId} — last seen ${student.lastSeen ? new Date(student.lastSeen).toLocaleTimeString() : 'unknown'}`}
        >
          <div className="student-name">{student.name || `Student ${student.student_id || '?'}`}</div>
          <div className="student-id">
            #{student.student_id || '—'} {student.status && `· ${student.status}`}
          </div>
        </div>
      ))}
    </div>
  )
}