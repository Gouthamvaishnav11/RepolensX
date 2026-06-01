import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  CheckCircle, XCircle, AlertCircle, ArrowLeft,
  GitBranch, Star, GitFork, FileCode, GitCommit,
  MessageSquare, Download, Map, Loader, Users, TrendingUp
} from 'lucide-react'
import { repoAPI } from '@/lib/api'
import api from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts'

const ScoreRing = ({ score, label, color }: { score: number, label: string, color: string }) => (
  <div className="flex flex-col items-center gap-2">
    <div className="relative w-20 h-20">
      <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
        <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1e293b" strokeWidth="3" />
        <circle cx="18" cy="18" r="15.9" fill="none" stroke={color} strokeWidth="3"
          strokeDasharray={`${score} 100`} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold font-display text-slate-100">{score}</span>
      </div>
    </div>
    <span className="text-xs text-slate-400 text-center">{label}</span>
  </div>
)

const ScoreColor = (s: number) => s >= 80 ? '#22c55e' : s >= 60 ? '#eab308' : s >= 40 ? '#f97316' : '#ef4444'
const ScoreLabel = (s: number) => s >= 80
  ? { text: 'Excellent', color: 'text-green-400',  bg: 'bg-green-900/30 border-green-700' }
  : s >= 60
  ? { text: 'Good',      color: 'text-yellow-400', bg: 'bg-yellow-900/30 border-yellow-700' }
  : s >= 40
  ? { text: 'Needs Work',color: 'text-orange-400', bg: 'bg-orange-900/30 border-orange-700' }
  : { text: 'Poor',      color: 'text-red-400',    bg: 'bg-red-900/30 border-red-700' }

export default function ReportPage() {
  const { repo_id } = useParams()
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!repo_id) return
    repoAPI.getReport(repo_id)
      .then(res => setReport(res.data))
      .catch(err => setError(err.response?.data?.detail || 'Failed to load report'))
      .finally(() => setLoading(false))
  }, [repo_id])

  const handleDownloadPDF = async () => {
    setDownloading(true)
    try {
      const res = await api.get(`/reports/${repo_id}/pdf`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `repolens-${report?.repository?.full_name?.replace('/', '-')}-report.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('PDF download failed.')
    } finally {
      setDownloading(false)
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><Loader className="w-10 h-10 text-brand-400 animate-spin" /></div>
  if (error) return <div className="min-h-screen flex items-center justify-center"><div className="glass-card p-10 text-center"><AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" /><p className="text-red-400">{error}</p><Link to="/dashboard" className="btn-secondary mt-4 inline-block">Back</Link></div></div>

  const { repository, analysis } = report
  const scores = analysis?.scores || {}
  const overall = scores.overall || 0
  const verdict = ScoreLabel(overall)
  const recruiterFeedback = analysis?.recruiter_feedback || {}
  const mentorRoadmap = analysis?.mentor_roadmap || {}
  const barData = [
    { name: 'Code',   score: scores.code_quality  || 0 },
    { name: 'Docs',   score: scores.documentation || 0 },
    { name: 'Tests',  score: scores.testing       || 0 },
    { name: 'DevOps', score: scores.devops        || 0 },
    { name: 'Arch',   score: scores.architecture  || 0 },
  ]

  return (
    <div className="max-w-6xl mx-auto px-6 py-28">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/dashboard" className="p-2 text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="font-display text-2xl font-bold text-slate-100 flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-brand-400" />{repository?.full_name}
          </h1>
          <p className="text-slate-400 text-sm">{repository?.description || 'No description'}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleDownloadPDF} disabled={downloading} className="btn-secondary flex items-center gap-2 text-sm">
            {downloading ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}PDF
          </button>
          <Link to={`/roadmap/${repo_id}`} className="btn-secondary flex items-center gap-2 text-sm">
            <Map className="w-4 h-4" />Roadmap
          </Link>
          <Link to={`/chat/${repo_id}`} className="btn-primary flex items-center gap-2 text-sm">
            <MessageSquare className="w-4 h-4" />Ask AI
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        {[{ icon: Star, label: `${repository?.stars || 0} Stars` }, { icon: GitFork, label: `${repository?.forks || 0} Forks` }, { icon: FileCode, label: `${analysis?.total_files || 0} Files` }, { icon: GitCommit, label: `${analysis?.total_commits || 0} Commits` }].map((stat, i) => (
          <div key={i} className="flex items-center gap-1.5 text-slate-400 text-xs glass-card px-3 py-1.5">
            <stat.icon className="w-3.5 h-3.5" />{stat.label}
          </div>
        ))}
        {repository?.language && <div className="flex items-center gap-1.5 text-brand-400 text-xs glass-card px-3 py-1.5"><span className="w-2 h-2 bg-brand-400 rounded-full" />{repository.language}</div>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="space-y-5">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 text-center">
            <p className="text-slate-400 text-sm mb-3">Overall Score</p>
            <div className="relative w-32 h-32 mx-auto mb-3">
              <svg viewBox="0 0 36 36" className="w-32 h-32 -rotate-90">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1e293b" strokeWidth="2.5" />
                <circle cx="18" cy="18" r="15.9" fill="none" stroke={ScoreColor(overall)} strokeWidth="2.5" strokeDasharray={`${overall} 100`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-bold font-display text-slate-100">{overall}</span>
                <span className="text-xs text-slate-500">/100</span>
              </div>
            </div>
            <span className={`text-sm font-medium px-3 py-1 rounded-full border ${verdict.bg} ${verdict.color}`}>{verdict.text}</span>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-5">
            <h3 className="font-display font-semibold text-slate-200 mb-4 text-sm">Score Breakdown</h3>
            <div className="flex flex-wrap gap-3 justify-center">
              <ScoreRing score={scores.recruiter || 0}     label="Recruiter"    color={ScoreColor(scores.recruiter || 0)} />
              <ScoreRing score={scores.code_quality || 0}  label="Code"         color={ScoreColor(scores.code_quality || 0)} />
              <ScoreRing score={scores.documentation || 0} label="Docs"         color={ScoreColor(scores.documentation || 0)} />
              <ScoreRing score={scores.testing || 0}       label="Testing"      color={ScoreColor(scores.testing || 0)} />
              <ScoreRing score={scores.devops || 0}        label="DevOps"       color={ScoreColor(scores.devops || 0)} />
              <ScoreRing score={scores.architecture || 0}  label="Architecture" color={ScoreColor(scores.architecture || 0)} />
            </div>
          </motion.div>

          {analysis?.languages && Object.keys(analysis.languages).length > 0 && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-5">
              <h3 className="font-display font-semibold text-slate-200 mb-3 text-sm">Languages</h3>
              <div className="space-y-2">
                {Object.entries(analysis.languages).slice(0, 5).map(([lang, bytes]: any) => {
                  const total = Object.values(analysis.languages).reduce((a: any, b: any) => a + b, 0) as number
                  const pct = Math.round((bytes / total) * 100)
                  return (
                    <div key={lang}>
                      <div className="flex justify-between text-xs text-slate-400 mb-1"><span>{lang}</span><span>{pct}%</span></div>
                      <div className="h-1.5 bg-dark-700 rounded-full"><div className="h-full bg-brand-500 rounded-full" style={{ width: `${pct}%` }} /></div>
                    </div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-5">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
            <h3 className="font-display font-semibold text-slate-200 mb-2">AI Summary</h3>
            <p className="text-slate-300 leading-relaxed">{analysis?.summary}</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-card p-6">
            <h3 className="font-display font-semibold text-slate-200 mb-4">Score Overview</h3>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#0f1629', border: '1px solid #334155', borderRadius: '8px' }} labelStyle={{ color: '#e2e8f0' }} />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>{barData.map((e, i) => <Cell key={i} fill={ScoreColor(e.score)} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-5">
              <h3 className="font-display font-semibold text-green-400 mb-3 flex items-center gap-2 text-sm"><CheckCircle className="w-4 h-4" />Strengths</h3>
              <ul className="space-y-1.5">{(analysis?.strengths || []).map((s: string, i: number) => <li key={i} className="text-slate-300 text-sm flex items-start gap-2"><span className="text-green-400">✓</span>{s}</li>)}</ul>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="glass-card p-5">
              <h3 className="font-display font-semibold text-red-400 mb-3 flex items-center gap-2 text-sm"><XCircle className="w-4 h-4" />Weaknesses</h3>
              <ul className="space-y-1.5">{(analysis?.weaknesses || []).map((w: string, i: number) => <li key={i} className="text-slate-300 text-sm flex items-start gap-2"><span className="text-red-400">✗</span>{w}</li>)}</ul>
            </motion.div>
          </div>

          {analysis?.missing_practices?.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-5">
              <h3 className="font-display font-semibold text-yellow-400 mb-3 flex items-center gap-2 text-sm"><AlertCircle className="w-4 h-4" />Missing Practices</h3>
              <div className="flex flex-wrap gap-2">{analysis.missing_practices.map((m: string, i: number) => <span key={i} className="text-xs bg-yellow-900/20 text-yellow-300 border border-yellow-800/50 px-3 py-1.5 rounded-lg">{m}</span>)}</div>
            </motion.div>
          )}

          {recruiterFeedback?.hiring_recommendation && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-5">
              <h3 className="font-display font-semibold text-slate-200 mb-4 flex items-center gap-2 text-sm"><Users className="w-4 h-4 text-brand-400" />Recruiter Evaluation</h3>
              <div className="flex flex-wrap gap-2 mb-3">
                <span className={`text-sm font-bold px-3 py-1.5 rounded-lg border ${recruiterFeedback.hiring_recommendation?.includes('Yes') ? 'bg-green-900/30 text-green-400 border-green-700' : 'bg-yellow-900/30 text-yellow-400 border-yellow-700'}`}>{recruiterFeedback.hiring_recommendation}</span>
                <span className="text-sm px-3 py-1.5 rounded-lg border bg-dark-700 text-slate-300 border-slate-700">{recruiterFeedback.seniority_level}</span>
                <span className="text-sm px-3 py-1.5 rounded-lg border bg-brand-900/30 text-brand-400 border-brand-700">Confidence: {recruiterFeedback.confidence_score}/100</span>
              </div>
              {recruiterFeedback.written_feedback && <p className="text-slate-300 text-sm leading-relaxed">{recruiterFeedback.written_feedback}</p>}
            </motion.div>
          )}

          {mentorRoadmap?.motivational_message && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="glass-card p-5 border-brand-700/40 bg-brand-900/10">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display font-semibold text-slate-100 mb-1 flex items-center gap-2 text-sm"><TrendingUp className="w-4 h-4 text-brand-400" />30-Day Growth Roadmap Ready</h3>
                  <p className="text-slate-400 text-xs italic">"{mentorRoadmap.motivational_message}"</p>
                </div>
                <Link to={`/roadmap/${repo_id}`} className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap ml-4">
                  <Map className="w-4 h-4" />View Roadmap
                </Link>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
