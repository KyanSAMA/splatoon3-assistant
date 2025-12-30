<script setup>
import { computed } from 'vue'

const props = defineProps({
  stageId: { type: Number, required: true },
  name: { type: String, required: true },
  stageMap: { type: Object, default: () => ({}) },
  stats: { type: Object, default: null },
  bestWeapons: { type: Array, default: () => [] },
  vsRule: { type: String, default: null }
})

const stageCode = computed(() => {
  return props.stageMap[props.stageId]?.code || 'Unknown'
})

const imageUrl = computed(() => {
  return `/static/stage/${stageCode.value}.png`
})

const winRate = computed(() => {
  if (!props.stats?.win_rate || !props.vsRule) return null
  const rate = props.stats.win_rate[props.vsRule]
  return rate != null ? rate : null
})

const winRatePercent = computed(() => {
  if (winRate.value == null) return null
  return (winRate.value * 100).toFixed(1)
})

const winRateClass = computed(() => {
  if (winRate.value == null) return ''
  if (winRate.value >= 0.55) return 'high'
  if (winRate.value <= 0.45) return 'low'
  return 'mid'
})

const getWeaponRateClass = (rate) => {
  if (rate >= 0.55) return 'high'
  if (rate <= 0.45) return 'low'
  return 'mid'
}

const handleImageError = (e) => {
  if (e.target.src.includes('Unknown.png')) return
  e.target.src = '/static/stage/Unknown.png'
}
</script>

<template>
  <div class="stage-card">
    <div class="image-wrapper">
      <img :src="imageUrl" :alt="name" loading="lazy" @error="handleImageError" />
      <div v-if="winRatePercent != null" class="win-rate-badge" :class="winRateClass">
        <span class="rate-value">{{ winRatePercent }}<small>%</small></span>
      </div>
    </div>

    <div class="info">
      <h3 class="name" :title="name">{{ name }}</h3>

      <div v-if="bestWeapons.length" class="weapons-section">
        <div class="weapons-list">
          <div v-for="weapon in bestWeapons" :key="weapon.weapon_id" class="weapon-item">
            <div class="weapon-icon-wrapper">
              <img
                :src="`/static/weapon/${weapon.weapon_code}.png`"
                :alt="weapon.weapon_name"
                :title="weapon.weapon_name"
                class="weapon-icon"
              />
            </div>
            <span class="weapon-rate" :class="getWeaponRateClass(weapon.win_rate)">
              {{ (weapon.win_rate * 100).toFixed(0) }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stage-card {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
}

.stage-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #2c2c2c;
  overflow: hidden;
}

.image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.stage-card:hover .image-wrapper img {
  transform: scale(1.05);
}

.win-rate-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 4px 10px;
  border-radius: 20px;
  color: white;
  font-weight: 800;
  font-size: 14px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  backdrop-filter: blur(4px);
  letter-spacing: -0.5px;
  display: flex;
  align-items: baseline;
}

.win-rate-badge small {
  font-size: 0.8em;
  margin-left: 1px;
  opacity: 0.9;
}

.win-rate-badge.high { background: linear-gradient(135deg, #85ea2d, #4ade80); color: #064e3b; }
.win-rate-badge.mid { background: linear-gradient(135deg, #facc15, #fbbf24); color: #451a03; }
.win-rate-badge.low { background: linear-gradient(135deg, #f87171, #ef4444); color: white; }

.info {
  padding: 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.weapons-section {
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px dashed #eee;
}

.weapons-list {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
}

.weapon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.weapon-icon-wrapper {
  width: 32px;
  height: 32px;
  background: #f5f5f5;
  border-radius: 50%;
  padding: 4px;
  box-shadow: inset 0 0 4px rgba(0,0,0,0.05);
}

.weapon-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.1));
}

.weapon-rate {
  font-size: 11px;
  font-weight: 700;
  color: #777;
}

.weapon-rate.high { color: #16a34a; }
.weapon-rate.mid { color: #d97706; }
.weapon-rate.low { color: #dc2626; }
</style>
