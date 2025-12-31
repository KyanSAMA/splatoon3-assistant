<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  mockBattles, mockTotalStats, mockOpponentStatsWin, mockOpponentStatsLose,
  mockWinRateRanking, mockLoseRateRanking, rgbaToCSS
} from '../mocks/battles.js'

const router = useRouter()

const activeTab = ref('ALL')
const tabs = [
  { label: '全部', value: 'ALL', modeKey: null },
  { label: '涂地', value: 'REGULAR', modeKey: 'REGULAR' },
  { label: '蛮颓挑战', value: 'BANKARA_CHALLENGE', modeKey: 'BANKARA_CHALLENGE' },
  { label: '蛮颓开放', value: 'BANKARA_OPEN', modeKey: 'BANKARA_OPEN' },
  { label: 'X比赛', value: 'X_MATCH', modeKey: 'X_MATCH' },
  { label: '活动', value: 'LEAGUE', modeKey: 'LEAGUE' },
  { label: '祭典', value: 'FEST', modeKey: 'FEST' }
]

const battles = ref(mockBattles)

const getRuleIcon = (rule) => `/static/vs_rule/${rule}.svg`
const getWeaponImg = (id) => `/static/weapon/${id}.png`
const getAwardIcon = (rank) => rank === 'GOLD' ? '/static/medal/IconMedal_00.png' : '/static/medal/IconMedal_01.png'

const currentStats = computed(() => {
  if (activeTab.value === 'ALL') {
    return { win: mockTotalStats.win, lose: mockTotalStats.lose, rate: mockTotalStats.winRate }
  }
  const key = tabs.find(t => t.value === activeTab.value)?.modeKey
  const stats = mockTotalStats.byMode[key]
  return stats ? { win: stats.win, lose: stats.lose, rate: stats.winRate } : { win: '-', lose: '-', rate: '-' }
})

const filteredBattles = computed(() => {
  let result = battles.value
  if (activeTab.value === 'REGULAR') {
    result = result.filter(b => b.vs_mode === 'REGULAR')
  } else if (activeTab.value === 'X_MATCH') {
    result = result.filter(b => b.vs_mode === 'X_MATCH')
  } else if (activeTab.value === 'BANKARA_CHALLENGE') {
    result = result.filter(b => b.vs_mode === 'BANKARA' && b.bankara_mode === 'CHALLENGE')
  } else if (activeTab.value === 'BANKARA_OPEN') {
    result = result.filter(b => b.vs_mode === 'BANKARA' && b.bankara_mode === 'OPEN')
  } else if (activeTab.value === 'LEAGUE') {
    result = result.filter(b => b.vs_mode === 'LEAGUE')
  } else if (activeTab.value === 'FEST') {
    result = result.filter(b => b.vs_mode === 'FEST')
  }
  return result
})

// Pie chart logic - sort by count, add Others
const pieColors = ['#EAFF3D', '#603BFF', '#E60012', '#00EBA7', '#F54E93', '#19D719', '#888']

const getPieData = (sourceData) => {
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

const winPieData = computed(() => getPieData(mockOpponentStatsWin))
const losePieData = computed(() => getPieData(mockOpponentStatsLose))
const winTotal = computed(() => mockOpponentStatsWin.reduce((a, b) => a + b.count, 0))
const loseTotal = computed(() => mockOpponentStatsLose.reduce((a, b) => a + b.count, 0))

const formatDuration = (sec) => {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatTime = (iso) => {
  const d = new Date(iso)
  const now = new Date()
  const isCurrentYear = d.getFullYear() === now.getFullYear()
  const datePart = `${(d.getMonth()+1)}/${d.getDate()}`
  const timePart = `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
  return isCurrentYear ? `${datePart} ${timePart}` : `${d.getFullYear()}/${datePart}`
}

const getModeLabel = (battle) => {
  if (battle.vs_mode === 'BANKARA') {
    return battle.bankara_mode === 'CHALLENGE' ? '挑战' : '开放'
  }
  return { REGULAR: '涂地', X_MATCH: 'X赛', LEAGUE: '活动', FEST: '祭典' }[battle.vs_mode] || battle.vs_mode
}

const getRuleLabel = (rule) => {
  return { AREA: '区域', LOFT: '塔楼', GOAL: '鱼虎', CLAM: '蛤蜊', TURF_WAR: '涂地' }[rule] || rule
}

const getTeamsSorted = (battle) => {
  return [...battle.teams].sort((a, b) => a.team_order - b.team_order)
}

const getMyPlayer = (battle) => {
  const myTeam = battle.teams.find(t => t.team_role === 'MY')
  return myTeam ? myTeam.players.find(p => p.is_myself) : null
}

const getColorBarStyle = (battle) => {
  const sorted = getTeamsSorted(battle)
  if (sorted.length < 2) return {}
  const t1 = sorted[0], t2 = sorted[1]
  const s1 = t1.score ?? (t1.paint_ratio ? t1.paint_ratio * 100 : 50)
  const s2 = t2.score ?? (t2.paint_ratio ? t2.paint_ratio * 100 : 50)
  const total = s1 + s2 || 1
  const p1 = (s1 / total) * 100
  return { background: `linear-gradient(to right, ${rgbaToCSS(t1.color)} ${p1}%, ${rgbaToCSS(t2.color)} ${p1}%)` }
}

const getScoreDisplay = (team) => {
  if (team?.score != null) return team.score
  if (team?.paint_ratio != null) return Math.round(team.paint_ratio * 100) + '%'
  return '-'
}

const goToDetail = (id) => {
  router.push({ name: 'battle-detail', params: { id } })
}
</script>

<template>
  <div class="battle-page">
    <!-- LEFT PANEL: Battle List -->
    <div class="left-panel">
      <div class="battle-list">
        <div
          v-for="battle in filteredBattles"
          :key="battle.id"
          class="battle-card"
          @click="goToDetail(battle.id)"
        >
          <div class="card-header">
            <div class="mode-rule">
              <span class="mode-badge" :class="[battle.vs_mode.toLowerCase(), battle.bankara_mode?.toLowerCase()]">
                {{ getModeLabel(battle) }}
              </span>
              <img :src="getRuleIcon(battle.vs_rule)" class="rule-icon" />
              <span class="rule-name">{{ getRuleLabel(battle.vs_rule) }}</span>
            </div>
            <div class="header-right">
              <span class="stage-name">{{ battle.stage.name }}</span>
              <span class="time">{{ formatTime(battle.played_time) }}</span>
            </div>
          </div>

          <div class="card-body">
            <div class="color-bar" :style="getColorBarStyle(battle)">
              <div class="score-overlay">
                <span class="score-val">{{ getScoreDisplay(getTeamsSorted(battle)[0]) }}</span>
                <div class="result-badge" :class="battle.judgement">
                  {{ battle.judgement === 'WIN' ? 'WIN!' : battle.judgement === 'LOSE' ? 'LOSE' : 'DRAW' }}
                  <span v-if="battle.knockout === 'WIN' || battle.knockout === 'LOSE'" class="ko-badge">KO!</span>
                </div>
                <span class="score-val">{{ getScoreDisplay(getTeamsSorted(battle)[1]) }}</span>
              </div>
            </div>

            <div class="card-footer">
              <div class="player-stats" v-if="getMyPlayer(battle)">
                <span class="kda">
                  <span class="k">{{ getMyPlayer(battle).k }}</span>
                  <span class="sep">/</span>
                  <span class="d">{{ getMyPlayer(battle).d }}</span>
                  <span class="sep">/</span>
                  <span class="a">{{ getMyPlayer(battle).a }}</span>
                </span>
                <span class="sp-tag">SP {{ getMyPlayer(battle).sp }}</span>
              </div>
              <div class="footer-right">
                <div v-if="battle.awards && battle.awards.length" class="list-awards">
                  <div v-for="(a, i) in battle.awards" :key="i" class="award-item">
                    <img :src="getAwardIcon(a.rank)" class="award-icon" />
                    <div class="tooltip">{{ a.name }}</div>
                  </div>
                </div>
                <span class="duration">{{ formatDuration(battle.duration) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT PANEL: Stats & Controls -->
    <div class="right-panel">
      <!-- 1. Mode Tabs -->
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
        </div>
      </div>

      <!-- 2. Overall Stats -->
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

      <!-- 3. Win Pie Chart -->
      <div class="dashboard-card">
        <h3 class="card-title win">WIN 武器分布</h3>
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
              <span class="name">{{ item.name }}</span>
              <span class="count">x{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Lose Pie Chart -->
      <div class="dashboard-card">
        <h3 class="card-title lose">LOSE 武器分布</h3>
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
              <span class="name">{{ item.name }}</span>
              <span class="count">x{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 5. Win Ranking -->
      <div class="dashboard-card">
        <h3 class="card-title win">高胜率对手</h3>
        <div class="ranking-bars">
          <div v-for="r in mockWinRateRanking.slice(0, 5)" :key="r.weapon_id" class="rank-bar win">
            <img :src="getWeaponImg(r.weapon_id)" class="rank-icon" />
            <div class="rank-info">
              <span class="rank-name">{{ r.name }}</span>
              <div class="progress-bg"><div class="progress-fill" :style="{ width: r.rate + '%' }"></div></div>
            </div>
            <span class="rank-val">{{ r.rate }}%</span>
          </div>
        </div>
      </div>

      <!-- 6. Lose Ranking -->
      <div class="dashboard-card">
        <h3 class="card-title lose">高败率对手</h3>
        <div class="ranking-bars">
          <div v-for="r in mockLoseRateRanking.slice(0, 5)" :key="r.weapon_id" class="rank-bar lose">
            <img :src="getWeaponImg(r.weapon_id)" class="rank-icon" />
            <div class="rank-info">
              <span class="rank-name">{{ r.name }}</span>
              <div class="progress-bg"><div class="progress-fill" :style="{ width: r.rate + '%' }"></div></div>
            </div>
            <span class="rank-val">{{ r.rate }}%</span>
          </div>
        </div>
      </div>
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
.mode-tab.LEAGUE .tab-ink { background: #F54E93; }
.mode-tab.FEST .tab-ink { background: #FFD000; }

.mode-tab.X_MATCH.active, .mode-tab.FEST.active { color: #000; }

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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #fafafa;
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
.mode-badge.bankara.open { background: #603BFF; }
.mode-badge.x_match { background: #00EBA7; color: #000; }
.mode-badge.regular { background: #19D719; }
.mode-badge.league { background: #F54E93; }
.mode-badge.fest { background: #FFD000; color: #000; }

.rule-icon {
  width: 20px;
  height: 20px;
}

.rule-name {
  font-size: 13px;
  color: #555;
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
  color: #555;
}

.time {
  font-size: 11px;
  color: #999;
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

/* Card Footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
}

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
.kda .d { color: #888; }
.kda .a { color: #888; font-size: 0.9em; }
.kda .sep { margin: 0 2px; color: #ccc; }

.sp-tag {
  font-size: 10px;
  background: #333;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 700;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 10px;
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
</style>
