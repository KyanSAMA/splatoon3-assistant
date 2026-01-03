<script setup>
import { computed } from 'vue'

const props = defineProps({
  step: {
    type: Number,
    default: 0
  },
  message: {
    type: String,
    default: ''
  }
})

const progress = computed(() => Math.min(Math.max(props.step * 25, 0), 100))
</script>

<template>
  <Teleport to="body">
    <div
      class="sync-overlay"
      role="alertdialog"
      aria-modal="true"
      aria-label="数据同步中"
    >
      <div class="sync-card">
        <div class="ink-splat top-splat"></div>
        <div class="ink-splat bottom-splat"></div>

        <div class="content">
          <div class="loading-spinner"></div>
          <h3 class="sync-title">数据同步中</h3>
          <p class="sync-message" aria-live="polite">{{ message || '准备中...' }}</p>

          <div
            class="progress-track"
            role="progressbar"
            :aria-valuenow="progress"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div class="progress-bar" :style="{ width: `${progress}%` }">
              <div class="progress-glow"></div>
            </div>
          </div>
          <div class="progress-text">{{ progress }}%</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.sync-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.sync-card {
  position: relative;
  width: 90%;
  max-width: 320px;
  background: #fff;
  border-radius: 24px;
  padding: 40px 30px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.content {
  position: relative;
  z-index: 2;
}

.ink-splat {
  position: absolute;
  z-index: 1;
  opacity: 0.08;
  pointer-events: none;
}

.top-splat {
  top: -40px;
  right: -40px;
  width: 160px;
  height: 160px;
  background: #E60012;
  border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
  transform: rotate(45deg);
}

.bottom-splat {
  bottom: -30px;
  left: -30px;
  width: 130px;
  height: 130px;
  background: #603BFF;
  border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
  transform: rotate(-15deg);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 5px solid #f0f0f0;
  border-top-color: #603BFF;
  border-right-color: #EAFF3D;
  border-radius: 50%;
  margin: 0 auto 20px;
  animation: spin 1s linear infinite;
}

.sync-title {
  font-size: 20px;
  font-weight: 800;
  color: #2d2d2d;
  margin-bottom: 8px;
}

.sync-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 24px;
  min-height: 1.5em;
}

.progress-track {
  height: 14px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  margin-bottom: 12px;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #E60012, #ff4d4d);
  border-radius: 10px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.progress-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    45deg,
    rgba(255,255,255,0.2) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255,255,255,0.2) 50%,
    rgba(255,255,255,0.2) 75%,
    transparent 75%,
    transparent
  );
  background-size: 24px 24px;
  animation: moveStripe 1s linear infinite;
}

.progress-text {
  font-family: monospace;
  font-weight: 700;
  color: #E60012;
  font-size: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes moveStripe {
  0% { background-position: 0 0; }
  100% { background-position: 24px 24px; }
}

@keyframes popIn {
  from { opacity: 0; transform: scale(0.9) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
