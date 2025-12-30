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

    const res = await fetch(`${API_BASE}/stage/stages`)
    if (!res.ok) return []
    const data = await res.json()
    setCached(cacheKey, data, 1440)
    return data
  },

  async getStageStats(vsStageId) {
    try {
      const res = await fetch(`${API_BASE}/stage/stages/${vsStageId}/stats`)
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
      const res = await fetch(url)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },

  async getMyAllStageStats() {
    try {
      const res = await fetch(`${API_BASE}/stage/my-stats`)
      if (!res.ok) return []
      return await res.json()
    } catch {
      return []
    }
  },

  async getMyBestWeapons() {
    try {
      const res = await fetch(`${API_BASE}/stage/my-best-weapons`)
      if (!res.ok) return {}
      const result = await res.json()
      return result.data || {}
    } catch {
      return {}
    }
  },

  async refreshToken() {
    const res = await fetch(`${API_BASE}/data/refresh/token`, { method: 'POST' })
    if (!res.ok) throw new Error('Token 刷新失败')
    return await res.json()
  },

  async refreshStageRecords() {
    const res = await fetch(`${API_BASE}/data/refresh/stages_records`, { method: 'POST' })
    if (!res.ok) throw new Error('地图数据刷新失败')
    return await res.json()
  },

  async refreshBattleDetails() {
    const res = await fetch(`${API_BASE}/data/refresh/battle_details?mode=ALL`, { method: 'POST' })
    if (!res.ok) throw new Error('对战数据刷新失败')
    return await res.json()
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
