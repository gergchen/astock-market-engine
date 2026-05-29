"""盘面评分 — 情绪周期 / 龙头强度 / 风险等级

所有评分规则直接提取自现有 Agent 逻辑，纯数值计算，不调用 LLM。
输入: MarketFeatures
输出: MarketScores (结构化的 0-100 分数)
"""
from dataclasses import dataclass, field
from typing import Any

from backend.feature_engine.market_features import MarketFeatures

from .score_utils import confidence_label, range_score

# ── 情绪周期六阶段定义（与 EmotionCycleAgent 保持一致）──
_EMOTION_STAGES = [
    {"name": "冰点期", "ideal_up": (0, 10), "ideal_zhaban": (0.6, 1.0), "ideal_board": (0, 2), "ideal_ratio": (0, 0.5)},
    {"name": "修复期", "ideal_up": (10, 20), "ideal_zhaban": (0.4, 0.6), "ideal_board": (3, 4), "ideal_ratio": (0.5, 1.5)},
    {"name": "主升期", "ideal_up": (20, 50), "ideal_zhaban": (0.2, 0.35), "ideal_board": (5, 8), "ideal_ratio": (1.5, 5)},
    {"name": "高潮期", "ideal_up": (50, 999), "ideal_zhaban": (0, 0.2), "ideal_board": (8, 99), "ideal_ratio": (5, 999)},
    {"name": "分歧期", "ideal_up": (30, 50), "ideal_zhaban": (0.35, 0.5), "ideal_board": (5, 7), "ideal_ratio": (1, 3)},
    {"name": "退潮期", "ideal_up": (0, 20), "ideal_zhaban": (0.5, 1.0), "ideal_board": (0, 3), "ideal_ratio": (0, 1)},
]

_EMOTION_WEIGHTS = {"up": 0.45, "zhaban": 0.25, "board": 0.2, "ratio": 0.1}

# 六阶段映射到 0-100 分（不是线性，主升期最高，冰点最低）
_STAGE_SCORE_MAP = {"冰点期": 10, "修复期": 40, "主升期": 85, "高潮期": 70, "分歧期": 50, "退潮期": 20}

# 各阶段操作建议
_STAGE_ADVICE = {
    "冰点期": "左侧布局机会，小仓试探，关注率先企稳的个股。",
    "修复期": "逐步加仓，跟随龙头，关注率先走出板块。",
    "主升期": "重仓跟随主线，快进快出，不轻易下车。",
    "高潮期": "减仓警惕，见好就收，不追高。",
    "分歧期": "轻仓观望，不追高，等待分歧转一致。",
    "退潮期": "空仓或做空，等待冰点。现金为王。",
}


@dataclass
class EmotionScores:
    """情绪周期评分"""
    score: int              # 0-100（主升期最高）
    stage: str              # 阶段名
    confidence: str         # 高/中/低
    all_stage_scores: dict[str, float] = field(default_factory=dict)
    signals: list[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class DragonIntensityScores:
    """龙头强度评分"""
    score: int              # 0-100
    top_leader_score: float = 0   # 总龙头得分（满分100）
    high_board_count: int = 0     # 连板 ≥5 的股数
    top_leaders: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RiskScores:
    """风险评分（0-100，越高越危险）"""
    score: int
    level: str             # 低/中/高/极高
    factors: list[str] = field(default_factory=list)


@dataclass
class MarketScores:
    """盘面评分汇总 — 一次计算，所有 Agent 和前端共用"""
    emotion: EmotionScores
    dragon_intensity: DragonIntensityScores
    risk: RiskScores
    computed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "emotion": {
                "score": self.emotion.score,
                "stage": self.emotion.stage,
                "confidence": self.emotion.confidence,
                "all_stage_scores": self.emotion.all_stage_scores,
                "signals": self.emotion.signals,
                "suggestion": self.emotion.suggestion,
            },
            "dragon_intensity": {
                "score": self.dragon_intensity.score,
                "top_leader_score": self.dragon_intensity.top_leader_score,
                "high_board_count": self.dragon_intensity.high_board_count,
                "top_leaders": self.dragon_intensity.top_leaders,
            },
            "risk": {
                "score": self.risk.score,
                "level": self.risk.level,
                "factors": self.risk.factors,
            },
            "computed_at": self.computed_at,
        }


def compute_emotion_scores(mf: MarketFeatures) -> EmotionScores:
    """从 MarketFeatures 计算情绪周期评分（纯规则，不调 LLM）"""
    up = mf.limit_up_count
    zhaban = mf.zhaban_rate
    board = mf.max_board_height
    ratio = mf.up_down_ratio

    zhaban_missing = zhaban <= 0 and mf.limit_up_count == 0
    board_missing = board == 0
    ratio_missing = mf.limit_down_count == 0

    best_stage = _EMOTION_STAGES[0]
    best_score = -1.0
    all_scores: dict[str, float] = {}

    for s in _EMOTION_STAGES:
        score = 0.0
        score += _EMOTION_WEIGHTS["up"] * range_score(up, s["ideal_up"])
        if zhaban_missing:
            score += _EMOTION_WEIGHTS["zhaban"]
        else:
            score += _EMOTION_WEIGHTS["zhaban"] * range_score(zhaban, s["ideal_zhaban"], min_denom=0.01)
        if board_missing:
            score += _EMOTION_WEIGHTS["board"]
        else:
            score += _EMOTION_WEIGHTS["board"] * range_score(board, s["ideal_board"])
        if ratio_missing:
            score += _EMOTION_WEIGHTS["ratio"]
        else:
            score += _EMOTION_WEIGHTS["ratio"] * range_score(ratio, s["ideal_ratio"], min_denom=0.1)

        all_scores[s["name"]] = round(score, 3)
        if score > best_score:
            best_score = score
            best_stage = s

    stage_name = best_stage["name"]
    base = _STAGE_SCORE_MAP.get(stage_name, 30)
    # 在基准分附近 ±10 按匹配度微调
    adjusted = min(100, max(0, base + int((best_score - 0.5) * 20)))

    signals = [f"涨停：{up}只"]
    if mf.limit_down_count > 0:
        signals.append(f"跌停：{mf.limit_down_count}只")
    if not zhaban_missing:
        signals.append(f"炸板率：{zhaban:.1%}")
    if board > 0:
        signals.append(f"最高连板：{board}板")

    return EmotionScores(
        score=adjusted,
        stage=stage_name,
        confidence=confidence_label(best_score),
        all_stage_scores=all_scores,
        signals=signals,
        suggestion=_STAGE_ADVICE.get(stage_name, "观望为主。"),
    )


def compute_dragon_intensity(mf: MarketFeatures) -> DragonIntensityScores:
    """计算龙头强度评分（简化版 DragonLeaderAgent 评分）"""
    pool = mf.limit_up_pool
    if pool is None or pool.empty:
        return DragonIntensityScores(score=0)

    # 统计连板分布
    try:
        boards_series = pool["连板数"].apply(
            lambda x: float(x) if hasattr(x, '__float__') or str(x).replace('.', '').replace('-', '').isdigit() else 0
        )
    except Exception:
        boards_series = pool["连板数"].apply(lambda x: 0)

    high_board_count = int((boards_series >= 5).sum())
    max_board = int(boards_series.max())

    # 行业涨停分布 → 板块集中度评分
    sector_counts: dict[str, int] = {}
    for ind in pool.get("所属行业", []):
        ind_s = str(ind)
        if ind_s and ind_s != "nan":
            sector_counts[ind_s] = sector_counts.get(ind_s, 0) + 1

    # 综合评分: 最高板(40) + 连板股数(30) + 板块集中度(30)
    board_score = min(max_board / 10, 1.0) * 40
    count_score = min(high_board_count / 5, 1.0) * 30
    max_sector_stocks = max(sector_counts.values()) if sector_counts else 0
    sector_score = min(max_sector_stocks / 10, 1.0) * 30

    total = board_score + count_score + sector_score

    # Top 3 龙头
    try:
        top = pool.nlargest(3, "连板数") if "连板数" in pool.columns else pool.head(3)
        top_leaders = [
            {"name": str(row.get("名称", "")), "boards": int(float(row.get("连板数", 0))),
             "industry": str(row.get("所属行业", ""))}
            for _, row in top.iterrows()
        ]
    except Exception:
        top_leaders = []

    return DragonIntensityScores(
        score=min(100, int(total)),
        top_leader_score=round(board_score, 1),
        high_board_count=high_board_count,
        top_leaders=top_leaders,
    )


def compute_risk_scores(mf: MarketFeatures, emotion_stage: str) -> RiskScores:
    """计算市场风险评分"""
    factors: list[str] = []
    risk_base = 30  # 基础风险分

    # 情绪极端 → 风险升高
    if emotion_stage == "高潮期":
        risk_base += 40
        factors.append("情绪极度亢奋，追高风险极大")
    elif emotion_stage == "退潮期":
        risk_base += 30
        factors.append("市场退潮，主线崩塌风险")
    elif emotion_stage == "分歧期":
        risk_base += 20
        factors.append("资金分歧明显，方向不明")
    elif emotion_stage == "冰点期":
        risk_base -= 10
        factors.append("极度低迷，流动性风险但估值安全")

    # 炸板率高 → 风险
    if mf.zhaban_rate > 0.5:
        risk_base += 15
        factors.append(f"炸板率高达{mf.zhaban_rate:.0%}，封板信心不足")
    elif mf.zhaban_rate > 0.35:
        risk_base += 8
        factors.append(f"炸板率偏高{mf.zhaban_rate:.0%}")

    # 涨跌停比极端
    if mf.limit_down_count > mf.limit_up_count:
        risk_base += 20
        factors.append(f"跌停({mf.limit_down_count})多于涨停({mf.limit_up_count})，空头主导")
    elif mf.up_down_ratio > 10 and mf.limit_up_count > 30:
        risk_base += 10
        factors.append("极度普涨，次日分化风险")

    # 大盘下跌
    if mf.index_pct_change < -2:
        risk_base += 15
        factors.append(f"大盘下跌{mf.index_pct_change:.1f}%，系统性风险")
    elif mf.index_pct_change < -1:
        risk_base += 5

    risk_score = max(0, min(100, risk_base))

    if risk_score >= 70:
        level = "极高"
    elif risk_score >= 50:
        level = "高"
    elif risk_score >= 30:
        level = "中"
    else:
        level = "低"

    if not factors:
        factors.append("当前无明显风险信号")

    return RiskScores(score=risk_score, level=level, factors=factors)


def compute_market_scores(mf: MarketFeatures) -> MarketScores:
    """一次计算全部盘面评分"""
    emotion = compute_emotion_scores(mf)
    dragon = compute_dragon_intensity(mf)
    risk = compute_risk_scores(mf, emotion.stage)
    return MarketScores(
        emotion=emotion,
        dragon_intensity=dragon,
        risk=risk,
        computed_at=mf.computed_at,
    )
