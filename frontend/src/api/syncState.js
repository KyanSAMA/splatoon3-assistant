import { ref, readonly } from 'vue'

const _isGlobalSyncing = ref(false)

export const isGlobalSyncing = readonly(_isGlobalSyncing)

export function setGlobalSyncing(val) {
  _isGlobalSyncing.value = val
}
