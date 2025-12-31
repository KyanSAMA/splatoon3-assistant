<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBattleById, rgbaToCSS } from '../mocks/battles.js'

const route = useRoute()
const router = useRouter()
const battle = ref(null)

onMounted(() => {
  battle.value = getBattleById(route.params.id)
})

const getRuleIcon = (rule) => `/static/vs_rule/${rule}.svg`
const getStageImg = (code) => `/static/stage/${code}.png`
const getWeaponImg = (id) => `/static/weapon/${id}.png`
const getAwardIcon = (rank) => rank === 'GOLD' ? '/static/medal/IconMedal_00.png' : '/static/medal/IconMedal_01.png'

const formatDuration = (sec) => {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatTime = (iso) => {
  const d = new Date(iso)
  const now = new Date()
  const isCurrentYear = d.getFullYear() === now.getFullYear()
  const datePart = `${(d.getMonth()+1).toString().padStart(2,'0')}/${d.getDate().toString().padStart(2,'0')}`
  const timePart = `${d.getHours()}:${d.getMinutes().toString().padStart(2,'0')}`
  return isCurrentYear ? `${datePart} ${timePart}` : `${d.getFullYear()}/${datePart} ${timePart}`
}

const getModeLabel = (b) => {
  if (b.vs_mode === 'BANKARA') {
    return b.bankara_mode === 'CHALLENGE' ? '蛮颓挑战' : '蛮颓开放'
  }
  return { REGULAR: '涂地对战', X_MATCH: 'X比赛', LEAGUE: '活动比赛', FEST: '祭典' }[b.vs_mode] || b.vs_mode
}

const getRuleLabel = (rule) => {
  return { AREA: '区域', LOFT: '塔楼', GOAL: '鱼虎', CLAM: '蛤蜊', TURF_WAR: '涂地' }[rule] || rule
}

const myTeam = computed(() => battle.value?.teams.find(t => t.team_role === 'MY'))
const otherTeam = computed(() => battle.value?.teams.find(t => t.team_role === 'OTHER'))

const getScoreDisplay = (team, rule) => {
  if (!team) return '-'
  if (rule === 'TURF_WAR') {
    return team.paint_ratio != null ? `${Math.round(team.paint_ratio * 100)}%` : '-'
  }
  return team.score != null ? team.score : '-'
}

const getColorBarStyle = (b) => {
  if (!b) return {}
  const sorted = [...b.teams].sort((a, b) => a.team_order - b.team_order)
  if (sorted.length < 2) return {}
  const t1 = sorted[0], t2 = sorted[1]
  const s1 = t1.score ?? (t1.paint_ratio ? t1.paint_ratio * 100 : 50)
  const s2 = t2.score ?? (t2.paint_ratio ? t2.paint_ratio * 100 : 50)
  const total = s1 + s2 || 1
  const p1 = (s1 / total) * 100
  return { background: `linear-gradient(to right, ${rgbaToCSS(t1.color)} ${p1}%, ${rgbaToCSS(t2.color)} ${p1}%)` }
}

const goBack = () => router.back()
</script>

<template>
  <div class="battle-detail-view">
    <div class="nav-bar">
      <button @click="goBack" class="btn-back">← 返回</button>
    </div>

    <div v-if="battle" class="detail-card">
      <!-- Header -->
      <div class="battle-header" :style="{ backgroundImage: `url(${getStageImg(battle.stage.code)})` }">
        <div class="header-overlay"></div>
        <div class="header-content">
          <div class="header-top">
            <span class="mode-tag">{{ getModeLabel(battle) }}</span>
            <span class="time">{{ formatTime(battle.played_time) }}</span>
          </div>
          <div class="stage-info">
            <div class="rule-badge">
              <img :src="getRuleIcon(battle.vs_rule)" />
            </div>
            <div class="stage-name-wrapper">
              <h1>{{ battle.stage.name }}</h1>
              <span class="rule-name">{{ getRuleLabel(battle.vs_rule) }}</span>
            </div>
          </div>
          <div class="match-meta">
            <span class="duration-tag">{{ formatDuration(battle.duration) }}</span>
            <span v-if="battle.knockout === 'WIN' || battle.knockout === 'LOSE'" class="ko-tag">KO!</span>
            <span v-if="battle.x_power" class="power-tag">XP {{ battle.x_power }}</span>
            <span v-else-if="battle.udemae" class="rank-tag">{{ battle.udemae }}</span>
          </div>
        </div>
      </div>

      <!-- Score Color Bar -->
      <div class="score-bar" :style="getColorBarStyle(battle)">
        <div class="score-content">
          <span class="team-score" :style="{ color: rgbaToCSS(myTeam?.color) }">
            {{ getScoreDisplay(myTeam, battle.vs_rule) }}
          </span>
          <span class="result-badge" :class="battle.judgement">
            {{ battle.judgement === 'WIN' ? 'WIN!' : battle.judgement === 'LOSE' ? 'LOSE' : 'DRAW' }}
          </span>
          <span class="team-score" :style="{ color: rgbaToCSS(otherTeam?.color) }">
            {{ getScoreDisplay(otherTeam, battle.vs_rule) }}
          </span>
        </div>
      </div>

      <!-- Awards -->
      <div v-if="battle.awards && battle.awards.length" class="awards-section">
        <div v-for="(a, i) in battle.awards" :key="i" class="award-pill">
          <img :src="getAwardIcon(a.rank)" class="award-icon-md" />
          <span class="award-text">{{ a.name }}</span>
        </div>
      </div>

      <!-- Teams -->
      <div class="teams-container">
        <!-- My Team -->
        <div class="team-section">
          <div class="team-header" :style="{ borderColor: rgbaToCSS(myTeam?.color) }">
            <span class="team-label">我方队伍</span>
          </div>
          <div class="player-list" v-if="myTeam?.players.length">
            <div class="player-row header-row">
              <span class="col-weapon"></span>
              <span class="col-name">玩家</span>
              <span class="col-stat">K</span>
              <span class="col-stat">D</span>
              <span class="col-stat">A</span>
              <span class="col-stat">SP</span>
              <span class="col-paint">涂地</span>
            </div>
            <div
              v-for="(p, idx) in myTeam.players"
              :key="idx"
              class="player-row"
              :class="{ 'is-myself': p.is_myself }"
            >
              <div class="col-weapon">
                <img :src="getWeaponImg(p.weapon_id)" />
              </div>
              <div class="col-name">
                {{ p.name }}
                <span v-if="p.crown" class="crown">👑</span>
              </div>
              <span class="col-stat">{{ p.k }}</span>
              <span class="col-stat">{{ p.d }}</span>
              <span class="col-stat">{{ p.a }}</span>
              <span class="col-stat">{{ p.sp }}</span>
              <span class="col-paint">{{ p.p }}p</span>
            </div>
          </div>
          <div v-else class="no-data">暂无玩家数据</div>
        </div>

        <!-- Other Team -->
        <div class="team-section">
          <div class="team-header" :style="{ borderColor: rgbaToCSS(otherTeam?.color) }">
            <span class="team-label">对方队伍</span>
          </div>
          <div class="player-list" v-if="otherTeam?.players.length">
            <div class="player-row header-row">
              <span class="col-weapon"></span>
              <span class="col-name">玩家</span>
              <span class="col-stat">K</span>
              <span class="col-stat">D</span>
              <span class="col-stat">A</span>
              <span class="col-stat">SP</span>
              <span class="col-paint">涂地</span>
            </div>
            <div v-for="(p, idx) in otherTeam.players" :key="idx" class="player-row">
              <div class="col-weapon">
                <img :src="getWeaponImg(p.weapon_id)" />
              </div>
              <div class="col-name">
                {{ p.name }}
                <span v-if="p.crown" class="crown">👑</span>
              </div>
              <span class="col-stat">{{ p.k }}</span>
              <span class="col-stat">{{ p.d }}</span>
              <span class="col-stat">{{ p.a }}</span>
              <span class="col-stat">{{ p.sp }}</span>
              <span class="col-paint">{{ p.p }}p</span>
            </div>
          </div>
          <div v-else class="no-data">暂无玩家数据</div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">加载中...</div>
  </div>
</template>

<style scoped>
.battle-detail-view {
  font-family: 'M PLUS Rounded 1c', -apple-system, sans-serif;
  width: 100%;
  max-width: 750px;
  margin: 0 auto;
  padding: 20px;
}

.nav-bar {
  margin-bottom: 16px;
}

.btn-back {
  background: none;
  border: 2px solid #333;
  border-radius: 20px;
  padding: 8px 18px;
  font-size: 14px;
  font-weight: 700;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #333;
  color: #EAFF3D;
}

.detail-card {
  background: #fff;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.battle-header {
  position: relative;
  height: 180px;
  background-size: cover;
  background-position: center;
  color: #fff;
}

.header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.2), rgba(0,0,0,0.75));
}

.header-content {
  position: relative;
  height: 100%;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.header-top {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  opacity: 0.9;
}

.mode-tag {
  background: rgba(255,255,255,0.2);
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 700;
}

.stage-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.rule-badge {
  width: 48px;
  height: 48px;
  background: rgba(0,0,0,0.5);
  border-radius: 50%;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rule-badge img {
  width: 100%;
  height: 100%;
}

.stage-name-wrapper h1 {
  font-size: 24px;
  font-weight: 900;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.rule-name {
  font-size: 14px;
  opacity: 0.85;
  font-weight: 600;
}

.match-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
}

.duration-tag {
  background: rgba(255,255,255,0.2);
  padding: 3px 10px;
  border-radius: 6px;
}

.ko-tag {
  background: #E60012;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 800;
}

.power-tag, .rank-tag {
  background: rgba(96,59,255,0.8);
  padding: 3px 10px;
  border-radius: 6px;
}

/* Score Bar */
.score-bar {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-content {
  display: flex;
  align-items: center;
  gap: 24px;
  background: rgba(0,0,0,0.5);
  padding: 10px 28px;
  border-radius: 35px;
}

.team-score {
  font-size: 28px;
  font-weight: 900;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  min-width: 60px;
  text-align: center;
}

.result-badge {
  font-size: 16px;
  font-weight: 900;
  padding: 6px 20px;
  border-radius: 8px;
  color: #fff;
}

.result-badge.WIN {
  background: #EAFF3D;
  color: #000;
}

.result-badge.LOSE {
  background: #E60012;
}

.result-badge.DRAW {
  background: #888;
}

/* Awards */
.awards-section {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 18px 20px 0;
  justify-content: center;
}

.award-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5f5f5;
  padding: 6px 14px;
  border-radius: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
}

.award-icon-md {
  width: 26px;
  height: 26px;
}

.award-text {
  font-size: 13px;
  color: #333;
  font-weight: 700;
}

/* Teams */
.teams-container {
  padding: 20px;
}

.team-section {
  margin-bottom: 24px;
}

.team-header {
  border-left: 6px solid #888;
  padding-left: 12px;
  margin-bottom: 14px;
}

.team-label {
  font-size: 16px;
  font-weight: 800;
  color: #333;
}

.player-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.player-row {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 10px;
  background: #f5f5f5;
  font-size: 14px;
  font-weight: 500;
}

.header-row {
  background: transparent;
  color: #888;
  font-size: 12px;
  font-weight: 700;
  padding-bottom: 4px;
}

.is-myself {
  background: #EAFF3D;
  border: 2px solid #333;
}

.col-weapon {
  width: 40px;
  display: flex;
  align-items: center;
}

.col-weapon img {
  width: 34px;
  height: 34px;
  object-fit: contain;
}

.col-name {
  flex: 1;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 10px;
}

.crown {
  margin-left: 4px;
}

.col-stat {
  width: 36px;
  text-align: center;
  font-weight: 600;
}

.col-paint {
  width: 65px;
  text-align: right;
  font-family: 'M PLUS Rounded 1c', monospace;
  color: #666;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 24px;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 50px;
  color: #888;
  font-size: 16px;
}
</style>
