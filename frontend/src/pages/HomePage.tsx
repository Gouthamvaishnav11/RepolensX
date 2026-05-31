import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Search, Zap, Users, TrendingUp, GitBranch, MessageSquare, Download, Shield } from 'lucide-react'

const features = [
  { icon: Zap, title: "7 AI Agents", desc: "Specialized agents for code, docs, testing, DevOps, and recruiter evaluation" },
  { icon: Search, title: "RAG Pipeline", desc: "Vector-powered semantic search over your entire repository knowledge base" },
  { icon: Users, title: "Recruiter Score", desc: "Get a hiring confidence score and written feedback like a real tech recruiter" },
  { icon: TrendingUp, title: "Mentor Roadmap", desc: "Personalized growth plan and skill-gap analysis to become interview-ready" },
  { icon: GitBranch, title: "Repo Comparison", desc: "Side-by-side comparison against industry-standard projects" },
  { icon: MessageSquare, title: "AI Chat", desc: "Ask anything about your repo — architecture, practices, improvements" },
  { icon: Download, title: "PDF Reports", desc: "Download full analysis reports to share with recruiters or mentors" },
  { icon: Shield, title: "Progress Tracking", desc: "Track your scores over time as you improve your repositories" },
]

const stats = [
  { value: "7", label: "Specialized AI Agents" },
  { value: "RAG", label: "Vector-Powered Analysis" },
  { value: "100%", label: "Open Source Stack" },
  { value: "∞", label: "No Usage Limits" },
]

export default function HomePage() {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  return (
    <div className="min-h-screen">
      {/* ─── Hero ─────────────────────────────────────────── */}
      <section className="pt-32 pb-20 px-6 text-center relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-600/5 rounded-full blur-3xl" />
          <div className="absolute top-20 left-20 w-64 h-64 bg-indigo-600/5 rounded-full blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="relative"
        >
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-brand-900/40 border border-brand-700/50 text-brand-400 text-xs font-medium px-4 py-2 rounded-full mb-8">
            <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-pulse" />
            Multi-Agent RAG Platform — 100% Open Source
          </div>

          <h1 className="font-display text-5xl md:text-7xl font-bold text-slate-100 mb-6 leading-tight">
            Turn Any GitHub Repo Into<br />
            <span className="gradient-text">AI-Powered Intelligence</span>
          </h1>

          <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 font-body leading-relaxed">
            RepoLens X uses 7 specialized AI agents and a RAG pipeline to analyze your GitHub
            repositories like a senior recruiter and engineering mentor — completely free.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href={`${API_BASE}/api/auth/github/login`}
              className="btn-primary text-base px-8 py-3.5 flex items-center gap-2 justify-center"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
              Get Started Free
            </a>
            <Link to="/analyze" className="btn-secondary text-base px-8 py-3.5">
              Analyze a Repo
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ─── Stats ────────────────────────────────────────── */}
      <section className="py-12 px-6 border-y border-slate-800">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i, duration: 0.5 }}
              className="text-center"
            >
              <div className="font-display text-3xl font-bold gradient-text mb-1">{stat.value}</div>
              <div className="text-slate-500 text-sm">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── Features ─────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="font-display text-3xl md:text-4xl font-bold text-slate-100 mb-4">
              Everything you need to understand any repository
            </h2>
            <p className="text-slate-400 text-lg max-w-xl mx-auto">
              Built with LangGraph, ChromaDB, Ollama, and BGE-M3 — all running locally with no limits.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i, duration: 0.5 }}
                className="glass-card p-6 hover:border-brand-700/50 transition-all duration-300 group"
              >
                <div className="w-10 h-10 rounded-xl bg-brand-900/50 flex items-center justify-center mb-4 group-hover:bg-brand-800/50 transition-colors">
                  <feature.icon className="w-5 h-5 text-brand-400" />
                </div>
                <h3 className="font-display font-semibold text-slate-100 mb-2">{feature.title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto text-center glass-card p-12 glow-green">
          <h2 className="font-display text-3xl font-bold text-slate-100 mb-4">
            Ready to analyze your first repository?
          </h2>
          <p className="text-slate-400 mb-8">
            Free plan includes 3 repos/month. No credit card required.
          </p>
          <a
            href={`${API_BASE}/api/auth/github/login`}
            className="btn-primary text-base px-8 py-3.5 inline-flex items-center gap-2"
          >
            Start for Free
          </a>
        </div>
      </section>
    </div>
  )
}
