import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from '@/components/layout/Navbar'
import HomePage from '@/pages/HomePage'
import AuthCallbackPage from '@/pages/AuthCallbackPage'
import DashboardPage from '@/pages/DashboardPage'
import AnalyzePage from '@/pages/AnalyzePage'
import StatusPage from '@/pages/StatusPage'
import ReportPage from '@/pages/ReportPage'
import ChatPage from '@/pages/ChatPage'
import ComparePage from '@/pages/ComparePage'
import ProgressPage from '@/pages/ProgressPage'
import RoadmapPage from '@/pages/RoadmapPage'
import ProfilePage from '@/pages/ProfilePage'
import { useAuthStore } from '@/store/authStore'

function Protected({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  const { isAuthenticated, fetchUser } = useAuthStore()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token && isAuthenticated) fetchUser()
  }, [])

  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
          <Route path="/analyze" element={<Protected><AnalyzePage /></Protected>} />
          <Route path="/status/:repo_id" element={<Protected><StatusPage /></Protected>} />
          <Route path="/report/:repo_id" element={<Protected><ReportPage /></Protected>} />
          <Route path="/chat/:repo_id" element={<Protected><ChatPage /></Protected>} />
          <Route path="/compare" element={<Protected><ComparePage /></Protected>} />
          <Route path="/progress" element={<Protected><ProgressPage /></Protected>} />
          <Route path="/roadmap" element={<Protected><RoadmapPage /></Protected>} />
          <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}