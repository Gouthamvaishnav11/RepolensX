import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Plus, GitBranch, Clock, CheckCircle, AlertCircle, Loader, BarChart2 } from 'lucide-react'
import { repoAPI, userAPI } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const statusIcon = {
  pending: <Clock className="w-4 h-4 text-slate-500" />,
  ingesting: <Loader className="w-4 h-4 text-blue-400 animate-spin" />,
  embedding: <Loader className="w-4 h-4 text-yellow-400 animate-spin" />,
  analyzing: <Loader className="w-4 h-4 text-brand-400 animate-spin" />,
  completed: <CheckCircle className="w-4 h-4 text-brand-400" />,
  failed: <AlertCircle className="w-4 h-4 text-red-400" />,
}

const statusColor = {
  pending: 'text-slate-400',
  ingesting: 'text-blue-400',
  embedding: 'text-yellow-400',
  analyzing: 'text-brand-400',
  completed: 'text-brand-400',
  failed: 'text-red-400',
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [repos, setRepos] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([repoAPI.getMyRepos(), userAPI.getStats()])
      .then(([reposRes, statsRes]) => {
        setRepos(reposRes.data)
        setStats(statsRes.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const limit = stats?.plan_limits?.repos_per_month || 3
  const used = stats?.repos_this_month || 0
  const usagePercent = limit === -1 ? 0 : Math.round((used / limit) * 100)

  return (
    <div className="max-w-7xl mx-auto px-6 py-28">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl font-bold text-slate-100">
            Welcome back, <span className="gradient-text">{user?.username}</span>
          </h1>
          <p className="text-slate-400 mt-1">Your repository intelligence dashboard</p>
        </div>
        <Link to="/analyze" className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Analyze Repo
        </Link>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-5"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 bg-brand-900/50 rounded-xl flex items-center justify-center">
                <GitBranch className="w-4 h-4 text-brand-400" />
              </div>
              <span className="text-slate-400 text-sm">Total Analyzed</span>
            </div>
            <div className="font-display text-3xl font-bold text-slate-100">
              {stats.total_repos_analyzed}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-5"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 bg-brand-900/50 rounded-xl flex items-center justify-center">
                <BarChart2 className="w-4 h-4 text-brand-400" />
              </div>
              <span className="text-slate-400 text-sm">This Month</span>
            </div>
            <div className="font-display text-3xl font-bold text-slate-100">
              {used} <span className="text-slate-500 text-lg font-normal">/ {limit === -1 ? '∞' : limit}</span>
            </div>
            {limit !== -1 && (
              <div className="mt-3 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-500 rounded-full transition-all"
                  style={{ width: `${usagePercent}%` }}
                />
              </div>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-5"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 bg-brand-900/50 rounded-xl flex items-center justify-center">
                <span className="text-brand-400 text-xs font-bold">PRO</span>
              </div>
              <span className="text-slate-400 text-sm">Current Plan</span>
            </div>
            <div className="font-display text-3xl font-bold text-slate-100 capitalize">
              {stats.plan}
            </div>
            {stats.plan === 'free' && (
              <Link to="/pricing" className="text-brand-400 text-xs mt-2 inline-block hover:underline">
                Upgrade to PRO →
              </Link>
            )}
          </motion.div>
        </div>
      )}

      {/* Repositories */}
      <div>
        <h2 className="font-display text-xl font-semibold text-slate-200 mb-4">Your Repositories</h2>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader className="w-8 h-8 text-brand-400 animate-spin" />
          </div>
        ) : repos.length === 0 ? (
          <div className="glass-card p-16 text-center">
            <GitBranch className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="font-display text-lg text-slate-300 mb-2">No repositories yet</h3>
            <p className="text-slate-500 mb-6">Submit your first GitHub repository to get started</p>
            <Link to="/analyze" className="btn-primary">
              Analyze Your First Repo
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {repos.map((repo: any, i: number) => (
              <motion.div
                key={repo.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.05 * i }}
                className="glass-card p-5 flex items-center justify-between hover:border-slate-600/80 transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-dark-700 rounded-xl flex items-center justify-center">
                    <GitBranch className="w-4 h-4 text-slate-400" />
                  </div>
                  <div>
                    <div className="font-medium text-slate-100 group-hover:text-brand-400 transition-colors">
                      {repo.full_name}
                    </div>
                    <div className="text-slate-500 text-xs mt-0.5">
                      {new Date(repo.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className={`flex items-center gap-1.5 text-sm ${statusColor[repo.status as keyof typeof statusColor] || 'text-slate-400'}`}>
                    {statusIcon[repo.status as keyof typeof statusIcon]}
                    <span className="capitalize">{repo.status}</span>
                  </div>

                  {repo.status === 'completed' && (
                    <Link
                      to={`/report/${repo.id}`}
                      className="btn-secondary text-sm py-1.5 px-4"
                    >
                      View Report
                    </Link>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
