import { motion } from 'framer-motion'
import { Check, Zap, Users, Building } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

const plans = [
  {
    name: "FREE",
    price: "₹0",
    period: "forever",
    icon: Zap,
    color: "border-slate-700",
    btnClass: "btn-secondary",
    features: [
      "3 repositories/month",
      "Basic evaluation report",
      "Recruiter score",
      "10 AI chat questions/month",
      "Public score link",
    ],
    missing: [
      "PDF report download",
      "Mentor growth roadmap",
      "Repo comparison",
      "Private repos",
      "Progress tracking",
    ],
  },
  {
    name: "PRO",
    price: "₹499",
    period: "/month",
    icon: Zap,
    color: "border-brand-600",
    popular: true,
    btnClass: "btn-primary",
    features: [
      "20 repositories/month",
      "Full 7-agent deep analysis",
      "Recruiter score + feedback",
      "100 AI chat questions/month",
      "PDF report download",
      "Mentor growth roadmap",
      "5 repo comparisons/month",
      "Progress tracking dashboard",
      "Private repos",
      "Priority queue",
    ],
    missing: [],
  },
  {
    name: "TEAM",
    price: "₹2,999",
    period: "/month",
    icon: Users,
    color: "border-purple-600",
    btnClass: "btn-secondary",
    features: [
      "Everything in PRO",
      "Unlimited repositories",
      "Unlimited AI chat",
      "Bulk candidate evaluation (50)",
      "Team dashboard",
      "Candidate ranking",
      "Custom scoring rubric",
      "API access",
      "Priority support",
    ],
    missing: [],
  },
  {
    name: "ENTERPRISE",
    price: "Custom",
    period: "",
    icon: Building,
    color: "border-yellow-600",
    btnClass: "btn-secondary",
    features: [
      "Everything in TEAM",
      "Unlimited candidates",
      "White-label branding",
      "Custom agent tuning",
      "On-premise deployment",
      "SLA guarantee",
      "Dedicated support",
      "ATS integration",
    ],
    missing: [],
  },
]

export default function PricingPage() {
  const { isAuthenticated } = useAuthStore()

  return (
    <div className="max-w-7xl mx-auto px-6 py-28">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-14"
      >
        <h1 className="font-display text-4xl md:text-5xl font-bold text-slate-100 mb-4">
          Simple, Transparent Pricing
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto">
          Start free. Upgrade when you need more. No hidden fees.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan, i) => (
          <motion.div
            key={plan.name}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i }}
            className={`glass-card p-6 relative border-2 ${plan.color} ${plan.popular ? 'glow-green' : ''}`}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                MOST POPULAR
              </div>
            )}

            <div className="mb-5">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${
                plan.popular ? 'bg-brand-900/50 border border-brand-700' : 'bg-dark-700 border border-slate-700'
              }`}>
                <plan.icon className={`w-5 h-5 ${plan.popular ? 'text-brand-400' : 'text-slate-400'}`} />
              </div>
              <h2 className="font-display text-xl font-bold text-slate-100">{plan.name}</h2>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="font-display text-3xl font-bold text-slate-100">{plan.price}</span>
                <span className="text-slate-500 text-sm">{plan.period}</span>
              </div>
            </div>

            <div className="space-y-2 mb-6">
              {plan.features.map((f, j) => (
                <div key={j} className="flex items-start gap-2 text-sm">
                  <Check className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-300">{f}</span>
                </div>
              ))}
              {plan.missing.map((f, j) => (
                <div key={j} className="flex items-start gap-2 text-sm opacity-40">
                  <span className="w-4 h-4 flex-shrink-0 mt-0.5 text-center">–</span>
                  <span className="text-slate-500">{f}</span>
                </div>
              ))}
            </div>

            {plan.name === 'FREE' && (
              <Link to={isAuthenticated ? '/dashboard' : '/'} className={`${plan.btnClass} w-full text-center block`}>
                {isAuthenticated ? 'Current Plan' : 'Get Started'}
              </Link>
            )}
            {plan.name === 'PRO' && (
              <Link to="/dashboard" className={`${plan.btnClass} w-full text-center block`}>
                Upgrade to PRO
              </Link>
            )}
            {plan.name === 'TEAM' && (
              <Link to="/dashboard" className={`${plan.btnClass} w-full text-center block`}>
                Get TEAM
              </Link>
            )}
            {plan.name === 'ENTERPRISE' && (
              <a href="mailto:contact@repolens.ai" className={`${plan.btnClass} w-full text-center block`}>
                Contact Us
              </a>
            )}
          </motion.div>
        ))}
      </div>

      {/* FAQ */}
      <div className="max-w-2xl mx-auto mt-16">
        <h2 className="font-display text-2xl font-bold text-slate-100 text-center mb-8">
          Frequently Asked Questions
        </h2>
        <div className="space-y-4">
          {[
            { q: "Is the free plan really free forever?", a: "Yes! The free plan has no time limit. You get 3 repo analyses per month, forever." },
            { q: "Can I analyze private GitHub repos?", a: "Yes, on PRO and above. You just need to provide your GitHub token with repo access." },
            { q: "What LLM does RepoLens X use?", a: "It runs Mistral 7B locally via Ollama — completely free, no API costs, no data leaves your machine." },
            { q: "Can I cancel anytime?", a: "Yes. Cancel anytime from your profile page. You keep access until the end of your billing period." },
          ].map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i }}
              className="glass-card p-5"
            >
              <h3 className="font-medium text-slate-200 mb-2">{faq.q}</h3>
              <p className="text-slate-400 text-sm">{faq.a}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
