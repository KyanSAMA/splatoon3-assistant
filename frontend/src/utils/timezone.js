/**
 * 时区工具模块
 * 抽象时区处理逻辑，便于后续添加时区设置功能
 */

// 时区模式：'local' 使用浏览器本地时区，数字表示固定偏移（小时）
const DEFAULT_TIMEZONE = 'local'

/**
 * 获取当前配置的时区设置
 * @returns {'local' | number} 'local' 或时区偏移小时数
 */
export const getTimezone = () => {
  // 未来可扩展：从 localStorage 读取用户设置
  // const userTz = localStorage.getItem('timezone')
  // if (userTz !== null) {
  //   return userTz === 'local' ? 'local' : parseInt(userTz, 10)
  // }
  return DEFAULT_TIMEZONE
}

/**
 * 将 UTC 时间字符串转换为目标时区的 Date 对象
 * @param {string} isoString - ISO 格式的 UTC 时间字符串
 * @returns {Date} 调整后的 Date 对象
 */
export const toLocalDate = (isoString) => {
  const tz = getTimezone()
  const utcDate = new Date(isoString)

  if (tz === 'local') {
    // 使用浏览器本地时区，new Date() 已自动转换
    return utcDate
  }

  // 使用固定时区偏移：先获取 UTC 时间戳，再加上偏移
  const utcTime = utcDate.getTime() + utcDate.getTimezoneOffset() * 60 * 1000
  return new Date(utcTime + tz * 60 * 60 * 1000)
}

/**
 * 格式化时间显示
 * @param {string} isoString - ISO 格式的 UTC 时间字符串
 * @param {object} options - 格式化选项
 * @param {boolean} options.showSeconds - 是否显示秒，默认 true
 * @param {boolean} options.showYear - 是否总是显示年份，默认 false（仅非当前年份显示）
 * @returns {string} 格式化后的时间字符串
 */
export const formatDateTime = (isoString, options = {}) => {
  const { showSeconds = true, showYear = false } = options

  const d = toLocalDate(isoString)
  const now = new Date()

  const year = d.getFullYear()
  const month = d.getMonth() + 1
  const day = d.getDate()
  const hours = d.getHours().toString().padStart(2, '0')
  const minutes = d.getMinutes().toString().padStart(2, '0')
  const seconds = d.getSeconds().toString().padStart(2, '0')

  const datePart = `${month}/${day}`
  const timePart = showSeconds ? `${hours}:${minutes}:${seconds}` : `${hours}:${minutes}`

  const isCurrentYear = year === now.getFullYear()

  if (showYear || !isCurrentYear) {
    return `${year}/${datePart} ${timePart}`
  }
  return `${datePart} ${timePart}`
}
