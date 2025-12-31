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
