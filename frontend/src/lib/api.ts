import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// ─── Request Interceptor: Attach JWT ──────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Response Interceptor: Handle 401 ─────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const res = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token } = res.data
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        original.headers.Authorization = `Bearer ${access_token}`
        return api(original)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/'
      }
    }
    return Promise.reject(error)
  }
)

export default api

// ─── API Functions ────────────────────────────────────────
export const authAPI = {
  getLoginUrl: () => api.get('/auth/github/login'),
  refreshToken: (token: string) => api.post('/auth/refresh', { refresh_token: token }),
}

export const userAPI = {
  getMe: () => api.get('/users/me'),
  getStats: () => api.get('/users/me/stats'),
  updatePreferences: (prefs: object) => api.put('/users/me/preferences', prefs),
}

export const repoAPI = {
  submit: (github_url: string) => api.post('/repos/submit', { github_url }),
  getStatus: (repo_id: string) => api.get(`/repos/${repo_id}/status`),
  getReport: (repo_id: string) => api.get(`/repos/${repo_id}/report`),
  getMyRepos: () => api.get('/repos/my-repos'),
  getPublicReport: (token: string) => api.get(`/repos/public/${token}`),
}

export const chatAPI = {
  sendMessage: (repo_id: string, message: string, history: any[]) =>
    api.post(`/chat/${repo_id}`, { message, conversation_history: history }),
  getHistory: (repo_id: string) => api.get(`/chat/${repo_id}/history`),
}
