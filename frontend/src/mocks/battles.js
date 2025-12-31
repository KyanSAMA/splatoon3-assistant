// Mock数据 - 基于真实SQLite数据结构
export const mockBattles = [
  {
    id: 236,
    played_time: '2025-12-30T13:55:57Z',
    vs_mode: 'BANKARA',
    vs_rule: 'AREA',
    judgement: 'LOSE',
    knockout: 'NEITHER',
    bankara_mode: 'OPEN',
    udemae: 'S',
    duration: 322,
    stage: { code: 'Twist', name: '大比目鱼海运中心' },
    awards: [
      { name: '墨汁消耗量 No.1', rank: 'GOLD' },
      { name: '同伴跳躍目標 No.1', rank: 'SILVER' }
    ],
    teams: [
      {
        team_role: 'OTHER',
        team_order: 1,
        score: 90,
        color: { r: 0.105882399, g: 0.749019623, b: 0.670588315, a: 1.0 },
        players: [
          { weapon_id: 3030, name: 'イカカモネ', k: 12, d: 7, a: 3, sp: 5, p: 1863, is_myself: 0, crown: 0 },
          { weapon_id: 10, name: 'キリギリス', k: 12, d: 8, a: 3, sp: 6, p: 1728, is_myself: 0, crown: 0 },
          { weapon_id: 7012, name: ':}～{:', k: 12, d: 3, a: 4, sp: 3, p: 1199, is_myself: 0, crown: 0 },
          { weapon_id: 31, name: 'ぶりぴー', k: 5, d: 9, a: 3, sp: 4, p: 1428, is_myself: 0, crown: 0 }
        ]
      },
      {
        team_role: 'MY',
        team_order: 2,
        score: 76,
        color: { r: 0.768627524, g: 0.227450997, b: 0.435294092, a: 1.0 },
        players: [
          { weapon_id: 41, name: 'ķìľľ', k: 16, d: 9, a: 2, sp: 5, p: 1494, is_myself: 0, crown: 0 },
          { weapon_id: 31, name: 'rice', k: 6, d: 6, a: 1, sp: 11, p: 2151, is_myself: 0, crown: 0 },
          { weapon_id: 2030, name: 'メロンパン', k: 7, d: 4, a: 1, sp: 5, p: 1086, is_myself: 0, crown: 0 },
          { weapon_id: 7030, name: 'わくここね', k: 3, d: 9, a: 1, sp: 7, p: 1512, is_myself: 1, crown: 0 }
        ]
      }
    ]
  },
  {
    id: 237,
    played_time: '2025-12-30T13:49:22Z',
    vs_mode: 'BANKARA',
    vs_rule: 'AREA',
    judgement: 'WIN',
    knockout: 'NEITHER',
    bankara_mode: 'OPEN',
    udemae: 'S',
    duration: 300,
    stage: { code: 'Factory', name: '鱼露遗迹' },
    awards: [
      { name: '奪目時間 No.1', rank: 'GOLD' },
      { name: '同伴跳躍目標 No.1', rank: 'GOLD' },
      { name: '墨汁消耗量 No.1', rank: 'SILVER' }
    ],
    teams: [
      {
        team_role: 'MY',
        team_order: 1,
        score: 72,
        color: { r: 0.117647097, g: 0.752941191, b: 0.678431392, a: 1.0 },
        players: [
          { weapon_id: 41, name: 'ķìľľ', k: 14, d: 11, a: 1, sp: 2, p: 1182, is_myself: 0, crown: 0 },
          { weapon_id: 7030, name: 'わくここね', k: 11, d: 8, a: 4, sp: 6, p: 1320, is_myself: 1, crown: 0 },
          { weapon_id: 31, name: 'rice', k: 10, d: 6, a: 2, sp: 11, p: 2073, is_myself: 0, crown: 0 },
          { weapon_id: 2030, name: 'メロンパン', k: 4, d: 4, a: 1, sp: 3, p: 848, is_myself: 0, crown: 0 }
        ]
      },
      {
        team_role: 'OTHER',
        team_order: 2,
        score: 68,
        color: { r: 0.847058773, g: 0.294117689, b: 0.196078405, a: 1.0 },
        players: [
          { weapon_id: 3005, name: 'おなすびプロシュート', k: 14, d: 11, a: 3, sp: 2, p: 1142, is_myself: 0, crown: 0 },
          { weapon_id: 7020, name: 'yu-uABXY', k: 9, d: 6, a: 1, sp: 4, p: 1188, is_myself: 0, crown: 0 },
          { weapon_id: 100, name: 'かがみもち', k: 6, d: 2, a: 1, sp: 8, p: 1905, is_myself: 0, crown: 0 },
          { weapon_id: 1042, name: '「なにもない」', k: 6, d: 12, a: 1, sp: 5, p: 1092, is_myself: 0, crown: 0 }
        ]
      }
    ]
  },
  {
    id: 238,
    played_time: '2025-12-30T13:43:04Z',
    vs_mode: 'BANKARA',
    vs_rule: 'LOFT',
    judgement: 'LOSE',
    knockout: 'LOSE',
    bankara_mode: 'CHALLENGE',
    udemae: 'S+',
    duration: 204,
    stage: { code: 'Twist', name: '大比目鱼海运中心' },
    awards: [{ name: '擊倒敵方王牌 No.1', rank: 'GOLD' }],
    teams: [
      {
        team_role: 'OTHER',
        team_order: 1,
        score: 100,
        color: { r: 0.117647097, g: 0.752941191, b: 0.678431392, a: 1.0 },
        players: [
          { weapon_id: 201, name: 'いおりまる', k: 10, d: 6, a: 0, sp: 3, p: 812, is_myself: 0, crown: 1 },
          { weapon_id: 4020, name: 'レイ', k: 5, d: 1, a: 2, sp: 3, p: 1007, is_myself: 0, crown: 0 },
          { weapon_id: 10, name: 'moca', k: 4, d: 4, a: 1, sp: 3, p: 973, is_myself: 0, crown: 0 },
          { weapon_id: 40, name: 'しゃけちゃずけ', k: 8, d: 7, a: 0, sp: 2, p: 908, is_myself: 0, crown: 0 }
        ]
      },
      {
        team_role: 'MY',
        team_order: 2,
        score: 0,
        color: { r: 0.847058773, g: 0.294117689, b: 0.196078405, a: 1.0 },
        players: [
          { weapon_id: 1, name: 'rice', k: 9, d: 7, a: 1, sp: 3, p: 814, is_myself: 0, crown: 0 },
          { weapon_id: 41, name: 'ķìľľ', k: 8, d: 7, a: 3, sp: 2, p: 1001, is_myself: 0, crown: 0 },
          { weapon_id: 7011, name: 'メロンパン', k: 1, d: 2, a: 1, sp: 3, p: 953, is_myself: 0, crown: 0 },
          { weapon_id: 7030, name: 'わくここね', k: 7, d: 8, a: 2, sp: 3, p: 676, is_myself: 1, crown: 0 }
        ]
      }
    ]
  },
  {
    id: 239,
    played_time: '2024-12-30T13:36:47Z',
    vs_mode: 'REGULAR',
    vs_rule: 'TURF_WAR',
    judgement: 'WIN',
    knockout: null,
    bankara_mode: null,
    udemae: null,
    duration: 180,
    stage: { code: 'Twist', name: '大比目鱼海运中心' },
    awards: [{ name: '超级涂地王 No.1', rank: 'GOLD' }],
    teams: [
      {
        team_role: 'MY',
        team_order: 1,
        score: null,
        paint_ratio: 0.523,
        color: { r: 0.435294092, g: 0.0156862792, b: 0.713725507, a: 1.0 },
        players: [
          { weapon_id: 7030, name: 'わくここね', k: 5, d: 3, a: 2, sp: 4, p: 1350, is_myself: 1, crown: 0 }
        ]
      },
      {
        team_role: 'OTHER',
        team_order: 2,
        score: null,
        paint_ratio: 0.477,
        color: { r: 0.80392158, g: 0.317647099, b: 0.0392156914, a: 1.0 },
        players: []
      }
    ]
  },
  {
    id: 240,
    played_time: '2025-12-30T12:50:00Z',
    vs_mode: 'X_MATCH',
    vs_rule: 'GOAL',
    judgement: 'WIN',
    knockout: 'WIN',
    bankara_mode: null,
    udemae: null,
    x_power: 2145.5,
    duration: 156,
    stage: { code: 'Factory', name: '鱼露遗迹' },
    awards: [{ name: '强力KO达成 No.1', rank: 'GOLD' }],
    teams: [
      {
        team_role: 'MY',
        team_order: 1,
        score: 100,
        color: { r: 0.749019623, g: 0.807843089, b: 0.254902005, a: 1.0 },
        players: [
          { weapon_id: 7030, name: 'わくここね', k: 12, d: 2, a: 5, sp: 4, p: 1580, is_myself: 1, crown: 1 }
        ]
      },
      {
        team_role: 'OTHER',
        team_order: 2,
        score: 23,
        color: { r: 0.388235301, g: 0.149019599, b: 0.80392158, a: 1.0 },
        players: []
      }
    ]
  },
  {
    id: 241,
    played_time: '2025-12-30T13:23:20Z',
    vs_mode: 'BANKARA',
    vs_rule: 'CLAM',
    judgement: 'WIN',
    knockout: 'NEITHER',
    bankara_mode: 'CHALLENGE',
    udemae: 'S+',
    duration: 300,
    stage: { code: 'Twist', name: '大比目鱼海运中心' },
    awards: [{ name: '特殊武器使用次數 No.1', rank: 'SILVER' }],
    teams: [
      {
        team_role: 'MY',
        team_order: 1,
        score: 86,
        color: { r: 0.749019623, g: 0.807843089, b: 0.254902005, a: 1.0 },
        players: [
          { weapon_id: 7030, name: 'わくここね', k: 8, d: 5, a: 3, sp: 8, p: 1420, is_myself: 1, crown: 0 }
        ]
      },
      {
        team_role: 'OTHER',
        team_order: 2,
        score: 66,
        color: { r: 0.388235301, g: 0.149019599, b: 0.80392158, a: 1.0 },
        players: []
      }
    ]
  },
  {
    id: 242,
    played_time: '2025-12-29T20:15:00Z',
    vs_mode: 'LEAGUE',
    vs_rule: 'AREA',
    judgement: 'WIN',
    knockout: 'NEITHER',
    bankara_mode: null,
    udemae: null,
    duration: 280,
    stage: { code: 'Factory', name: '鱼露遗迹' },
    awards: [],
    teams: [
      {
        team_role: 'MY',
        team_order: 1,
        score: 100,
        color: { r: 0.2, g: 0.8, b: 0.4, a: 1.0 },
        players: [
          { weapon_id: 7030, name: 'わくここね', k: 10, d: 4, a: 2, sp: 5, p: 1600, is_myself: 1, crown: 0 }
        ]
      },
      {
        team_role: 'OTHER',
        team_order: 2,
        score: 45,
        color: { r: 0.8, g: 0.2, b: 0.6, a: 1.0 },
        players: []
      }
    ]
  },
  {
    id: 243,
    played_time: '2025-12-29T19:30:00Z',
    vs_mode: 'FEST',
    vs_rule: 'TURF_WAR',
    judgement: 'LOSE',
    knockout: null,
    bankara_mode: null,
    udemae: null,
    fest_power: 1850.0,
    duration: 180,
    stage: { code: 'Twist', name: '大比目鱼海运中心' },
    awards: [{ name: '涂地面积 No.1', rank: 'SILVER' }],
    teams: [
      {
        team_role: 'MY',
        team_order: 1,
        score: null,
        paint_ratio: 0.42,
        color: { r: 1.0, g: 0.4, b: 0.1, a: 1.0 },
        players: [
          { weapon_id: 7030, name: 'わくここね', k: 3, d: 6, a: 1, sp: 3, p: 1200, is_myself: 1, crown: 0 }
        ]
      },
      {
        team_role: 'OTHER',
        team_order: 2,
        score: null,
        paint_ratio: 0.58,
        color: { r: 0.1, g: 0.5, b: 0.9, a: 1.0 },
        players: []
      }
    ]
  },
  {
    id: 244,
    played_time: '2025-12-30T13:10:35Z',
    vs_mode: 'BANKARA',
    vs_rule: 'AREA',
    judgement: 'DRAW',
    knockout: null,
    bankara_mode: 'OPEN',
    udemae: 'S',
    duration: 65,
    stage: { code: 'Factory', name: '鱼露遗迹' },
    awards: [],
    teams: [
      {
        team_role: 'MY',
        team_order: 99,
        score: null,
        color: { r: 0.172549993, g: 0.721568584, b: 0.133333296, a: 1.0 },
        players: []
      },
      {
        team_role: 'OTHER',
        team_order: 99,
        score: null,
        color: { r: 0.756862819, g: 0.176470593, b: 0.454901993, a: 1.0 },
        players: []
      }
    ]
  }
]

export const mockWeapons = {
  7030: { code: 7030, name: '邦普V', class: '弓' },
  7020: { code: 7020, name: 'LACT-450', class: '弓' },
  7011: { code: 7011, name: '三发猎鱼弓 联名', class: '弓' },
  7012: { code: 7012, name: '三发猎鱼弓 灯', class: '弓' },
  41: { code: 41, name: '斯普拉射击枪 联名', class: '射击枪' },
  40: { code: 40, name: '斯普拉射击枪', class: '射击枪' },
  31: { code: 31, name: '专业模型枪RG', class: '射击枪' },
  2030: { code: 2030, name: '公升4K', class: '狙击枪' },
  1: { code: 1, name: '广域标记枪 新型', class: '射击枪' },
  10: { code: 10, name: '新叶射击枪', class: '射击枪' },
  100: { code: 100, name: '太空射击枪', class: '射击枪' },
  201: { code: 201, name: '新星爆破枪 新型', class: '爆破枪' },
  50: { code: 50, name: '.52加仑', class: '射击枪' },
  60: { code: 60, name: 'N-ZAP85', class: '射击枪' },
  4020: { code: 4020, name: '消防栓旋转枪', class: '旋转枪' },
  3030: { code: 3030, name: '满溢泡澡泼桶', class: '泼桶' },
  3005: { code: 3005, name: '秩序泼桶 复制', class: '泼桶' },
  1042: { code: 1042, name: '宽滚筒 惑', class: '滚筒' }
}

// 对手武器统计 - 胜场
export const mockOpponentStatsWin = [
  { weapon_id: 3005, name: '秩序泼桶 复制', count: 8 },
  { weapon_id: 7020, name: 'LACT-450', count: 6 },
  { weapon_id: 100, name: '太空射击枪', count: 5 },
  { weapon_id: 1042, name: '宽滚筒 惑', count: 4 },
  { weapon_id: 41, name: '斯普拉射击枪 联名', count: 22 },
  { weapon_id: 31, name: '专业模型枪RG', count: 18 }
]

// 对手武器统计 - 败场
export const mockOpponentStatsLose = [
  { weapon_id: 3030, name: '满溢泡澡泼桶', count: 12 },
  { weapon_id: 10, name: '新叶射击枪', count: 10 },
  { weapon_id: 7012, name: '三发猎鱼弓 灯', count: 8 },
  { weapon_id: 31, name: '专业模型枪RG', count: 35 },
  { weapon_id: 201, name: '新星爆破枪 新型', count: 7 },
  { weapon_id: 4020, name: '消防栓旋转枪', count: 28 },
  { weapon_id: 40, name: '斯普拉射击枪', count: 27 }
]

// 胜率排行
export const mockWinRateRanking = [
  { weapon_id: 3005, name: '秩序泼桶 复制', win: 8, total: 10, rate: 80 },
  { weapon_id: 7020, name: 'LACT-450', win: 6, total: 9, rate: 67 },
  { weapon_id: 100, name: '太空射击枪', win: 5, total: 8, rate: 63 },
  { weapon_id: 1042, name: '宽滚筒 惑', win: 4, total: 7, rate: 57 },
  { weapon_id: 41, name: '斯普拉射击枪 联名', win: 22, total: 54, rate: 41 },
  { weapon_id: 31, name: '专业模型枪RG', win: 18, total: 53, rate: 34 }
]

// 败率排行
export const mockLoseRateRanking = [
  { weapon_id: 4020, name: '消防栓旋转枪', lose: 28, total: 42, rate: 67 },
  { weapon_id: 3030, name: '满溢泡澡泼桶', lose: 12, total: 20, rate: 60 },
  { weapon_id: 10, name: '新叶射击枪', lose: 10, total: 18, rate: 56 },
  { weapon_id: 31, name: '专业模型枪RG', lose: 35, total: 53, rate: 66 },
  { weapon_id: 40, name: '斯普拉射击枪', lose: 27, total: 42, rate: 64 }
]

// 总体战绩统计
export const mockTotalStats = {
  total: 156,
  win: 89,
  lose: 65,
  draw: 2,
  winRate: 57,
  byMode: {
    REGULAR: { total: 32, win: 18, lose: 14, winRate: 56 },
    BANKARA_OPEN: { total: 45, win: 24, lose: 20, draw: 1, winRate: 53 },
    BANKARA_CHALLENGE: { total: 38, win: 22, lose: 16, winRate: 58 },
    X_MATCH: { total: 25, win: 16, lose: 9, winRate: 64 },
    LEAGUE: { total: 12, win: 7, lose: 5, winRate: 58 },
    FEST: { total: 4, win: 2, lose: 1, draw: 1, winRate: 50 }
  }
}

export function getBattleById(id) {
  return mockBattles.find(b => b.id === parseInt(id))
}

export function rgbaToCSS(color) {
  if (!color) return '#888'
  return `rgba(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)}, ${color.a})`
}
