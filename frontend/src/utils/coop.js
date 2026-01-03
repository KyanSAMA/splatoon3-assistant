import { CoopEnemyInfo, CoopBossInfo } from '../enums/coop/coop_enemy'
import { CoopStage } from '../enums/coop/coop_stage'
import { WeaponInfoMain, Hash2Id } from '../enums/weapon/main'
import { WeaponInfoSpecial } from '../enums/weapon/special'

const extractNumericId = (value) => {
  if (!value) return NaN
  const match = String(value).match(/(\d+)$/)
  return match ? parseInt(match[1], 10) : NaN
}

const getEnumKeyById = (enumIdObj, id) => {
  if (typeof id !== 'number' || isNaN(id)) return null
  return Object.entries(enumIdObj).find(([, v]) => v === id)?.[0] || null
}

// Enemy ID 解析: "CoopEnemy-10" -> 10
export const parseCoopEnemyId = (id) => extractNumericId(id)

// 根据数字 ID 获取敌人枚举名称
export const getEnemyEnumName = (numericId) => {
  const id = Number(numericId)
  return getEnumKeyById(CoopEnemyInfo.Id, id) || getEnumKeyById(CoopBossInfo.Id, id) || null
}

// 获取敌人图片路径
export const getEnemyImagePath = (numericId) => {
  const name = getEnemyEnumName(numericId) || 'Dummy'
  return `/static/coop_enemy/${name}.png`
}

// Stage ID 解析: "CoopStage-105" -> 105
export const parseCoopStageId = (id) => extractNumericId(id)

// 根据数字 ID 获取地图枚举名称
export const getStageEnumName = (numericId) => {
  const id = Number(numericId)
  return getEnumKeyById(CoopStage.Id, id) || null
}

// 获取地图图片路径
export const getStageImagePath = (stageIdOrName) => {
  let name = stageIdOrName
  if (typeof stageIdOrName === 'number') {
    name = getStageEnumName(stageIdOrName) || 'Unknown'
  }
  return `/static/stage_l/${name}.png`
}

export const getStageBannerPath = (stageIdOrName) => {
  let name = stageIdOrName
  if (typeof stageIdOrName === 'number') {
    name = getStageEnumName(stageIdOrName) || 'Unknown'
  }
  return `/static/stage_banner/${name}.png`
}

// 从 Nintendo URL 提取武器 Hash
export const extractWeaponHashFromUrl = (url) => {
  if (typeof url !== 'string') return ''
  const match = url.match(/([0-9a-f]{64})/i)
  return match ? match[1].toLowerCase() : ''
}

// Hash 转武器 ID
export const getWeaponIdFromHash = (hash) => {
  if (!hash) return WeaponInfoMain.Id.Dummy
  const result = Hash2Id(hash.toLowerCase())
  return typeof result === 'number' ? result : WeaponInfoMain.Id.Dummy
}

// 获取武器图片路径
export const getWeaponImagePath = (weaponId) => {
  const id = parseInt(weaponId, 10)
  if (isNaN(id)) return '/static/weapon/0.png'
  return `/static/weapon/${id}.png`
}

// 获取大招图片路径 (special_weapon_id: 20012 -> 12)
export const getSpecialWeaponEnumName = (specialId) => {
  const id = Number(specialId)
  return getEnumKeyById(WeaponInfoSpecial.Id, id) || null
}

export const getSpecialWeaponImagePath = (specialId) => {
  const id = parseInt(specialId, 10)
  if (isNaN(id)) return ''
  const code = id % 100
  return `/static/special_weapon/${code}.png`
}

// 格式化危险度: 1.94 -> "194%"
export const formatDangerRate = (rate) => {
  if (typeof rate !== 'number' || isNaN(rate)) return ''
  return `${Math.round(rate * 100)}%`
}

// 格式化结果: 0 -> "Clear", 1-3 -> "Wave X"
export const formatResultWave = (wave) => {
  const value = Number(wave)
  if (isNaN(value)) return ''
  return value === 0 ? 'Clear' : `Wave ${value}`
}

// 获取物种图片路径
export const getSpeciesImagePath = (species, type = 'rescues') => {
  if (!species) return ''
  const s = species.toLowerCase()
  const t = type === 'rescued' ? 'rescued' : 'rescues'
  return `/static/coop/${s}/${t}.png`
}

// 规则名称映射
export const getRuleName = (rule) => {
  const map = {
    REGULAR: '普通打工',
    BIG_RUN: '大型跑',
    TEAM_CONTEST: '团队打工'
  }
  return map[rule] || rule
}

// 水位名称映射
export const getWaterLevelName = (level) => {
  const map = { 0: '干潮', 1: '普通', 2: '满潮' }
  return map[level] ?? '-'
}

// 安全 JSON 解析
export const safeParse = (val, fallback = null) => {
  if (!val) return fallback
  if (typeof val === 'object') return val
  try { return JSON.parse(val) } catch { return fallback }
}

// 排序敌人统计 (按 ID 数字排序)
export const sortEnemiesByNumericId = (enemies) => {
  return [...enemies].sort((a, b) => {
    const idA = parseCoopEnemyId(a.enemy_id || a.boss_id)
    const idB = parseCoopEnemyId(b.enemy_id || b.boss_id)
    return idA - idB
  })
}
