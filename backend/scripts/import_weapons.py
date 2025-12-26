#!/usr/bin/env python3
"""
武器数据导入脚本
从 params.json 读取数据，结合 weapons.json 和 WEAPON_INFO.json 生成 SQL INSERT 语句
"""
import json
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_json(file_path: Path) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"缺少数据文件: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败: {file_path} -> {exc}") from exc


def escape_sql_string(s: str) -> str:
    """转义 SQL 字符串中的单引号"""
    if s is None:
        return "NULL"
    return f"'{s.replace(chr(39), chr(39)+chr(39))}'"


def json_to_sql(obj: dict) -> str:
    """将字典转为 SQL JSON 字符串"""
    if not obj:
        return "NULL"
    return f"'{json.dumps(obj, ensure_ascii=False).replace(chr(39), chr(39)+chr(39))}'"


def ensure_number(value: Any, field: str) -> int | float | None:
    """校验并返回数字，防止类型注入"""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} 不应为布尔类型")
    if isinstance(value, (int, float)):
        return value
    raise ValueError(f"{field} 应为数字，当前为 {value!r}")


def sql_number(value: int | float | None) -> str:
    """将数字转换为可空 SQL 片段"""
    return "NULL" if value is None else str(value)


def generate_main_weapons_sql(params: dict, weapons_lang: dict, weapon_info: list) -> list[str]:
    """生成主武器 INSERT 语句"""
    info_map = {
        item["zh_name"]: item
        for item in weapon_info
        if isinstance(item, dict) and "zh_name" in item
    }

    sqls = []
    for code, data in params.get("mainWeapons", {}).items():
        special_point = ensure_number(data.get("SpecialPoint"), "SpecialPoint")
        sub_weapon_code = data.get("subWeaponId")
        special_weapon_code = data.get("specialWeaponId")

        lang_key = f"MAIN_{code}"
        zh_name = weapons_lang.get(lang_key)

        weapon_class = None
        distance_class = None
        if zh_name and zh_name in info_map:
            weapon_class = info_map[zh_name].get("zh_weapon_class")
            distance_class = info_map[zh_name].get("zh_father_class")

        params_body = {
            k: v for k, v in data.items()
            if k not in {"SpecialPoint", "subWeaponId", "specialWeaponId"}
        }
        params_json = json_to_sql(params_body)

        sql = (
            f"INSERT INTO main_weapon (code, special_point, sub_weapon_code, special_weapon_code, "
            f"zh_name, weapon_class, distance_class, params) VALUES ("
            f"{escape_sql_string(code)}, "
            f"{sql_number(special_point)}, "
            f"{escape_sql_string(str(sub_weapon_code)) if sub_weapon_code is not None else 'NULL'}, "
            f"{escape_sql_string(str(special_weapon_code)) if special_weapon_code is not None else 'NULL'}, "
            f"{escape_sql_string(zh_name)}, "
            f"{escape_sql_string(weapon_class)}, "
            f"{escape_sql_string(distance_class)}, "
            f"{params_json}"
            f");"
        )
        sqls.append(sql)

    return sqls


def generate_sub_weapons_sql(params: dict, weapons_lang: dict) -> list[str]:
    """生成副武器 INSERT 语句"""
    sqls = []
    for code, data in params.get("subWeapons", {}).items():
        ink_consume = ensure_number(data.get("InkConsume"), "InkConsume")

        lang_key = f"SUB_{code}"
        zh_name = weapons_lang.get(lang_key)

        params_body = {k: v for k, v in data.items() if k != "InkConsume"}
        params_json = json_to_sql(params_body)

        sql = (
            f"INSERT INTO sub_weapon (code, ink_consume, zh_name, params) VALUES ("
            f"{escape_sql_string(code)}, "
            f"{sql_number(ink_consume)}, "
            f"{escape_sql_string(zh_name)}, "
            f"{params_json}"
            f");"
        )
        sqls.append(sql)

    return sqls


def generate_special_weapons_sql(params: dict, weapons_lang: dict) -> list[str]:
    """生成特殊武器 INSERT 语句"""
    sqls = []
    for code, data in params.get("specialWeapons", {}).items():
        lang_key = f"SPECIAL_{code}"
        zh_name = weapons_lang.get(lang_key)

        params_json = json_to_sql(data)

        sql = (
            f"INSERT INTO special_weapon (code, zh_name, params) VALUES ("
            f"{escape_sql_string(code)}, "
            f"{escape_sql_string(zh_name)}, "
            f"{params_json}"
            f");"
        )
        sqls.append(sql)

    return sqls


def main() -> int:
    try:
        params = load_json(DATA_DIR / "json" / "params.json")
        weapons_lang = load_json(DATA_DIR / "langs" / "zh-CN" / "weapons.json")
        weapon_info = load_json(DATA_DIR / "json" / "WEAPON_INFO.json")

        all_sqls = [
            "-- 武器数据导入 SQL",
            "-- 自动生成，请勿手动修改\n",
            "BEGIN;",
            "PRAGMA foreign_keys=OFF;",
            "\n-- 清空现有数据",
            "DELETE FROM main_weapon;",
            "DELETE FROM sub_weapon;",
            "DELETE FROM special_weapon;",
            "DELETE FROM sqlite_sequence WHERE name IN ('main_weapon','sub_weapon','special_weapon');",
            "PRAGMA foreign_keys=ON;",
            "\n-- 副武器数据 (先导入，被主武器引用)",
        ]
        all_sqls.extend(generate_sub_weapons_sql(params, weapons_lang))

        all_sqls.append("\n-- 特殊武器数据 (先导入，被主武器引用)")
        all_sqls.extend(generate_special_weapons_sql(params, weapons_lang))

        all_sqls.append("\n-- 主武器数据")
        all_sqls.extend(generate_main_weapons_sql(params, weapons_lang, weapon_info))

        all_sqls.append("\nCOMMIT;")

        output_path = BACKEND_DIR / "database" / "migrations" / "002_import_data.sql"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_sqls))

        print(f"SQL 文件已生成: {output_path}")
        print(f"主武器: {len(params.get('mainWeapons', {}))} 条")
        print(f"副武器: {len(params.get('subWeapons', {}))} 条")
        print(f"特殊武器: {len(params.get('specialWeapons', {}))} 条")
        return 0
    except Exception as exc:
        print(f"生成 SQL 失败: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
