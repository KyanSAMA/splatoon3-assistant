<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  step: { type: Number, default: 0 },
  message: { type: String, default: '' },
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const isMinimized = ref(false)
const backdropMouseDown = ref(false)

const progress = computed(() => Math.min(Math.max(props.step * 25, 0), 100))

watch(() => props.modelValue, (val) => {
  if (val) isMinimized.value = false
})

const handleBackdropMouseDown = (e) => {
  if (e.target === e.currentTarget) backdropMouseDown.value = true
}

const handleBackdropMouseUp = (e) => {
  if (e.target === e.currentTarget && backdropMouseDown.value) {
    isMinimized.value = true
  }
  backdropMouseDown.value = false
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="sync-wrapper">
        <!-- Minimized Mode -->
        <Transition name="scale">
          <div
            v-if="isMinimized"
            class="minimized-widget"
            @click="isMinimized = false"
            role="button"
            aria-label="展开同步进度"
          >
            <div class="mini-spinner"></div>
            <span class="mini-text">{{ progress }}%</span>
          </div>
        </Transition>

        <!-- Expanded Mode -->
        <Transition name="pop">
          <div
            v-if="!isMinimized"
            class="sync-overlay"
            role="alertdialog"
            aria-modal="true"
            aria-label="数据同步中"
            @mousedown="handleBackdropMouseDown"
            @mouseup="handleBackdropMouseUp"
          >
            <div class="sync-card" @mousedown.stop>
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
                <p class="minimize-hint">点击空白处可最小化</p>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sync-wrapper {
  position: relative;
  z-index: 9999;
  pointer-events: none;
}

.sync-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  pointer-events: auto;
}

/* Minimized Widget */
.minimized-widget {
  position: fixed;
  top: 70px;
  right: 20px;
  width: 44px;
  height: 44px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10000;
  overflow: hidden;
  border: 2px solid #603BFF;
  pointer-events: auto;
}

.mini-spinner {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #EAFF3D;
  border-right-color: #E60012;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.mini-text {
  font-size: 11px;
  font-weight: 800;
  color: #603BFF;
  font-family: monospace;
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

.minimize-hint {
  margin-top: 16px;
  font-size: 12px;
  color: #999;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes moveStripe {
  0% { background-position: 0 0; }
  100% { background-position: 24px 24px; }
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.pop-enter-active, .pop-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.pop-enter-from, .pop-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.scale-enter-active, .scale-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: top right;
}
.scale-enter-from, .scale-leave-to {
  opacity: 0;
  transform: translate(12px, -12px) scale(0);
}
</style>
