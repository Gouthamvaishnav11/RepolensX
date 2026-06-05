import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Map, CheckCircle, BookOpen, Target, Loader, AlertCircle, TrendingUp, Star } from 'lucide-react'
import { repoAPI } from '@/lib/api'

const WEEK_COLORS = ['#22c55e', '#818cf8', '#f59e0b', '#06b6d4']
const WEEK_BG     = ['bg-green-900/20 border-green-700', 'bg-indigo-900/20 border-indigo-700', 'bg-yellow-900/20 border-yellow-700', 'bg-cyan-900/20 border-cyan-700']

export default function RoadmapPage() {
  const { repo_id } = useParams()
  const [roadmap, setRoadmap]   = useState<any>(null)
  const [repoName, setRepoName] = useState('')
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  useEffect(() => {
    if (!repo_id) return
    repoAPI.getReport(repo_id)
      .then(res => {
        setRepoName(res.data?.repository?.full_name || '')
        const rm = res.data?.analysis?.mentor_roadmap
        if (!rm) setError('No roadmap yet. Please re-run the analysis.')
        else setRoadmap(rm)
      })
      .catch(() => setError('Failed to load roadmap'))
      .finally(() => setLoading(false))
  }, [repo_id])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader className="w-8 h-8 text-brand-400 animate-spin" />
    </div>
  )

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="glass-card p-10 text-center max-w-md">
        <AlertCircle className="w-10 h-10 text-yellow-400 mx-auto mb-3" />
        <p className="text-slate-300 mb-4">{error}</p>
        <Link to={`/report/${repo_id}`} className="btn-secondary">Back to Report</Link>
      </div>
    </div>
  )

  const weeks = roadmap?.roadmap || {}
  const weekKeys = ['week_1', 'week_2', 'week_3', 'week_4']

  return (
    <div className="max-w-4xl mx-auto px-6 py-28">

      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <Link to={`/report/${repo_id}`} className="p-2 text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Map className="w-6 h-6 text-brand-400" />
            30-Day Growth Roadmap
          </h1>
          <p className="text-slate-400 text-sm">{repoName}</p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 text-center">
          <p className="text-slate-500 text-xs mb-1">Developer Level</p>
          <p className="font-display text-lg font-bold text-brand-400">
            {roadmap?.developer_level || 'Mid-level'}
          </p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="glass-card p-4 text-center">
          <p className="text-slate-500 text-xs mb-1">Expected Score After</p>
          <p className="font-display text-lg font-bold text-green-400">
            {roadmap?.expected_score_after || 0}/100
          </p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass-card p-4 text-center">
          <p className="text-slate-500 text-xs mb-1">Primary Focus</p>
          <p className="font-display text-sm font-bold text-yellow-400 leading-tight">
            {roadmap?.primary_focus_area || 'Testing & CI/CD'}
          </p>
        </motion.div>
      </div>

      {/* Motivational Message */}
      {roadmap?.motivational_message && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass-card p-5 mb-8 border-brand-700/40 bg-brand-900/10 flex items-center gap-3">
          <Star className="w-5 h-5 text-brand-400 flex-shrink-0" />
          <p className="text-brand-300 italic">"{roadmap.motivational_message}"</p>
        </motion.div>
      )}

      {/* Weekly Plan */}
      <div className="space-y-5 mb-8">
        {weekKeys.map((weekKey, i) => {
          const week = weeks[weekKey]
          if (!week) return null
          return (
            <motion.div key={weekKey}
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 * i }}
              className={`glass-card p-6 border ${WEEK_BG[i]}`}>
              {/* Week header */}
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center border-2 font-display font-bold text-base"
                  style={{ borderColor: WEEK_COLORS[i], color: WEEK_COLORS[i], background: WEEK_COLORS[i] + '22' }}>
                  W{i + 1}
                </div>
                <div>
                  <p className="text-xs text-slate-500">Week {i + 1} of 4</p>
                  <h3 className="font-display font-semibold text-slate-100 text-lg">{week.title}</h3>
                </div>
              </div>

              {/* Tasks */}
              <div className="space-y-2.5">
                {(week.tasks || []).map((task: string, j: number) => (
                  <motion.div key={j}
                    initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 * i + 0.05 * j }}
                    className="flex items-start gap-3 p-3 bg-dark-800/50 rounded-xl">
                    <div className="w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ borderColor: WEEK_COLORS[i] }}>
                      <div className="w-2 h-2 rounded-full" style={{ background: WEEK_COLORS[i] }} />
                    </div>
                    <span className="text-slate-200 text-sm leading-relaxed">{task}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Resources */}
      {roadmap?.resources && roadmap.resources.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 mb-6">
          <h2 className="font-display font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-400" />
            Recommended Resources
          </h2>
          <div className="space-y-3">
            {roadmap.resources.map((res: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-4 bg-dark-700/50 rounded-xl border border-slate-800">
                <div className="w-8 h-8 rounded-lg bg-brand-900/50 border border-brand-700 flex items-center justify-center flex-shrink-0">
                  <Target className="w-4 h-4 text-brand-400" />
                </div>
                <div className="flex-1">
                  <p className="text-slate-200 text-sm font-medium">{res.title}</p>
                  <p className="text-slate-400 text-xs mt-0.5">{res.reason}</p>
                  <span className="inline-block text-xs bg-dark-600 text-slate-400 px-2 py-0.5 rounded mt-1.5 capitalize border border-slate-700">
                    {res.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* CTA */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="glass-card p-5 border-brand-700/40 bg-brand-900/10 flex items-center justify-between">
        <div>
          <p className="font-display font-semibold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-brand-400" /> Ready to improve your score?
          </p>
          <p className="text-slate-400 text-xs mt-0.5">Ask the AI for more specific guidance</p>
        </div>
        <Link to={`/chat/${repo_id}`} className="btn-primary text-sm">Ask AI Chat</Link>
      </motion.div>

    </div>
  )
}