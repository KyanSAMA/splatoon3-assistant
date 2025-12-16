# Splatoon3 Assistant

> 🎮 Splatoon3 游戏助手 - 通过 Nintendo Switch Online API 获取游戏数据

**项目状态**: 🚧 开发中

## ✨ 特性

- 🔐 完整的 NSO 认证流程
- 🔄 Token 自动刷新（无需手动处理过期）
- 📊 完整的 SplatNet3 API 支持
- 💾 安全的 Token 持久化存储
- 🎯 清晰的错误类型和提示

## 🚀 快速开始

### 安装

```bash
# 克隆项目
cd splatoon3-assistant

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 基础使用

#### 完整示例

```python
import asyncio
from src import NSOAuth, SplatNet3API, TokenStore

async def main():
    token_store = TokenStore(".token_cache.json")
    auth = NSOAuth()
    if not token_store.exists():
        # 1. 认证
        url, verifier = await auth.login_in()
        print(f"请访问: {url}")

        callback_url = input("粘贴回调 URL: ")
        session_token = await auth.login_in_2(callback_url, verifier)

        # 2. 获取 tokens
        access_token, g_token, nickname, lang, country, _ = await auth.get_gtoken(session_token)
        bullet_token = await auth.get_bullet(g_token)
    else:
        print("已存在本地文件，将使用本地token")
        session_token, access_token, g_token, bullet_token, user_lang, user_country = token_store.get_tokens_for_api()

    # 3. 创建 API 实例（支持自动刷新）
    api = SplatNet3API(
        nso_auth=auth,
        session_token=session_token,
        access_token=access_token,
        g_token=g_token,
        bullet_token=bullet_token,
        on_tokens_updated=lambda t: token_store.save(t)
    )

    # 4. 使用 API
    try:
        battles = await api.get_recent_battles()
        print(f"✓ 获取到 {len(battles)} 场对战记录")
    except Exception as e:
        print(f"✗ 错误: {e}")
    finally:
        await api.close()

asyncio.run(main())
```

#### 运行测试

```bash
python tests/test_full_flow.py
```

## 📚 API 文档

### 认证

```python
from src import NSOAuth

auth = NSOAuth()
url, verifier = await auth.login_in()
session_token = await auth.login_in_2(callback_url, verifier)
```

### 数据查询

```python
from src import SplatNet3API

api = SplatNet3API(...)

# 对战数据
battles = await api.get_recent_battles()      # 最近对战
bankara = await api.get_bankara_battles()     # 蛮颓对战
x_battles = await api.get_x_battles()         # X 对战

# 打工数据
coops = await api.get_coops()                 # 打工历史
coop_detail = await api.get_coop_detail(id)   # 打工详情

# 其他
friends = await api.get_friends()             # 好友列表
schedule = await api.get_schedule()           # 日程表
```

### Token 持久化

```python
from src import TokenStore

store = TokenStore(".token_cache.json")
store.save({"session_token": "...", "g_token": "...", "bullet_token": "..."})
tokens = store.load()
```

## ⚠️ 常见问题

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| `SessionExpiredError` | session_token 过期 | 重新登录（扫码） |
| `MembershipRequiredError` | NSO 会员过期 | 续费 NSO 会员 |
| `BulletTokenError` | Token 错误 | 检查版本或账号状态 |

## 📁 项目结构

```
splatoon3-assistant/
├── src/                  # 源代码
│   ├── nso_auth.py      # NSO 认证
│   ├── splatnet3_api.py # SplatNet3 API
│   ├── token_store.py   # Token 存储
│   └── exceptions.py    # 异常定义
├── tests/               # 测试文件
├── README.md           # 项目说明（本文件）
├── TECHNICAL_ROADMAP.md # 技术路线
└── CLAUDE.md           # 开发文档
```

## 🔧 技术栈

- Python 3.8+
- httpx (HTTP 客户端)
- beautifulsoup4 (HTML 解析)

## 📝 开发日志

- **2024-12-13**: Token 自动刷新功能
- **2024-12-12**: v4 API 加密支持
- **2024-12-10**: NSO API 集成完成

详细技术路线请查看 [TECHNICAL_ROADMAP.md](TECHNICAL_ROADMAP.md)

## 📄 许可证

本项目仅供学习和个人使用。

## 🙏 致谢

本项目的实现参考了以下开源项目：

- [splatoon3-nso](https://github.com/Cypas/splatoon3-nso) - NSO 认证流程和 GraphQL API 封装的主要参考
- [splatoon3-schedule](https://github.com/Cypas/splatoon3-schedule) - 数据处理和项目架构参考
- [nxapi](https://github.com/samuelthomas2774/nxapi) - NSO API v4 加密支持

感谢 Splatoon3 开源社区的贡献！
