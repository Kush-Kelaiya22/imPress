/**
 * WebSocket client for class sessions.
 * Connects to /ws/class/{classId} and dispatches events.
 */

const WS_BASE = 'ws://localhost:8000/ws/class/'

class ClassSocket {
  constructor() {
    this.ws = null
    this.classId = null
    this.handlers = {}  // event → [callbacks]
    this.reconnectAttempts = 0
    this.manuallyClosed = false
  }

  connect(classId, role = 'teacher') {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Already connected — just update class if different
      if (this.classId !== classId) {
        this.close()
      } else {
        return
      }
    }

    this.classId = classId
    this.manuallyClosed = false

    const url = `${WS_BASE}${classId}?role=${role}`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log(`[WS] Connected to class ${classId}`)
      this.reconnectAttempts = 0
      this.emit('connected', { classId })
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emit(data.event, data)
      } catch (e) {
        console.error('[WS] Failed to parse message:', event.data)
      }
    }

    this.ws.onclose = () => {
      console.log(`[WS] Disconnected from class ${this.classId}`)
      this.emit('disconnected', { classId: this.classId })

      // Auto-reconnect with backoff (5s, then 10s, max 30s)
      if (!this.manuallyClosed) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }

  scheduleReconnect() {
    this.reconnectAttempts++
    const delay = Math.min(5000 * Math.pow(2, this.reconnectAttempts - 1), 30000)
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    setTimeout(() => {
      if (!this.manuallyClosed && this.classId) {
        this.connect(this.classId)
      }
    }, delay)
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  // Register an event handler
  on(event, callback) {
    if (!this.handlers[event]) {
      this.handlers[event] = []
    }
    this.handlers[event].push(callback)
  }

  // Remove an event handler
  off(event, callback) {
    if (!this.handlers[event]) return
    this.handlers[event] = this.handlers[event].filter((cb) => cb !== callback)
  }

  emit(event, data) {
    const callbacks = this.handlers[event]
    if (callbacks) {
      callbacks.forEach((cb) => {
        try {
          cb(data)
        } catch (e) {
          console.error(`[WS] Handler error for "${event}":`, e)
        }
      })
    }
  }

  close() {
    this.manuallyClosed = true
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

// Singleton
export const classSocket = new ClassSocket()

// Helper hook
export const WS_EVENTS = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  QUIZ_QUESTION: 'quiz_question',
  QUIZ_END: 'quiz_end',
  POLL_START: 'poll_start',
  POLL_END: 'poll_end',
  ANSWER_RECEIVED: 'answer_received',
  POLL_VOTE_RECEIVED: 'poll_vote_received',
  STUDENT_DATA: 'student_data',
  DEVICE_STATUS: 'device_status',
}