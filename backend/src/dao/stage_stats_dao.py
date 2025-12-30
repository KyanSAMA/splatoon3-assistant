"""地图统计数据访问层 (DAO) - SQLAlchemy 2.0"""

from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, case, and_

from .database import get_session
from .models.stage import Stage
from .models.user import UserStageRecord
from .models.battle import BattleDetail, BattlePlayer


RULE_MAP = {
    "AREA": "win_rate_ar",
    "LOFT": "win_rate_lf",
    "GOAL": "win_rate_gl",
    "CLAM": "win_rate_cl",
    "TURF_WAR": "win_rate_tw",
}


async def get_stages_with_vs_stage_id() -> List[Dict[str, Any]]:
    """获取所有有 vs_stage_id 的地图"""
    async with get_session() as session:
        stmt = select(Stage).where(
            Stage.vs_stage_id.isnot(None)
        ).order_by(Stage.vs_stage_id)
        result = await session.execute(stmt)
        stages = result.scalars().all()
        return [s.to_dict() for s in stages]


async def get_user_stage_stats(user_id: int, vs_stage_id: int) -> Optional[Dict[str, Any]]:
    """获取用户在指定地图的各模式胜率"""
    async with get_session() as session:
        stmt = select(UserStageRecord).where(
            UserStageRecord.user_id == user_id,
            UserStageRecord.vs_stage_id == vs_stage_id,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return {
            "vs_stage_id": vs_stage_id,
            "win_rate": {
                "AREA": record.win_rate_ar,
                "LOFT": record.win_rate_lf,
                "GOAL": record.win_rate_gl,
                "CLAM": record.win_rate_cl,
                "TURF_WAR": record.win_rate_tw,
            }
        }


async def get_user_stage_best_weapon(
    user_id: int,
    vs_stage_id: int,
    vs_rule: Optional[str] = None,
    min_battles: int = 3
) -> Optional[Dict[str, Any]]:
    """
    获取用户在指定地图的最佳武器

    Args:
        user_id: 用户ID
        vs_stage_id: 地图ID
        vs_rule: 规则 (AREA/LOFT/GOAL/CLAM/TURF_WAR)，None 时返回所有规则中最佳
        min_battles: 最少对战场数
    """
    async with get_session() as session:
        conditions = [
            BattleDetail.user_id == user_id,
            BattleDetail.vs_stage_id == vs_stage_id,
            BattlePlayer.is_myself == 1,
        ]
        if vs_rule:
            conditions.append(BattleDetail.vs_rule == vs_rule)

        stmt = (
            select(
                BattlePlayer.weapon_id,
                BattleDetail.vs_rule,
                func.count().label("total"),
                func.sum(
                    case((BattleDetail.judgement == "WIN", 1), else_=0)
                ).label("wins"),
            )
            .select_from(BattleDetail)
            .join(BattlePlayer, BattlePlayer.battle_id == BattleDetail.id)
            .where(and_(*conditions))
            .group_by(BattlePlayer.weapon_id, BattleDetail.vs_rule)
            .having(func.count() >= min_battles)
        )
        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            return None

        best = None
        best_rate = -1.0
        for row in rows:
            weapon_id, rule, total, wins = row
            if total > 0:
                rate = wins / total
                if rate > best_rate or (rate == best_rate and best and total > best["total_battles"]):
                    best_rate = rate
                    best = {
                        "weapon_id": weapon_id,
                        "vs_rule": rule,
                        "win_rate": round(rate, 4),
                        "total_battles": total,
                    }

        return best


async def get_user_all_stage_stats(user_id: int) -> List[Dict[str, Any]]:
    """获取用户所有地图的胜率统计"""
    async with get_session() as session:
        stmt = select(UserStageRecord).where(
            UserStageRecord.user_id == user_id
        ).order_by(UserStageRecord.vs_stage_id)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "vs_stage_id": r.vs_stage_id,
                "stage_code": r.stage_code,
                "name": r.name,
                "win_rate": {
                    "AREA": r.win_rate_ar,
                    "LOFT": r.win_rate_lf,
                    "GOAL": r.win_rate_gl,
                    "CLAM": r.win_rate_cl,
                    "TURF_WAR": r.win_rate_tw,
                }
            }
            for r in records
        ]


async def get_user_all_best_weapons(
    user_id: int,
    min_battles: int = 3,
    top_n: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    批量获取用户所有地图+规则+模式的最佳武器

    返回格式: {
        "1_TURF_WAR_REGULAR": [...],  # vs_stage_id_rule_mode
        "1_AREA_CHALLENGE": [...],
        "1_AREA_OPEN": [...],
    }
    """
    from sqlalchemy import text

    sql = """
    WITH weapon_stats AS (
        SELECT
            bd.vs_stage_id,
            bd.vs_rule,
            bd.vs_mode,
            CASE
                WHEN bd.vs_mode = 'BANKARA' THEN COALESCE(bd.bankara_mode, 'CHALLENGE')
                ELSE bd.vs_mode
            END as sub_mode,
            bp.weapon_id,
            mw.code as weapon_code,
            mw.zh_name as weapon_name,
            COUNT(*) as total,
            SUM(CASE WHEN bd.judgement = 'WIN' THEN 1 ELSE 0 END) as wins
        FROM battle_detail bd
        JOIN battle_player bp ON bp.battle_id = bd.id
        JOIN main_weapon mw ON CAST(mw.code AS INTEGER) = bp.weapon_id
        WHERE bd.user_id = :user_id
          AND bp.is_myself = 1
          AND bd.vs_stage_id IS NOT NULL
          AND bd.vs_mode IN ('REGULAR', 'BANKARA', 'X_MATCH')
          AND bd.judgement != 'DRAW'
        GROUP BY bd.vs_stage_id, bd.vs_rule, bd.vs_mode, sub_mode, bp.weapon_id
        HAVING COUNT(*) >= :min_battles
    ),
    ranked AS (
        SELECT *,
            CAST(wins AS REAL) / total as win_rate,
            ROW_NUMBER() OVER (
                PARTITION BY vs_stage_id, vs_rule, sub_mode
                ORDER BY CAST(wins AS REAL) / total DESC, total DESC
            ) as rn
        FROM weapon_stats
    )
    SELECT vs_stage_id, vs_rule, sub_mode, weapon_id, weapon_code, weapon_name,
           total, wins, win_rate
    FROM ranked
    WHERE rn <= :top_n
    ORDER BY vs_stage_id, vs_rule, sub_mode, rn
    """

    async with get_session() as session:
        result = await session.execute(
            text(sql),
            {"user_id": user_id, "min_battles": min_battles, "top_n": top_n}
        )
        rows = result.mappings().all()

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            key = f"{row['vs_stage_id']}_{row['vs_rule']}_{row['sub_mode']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({
                "weapon_id": row["weapon_id"],
                "weapon_code": row["weapon_code"],
                "weapon_name": row["weapon_name"],
                "win_rate": round(row["win_rate"], 4),
                "total_battles": row["total"],
            })

        return grouped
