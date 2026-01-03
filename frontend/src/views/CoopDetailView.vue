<script setup>
defineOptions({ name: 'CoopDetailView' })

import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { splatoonService } from '../api/splatoon'
import { formatDateTime } from '../utils/timezone'
import {
  parseCoopStageId,
  parseCoopEnemyId,
  getStageEnumName,
  getStageBannerPath,
  getEnemyImagePath,
  extractWeaponHashFromUrl,
  getWeaponIdFromHash,
  getWeaponImagePath,
  getSpecialWeaponImagePath,
  formatDangerRate,
  formatResultWave,
  getSpeciesImagePath,
  getRuleName,
  getWaterLevelName,
  safeParse
} from '../utils/coop'

const route = useRoute()
const router = useRouter()
const coop = ref(null)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    coop.value = await splatoonService.getCoopDetail(route.params.id)
    if (!coop.value) {
      error.value = '未找到打工记录'
    }
  } catch (e) {
    error.value = '加载失败: ' + (e.message || '未知错误')
    console.error(e)
  } finally {
    loading.value = false
  }
})

const goBack = () => router.back()

const getStageImg = (stageId) => {
  const numericId = parseCoopStageId(stageId)
  const name = getStageEnumName(numericId)
  return getStageBannerPath(name || 'Unknown')
}

// 解析玩家武器列表
const parsePlayerWeapons = (player) => {
  if (!player) return []
  const images = safeParse(player.images, {})
  const weaponNames = safeParse(player.weapon_names, [])
  return weaponNames.map(name => {
    const url = images[name] || ''
    const hash = extractWeaponHashFromUrl(url)
    const weaponId = getWeaponIdFromHash(hash)
    return { name, id: weaponId, img: getWeaponImagePath(weaponId) }
  })
}

// 解析波次特殊武器
const parseWaveSpecials = (wave) => {
  const ids = safeParse(wave.special_weapons, [])
  const names = safeParse(wave.special_weapon_names, [])
  return ids.map((rawId, i) => {
    // rawId 格式: "SpecialWeapon-20012" 或直接是数字
    const match = String(rawId).match(/(\d+)$/)
    const numericId = match ? parseInt(match[1], 10) : null
    return {
      id: numericId,
      name: names[i] || '',
      img: numericId ? getSpecialWeaponImagePath(numericId) : ''
    }
  }).filter(sp => sp.img)
}

// 生成波浪 SVG 路径
const getWavePath = (level) => {
  let baseY
  if (level === 2) baseY = 50      // 满潮: 覆盖 50%
  else if (level === 1) baseY = 65 // 普通: 覆盖 35%
  else baseY = 80                   // 干潮: 覆盖 20%
  const amplitude = 3
  let path = `M 0 ${baseY}`
  for (let i = 0; i < 4; i++) {
    path += ` q 6.25 -${amplitude} 12.5 0 t 12.5 0`
  }
  path += ` V 100 H 0 Z`
  return path
}

// 判断波次是否成功
const isWaveClear = (wave) => {
  if (!wave.deliver_norm) {
    // EX 波次：根据 boss_defeated 判断
    return coop.value?.boss_defeated === 1
  }
  return (wave.team_deliver_count || 0) >= wave.deliver_norm
}

// 计算总金蛋数
const totalGoldenEggs = computed(() => {
  if (!coop.value?.waves) return 0
  return coop.value.waves.reduce((sum, w) => sum + (w.team_deliver_count || 0), 0)
})

// 均匀分行：上行数量 >= 下行数量
const balanceRows = (items, maxPerRow) => {
  const total = items.length
  if (total === 0) return []
  if (total <= maxPerRow) return [items]
  const rows = Math.ceil(total / maxPerRow)
  const baseCount = Math.floor(total / rows)
  const extra = total % rows
  const result = []
  let index = 0
  for (let i = 0; i < rows; i++) {
    const count = baseCount + (i < extra ? 1 : 0)
    result.push(items.slice(index, index + count))
    index += count
  }
  return result
}

// 敌人统计：按照下发数据显示，按 ID 排序，鲑鱼和 Boss 分开
const enemyStats = computed(() => {
  if (!coop.value?.enemies) return []
  return [...coop.value.enemies]
    .map(e => ({
      ...e,
      numericId: parseCoopEnemyId(e.enemy_id)
    }))
    .sort((a, b) => a.numericId - b.numericId)
})

// 敌人按行分组（每行最多6个）
const enemyRows = computed(() => balanceRows(enemyStats.value, 6))

const bossStats = computed(() => {
  if (!coop.value?.bosses) return []
  return [...coop.value.bosses]
    .map(b => ({
      ...b,
      numericId: parseCoopEnemyId(b.boss_id)
    }))
    .sort((a, b) => a.numericId - b.numericId)
})

const hasScales = (c) => c.scale_gold > 0 || c.scale_silver > 0 || c.scale_bronze > 0
</script>

<template>
  <div class="coop-detail-view">
    <div class="nav-bar">
      <button @click="goBack" class="btn-back">← 返回</button>
    </div>

    <div v-if="coop" class="detail-card">
      <!-- Header -->
      <div class="coop-header" :style="{ backgroundImage: `url(${getStageImg(coop.stage_id)})` }">
        <div class="header-overlay">
          <div class="header-top">
            <span class="rule-badge" :class="coop.rule.toLowerCase()">{{ getRuleName(coop.rule) }}</span>
            <span class="danger-rate">{{ formatDangerRate(coop.danger_rate) }}</span>
            <span class="stage-name">{{ coop.stage_name }}</span>
            <span class="played-time">{{ formatDateTime(coop.played_time) }}</span>
          </div>
          <div class="header-center">
            <div class="result-badge" :class="{ clear: coop.result_wave === 0 }">
              {{ formatResultWave(coop.result_wave) }}
            </div>
          </div>
          <div class="header-bottom">
            <div class="grade-info">
              <span class="grade-name">{{ coop.after_grade_name }}</span>
              <span class="grade-point">{{ coop.after_grade_point }}p</span>
            </div>
            <div class="job-scores" v-if="coop.job_score || coop.job_point">
              <span class="job-score" v-if="coop.job_score">得分 {{ coop.job_score }}</span>
              <span class="job-rate" v-if="coop.job_rate">x{{ coop.job_rate?.toFixed(2) }}</span>
              <span class="job-bonus" v-if="coop.job_bonus">+{{ coop.job_bonus }}</span>
              <span class="job-point" v-if="coop.job_point">= {{ coop.job_point }}p</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Bar -->
      <div class="summary-bar">
        <div class="summary-left">
          <div class="total-eggs">
            <img :src="'/static/coop/golden_egg.png'" class="egg-icon" />
            <span>x{{ totalGoldenEggs }}</span>
          </div>
          <div class="scales-group" v-if="hasScales(coop)">
            <div class="scale-item" v-if="coop.scale_gold">
              <img :src="'/static/coop/scale_gold.png'" />x{{ coop.scale_gold }}
            </div>
            <div class="scale-item" v-if="coop.scale_silver">
              <img :src="'/static/coop/scale_silver.png'" />x{{ coop.scale_silver }}
            </div>
            <div class="scale-item" v-if="coop.scale_bronze">
              <img :src="'/static/coop/scale_bronze.png'" />x{{ coop.scale_bronze }}
            </div>
          </div>
          <div class="boss-result" v-if="coop.boss_id">
            <img :src="getEnemyImagePath(parseCoopEnemyId(coop.boss_id))" class="boss-icon" :class="{ defeated: coop.boss_defeated }" />
            <span class="boss-status" :class="{ success: coop.boss_defeated }">
              {{ coop.boss_defeated ? '击破!' : '失败' }}
            </span>
          </div>
        </div>
        <div class="summary-right">
          <div class="smell-meter">
            <div class="meter-bar">
              <div class="meter-fill" :style="{ width: `${((coop.smell_meter || 0) / 5) * 100}%` }"></div>
            </div>
            <span class="meter-val">{{ coop.smell_meter || 0 }}/5</span>
          </div>
        </div>
      </div>

      <!-- Wave Details -->
      <div class="section-card wave-section">
        <h3 class="section-title">波次详情</h3>
        <div class="wave-container">
          <div v-for="w in coop.waves" :key="w.wave_number" class="wave-column">
            <!-- 数据框 -->
            <div
              class="wave-card"
              :class="{
                'is-clear': isWaveClear(w),
                'is-fail': !isWaveClear(w),
                'is-ex': !w.deliver_norm
              }"
            >
              <!-- 波浪背景层 -->
              <svg class="wave-bg" viewBox="0 0 100 100" preserveAspectRatio="none">
                <path :d="getWavePath(w.water_level)" class="wave-path" />
              </svg>
              <div v-if="!isWaveClear(w)" class="fail-overlay"></div>

              <!-- GJ/NG 徽章 -->
              <div class="wave-badge" :class="isWaveClear(w) ? 'badge-gj' : 'badge-ng'">
                {{ isWaveClear(w) ? 'GJ!' : 'NG' }}
              </div>

              <!-- 波次标签 -->
              <div class="wave-label" :class="{ 'is-ex-label': !w.deliver_norm }">
                {{ !w.deliver_norm ? 'EX-WAVE' : `WAVE ${w.wave_number}` }}
              </div>

              <!-- 配额栏（黑底白字） -->
              <div class="quota-bar">
                <template v-if="w.deliver_norm">
                  <span class="deliver-num">{{ w.team_deliver_count || 0 }}</span>
                  <span class="divider">/</span>
                  <span class="quota-num">{{ w.deliver_norm }}</span>
                </template>
                <span v-else class="boss-name">{{ coop.boss_name || '头目联合' }}</span>
              </div>

              <!-- 水位 -->
              <div class="water-level-text">{{ getWaterLevelName(w.water_level) }}</div>

              <!-- 事件名称 -->
              <div class="event-text">{{ w.event_name || '-' }}</div>

              <!-- 出现蛋数 -->
              <div class="pop-section">
                <div class="pop-row">
                  <img :src="'/static/coop/golden_egg.png'" class="pop-icon" />
                  <span class="pop-count">{{ w.golden_pop_count || 0 }}</span>
                </div>
                <div class="pop-label">出现数量</div>
              </div>
            </div>

            <!-- 特殊武器（数据框外） -->
            <div class="wave-specials">
              <img v-for="(sp, i) in parseWaveSpecials(w)" :key="i" :src="sp.img" :title="sp.name" class="special-icon" />
            </div>
          </div>
        </div>
      </div>

      <!-- Player List -->
      <div class="section-card">
        <h3 class="section-title">队员数据</h3>
        <div class="player-list">
          <div v-for="p in coop.players" :key="p.player_order" class="player-card" :class="{ 'is-myself': p.is_myself === 1 }">
            <div class="player-main">
              <div class="player-info">
                <div v-if="p.byname" class="player-byname">{{ p.byname }}</div>
                <div class="player-name">
                  {{ p.name }}<span v-if="p.name_id" class="name-id">#{{ p.name_id }}</span>
                </div>
              </div>
              <div class="weapons-list">
                <img v-for="(w, i) in parsePlayerWeapons(p)" :key="i" :src="w.img" :title="w.name" class="weapon-icon" />
                <img v-if="p.special_weapon_id" :src="getSpecialWeaponImagePath(p.special_weapon_id)" :title="p.special_weapon_name" class="special-icon" />
              </div>
              <div class="player-stats">
                <div class="stat-item" title="巨大鲑鱼击倒">
                  <span class="stat-label">巨大鲑鱼</span>
                  <span class="stat-val">x{{ p.defeat_enemy_count }}</span>
                </div>
                <div class="stat-item" title="金鲑鱼卵">
                  <img :src="'/static/coop/golden_egg.png'" class="stat-icon" />
                  <span class="stat-val golden">x{{ p.golden_deliver_count }} <small>&lt;{{ p.golden_assist_count }}&gt;</small></span>
                </div>
                <div class="stat-item" title="鲑鱼卵">
                  <img :src="'/static/coop/power_egg.png'" class="stat-icon" />
                  <span class="stat-val">x{{ p.deliver_count }}</span>
                </div>
                <div class="stat-item rescue" title="救援/被救">
                  <img :src="getSpeciesImagePath(p.species, 'rescues')" class="species-icon" />
                  <span class="stat-val rescue-val">x{{ p.rescue_count }}</span>
                  <span class="sep">/</span>
                  <img :src="getSpeciesImagePath(p.species, 'rescued')" class="species-icon" />
                  <span class="stat-val rescued-val">x{{ p.rescued_count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Enemy Stats -->
      <div class="section-card">
        <h3 class="section-title">已击倒的巨大鲑鱼</h3>
        <div class="enemy-stats-grid">
          <template v-if="enemyRows.length">
            <div v-for="(row, rowIdx) in enemyRows" :key="rowIdx" class="enemy-row">
              <div v-for="e in row" :key="e.enemy_id" class="enemy-item">
                <img :src="getEnemyImagePath(e.numericId)" class="enemy-icon" />
                <div class="enemy-counts">
                  <span class="defeat-main">{{ e.team_defeat_count }}<span class="defeat-self">（{{ e.defeat_count }}）</span></span>
                  <span class="pop-count">/ {{ e.pop_count }}</span>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="no-data">暂无敌人数据</div>
        </div>
        <div class="section-note" v-if="enemyRows.length">*括号内的数字为自己击倒的数量</div>
      </div>

      <!-- Boss Stats -->
      <div class="section-card" v-if="bossStats.length || coop.boss_id">
        <h3 class="section-title">Boss 击倒</h3>
        <div class="enemy-stats-grid">
          <!-- 头目联合：显示 bosses 数组 -->
          <div class="enemy-list" v-if="bossStats.length">
            <div v-for="b in bossStats" :key="b.boss_id" class="enemy-item boss">
              <img :src="getEnemyImagePath(b.numericId)" class="enemy-icon" />
              <div class="enemy-counts">
                <span class="defeat-count" :class="{ success: b.has_defeat_boss }">{{ b.has_defeat_boss ? '击破!' : '失败' }}</span>
              </div>
            </div>
          </div>
          <!-- 普通打工：显示主表的 boss_id 和 boss_defeated -->
          <div class="enemy-list" v-else-if="coop.boss_id">
            <div class="enemy-item boss">
              <img :src="getEnemyImagePath(parseCoopEnemyId(coop.boss_id))" class="enemy-icon" />
              <div class="enemy-counts">
                <span class="defeat-count" :class="{ success: coop.boss_defeated }">{{ coop.boss_defeated ? '击破!' : '失败' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="empty-state">加载中...</div>
    <div v-else-if="error" class="empty-state error">{{ error }}</div>
    <div v-else class="empty-state">未找到打工记录</div>
  </div>
</template>

<style scoped>
.coop-detail-view {
  --coop-orange: #FF5600;
  --coop-green: #41B923;
  font-family: 'M PLUS Rounded 1c', -apple-system, sans-serif;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.nav-bar { margin-bottom: 16px; }

.btn-back {
  background: none;
  border: 2px solid #333;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 14px;
  font-weight: 700;
  color: #333;
  cursor: pointer;
}
.btn-back:hover { background: #333; color: #EAFF3D; }

.detail-card {
  background: #fff;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

/* Header */
.coop-header {
  position: relative;
  height: 180px;
  background-size: cover;
  background-position: center;
}

.header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.5));
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #fff;
}

.header-top {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.rule-badge {
  padding: 3px 10px;
  border-radius: 4px;
  background: var(--coop-orange);
  font-weight: 700;
  font-size: 12px;
}
.rule-badge.big_run { background: #603BFF; }
.rule-badge.team_contest { background: #E8C400; color: #333; }

.danger-rate { font-weight: 700; color: #EAFF3D; }
.stage-name { font-weight: 600; color: #EAFF3D; }
.played-time { margin-left: auto; opacity: 0.8; }

.header-center {
  display: flex;
  justify-content: center;
}

.result-badge {
  padding: 8px 28px;
  border-radius: 24px;
  background: #E60012;
  color: #fff;
  font-weight: 900;
  font-size: 24px;
}
.result-badge.clear { background: var(--coop-green); }

.header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grade-info { font-weight: 700; }
.grade-name { color: #EAFF3D; font-size: 16px; }
.grade-point { color: rgba(255,255,255,0.7); font-size: 13px; margin-left: 4px; }

.job-scores {
  display: flex;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  background: rgba(0,0,0,0.4);
  padding: 6px 12px;
  border-radius: 8px;
}
.job-score { color: #fff; }
.job-rate { color: #EAFF3D; }
.job-bonus { color: var(--coop-green); }
.job-point { color: #fff; }

/* Summary Bar */
.summary-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: linear-gradient(135deg, #42211A 0%, #26120F 100%);
  color: #fff;
}

.summary-left, .summary-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.total-eggs {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 18px;
  color: #FFD700;
}
.total-eggs .egg-icon { width: 28px; height: 28px; }

.scales-group { display: flex; gap: 10px; }
.scale-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  font-weight: 700;
}
.scale-item img { width: 20px; height: 20px; }

.smell-meter {
  display: flex;
  align-items: center;
  gap: 8px;
}
.meter-bar {
  width: 80px;
  height: 10px;
  background: #444;
  border-radius: 5px;
  overflow: hidden;
}
.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--coop-orange), #EAFF3D);
}
.meter-val { font-size: 13px; font-weight: 700; }

.boss-result {
  display: flex;
  align-items: center;
  gap: 6px;
}
.boss-icon {
  width: 32px;
  height: 32px;
  opacity: 0.4;
}
.boss-icon.defeated { opacity: 1; }
.boss-status { font-size: 13px; font-weight: 700; color: #ff6b6b; }
.boss-status.success { color: var(--coop-green); }

/* Section Card */
.section-card {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}
.section-card:last-child { border-bottom: none; }

.section-title {
  font-size: 16px;
  font-weight: 800;
  color: #333;
  margin: 0 0 16px;
  padding-left: 12px;
  border-left: 4px solid var(--coop-orange);
}

/* Wave Section */
.wave-section {
  background: #fff;
  padding: 20px;
}

.wave-container {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.wave-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 90px;
}

.wave-card {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-radius: 8px;
  padding: 6px 4px 8px;
  position: relative;
  overflow: visible;
  isolation: isolate;
  background: #DCE643;
  color: #1a1a1a;
}

/* 波浪背景 */
.wave-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  border-radius: 8px;
  overflow: hidden;
}

.wave-path {
  fill: rgba(100, 100, 100, 0.25);
  stroke: rgba(80, 80, 80, 0.4);
  stroke-width: 0.8;
  vector-effect: non-scaling-stroke;
}

/* 失败蒙版 */
.fail-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(80, 80, 80, 0.45);
  z-index: 1;
  pointer-events: none;
  border-radius: 8px;
}

/* EX 波次样式 */
.wave-card.is-ex {
  background: linear-gradient(180deg, #DCE643 0%, #BFC932 100%);
}

/* 内容层级 */
.wave-label, .quota-bar, .water-area, .wave-badge {
  z-index: 2;
  position: relative;
}

/* GJ/NG 徽章（波次卡片） */
.wave-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 9px;
  font-weight: 900;
  padding: 2px 5px;
  border-radius: 4px;
  transform: rotate(6deg);
  box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
  z-index: 10;
}

.badge-gj {
  background: #232323;
  color: #00FFCC;
}

.badge-ng {
  background: #232323;
  color: #FF505E;
}

/* 波次标签 */
.wave-label {
  font-weight: 800;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: -0.5px;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.wave-label.is-ex-label {
  color: #1a1a1a;
}

/* 配额栏（黑底白字） */
.quota-bar {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  width: calc(100% + 8px);
  margin: 0 -4px;
  padding: 4px 0;
  background: #1a1a1a;
  border: 2px solid #000;
  color: #fff;
}

.deliver-num {
  font-size: 13px;
  font-weight: 900;
}

.divider {
  font-size: 12px;
  opacity: 0.6;
  font-weight: 900;
}

.quota-num {
  font-size: 12px;
  font-weight: 700;
  opacity: 0.8;
}

.boss-name {
  font-size: 11px;
  font-weight: 900;
  color: #fff;
}

/* 水位区域 */
.water-area {
  position: relative;
  width: calc(100% + 8px);
  margin: 0 -4px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.water-area .wave-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.water-area .wave-path {
  fill: rgba(100, 100, 100, 0.25);
  stroke: rgba(80, 80, 80, 0.4);
  stroke-width: 0.8;
  vector-effect: non-scaling-stroke;
}

.water-area .fail-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(80, 80, 80, 0.45);
  z-index: 1;
  pointer-events: none;
}

/* 水位 */
.water-level-text {
  font-size: 12px;
  font-weight: 800;
  color: #1a1a1a;
  z-index: 2;
  position: relative;
}

/* 事件名称 */
.event-text {
  font-size: 11px;
  font-weight: 800;
  color: #1a1a1a;
  margin-top: 2px;
  z-index: 2;
  position: relative;
}

/* 出现蛋数 */
.pop-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 6px;
  z-index: 2;
  position: relative;
}

.pop-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.pop-icon {
  width: 14px;
  height: 14px;
}

.pop-count {
  font-size: 12px;
  font-weight: 400;
  color: #000;
}

.pop-label {
  font-size: 9px;
  color: #000000;
  margin-top: 1px;
}

/* Zone C: 特殊武器（数据框外） */
.wave-specials {
  display: flex;
  justify-content: center;
  gap: 2px;
  flex-wrap: wrap;
  min-height: 24px;
  margin-top: 4px;
  width: 100%;
}

.wave-specials .special-icon {
  width: 20px;
  height: 20px;
  background: #e0e0e0;
  border-radius: 50%;
  padding: 2px;
}

/* Player List */
.player-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.player-card {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 12px 16px;
  transition: all 0.2s;
}
.player-card:hover { background: #efefef; }
.player-card.is-myself {
  background: #EAFF3D;
  border: 2px solid #333;
}

.player-main {
  display: grid;
  grid-template-columns: 150px auto 1fr;
  align-items: center;
  gap: 16px;
}

.player-info { overflow: hidden; }
.player-byname {
  font-size: 10px;
  color: #666;
  font-weight: 600;
}
.player-name {
  font-weight: 700;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.name-id { font-size: 11px; color: #999; font-weight: 400; margin-left: 2px; }

.weapons-list {
  display: flex;
  gap: 6px;
  align-items: center;
}
.weapon-icon {
  width: 32px;
  height: 32px;
  background: #222;
  border-radius: 50%;
  padding: 3px;
}
.weapons-list .special-icon {
  width: 28px;
  height: 28px;
  margin-left: 4px;
}

.player-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}
.stat-label { color: #666; font-size: 11px; }
.stat-icon { width: 18px; height: 18px; }
.stat-val { color: #333; }
.stat-val.golden { color: #FFD700; }
.stat-val small { color: #888; font-size: 11px; }

.stat-item.rescue {
  display: flex;
  align-items: center;
  gap: 3px;
}
.species-icon { height: 20px; width: auto; }
.rescue-val { color: var(--coop-green); }
.rescued-val { color: #ff6b6b; }
.sep { color: #999; }

/* Enemy Stats Grid */
.enemy-stats-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.enemy-row {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.enemy-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.enemy-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  background: #f5f5f5;
  border-radius: 10px;
  min-width: 85px;
}
.enemy-item.boss { background: #ffebee; }

.enemy-item .enemy-icon {
  width: 36px;
  height: 36px;
}
.enemy-item.boss .enemy-icon {
  width: 42px;
  height: 42px;
}

.enemy-counts {
  display: flex;
  align-items: baseline;
  gap: 2px;
  white-space: nowrap;
}
.defeat-main {
  font-size: 13px;
  font-weight: 700;
  color: #333;
}
.defeat-self {
  font-size: 10px;
  font-weight: 600;
  color: #666;
}
.defeat-count {
  font-size: 13px;
  font-weight: 700;
  color: #333;
}
.defeat-count.success { color: var(--coop-green); }
.pop-count {
  font-size: 13px;
  font-weight: 700;
  color: #000000;
}

.section-note {
  margin-top: 12px;
  font-size: 11px;
  color: #999;
  text-align: right;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 13px;
}

/* States */
.empty-state {
  text-align: center;
  padding: 50px;
  color: #888;
}
.empty-state.error { color: #E60012; }
</style>
