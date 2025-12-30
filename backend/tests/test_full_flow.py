#!/usr/bin/env python3
"""
Splatoon3 Assistant - 功能测试

完整的NSO登录到获取API数据流程（参照 splatoon3-nso/handle/login.py）

使用方法:
    cd splatoon3-assistant
    source .venv/bin/activate
    python backend/tests/test_full_flow.py
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

# 设置代理环境变量（需在导入 src 前设置）
os.environ.setdefault("SPLATOON3_PROXY_ADDRESS", "127.0.0.1:7890")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.src import (
    NSOAuth,
    SplatNet3API,
    TokenStore,
    SessionExpiredError,
    MembershipRequiredError,
    BulletTokenError,
    TokenRefreshError,
)


#============================================================
# Token 缓存管理
# ============================================================

TOKEN_CACHE_FILE = Path(__file__).parent / ".token_cache.json"
TEST_OUTPUT_DIR = Path(__file__).parent / "json"


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


def dataclass_to_dict(obj: Any) -> Any:
    """递归将 dataclass 转换为 dict"""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    return obj


def save_test_result(method_name: str, raw_result: dict, parsed_result: Any = None) -> None:
    """保存测试结果（原始数据 + 解析后数据）"""
    try:
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 保存原始数据
        raw_path = TEST_OUTPUT_DIR / f"{method_name}.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(raw_result, f, indent=2, ensure_ascii=False)
        print(f"    → 原始数据: {raw_path}")

        # 保存解析后数据
        if parsed_result is not None:
            parsed_path = TEST_OUTPUT_DIR / f"{method_name}_parsed.json"
            parsed_dict = dataclass_to_dict(parsed_result)
            with open(parsed_path, "w", encoding="utf-8") as f:
                json.dump(parsed_dict, f, indent=2, ensure_ascii=False)
            print(f"    → 解析数据: {parsed_path}")

    except Exception as e:
        print(f"⚠ 保存结果失败: {e}")


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
    print(f"  用户信息: {user_info}")

    # Step 4: 获取 bullet_token (对应 s3s.get_bullet())
    print("\n[Step 4] 获取 bullet_token...")
    bullet_token = await auth.get_bullet(g_token)

    if not bullet_token:
        raise ValueError("获取 bullet_token 失败")

    print(f"✓ bullet_token: {bullet_token[:20]}...")

    # 组装结果
    tokens = {
        "session_token": session_token,
        "access_token": access_token,
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

async def test_all_apis(tokens: dict) -> dict:
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
        access_token=tokens.get("access_token"),
        g_token=tokens["g_token"],
        bullet_token=tokens["bullet_token"],
        user_lang=tokens.get("user_lang", "zh-CN"),
        user_country=tokens.get("user_country", "JP"),
        on_tokens_updated=lambda t: token_store.save(t)
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
        ("get_schedule", "日程安排"),
        # ("get_last_one_battle", "最新一局对战ID"),
        # ("get_x_ranking", "X排行榜"),
        # ("get_app_ns_friend_list", "NSO好友列表"),
        # ("get_app_ns_myself", "NSO我的信息"),
    ]

    results = {}
    success_count = 0

    for method_name, description in test_cases:
        print(f"\n[测试] {description} ({method_name})...", end=" ")

        try:
            method = getattr(api, method_name)
            result = await method()

            if result is None:
                print("⚠ 返回空数据")
                continue

            results[method_name] = result
            success_count += 1
            print("✓ 成功")

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

    # 测试详情接口
    await test_detail_apis(api, results)

    await api.close()

    # 汇总
    print("\n" + "=" * 60)
    print(f"测试完成: {success_count}/{len(test_cases)} 成功")
    print("=" * 60)

    return results


async def test_detail_apis(api: SplatNet3API, results: dict) -> None:
    """测试详情接口（需要从列表接口获取 ID）- 分别测试各类型对战"""
    print("\n" + "-" * 60)
    print("详情接口测试 - 比较不同类型对战的 Detail 差异")
    print("-" * 60)

    # 定义各类型对战的映射
    battle_types = [
        ("get_recent_battles", "latestBattleHistories", "最近对战"),
        ("get_regular_battles", "regularBattleHistories", "涂地对战"),
        ("get_bankara_battles", "bankaraBattleHistories", "蛮颓对战"),
        ("get_x_battles", "xBattleHistories", "X比赛"),
        ("get_event_battles", "eventBattleHistories", "活动对战"),
        ("get_private_battles", "privateBattleHistories", "私房对战"),
    ]

    detail_results = {}

    for method_key, history_key, type_name in battle_types:
        if method_key not in results:
            print(f"\n[跳过] {type_name} - 无列表数据")
            continue

        battle_id = _extract_battle_id_from_result(results[method_key], history_key)
        if not battle_id:
            print(f"\n[跳过] {type_name} - 无可用对战ID")
            continue

        print(f"\n[测试] {type_name} 详情 (get_battle_detail)...", end=" ")
        try:
            result = await api.get_battle_detail(battle_id)
            if result:
                print("✓ 成功")

                # 保存结果
                filename = f"battle_detail_{method_key.replace('get_', '').replace('_battles', '')}"
                result_with_meta = dict(result) if isinstance(result, dict) else {"data": result}
                save_test_result(filename, result_with_meta)
                detail_results[type_name] = result

                # 打印关键字段
                _print_detail_summary(type_name, result)
            else:
                print("⚠ 返回空数据")
        except Exception as e:
            print(f"✗ 失败: {e}")

    # 比较不同类型的差异
    # if len(detail_results) > 1:
    #     print("\n" + "-" * 60)
    #     print("各类型对战 Detail 字段差异分析")
    #     print("-" * 60)
    #     _compare_battle_details(detail_results)

    # 测试打工详情
    coop_id = extract_coop_id(results)
    if coop_id:
        print(f"\n[测试] 打工详情 (get_coop_detail)...", end=" ")
        try:
            result = await api.get_coop_detail(coop_id)
            if result:
                print("✓ 成功")
                result_with_meta = dict(result) if isinstance(result, dict) else {"data": result}
                save_test_result("get_coop_detail", result_with_meta)
            else:
                print("⚠ 返回空数据")
        except Exception as e:
            print(f"✗ 失败: {e}")
    else:
        print("\n[跳过] 打工详情 - 无可用的打工ID")


def _extract_battle_id_from_result(result: dict, history_key: str) -> Optional[str]:
    """从单个对战结果中提取第一个对战 ID"""
    try:
        groups = result.get("data", {}).get(history_key, {}).get("historyGroups", {}).get("nodes", [])
        for group in groups:
            details = group.get("historyDetails", {}).get("nodes", [])
            if details:
                return details[0].get("id")
    except Exception:
        pass
    return None


def _print_detail_summary(type_name: str, result: dict) -> None:
    """打印对战详情摘要"""
    try:
        detail = result.get("data", {}).get("vsHistoryDetail", {})
        if not detail:
            return

        # 基本信息
        vs_mode = detail.get("vsMode", {}).get("mode", "Unknown")
        vs_rule = detail.get("vsRule", {}).get("name", "Unknown")
        judgement = detail.get("judgement", "Unknown")
        knockout = detail.get("knockout")

        print(f"    → 模式: {vs_mode} | 规则: {vs_rule} | 结果: {judgement}", end="")
        if knockout is not None:
            print(f" | KO: {knockout}")
        else:
            print()

        # 特有字段检测
        special_fields = []
        if detail.get("bankaraMatch"):
            bm = detail["bankaraMatch"]
            special_fields.append(f"bankaraMatch(mode={bm.get('mode')}, earnedUdemaePoint={bm.get('earnedUdemaePoint')})")
        if detail.get("xMatch"):
            xm = detail["xMatch"]
            special_fields.append(f"xMatch(lastXPower={xm.get('lastXPower')})")
        if detail.get("leagueMatch"):
            special_fields.append("leagueMatch(活动)")
        if detail.get("festMatch"):
            fm = detail["festMatch"]
            special_fields.append(f"festMatch(dragonMatchType={fm.get('dragonMatchType')})")

        if special_fields:
            print(f"    → 特有字段: {', '.join(special_fields)}")

    except Exception as e:
        print(f"    → 解析摘要失败: {e}")


def _compare_battle_details(detail_results: dict) -> None:
    """比较不同类型对战的字段差异"""
    all_keys = {}

    # 收集所有类型的顶层字段
    for type_name, result in detail_results.items():
        detail = result.get("data", {}).get("vsHistoryDetail", {})
        if detail:
            keys = set(detail.keys())
            all_keys[type_name] = keys

    if not all_keys:
        print("  无法提取字段进行比较")
        return

    # 找出共同字段和差异字段
    common_keys = set.intersection(*all_keys.values()) if all_keys else set()
    all_unique = set.union(*all_keys.values()) if all_keys else set()

    print(f"\n  共同字段 ({len(common_keys)}个):")
    print(f"    {', '.join(sorted(common_keys)[:15])}...")

    print(f"\n  各类型特有/差异字段:")
    for type_name, keys in all_keys.items():
        unique = keys - common_keys
        if unique:
            print(f"    [{type_name}] 特有: {', '.join(sorted(unique))}")
        else:
            print(f"    [{type_name}] 无特有字段")


def extract_battle_id(results: dict) -> Optional[str]:
    """从对战列表中提取第一个对战 ID"""
    for key in ["get_recent_battles",
                "get_bankara_battles",
                "get_regular_battles",
                "get_event_battles",
                "get_private_battles",
                "get_x_ranking"]:
        if key not in results:
            continue
        try:
            # 根据 key 获取对应的 history key
            history_keys = {
                "get_recent_battles": "latestBattleHistories",
                "get_bankara_battles": "bankaraBattleHistories",
                "get_regular_battles": "regularBattleHistories",
                "get_event_battles": "eventBattleHistories",
                "get_private_battles": "privateBattleHistories",
                "get_x_ranking": "xBattleHistories",
            }
            history_key = history_keys.get(key, "latestBattleHistories")
            groups = results[key].get("data", {}).get(history_key, {}).get("historyGroups", {}).get("nodes", [])
            for group in groups:
                details = group.get("historyDetails", {}).get("nodes", [])
                if details:
                    return details[0].get("id")
        except Exception:
            continue
    return None


def extract_coop_id(results: dict) -> Optional[str]:
    """从打工列表中提取第一个打工 ID"""
    if "get_coops" not in results:
        return None
    try:
        groups = results["get_coops"].get("data", {}).get("coopResult", {}).get("historyGroups", {}).get("nodes", [])
        for group in groups:
            details = group.get("historyDetails", {}).get("nodes", [])
            if details:
                return details[0].get("id")
    except Exception:
        pass
    return None


def _print_result_summary(method_name: str, result: dict, parsed: Any = None) -> None:
    """打印结果摘要"""
    try:
        if parsed:
            # 使用解析后的数据打印摘要
            if hasattr(parsed, 'summary') and parsed.summary:
                s = parsed.summary
                print(f"    → 战绩: {s.win}胜 {s.lose}负 (胜率 {s.win_rate:.1%})")
            if hasattr(parsed, 'battles') and parsed.battles:
                print(f"    → 共 {len(parsed.battles)} 场对战记录")
            if hasattr(parsed, 'details') and parsed.details:
                print(f"    → 共 {len(parsed.details)} 场打工记录")
            if hasattr(parsed, 'friends') and parsed.friends:
                online = len([f for f in parsed.friends if f.is_online])
                print(f"    → 共 {len(parsed.friends)} 位好友 ({online} 在线)")
            if hasattr(parsed, 'current_player') and parsed.current_player:
                p = parsed.current_player
                print(f"    → 玩家: {p.full_name}")
            return

        # 回退到原始数据解析
        if method_name == "get_history_summary":
            history = result.get("data", {}).get("playHistory", {})
            if history:
                rank = history.get("udemaeMax")
                print(f"    → 最高段位: {rank}")
        elif method_name == "get_schedule":
            schedules = result.get("data", {})
            if schedules:
                print(f"    → 包含 {len(schedules)} 种日程类型")

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
    # await test_all_apis(tokens)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        raise
