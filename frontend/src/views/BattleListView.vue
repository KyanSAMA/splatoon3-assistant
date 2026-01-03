<script setup>
defineOptions({ name: 'BattleListView' })

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { rgbaToCSS } from '../mocks/battles.js'
import { splatoonService } from '../api/splatoon'
import { formatDateTime } from '../utils/timezone'

const router = useRouter()

const activeTab = ref('ALL')
const tabs = [
  { label: '全部', value: 'ALL', modeKey: null },
  { label: '涂地', value: 'REGULAR', modeKey: 'REGULAR' },
  { label: '蛮颓挑战', value: 'BANKARA_CHALLENGE', modeKey: 'BANKARA_CHALLENGE' },
  { label: '蛮颓开放', value: 'BANKARA_OPEN', modeKey: 'BANKARA_OPEN' },
  { label: 'X比赛', value: 'X_MATCH', modeKey: 'X_MATCH' },
  { label: '祭典', value: 'FEST', modeKey: 'FEST' },
  { label: '活动', value: 'LEAGUE', modeKey: 'LEAGUE' },
  { label: '私房', value: 'PRIVATE', modeKey: 'PRIVATE' }
]

const battles = ref([])
const dashboard = ref(null)
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const refreshing = ref(false)
const refreshStatus = ref('')
const PAGE_SIZE = 20

const selectedWeaponId = ref('ALL')
const showWeaponDropdown = ref(false)

// 时间筛选
const startTimeLocal = ref('')
const endTimeLocal = ref('')
const showTimeDropdown = ref(false)

// 武器缓存（全量武器信息）
const mainWeapons = ref([])

// 用户使用过的武器 ID 列表（根据当前模式筛选）
const userWeaponIds = ref([])

// 地图缓存
const stages = ref([])

// 时间转换：本地时间 -> ISO8601（开始时间取分钟开始，结束时间取分钟结束）
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

// 构建筛选参数
const getFilterParams = () => {
  const params = {}
  if (activeTab.value === 'REGULAR') {
    params.vs_mode = 'REGULAR'
  } else if (activeTab.value === 'X_MATCH') {
    params.vs_mode = 'X_MATCH'
  } else if (activeTab.value === 'BANKARA_CHALLENGE') {
    params.vs_mode = 'BANKARA'
    params.bankara_mode = 'CHALLENGE'
  } else if (activeTab.value === 'BANKARA_OPEN') {
    params.vs_mode = 'BANKARA'
    params.bankara_mode = 'OPEN'
  } else if (activeTab.value === 'FEST') {
    params.vs_mode = 'FEST'
  } else if (activeTab.value === 'LEAGUE') {
    params.vs_mode = 'LEAGUE'
  } else if (activeTab.value === 'PRIVATE') {
    params.vs_mode = 'PRIVATE'
  }
  if (selectedWeaponId.value !== 'ALL') {
    params.weapon_id = selectedWeaponId.value
  }
  const startISO = toISO8601Start(startTimeLocal.value)
  const endISO = toISO8601End(endTimeLocal.value)
  if (startISO) params.start_time = startISO
  if (endISO) params.end_time = endISO
  return params
}

// 加载对战列表（重置）
const loadBattles = async () => {
  loading.value = true
  hasMore.value = true
  try {
    const params = { ...getFilterParams(), limit: PAGE_SIZE, offset: 0 }
    const list = await splatoonService.getBattleList(params)
    battles.value = list || []
    hasMore.value = list.length >= PAGE_SIZE
  } catch (e) {
    console.error('Failed to load battles:', e)
  } finally {
    loading.value = false
  }
}

// 加载更多（瀑布流）
const loadMore = async () => {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const params = { ...getFilterParams(), limit: PAGE_SIZE, offset: battles.value.length }
    const list = await splatoonService.getBattleList(params)
    if (list.length > 0) {
      battles.value = [...battles.value, ...list]
    }
    hasMore.value = list.length >= PAGE_SIZE
  } catch (e) {
    console.error('Failed to load more:', e)
  } finally {
    loadingMore.value = false
  }
}

// 加载 dashboard
const loadDashboard = async () => {
  try {
    const params = getFilterParams()
    dashboard.value = await splatoonService.getBattleDashboard(params)
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  }
}

// 加载武器列表（全量缓存）
const loadWeapons = async () => {
  mainWeapons.value = await splatoonService.getMainWeapons()
}

// 加载用户使用过的武器（根据当前模式筛选）
const loadUserWeapons = async () => {
  const params = getFilterParams()
  // 不传 weapon_id，只传模式筛选参数
  delete params.weapon_id
  userWeaponIds.value = await splatoonService.getUserWeapons(params)
}

// 加载地图列表（缓存）
const loadStages = async () => {
  stages.value = await splatoonService.getStages()
}

// 初始加载
const loadData = async () => {
  await Promise.all([loadBattles(), loadDashboard(), loadWeapons(), loadStages(), loadUserWeapons()])
}

// 刷新数据
const refreshData = async () => {
  if (refreshing.value) return
  refreshing.value = true
  refreshStatus.value = ''

  try {
    refreshStatus.value = '刷新 Token...'
    await splatoonService.refreshToken()

    refreshStatus.value = '同步对战记录...'
    await splatoonService.refreshBattleDetails()

    refreshStatus.value = '同步武器数据...'
    await splatoonService.refreshWeaponRecords()

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

// 监听模式变化 - 重新加载用户武器列表
watch(activeTab, async () => {
  // 重置武器选择
  selectedWeaponId.value = 'ALL'
  // 重新加载用户武器列表
  await loadUserWeapons()
  // 加载对战列表和仪表盘
  loadBattles()
  loadDashboard()
})

// 监听武器选择变化
watch(selectedWeaponId, () => {
  loadBattles()
  loadDashboard()
})

// 监听时间筛选变化 - 仅在关闭下拉框时触发
watch(showTimeDropdown, (newVal, oldVal) => {
  if (oldVal === true && newVal === false) {
    loadUserWeapons()
    loadBattles()
    loadDashboard()
  }
})

// 清空时间筛选
const clearTimeFilter = () => {
  startTimeLocal.value = ''
  endTimeLocal.value = ''
  loadUserWeapons()
  loadBattles()
  loadDashboard()
}

// 时间筛选显示文本
const timeFilterLabel = computed(() => {
  if (!startTimeLocal.value && !endTimeLocal.value) return '时间筛选'
  const formatLocal = (dt) => {
    if (!dt) return ''
    const d = new Date(dt)
    const m = (d.getMonth() + 1).toString().padStart(2, '0')
    const day = d.getDate().toString().padStart(2, '0')
    const h = d.getHours().toString().padStart(2, '0')
    const min = d.getMinutes().toString().padStart(2, '0')
    return `${m}/${day} ${h}:${min}`
  }
  const s = formatLocal(startTimeLocal.value)
  const e = formatLocal(endTimeLocal.value)
  if (s && e) return `${s} ~ ${e}`
  if (s) return `${s} ~`
  return `~ ${e}`
})

// 点击外部关闭下拉框
const weaponFilterRef = ref(null)
const timeFilterRef = ref(null)

const handleClickOutside = (e) => {
  if (weaponFilterRef.value && !weaponFilterRef.value.contains(e.target)) {
    showWeaponDropdown.value = false
  }
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

// 滚动加载
const battleListRef = ref(null)
const handleScroll = (e) => {
  const el = e.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) {
    loadMore()
  }
}

const getMyPlayer = (battle) => {
  const myTeam = battle.teams?.find(t => t.team_role === 'MY')
  return myTeam ? myTeam.players?.find(p => p.is_myself === 1) : null
}

// 根据 weapon_id 获取武器信息（从缓存）
const getWeaponInfo = (weaponId) => {
  return mainWeapons.value.find(w => String(w.code) === String(weaponId))
}

// 根据 weapon_id 获取武器名称
const getWeaponName = (weaponId) => {
  const weapon = getWeaponInfo(weaponId)
  return weapon?.zh_name || weaponId
}

// 根据 vs_stage_id 获取 stage code
const getStageCode = (vsStageId) => {
  const stage = stages.value.find(s => s.vs_stage_id === vsStageId)
  return stage?.code || vsStageId
}

// 根据 vs_stage_id 获取地图名称
const getStageName = (vsStageId) => {
  const stage = stages.value.find(s => s.vs_stage_id === vsStageId)
  return stage?.zh_name || ''
}

// 武器下拉选项（根据用户使用过的武器 ID 过滤）
const weaponOptions = computed(() => {
  if (!userWeaponIds.value.length) return []
  return userWeaponIds.value
    .map(id => {
      const weapon = mainWeapons.value.find(w => Number(w.code) === Number(id))
      return weapon ? { id: weapon.code, name: weapon.zh_name || weapon.code } : null
    })
    .filter(Boolean)
})

// 获取选中武器的名称
const selectedWeaponName = computed(() => {
  if (selectedWeaponId.value === 'ALL') return '全部武器'
  const weapon = mainWeapons.value.find(w => String(w.code) === String(selectedWeaponId.value))
  return weapon?.zh_name || selectedWeaponId.value
})

const getRuleIcon = (rule) => `/static/vs_rule/${rule}.svg`
const getWeaponImg = (code) => `/static/weapon/${code}.png`
const getSubWeaponImg = (code) => `/static/sub_weapon/${code}.png`
const getSpecialWeaponImg = (code) => `/static/special_weapon/${code}.png`
const getStageImg = (stageId) => `/static/stage_banner/${stageId}.png`
const getAwardIcon = (rank) => rank === 'GOLD' ? '/static/medal/IconMedal_00.png' : '/static/medal/IconMedal_01.png'

// 解析 JSON 字段
const parseJson = (val) => {
  if (!val) return null
  if (typeof val === 'object') return val
  try { return JSON.parse(val) } catch { return null }
}

const currentStats = computed(() => {
  if (dashboard.value?.stats) {
    return {
      win: dashboard.value.stats.win,
      lose: dashboard.value.stats.lose,
      rate: dashboard.value.stats.winRate
    }
  }
  return { win: 0, lose: 0, rate: '-' }
})

// Pie chart logic - sort by count, add Others
const pieColors = ['#EAFF3D', '#603BFF', '#E60012', '#00EBA7', '#F54E93', '#19D719', '#888']

const getPieData = (sourceData) => {
  if (!sourceData?.length) return []
  const sorted = [...sourceData].sort((a, b) => b.count - a.count)
  const top6 = sorted.slice(0, 6)
  const others = sorted.slice(6)
  const othersCount = others.reduce((acc, item) => acc + item.count, 0)
  const result = [...top6]
  if (othersCount > 0) {
    result.push({ name: '其他', count: othersCount, weapon_id: 'others' })
  }
  const total = result.reduce((acc, item) => acc + item.count, 0)
  return result.map((item, index) => ({
    ...item,
    percent: total > 0 ? (item.count / total) * 100 : 0,
    color: pieColors[index % pieColors.length]
  }))
}

const getConicGradient = (pieData) => {
  if (!pieData.length) return '#f0f0f0'
  let current = 0
  return `conic-gradient(${pieData.map(d => {
    const end = current + d.percent
    const segment = `${d.color} ${current}% ${end}%`
    current = end
    return segment
  }).join(', ')})`
}

const winPieData = computed(() => getPieData(dashboard.value?.opponentStatsWin))
const losePieData = computed(() => getPieData(dashboard.value?.opponentStatsLose))
const winTotal = computed(() => dashboard.value?.opponentWinTotal || 0)
const loseTotal = computed(() => dashboard.value?.opponentLoseTotal || 0)

const currentWinRanking = computed(() => dashboard.value?.opponentWinRates || [])
const currentLoseRanking = computed(() => dashboard.value?.opponentLoseRates || [])

// 队友统计（使用 dashboard 数据）
const teammateWinRanking = computed(() => dashboard.value?.teammateWinRates || [])
const teammateLoseRanking = computed(() => dashboard.value?.teammateLoseRates || [])

const formatDuration = (sec) => {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatTime = (iso) => formatDateTime(iso)

const getModeLabel = (battle) => {
  if (battle.vs_mode === 'BANKARA') {
    return battle.bankara_mode === 'CHALLENGE' ? '挑战' : '开放'
  }
  return { REGULAR: '涂地', X_MATCH: 'X赛', FEST: '祭典', LEAGUE: '活动', PRIVATE: '私房' }[battle.vs_mode] || battle.vs_mode
}

const getUdemaeColor = (udemae) => {
  if (!udemae) return '#888'
  if (udemae.includes('S+')) return '#F54E93'
  if (udemae.startsWith('S')) return '#603BFF'
  if (udemae.startsWith('A')) return '#00C2CB'
  if (udemae.startsWith('B')) return '#FF9F2C'
  return '#888'
}

const getRuleLabel = (rule) => {
  return { AREA: '区域', LOFT: '塔楼', GOAL: '鱼虎', CLAM: '蛤蜊', TURF_WAR: '涂地' }[rule] || rule
}

const getTeamsSorted = (battle) => {
  const myTeam = battle.teams?.find(t => t.team_role === 'MY')
  const otherTeam = battle.teams?.find(t => t.team_role === 'OTHER')
  return [myTeam, otherTeam]
}

const getColorBarStyle = (battle) => {
  const [t1, t2] = getTeamsSorted(battle)
  if (!t1 || !t2) return {}
  const s1 = t1.score ?? (t1.paint_ratio ? t1.paint_ratio * 100 : 50)
  const s2 = t2.score ?? (t2.paint_ratio ? t2.paint_ratio * 100 : 50)
  const total = s1 + s2 || 1
  const p1 = (s1 / total) * 100
  return { background: `linear-gradient(to right, ${rgbaToCSS(parseJson(t1.color))} ${p1}%, ${rgbaToCSS(parseJson(t2.color))} ${p1}%)` }
}

const getScoreDisplay = (team) => {
  if (team?.score != null) return team.score
  if (team?.paint_ratio != null) return Math.round(team.paint_ratio * 100) + '%'
  return '-'
}

const goToDetail = (id) => {
  router.push({ name: 'battle-detail', params: { id } })
}

const isLose = (judgement) => ['LOSE', 'DEEMED_LOSE', 'EXEMPTED_LOSE'].includes(judgement)
const getResultClass = (judgement) => judgement === 'WIN' ? 'WIN' : isLose(judgement) ? 'LOSE' : 'DRAW'
const getResultText = (judgement) => {
  if (judgement === 'WIN') return 'WIN!'
  if (judgement === 'DEEMED_LOSE') return 'LOSE(DEEMED)'
  if (judgement === 'EXEMPTED_LOSE') return 'LOSE(EXEMPTED)'
  if (judgement === 'LOSE') return 'LOSE'
  return 'DRAW'
}
</script>

<template>
  <div class="battle-page">
    <!-- LEFT PANEL: Battle List -->
    <div class="left-panel">
      <div class="battle-list" @scroll="handleScroll">
        <div
          v-for="battle in battles"
          :key="battle.id"
          class="battle-card"
          @click="goToDetail(battle.id)"
        >
          <div class="card-header" :style="{ backgroundImage: `url(${getStageImg(getStageCode(battle.vs_stage_id))})` }">
            <div class="header-overlay">
              <div class="mode-rule">
                <span class="mode-badge" :class="[battle.vs_mode.toLowerCase(), battle.bankara_mode?.toLowerCase()]">
                  {{ getModeLabel(battle) }}
                </span>
                <img :src="getRuleIcon(battle.vs_rule)" class="rule-icon" />
                <span class="rule-name">{{ getRuleLabel(battle.vs_rule) }}</span>
              </div>
              <div class="header-right">
                <span class="stage-name">{{ battle.stage?.zh_name }}</span>
                <span class="time">{{ formatTime(battle.played_time) }}</span>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div class="color-bar" :style="getColorBarStyle(battle)">
              <div class="score-overlay">
                <span class="score-val">{{ getScoreDisplay(getTeamsSorted(battle)[0]) }}</span>
                <div class="result-badge" :class="getResultClass(battle.judgement)">
                  {{ getResultText(battle.judgement) }}
                  <span v-if="battle.knockout === 'WIN' || battle.knockout === 'LOSE'" class="ko-badge">KO!</span>
                </div>
                <span class="score-val">{{ getScoreDisplay(getTeamsSorted(battle)[1]) }}</span>
              </div>
            </div>

            <div class="card-footer">
              <div class="footer-left" v-if="getMyPlayer(battle)">
                <div class="weapon-set">
                  <img :src="getWeaponImg(getMyPlayer(battle).weapon_id)" class="w-main" />
                  <img v-if="getWeaponInfo(getMyPlayer(battle).weapon_id)" :src="getSubWeaponImg(getWeaponInfo(getMyPlayer(battle).weapon_id).sub_weapon_code)" class="w-sub" />
                  <img v-if="getWeaponInfo(getMyPlayer(battle).weapon_id)" :src="getSpecialWeaponImg(getWeaponInfo(getMyPlayer(battle).weapon_id).special_weapon_code)" class="w-special" />
                </div>
                <div class="player-stats">
                  <span class="kda">
                    <span class="k">{{ getMyPlayer(battle).kill_count }}<span class="a">&lt;{{ getMyPlayer(battle).assist_count }}&gt;</span></span>
                    <span class="sep">/</span>
                    <span class="d">{{ getMyPlayer(battle).death_count }}</span>
                  </span>
                  <span class="paint-point">{{ getMyPlayer(battle).paint }}p</span>
                  <span class="sp-tag">SP{{ getMyPlayer(battle).special_count }}</span>
                </div>
              </div>
              <div class="footer-center">
                <span v-if="battle.vs_mode === 'BANKARA' && battle.udemae" class="stat-badge udemae" :style="{ background: getUdemaeColor(battle.udemae) }">
                  {{ battle.udemae }}
                </span>
                <div v-if="battle.vs_mode === 'BANKARA' && battle.bankara_mode === 'CHALLENGE' && battle.weapon_power && getMyPlayer(battle)" class="stat-badge power">
                  <img :src="getWeaponImg(getMyPlayer(battle).weapon_id)" class="power-icon-sm" />
                  <span class="power-val">{{ battle.weapon_power.toFixed(1) }}</span>
                </div>
                <div v-if="battle.vs_mode === 'BANKARA' && battle.bankara_mode === 'OPEN' && battle.bankara_power" class="stat-badge power open">
                  <span class="power-label">BP</span>
                  <span class="power-val">{{ battle.bankara_power.toFixed(1) }}</span>
                </div>
                <div v-if="battle.vs_mode === 'X_MATCH' && battle.x_power" class="stat-badge power x-match">
                  <span class="power-label">XP</span>
                  <span class="power-val">{{ battle.x_power.toFixed(1) }}</span>
                </div>
                <div v-if="battle.vs_mode === 'FEST' && battle.fest_power" class="stat-badge power fest">
                  <span class="power-label">FP</span>
                  <span class="power-val">{{ battle.fest_power.toFixed(1) }}</span>
                </div>
                <div v-if="battle.vs_mode === 'LEAGUE'" class="stat-badge power league">
                  <span class="power-label">LP</span>
                  <span class="power-val" v-if="battle.my_league_power">{{ battle.my_league_power.toFixed(1) }}</span>
                  <span class="power-val" v-else>-</span>
                </div>
                <span v-if="battle.vs_mode === 'LEAGUE' && battle.league_match_event_name" class="event-name">{{ battle.league_match_event_name }}</span>
              </div>
              <div class="footer-right">
                <div v-if="parseJson(battle.awards)?.length" class="list-awards">
                  <div v-for="(a, i) in parseJson(battle.awards)" :key="i" class="award-item">
                    <img :src="getAwardIcon(a.rank)" class="award-icon" />
                    <div class="tooltip">{{ a.name }}</div>
                  </div>
                </div>
                <span class="duration">{{ formatDuration(battle.duration) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="loadingMore" class="loading-more">加载中...</div>
        <div v-else-if="!hasMore && battles.length > 0" class="no-more">没有更多了</div>
      </div>
    </div>

    <!-- RIGHT PANEL: Stats & Controls -->
    <div class="right-panel">
      <!-- 1. Overall Stats -->
      <div class="stats-badge">
        <div class="stat-group win">
          <span class="label">WIN</span>
          <span class="value">{{ currentStats.win }}</span>
        </div>
        <div class="stat-divider">/</div>
        <div class="stat-group lose">
          <span class="label">LOSE</span>
          <span class="value">{{ currentStats.lose }}</span>
        </div>
        <div class="stat-rate">{{ currentStats.rate }}%</div>
      </div>

      <!-- 2. Mode Tabs -->
      <div class="mode-tabs-scroll">
        <div class="mode-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            :class="['mode-tab', tab.value, { active: activeTab === tab.value }]"
            @click="activeTab = tab.value"
          >
            <span class="tab-ink"></span>
            <span class="tab-text">{{ tab.label }}</span>
          </button>
          <button class="mode-tab refresh-btn" :class="{ refreshing: refreshing }" @click="refreshData" :disabled="refreshing">
            <span class="tab-text" :class="{ 'icon-spin': refreshing }">↻</span>
          </button>
        </div>
        <div class="refresh-bar-wrapper" :class="{ show: !!refreshStatus }">
          <div class="refresh-bar-progress" :class="{ indeterminate: refreshing }"></div>
          <div class="refresh-bar-text">{{ refreshStatus }}</div>
        </div>
      </div>

      <!-- Time Filter -->
      <div class="time-filter" ref="timeFilterRef">
        <div class="filter-trigger" @click.stop="showTimeDropdown = !showTimeDropdown">
          <span class="filter-time-icon">TIME</span>
          <span class="filter-label">{{ timeFilterLabel }}</span>
          <button v-if="startTimeLocal || endTimeLocal" class="clear-time-btn" @click.stop="clearTimeFilter">×</button>
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

      <!-- Weapon Filter -->
      <div class="weapon-filter" ref="weaponFilterRef">
        <div class="filter-trigger" @click.stop="showWeaponDropdown = !showWeaponDropdown">
          <img v-if="selectedWeaponId !== 'ALL'" :src="getWeaponImg(selectedWeaponId)" class="filter-weapon-icon" />
          <span v-else class="filter-all-icon">ALL</span>
          <span class="filter-label">{{ selectedWeaponName }}</span>
          <span class="filter-arrow">{{ showWeaponDropdown ? '▲' : '▼' }}</span>
        </div>
        <div v-if="showWeaponDropdown" class="filter-dropdown">
          <div class="filter-option" :class="{ active: selectedWeaponId === 'ALL' }" @click="selectedWeaponId = 'ALL'; showWeaponDropdown = false">
            <span class="option-all">ALL</span>
            <span class="option-name">全部武器</span>
          </div>
          <div v-for="w in weaponOptions" :key="w.id" class="filter-option" :class="{ active: selectedWeaponId === w.id }" @click="selectedWeaponId = w.id; showWeaponDropdown = false">
            <img :src="getWeaponImg(w.id)" class="option-icon" />
            <span class="option-name">{{ w.name }}</span>
          </div>
        </div>
      </div>

      <!-- 3. Win Pie Chart -->
      <div class="dashboard-card">
        <h3 class="card-title win">胜局中对手武器出场榜</h3>
        <div class="chart-layout">
          <div class="pie-chart-container">
            <div class="pie-chart" :style="{ background: getConicGradient(winPieData) }">
              <div class="chart-hole">
                <span class="total-label">Total</span>
                <span class="total-val">{{ winTotal }}</span>
              </div>
            </div>
          </div>
          <div class="chart-legend">
            <div v-for="item in winPieData" :key="item.weapon_id" class="legend-item">
              <span class="dot" :style="{ background: item.color }"></span>
              <img v-if="item.weapon_id !== 'others'" :src="getWeaponImg(item.weapon_id)" class="legend-icon" />
              <span class="name">{{ item.weapon_id === 'others' ? '其他' : getWeaponName(item.weapon_id) }}</span>
              <span class="count">x{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Lose Pie Chart -->
      <div class="dashboard-card">
        <h3 class="card-title lose">败局中对手武器出场榜</h3>
        <div class="chart-layout">
          <div class="pie-chart-container">
            <div class="pie-chart" :style="{ background: getConicGradient(losePieData) }">
              <div class="chart-hole">
                <span class="total-label">Total</span>
                <span class="total-val">{{ loseTotal }}</span>
              </div>
            </div>
          </div>
          <div class="chart-legend">
            <div v-for="item in losePieData" :key="item.weapon_id" class="legend-item">
              <span class="dot" :style="{ background: item.color }"></span>
              <img v-if="item.weapon_id !== 'others'" :src="getWeaponImg(item.weapon_id)" class="legend-icon" />
              <span class="name">{{ item.weapon_id === 'others' ? '其他' : getWeaponName(item.weapon_id) }}</span>
              <span class="count">x{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 5. Win Ranking -->
      <div class="dashboard-card">
        <h3 class="card-title win">对手武器克制榜</h3>
        <div class="ranking-bars">
          <div v-for="r in currentWinRanking.slice(0, 5)" :key="r.weapon_id" class="rank-bar win">
            <img :src="getWeaponImg(r.weapon_id)" class="rank-icon" />
            <div class="rank-info">
              <span class="rank-name">{{ getWeaponName(r.weapon_id) }}</span>
              <div class="progress-bg"><div class="progress-fill" :style="{ width: r.rate + '%' }"></div></div>
            </div>
            <span class="rank-val">{{ r.rate }}%<div class="tooltip">{{ r.win }}/{{ r.total }}</div></span>
          </div>
        </div>
      </div>

      <!-- 6. Lose Ranking -->
      <div class="dashboard-card">
        <h3 class="card-title lose">对手武器苦手榜</h3>
        <div class="ranking-bars">
          <div v-for="r in currentLoseRanking.slice(0, 5)" :key="r.weapon_id" class="rank-bar lose">
            <img :src="getWeaponImg(r.weapon_id)" class="rank-icon" />
            <div class="rank-info">
              <span class="rank-name">{{ getWeaponName(r.weapon_id) }}</span>
              <div class="progress-bg"><div class="progress-fill" :style="{ width: r.rate + '%' }"></div></div>
            </div>
            <span class="rank-val">{{ r.rate }}%<div class="tooltip">{{ r.lose }}/{{ r.total }}</div></span>
          </div>
        </div>
      </div>

      <!-- 7. Teammate Win Ranking -->
      <div class="dashboard-card">
        <h3 class="card-title win">最佳队友武器拍档</h3>
        <div class="ranking-bars">
          <div v-for="r in teammateWinRanking.slice(0, 5)" :key="r.weapon_id" class="rank-bar win">
            <img :src="getWeaponImg(r.weapon_id)" class="rank-icon" />
            <div class="rank-info">
              <span class="rank-name">{{ getWeaponName(r.weapon_id) }}</span>
              <div class="progress-bg"><div class="progress-fill" :style="{ width: r.rate + '%' }"></div></div>
            </div>
            <span class="rank-val">{{ r.rate }}%<div class="tooltip">{{ r.win }}/{{ r.total }}</div></span>
          </div>
        </div>
      </div>

      <!-- 8. Teammate Lose Ranking -->
      <div class="dashboard-card">
        <h3 class="card-title lose">最低契合度队友武器</h3>
        <div class="ranking-bars">
          <div v-for="r in teammateLoseRanking.slice(0, 5)" :key="r.weapon_id" class="rank-bar lose">
            <img :src="getWeaponImg(r.weapon_id)" class="rank-icon" />
            <div class="rank-info">
              <span class="rank-name">{{ getWeaponName(r.weapon_id) }}</span>
              <div class="progress-bg"><div class="progress-fill" :style="{ width: r.rate + '%' }"></div></div>
            </div>
            <span class="rank-val">{{ r.rate }}%<div class="tooltip">{{ r.lose }}/{{ r.total }}</div></span>
          </div>
        </div>
      </div>

      <div class="footer-note">* 胜率/败率数据仅统计遇到5次以上的数据</div>
    </div>
  </div>
</template>

<style scoped>
.battle-page {
  font-family: 'M PLUS Rounded 1c', -apple-system, sans-serif;
  display: flex;
  flex-direction: row;
  gap: 16px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 16px;
  height: calc(100vh - 70px);
  color: #333;
}

.left-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.right-panel {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 4px;
}

/* Stats Badge */
.stats-badge {
  background: #333;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 10px 24px;
  border-radius: 30px;
  box-shadow: 0 4px 0 rgba(0,0,0,0.2);
  transform: rotate(-1deg);
}

.stat-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.2;
}

.stat-group .label { font-size: 10px; font-weight: 700; opacity: 0.7; letter-spacing: 1px; }
.stat-group .value { font-size: 24px; font-weight: 900; }
.stat-group.win .value { color: #EAFF3D; }
.stat-group.lose .value { color: #FF6B6B; }
.stat-divider { font-size: 20px; color: #666; }
.stat-rate { font-size: 28px; font-weight: 900; color: #fff; text-shadow: 2px 2px 0 #603BFF; margin-left: 8px; }

/* Dashboard Card */
.dashboard-card {
  background: #fff;
  border-radius: 20px;
  padding: 14px;
  box-shadow: 0 4px 0 rgba(0,0,0,0.05);
  border: 2px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 13px;
  font-weight: 900;
  margin: 0 0 10px 0;
  text-transform: uppercase;
  display: flex;
  align-items: center;
}

.card-title.win::before {
  content: '';
  display: inline-block;
  width: 10px;
  height: 10px;
  background: #EAFF3D;
  border-radius: 50%;
  margin-right: 8px;
  box-shadow: 0 0 0 2px #333;
}

.card-title.lose::before {
  content: '';
  display: inline-block;
  width: 10px;
  height: 10px;
  background: #E60012;
  border-radius: 50%;
  margin-right: 8px;
  box-shadow: 0 0 0 2px #333;
}

/* Pie Chart */
.chart-layout {
  display: flex;
  gap: 10px;
  flex: 1;
  align-items: center;
}

.pie-chart-container {
  flex-shrink: 0;
}

.pie-chart {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  position: relative;
  border: 3px solid #fff;
  box-shadow: 0 3px 8px rgba(0,0,0,0.1);
}

.chart-hole {
  position: absolute;
  inset: 22%;
  background: #fff;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.total-label { font-size: 8px; color: #888; font-weight: 700; }
.total-val { font-size: 18px; font-weight: 900; line-height: 1; color: #333; }

.chart-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
}

.legend-item .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  flex-shrink: 0;
}

.legend-item .name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #555;
}

.legend-item .count { color: #999; font-size: 9px; }

/* Rankings */
.ranking-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rank-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.rank-icon {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.rank-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.rank-name {
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-bg {
  height: 5px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
}

.rank-bar.win .progress-fill { background: #19D719; }
.rank-bar.lose .progress-fill { background: #E60012; }

.rank-val {
  font-size: 10px;
  font-weight: 900;
  width: 28px;
  text-align: right;
  position: relative;
  cursor: pointer;
}

.rank-val:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

/* Mode Tabs */
.mode-tabs-scroll {
  overflow-x: auto;
  padding: 4px 4px 12px 4px;
  margin: 0 -4px;
  flex-shrink: 0;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  white-space: nowrap;
  flex-wrap: wrap;
}

.mode-tab {
  position: relative;
  padding: 8px 14px;
  background: #fff;
  border: 2px solid #eee;
  border-radius: 16px;
  font-weight: 900;
  font-size: 12px;
  color: #888;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  transform: rotate(-1deg);
}

.mode-tab:nth-child(even) { transform: rotate(1deg); }
.mode-tab:hover { transform: scale(1.05) rotate(0deg); z-index: 10; }

.mode-tab.active {
  border-color: transparent;
  color: #fff;
  transform: scale(1.08) rotate(-2deg);
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
  z-index: 20;
}

.mode-tab .tab-ink {
  position: absolute;
  inset: 0;
  opacity: 0;
  z-index: 0;
  transition: opacity 0.2s;
}

.mode-tab.active .tab-ink { opacity: 1; }
.mode-tab .tab-text { position: relative; z-index: 1; }

/* Mode Colors */
.mode-tab.ALL .tab-ink { background: #333; }
.mode-tab.REGULAR .tab-ink { background: #19D719; }
.mode-tab.BANKARA_CHALLENGE .tab-ink { background: #E60012; }
.mode-tab.BANKARA_OPEN .tab-ink { background: #603BFF; }
.mode-tab.X_MATCH .tab-ink { background: #00EBA7; }
.mode-tab.FEST .tab-ink { background: linear-gradient(135deg, #EAFF3D 0%, #F54E93 50%, #603BFF 100%); }
.mode-tab.LEAGUE .tab-ink { background: #F54E93; }
.mode-tab.PRIVATE .tab-ink { background: #888; }

.mode-tab.X_MATCH.active { color: #000; }
.mode-tab.FEST.active { color: #000; }

.mode-tab.refresh-btn {
  background: #f0f0f0;
  border-color: #ddd;
  color: #666;
  min-width: 40px;
  padding: 8px 10px;
}

.mode-tab.refresh-btn:hover {
  background: #e0e0e0;
  color: #333;
}

.mode-tab.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mode-tab.refresh-btn.refreshing {
  background: #E60012;
  border-color: #E60012;
  color: #fff;
}

.icon-spin {
  display: inline-block;
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
  margin-top: 12px;
  position: relative;
  background: linear-gradient(90deg, #E60012, #ff6b6b);
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
    #E60012 0%,
    #ff6b6b 50%,
    #E60012 100%
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

/* Battle List */
.battle-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
  min-height: 0;
  height: 100%;
}

.battle-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s;
  box-shadow: 0 3px 0 rgba(0,0,0,0.05);
  border: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.battle-card:hover {
  transform: translateY(-2px);
}

.card-header {
  position: relative;
  height: 56px;
  background-size: cover;
  background-position: center;
}

.header-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 14px;
}

.mode-rule {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-badge {
  font-size: 11px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 4px;
  background: #333;
  color: #fff;
}

.mode-badge.bankara.challenge { background: #E60012; }
.mode-badge.bankara.open { background: #4820CC; }
.mode-badge.x_match { background: #00EBA7; color: #000; }
.mode-badge.regular { background: #19D719; }
.mode-badge.fest { background: linear-gradient(135deg, #EAFF3D, #F54E93); color: #000; }
.mode-badge.league { background: #F54E93; }
.mode-badge.private { background: #888; }

.rule-icon {
  width: 20px;
  height: 20px;
}

.rule-name {
  font-size: 13px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stage-name {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
}

.time {
  font-size: 11px;
  color: rgba(255,255,255,0.9);
}

/* Card Body */
.card-body {
  padding: 0;
}

.color-bar {
  height: 48px;
  position: relative;
}

.score-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 14px;
}

.score-val {
  font-size: 18px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
  min-width: 40px;
}

.score-val:last-child {
  text-align: right;
}

.result-badge {
  font-size: 13px;
  font-weight: 900;
  padding: 5px 14px;
  border-radius: 20px;
  color: #fff;
  background: #333;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  gap: 6px;
}

.result-badge.WIN {
  background: #EAFF3D;
  color: #000;
  border-color: #333;
}

.result-badge.LOSE {
  background: #E60012;
}

.result-badge.DRAW {
  background: #888;
}

.ko-badge {
  background: #000;
  color: #EAFF3D;
  padding: 1px 5px;
  font-size: 10px;
  border-radius: 4px;
  font-weight: 800;
}

/* Footer Center - Stats Display */
.footer-center {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}

.stat-badge.udemae {
  color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

.stat-badge.power {
  background: #333;
  color: #EAFF3D;
  font-family: 'M PLUS Rounded 1c', monospace;
}

.stat-badge.power.x-match { color: #00EBA7; }
.stat-badge.power.fest { color: #F54E93; }
.stat-badge.power.league { color: #fff; }
.stat-badge.power.open { color: #BFA6FF; }

.power-icon-sm {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.power-label {
  font-size: 9px;
  opacity: 0.7;
  margin-right: 2px;
}

.power-val {
  font-weight: 800;
}

.event-name {
  font-size: 10px;
  font-weight: 600;
  color: #F54E93;
  background: rgba(245, 78, 147, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Card Footer */
.card-footer {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  position: relative;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.weapon-set {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  background: #f5f5f5;
  padding: 4px 6px;
  border-radius: 8px;
}

.w-main { width: 28px; height: 28px; object-fit: contain; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.15)); }
.w-sub { width: 16px; height: 16px; object-fit: contain; opacity: 0.85; }
.w-special { width: 16px; height: 16px; object-fit: contain; opacity: 0.85; }

.player-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f0f0;
  padding: 4px 10px;
  border-radius: 8px;
}

.kda {
  font-weight: 700;
  font-size: 14px;
}

.kda .k { color: #333; }
.kda .k .a { font-size: 0.8em; color: #888; }
.kda .d { color: #888; }
.kda .sep { margin: 0 2px; color: #ccc; }

.paint-point {
  color: #19D719;
  font-weight: 700;
  font-size: 12px;
}

.sp-tag {
  font-size: 10px;
  background: #333;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
}

.list-awards {
  display: flex;
  gap: 4px;
}

.award-item {
  position: relative;
}

.award-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  cursor: help;
}

.tooltip {
  visibility: hidden;
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  white-space: nowrap;
  z-index: 10;
  margin-bottom: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.award-item:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

.duration {
  font-size: 12px;
  color: #888;
  font-family: 'M PLUS Rounded 1c', monospace;
  background: #f0f0f0;
  padding: 3px 8px;
  border-radius: 6px;
}

/* Weapon Filter */
.weapon-filter {
  position: relative;
}

.filter-trigger {
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

.filter-trigger:hover {
  border-color: #333;
}

.filter-weapon-icon {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.filter-all-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #333;
  color: #EAFF3D;
  font-size: 10px;
  font-weight: 900;
  border-radius: 6px;
}

.filter-label {
  flex: 1;
  font-size: 13px;
  font-weight: 700;
  color: #333;
}

.filter-arrow {
  font-size: 10px;
  color: #888;
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
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.filter-option:hover {
  background: #f5f5f5;
}

.filter-option.active {
  background: #EAFF3D;
}

.option-all {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #333;
  color: #EAFF3D;
  font-size: 8px;
  font-weight: 900;
  border-radius: 4px;
}

.option-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.option-name {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.loading-more, .no-more {
  text-align: center;
  padding: 16px;
  color: #888;
  font-size: 13px;
}

.loading-more {
  color: #603BFF;
  font-weight: 600;
}

.footer-note {
  margin-top: 24px;
  padding: 12px 16px;
  background: #f8f8f8;
  border-radius: 8px;
  font-size: 11px;
  color: #888;
  line-height: 1.6;
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
  border-color: #333;
}

.filter-time-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #333;
  color: #EAFF3D;
  font-size: 8px;
  font-weight: 900;
  border-radius: 6px;
}

.clear-time-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #333;
  color: #EAFF3D;
  border-radius: 50%;
  border: none;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.clear-time-btn:hover {
  background: #E60012;
}

.time-dropdown {
  width: 280px;
  padding: 12px;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}

.time-input-group:last-child {
  margin-bottom: 0;
}

.time-label {
  font-size: 11px;
  font-weight: 700;
  color: #666;
}

.time-input {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px 10px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  color: #333;
  outline: none;
  transition: border-color 0.2s;
}

.time-input:focus {
  border-color: #333;
}

.time-input::-webkit-calendar-picker-indicator {
  cursor: pointer;
}
</style>
