import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GitBranch, Search, AlertCircle, Loader } from 'lucide-react'
import { repoAPI } from '@/lib/api'

const EXAMPLE_REPOS = [
  "https://github.com/tiangolo/fastapi",
  "https://github.com/vercel/next.js",
  "https://github.com/facebook/react",
]

export default function AnalyzePage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setError('')

    try {
      const res = await repoAPI.submit(url.trim())
      navigate(`/status/${res.data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit repository. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-28">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-center mb-12">
          <div className="w-16 h-16 rounded-2xl bg-brand-900/50 border border-brand-700 flex items-center justify-center mx-auto mb-6">
            <Search className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="font-display text-4xl font-bold text-slate-100 mb-3">
            Analyze a Repository
          </h1>
          <p className="text-slate-400 text-lg">
            Paste any GitHub repository URL and our 7 AI agents will analyze it instantly.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-8">
          <label className="block text-slate-300 text-sm font-medium mb-2">
            GitHub Repository URL
          </label>
          <div className="flex gap-3">
            <div className="relative flex-1">
              <GitBranch className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="input-field pl-10"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="btn-primary px-6 flex items-center gap-2 whitespace-nowrap"
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Analyze
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-900/20 border border-red-800/50 rounded-lg p-3">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <div className="mt-6">
            <p className="text-slate-500 text-xs mb-3">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_REPOS.map(repo => (
                <button
                  key={repo}
                  type="button"
                  onClick={() => setUrl(repo)}
                  className="text-xs bg-dark-700 hover:bg-dark-600 text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition-all"
                >
                  {repo.replace('https://github.com/', '')}
                </button>
              ))}
            </div>
          </div>
        </form>

        {/* What happens next */}
        <div className="mt-8 glass-card p-6">
          <h3 className="font-display font-semibold text-slate-200 mb-4 text-sm uppercase tracking-wider">
            What happens after you submit
          </h3>
          <div className="space-y-3">
            {[
              { step: "1", text: "Agent 1 fetches repository data, code, commits, and docs from GitHub" },
              { step: "2", text: "Agent 2 chunks and embeds everything into ChromaDB vector store" },
              { step: "3", text: "Agents 3-6 analyze code quality, architecture, docs, and DevOps" },
              { step: "4", text: "Agent 4 simulates a recruiter and scores your hiring readiness" },
              { step: "5", text: "Agent 7 generates your personalized developer growth roadmap" },
            ].map(item => (
              <div key={item.step} className="flex gap-3 text-sm">
                <span className="w-6 h-6 rounded-full bg-brand-900/50 text-brand-400 text-xs flex items-center justify-center flex-shrink-0 font-bold">
                  {item.step}
                </span>
                <span className="text-slate-400">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
