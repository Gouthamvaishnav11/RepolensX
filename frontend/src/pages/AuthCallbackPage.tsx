import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Search } from 'lucide-react'

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const { setTokens, fetchUser } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    const access_token = searchParams.get('access_token')
    const refresh_token = searchParams.get('refresh_token')

    if (access_token && refresh_token) {
      setTokens(access_token, refresh_token)
      fetchUser().then(() => {
        navigate('/dashboard')
      })
    } else {
      navigate('/?error=auth_failed')
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 rounded-2xl bg-brand-900/50 border border-brand-700 flex items-center justify-center mx-auto mb-6 animate-pulse-slow">
          <Search className="w-8 h-8 text-brand-400" />
        </div>
        <p className="text-slate-400 font-body">Authenticating with GitHub...</p>
        <div className="mt-4 flex justify-center gap-1">
          {[0,1,2].map(i => (
            <div
              key={i}
              className="w-2 h-2 bg-brand-500 rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
