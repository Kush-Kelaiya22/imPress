import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth.jsx'
import Navbar from './components/Navbar.jsx'
import SessionGuard from './components/SessionGuard.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Classes from './pages/Classes.jsx'
import QuizCreate from './pages/QuizCreate.jsx'
import PollLive from './pages/PollLive.jsx'
import DeviceTree from './pages/DeviceTree.jsx'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return (
    <>
      <SessionGuard />
      {children}
    </>
  )
}

function AppRoutes() {
  const { token } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <div className="app-container">
              <Navbar />
              <main className="main-content">
                <Dashboard />
              </main>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/classes"
        element={
          <ProtectedRoute>
            <div className="app-container">
              <Navbar />
              <main className="main-content">
                <Classes />
              </main>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/classes/:classId/quiz"
        element={
          <ProtectedRoute>
            <div className="app-container">
              <Navbar />
              <main className="main-content">
                <QuizCreate />
              </main>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/classes/:classId/poll"
        element={
          <ProtectedRoute>
            <div className="app-container">
              <Navbar />
              <main className="main-content">
                <PollLive />
              </main>
            </div>
          </ProtectedRoute>
        }
      />

      <Route
        path="/classes/:classId/devices"
        element={
          <ProtectedRoute>
            <div className="app-container">
              <Navbar />
              <main className="main-content">
                <DeviceTree />
              </main>
            </div>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}