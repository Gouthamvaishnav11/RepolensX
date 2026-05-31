import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, ArrowLeft, Bot, User, Loader, FileCode } from 'lucide-react'
import { chatAPI, repoAPI } from '@/lib/api'

const SUGGESTIONS = [
  "Why is my architecture weak?",
  "What backend practices are missing?",
  "Is this repository interview-ready?",
  "How would a recruiter evaluate this?",
  "What skills does this repo demonstrate?",
  "Generate a senior-level improvement plan",
]

export default function ChatPage() {
  const { repo_id } = useParams()
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [repo, setRepo] = useState<any>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!repo_id) return
    // Load repo info and chat history
    repoAPI.getMyRepos().then(res => {
      const found = res.data.find((r: any) => r.id === repo_id)
      if (found) setRepo(found)
    })
    chatAPI.getHistory(repo_id).then(res => {
      setMessages(res.data.map((m: any) => ({
        role: m.role,
        content: m.content,
      })))
    }).catch(() => {})
  }, [repo_id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text?: string) => {
    const message = text || input.trim()
    if (!message || loading || !repo_id) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: message }])
    setLoading(true)

    try {
      const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }))
      const res = await chatAPI.sendMessage(repo_id, message, history)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.message,
        sources: res.data.sources,
      }])
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.response?.data?.detail || 'Failed to get response'}`,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-20 h-screen flex flex-col">

      {/* Header */}
      <div className="flex items-center gap-3 mb-4 pt-8">
        <Link to={`/report/${repo_id}`} className="p-2 text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="w-8 h-8 bg-brand-900/50 rounded-xl border border-brand-700 flex items-center justify-center">
          <Bot className="w-4 h-4 text-brand-400" />
        </div>
        <div>
          <h1 className="font-display font-bold text-slate-100">AI Repository Chat</h1>
          <p className="text-slate-500 text-xs">{repo?.full_name || 'Loading...'}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-2">

        {/* Welcome */}
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-8"
          >
            <div className="w-14 h-14 bg-brand-900/50 border border-brand-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Bot className="w-7 h-7 text-brand-400" />
            </div>
            <h2 className="font-display text-xl font-bold text-slate-100 mb-2">
              Ask anything about this repository
            </h2>
            <p className="text-slate-400 text-sm mb-6">
              Powered by RAG — answers are grounded in actual repository code
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-xl mx-auto">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  className="text-xs bg-dark-700 hover:bg-dark-600 text-slate-300 hover:text-slate-100 px-3 py-2 rounded-xl border border-slate-700 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Message list */}
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user'
                  ? 'bg-brand-700'
                  : 'bg-dark-700 border border-slate-700'
              }`}>
                {msg.role === 'user'
                  ? <User className="w-4 h-4 text-white" />
                  : <Bot className="w-4 h-4 text-brand-400" />
                }
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] space-y-2`}>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-700 text-white rounded-tr-sm'
                    : 'bg-dark-800 border border-slate-700/50 text-slate-200 rounded-tl-sm'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>

                {/* Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pl-1">
                    {msg.sources.slice(0, 3).map((src: any, j: number) => (
                      <div key={j} className="flex items-center gap-1 text-xs bg-dark-700 text-slate-400 px-2 py-1 rounded-lg border border-slate-700">
                        <FileCode className="w-3 h-3" />
                        <span className="truncate max-w-[120px]">{src.file_path}</span>
                        <span className="text-brand-500">{Math.round(src.relevance_score * 100)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-xl bg-dark-700 border border-slate-700 flex items-center justify-center">
              <Bot className="w-4 h-4 text-brand-400" />
            </div>
            <div className="bg-dark-800 border border-slate-700/50 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1.5">
                {[0,1,2].map(i => (
                  <div key={i} className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="pt-4 pb-2">
        <div className="flex gap-3 glass-card p-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Ask anything about this repository..."
            className="flex-1 bg-transparent text-slate-100 placeholder:text-slate-500 text-sm px-3 py-2 focus:outline-none"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="btn-primary p-2.5 rounded-xl"
          >
            {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-center text-slate-600 text-xs mt-2">
          Answers grounded in repository code via RAG pipeline
        </p>
      </div>
    </div>
  )
}
