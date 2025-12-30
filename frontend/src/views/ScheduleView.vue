<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { splatoonService, RULE_NAMES, MODE_NAMES } from '../api/splatoon'
import StageCard from '../components/StageCard.vue'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const activeTab = ref('regular')

const rawSchedules = ref(null)
const locale = ref(null)
const stageMap = ref({})
const userStats = ref({})
const bestWeapons = ref({})
const now = ref(new Date())
const showBackToTop = ref(false)
let timer = null

const TABS = [
  { id: 'regular', name: '一般比赛' },
  { id: 'bankara_challenge', name: '蛮颓(挑战)' },
  { id: 'bankara_open', name: '蛮颓(开放)' },
  { id: 'x', name: 'X比赛' },
  { id: 'event', name: '活动' },
  { id: 'coop', name: '打工' }
]

const loadData = async () => {
  try {
    loading.value = true
    error.value = ''

    const [sched, loc, stages, stats, weapons] = await Promise.all([
      splatoonService.getSchedules(),
      splatoonService.getLocale(),
      splatoonService.getStages(),
      splatoonService.getMyAllStageStats().catch(() => []),
      splatoonService.getMyBestWeapons().catch(() => ({}))
    ])

    rawSchedules.value = sched.data
    locale.value = loc
    bestWeapons.value = weapons

    if (Array.isArray(stages)) {
      stages.forEach(s => {
        stageMap.value[s.vs_stage_id] = s
      })
    }

    if (Array.isArray(stats)) {
      stats.forEach(s => {
        userStats.value[s.vs_stage_id] = s
      })
    }
  } catch (e) {
    console.error(e)
    error.value = '加载日程失败'
  } finally {
    loading.value = false
  }
}

const getStageName = (stage) => {
  if (locale.value?.stages?.[stage.id]?.name) {
    return locale.value.stages[stage.id].name
  }
  return stage.name
}

const getCoopStageName = (stage) => {
  if (locale.value?.stages?.[stage?.id]?.name) {
    return locale.value.stages[stage.id].name
  }
  return stage?.name || ''
}

const getBossName = (boss) => {
  if (locale.value?.bosses?.[boss?.id]?.name) {
    return locale.value.bosses[boss.id].name
  }
  return boss?.name || ''
}

const getWeaponName = (weapon) => {
  if (locale.value?.weapons?.[weapon?.__splatoon3ink_id]?.name) {
    return locale.value.weapons[weapon.__splatoon3ink_id].name
  }
  return weapon?.name || ''
}

const getEventName = (event) => {
  if (locale.value?.events?.[event?.id]?.name) {
    return locale.value.events[event.id].name
  }
  return event?.name || ''
}

const getRuleName = (rule) => {
  if (locale.value?.rules?.[rule?.id]?.name) {
    return locale.value.rules[rule.id].name
  }
  return RULE_NAMES[rule?.rule] || rule?.name || ''
}

const mapRuleToKey = (rule) => {
  const ruleMap = {
    'TURF_WAR': 'TURF_WAR',
    'AREA': 'AREA',
    'LOFT': 'LOFT',
    'GOAL': 'GOAL',
    'CLAM': 'CLAM',
  }
  return ruleMap[rule] || null
}

const getBestWeaponsForStage = (stageId, ruleKey, mode) => {
  if (!ruleKey) return []
  const key = `${stageId}_${ruleKey}_${mode}`
  return bestWeapons.value[key] || []
}

const handleScroll = () => {
  showBackToTop.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const currentSchedules = computed(() => {
  if (!rawSchedules.value) return []

  if (activeTab.value === 'coop') {
    return coopSchedules.value
  }

  if (activeTab.value === 'event') {
    return eventSchedules.value
  }

  let nodes = []
  let settingKey = ''
  let vsMode = 'REGULAR'

  if (activeTab.value === 'regular') {
    nodes = rawSchedules.value.regularSchedules?.nodes || []
    settingKey = 'regularMatchSetting'
    vsMode = 'REGULAR'
  } else if (activeTab.value.startsWith('bankara')) {
    nodes = rawSchedules.value.bankaraSchedules?.nodes || []
    settingKey = 'bankaraMatchSettings'
    vsMode = 'BANKARA'
  } else if (activeTab.value === 'x') {
    nodes = rawSchedules.value.xSchedules?.nodes || []
    settingKey = 'xMatchSetting'
    vsMode = 'X_MATCH'
  }

  return nodes.slice(0, 12).map(node => {
    const settings = node[settingKey]
    const matchSettings = Array.isArray(settings) ? settings : (settings ? [settings] : [])

    return {
      type: 'vs',
      startTime: new Date(node.startTime),
      endTime: new Date(node.endTime),
      matches: matchSettings.filter(Boolean).filter(setting => {
        if (activeTab.value === 'bankara_challenge') return (setting.bankaraMode || setting.mode) === 'CHALLENGE'
        if (activeTab.value === 'bankara_open') return (setting.bankaraMode || setting.mode) === 'OPEN'
        return true
      }).map(setting => {
        const ruleKey = mapRuleToKey(setting.vsRule?.rule)
        const bankaraMode = setting.bankaraMode || setting.mode
        const weaponMode = vsMode === 'BANKARA' ? (bankaraMode || 'CHALLENGE') : vsMode

        return {
          rule: setting.vsRule,
          ruleKey,
          mode: bankaraMode,
          weaponMode,
          stages: setting.vsStages?.map(s => ({
            id: s.vsStageId,
            rawId: s.id,
            name: getStageName(s),
            stats: userStats.value[s.vsStageId] || null
          })) || []
        }
      })
    }
  })
})

const coopSchedules = computed(() => {
  if (!rawSchedules.value?.coopGroupingSchedule) return []

  const nodes = rawSchedules.value.coopGroupingSchedule.regularSchedules?.nodes || []
  return nodes.slice(0, 6).map(node => ({
    type: 'coop',
    startTime: new Date(node.startTime),
    endTime: new Date(node.endTime),
    setting: node.setting,
    stage: node.setting?.coopStage,
    weapons: node.setting?.weapons || [],
    boss: node.setting?.boss
  }))
})

const eventSchedules = computed(() => {
  if (!rawSchedules.value?.eventSchedules) return []

  const nodes = rawSchedules.value.eventSchedules.nodes || []
  const result = []

  for (const node of nodes.slice(0, 4)) {
    const setting = node.leagueMatchSetting
    if (!setting) continue

    const periods = node.timePeriods || []
    const ruleKey = mapRuleToKey(setting.vsRule?.rule)

    result.push({
      type: 'event',
      event: setting.leagueMatchEvent,
      rule: setting.vsRule,
      ruleKey,
      periods: periods.slice(0, 6).map(p => ({
        startTime: new Date(p.startTime),
        endTime: new Date(p.endTime)
      })),
      stages: setting.vsStages?.map(s => ({
        id: s.vsStageId,
        rawId: s.id,
        name: getStageName(s),
        stats: userStats.value[s.vsStageId] || null
      })) || []
    })
  }
  return result
})

const formatTime = (date) => format(date, 'HH:mm')
const formatDate = (date) => format(date, 'MM/dd')
const formatDateWeekday = (date) => format(date, 'M/d EEE', { locale: zhCN })
const formatDateTime = (date) => format(date, 'MM/dd HH:mm')

const isNow = (start, end) => {
  return now.value >= start && now.value < end
}

onMounted(() => {
  loadData()
  timer = setInterval(() => {
    now.value = new Date()
  }, 60000)
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="schedule-view">
    <!-- 固定头部 -->
    <div class="sticky-header">
      <div class="nav-header">
        <button @click="router.push('/')" class="btn-back">← 返回</button>
        <h1>日程表</h1>
      </div>

      <div class="tabs-container">
        <div class="tabs">
          <button
            v-for="tab in TABS"
            :key="tab.id"
            class="tab-btn"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else-if="error" class="error">{{ error }}</div>

      <!-- 打工日程 -->
      <div v-else-if="activeTab === 'coop'" class="timeline">
        <div
          v-for="(slot, index) in coopSchedules"
          :key="index"
          class="time-slot coop-slot"
          :class="{ current: isNow(slot.startTime, slot.endTime) }"
        >
          <div class="time-header">
            <span class="date">{{ formatDateWeekday(slot.startTime) }}</span>
            <span class="time">{{ formatTime(slot.startTime) }} - {{ formatTime(slot.endTime) }}</span>
            <span v-if="isNow(slot.startTime, slot.endTime)" class="now-badge">进行中</span>
          </div>

          <div class="coop-card">
            <div class="coop-image-wrapper">
              <img v-if="slot.stage?.thumbnailImage?.url" :src="slot.stage.thumbnailImage.url" :alt="slot.stage.name" />
            </div>
            <div class="coop-info">
              <div class="coop-stage-name">{{ getCoopStageName(slot.stage) }}</div>
              <div v-if="slot.boss" class="coop-boss">
                <span class="coop-boss-label">BOSS</span>
                <span>{{ getBossName(slot.boss) }}</span>
              </div>
              <div class="coop-weapons">
                <template v-for="(weapon, wIdx) in slot.weapons" :key="wIdx">
                  <img
                    v-if="weapon?.image?.url"
                    :src="weapon.image.url"
                    :alt="weapon?.name || '随机武器'"
                    :title="getWeaponName(weapon) || '随机武器'"
                    class="coop-weapon-img"
                  />
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 活动日程 -->
      <div v-else-if="activeTab === 'event'" class="timeline">
        <div
          v-for="(event, index) in eventSchedules"
          :key="index"
          class="time-slot event-slot"
        >
          <div class="event-header">
            <span class="event-name">{{ getEventName(event.event) }}</span>
            <img v-if="event.ruleKey" :src="`/static/vs_rule/${event.ruleKey}.svg`" class="rule-icon" />
            <span class="rule-name">{{ getRuleName(event.rule) }}</span>
          </div>

          <div class="event-periods">
            <div
              v-for="(period, pIdx) in event.periods"
              :key="pIdx"
              class="period-badge"
              :class="{ current: isNow(period.startTime, period.endTime) }"
            >
              {{ formatDateTime(period.startTime) }} - {{ formatTime(period.endTime) }}
            </div>
          </div>

          <div class="stages-grid">
            <StageCard
              v-for="stage in event.stages"
              :key="stage.id"
              :stageId="stage.id"
              :name="stage.name"
              :stageMap="stageMap"
              :stats="stage.stats"
              :vsRule="event.ruleKey"
              :bestWeapons="getBestWeaponsForStage(stage.id, event.ruleKey, 'LEAGUE')"
            />
          </div>
        </div>
      </div>

      <!-- VS日程 -->
      <div v-else class="timeline">
        <div
          v-for="(slot, index) in currentSchedules"
          :key="index"
          class="time-slot"
          :class="{ current: isNow(slot.startTime, slot.endTime) }"
        >
          <div class="time-header">
            <span class="date">{{ formatDate(slot.startTime) }}</span>
            <span class="time">{{ formatTime(slot.startTime) }} - {{ formatTime(slot.endTime) }}</span>
            <span v-if="isNow(slot.startTime, slot.endTime)" class="now-badge">进行中</span>
          </div>

          <div class="matches">
            <div v-for="(match, mIdx) in slot.matches" :key="mIdx" class="match-group">
              <div class="match-header">
                <span v-if="match.mode" class="mode-badge" :class="match.mode.toLowerCase()">
                  {{ MODE_NAMES[match.mode] || match.mode }}
                </span>
                <img v-if="match.ruleKey" :src="`/static/vs_rule/${match.ruleKey}.svg`" class="rule-icon" />
                <span class="rule-name">{{ getRuleName(match.rule) }}</span>
              </div>
              <div class="stages-grid">
                <StageCard
                  v-for="stage in match.stages"
                  :key="stage.id"
                  :stageId="stage.id"
                  :name="stage.name"
                  :stageMap="stageMap"
                  :stats="stage.stats"
                  :vsRule="match.ruleKey"
                  :bestWeapons="getBestWeaponsForStage(stage.id, match.ruleKey, match.weaponMode)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部注解 -->
      <div v-if="!loading && !error && activeTab !== 'coop'" class="footer-note">
        <p>* 胜率数据来源于 NSO 官方统计</p>
        <p>* 推荐武器基于已同步的对战记录计算，需达到一定场次才会显示</p>
      </div>
    </div>

    <!-- 返回顶部按钮 -->
    <button
      class="back-to-top"
      :class="{ show: showBackToTop }"
      @click="scrollToTop"
      aria-label="回到顶部"
    >
      ↑
    </button>
  </div>
</template>

<style scoped>
.schedule-view {
  max-width: 700px;
  width: 100%;
  margin: 0 auto;
  position: relative;
}

/* 头部 */
.sticky-header {
  margin-bottom: 16px;
}

.nav-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.nav-header h1 {
  flex: 1;
  font-size: 18px;
  color: #333;
  margin: 0;
}

.btn-back {
  border: none;
  background: #f0f0f0;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 8px;
}

.btn-back:hover {
  background: #e0e0e0;
}

.tabs-container {
  overflow-x: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.tabs-container::-webkit-scrollbar {
  display: none;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: #f0f0f0;
  color: #666;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

.tab-btn:hover {
  background: #e0e0e0;
}

.tab-btn.active {
  background: #E60012;
  color: #fff;
}

/* 内容区域 */
.content {
  padding: 16px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #666;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top-color: #E60012;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  text-align: center;
  padding: 40px;
  color: #E60012;
  background: #fff5f5;
  border-radius: 12px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.time-slot {
  background: #fafafa;
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid #ddd;
}

.time-slot.current {
  border-left-color: #E60012;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.time-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.date {
  font-weight: 700;
  color: #333;
  font-size: 14px;
}

.time {
  color: #666;
  font-size: 14px;
}

.now-badge {
  background: #E60012;
  color: #fff;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.matches {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.match-group {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.match-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.mode-badge {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.mode-badge.challenge {
  background: #603BFF;
  color: #fff;
}

.mode-badge.open {
  background: #EAFF3D;
  color: #333;
}

.rule-name {
  font-weight: 700;
  color: #333;
  font-size: 14px;
}

.rule-icon {
  width: 20px;
  height: 20px;
}

.stages-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* Coop styles */
.coop-slot.current {
  border-left-color: #F75B28;
}

.coop-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.coop-image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #2c2c2c;
  overflow: hidden;
}

.coop-image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.coop-info {
  padding: 12px;
}

.coop-stage-name {
  font-weight: 700;
  color: #1a1a1a;
  font-size: 14px;
  margin-bottom: 8px;
}

.coop-boss {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #F75B28;
  font-weight: 600;
  margin-bottom: 8px;
}

.coop-boss-label {
  background: #F75B28;
  color: #fff;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: bold;
}

.coop-weapons {
  display: flex;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px dashed #eee;
}

.coop-weapon-img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  background: #f5f5f5;
  border-radius: 50%;
  padding: 4px;
}

/* Event styles */
.event-slot.current {
  border-left-color: #603BFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.event-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.event-name {
  font-weight: 700;
  color: #603BFF;
  font-size: 15px;
}

.event-periods {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.period-badge {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #f0f0f0;
  color: #666;
}

.period-badge.current {
  background: #603BFF;
  color: #fff;
}

/* Footer */
.footer-note {
  margin-top: 24px;
  padding: 12px 16px;
  background: #f8f8f8;
  border-radius: 8px;
  font-size: 11px;
  color: #888;
  line-height: 1.6;
}

.footer-note p {
  margin: 0;
}

/* Back to Top */
.back-to-top {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #E60012;
  color: white;
  border: none;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  opacity: 0;
  pointer-events: none;
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-to-top.show {
  opacity: 1;
  pointer-events: auto;
}

.back-to-top:hover {
  background: #cc0010;
}

@media (max-width: 500px) {
  .stages-grid {
    grid-template-columns: 1fr;
  }
  .coop-weapon-img {
    width: 32px;
    height: 32px;
  }
  .back-to-top {
    bottom: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
  }
}
</style>
