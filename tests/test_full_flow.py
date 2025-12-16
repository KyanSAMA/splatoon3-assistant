#!/usr/bin/env python3
"""
Splatoon3 Assistant - 功能测试

完整的NSO登录到获取API数据流程（参照 splatoon3-nso/handle/login.py）

使用方法:
    cd splatoon3-assistant
    source .venv/bin/activate
    python tests/test_full_flow.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    NSOAuth,
    SplatNet3API,
    TokenStore,
    SessionExpiredError,
    MembershipRequiredError,
    BulletTokenError,
    TokenRefreshError
)


#============================================================
# Token 缓存管理
# ============================================================

TOKEN_CACHE_FILE = Path(__file__).parent / ".token_cache.json"


def load_cached_tokens() -> Optional[dict]:
    """加载缓存的 tokens"""
    if TOKEN_CACHE_FILE.exists():
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                data = json.load(f)
                print(f"✓ 从缓存加载 tokens: {TOKEN_CACHE_FILE}")
                return data
        except Exception as e:
            print(f"⚠ 加载缓存失败: {e}")
    return None


def save_tokens(tokens: dict) -> None:
    """保存 tokens 到缓存"""
    try:
        with open(TOKEN_CACHE_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        print(f"✓ Tokens 已保存到: {TOKEN_CACHE_FILE}")
    except Exception as e:
        print(f"⚠ 保存缓存失败: {e}")


def clear_token_cache() -> None:
    """清除 token 缓存"""
    if TOKEN_CACHE_FILE.exists():
        TOKEN_CACHE_FILE.unlink()
        print("✓ Token 缓存已清除")


# ============================================================
# 登录流程（参照 splatoon3-nso/handle/login.py）
# ============================================================

async def login_flow() -> dict:
    """完整的 NSO 登录流程"""
    print("\n" + "=" * 60)
    print("NSO 登录流程")
    print("=" * 60)
    
    # 重置缓存版本
    NSOAuth.reset_cached_versions()
    
    auth = NSOAuth()
    
    # Step 1: 生成登录 URL (对应 s3s.login_in())
    print("\n[Step 1] 生成 Nintendo 登录 URL...")
    url, verifier = await auth.login_in()
    
    print("\n请在浏览器中打开以下链接并登录 Nintendo 账号:")
    print("-" * 60)
    print(url)
    print("-" * 60)
    
    print("\n登录完成后，会跳转到一个以 'npf71b963c1b7b6d119://auth' 开头的页面。")
    print("请复制该页面的完整 URL（右键复制链接）。")
    
    # Step 2: 获取 session_token (对应 s3s.login_in_2())
    callback_url = input("\n请粘贴回调 URL: ").strip()
    
    if not callback_url:
        raise ValueError("未输入回调 URL")
    
    print("\n[Step 2] 获取 session_token...")
    session_token = await auth.login_in_2(callback_url, verifier)
    
    if not session_token:
        raise ValueError("获取 session_token 失败")
    
    print(f"✓ session_token: {session_token[:20]}...")
    
    # Step 3: 获取 g_token (对应 s3s.get_gtoken())
    print("\n[Step 3] 获取 g_token...")
    access_token, g_token, nickname, lang, country, user_info = await auth.get_gtoken(session_token)
    
    print(f"✓ g_token: {g_token[:20]}...")
    print(f"  用户昵称: {nickname}")
    print(f"  语言: {lang}")
    print(f"  国家: {country}")
    
    # Step 4: 获取 bullet_token (对应 s3s.get_bullet())
    print("\n[Step 4] 获取 bullet_token...")
    bullet_token = await auth.get_bullet(g_token)
    
    if not bullet_token:
        raise ValueError("获取 bullet_token 失败")
    
    print(f"✓ bullet_token: {bullet_token[:20]}...")
    
    # 组装结果
    tokens = {
        "session_token": session_token,
        "g_token": g_token,
        "bullet_token": bullet_token,
        "user_lang": lang,
        "user_country": country,
        "user_nickname": nickname,
        "created_at": datetime.now().isoformat(),
    }
    
    await auth.close()
    
    return tokens


# ============================================================
# API 测试（参照 splatoon3-nso/s3s/splatoon.py）
# ============================================================

async def test_all_apis(tokens: dict) -> None:
    """测试所有 SplatNet3 API（带自动刷新）"""
    print("\n" + "=" * 60)
    print("SplatNet3 API 测试（带 Token 自动刷新）")
    print("=" * 60)

    # 使用 TokenStore 管理持久化
    token_store = TokenStore(TOKEN_CACHE_FILE)

    # 创建带自动刷新的 API 实例
    auth = NSOAuth()
    api = SplatNet3API(
        nso_auth=auth,
        session_token=tokens["session_token"],
        g_token=tokens["g_token"],
        bullet_token=tokens["bullet_token"],
        user_lang=tokens.get("user_lang", "zh-CN"),
        user_country=tokens.get("user_country", "JP"),
        on_tokens_updated=lambda t: token_store.save(t)  # 自动保存刷新后的 token
    )

    print(f"\n✓ API 实例已创建（支持 Token 自动刷新）")
    print(f"  - Session Token: {tokens['session_token'][:20]}...")
    print(f"  - 自动刷新: 启用")
    
    # 测试用例列表
    test_cases = [
        # ("get_home", "主页数据"),
        # ("get_history_summary", "历史总览"),
        # ("get_recent_battles", "最近对战"),
        # ("get_regular_battles", "涂地对战"),
        # ("get_bankara_battles", "蛮颓对战"),
        # ("get_x_battles", "X 比赛"),
        # ("get_event_battles", "活动对战"),
        # ("get_private_battles", "私房对战"),
        # ("get_coops", "打工历史"),
        # ("get_friends", "好友列表"),
        # ("get_weapon_records", "武器记录"),
        # ("get_stage_records", "场地记录"),
        # ("get_schedule", "日程安排"),
        # ("get_app_ns_friend_list", "ns好友列表"),
        # ("get_app_ns_myself", "ns我的信息"),
    ]
    
    results = {}
    success_count = 0
    
    for method_name, description in test_cases:
        print(f"\n[测试] {description} ({method_name})...", end=" ")

        try:
            method = getattr(api, method_name)
            result = await method()

            if result:
                results[method_name] = result
                success_count += 1
                print("✓ 成功")
                _print_result_summary(method_name, result)

                # 打印完整的 API 结果
                print(f"\n    【{description} - 完整结果】")
                print("-" * 60)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("-" * 60)
            else:
                print("⚠ 返回空数据")

        except SessionExpiredError:
            print(f"✗ Session Token 已过期，需要重新登录")
            print("   → 请运行测试并选择 'clear' 来清除缓存并重新登录")
            break
        except MembershipRequiredError as e:
            print(f"✗ {e}")
            print("   → 请前往任天堂官网续费 NSO 会员")
            break
        except BulletTokenError as e:
            print(f"✗ Bullet Token 错误: {e}")
            if e.status_code == 403:
                print("   → 应用版本过时，请更新 nso_auth.py 中的版本号")
            elif e.status_code == 499:
                print("   → 账号已被封禁")
            break
        except TokenRefreshError as e:
            print(f"✗ Token 刷新失败: {e}")
            print("   → 请检查网络连接或稍后重试")
            break
        except Exception as e:
            print(f"✗ 失败: {e}")
    
    await api.close()
    
    # 汇总
    print("\n" + "=" * 60)
    print(f"测试完成: {success_count}/{len(test_cases)} 成功")
    print("=" * 60)


def _print_result_summary(method_name: str, result: dict) -> None:
    """打印结果摘要"""
    try:
        if method_name == "get_recent_battles":
            battles = result.get("data", {}).get("latestBattleHistories", {}).get("historyGroups", {}).get("nodes", [])
            total = sum(len(g.get("historyDetails", {}).get("nodes", [])) for g in battles)
            print(f"    → 共 {total} 场对战记录")
            
        elif method_name == "get_coops":
            groups = result.get("data", {}).get("coopResult", {}).get("historyGroups", {}).get("nodes", [])
            total = sum(len(g.get("historyDetails", {}).get("nodes", [])) for g in groups)
            print(f"    → 共 {total} 场打工记录")
            
        elif method_name == "get_friends":
            friends = result.get("data", {}).get("friends", {}).get("nodes", [])
            print(f"    → 共 {len(friends)} 位好友")
            
        elif method_name == "get_history_summary":
            history = result.get("data", {}).get("playHistory", {})
            if history:
                rank = history.get("udemaeMax")
                print(f"    → 最高段位: {rank}")
    except Exception:
        pass


# ============================================================
# 主程序
# ============================================================

async def main():
    """主程序入口"""
    print("=" * 60)
    print("Splatoon3 Assistant - 功能测试")
    print("=" * 60)
    
    # 检查缓存
    tokens = load_cached_tokens()
    
    if tokens:
        print(f"\n已缓存的账号: {tokens.get('user_nickname', 'Unknown')}")
        print(f"创建时间: {tokens.get('created_at', 'Unknown')}")
        
        choice = input("\n使用缓存的 tokens? [Y/n/clear]: ").strip().lower()
        
        if choice == "clear":
            clear_token_cache()
            tokens = None
        elif choice == "n":
            tokens = None
    
    # 登录
    if not tokens:
        tokens = await login_flow()
        save_tokens(tokens)
    
    # 测试 API
    await test_all_apis(tokens)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        raise
