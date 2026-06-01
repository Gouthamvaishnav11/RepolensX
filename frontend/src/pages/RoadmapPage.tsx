import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Map, CheckCircle, BookOpen, Target, Loader, AlertCircle } from 'lucide-react'
import { repoAPI } from '@/lib/api'

export default function RoadmapPage() {
  const { repo_id } = useParams()
  const [roadmap, setRoadmap] = useState<any>(null)
  const [repo, setRepo] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!repo_id) return
    repoAPI.getReport(repo_id)
      .then(res => {
        setRepo(res.data.repository)
        setRoadmap(res.data.analysis.mentor_roadmap)
      })
      .catch(() => setError('Failed to load roadmap'))
      .finally(() => setLoading(false))
  }, [repo_id])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader className="w-8 h-8 text-brand-400 animate-spin" />
    </div>
  )

  if (error || !roadmap) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="glass-card p-10 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <p className="text-slate-400">{error || 'No roadmap available yet. Run analysis first.'}</p>
        <Link to="/dashboard" className="btn-secondary mt-4 inline-block">Back</Link>
      </div>
    </div>
  )

  const weeks = roadmap.roadmap || {}
  const weekColors = ['#22c55e', '#818cf8', '#f59e0b', '#06b6d4']
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
          <p className="text-slate-400 text-sm">{repo?.full_name}</p>
        </div>
      </div>

      {/* Developer Level + Focus */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5 text-center"
        >
          <p className="text-slate-500 text-xs mb-1">Developer Level</p>
          <p className="font-display text-xl font-bold text-brand-400">
            {roadmap.developer_level || 'Mid-level'}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-5 text-center"
        >
          <p className="text-slate-500 text-xs mb-1">Expected Score After</p>
          <p className="font-display text-xl font-bold text-green-400">
            {roadmap.expected_score_after || 0}/100
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-5 text-center"
        >
          <p className="text-slate-500 text-xs mb-1">Primary Focus</p>
          <p className="font-display text-sm font-bold text-yellow-400">
            {roadmap.primary_focus_area || 'Testing'}
          </p>
        </motion.div>
      </div>

      {/* Motivational Message */}
      {roadmap.motivational_message && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-5 mb-8 border-brand-700/40 bg-brand-900/10"
        >
          <p className="text-brand-300 italic text-center">
            "{roadmap.motivational_message}"
          </p>
        </motion.div>
      )}

      {/* Weekly Plan */}
      <div className="space-y-5 mb-8">
        {weekKeys.map((weekKey, i) => {
          const week = weeks[weekKey]
          if (!week) return null
          return (
            <motion.div
              key={weekKey}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * i }}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center font-display font-bold text-sm text-white"
                  style={{ backgroundColor: weekColors[i] + '33', border: `2px solid ${weekColors[i]}` }}
                >
                  <span style={{ color: weekColors[i] }}>W{i + 1}</span>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Week {i + 1}</p>
                  <h3 className="font-display font-semibold text-slate-100">{week.title}</h3>
                </div>
              </div>
              <div className="space-y-2 pl-13">
                {(week.tasks || []).map((task: string, j: number) => (
                  <div key={j} className="flex items-start gap-2.5">
                    <CheckCircle className="w-4 h-4 text-slate-600 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-300 text-sm">{task}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Resources */}
      {roadmap.resources && roadmap.resources.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          <h2 className="font-display font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-400" />
            Recommended Resources
          </h2>
          <div className="space-y-3">
            {roadmap.resources.map((res: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-dark-700/50 rounded-xl">
                <div className="w-7 h-7 rounded-lg bg-brand-900/50 flex items-center justify-center flex-shrink-0">
                  <Target className="w-3.5 h-3.5 text-brand-400" />
                </div>
                <div>
                  <p className="text-slate-200 text-sm font-medium">{res.title}</p>
                  <p className="text-slate-500 text-xs mt-0.5">{res.reason}</p>
                  <span className="text-xs bg-dark-600 text-slate-400 px-2 py-0.5 rounded mt-1 inline-block capitalize">
                    {res.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
