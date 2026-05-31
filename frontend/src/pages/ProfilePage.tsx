import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { User, GitBranch, BarChart2, Calendar, Shield, LogOut } from 'lucide-react'
import { userAPI } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Link } from 'react-router-dom'

export default function ProfilePage() {
  const { user, logout } = useAuthStore()
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    userAPI.getStats().then((res) => setStats(res.data))
  }, [])

  const planColors: Record<string, string> = {
    free: 'text-slate-400 bg-slate-800 border-slate-700',
    pro: 'text-brand-400 bg-brand-900/50 border-brand-700',
    team: 'text-purple-400 bg-purple-900/50 border-purple-700',
    enterprise: 'text-yellow-400 bg-yellow-900/50 border-yellow-700',
  }

  const planLimits: Record<string, any> = {
    free: { repos: 3, chat: 10, label: 'Free Forever' },
    pro: { repos: 20, chat: 100, label: '₹499/month' },
    team: { repos: '∞', chat: '∞', label: '₹2,999/month' },
    enterprise: { repos: '∞', chat: '∞', label: 'Custom Enterprise' },
  }

  const plan = user?.plan || 'free'
  const limits = planLimits[plan] || planLimits.free
  const used = user?.repos_analyzed_this_month || 0

  const repoLimit =
    typeof limits.repos === 'number' ? limits.repos : 999

  const usagePct =
    typeof limits.repos === 'number'
      ? Math.round((used / repoLimit) * 100)
      : 0

  return (
    <div className="max-w-3xl mx-auto px-6 py-28">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Profile Header */}
        <div className="glass-card p-8 mb-6 flex items-center gap-6">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.username}
              className="w-20 h-20 rounded-2xl ring-2 ring-brand-700"
            />
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-dark-700 border border-slate-700 flex items-center justify-center">
              <User className="w-10 h-10 text-slate-500" />
            </div>
          )}

          <div className="flex-1">
            <h1 className="font-display text-2xl font-bold text-slate-100 mb-1">
              {user?.name || user?.username}
            </h1>

            <p className="text-slate-400 text-sm mb-3">
              @{user?.username}
            </p>

            <span
              className={`text-xs font-bold px-3 py-1.5 rounded-full border ${
                planColors[plan]
              }`}
            >
              {plan.toUpperCase()} — {limits.label}
            </span>
          </div>

          <button
            onClick={logout}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            {
              icon: GitBranch,
              label: 'Total Repos',
              value: stats?.total_repos_analyzed || 0,
            },
            {
              icon: BarChart2,
              label: 'This Month',
              value: `${used}/${
                typeof limits.repos === 'number'
                  ? limits.repos
                  : '∞'
              }`,
            },
            {
              icon: Shield,
              label: 'Plan',
              value: plan.toUpperCase(),
            },
            {
              icon: Calendar,
              label: 'Member Since',
              value: user?.created_at
                ? new Date(user.created_at).getFullYear()
                : '—',
            },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card p-4 text-center"
            >
              <div className="w-8 h-8 bg-brand-900/50 rounded-lg flex items-center justify-center mx-auto mb-2">
                <stat.icon className="w-4 h-4 text-brand-400" />
              </div>

              <p className="font-display font-bold text-slate-100">
                {stat.value}
              </p>

              <p className="text-slate-500 text-xs mt-0.5">
                {stat.label}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Usage Bar */}
        {plan !== 'team' && plan !== 'enterprise' && (
          <div className="glass-card p-5 mb-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300">
                Monthly Usage
              </span>
              <span className="text-slate-400">
                {used} / {limits.repos} repos
              </span>
            </div>

            <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  usagePct >= 90
                    ? 'bg-red-500'
                    : 'bg-brand-500'
                }`}
                style={{ width: `${usagePct}%` }}
              />
            </div>

            {usagePct >= 80 && (
              <p className="text-yellow-400 text-xs mt-2">
                ⚠️ Almost at limit —{' '}
                <Link
                  to="/pricing"
                  className="underline"
                >
                  upgrade to PRO
                </Link>
              </p>
            )}
          </div>
        )}

        {/* Plan Features */}
        <div className="glass-card p-6 mb-6">
          <h2 className="font-display font-semibold text-slate-200 mb-4">
            Your Plan Features
          </h2>

          <div className="space-y-3">
            {[
              {
                feature: 'Repos per month',
                value:
                  typeof limits.repos === 'number'
                    ? `${limits.repos} repos`
                    : 'Unlimited',
              },
              {
                feature: 'AI Chat questions',
                value:
                  typeof limits.chat === 'number'
                    ? `${limits.chat}/month`
                    : 'Unlimited',
              },
              {
                feature: 'PDF Reports',
                value:
                  plan !== 'free'
                    ? '✅ Included'
                    : '❌ PRO only',
              },
              {
                feature: 'Mentor Roadmap',
                value:
                  plan !== 'free'
                    ? '✅ Included'
                    : '❌ PRO only',
              },
              {
                feature: 'Repo Comparison',
                value:
                  plan !== 'free'
                    ? '✅ Included'
                    : '❌ PRO only',
              },
              {
                feature: 'Private Repos',
                value:
                  plan !== 'free'
                    ? '✅ Included'
                    : '❌ PRO only',
              },
              {
                feature: 'Bulk Evaluation',
                value:
                  plan === 'team' ||
                  plan === 'enterprise'
                    ? '✅ Included'
                    : '❌ TEAM only',
              },
              {
                feature: 'API Access',
                value:
                  plan === 'team' ||
                  plan === 'enterprise'
                    ? '✅ Included'
                    : '❌ TEAM only',
              },
            ].map((item, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0"
              >
                <span className="text-slate-400 text-sm">
                  {item.feature}
                </span>

                <span
                  className={`text-sm font-medium ${
                    item.value.includes('❌')
                      ? 'text-slate-600'
                      : 'text-slate-200'
                  }`}
                >
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Upgrade CTA */}
        {plan === 'free' && (
          <div className="glass-card p-6 border-brand-700/50 bg-brand-900/10 text-center">
            <h3 className="font-display font-bold text-slate-100 mb-2">
              Unlock Full Power
            </h3>

            <p className="text-slate-400 text-sm mb-4">
              Upgrade to PRO for ₹499/month and get
              20 repos, PDF reports, and mentor
              roadmaps
            </p>

            <Link
              to="/pricing"
              className="btn-primary inline-flex items-center gap-2"
            >
              Upgrade to PRO →
            </Link>
          </div>
        )}
      </motion.div>
    </div>
  )
}