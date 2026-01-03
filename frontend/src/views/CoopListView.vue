<script setup>
defineOptions({ name: 'CoopListView' })

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
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
  safeParse
} from '../utils/coop'

const router = useRouter()

const coops = ref([])
const scales = ref(null)
const enemies = ref([])
const bosses = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const refreshing = ref(false)
const refreshStatus = ref('')
const PAGE_SIZE = 20

const startTimeLocal = ref('')
const endTimeLocal = ref('')
const showTimeDropdown = ref(false)
const timeFilterRef = ref(null)

const toISO8601Start = (localDateTime) => {
  if (!localDateTime) return null
  const date = new Date(localDateTime)
  date.setSeconds(0, 0)
  return date.toISOString()
}

const toISO8601End = (localDateTime) => {
  if (!localDateTime) return null
  const date = new Date(localDateTime)
  date.setSeconds(59, 999)
  return date.toISOString()
}

const getFilterParams = () => {
  const params = {}
  const startISO = toISO8601Start(startTimeLocal.value)
  const endISO = toISO8601End(endTimeLocal.value)
  if (startISO) params.start_time = startISO
  if (endISO) params.end_time = endISO
  return params
}

const loadCoops = async () => {
  loading.value = true
  hasMore.value = true
  try {
    const params = { ...getFilterParams(), limit: PAGE_SIZE, offset: 0 }
    const list = await splatoonService.getCoopList(params)
    coops.value = list || []
    hasMore.value = list.length >= PAGE_SIZE
  } catch (e) {
    console.error('Failed to load coops:', e)
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const params = { ...getFilterParams(), limit: PAGE_SIZE, offset: coops.value.length }
    const list = await splatoonService.getCoopList(params)
    if (list.length > 0) {
      coops.value = [...coops.value, ...list]
    }
    hasMore.value = list.length >= PAGE_SIZE
  } catch (e) {
    console.error('Failed to load more:', e)
  } finally {
    loadingMore.value = false
  }
}

const loadStats = async () => {
  try {
    const params = getFilterParams()
    const [scalesData, enemiesData, bossesData] = await Promise.all([
      splatoonService.getCoopScales(params),
      splatoonService.getCoopEnemies(params),
      splatoonService.getCoopBosses(params)
    ])
    scales.value = scalesData
    enemies.value = enemiesData || []
    bosses.value = bossesData || []
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

const loadData = async () => {
  await Promise.all([loadCoops(), loadStats()])
}

const refreshData = async () => {
  if (refreshing.value) return
  refreshing.value = true
  refreshStatus.value = ''
  try {
    refreshStatus.value = '刷新 Token...'
    await splatoonService.refreshToken()
    refreshStatus.value = '同步打工记录...'
    await splatoonService.refreshCoopDetails()
    refreshStatus.value = '加载数据...'
    await loadData()
    refreshStatus.value = '刷新完成'
    setTimeout(() => { refreshStatus.value = '' }, 2000)
  } catch (e) {
    console.error('Refresh failed:', e)
    refreshStatus.value = '刷新失败: ' + (e.message || '未知错误')
    setTimeout(() => { refreshStatus.value = '' }, 3000)
  } finally {
    refreshing.value = false
  }
}

watch([startTimeLocal, endTimeLocal], () => {
  loadData()
})

const handleClickOutside = (e) => {
  if (timeFilterRef.value && !timeFilterRef.value.contains(e.target)) {
    showTimeDropdown.value = false
  }
}

onMounted(() => {
  loadData()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const coopListRef = ref(null)
const handleScroll = (e) => {
  const el = e.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) {
    loadMore()
  }
}

const goToDetail = (id) => {
  router.push(`/coop/${id}`)
}

const getStageImg = (stageId) => {
  const numericId = parseCoopStageId(stageId)
  const name = getStageEnumName(numericId)
  return getStageBannerPath(name || 'Unknown')
}

const parseWeapons = (c) => {
  if (!c.myself) return []
  const images = safeParse(c.myself.images, {})
  const weaponNames = safeParse(c.myself.weapon_names, [])
  return weaponNames.map(name => {
    const url = images[name] || ''
    const hash = extractWeaponHashFromUrl(url)
    const weaponId = getWeaponIdFromHash(hash)
    return { name, id: weaponId, img: getWeaponImagePath(weaponId) }
  })
}

const hasScales = (c) => c.scale_gold > 0 || c.scale_silver > 0 || c.scale_bronze > 0

const clearTimeFilter = () => {
  startTimeLocal.value = ''
  endTimeLocal.value = ''
}

const hasTimeFilter = computed(() => startTimeLocal.value || endTimeLocal.value)

// 敌人分组 ID
const regularEnemyIds = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] // 普通敌人
const specialEnemyIds = [15, 17, 20] // 特殊鲑鱼: SakelienGolden, Sakedozer, SakeBigMouth
const bossIds = [23, 24, 25] // Boss: SakelienGiant, SakeRope, SakeJaw (排除 Triple, Random)

// 构建统计数据的辅助函数
const buildStats = (ids, dataSource, idField = 'enemy_id') => {
  const statsMap = new Map()
  dataSource.forEach(item => {
    const id = parseCoopEnemyId(item[idField])
    statsMap.set(id, { defeat_count: item.defeat_count, encounter_count: item.encounter_count })
  })
  return ids.map(id => ({
    enemy_id: `CoopEnemy-${id}`,
    defeat_count: statsMap.get(id)?.defeat_count || 0
  }))
}

// 普通敌人统计
const regularEnemyStats = computed(() => buildStats(regularEnemyIds, enemies.value))

// 特殊鲑鱼统计
const specialEnemyStats = computed(() => buildStats(specialEnemyIds, enemies.value))

// Boss 统计
const bossEnemyStats = computed(() => buildStats(bossIds, bosses.value, 'boss_id'))

// 计算占位符数量（3列网格）
const regularSpacerCount = computed(() => {
  const r = regularEnemyStats.value.length % 3
  return r === 0 ? 0 : 3 - r
})
const specialSpacerCount = computed(() => {
  const r = specialEnemyStats.value.length % 3
  return r === 0 ? 0 : 3 - r
})
</script>

<template>
  <div class="coop-page">
    <!-- LEFT PANEL: Coop List -->
    <div class="left-panel">
      <div class="coop-list" ref="coopListRef" @scroll="handleScroll">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <span>加载中...</span>
        </div>

        <template v-else>
          <div
            v-for="c in coops"
            :key="c.id"
            class="coop-card"
            @click="goToDetail(c.id)"
            @keydown.enter="goToDetail(c.id)"
            tabindex="0"
            role="button"
          >
            <!-- Card Header -->
            <div class="card-header" :style="{ backgroundImage: `url(${getStageImg(c.stage_id)})` }">
              <div class="header-overlay">
                <div class="header-top">
                  <span class="rule-badge" :class="c.rule.toLowerCase()">{{ getRuleName(c.rule) }}</span>
                  <span class="danger-rate">{{ formatDangerRate(c.danger_rate) }}</span>
                  <span class="stage-name">{{ c.stage_name }}</span>
                  <span class="played-time">{{ formatDateTime(c.played_time) }}</span>
                </div>
                <div class="header-main">
                  <!-- 左对齐: wave, 段位, 鳞片, boss -->
                  <div class="header-left">
                    <div class="result-badge" :class="{ clear: c.result_wave === 0 }">
                      {{ formatResultWave(c.result_wave) }}
                    </div>
                    <div class="grade-info">
                      <span class="grade-name">{{ c.after_grade_name }}</span>
                      <span class="grade-point">{{ c.after_grade_point }}p</span>
                    </div>
                    <div class="scales-rewards" v-if="hasScales(c)">
                      <div class="scale-item" v-if="c.scale_gold">
                        <img :src="'/static/coop/scale_gold.png'" alt="金鳞片" /> x{{ c.scale_gold }}
                      </div>
                      <div class="scale-item" v-if="c.scale_silver">
                        <img :src="'/static/coop/scale_silver.png'" alt="银鳞片" /> x{{ c.scale_silver }}
                      </div>
                      <div class="scale-item" v-if="c.scale_bronze">
                        <img :src="'/static/coop/scale_bronze.png'" alt="铜鳞片" /> x{{ c.scale_bronze }}
                      </div>
                    </div>
                    <div class="boss-info" v-if="c.boss_id">
                      <img :src="getEnemyImagePath(parseCoopEnemyId(c.boss_id))" class="boss-icon" :class="{ defeated: c.boss_defeated }" />
                      <span class="boss-status" :class="{ success: c.boss_defeated }">
                        {{ c.boss_defeated ? '击破!' : '失败' }}
                      </span>
                    </div>
                  </div>
                  <!-- 右对齐: 总鱼蛋数, 特殊槽 -->
                  <div class="header-right">
                    <div class="total-golden-eggs">
                      <img :src="'/static/coop/golden_egg.png'" class="golden-egg-icon" alt="金蛋" />
                      <span class="golden-egg-count">x{{ c.total_deliver_count || 0 }}</span>
                    </div>
                    <div class="smell-meter">
                      <div class="meter-bar">
                        <div class="meter-fill" :style="{ width: `${((c.smell_meter || 0) / 5) * 100}%` }"></div>
                      </div>
                      <span class="meter-val">{{ c.smell_meter || 0 }}/5</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Card Body -->
            <div class="card-body">

              <!-- Player Stats -->
              <div class="stats-row" v-if="c.myself">
                <div class="weapons-list">
                  <img v-for="(w, i) in parseWeapons(c)" :key="i" :src="w.img" :title="w.name" class="weapon-icon" />
                  <img v-if="c.myself.special_weapon_id" :src="getSpecialWeaponImagePath(c.myself.special_weapon_id)" class="special-icon" :title="c.myself.special_weapon_name" />
                </div>

                <div class="metrics">
                  <div class="metric" title="巨大鲑鱼击倒">
                    <span class="metric-label">巨大鲑鱼</span>
                    <span class="metric-val">x{{ c.myself.defeat_enemy_count }}</span>
                  </div>
                  <div class="metric" title="金鲑鱼卵">
                    <img :src="'/static/coop/golden_egg.png'" class="egg-icon" alt="金蛋" />
                    <span class="metric-val">x{{ c.myself.golden_deliver_count }} <small>&lt;{{ c.myself.golden_assist_count }}&gt;</small></span>
                  </div>
                  <div class="metric" title="鲑鱼卵">
                    <img :src="'/static/coop/power_egg.png'" class="egg-icon" alt="能量蛋" />
                    <span class="metric-val">x{{ c.myself.deliver_count }}</span>
                  </div>
                  <div class="metric rescue-metric" title="救援/被救">
                    <img :src="getSpeciesImagePath(c.myself.species, 'rescues')" class="species-icon" alt="救援" />
                    <span class="metric-val rescue">x{{ c.myself.rescue_count }}</span>
                    <span class="sep">/</span>
                    <img :src="getSpeciesImagePath(c.myself.species, 'rescued')" class="species-icon" alt="被救" />
                    <span class="metric-val rescued">x{{ c.myself.rescued_count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="coops.length === 0" class="empty-state">
            <p>暂无打工记录</p>
          </div>

          <div v-if="loadingMore" class="loading-more">加载更多...</div>
          <div v-if="!hasMore && coops.length > 0" class="no-more">没有更多了</div>
        </template>
      </div>
    </div>

    <!-- RIGHT PANEL: Sidebar -->
    <div class="right-panel">
      <!-- Refresh Section -->
      <div class="refresh-section">
        <button class="refresh-btn" :disabled="refreshing" @click="refreshData">
          <span class="refresh-icon" :class="{ spin: refreshing }">↻</span>
          <span>{{ refreshing ? '刷新中...' : '刷新数据' }}</span>
        </button>
        <div class="refresh-bar-wrapper" :class="{ show: !!refreshStatus }">
          <div class="refresh-bar-progress" :class="{ indeterminate: refreshing }"></div>
          <div class="refresh-bar-text">{{ refreshStatus }}</div>
        </div>
      </div>

      <!-- Time Filter (参考对战样式) -->
      <div class="time-filter" ref="timeFilterRef">
        <div class="filter-trigger" @click.stop="showTimeDropdown = !showTimeDropdown">
          <span class="filter-time-icon">TIME</span>
          <span class="filter-label">{{ hasTimeFilter ? '已筛选' : '时间筛选' }}</span>
          <button v-if="hasTimeFilter" class="clear-time-btn" @click.stop="clearTimeFilter">×</button>
          <span v-else class="filter-arrow">{{ showTimeDropdown ? '▲' : '▼' }}</span>
        </div>
        <div v-if="showTimeDropdown" class="filter-dropdown time-dropdown">
          <div class="time-input-group">
            <label class="time-label">开始时间</label>
            <input type="datetime-local" v-model="startTimeLocal" class="time-input" />
          </div>
          <div class="time-input-group">
            <label class="time-label">结束时间</label>
            <input type="datetime-local" v-model="endTimeLocal" class="time-input" />
          </div>
        </div>
      </div>

      <!-- Scales Stats -->
      <div class="stats-card" v-if="scales">
        <h3 class="card-title">鳞片统计</h3>
        <div class="scale-stats">
          <div class="scale-stat">
            <img :src="'/static/coop/scale_gold.png'" alt="金鳞片" />
            <span>x {{ scales.scale_gold || 0 }}</span>
          </div>
          <div class="scale-stat">
            <img :src="'/static/coop/scale_silver.png'" alt="银鳞片" />
            <span>x {{ scales.scale_silver || 0 }}</span>
          </div>
          <div class="scale-stat">
            <img :src="'/static/coop/scale_bronze.png'" alt="铜鳞片" />
            <span>x {{ scales.scale_bronze || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Enemy & Boss Stats -->
      <div class="stats-card">
        <h3 class="card-title">已击倒的巨大鲑鱼</h3>
        <div class="enemy-stats">
          <!-- 普通敌人 -->
          <div v-for="e in regularEnemyStats" :key="e.enemy_id" class="enemy-stat">
            <img :src="getEnemyImagePath(parseCoopEnemyId(e.enemy_id))" class="enemy-icon" />
            <span class="enemy-count">x {{ e.defeat_count }}</span>
          </div>
          <!-- 占位符，使特殊鲑鱼从新行开始 -->
          <div v-for="n in regularSpacerCount" :key="'spacer1-' + n" class="enemy-stat spacer"></div>
          <!-- 特殊鲑鱼 -->
          <div v-for="e in specialEnemyStats" :key="e.enemy_id" class="enemy-stat special">
            <img :src="getEnemyImagePath(parseCoopEnemyId(e.enemy_id))" class="enemy-icon" />
            <span class="enemy-count">x {{ e.defeat_count }}</span>
          </div>
          <!-- 占位符，使 Boss 从新行开始 -->
          <div v-for="n in specialSpacerCount" :key="'spacer2-' + n" class="enemy-stat spacer"></div>
          <!-- Boss -->
          <div v-for="b in bossEnemyStats" :key="b.enemy_id" class="enemy-stat boss">
            <img :src="getEnemyImagePath(parseCoopEnemyId(b.enemy_id))" class="enemy-icon" />
            <span class="enemy-count">x {{ b.defeat_count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.coop-page {
  --coop-orange: #FF5600;
  --coop-green: #41B923;
  --coop-bg: #1a1a2e;
  display: flex;
  flex-direction: row;
  gap: 16px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 16px;
  height: calc(100vh - 70px);
  box-sizing: border-box;
}

/* Left Panel */
.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
}

.coop-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 8px;
  min-height: 0;
}

/* Coop Card */
.coop-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.coop-card:hover, .coop-card:focus-visible {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(255, 86, 0, 0.15);
  outline: none;
}

.coop-card:focus-visible {
  box-shadow: 0 0 0 3px var(--coop-orange);
}

.card-header {
  position: relative;
  height: 90px;
  background-size: cover;
  background-position: center;
}

.header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.4));
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.header-top {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-size: 13px;
}

.rule-badge {
  padding: 3px 10px;
  border-radius: 4px;
  background: #FF5600;
  font-weight: 700;
  font-size: 12px;
}

.rule-badge.big_run { background: #603BFF; }
.rule-badge.team_contest { background: #E8C400; color: #333; }

.danger-rate {
  font-weight: 700;
  color: #EAFF3D;
}

.played-time {
  margin-left: auto;
  opacity: 0.8;
}

.stage-name {
  font-weight: 600;
  color: #EAFF3D;
}

.header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-badge {
  padding: 4px 12px;
  border-radius: 20px;
  background: #E60012;
  color: #fff;
  font-weight: 800;
  font-size: 15px;
}

.result-badge.clear {
  background: #41B923;
}

.smell-meter {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px 10px;
  border-radius: 12px;
}

.meter-bar {
  width: 60px;
  height: 8px;
  background: #444;
  border-radius: 4px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, #FF5600, #EAFF3D);
  transition: width 0.3s;
}

.meter-val {
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

/* Card Body */
.card-body {
  padding: 14px 16px;
  background: linear-gradient(135deg, #42211A 0%, #26120F 100%);
}

.grade-info {
  font-weight: 700;
  color: #fff;
  font-size: 12px;
}

.grade-name {
  color: #EAFF3D;
}

.grade-point {
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
  margin-left: 2px;
}

.scales-rewards {
  display: flex;
  gap: 8px;
}

.scale-item {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.scale-item img {
  width: 16px;
  height: 16px;
}

.boss-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.boss-icon {
  width: 24px;
  height: 24px;
  opacity: 0.4;
  transition: opacity 0.2s;
}

.boss-icon.defeated {
  opacity: 1;
}

.boss-status {
  font-size: 11px;
  font-weight: 700;
  color: #ff6b6b;
}

.boss-status.success {
  color: #41B923;
}

.total-golden-eggs {
  display: flex;
  align-items: center;
  gap: 4px;
}

.golden-egg-icon {
  width: auto;
  height: 20px;
}

.golden-egg-count {
  font-size: 12px;
  font-weight: 700;
  color: #FFD700;
}

/* Stats Row */
.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.weapons-list {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.weapon-icon {
  width: 34px;
  height: 34px;
  background: #222;
  border-radius: 50%;
  padding: 4px;
}

.special-icon {
  width: 30px;
  height: 30px;
  margin-left: 6px;
}

.metrics {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.metric {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

.metric .label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
}

.metric-label {
  color: rgba(255, 255, 255, 0.8);
}

.egg-icon {
  width: auto;
  height: 18px;
}

.metric .val {
  min-width: 28px;
  text-align: right;
  display: inline-block;
}

.metric small {
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
}

.rescue-metric {
  display: flex;
  align-items: center;
  gap: 4px;
}

.species-icon {
  width: auto;
  height: 22px;
}

.metric-val.rescue {
  color: #41B923;
}

.metric-val.rescued {
  color: #ff6b6b;
}

.sep {
  color: rgba(255, 255, 255, 0.4);
}

/* Right Panel */
.right-panel {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 4px;
}

/* Refresh Section */
.refresh-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: #FF5600;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #e64d00;
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.refresh-icon {
  font-size: 18px;
}

.refresh-icon.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.refresh-bar-wrapper {
  height: 0;
  overflow: hidden;
  transition: height 0.3s ease;
  border-radius: 6px;
  position: relative;
  background: linear-gradient(90deg, #FF5600, #ff8c4d);
}

.refresh-bar-wrapper.show {
  height: 28px;
}

.refresh-bar-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
}

.refresh-bar-progress.indeterminate {
  background: repeating-linear-gradient(
    90deg,
    #FF5600 0%,
    #ff8c4d 50%,
    #FF5600 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s linear infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.refresh-bar-text {
  position: relative;
  width: 100%;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Time Filter */
.time-filter {
  position: relative;
}

.time-filter .filter-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.time-filter .filter-trigger:hover {
  border-color: #FF5600;
}

.filter-time-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FF5600;
  color: #fff;
  font-size: 8px;
  font-weight: 900;
  border-radius: 6px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.filter-arrow {
  margin-left: auto;
  font-size: 10px;
  color: #888;
}

.clear-time-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FF5600;
  color: #fff;
  border-radius: 50%;
  border: none;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  margin-left: auto;
}

.clear-time-btn:hover {
  background: #E60012;
}

.filter-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  margin-top: 4px;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Filter Card */
.filter-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.filter-title {
  font-weight: 700;
  color: #333;
}

.clear-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #E60012;
  color: #fff;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.time-dropdown {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-label {
  font-size: 11px;
  color: #888;
  font-weight: 600;
}

.time-input {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  font-family: inherit;
}

.time-input:focus {
  outline: none;
  border-color: #FF5600;
}

/* Stats Card */
.stats-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 14px;
  font-weight: 700;
  color: #333;
  margin-bottom: 14px;
}

.scale-stats {
  display: flex;
  justify-content: space-around;
}

.scale-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  color: #333;
}

.scale-stat img {
  width: 36px;
  height: 36px;
}

.enemy-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.enemy-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.enemy-stat.spacer {
  visibility: hidden;
}

.enemy-stat.boss .enemy-icon {
  width: 36px;
  height: 36px;
}

.enemy-stat.special .enemy-icon {
  width: 36px;
  height: 36px;
}

.enemy-icon {
  width: 32px;
  height: 32px;
}

.enemy-count {
  font-size: 11px;
  font-weight: 700;
  color: #333;
}

.enemy-encounter {
  font-size: 11px;
  color: #888;
}

/* States */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #666;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #f0f0f0;
  border-top-color: #FF5600;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.loading-more, .no-more {
  text-align: center;
  padding: 16px;
  color: #888;
  font-size: 13px;
}

.loading-more {
  color: #FF5600;
  font-weight: 600;
}

/* Responsive */
@media (max-width: 900px) {
  .coop-page {
    flex-direction: column;
  }

  .right-panel {
    width: 100%;
    order: -1;
  }
}
</style>
