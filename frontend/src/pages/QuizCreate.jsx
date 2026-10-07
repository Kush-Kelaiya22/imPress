import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { quizzesApi } from '../api/client.js'
import { classSocket } from '../api/websocket.js'

export default function QuizCreate() {
  const { classId } = useParams()
  const [title, setTitle] = useState('')
  const [questions, setQuestions] = useState([
    { question_text: '', options: ['', '', '', ''], correct_option: 0, time_limit_s: 30 },
  ])
  const [quizTitle, setQuizTitle] = useState('')
  const [quiz, setQuiz] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [results, setResults] = useState([])
  const [view, setView] = useState('editor')  // 'editor' | 'live' | 'results'
  const [toast, setToast] = useState('')

  // Listen for live quiz events
  useEffect(() => {
    classSocket.on('quiz_question', handleQuestion)
    classSocket.on('answer_received', handleAnswer)
    classSocket.on('quiz_end', handleQuizEnd)
    return () => {
      classSocket.off('quiz_question', handleQuestion)
      classSocket.off('answer_received', handleAnswer)
      classSocket.off('quiz_end', handleQuizEnd)
    }
  }, [])

  const showToast = (text) => {
    setToast(text)
    setTimeout(() => setToast(''), 4000)
  }

  const handleQuestion = (data) => {
    if (data.quiz_id !== quiz?.id) return
    setCurrentQuestion(data)
    setResults((prev) => [...prev].map((r) => r))  // reset answer counts
  }

  const handleAnswer = (data) => {
    if (data.quiz_id !== quiz?.id) return
    setCurrentQuestion((prev) => ({
      ...prev,
      total_answers: data.total_answers,
    }))
  }

  const handleQuizEnd = (data) => {
    if (data.quiz_id !== quiz?.id) return
    showToast('Quiz ended!')
    setView('results')
    loadResults()
  }

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      { question_text: '', options: ['', '', '', ''], correct_option: 0, time_limit_s: 30 },
    ])
  }

  const updateQuestion = (qi, field, value) => {
    setQuestions((prev) =>
      prev.map((q, i) => (i === qi ? { ...q, [field]: value } : q))
    )
  }

  const updateOption = (qi, oi, value) => {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === qi
          ? { ...q, options: q.options.map((o, oi2) => (oi2 === oi ? value : o)) }
          : q
      )
    )
  }

  const removeQuestion = (qi) => {
    setQuestions((prev) => prev.filter((_, i) => i !== qi))
  }

  const createQuiz = async () => {
    if (!title.trim()) {
      showToast('Please enter a quiz title')
      return
    }

    const validQuestions = questions.filter((q) => q.question_text.trim())
    if (validQuestions.length === 0) {
      showToast('Add at least one question')
      return
    }

    try {
      const res = await quizzesApi.create({
        title,
        class_session_id: Number(classId),
        questions: validQuestions.map((q) => ({
          question_text: q.question_text,
          options: q.options.filter((o) => o.trim()),
          correct_option: q.correct_option,
          time_limit_s: q.time_limit_s,
        })),
      })
      setQuiz(res.data)
      setQuizTitle(title)
      showToast('Quiz created! Now start it to broadcast to students.')
      setView('live')
    } catch (err) {
      showToast('Failed to create quiz')
    }
  }

  const startQuiz = async () => {
    await quizzesApi.start(quiz.id)
    showToast('Quiz started!')
  }

  const nextQuestion = async () => {
    await quizzesApi.next(quiz.id)
  }

  const endQuiz = async () => {
    await quizzesApi.stop(quiz.id)
  }

  const loadResults = async () => {
    const res = await quizzesApi.results(quiz.id)
    setResults(res.data.results)
  }

  // ── Editor view ──
  if (view === 'editor') {
    return (
      <div>
        {toast && <div className="toast">{toast}</div>}
        <div style={{ marginBottom: 24 }}>
          <Link to="/classes" className="btn btn-outline btn-sm">← Back</Link>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h1>Create Quiz</h1>
          <button className="btn btn-primary" onClick={createQuiz}>
            Create Quiz
          </button>
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          <div className="form-group">
            <label>Quiz Title</label>
            <input
              className="form-control"
              placeholder="e.g. Chapter 3 Review"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
        </div>

        {questions.map((q, qi) => (
          <div key={qi} className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <strong>Question {qi + 1}</strong>
              {questions.length > 1 && (
                <button className="btn btn-danger btn-sm" onClick={() => removeQuestion(qi)}>
                  ✕ Remove
                </button>
              )}
            </div>

            <div className="form-group">
              <label>Question Text</label>
              <input
                className="form-control"
                placeholder="e.g. What is the capital of France?"
                value={q.question_text}
                onChange={(e) => updateQuestion(qi, 'question_text', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Options (A-D)</label>
              {q.options.map((opt, oi) => (
                <div key={oi} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <span
                    style={{
                      width: 28,
                      height: 28,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: 6,
                      background: q.correct_option === oi ? 'var(--success)' : '#eef2ff',
                      color: q.correct_option === oi ? 'white' : 'var(--primary)',
                      fontWeight: 700,
                      fontSize: '0.8rem',
                      flexShrink: 0,
                      alignSelf: 'center',
                    }}
                  >
                    {String.fromCharCode(65 + oi)}
                  </span>
                  <input
                    className="form-control"
                    placeholder={`Option ${String.fromCharCode(65 + oi)}`}
                    value={opt}
                    onChange={(e) => updateOption(qi, oi, e.target.value)}
                  />
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => updateQuestion(qi, 'correct_option', oi)}
                    title="Mark as correct answer"
                    style={{
                      background: q.correct_option === oi ? 'var(--success)' : '',
                      color: q.correct_option === oi ? 'white' : '',
                    }}
                  >
                    ✓
                  </button>
                </div>
              ))}
            </div>

            <div className="form-group" style={{ maxWidth: 200 }}>
              <label>Time Limit (seconds)</label>
              <input
                className="form-control"
                type="number"
                min={10}
                max={120}
                value={q.time_limit_s}
                onChange={(e) => updateQuestion(qi, 'time_limit_s', parseInt(e.target.value) || 30)}
              />
            </div>
          </div>
        ))}

        <button className="btn btn-outline" onClick={addQuestion}>
          + Add Question
        </button>
      </div>
    )
  }

  // ── Live view ──
  if (view === 'live') {
    return (
      <div>
        {toast && <div className="toast">{toast}</div>}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h1 style={{ marginBottom: 4 }}>{quiz?.title || 'Quiz'}</h1>
            <span className="badge badge-active" style={{ fontSize: '0.8rem' }}>
              LIVE — broadcasting to students
            </span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={startQuiz}>
              ▶ Start Quiz
            </button>
            <button className="btn btn-outline" onClick={nextQuestion}>
              Next Question
            </button>
            <button className="btn btn-danger" onClick={endQuiz}>
              ■ End Quiz
            </button>
          </div>
        </div>

        {currentQuestion ? (
          <div className="quiz-question">
            <h3>
              Question {currentQuestion.question_num + 1} of {currentQuestion.total_questions}
            </h3>
            <p style={{ fontSize: '1.1rem', marginBottom: 16, color: 'var(--text)' }}>
              {currentQuestion.question_text}
            </p>

            <div className="option-list">
              {(currentQuestion.options || []).map((opt, i) => (
                <div key={i} className="option-item">
                  <span className="option-letter">{String.fromCharCode(65 + i)}</span>
                  {opt}
                  {currentQuestion.total_answers > 0 && (
                    <span className="option-count">
                      {currentQuestion.option_counts?.[i] || 0}
                    </span>
                  )}
                </div>
              ))}
            </div>

            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Answers received: <strong>{currentQuestion.total_answers || 0}</strong>
            </div>
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            <p style={{ marginBottom: 16 }}>Quiz is ready but not yet broadcasting.</p>
            <button className="btn btn-primary" onClick={startQuiz}>
              ▶ Start Quiz Now
            </button>
          </div>
        )}
      </div>
    )
  }

  // ── Results view ──
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Quiz Results: {quiz?.title || quizTitle}</h1>
        <Link to="/classes" className="btn btn-outline btn-sm">
          Back to Classes
        </Link>
      </div>

      {results.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '60px' }}>
          No results available.
        </div>
      ) : (
        <div className="grid">
          {results.map((r, i) => (
            <div key={i} className="card quiz-question">
              <h3 style={{ marginBottom: 16 }}>
                Q{r.question_num + 1}: {r.question_text}
              </h3>

              <div className="option-list">
                {(r.options || []).map((opt, oi) => {
                  const isCorrect = oi === r.correct_option
                  const pct = r.total_answers > 0
                    ? Math.round(((r.option_counts[oi] || 0) / r.total_answers) * 100)
                    : 0
                  return (
                    <div
                      key={oi}
                      className="option-item"
                      style={{
                        borderColor: isCorrect ? 'var(--success)' : 'var(--border)',
                      }}
                    >
                      <span
                        className="option-letter"
                        style={{
                          background: isCorrect ? 'var(--success)' : '#eef2ff',
                          color: isCorrect ? 'white' : 'var(--primary)',
                        }}
                      >
                        {String.fromCharCode(65 + oi)}
                      </span>
                      {opt} {isCorrect && ' ✓'}
                      <span className="option-count">
                        {r.option_counts[oi] || 0} ({pct}%)
                      </span>
                    </div>
                  )
                })}
              </div>

              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Total answers: <strong>{r.total_answers}</strong>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}