import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle, AlertCircle, Loader, GitBranch } from 'lucide-react'
import { repoAPI } from '@/lib/api'

const STEPS = [
  { status: 'ingesting', label: 'Fetching from GitHub', desc: 'Cloning repo, extracting code, commits, and docs...' },
  { status: 'embedding', label: 'Building Knowledge Base', desc: 'Chunking files and generating vector embeddings...' },
  { status: 'analyzing', label: 'Running AI Agents', desc: '7 specialized agents analyzing your repository...' },
  { status: 'completed', label: 'Analysis Complete', desc: 'Your report is ready!' },
]

export default function StatusPage() {
  const { repo_id } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!repo_id) return

    const poll = async () => {
      try {
        const res = await repoAPI.getStatus(repo_id)
        setStatus(res.data)

        if (res.data.status === 'completed') {
          setTimeout(() => navigate(`/report/${repo_id}`), 1500)
        } else if (res.data.status === 'failed') {
          setError('Analysis failed. Please try again.')
        }
      } catch (err: any) {
        setError('Failed to get status.')
      }
    }

    poll()
    const interval = setInterval(poll, 3000)
    return () => clearInterval(interval)
  }, [repo_id])

  const currentStepIndex = STEPS.findIndex(s => s.status === status?.status)

  return (
    <div className="max-w-lg mx-auto px-6 py-28">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <div className="w-16 h-16 rounded-2xl bg-brand-900/50 border border-brand-700 flex items-center justify-center mx-auto mb-6">
          <GitBranch className="w-8 h-8 text-brand-400" />
        </div>
        <h1 className="font-display text-3xl font-bold text-slate-100 mb-2">Analyzing Repository</h1>
        <p className="text-slate-400">{status?.message || 'Starting analysis...'}</p>
      </motion.div>

      {/* Progress bar */}
      <div className="glass-card p-8 mb-6">
        <div className="flex justify-between text-sm text-slate-400 mb-2">
          <span>Progress</span>
          <span>{status?.progress_percent || 0}%</span>
        </div>
        <div className="h-2 bg-dark-700 rounded-full overflow-hidden mb-8">
          <motion.div
            className="h-full bg-gradient-to-r from-brand-600 to-emerald-400 rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${status?.progress_percent || 0}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Steps */}
        <div className="space-y-5">
          {STEPS.map((step, i) => {
            const isCompleted = currentStepIndex > i
            const isCurrent = currentStepIndex === i
            const isPending = currentStepIndex < i

            return (
              <div key={step.status} className="flex items-start gap-3">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  isCompleted ? 'bg-brand-600' :
                  isCurrent ? 'bg-brand-900 border-2 border-brand-500' :
                  'bg-dark-700 border border-slate-700'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4 text-white" />
                  ) : isCurrent ? (
                    <Loader className="w-3.5 h-3.5 text-brand-400 animate-spin" />
                  ) : (
                    <span className="w-2 h-2 bg-slate-600 rounded-full" />
                  )}
                </div>
                <div>
                  <div className={`font-medium text-sm ${
                    isCompleted ? 'text-brand-400' :
                    isCurrent ? 'text-slate-100' :
                    'text-slate-500'
                  }`}>
                    {step.label}
                  </div>
                  {(isCurrent || isCompleted) && (
                    <div className="text-slate-500 text-xs mt-0.5">{step.desc}</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm bg-red-900/20 border border-red-800/50 rounded-lg p-4">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <p className="text-center text-slate-600 text-xs mt-6">
        This page auto-refreshes every 3 seconds. You can safely navigate away.
      </p>
    </div>
  )
}
