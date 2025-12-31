/**
 * Session 状态管理
 * 用于处理全局 session 过期事件
 */

// Session 过期事件监听器
const listeners = new Set()

/**
 * 监听 session 过期事件
 * @param {Function} callback 回调函数
 * @returns {Function} 取消监听函数
 */
export function onSessionExpired(callback) {
  listeners.add(callback)
  return () => listeners.delete(callback)
}

/**
 * 触发 session 过期事件
 */
export function emitSessionExpired() {
  listeners.forEach(cb => cb())
}

/**
 * 检查 API 响应是否为 session 过期错误
 * @param {Response} response fetch 响应对象
 * @returns {Promise<boolean>} 是否为 session 过期
 */
export async function checkSessionExpired(response) {
  if (response.status === 401) {
    try {
      const data = await response.clone().json()
      // 检查两种格式：字符串 detail 或对象 detail.code
      if (data.detail?.code === 'SESSION_EXPIRED' ||
          (typeof data.detail === 'string' && data.detail.includes('Session'))) {
        emitSessionExpired()
        return true
      }
    } catch {
      // 无法解析 JSON，可能是其他 401 错误
    }
  }
  return false
}
