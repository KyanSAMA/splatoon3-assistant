# Splatoon3 Assistant - Development Guide

> **同步说明**: 本文件与 `CLAUDE.md` 内容保持一致，修改任意一个时请同时更新另一个。

## 项目简介

Splatoon3 游戏助手 - 通过获取 Splatoon3 的战斗数据及其他辅助数据进行数据分析。

**核心特性**:
- 完整的 NSO 认证流程（参照 splatoon3-nso）
- Token 自动刷新机制（401 错误自动处理）
- 并发安全（asyncio.Lock + 双重检查锁定）
- 明确的异常类型系统
- Token 持久化存储

---

## 项目结构

```
splatoon3-assistant/
├── backend/                      # 后端服务
│   ├── main.py                   # 入口文件
│   ├── requirements.txt          # Python 依赖
│   ├── scripts/
│   │   └── import_weapons.py     # 武器数据导入脚本
│   └── src/
│       ├── api/                  # API 层
│       │   ├── graphql_utils.py  # GraphQL 工具
│       │   └── splatnet3_api.py  # SplatNet3 API
│       ├── auth/                 # 认证模块
│       │   ├── nso_auth.py       # NSO 认证
│       │   └── token_store.py    # Token 持久化
│       ├── core/                 # 核心模块
│       │   ├── config.py         # 配置管理
│       │   ├── exceptions.py     # 异常类型
│       │   └── http_client.py    # HTTP 客户端
│       ├── dao/                  # 数据访问层
│       │   ├── database.py       # 数据库连接
│       │   ├── models/           # ORM 模型
│       │   │   ├── battle.py
│       │   │   ├── coop.py
│       │   │   ├── stage.py
│       │   │   ├── user.py
│       │   │   └── weapon.py
│       │   ├── battle_detail_dao.py
│       │   ├── coop_detail_dao.py
│       │   ├── stage_dao.py
│       │   ├── stage_record_dao.py
│       │   ├── stage_stats_dao.py
│       │   ├── user_dao.py
│       │   ├── weapon_dao.py
│       │   └── weapon_record_dao.py
│       ├── models/               # 业务模型
│       │   ├── skill.py
│       │   ├── stage.py
│       │   ├── user.py
│       │   └── weapon.py
│       ├── services/             # 服务层
│       │   ├── auth_service.py
│       │   ├── battle_detail_refresh_service.py
│       │   ├── coop_detail_refresh_service.py
│       │   ├── splatoon3_data_refresh_service.py
│       │   └── stage_service.py
│       └── utils/                # 工具模块
│           └── id_parser.py
├── frontend/                     # 前端应用
│   ├── dist/                     # 构建输出
│   ├── index.html
│   ├── package.json
│   └── README.md
├── data/                         # 数据文件
│   ├── docs/                     # 游戏文档
│   ├── json/                     # JSON 数据
│   └── langs/zh-CN/              # 中文语言包
├── CLAUDE.md                     # 开发文档
├── GEMINI.md                     # 开发文档（本文件）
├── README.md                     # 项目说明
└── TECHNICAL_ROADMAP.md          # 技术路线
```

---

## 常见问题

### Session Token 过期
**现象**: `SessionExpiredError`
**原因**: 修改密码、长时间未用
**解决**: 清除缓存，重新登录

### NSO 会员过期
**现象**: `MembershipRequiredError`
**原因**: NSO 会员到期
**解决**: 续费 NSO 会员

### Bullet Token 错误
**现象**: `BulletTokenError`（403/499）
**原因**: 版本过时/账号封禁
**解决**: 更新版本/检查账号状态

---

## 修改建议

如果在开发过程中有新的改进建议，请补充到此处。

---

## 前端 UI 规范

### 品牌与版权

- **禁止** 在 UI 中显示 "Nintendo"、"Nintendo Switch" 等任天堂相关文字
- **禁止** 使用任天堂官方 Logo 或图标
- **禁止** 显示 "Not affiliated with Nintendo" 等声明（此为个人项目，无需声明）
- 项目名称统一使用 "Splatoon3 Assistant"

### 设计规范

**图片本地化**:
- Nintendo API 返回的图片 URL 需要认证，无法直接使用
- 解决方案: 通过 URL 中的 hash 值映射到本地图片
- 本地图片路径: `/static/{type}/{code}.png`
- Hash 映射表定义在 `src/enums/{type}/`里

**数据区固定宽度** (解决布局对齐问题):
```css
.stats-group { min-width: 130px; justify-content: flex-end; }
.kda { min-width: 55px; font-family: monospace; }
.sp-tag { min-width: 32px; text-align: center; }
.paint { min-width: 40px; text-align: right; }
```

---

## 静态资源服务

静态图片位于 `frontend/public/static/`，由 Vite 直接提供服务：

| 路径 | 目录 | 用途 |
|------|------|------|
| `/static/stage` | `public/static/stage` | 地图缩略图 |
| `/static/stage_l` | `public/static/stage_l` | 地图大图 |
| `/static/weapon` | `public/static/main_weapon` | 主武器图片 |
| `/static/sub_weapon` | `public/static/sub_weapon` | 副武器图片 |
| `/static/special_weapon` | `public/static/special_weapon` | 大招图片 |
| `/static/skill` | `public/static/skill` | 技能图片 |
| `/static/vs_rule` | `public/static/vs_rule` | 规则图标 |
| `/static/medal` | `public/static/medal` | 奖章图标 |
| `/static/coop_enemy` | `public/static/coop_enemy` | 打工敌人图片 |
| `/static/coop` | `public/static/coop` | 打工通用图片 |
