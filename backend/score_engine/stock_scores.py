"""个股评分 — 主力行为 / 技术健康度 / 综合评分

规则直接提取自 MainCapitalAgent + StockAnalysisAgent，纯数值计算。
输入: StockFeatures
输出: StockScores (结构化 0-100 分数)
"""
from dataclasses import dataclass, field
from typing import Any

from backend.feature_engine.stock_features import StockFeatures

from .score_utils import confidence_label

# ── 主力四阶段规则（与 MainCapitalAgent 完全一致）──
_CAPITAL_MAX = {"吸筹": 6, "洗盘": 5, "主升": 6, "出货": 6}

# 阶段 → 0-100 映射（主升=100，出货=0，吸筹/洗盘居中偏上）
_CAPITAL_SCORE_MAP = {"主升": 90, "吸筹": 70, "洗盘": 50, "出货": 15}

_CAPITAL_ADVICE = {
    "吸筹": "中线关注，可小仓跟随主力建仓，设好止损。",
    "洗盘": "持股耐心等待，洗盘结束后大概率继续上行。",
    "主升": "趋势良好可持有，但注意不要追高加仓。",
    "出货": "建议减仓或离场，保住利润为主。",
}


@dataclass
class MainCapitalScores:
    """主力行为评分"""
    score: int                      # 0-100（主升=90，出货=15）
    stage: str                      # 吸筹/洗盘/主升/出货
    confidence: str                 # 高/中/低
    all_stage_scores: dict[str, float] = field(default_factory=dict)
    factors: list[str] = field(default_factory=list)
    advice: str = ""


@dataclass
class TechnicalScores:
    """技术面评分"""
    score: int                      # 0-100
    trend_score: int                # 趋势分（均线位置）
    volume_score: int               # 量能分
    position_score: int             # 位置分
    factors: list[str] = field(default_factory=list)


@dataclass
class StockScores:
    """个股评分汇总"""
    symbol: str
    name: str
    main_capital: MainCapitalScores
    technical: TechnicalScores
    composite: int = 0              # 综合评分 0-100

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "main_capital": {
                "score": self.main_capital.score,
                "stage": self.main_capital.stage,
                "confidence": self.main_capital.confidence,
                "all_stage_scores": self.main_capital.all_stage_scores,
                "factors": self.main_capital.factors,
                "advice": self.main_capital.advice,
            },
            "technical": {
                "score": self.technical.score,
                "trend_score": self.technical.trend_score,
                "volume_score": self.technical.volume_score,
                "position_score": self.technical.position_score,
                "factors": self.technical.factors,
            },
            "composite": self.composite,
        }


def compute_capital_scores(sf: StockFeatures) -> MainCapitalScores:
    """主力行为评分 — 规则与 MainCapitalAgent 完全对齐"""
    pr = sf.price_ratio_vs_ma60
    vr = sf.vol_ratio_vs_avg20
    turnover = sf.turnover
    pct = sf.pct_change
    high = sf.high
    close = sf.close
    low = sf.low

    scores: dict[str, float] = {}
    all_factors: dict[str, list[str]] = {}

    # ── 吸筹 (满分6: K线5 + 资金流向1) ──
    s = 0; r = []
    if pr < 0.9: s += 1; r.append("股价低于60日均价90%，处于低位")
    if vr < 1.2: s += 1; r.append("量能温和，未异常放量")
    if 1 <= turnover <= 3: s += 1; r.append(f"换手率{turnover:.1f}%，温和换手")
    if pct > 0 and (high - close) < (close - low): s += 1; r.append("收盘接近最高价，有下影线")
    if sf.main_flow > 0: s += 1; r.append(f"主力净流入{sf.main_flow:.0f}万，资金支持吸筹判断")
    scores["吸筹"] = s / _CAPITAL_MAX["吸筹"]
    all_factors["吸筹"] = r

    # ── 洗盘 (满分5) ──
    s = 0; r = []
    if 0.8 <= pr <= 0.95: s += 1; r.append("股价在近期高点下方10%-20%")
    if vr < 0.6: s += 1; r.append("成交量萎缩至20日均量60%以下")
    if abs(pct) < 2: s += 1; r.append("振幅较小，无方向性大阴线")
    if turnover < 1.5: s += 1; r.append("换手率低于1.5%")
    scores["洗盘"] = s / _CAPITAL_MAX["洗盘"]
    all_factors["洗盘"] = r

    # ── 主升 (满分6: K线5 + 资金流向1) ──
    s = 0; r = []
    if pr >= 1.05: s += 1; r.append("股价站上60日均线，突破前高")
    if vr >= 1.5: s += 1; r.append("成交量高于20日均量150%")
    if pct > 0: s += 1; r.append("今日上涨")
    if turnover > 3: s += 1; r.append(f"换手率{turnover:.1f}%，交易活跃")
    if close > 0 and (high - low) / close < 0.06: s += 1; r.append("振幅适中，上涨稳健")
    if sf.main_flow > 0: s += 1; r.append(f"主力净流入{sf.main_flow:.0f}万")
    scores["主升"] = s / _CAPITAL_MAX["主升"]
    all_factors["主升"] = r

    # ── 出货 (满分6: K线4 + 资金流向1 + 趋势跌幅1) ──
    s = 0; r = []
    if pr >= 1.3: s += 1; r.append(f"累计涨幅{sf.cum_gain_60d or 0:.1f}%，处于高位")
    if vr > 1.5 and pct < 1: s += 1; r.append("放量滞涨，量价背离")
    if turnover > 5: s += 1; r.append(f"换手率{turnover:.1f}%>5%，筹码大量交换")
    if pct < -3: s += 1; r.append(f"跌幅{pct:.1f}%，有出货迹象")
    if sf.main_flow < 0: s += 1; r.append(f"主力净流出{abs(sf.main_flow):.0f}万")
    if pct < 0 and sf.main_flow < -500: s += 1; r.append("下跌+主力大幅流出，出货特征明显")
    scores["出货"] = s / _CAPITAL_MAX["出货"]
    all_factors["出货"] = r

    # 取最高分阶段
    best_stage = max(scores, key=scores.get)
    best_score = scores[best_stage]
    base = _CAPITAL_SCORE_MAP.get(best_stage, 30)
    # 按匹配度微调
    adjusted = min(100, max(0, base + int((best_score - 0.4) * 25)))

    return MainCapitalScores(
        score=adjusted,
        stage=best_stage,
        confidence=confidence_label(best_score),
        all_stage_scores={k: round(v, 2) for k, v in scores.items()},
        factors=all_factors[best_stage] if all_factors[best_stage] else ["信号不明确"],
        advice=_CAPITAL_ADVICE.get(best_stage, "观望为主，等待明确信号。"),
    )


def compute_technical_scores(sf: StockFeatures) -> TechnicalScores:
    """技术面评分"""
    factors: list[str] = []

    # ── 趋势分 (0-40) — 基于均线位置 ──
    trend = 20
    above_ma20 = sf.close > sf.ma_20
    above_ma60 = sf.close > sf.ma_60
    if above_ma20 and above_ma60:
        trend = 35
        factors.append("股价站上全部均线，趋势偏强")
    elif not above_ma20 and not above_ma60:
        trend = 10
        factors.append("股价跌破所有均线，趋势偏弱")
    else:
        trend = 22
        factors.append("股价在均线之间，方向不明")

    # ── 量能分 (0-30) ──
    vr = sf.vol_ratio_vs_avg20
    if 0.8 <= vr <= 1.5:
        volume = 25
        factors.append("成交量正常，未异常缩/放量")
    elif vr > 1.5:
        volume = 20
        factors.append(f"放量{vr:.1f}倍，关注放量方向")
    else:
        volume = 15
        factors.append(f"缩量至{vr:.1f}倍，交投清淡")

    # ── 位置分 (0-30) — 基于近期累计涨幅 ──
    cg = sf.cum_gain_60d
    if cg is None:
        position = 15
    elif cg > 50:
        position = 5
        factors.append(f"近60日涨幅{cg:.1f}%，处于高位区间，追高风险大")
    elif cg > 20:
        position = 15
        factors.append(f"近60日涨幅{cg:.1f}%，已有一定盈利盘")
    elif cg > 0:
        position = 25
        factors.append(f"近60日涨幅{cg:.1f}%，位置适中偏强")
    elif cg > -20:
        position = 20
        factors.append(f"近60日跌幅{cg:.1f}%，处于回调位")
    else:
        position = 10
        factors.append(f"近60日跌幅{cg:.1f}%，处于低位")

    # 资金流向修正
    flow_bonus = 0
    if sf.main_flow > 5000:
        flow_bonus = 8
        factors.append(f"主力净流入{sf.main_flow:.0f}万元，资金看好")
    elif sf.main_flow > 1000:
        flow_bonus = 4
    elif sf.main_flow < -5000:
        flow_bonus = -8
        factors.append(f"主力净流出{abs(sf.main_flow):.0f}万元，资金离场")
    elif sf.main_flow < -1000:
        flow_bonus = -4

    total = max(0, min(100, trend + volume + position + flow_bonus))

    return TechnicalScores(
        score=total,
        trend_score=trend,
        volume_score=volume,
        position_score=position,
        factors=factors,
    )


def compute_stock_scores(sf: StockFeatures) -> StockScores:
    """一次计算全部个股评分"""
    capital = compute_capital_scores(sf)
    technical = compute_technical_scores(sf)
    # 综合分: 主力行为 60% + 技术面 40%
    composite = min(100, max(0, round(capital.score * 0.6 + technical.score * 0.4)))
    return StockScores(
        symbol=sf.symbol,
        name=sf.name,
        main_capital=capital,
        technical=technical,
        composite=composite,
    )
