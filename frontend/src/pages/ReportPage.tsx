import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft, GitBranch, Star, GitFork, FileCode, GitCommit,
  MessageSquare, Download, Map, Loader, Users, TrendingUp,
  Code, BookOpen, TestTube, Server, Layout, AlertCircle,
} from 'lucide-react'
import { repoAPI } from '@/lib/api'
import api from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts'

const ScoreColor = (s: number) =>
  s >= 80 ? '#22c55e' : s >= 60 ? '#eab308' : s >= 40 ? '#f97316' : '#ef4444'

const ScoreBadge = (s: number) =>
  s >= 80 ? 'bg-green-900/30 text-green-400 border-green-700'
  : s >= 60 ? 'bg-yellow-900/30 text-yellow-400 border-yellow-700'
  : s >= 40 ? 'bg-orange-900/30 text-orange-400 border-orange-700'
  : 'bg-red-900/30 text-red-400 border-red-700'

const ScoreText = (s: number) =>
  s >= 80 ? 'Excellent' : s >= 60 ? 'Good' : s >= 40 ? 'Needs Work' : 'Poor'

const ScoreRing = ({ score, label, color }: any) => (
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

// Generate smart description from score + category name
function smartDescription(category: string, score: number, repoName: string): string {
  const level = score >= 80 ? 'excellent' : score >= 60 ? 'good' : score >= 40 ? 'needs improvement' : 'poor'
  const descriptions: Record<string, Record<string, string>> = {
    code_quality: {
      excellent: `The code quality in ${repoName} is excellent at ${score}/100. The codebase is well-organized, follows conventions, and demonstrates strong engineering practices.`,
      good:      `Code quality scored ${score}/100 — solid overall. The codebase is functional but could benefit from better type hints, error handling, and inline documentation.`,
      'needs improvement': `Code quality scored ${score}/100 and needs work. Consider adding type hints, improving error handling, and organizing code into cleaner modules.`,
      poor:      `Code quality scored ${score}/100. The codebase needs significant restructuring — focus on organizing into logical modules and adding proper error handling.`,
    },
    documentation: {
      excellent: `Documentation is excellent at ${score}/100. The README is comprehensive with clear setup instructions, usage examples, and API documentation.`,
      good:      `Documentation scored ${score}/100. A README exists with basic information, but adding more code examples and a detailed API guide would help newcomers.`,
      'needs improvement': `Documentation scored ${score}/100. The README is minimal or missing key sections like installation steps, usage examples, or API reference.`,
      poor:      `Documentation scored ${score}/100. There is no README or it is incomplete. Without documentation, nobody can use or contribute to this project.`,
    },
    testing: {
      excellent: `Testing is excellent at ${score}/100. Unit tests, integration tests, and CI/CD pipelines are all in place — this repo is reliable and production-ready.`,
      good:      `Testing scored ${score}/100. Test files are present and CI/CD is configured. Adding more edge-case coverage would push this to excellent.`,
      'needs improvement': `Testing scored ${score}/100. Some tests exist but there is no CI/CD pipeline or test coverage is low. Add GitHub Actions to auto-run tests on every commit.`,
      poor:      `Testing scored ${score}/100. No unit tests were found. This is the single most impactful improvement — add pytest or jest tests for all core functions.`,
    },
    devops: {
      excellent: `DevOps setup is excellent at ${score}/100. Docker, CI/CD, environment configuration, and deployment scripts are all properly configured.`,
      good:      `DevOps scored ${score}/100. CI/CD is present and the project has some deployment configuration. Adding Docker or a proper .env.example would complete the setup.`,
      'needs improvement': `DevOps scored ${score}/100. Basic CI/CD may exist but Docker and environment management are missing. Adding a Dockerfile and GitHub Actions workflow is recommended.`,
      poor:      `DevOps scored ${score}/100. No CI/CD, Docker, or deployment configuration was found. This makes the project difficult to deploy consistently across environments.`,
    },
    architecture: {
      excellent: `Architecture is excellent at ${score}/100. The project follows a clean layered structure with proper separation of concerns across routes, models, services, and utilities.`,
      good:      `Architecture scored ${score}/100. The folder structure is logical and reasonably organized. Adding a services layer or cleaner module separation would improve it further.`,
      'needs improvement': `Architecture scored ${score}/100. The project structure is fairly flat. Organizing code into clear modules like routes, models, utils, and services would help maintainability.`,
      poor:      `Architecture scored ${score}/100. The project has a flat or disorganized structure. Refactoring into a proper layered architecture is strongly recommended.`,
    },
  }
  return descriptions[category]?.[level] || `${category.replace('_', ' ')} scored ${score}/100.`
}

// Match repo files to each category
function getRelatedFiles(category: string, filePaths: string[]): string[] {
  const keywords: Record<string, string[]> = {
    code_quality:  ['main', 'app', 'index', 'server', 'api', 'utils', 'helpers', 'lib', 'core'],
    documentation: ['readme', 'docs', 'contributing', 'changelog', 'license', 'wiki', '.md'],
    testing:       ['test', 'spec', '__tests__', 'jest', 'pytest', 'vitest', 'cypress', 'e2e'],
    devops:        ['dockerfile', 'docker-compose', '.github', 'workflow', '.env', 'nginx', 'deploy', 'ci'],
    architecture:  ['routes', 'models', 'controllers', 'services', 'middleware', 'config', 'schema', 'store'],
  }
  const kws = keywords[category] || []
  return filePaths
    .filter(p => kws.some(k => p.toLowerCase().includes(k)))
    .slice(0, 4)
}

const DescriptionCard = ({ icon: Icon, title, score, description, color, relatedFiles }: any) => (
  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: color + '22', border: `1px solid ${color}44` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <h3 className="font-display font-semibold text-slate-200 text-sm">{title}</h3>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xl font-bold font-display" style={{ color }}>{score}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full border ${ScoreBadge(score)}`}>{ScoreText(score)}</span>
      </div>
    </div>

    {/* Score bar */}
    <div className="h-1.5 bg-dark-700 rounded-full mb-3">
      <div className="h-full rounded-full transition-all duration-700"
        style={{ width: `${score}%`, background: color }} />
    </div>

    {/* Description — always shows something meaningful */}
    <p className="text-slate-300 text-sm leading-relaxed mb-3">{description}</p>

    {/* Related files — only show when files exist */}
    {relatedFiles.length > 0 && (
      <div>
        <p className="text-xs text-slate-500 mb-1.5 flex items-center gap-1">
          <FileCode className="w-3 h-3" /> Files found in this repo:
        </p>
        <div className="flex flex-wrap gap-1.5">
          {relatedFiles.map((f: string, i: number) => (
            <span key={i}
              className="text-xs bg-dark-700 text-slate-300 px-2.5 py-1 rounded-lg border border-slate-700 font-mono">
              {f.split('/').slice(-2).join('/')}
            </span>
          ))}
        </div>
      </div>
    )}
  </motion.div>
)

export default function ReportPage() {
  const { repo_id } = useParams()
  const [report, setReport]   = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDL]  = useState(false)
  const [error, setError]     = useState('')

  useEffect(() => {
    if (!repo_id) return
    repoAPI.getReport(repo_id)
      .then(res => setReport(res.data))
      .catch(err => setError(err.response?.data?.detail || 'Failed to load report'))
      .finally(() => setLoading(false))
  }, [repo_id])

  const downloadPDF = async () => {
    setDL(true)
    try {
      const res = await api.get(`/reports/${repo_id}/pdf`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `repolens-${report?.repository?.full_name?.replace('/', '-')}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch { alert('PDF generation failed. Make sure reportlab is installed.') }
    finally { setDL(false) }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader className="w-10 h-10 text-brand-400 animate-spin" />
    </div>
  )

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="glass-card p-10 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <p className="text-red-400 mb-4">{error}</p>
        <Link to="/dashboard" className="btn-secondary">Back to Dashboard</Link>
      </div>
    </div>
  )

  const { repository, analysis } = report
  const scores  = analysis?.scores || {}
  const rf      = analysis?.recruiter_feedback || {}
  const mr      = analysis?.mentor_roadmap || {}
  const desc    = rf.written_descriptions || {}
  const overall = Math.round(scores.overall || 0)
  const repoName = repository?.full_name || 'this repository'

  // Extract file paths — from stored data or empty array
  const filePaths: string[] = (rf.code_file_paths || [])

  const barData = [
    { name: 'Code',   score: Math.round(scores.code_quality  || 0) },
    { name: 'Docs',   score: Math.round(scores.documentation || 0) },
    { name: 'Tests',  score: Math.round(scores.testing       || 0) },
    { name: 'DevOps', score: Math.round(scores.devops        || 0) },
    { name: 'Arch',   score: Math.round(scores.architecture  || 0) },
  ]

  const categories = [
    { key: 'code_quality',  icon: Code,     title: 'Code Quality',   score: Math.round(scores.code_quality  || 0), color: '#22c55e' },
    { key: 'documentation', icon: BookOpen, title: 'Documentation',  score: Math.round(scores.documentation || 0), color: '#818cf8' },
    { key: 'testing',       icon: TestTube, title: 'Testing',        score: Math.round(scores.testing       || 0), color: '#f59e0b' },
    { key: 'devops',        icon: Server,   title: 'DevOps & CI/CD', score: Math.round(scores.devops        || 0), color: '#06b6d4' },
    { key: 'architecture',  icon: Layout,   title: 'Architecture',   score: Math.round(scores.architecture  || 0), color: '#f97316' },
  ]

  // Helper to safely get string values
  const getSafeString = (value: any): string => {
    if (typeof value === 'string') return value
    if (typeof value === 'number') return String(value)
    return ''
  }

  // Helper to safely check if string includes substring
  const safeIncludes = (value: any, substring: string): boolean => {
    const str = getSafeString(value)
    return str.includes(substring)
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-28">

      {/* Header */}
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
        <div className="flex gap-2 flex-wrap justify-end">
          <button onClick={downloadPDF} disabled={downloading}
            className="btn-secondary flex items-center gap-1.5 text-sm">
            {downloading ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            PDF
          </button>
          <Link to={`/roadmap/${repo_id}`} className="btn-secondary flex items-center gap-1.5 text-sm">
            <Map className="w-4 h-4" />Roadmap
          </Link>
          <Link to={`/chat/${repo_id}`} className="btn-primary flex items-center gap-1.5 text-sm">
            <MessageSquare className="w-4 h-4" />Ask AI
          </Link>
        </div>
      </div>

      {/* Repo Stats */}
      <div className="flex flex-wrap gap-2 mb-8">
        {[
          { icon: Star,      v: `${repository?.stars || 0} Stars` },
          { icon: GitFork,   v: `${repository?.forks || 0} Forks` },
          { icon: FileCode,  v: `${analysis?.total_files || 0} Files` },
          { icon: GitCommit, v: `${analysis?.total_commits || 0} Commits` },
        ].map((s, i) => (
          <div key={i} className="flex items-center gap-1.5 text-slate-400 text-xs glass-card px-3 py-1.5">
            <s.icon className="w-3.5 h-3.5" />{s.v}
          </div>
        ))}
        {repository?.language && (
          <div className="flex items-center gap-1.5 text-brand-400 text-xs glass-card px-3 py-1.5">
            <span className="w-2 h-2 bg-brand-400 rounded-full" />{repository.language}
          </div>
        )}
      </div>

      {/* Overall Score + Summary */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 mb-6">
        <div className="flex flex-col md:flex-row items-center gap-6">
          <div className="text-center flex-shrink-0">
            <p className="text-slate-400 text-xs mb-2">Overall Score</p>
            <div className="relative w-28 h-28">
              <svg viewBox="0 0 36 36" className="w-28 h-28 -rotate-90">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1e293b" strokeWidth="2.5" />
                <circle cx="18" cy="18" r="15.9" fill="none"
                  stroke={ScoreColor(overall)} strokeWidth="2.5"
                  strokeDasharray={`${overall} 100`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold font-display text-slate-100">{overall}</span>
                <span className="text-xs text-slate-500">/100</span>
              </div>
            </div>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full border mt-2 inline-block ${ScoreBadge(overall)}`}>
              {ScoreText(overall)}
            </span>
          </div>

          <div className="flex-1">
            <h2 className="font-display font-semibold text-slate-200 mb-2">Overall Assessment</h2>
            <p className="text-slate-300 text-sm leading-relaxed mb-4">
              {desc.overall || analysis?.summary ||
                `${repoName} scored ${overall}/100 overall. ${overall >= 70
                  ? 'This repository demonstrates solid engineering practices and would make a good portfolio piece.'
                  : 'This repository shows potential but needs improvements in testing, documentation, and DevOps before being production-ready.'
                }`
              }
            </p>
            <div className="flex flex-wrap gap-3">
              {categories.map(c => (
                <ScoreRing key={c.key} score={c.score} label={c.title.split(' ')[0]} color={ScoreColor(c.score)} />
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Bar Chart */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }} className="glass-card p-5 mb-6">
        <h2 className="font-display font-semibold text-slate-200 mb-3 text-sm">Score Overview</h2>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#0f1629', border: '1px solid #334155', borderRadius: '8px' }}
              labelStyle={{ color: '#e2e8f0' }} />
            <Bar dataKey="score" radius={[4, 4, 0, 0]}>
              {barData.map((e, i) => <Cell key={i} fill={ScoreColor(e.score)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Detailed Analysis Cards */}
      <h2 className="font-display font-semibold text-slate-200 mb-4">Detailed Analysis</h2>
      <div className="space-y-4 mb-6">
        {categories.map((cat, i) => (
          <motion.div key={cat.key} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * i }}>
            <DescriptionCard
              icon={cat.icon}
              title={cat.title}
              score={cat.score}
              color={cat.color}
              description={
                desc[cat.key] ||
                smartDescription(cat.key, cat.score, repoName)
              }
              relatedFiles={getRelatedFiles(cat.key, filePaths)}
            />
          </motion.div>
        ))}
      </div>

      {/* Recruiter Section - FIXED */}
      {rf && Object.keys(rf).length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-6">
          <h2 className="font-display font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-brand-400" />Recruiter Evaluation
          </h2>
          
          {/* Recruiter badges - safely render only if values exist and are strings */}
          <div className="flex flex-wrap gap-2 mb-3">
            {rf.hiring_recommendation && typeof rf.hiring_recommendation === 'string' && (
              <span className={`text-sm font-bold px-3 py-1.5 rounded-lg border ${
                rf.hiring_recommendation.includes('Yes')
                  ? 'bg-green-900/30 text-green-400 border-green-700'
                  : rf.hiring_recommendation === 'Maybe'
                  ? 'bg-yellow-900/30 text-yellow-400 border-yellow-700'
                  : 'bg-red-900/30 text-red-400 border-red-700'
              }`}>
                {rf.hiring_recommendation}
              </span>
            )}
            
            {rf.seniority_level && typeof rf.seniority_level === 'string' && (
              <span className="text-sm px-3 py-1.5 rounded-lg border bg-dark-700 text-slate-300 border-slate-700">
                {rf.seniority_level}
              </span>
            )}
            
            {rf.confidence_score && typeof rf.confidence_score === 'number' && (
              <span className="text-sm px-3 py-1.5 rounded-lg border bg-brand-900/30 text-brand-400 border-brand-700">
                Confidence: {rf.confidence_score}/100
              </span>
            )}
          </div>

          {/* Recruiter description - safely render */}
          <p className="text-slate-300 text-sm leading-relaxed">
            {(() => {
              // Try to get description from various sources
              if (desc.recruiter && typeof desc.recruiter === 'string') {
                return desc.recruiter
              }
              if (rf.written_feedback && typeof rf.written_feedback === 'string') {
                return rf.written_feedback
              }
              
              // Generate fallback description
              const recommendation = getSafeString(rf.hiring_recommendation)
              const seniority = getSafeString(rf.seniority_level)
              
              if (recommendation.includes('Yes')) {
                return `This developer demonstrates ${seniority.toLowerCase() || 'solid'} level skills. The repository would likely pass an initial technical portfolio review.`
              } else {
                return `This repository shows potential. Improving the score to above 70 by adding tests and CI/CD would make it interview-ready.`
              }
            })()}
          </p>

          {/* Green Flags */}
          {rf.green_flags && Array.isArray(rf.green_flags) && rf.green_flags.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-green-400 font-semibold mb-1.5">✅ Green Flags:</p>
              <ul className="text-xs text-slate-300 space-y-0.5 list-disc list-inside">
                {rf.green_flags.map((flag: string, i: number) => (
                  <li key={i}>{flag}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Red Flags */}
          {rf.red_flags && Array.isArray(rf.red_flags) && rf.red_flags.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-red-400 font-semibold mb-1.5">⚠️ Red Flags:</p>
              <ul className="text-xs text-slate-300 space-y-0.5 list-disc list-inside">
                {rf.red_flags.map((flag: string, i: number) => (
                  <li key={i}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* Roadmap CTA */}
      {mr?.motivational_message && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5 border-brand-700/40 bg-brand-900/10 flex items-center justify-between">
          <div>
            <p className="font-display font-semibold text-slate-100 flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-brand-400" />30-Day Growth Roadmap Ready
            </p>
            <p className="text-slate-400 text-xs mt-0.5 italic">"{mr.motivational_message}"</p>
          </div>
          <Link to={`/roadmap/${repo_id}`}
            className="btn-primary flex items-center gap-2 text-sm ml-4 whitespace-nowrap">
            <Map className="w-4 h-4" />View Roadmap
          </Link>
        </motion.div>
      )}

    </div>
  )
}