<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { rgbaToCSS } from '../mocks/battles.js'
import { splatoonService } from '../api/splatoon'
import { formatDateTime } from '../utils/timezone'

const route = useRoute()
const router = useRouter()
const battle = ref(null)
const loading = ref(false)
const error = ref('')

// 武器缓存
const mainWeapons = ref([])

onMounted(async () => {
  loading.value = true
  try {
    // 并行加载对战详情和武器列表
    const [battleData, weapons] = await Promise.all([
      splatoonService.getBattleDetail(route.params.id),
      splatoonService.getMainWeapons()
    ])
    battle.value = battleData
    mainWeapons.value = weapons || []
    if (!battle.value) {
      error.value = '未找到对战记录'
    }
  } catch (e) {
    error.value = '加载失败: ' + (e.message || '未知错误')
    console.error(e)
  } finally {
    loading.value = false
  }
})

// 根据 weapon_id 获取武器信息
const getWeaponInfo = (weaponId) => {
  return mainWeapons.value.find(w => String(w.code) === String(weaponId))
}

const getRuleIcon = (rule) => `/static/vs_rule/${rule}.svg`
const getStageImgL = (code) => `/static/stage_l/${code}.png`
const getWeaponImg = (id) => `/static/weapon/${id}.png`
const getSubWeaponImg = (code) => `/static/sub_weapon/${code}.png`
const getSpecialWeaponImg = (code) => `/static/special_weapon/${code}.png`
const getAwardIcon = (rank) => rank === 'GOLD' ? '/static/medal/IconMedal_00.png' : '/static/medal/IconMedal_01.png'

// 技能图片 hash -> 本地文件名映射
const skillHashMap = {
  '5c98cc37d2ce56291a7e430459dc9c44d53ca98b8426c5192f4a53e6dd6e4293': 'ink_saver_main',
  '11293d8fe7cfb82d55629c058a447f67968fc449fd52e7dd53f7f162fa4672e3': 'ink_saver_sub',
  '29b845ea895b931bfaf895e0161aeb47166cbf05f94f04601769c885d019073b': 'ink_recovery_up',
  '3b6c56c57a6d8024f9c7d6e259ffa2e2be4bdf958653b834e524ffcbf1e6808e': 'run_speed_up',
  '087ffffe40c28a40a39dc4a577c235f4cc375540c79dfa8ede1d8b63a063f261': 'swim_speed_up',
  'e8668a2af7259be74814a9e453528a3e9773435a34177617a45bbf79ad0feb17': 'special_charge_up',
  'e3154ab67494df2793b72eabf912104c21fbca71e540230597222e766756b3e4': 'special_saver',
  'fba267bd56f536253a6bcce1e919d8a48c2b793c1b554ac968af8d2068b22cab': 'special_power_up',
  'aaa9b7e95a61bfd869aaa9beb836c74f9b8d4e5d4186768a27d6e443c64f33ce': 'quick_respawn',
  '138820ed46d68bdf2d7a21fb3f74621d8fc8c2a7cb6abe8d7c1a3d7c465108a7': 'quick_super_jump',
  '9df9825e470e00727aa1009c4418cf0ace58e1e529dab9a7c1787309bb25f327': 'sub_power_up',
  'db36f7e89194ed642f53465abfa449669031a66d7538135c703d3f7d41f99c0d': 'ink_resistance_up',
  '664489b24e668ef1937bfc9a80a8cf9cf4927b1e16481fa48e7faee42122996d': 'sub_resistance_up',
  '1a0c78a1714c5abababd7ffcba258c723fefade1f92684aa5f0ff7784cc467d0': 'intensify_action',
  '85d97cd3d5890b80e020a554167e69b5acfa86e96d6e075b5776e6a8562d3d4a': 'opening_gambit',
  'd514787f65831c5121f68b8d96338412a0d261e39e522638488b24895e97eb88': 'last_ditch_effort',
  'aa5b599075c3c1d27eff696aeded9f1e1ddf7ae3d720268e520b260db5600d60': 'tenacity',
  '748c101d23261aee8404c573a947ffc7e116a8da588c7371c40c4f2af6a05a19': 'comeback',
  '2c0ef71abfb3efe0e67ab981fc9cd46efddcaf93e6e20da96980079f8509d05d': 'ninja_squid',
  'de15cad48e5f23d147449c70ee4e2973118959a1a115401561e90fc65b53311b': 'haunt',
  '56816a7181e663b5fedce6315eb0ad538e0aadc257b46a630fcfcc4a16155941': 'thermal_ink',
  'de0d92f7dfed6c76772653d6858e7b67dd1c83be31bd2324c7939105180f5b71': 'respawn_punisher',
  '0d6607b6334e1e84279e482c1b54659e31d30486ef0576156ee0974d8d569dbc': 'ability_doubler',
  'f9c21eacf6dbc1d06edbe498962f8ed766ab43cb1d63806f3731bf57411ae7b6': 'stealth_jump',
  '9d982dc1a7a8a427d74df0edcebcc13383c325c96e75af17b9cdb6f4e8dafb24': 'object_shredder',
  '18f03a68ee64da0a2e4e40d6fc19de2e9af3569bb6762551037fd22cf07b7d2d': 'drop_roller',
  'dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91': 'null'
}

// 从 URL 解析 hash 并获取本地图片路径
const getSkillImg = (url) => {
  if (!url) return null
  // URL 格式: https://.../skill_img/{hash}_0.png?...
  const match = url.match(/skill_img\/([a-f0-9]+)_/)
  if (!match) return null
  const hash = match[1]
  const filename = skillHashMap[hash]
  return filename ? `/static/skill/${filename}.png` : null
}

const nullSkillImg = '/static/skill/null.png'

// 补齐副技能数组到3个
const padSubs = (subs) => {
  // 后端返回的是 JSON 字符串或数组
  let arr = subs
  if (typeof subs === 'string') {
    try { arr = JSON.parse(subs) } catch { arr = [] }
  }
  arr = arr || []
  return [arr[0] || null, arr[1] || null, arr[2] || null]
}

// 解析 JSON 字段
const parseJson = (val) => {
  if (!val) return null
  if (typeof val === 'object') return val
  try { return JSON.parse(val) } catch { return null }
}

const formatDuration = (sec) => {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatTime = (iso) => formatDateTime(iso)

const getModeLabel = (b) => {
  if (b.vs_mode === 'BANKARA') return b.bankara_mode === 'CHALLENGE' ? '蛮颓挑战' : '蛮颓开放'
  return { REGULAR: '涂地对战', X_MATCH: 'X比赛', LEAGUE: '活动比赛', FEST: '祭典', PRIVATE: '私房' }[b.vs_mode] || b.vs_mode
}

const getRuleLabel = (rule) => ({ AREA: '区域', LOFT: '塔楼', GOAL: '鱼虎', CLAM: '蛤蜊', TURF_WAR: '涂地' }[rule] || rule)

const getUdemaeColor = (udemae) => {
  if (!udemae) return '#888'
  if (udemae.includes('S+')) return '#F54E93'
  if (udemae.startsWith('S')) return '#603BFF'
  if (udemae.startsWith('A')) return '#00C2CB'
  if (udemae.startsWith('B')) return '#FF9F2C'
  return '#888'
}

const myTeam = computed(() => battle.value?.teams.find(t => t.team_role === 'MY'))
const otherTeam = computed(() => battle.value?.teams.find(t => t.team_role === 'OTHER'))
const getMyPlayer = (b) => {
  const myTeam = b?.teams.find(t => t.team_role === 'MY')
  return myTeam?.players.find(p => p.is_myself === 1)
}

const getScoreDisplay = (team, rule) => {
  if (!team) return '-'
  if (rule === 'TURF_WAR') return team.paint_ratio != null ? `${Math.round(team.paint_ratio * 100)}%` : '-'
  return team.score != null ? team.score : '-'
}

const getColorBarStyle = (b) => {
  if (!b) return {}
  const t1 = b.teams.find(t => t.team_role === 'MY')
  const t2 = b.teams.find(t => t.team_role === 'OTHER')
  if (!t1 || !t2) return {}
  const s1 = t1.score ?? (t1.paint_ratio ? t1.paint_ratio * 100 : 50)
  const s2 = t2.score ?? (t2.paint_ratio ? t2.paint_ratio * 100 : 50)
  const total = s1 + s2 || 1
  const p1 = (s1 / total) * 100
  return { background: `linear-gradient(to right, ${rgbaToCSS(parseJson(t1.color))} ${p1}%, ${rgbaToCSS(parseJson(t2.color))} ${p1}%)` }
}

const goBack = () => router.back()

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
  <div class="battle-detail-view">
    <div class="nav-bar">
      <button @click="goBack" class="btn-back">← 返回</button>
    </div>

    <div v-if="battle" class="detail-card">
      <!-- Header with large stage image -->
      <div class="battle-header" :style="{ backgroundImage: `url(${getStageImgL(battle.stage.code)})` }">
        <div class="header-overlay"></div>
        <div class="header-content">
          <div class="header-top">
            <span class="mode-tag">{{ getModeLabel(battle) }}</span>
            <span class="time">{{ formatTime(battle.played_time) }}</span>
          </div>
          <div class="header-center">
            <img :src="getRuleIcon(battle.vs_rule)" class="rule-icon-lg" />
            <span class="rule-name">{{ getRuleLabel(battle.vs_rule) }}</span>
            <h1 class="stage-name">{{ battle.stage.name }}</h1>
          </div>
          <div class="header-bottom">
            <span class="duration-tag">{{ formatDuration(battle.duration) }}</span>
            <span v-if="battle.knockout === 'WIN' || battle.knockout === 'LOSE'" class="ko-tag">KO!</span>
          </div>
        </div>
      </div>

      <!-- Score Bar -->
      <div class="score-bar" :style="getColorBarStyle(battle)">
        <div class="score-content">
          <span class="team-score">{{ getScoreDisplay(myTeam, battle.vs_rule) }}</span>
          <span class="result-badge" :class="getResultClass(battle.judgement)">
            {{ getResultText(battle.judgement) }}
          </span>
          <span class="team-score">{{ getScoreDisplay(otherTeam, battle.vs_rule) }}</span>
        </div>
      </div>

      <!-- Mode Stats -->
      <div class="mode-stats" v-if="battle.udemae || battle.weapon_power || battle.x_power || battle.fest_power || battle.my_league_power">
        <span v-if="battle.udemae" class="stat-badge udemae" :style="{ background: getUdemaeColor(battle.udemae) }">{{ battle.udemae }}</span>
        <div v-if="battle.weapon_power && getMyPlayer(battle)" class="stat-badge power">
          <img :src="getWeaponImg(getMyPlayer(battle).weapon_id)" class="power-icon" />
          <span>{{ battle.weapon_power.toFixed(1) }}</span>
        </div>
        <div v-if="battle.x_power" class="stat-badge power x-match">
          <span class="power-label">XP</span>
          <span>{{ battle.x_power.toFixed(1) }}</span>
        </div>
        <div v-if="battle.fest_power" class="stat-badge power fest">
          <span class="power-label">FP</span>
          <span>{{ battle.fest_power.toFixed(1) }}</span>
        </div>
        <div v-if="battle.my_league_power" class="stat-badge power league">
          <span class="power-label">LP</span>
          <span>{{ battle.my_league_power.toFixed(1) }}</span>
        </div>
        <span v-if="battle.league_match_event_name" class="event-name">{{ battle.league_match_event_name }}</span>
      </div>

      <!-- Awards -->
      <div v-if="parseJson(battle.awards)?.length" class="awards-section">
        <div v-for="(a, i) in parseJson(battle.awards)" :key="i" class="award-pill">
          <img :src="getAwardIcon(a.rank)" class="award-icon" />
          <span>{{ a.name }}</span>
        </div>
      </div>

      <!-- Teams -->
      <div class="teams-container">
        <!-- My Team -->
        <div class="team-section">
          <div class="team-header" :style="{ borderColor: rgbaToCSS(parseJson(myTeam?.color)) }">
            <span class="team-label">我方队伍</span>
          </div>
          <div class="player-list" v-if="myTeam?.players.length">
            <div
              v-for="(p, idx) in myTeam.players"
              :key="idx"
              class="player-card"
              :class="{ 'is-myself': p.is_myself === 1 }"
            >
              <div class="player-main">
                <div class="weapons-group">
                  <img :src="getWeaponImg(p.weapon_id)" class="weapon-main" />
                  <div class="sub-special" v-if="getWeaponInfo(p.weapon_id)">
                    <img :src="getSubWeaponImg(getWeaponInfo(p.weapon_id).sub_weapon_code)" class="weapon-sub" />
                    <img :src="getSpecialWeaponImg(getWeaponInfo(p.weapon_id).special_weapon_code)" class="weapon-special" />
                  </div>
                </div>
                <div class="player-name">
                  <div v-if="p.byname" class="player-byname">{{ p.byname }}</div>
                  <div class="player-name-text">
                    {{ p.name }}<span v-if="p.name_id" class="name-id">#{{ p.name_id }}</span>
                    <span v-if="p.crown" class="crown">👑</span>
                  </div>
                </div>
                <div class="skills-inline">
                  <div class="gear-row">
                    <img :src="getSkillImg(parseJson(p.head_skills_images)?.[p.head_main_skill]) || nullSkillImg" class="skill-img main" :title="p.head_main_skill || ''" />
                    <template v-for="(s, i) in padSubs(p.head_additional_skills)" :key="'h'+i">
                      <img :src="(s && getSkillImg(parseJson(p.head_skills_images)?.[s])) || nullSkillImg" class="skill-img sub" :title="s || ''" />
                    </template>
                  </div>
                  <div class="gear-row">
                    <img :src="getSkillImg(parseJson(p.clothing_skills_images)?.[p.clothing_main_skill]) || nullSkillImg" class="skill-img main" :title="p.clothing_main_skill || ''" />
                    <template v-for="(s, i) in padSubs(p.clothing_additional_skills)" :key="'c'+i">
                      <img :src="(s && getSkillImg(parseJson(p.clothing_skills_images)?.[s])) || nullSkillImg" class="skill-img sub" :title="s || ''" />
                    </template>
                  </div>
                  <div class="gear-row">
                    <img :src="getSkillImg(parseJson(p.shoes_skills_images)?.[p.shoes_main_skill]) || nullSkillImg" class="skill-img main" :title="p.shoes_main_skill || ''" />
                    <template v-for="(s, i) in padSubs(p.shoes_additional_skills)" :key="'s'+i">
                      <img :src="(s && getSkillImg(parseJson(p.shoes_skills_images)?.[s])) || nullSkillImg" class="skill-img sub" :title="s || ''" />
                    </template>
                  </div>
                </div>
                <div class="stats-group">
                  <div class="kda">
                    <span class="k">{{ p.kill_count }}<span class="a">&lt;{{ p.assist_count }}&gt;</span></span>/<span class="d">{{ p.death_count }}</span>
                  </div>
                  <span class="sp-tag">SP{{ p.special_count }}</span>
                  <span class="paint">{{ p.paint }}p</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Other Team -->
        <div class="team-section">
          <div class="team-header" :style="{ borderColor: rgbaToCSS(parseJson(otherTeam?.color)) }">
            <span class="team-label">对方队伍</span>
          </div>
          <div class="player-list" v-if="otherTeam?.players.length">
            <div
              v-for="(p, idx) in otherTeam.players"
              :key="idx"
              class="player-card"
            >
              <div class="player-main">
                <div class="weapons-group">
                  <img :src="getWeaponImg(p.weapon_id)" class="weapon-main" />
                  <div class="sub-special" v-if="getWeaponInfo(p.weapon_id)">
                    <img :src="getSubWeaponImg(getWeaponInfo(p.weapon_id).sub_weapon_code)" class="weapon-sub" />
                    <img :src="getSpecialWeaponImg(getWeaponInfo(p.weapon_id).special_weapon_code)" class="weapon-special" />
                  </div>
                </div>
                <div class="player-name">
                  <div v-if="p.byname" class="player-byname">{{ p.byname }}</div>
                  <div class="player-name-text">
                    {{ p.name }}<span v-if="p.name_id" class="name-id">#{{ p.name_id }}</span>
                    <span v-if="p.crown" class="crown">👑</span>
                  </div>
                </div>
                <div class="skills-inline">
                  <div class="gear-row">
                    <img :src="getSkillImg(parseJson(p.head_skills_images)?.[p.head_main_skill]) || nullSkillImg" class="skill-img main" :title="p.head_main_skill || ''" />
                    <template v-for="(s, i) in padSubs(p.head_additional_skills)" :key="'h'+i">
                      <img :src="(s && getSkillImg(parseJson(p.head_skills_images)?.[s])) || nullSkillImg" class="skill-img sub" :title="s || ''" />
                    </template>
                  </div>
                  <div class="gear-row">
                    <img :src="getSkillImg(parseJson(p.clothing_skills_images)?.[p.clothing_main_skill]) || nullSkillImg" class="skill-img main" :title="p.clothing_main_skill || ''" />
                    <template v-for="(s, i) in padSubs(p.clothing_additional_skills)" :key="'c'+i">
                      <img :src="(s && getSkillImg(parseJson(p.clothing_skills_images)?.[s])) || nullSkillImg" class="skill-img sub" :title="s || ''" />
                    </template>
                  </div>
                  <div class="gear-row">
                    <img :src="getSkillImg(parseJson(p.shoes_skills_images)?.[p.shoes_main_skill]) || nullSkillImg" class="skill-img main" :title="p.shoes_main_skill || ''" />
                    <template v-for="(s, i) in padSubs(p.shoes_additional_skills)" :key="'s'+i">
                      <img :src="(s && getSkillImg(parseJson(p.shoes_skills_images)?.[s])) || nullSkillImg" class="skill-img sub" :title="s || ''" />
                    </template>
                  </div>
                </div>
                <div class="stats-group">
                  <div class="kda">
                    <span class="k">{{ p.kill_count }}<span class="a">&lt;{{ p.assist_count }}&gt;</span></span>/<span class="d">{{ p.death_count }}</span>
                  </div>
                  <span class="sp-tag">SP{{ p.special_count }}</span>
                  <span class="paint">{{ p.paint }}p</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-data">暂无玩家数据</div>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="empty-state">加载中...</div>
    <div v-else-if="error" class="empty-state error">{{ error }}</div>
    <div v-else class="empty-state">未找到对战记录</div>
  </div>
</template>

<style scoped>
.battle-detail-view {
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
.battle-header {
  position: relative;
  height: 220px;
  background-size: cover;
  background-position: center;
  color: #fff;
}

.header-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.75));
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
}

.mode-tag {
  background: rgba(255,255,255,0.2);
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 700;
}

.header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.rule-icon-lg { width: 56px; height: 56px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); }
.rule-name { font-size: 14px; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
.stage-name { font-size: 26px; font-weight: 900; margin: 0; text-shadow: 0 2px 6px rgba(0,0,0,0.8); }

.header-bottom {
  display: flex;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
}

.duration-tag, .ko-tag {
  background: rgba(255,255,255,0.2);
  padding: 4px 12px;
  border-radius: 6px;
}
.ko-tag { background: #E60012; font-weight: 800; }

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
  color: #fff;
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
  border: 2px solid #fff;
}
.result-badge.WIN { background: #EAFF3D; color: #000; border-color: #333; }
.result-badge.LOSE { background: #E60012; }
.result-badge.DRAW { background: #888; }

/* Mode Stats */
.mode-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: #fafafa;
  flex-wrap: wrap;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
}
.stat-badge.udemae { color: #fff; }
.stat-badge.power { background: #333; color: #EAFF3D; }
.stat-badge.power.x-match { color: #00EBA7; }
.stat-badge.power.fest { color: #F54E93; }
.stat-badge.power.league { color: #fff; }
.power-icon { width: 18px; height: 18px; }
.power-label { font-size: 10px; opacity: 0.8; }
.event-name { font-size: 12px; color: #666; font-weight: 600; }

/* Awards */
.awards-section {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px 20px;
  justify-content: center;
  border-bottom: 1px solid #f0f0f0;
}

.award-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f5f5f5;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}
.award-icon { width: 22px; height: 22px; }

/* Teams */
.teams-container { padding: 20px; }

.team-section { margin-bottom: 20px; }
.team-section:last-child { margin-bottom: 0; }

.team-header {
  border-left: 5px solid #888;
  padding-left: 12px;
  margin-bottom: 12px;
}
.team-label { font-size: 15px; font-weight: 800; color: #333; }

.player-list { display: flex; flex-direction: column; gap: 8px; }

.player-card {
  background: #f5f5f5;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}
.player-card:hover { background: #efefef; }
.player-card.is-myself { background: #EAFF3D; border: 2px solid #333; }
.player-card.is-myself:hover { background: #e0f030; }

.player-main {
  display: grid;
  grid-template-columns: auto 140px 1fr auto;
  align-items: center;
  padding: 8px 14px;
  gap: 12px;
}

.weapons-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.weapon-main { width: 36px; height: 36px; object-fit: contain; }
.sub-special { display: flex; flex-direction: column; gap: 2px; }
.weapon-sub, .weapon-special { width: 18px; height: 18px; object-fit: contain; opacity: 0.85; }

.player-name {
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}
.player-byname {
  font-size: 10px;
  color: #666;
  font-weight: 600;
  line-height: 1.2;
}
.player-name-text {
  font-weight: 700;
  font-size: 14px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  display: flex;
  align-items: baseline;
}
.name-id {
  font-size: 11px;
  color: #999;
  font-weight: 400;
  margin-left: 2px;
}
.crown { margin-left: 4px; }

.kda {
  font-weight: 700;
  font-size: 14px;
  font-family: monospace;
  text-align: center;
  min-width: 55px;
}
.kda .k { color: #333; }
.kda .k .a { font-size: 0.8em; color: #888; }
.kda .d { color: #888; }

.sp-tag {
  background: #333;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  min-width: 32px;
  text-align: center;
}

.paint {
  font-size: 12px;
  color: #19D719;
  font-weight: 700;
  min-width: 40px;
  text-align: right;
}

.stats-group {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  min-width: 130px;
  justify-content: flex-end;
}

/* Skills Inline */
.skills-inline {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 6px;
}

.gear-row {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  padding: 3px 4px;
}

.skill {
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 3px;
  background: #fff;
  color: #333;
  white-space: nowrap;
}
.skill.main { background: #333; color: #fff; font-weight: 700; }
.skill.sub { background: #333; color: #fff; }

.skill-img {
  object-fit: contain;
  border-radius: 50%;
  flex-shrink: 0;
}
.skill-img.main {
  width: 36px;
  height: 36px;
  background: #333;
  padding: 3px;
}
.skill-img.sub {
  width: 29px;
  height: 29px;
  background: #333;
  padding: 2px;
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
}

.empty-state.error {
  color: #E60012;
}
</style>
