"""Base64 ID 解析工具"""

import base64
import re
from typing import Optional, Tuple


def decode_splatnet_id(b64_id: str) -> str:
    """
    解码 SplatNet3 的 Base64 ID

    示例:
        "VnNTdGFnZS0xMQ==" -> "VsStage-11"
    """
    try:
        return base64.b64decode(b64_id).decode("utf-8")
    except Exception:
        return b64_id


def extract_vs_stage_id(b64_id: str) -> Optional[int]:
    """
    从 Base64 编码的 vsStage ID 中提取数字 ID

    示例:
        "VnNTdGFnZS0xMQ==" -> "VsStage-11" -> 11
    """
    decoded = decode_splatnet_id(b64_id)
    match = re.search(r"VsStage-(\d+)", decoded)
    if match:
        return int(match.group(1))
    return None


def extract_weapon_id(b64_id: str) -> Optional[int]:
    """
    从 Base64 编码的 Weapon ID 中提取数字 ID

    示例:
        "V2VhcG9uLTI2MQ==" -> "Weapon-261" -> 261
    """
    decoded = decode_splatnet_id(b64_id)
    match = re.search(r"Weapon-(\d+)", decoded)
    if match:
        return int(match.group(1))
    return None


def extract_vs_rule(b64_id: str) -> Optional[str]:
    """
    从 Base64 编码的 vsRule ID 中提取规则

    VsRule-1 -> AREA, VsRule-2 -> LOFT, VsRule-3 -> GOAL, VsRule-4 -> CLAM
    """
    decoded = decode_splatnet_id(b64_id)
    match = re.search(r"VsRule-(\d+)", decoded)
    if match:
        rule_map = {"1": "AREA", "2": "LOFT", "3": "GOAL", "4": "CLAM", "0": "TURF_WAR"}
        return rule_map.get(match.group(1))
    return None


def extract_splatoon_id_from_battle(b64_id: str) -> Optional[str]:
    """
    从 Base64 编码的对战 ID 中提取 splatoon_id

    解码后格式: VsHistoryDetail-{splatoon_id}:{mode}:{timestamp}_{uuid}
    示例:
        VsHistoryDetail-u-qzg6dio7d5tnffrjanmm:BANKARA:20251224T072314_uuid
        -> u-qzg6dio7d5tnffrjanmm
    """
    decoded = decode_splatnet_id(b64_id)
    if not decoded.startswith("VsHistoryDetail-"):
        return None

    # 去掉前缀 "VsHistoryDetail-"
    rest = decoded[len("VsHistoryDetail-"):]
    # 取第一个 : 之前的部分
    if ":" in rest:
        return rest.split(":")[0]
    return rest


def extract_battle_uid(b64_id: str) -> str:
    """
    从 Base64 编码的对战 ID 中提取唯一标识

    解码后格式: VsHistoryDetail-{user_id}:{mode}:{timestamp}_{uuid}
    返回: {mode}:{timestamp}_{uuid} 部分作为唯一标识
    """
    decoded = decode_splatnet_id(b64_id)
    if decoded.startswith("VsHistoryDetail-"):
        parts = decoded.split(":", 1)
        if len(parts) > 1:
            return parts[1]
    return decoded


def parse_battle_id(b64_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    解析对战 ID，返回 (uid, mode, timestamp)

    示例:
        解码后: VsHistoryDetail-u-xxx:BANKARA:20251224T072314_uuid
        返回: ("BANKARA:20251224T072314_uuid", "BANKARA", "20251224T072314")
    """
    decoded = decode_splatnet_id(b64_id)

    if not decoded.startswith("VsHistoryDetail-"):
        return (decoded, None, None)

    try:
        parts = decoded.split(":")
        if len(parts) >= 3:
            mode = parts[1]
            timestamp_uuid = parts[2]
            timestamp = timestamp_uuid.split("_")[0] if "_" in timestamp_uuid else None
            uid = f"{mode}:{timestamp_uuid}"
            return (uid, mode, timestamp)
    except Exception:
        pass

    return (decoded, None, None)
