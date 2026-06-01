
import { Link, useLocation } from "react-router-dom"
import { useAuthStore } from "@/store/authStore"
import { Search, BarChart2, GitBranch, User, LogOut, Zap, TrendingUp, DollarSign } from 'lucide-react'
export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const location = useLocation()
  const isActive = (path: string) => location.pathname === path

  const handleLogin = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/auth/github/login")
      const data = await res.json()
      window.location.href = data.auth_url
    } catch (err) {
      console.error("Login failed", err)
    }
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-slate-800/80 bg-dark-900/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center group-hover:bg-brand-500 transition-colors">
            <Search className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-lg text-slate-100">
            RepoLens <span className="text-brand-400">X</span>
          </span>
        </Link>

        {isAuthenticated && (
          <div className="hidden md:flex items-center gap-6">
            <Link
              to="/dashboard"
              className={`nav-link flex items-center gap-1.5 ${isActive('/dashboard') ? 'active' : ''}`}
            >
              <BarChart2 className="w-4 h-4" />
              Dashboard
            </Link>
            <Link
              to="/analyze"
              className={`nav-link flex items-center gap-1.5 ${isActive('/analyze') ? 'active' : ''}`}
            >
              <Zap className="w-4 h-4" />
              Analyze
            </Link>
            <Link
              to="/compare"
              className={`nav-link flex items-center gap-1.5 ${isActive('/compare') ? 'active' : ''}`}
            >
              <GitBranch className="w-4 h-4" />
              Compare
            </Link>
            <Link
              to="/progress"
              className={`nav-link flex items-center gap-1.5 ${isActive('/progress') ? 'active' : ''}`}
            >
              <TrendingUp className="w-4 h-4" />
              Progress
            </Link>
            <Link
              to="/pricing"
              className={`nav-link flex items-center gap-1.5 ${isActive('/pricing') ? 'active' : ''}`}
            >
              < DollarSign className="w-4 h-4" />
              Pricing
            </Link>
          </div>
        )}

        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium px-2.5 py-1 rounded-full border bg-slate-800 text-slate-400 border-slate-700">
                {user.plan.toUpperCase()}
              </span>
              <Link to="/profile" className="flex items-center gap-2 group">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.username} className="w-8 h-8 rounded-full" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-dark-600 flex items-center justify-center">
                    <User className="w-4 h-4 text-slate-400" />
                  </div>
                )}
                <span className="text-sm text-slate-300 hidden md:block">{user.username}</span>
              </Link>
              <button onClick={logout} className="p-2 text-slate-500 hover:text-slate-300 transition-colors">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button onClick={handleLogin} className="btn-primary flex items-center gap-2 text-sm">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              Login with GitHub
            </button>
          )}
        </div>
      </div>
    </nav>
  )
}
