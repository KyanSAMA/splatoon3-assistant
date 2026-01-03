"""用户数据导出/导入服务"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao.database import get_session
from src.dao.models.user import User, UserStageRecord, UserWeaponRecord
from src.dao.models.battle import BattleDetail, BattleTeam, BattlePlayer, BattleAward
from src.dao.models.coop import CoopDetail, CoopPlayer, CoopWave, CoopEnemy, CoopBoss

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])

EXPORT_VERSION = "1.0"

# 不导出的敏感字段
EXCLUDED_USER_FIELDS = {"session_token", "access_token", "g_token", "bullet_token"}


def model_to_dict(obj, exclude: set = None) -> Dict[str, Any]:
    """将 ORM 模型转换为字典"""
    exclude = exclude or set()
    result = {}
    for c in obj.__table__.columns:
        if c.name in exclude:
            continue
        val = getattr(obj, c.name)
        if isinstance(val, datetime):
            result[c.name] = val.isoformat()
        else:
            result[c.name] = val
    return result


async def export_user_data(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    """导出用户完整数据"""
    # 1. 用户基本信息
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    user_data = model_to_dict(user, exclude=EXCLUDED_USER_FIELDS)

    # 2. 用户统计记录
    stage_records = (await session.execute(
        select(UserStageRecord).where(UserStageRecord.user_id == user_id)
    )).scalars().all()

    weapon_records = (await session.execute(
        select(UserWeaponRecord).where(UserWeaponRecord.user_id == user_id)
    )).scalars().all()

    # 3. 对战数据（含关联）
    battles = (await session.execute(
        select(BattleDetail).where(BattleDetail.user_id == user_id)
    )).scalars().all()

    battle_records = []
    for battle in battles:
        battle_dict = model_to_dict(battle)

        # 队伍和玩家
        teams = (await session.execute(
            select(BattleTeam).where(BattleTeam.battle_id == battle.id)
        )).scalars().all()

        teams_data = []
        for team in teams:
            players = (await session.execute(
                select(BattlePlayer).where(BattlePlayer.team_id == team.id)
            )).scalars().all()
            teams_data.append({
                "team": model_to_dict(team),
                "players": [model_to_dict(p) for p in players]
            })

        # 徽章
        awards = (await session.execute(
            select(BattleAward).where(BattleAward.battle_id == battle.id)
        )).scalars().all()

        battle_records.append({
            "detail": battle_dict,
            "teams": teams_data,
            "awards": [model_to_dict(a) for a in awards]
        })

    # 4. 打工数据（含关联）
    coops = (await session.execute(
        select(CoopDetail).where(CoopDetail.user_id == user_id)
    )).scalars().all()

    coop_records = []
    for coop in coops:
        coop_dict = model_to_dict(coop)

        players = (await session.execute(
            select(CoopPlayer).where(CoopPlayer.coop_id == coop.id)
        )).scalars().all()

        waves = (await session.execute(
            select(CoopWave).where(CoopWave.coop_id == coop.id)
        )).scalars().all()

        enemies = (await session.execute(
            select(CoopEnemy).where(CoopEnemy.coop_id == coop.id)
        )).scalars().all()

        bosses = (await session.execute(
            select(CoopBoss).where(CoopBoss.coop_id == coop.id)
        )).scalars().all()

        coop_records.append({
            "detail": coop_dict,
            "players": [model_to_dict(p) for p in players],
            "waves": [model_to_dict(w) for w in waves],
            "enemies": [model_to_dict(e) for e in enemies],
            "bosses": [model_to_dict(b) for b in bosses]
        })

    return {
        "version": EXPORT_VERSION,
        "export_time": datetime.now().isoformat(),
        "user": user_data,
        "stage_records": [model_to_dict(r) for r in stage_records],
        "weapon_records": [model_to_dict(r) for r in weapon_records],
        "battle_records": battle_records,
        "coop_records": coop_records,
        "stats": {
            "battle_count": len(battle_records),
            "coop_count": len(coop_records),
            "stage_record_count": len(stage_records),
            "weapon_record_count": len(weapon_records)
        }
    }


def parse_datetime(val: Any) -> Optional[datetime]:
    """解析日期时间字符串"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def dict_to_model(model_class, data: Dict[str, Any], exclude_keys: set = None):
    """字典转 ORM 模型（排除指定字段）"""
    exclude_keys = exclude_keys or set()
    filtered = {}
    columns = {c.name for c in model_class.__table__.columns}
    for k, v in data.items():
        if k in exclude_keys or k not in columns:
            continue
        # 处理日期时间字段
        col = model_class.__table__.columns.get(k)
        if col is not None and "DateTime" in str(col.type):
            v = parse_datetime(v)
        filtered[k] = v
    return model_class(**filtered)


class ImportResult(BaseModel):
    """导入结果"""
    success: bool
    user_id: Optional[int] = None
    battles_imported: int = 0
    battles_skipped: int = 0
    coops_imported: int = 0
    coops_skipped: int = 0
    stage_records_imported: int = 0
    stage_records_skipped: int = 0
    weapon_records_imported: int = 0
    weapon_records_skipped: int = 0
    errors: List[str] = []


async def import_user_data(session: AsyncSession, data: Dict[str, Any]) -> ImportResult:
    """导入用户数据"""
    result = ImportResult(success=False)

    try:
        # 验证版本
        version = data.get("version", "")
        if not version.startswith("1."):
            result.errors.append(f"不支持的数据版本: {version}")
            return result

        user_data = data.get("user", {})
        if not user_data:
            result.errors.append("缺少用户数据")
            return result

        # 1. 查找或创建用户（通过 nsa_id 匹配）
        nsa_id = user_data.get("nsa_id")
        if not nsa_id:
            result.errors.append("缺少用户 nsa_id")
            return result

        existing_user = (await session.execute(
            select(User).where(User.nsa_id == nsa_id)
        )).scalar_one_or_none()

        if existing_user:
            user = existing_user
            # 更新非敏感字段
            for field in ["splatoon_id", "user_nickname", "user_lang", "user_country"]:
                if field in user_data:
                    setattr(user, field, user_data[field])
        else:
            # 创建新用户（无 token，需要重新登录）
            user = dict_to_model(User, user_data, exclude_keys={"id"} | EXCLUDED_USER_FIELDS)
            user.session_expired = 1  # 标记需要重新登录
            session.add(user)
            await session.flush()

        result.user_id = user.id

        # 2. 导入地图记录（已存在则跳过）
        for sr_data in data.get("stage_records", []):
            vs_stage_id = sr_data.get("vs_stage_id")
            existing = (await session.execute(
                select(UserStageRecord).where(
                    UserStageRecord.user_id == user.id,
                    UserStageRecord.vs_stage_id == vs_stage_id
                )
            )).scalar_one_or_none()

            if existing:
                result.stage_records_skipped += 1
            else:
                sr = dict_to_model(UserStageRecord, sr_data, exclude_keys={"id", "user_id"})
                sr.user_id = user.id
                session.add(sr)
                result.stage_records_imported += 1

        # 3. 导入武器记录（已存在则跳过）
        for wr_data in data.get("weapon_records", []):
            main_weapon_id = wr_data.get("main_weapon_id")
            existing = (await session.execute(
                select(UserWeaponRecord).where(
                    UserWeaponRecord.user_id == user.id,
                    UserWeaponRecord.main_weapon_id == main_weapon_id
                )
            )).scalar_one_or_none()

            if existing:
                result.weapon_records_skipped += 1
            else:
                wr = dict_to_model(UserWeaponRecord, wr_data, exclude_keys={"id", "user_id"})
                wr.user_id = user.id
                session.add(wr)
                result.weapon_records_imported += 1

        # 4. 导入对战数据
        for battle_data in data.get("battle_records", []):
            detail = battle_data.get("detail", {})
            splatoon_id = detail.get("splatoon_id")
            played_time = detail.get("played_time")  # 字符串比较

            # 检查是否已存在
            existing = (await session.execute(
                select(BattleDetail).where(
                    BattleDetail.user_id == user.id,
                    BattleDetail.splatoon_id == splatoon_id,
                    BattleDetail.played_time == played_time
                )
            )).scalar_one_or_none()

            if existing:
                result.battles_skipped += 1
                continue

            # 创建对战详情
            battle = dict_to_model(BattleDetail, detail, exclude_keys={"id", "user_id"})
            battle.user_id = user.id
            session.add(battle)
            await session.flush()

            # 创建队伍和玩家
            for team_data in battle_data.get("teams", []):
                team = dict_to_model(BattleTeam, team_data.get("team", {}), exclude_keys={"id", "battle_id"})
                team.battle_id = battle.id
                session.add(team)
                await session.flush()

                for player_data in team_data.get("players", []):
                    player = dict_to_model(BattlePlayer, player_data, exclude_keys={"id", "battle_id", "team_id"})
                    player.battle_id = battle.id
                    player.team_id = team.id
                    session.add(player)

            # 创建徽章
            for award_data in battle_data.get("awards", []):
                award = dict_to_model(BattleAward, award_data, exclude_keys={"id", "battle_id", "user_id"})
                award.battle_id = battle.id
                award.user_id = user.id
                session.add(award)

            result.battles_imported += 1

        # 5. 导入打工数据
        for coop_data in data.get("coop_records", []):
            detail = coop_data.get("detail", {})
            splatoon_id = detail.get("splatoon_id")
            played_time = detail.get("played_time")  # 字符串比较

            # 检查是否已存在
            existing = (await session.execute(
                select(CoopDetail).where(
                    CoopDetail.user_id == user.id,
                    CoopDetail.splatoon_id == splatoon_id,
                    CoopDetail.played_time == played_time
                )
            )).scalar_one_or_none()

            if existing:
                result.coops_skipped += 1
                continue

            # 创建打工详情
            coop = dict_to_model(CoopDetail, detail, exclude_keys={"id", "user_id"})
            coop.user_id = user.id
            session.add(coop)
            await session.flush()

            # 创建玩家
            for player_data in coop_data.get("players", []):
                player = dict_to_model(CoopPlayer, player_data, exclude_keys={"id", "coop_id"})
                player.coop_id = coop.id
                session.add(player)

            # 创建波次
            for wave_data in coop_data.get("waves", []):
                wave = dict_to_model(CoopWave, wave_data, exclude_keys={"id", "coop_id"})
                wave.coop_id = coop.id
                session.add(wave)

            # 创建敌人
            for enemy_data in coop_data.get("enemies", []):
                enemy = dict_to_model(CoopEnemy, enemy_data, exclude_keys={"id", "coop_id"})
                enemy.coop_id = coop.id
                session.add(enemy)

            # 创建 Boss
            for boss_data in coop_data.get("bosses", []):
                boss = dict_to_model(CoopBoss, boss_data, exclude_keys={"id", "coop_id"})
                boss.coop_id = coop.id
                session.add(boss)

            result.coops_imported += 1

        result.success = True

    except Exception as e:
        logger.exception("导入数据失败")
        result.errors.append(str(e))

    return result


# API 端点

@router.get("/export")
async def export_data():
    """导出当前用户的所有数据"""
    async with get_session() as session:
        # 获取当前用户
        current_user = (await session.execute(
            select(User).where(User.is_current == 1)
        )).scalar_one_or_none()

        if not current_user:
            raise HTTPException(status_code=400, detail="没有登录用户")

        data = await export_user_data(session, current_user.id)

        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f"attachment; filename=splatoon3_backup_{current_user.user_nickname}_{datetime.now().strftime('%Y%m%d')}.json"
            }
        )


@router.post("/import", response_model=ImportResult)
async def import_data(file: UploadFile):
    """导入用户数据"""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="仅支持 JSON 文件")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}")

    async with get_session() as session:
        result = await import_user_data(session, data)
        return result
