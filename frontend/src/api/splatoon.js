import { checkSessionExpired } from './session'

const S3_INK_BASE = 'https://splatoon3.ink/data'
const API_BASE = '/api'

const getCached = (key) => {
  const item = localStorage.getItem(key)
  if (!item) return null
  try {
    const { value, expiry } = JSON.parse(item)
    if (Date.now() > expiry) {
      localStorage.removeItem(key)
      return null
    }
    return value
  } catch {
    return null
  }
}

const setCached = (key, value, ttlMinutes = 60) => {
  const expiry = Date.now() + ttlMinutes * 60 * 1000
  localStorage.setItem(key, JSON.stringify({ value, expiry }))
}

/**
 * 封装 fetch，自动检查 session 过期
 */
const apiFetch = async (url, options = {}) => {
  const res = await fetch(url, options)
  if (await checkSessionExpired(res)) {
    throw new Error('SESSION_EXPIRED')
  }
  return res
}

export const splatoonService = {
  async getSchedules() {
    const cacheKey = 's3_schedules'
    const cached = getCached(cacheKey)
    if (cached) return cached

    const res = await fetch(`${S3_INK_BASE}/schedules.json`)
    if (!res.ok) throw new Error('Failed to fetch schedules')
    const data = await res.json()
    setCached(cacheKey, data, 30)
    return data
  },

  async getLocale() {
    const cacheKey = 's3_locale_zh_CN'
    const cached = getCached(cacheKey)
    if (cached) return cached

    const res = await fetch(`${S3_INK_BASE}/locale/zh-CN.json`)
    if (!res.ok) throw new Error('Failed to fetch locale')
    const data = await res.json()
    setCached(cacheKey, data, 120)
    return data
  },

  async getStages() {
    const cacheKey = 's3_stages'
    const cached = getCached(cacheKey)
    if (cached) return cached

    const res = await apiFetch(`${API_BASE}/stage/stages`)
    if (!res.ok) return []
    const data = await res.json()
    setCached(cacheKey, data, 1440)
    return data
  },

  async getStageStats(vsStageId) {
    try {
      const res = await apiFetch(`${API_BASE}/stage/stages/${vsStageId}/stats`)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },

  async getStageBestWeapon(vsStageId, vsRule = null) {
    try {
      let url = `${API_BASE}/stage/stages/${vsStageId}/best-weapon`
      if (vsRule) url += `?vs_rule=${vsRule}`
      const res = await apiFetch(url)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },

  async getMyAllStageStats() {
    try {
      const res = await apiFetch(`${API_BASE}/stage/my-stats`)
      if (!res.ok) return []
      return await res.json()
    } catch {
      return []
    }
  },

  async getMyBestWeapons() {
    try {
      const res = await apiFetch(`${API_BASE}/stage/my-best-weapons`)
      if (!res.ok) return {}
      const result = await res.json()
      return result.data || {}
    } catch {
      return {}
    }
  },

  async getBattleList(params = {}) {
    try {
      const query = new URLSearchParams()
      if (params.vs_mode) query.set('vs_mode', params.vs_mode)
      if (params.vs_rule) query.set('vs_rule', params.vs_rule)
      if (params.weapon_id) query.set('weapon_id', params.weapon_id)
      if (params.bankara_mode) query.set('bankara_mode', params.bankara_mode)
      if (params.start_time) query.set('start_time', params.start_time)
      if (params.end_time) query.set('end_time', params.end_time)
      if (params.limit) query.set('limit', params.limit)
      if (params.offset) query.set('offset', params.offset)
      const qs = query.toString()
      const url = qs ? `${API_BASE}/battle/battles?${qs}` : `${API_BASE}/battle/battles`
      const res = await apiFetch(url)
      if (!res.ok) return []
      return await res.json()
    } catch {
      return []
    }
  },

  async getBattleDetail(id) {
    try {
      const res = await apiFetch(`${API_BASE}/battle/battles/${id}`)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },

  async getBattleStats(params = {}) {
    try {
      const query = new URLSearchParams()
      if (params.vs_mode) query.set('vs_mode', params.vs_mode)
      if (params.vs_rule) query.set('vs_rule', params.vs_rule)
      if (params.weapon_id) query.set('weapon_id', params.weapon_id)
      if (params.bankara_mode) query.set('bankara_mode', params.bankara_mode)
      const qs = query.toString()
      const url = qs ? `${API_BASE}/battle/stats?${qs}` : `${API_BASE}/battle/stats`
      const res = await apiFetch(url)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },

  async getBattleDashboard(params = {}) {
    try {
      const query = new URLSearchParams()
      if (params.vs_mode) query.set('vs_mode', params.vs_mode)
      if (params.vs_rule) query.set('vs_rule', params.vs_rule)
      if (params.weapon_id) query.set('weapon_id', params.weapon_id)
      if (params.bankara_mode) query.set('bankara_mode', params.bankara_mode)
      if (params.start_time) query.set('start_time', params.start_time)
      if (params.end_time) query.set('end_time', params.end_time)
      const qs = query.toString()
      const url = qs ? `${API_BASE}/battle/dashboard?${qs}` : `${API_BASE}/battle/dashboard`
      const res = await apiFetch(url)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },

  async refreshToken() {
    const res = await apiFetch(`${API_BASE}/data/refresh/token`, { method: 'POST' })
    if (!res.ok) throw new Error('Token 刷新失败')
    return await res.json()
  },

  async refreshStageRecords() {
    const res = await apiFetch(`${API_BASE}/data/refresh/stages_records`, { method: 'POST' })
    if (!res.ok) throw new Error('地图数据刷新失败')
    return await res.json()
  },

  async refreshBattleDetails() {
    const res = await apiFetch(`${API_BASE}/data/refresh/battle_details?mode=ALL`, { method: 'POST' })
    if (!res.ok) throw new Error('对战数据刷新失败')
    return await res.json()
  },

  async getMainWeapons() {
    const cacheKey = 's3_main_weapons'
    const cached = getCached(cacheKey)
    if (cached) return cached

    try {
      const res = await apiFetch(`${API_BASE}/battle/main-weapons`)
      if (!res.ok) return []
      const data = await res.json()
      setCached(cacheKey, data, 1440) // 缓存24小时
      return data
    } catch {
      return []
    }
  },

  async getUserWeapons(params = {}) {
    try {
      const query = new URLSearchParams()
      if (params.vs_mode) query.set('vs_mode', params.vs_mode)
      if (params.vs_rule) query.set('vs_rule', params.vs_rule)
      if (params.bankara_mode) query.set('bankara_mode', params.bankara_mode)
      if (params.start_time) query.set('start_time', params.start_time)
      if (params.end_time) query.set('end_time', params.end_time)
      const qs = query.toString()
      const url = qs ? `${API_BASE}/battle/weapons?${qs}` : `${API_BASE}/battle/weapons`
      const res = await apiFetch(url)
      if (!res.ok) return []
      return await res.json()
    } catch {
      return []
    }
  },

  async getSubWeapons() {
    const cacheKey = 's3_sub_weapons'
    const cached = getCached(cacheKey)
    if (cached) return cached

    try {
      const res = await apiFetch(`${API_BASE}/battle/sub-weapons`)
      if (!res.ok) return []
      const data = await res.json()
      setCached(cacheKey, data, 1440)
      return data
    } catch {
      return []
    }
  },

  async getSpecialWeapons() {
    const cacheKey = 's3_special_weapons'
    const cached = getCached(cacheKey)
    if (cached) return cached

    try {
      const res = await apiFetch(`${API_BASE}/battle/special-weapons`)
      if (!res.ok) return []
      const data = await res.json()
      setCached(cacheKey, data, 1440)
      return data
    } catch {
      return []
    }
  },

  clearScheduleCache() {
    localStorage.removeItem('s3_schedules')
  }
}

export const RULE_NAMES = {
  TURF_WAR: '涂地',
  AREA: '区域',
  LOFT: '塔楼',
  GOAL: '鱼虎',
  CLAM: '蛤蜊'
}

export const MODE_NAMES = {
  CHALLENGE: '挑战',
  OPEN: '开放'
}
