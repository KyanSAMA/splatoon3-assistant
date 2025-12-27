const API_BASE = '/api'

export const authService = {
  async getLoginUrl() {
    const res = await fetch(`${API_BASE}/auth/login`)
    if (!res.ok) throw new Error('Failed to get login URL')
    return res.json()
  },

  async handleCallback(callbackUrl, state) {
    const res = await fetch(`${API_BASE}/auth/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ callback_url: callbackUrl, state })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Login failed')
    }
    return res.json()
  },

  async getCurrentUser() {
    const res = await fetch(`${API_BASE}/auth/current`)
    if (res.status === 401 || res.status === 404) return null
    if (!res.ok) throw new Error('获取用户信息失败')
    return res.json()
  },

  async getUsers() {
    const res = await fetch(`${API_BASE}/auth/users`)
    if (res.status === 401) return []
    if (!res.ok) throw new Error('获取用户列表失败')
    return res.json()
  },

  async switchUser(userId) {
    const res = await fetch(`${API_BASE}/auth/switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })
    if (!res.ok) throw new Error('Failed to switch user')
    return res.json()
  },

  async logout() {
    const res = await fetch(`${API_BASE}/auth/logout`, { method: 'POST' })
    if (!res.ok) throw new Error('登出失败')
    return res.json()
  }
}
