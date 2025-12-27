# Splatoon3 Assistant - 项目开发文档

> **同步说明**: 本文件与 `GEMINI.md` 内容保持一致，修改任意一个时请同时更新另一个。

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
├── src/
│   ├── __init__.py          # 包初始化和导出
│   ├── config.py            # 配置管理
│   ├── http_client.py       # HTTP 客户端封装
│   ├── nso_auth.py          # NSO 认证 (参照 S3S 类)
│   ├── graphql_utils.py     # GraphQL 工具
│   ├── splatnet3_api.py     # SplatNet3 API (参照 Splatoon 类)
│   ├── token_store.py       # Token 持久化存储
│   └── exceptions.py        # 自定义异常类型
├── tests/
│   ├── test_full_flow.py    # 功能测试
│   └── .token_cache.json    # Token 缓存（自动生成）
├── requirements.txt         # Python 依赖
├── README.md               # 用户文档
├── TECHNICAL_ROADMAP.md    # 技术路线
├── CLAUDE.md               # 开发文档（本文件）
└── GEMINI.md               # 开发文档（同步）
```

---

## 核心 API 使用

### NSOAuth - 认证

```python
from src import NSOAuth

auth = NSOAuth()

# 认证流程
url, verifier = await auth.login_in()
session_token = await auth.login_in_2(callback_url, verifier)
access_token, g_token, nickname, lang, country, user_info = await auth.get_gtoken(session_token)
bullet_token = await auth.get_bullet(g_token)
```

### SplatNet3API - 数据查询

```python
from src import SplatNet3API, TokenStore

# 带自动刷新（推荐）
api = SplatNet3API(
    nso_auth=auth,
    session_token="...",
    g_token="...",
    bullet_token="...",
    on_tokens_updated=lambda t: TokenStore(".token_cache.json").save(t)
)

# 简单模式
api = SplatNet3API.simple(g_token="...", bullet_token="...")

# 使用
battles = await api.get_recent_battles()
```

### 异常处理

```python
from src import SessionExpiredError, MembershipRequiredError, BulletTokenError, TokenRefreshError

try:
    result = await api.get_recent_battles()
except SessionExpiredError:
    # 需要重新登录
except MembershipRequiredError:
    # NSO 会员过期
except BulletTokenError as e:
    # Token 错误（版本过时/封禁）
except TokenRefreshError:
    # 刷新失败（网络等）
```

---

## 开发注意事项

### Token 自动刷新机制

**核心流程**:
```
API 请求 → 401 错误 → 自动刷新 Token → 保存 → 重试请求
```

**关键实现**:
- `SplatNet3API.request()`: 检测 401，触发刷新
- `_refresh_tokens()`: 加锁刷新，返回 `(success, token_data)`
- 并发控制: `asyncio.Lock` + 双重检查锁定
- 回调在锁外执行，避免死锁

**并发安全**:
```python
async with self._refresh_lock:
    if self._is_refreshing:
        return (True, None)  # 复用其他协程的刷新结果

    self._is_refreshing = True
    # 执行刷新...
    self._is_refreshing = False
```

### 异常类型设计

| 异常 | 用途 | 处理方式 |
|------|------|---------|
| `SessionExpiredError` | session_token 过期 | 引导重新登录 |
| `MembershipRequiredError` | NSO 会员过期 | 提示续费 |
| `BulletTokenError` | Bullet token 错误 | 检查版本/状态 |
| `TokenRefreshError` | 刷新失败 | 重试/检查网络 |

### 最佳实践

**1. 使用 TokenStore 管理持久化**
```python
store = TokenStore(".token_cache.json")
api = SplatNet3API(on_tokens_updated=lambda t: store.save(t))
```

**2. 回调函数保持简单**
```python
# ✅ 推荐
on_tokens_updated=lambda t: store.save(t)

# ❌ 不推荐（会死锁）
on_tokens_updated=lambda t: await api.get_home()
```

**3. 正确的异常处理**
```python
# ✅ 区分异常类型
try:
    result = await api.get_recent_battles()
except SessionExpiredError:
    handle_relogin()
except MembershipRequiredError:
    notify_membership_expired()

# ❌ 捕获所有异常
except Exception:
    pass  # 丢失错误信息
```

---

## 开发日志

### 2024-12-13: Token 自动刷新功能

**实现功能**:
- [x] 401 错误自动检测和刷新
- [x] 并发刷新控制（asyncio.Lock + DCL）
- [x] 明确的异常类型系统
- [x] TokenStore 持久化（原子写入）
- [x] 回调机制（锁外执行）

**代码质量**:
- 经过 3 轮 Codex review
- 修复返回值类型不一致
- 修复回调死锁问题
- 完善异常传播机制

**技术细节**: 详见 `TECHNICAL_ROADMAP.md`

### 2024-12-12: v4 API 加密支持

- [x] 升级到 v4 API
- [x] nxapi 加密/解密功能
- [x] OAuth scope: `ca:gf ca:er ca:dr`

### 2024-12-10: NSO API 集成完成

- [x] 完整认证流程（参照 S3S 类）
- [x] GraphQL API 封装（参照 Splatoon 类）
- [x] 功能测试文件

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
