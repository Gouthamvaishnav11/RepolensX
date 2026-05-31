import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { TrendingUp, GitBranch, ArrowRight, Loader } from 'lucide-react'
import { repoAPI } from '@/lib/api'
import api from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function ProgressPage() {
  const [repos, setRepos] = useState<any[]>([])
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    repoAPI.getMyRepos().then(async res => {
      const completed = res.data.filter((r: any) => r.status === 'completed')
      setRepos(completed)

      const reportData = await Promise.all(
        completed.map(async (repo: any) => {
          try {
            const r = await repoAPI.getReport(repo.id)
            return {
              name: repo.name,
              full_name: repo.full_name,
              id: repo.id,
              date: repo.created_at,
              overall: r.data.analysis.scores.overall || 0,
              recruiter: r.data.analysis.scores.recruiter || 0,
              code_quality: r.data.analysis.scores.code_quality || 0,
              testing: r.data.analysis.scores.testing || 0,
              documentation: r.data.analysis.scores.documentation || 0,
            }
          } catch { return null }
        })
      )
      setReports(reportData.filter(Boolean).sort((a: any, b: any) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
      ))
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader className="w-8 h-8 text-brand-400 animate-spin" />
    </div>
  )

  return (
    <div className="max-w-5xl mx-auto px-6 py-28">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-slate-100 mb-2 flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-brand-400" />
            Progress Tracking
          </h1>
          <p className="text-slate-400">Track your repository scores over time</p>
        </div>

        {reports.length === 0 ? (
          <div className="glass-card p-16 text-center">
            <TrendingUp className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="font-display text-lg text-slate-300 mb-2">No data yet</h3>
            <p className="text-slate-500 mb-6">Analyze some repositories to track your progress</p>
            <Link to="/analyze" className="btn-primary">Analyze a Repo</Link>
          </div>
        ) : (
          <div className="space-y-6">

            {/* Score Chart */}
            {reports.length > 1 && (
              <div className="glass-card p-6">
                <h2 className="font-display font-semibold text-slate-200 mb-4">Score Trend</h2>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={reports}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} />
                    <Tooltip
                      contentStyle={{ background: '#0f1629', border: '1px solid #334155', borderRadius: '8px' }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Line type="monotone" dataKey="overall" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e' }} name="Overall" />
                    <Line type="monotone" dataKey="recruiter" stroke="#818cf8" strokeWidth={2} dot={{ fill: '#818cf8' }} name="Recruiter" />
                    <Line type="monotone" dataKey="testing" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b' }} name="Testing" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Repo Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reports.map((report: any, i: number) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * i }}
                  className="glass-card p-5 hover:border-slate-600 transition-all"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-brand-400" />
                      <span className="font-medium text-slate-200 text-sm">{report.full_name}</span>
                    </div>
                    <span className="text-2xl font-display font-bold text-brand-400">{report.overall}</span>
                  </div>

                  <div className="space-y-2 mb-4">
                    {[
                      { label: 'Recruiter', value: report.recruiter, color: '#818cf8' },
                      { label: 'Code Quality', value: report.code_quality, color: '#22c55e' },
                      { label: 'Testing', value: report.testing, color: '#f59e0b' },
                      { label: 'Documentation', value: report.documentation, color: '#06b6d4' },
                    ].map(item => (
                      <div key={item.label} className="flex items-center gap-2">
                        <span className="text-xs text-slate-500 w-24">{item.label}</span>
                        <div className="flex-1 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${item.value}%`, backgroundColor: item.color }} />
                        </div>
                        <span className="text-xs text-slate-400 w-6 text-right">{item.value}</span>
                      </div>
                    ))}
                  </div>

                  <Link to={`/report/${report.id}`} className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 transition-colors">
                    View full report <ArrowRight className="w-3 h-3" />
                  </Link>
                </motion.div>
              ))}
            </div>

          </div>
        )}
      </motion.div>
    </div>
  )
}
