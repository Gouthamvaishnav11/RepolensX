import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { GitBranch, ArrowRight, Trophy, Loader, AlertCircle } from 'lucide-react'
import { repoAPI } from '@/lib/api'
import api from '@/lib/api'

const categories = [
  { key: 'overall',       label: 'Overall' },
  { key: 'code_quality',  label: 'Code Quality' },
  { key: 'documentation', label: 'Documentation' },
  { key: 'testing',       label: 'Testing' },
  { key: 'devops',        label: 'DevOps' },
  { key: 'architecture',  label: 'Architecture' },
]

const ScoreBar = ({ score, max = 100, color }: { score: number, max?: number, color: string }) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 h-2 bg-dark-700 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score}%`, backgroundColor: color }} />
    </div>
    <span className="text-sm font-medium text-slate-200 w-8 text-right">{score}</span>
  </div>
)

export default function ComparePage() {
  const [repos, setRepos] = useState<any[]>([])
  const [repo1, setRepo1] = useState('')
  const [repo2, setRepo2] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    repoAPI.getMyRepos().then(res => {
      const completed = res.data.filter((r: any) => r.status === 'completed')
      setRepos(completed)
    })
  }, [])

  const handleCompare = async () => {
    if (!repo1 || !repo2 || repo1 === repo2) {
      setError('Please select two different repositories')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await api.get(`/compare/${repo1}/${repo2}`)
      setResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-28">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="text-center mb-10">
          <h1 className="font-display text-3xl font-bold text-slate-100 mb-2">Compare Repositories</h1>
          <p className="text-slate-400">Side-by-side analysis comparison of two repositories</p>
        </div>

        {/* Selector */}
        <div className="glass-card p-6 mb-8">
          <div className="flex flex-col md:flex-row items-center gap-4">
            <select
              value={repo1}
              onChange={e => setRepo1(e.target.value)}
              className="input-field flex-1"
            >
              <option value="">Select Repository 1</option>
              {repos.map((r: any) => (
                <option key={r.id} value={r.id}>{r.full_name}</option>
              ))}
            </select>

            <div className="text-slate-500"><ArrowRight className="w-5 h-5" /></div>

            <select
              value={repo2}
              onChange={e => setRepo2(e.target.value)}
              className="input-field flex-1"
            >
              <option value="">Select Repository 2</option>
              {repos.map((r: any) => (
                <option key={r.id} value={r.id}>{r.full_name}</option>
              ))}
            </select>

            <button
              onClick={handleCompare}
              disabled={loading || !repo1 || !repo2}
              className="btn-primary flex items-center gap-2 whitespace-nowrap"
            >
              {loading ? <Loader className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
              Compare
            </button>
          </div>

          {error && (
            <div className="mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-900/20 border border-red-800/50 rounded-lg p-3">
              <AlertCircle className="w-4 h-4" />{error}
            </div>
          )}

          {repos.length < 2 && (
            <p className="text-slate-500 text-sm text-center mt-3">
              You need at least 2 analyzed repositories to compare.
            </p>
          )}
        </div>

        {/* Results */}
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">

            {/* Winner Banner */}
            <div className="glass-card p-5 border-brand-700/50 bg-brand-900/10 flex items-center gap-4">
              <div className="w-12 h-12 bg-brand-900/50 rounded-xl border border-brand-700 flex items-center justify-center">
                <Trophy className="w-6 h-6 text-brand-400" />
              </div>
              <div>
                <p className="text-slate-400 text-sm">Overall Winner</p>
                <p className="font-display text-xl font-bold text-brand-400">{result.overall_winner}</p>
              </div>
            </div>

            {/* Score Comparison */}
            <div className="glass-card p-6">
              <h2 className="font-display font-semibold text-slate-200 mb-6">Score Comparison</h2>
              <div className="space-y-5">
                {categories.map(cat => {
                  const data = result.comparison[cat.key]
                  if (!data) return null
                  return (
                    <div key={cat.key}>
                      <div className="flex justify-between text-xs text-slate-400 mb-2">
                        <span>{cat.label}</span>
                        <span className="text-brand-400">Diff: {data.diff}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-xs text-slate-500 mb-1 truncate">{result.repo1.full_name}</p>
                          <ScoreBar score={data.repo1}
                            color={data.winner === result.repo1.full_name ? '#22c55e' : '#64748b'} />
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 mb-1 truncate">{result.repo2.full_name}</p>
                          <ScoreBar score={data.repo2}
                            color={data.winner === result.repo2.full_name ? '#22c55e' : '#64748b'} />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Insights */}
            {result.insights.length > 0 && (
              <div className="glass-card p-5">
                <h2 className="font-display font-semibold text-slate-200 mb-3">Key Insights</h2>
                <ul className="space-y-2">
                  {result.insights.map((insight: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-slate-300 text-sm">
                      <span className="text-brand-400 mt-0.5">→</span> {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Side by side summaries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[result.repo1, result.repo2].map((repo: any, i: number) => (
                <div key={i} className="glass-card p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch className="w-4 h-4 text-brand-400" />
                    <h3 className="font-display font-semibold text-slate-200 text-sm">{repo.full_name}</h3>
                  </div>
                  <p className="text-slate-400 text-xs mb-3">{repo.summary}</p>
                  <div className="space-y-1">
                    {(repo.strengths || []).slice(0, 3).map((s: string, j: number) => (
                      <div key={j} className="text-xs text-green-400 flex items-center gap-1">
                        <span>✓</span> {s}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
