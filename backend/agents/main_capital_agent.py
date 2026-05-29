"""主力行为识别 Agent

基于文档第十九章的量化规则，识别主力处于吸筹/洗盘/主升/出货哪个阶段。
"""
from typing import Any


class MainCapitalAgent:
    """主力行为识别分析器"""

    def __init__(self):
        self.stages = ["吸筹", "洗盘", "主升", "出货"]

    def analyze(self, stock_data: dict[str, Any]) -> dict[str, Any]:
        """对股票数据进行主力行为分析"""
        close = stock_data.get("close", 0)
        avg_60 = stock_data.get("ma_60", close)
        volume = stock_data.get("volume", 0)
        avg_vol_20 = stock_data.get("avg_volume_20", volume)
        turnover = stock_data.get("turnover", 0)
        pct = stock_data.get("pct_change", 0)
        high = stock_data.get("high", close)
        low = stock_data.get("low", close)
        range_high = stock_data.get("range_high", 0)

        price_ratio = close / avg_60 if avg_60 > 0 else 1
        vol_ratio = volume / avg_vol_20 if avg_vol_20 > 0 else 1

        scores = self._calc_scores(
            price_ratio, vol_ratio, turnover, pct, high, low, close, range_high
        )

        best_stage = max(scores, key=lambda k: scores[k]["score"])
        result = scores[best_stage]

        return {
            "stage": best_stage,
            "confidence": self._confidence_label(result["score"]),
            "description": self._get_description(best_stage, result["score"]),
            "details": result["reasons"],
            "all_scores": {k: v["score"] for k, v in scores.items()},
        }

    def _calc_scores(self, price_ratio, vol_ratio, turnover, pct, high, low, close, range_high):
        scores = {}
        max_per_stage = {"吸筹": 5, "洗盘": 5, "主升": 5, "出货": 5}

        # 吸筹
        reasons = []
        s = 0
        if price_ratio < 0.9:
            s += 1
            reasons.append("股价低于60日均价90%，处于低位")
        if vol_ratio < 1.2:
            s += 1
            reasons.append("量能温和，未异常放量")
        if 1 <= turnover <= 3:
            s += 1
            reasons.append("换手率1%-3%，温和换手")
        if pct > 0 and (high - close) < (close - low):
            s += 1
            reasons.append("收盘接近最高价，有下影线")
        scores["吸筹"] = {"score": round(s / max_per_stage["吸筹"], 2), "reasons": reasons}

        # 洗盘
        reasons = []
        s = 0
        if 0.8 <= price_ratio <= 0.95:
            s += 1
            reasons.append("股价在近期高点下方10%-20%")
        if vol_ratio < 0.6:
            s += 1
            reasons.append("成交量萎缩至20日均量60%以下")
        if abs(pct) < 2:
            s += 1
            reasons.append("振幅较小，无方向性大阴线")
        if turnover < 1.5:
            s += 1
            reasons.append("换手率低于1.5%")
        scores["洗盘"] = {"score": round(s / max_per_stage["洗盘"], 2), "reasons": reasons}

        # 主升
        reasons = []
        s = 0
        if price_ratio >= 1.05:
            s += 1
            reasons.append("股价站上60日均线，突破前高")
        if vol_ratio >= 1.5:
            s += 1
            reasons.append("成交量高于20日均量150%")
        if pct > 0:
            s += 1
            reasons.append("今日上涨")
        if turnover > 3:
            s += 1
            reasons.append("换手率超过3%，交易活跃")
        if (high - low) / close < 0.06:
            s += 1
            reasons.append("振幅适中，上涨稳健")
        scores["主升"] = {"score": round(s / max_per_stage["主升"], 2), "reasons": reasons}

        # 出货
        reasons = []
        s = 0
        if range_high > 0 and close / range_high > 0.8 and price_ratio >= 1.3:
            s += 1
            reasons.append("累计涨幅较大（>30%）")
        if vol_ratio > 1.5 and pct < 1:
            s += 1
            reasons.append("放量滞涨，量价背离")
        if turnover > 5:
            s += 1
            reasons.append("换手率超过5%，筹码大量交换")
        if pct < -3:
            s += 1
            reasons.append("跌幅较大，有出货迹象")
        scores["出货"] = {"score": round(s / max_per_stage["出货"], 2), "reasons": reasons}

        return scores

    def _confidence_label(self, score: float) -> str:
        if score >= 0.8:
            return "高"
        elif score >= 0.5:
            return "中"
        return "低"

    def _get_description(self, stage: str, score: float) -> str:
        descs = {
            "吸筹": "该股近期大单持续净流入，结合低位缩量特征，疑似主力悄悄建仓，散户恐慌出局反而给了机会。" if score >= 0.6 else "初步呈现吸筹迹象，需进一步观察。",
            "洗盘": "当前更像主力洗盘，而非资金出逃。缩量横盘是洗去浮筹信号，主力并未真正离场。" if score >= 0.6 else "信号不明显，观望为主。",
            "主升": "该股进入主升段，量价配合良好，大单持续净流入。追涨需注意仓位控制，避免高位接盘。" if score >= 0.6 else "有启动迹象，但尚未确认。",
            "出货": "高位放量滞涨，大单净流出明显，出货特征较清晰。持仓者建议设好止损，谨慎追高。" if score >= 0.6 else "出货信号不明显，但需保持警惕。",
        }
        return descs.get(stage, "信号不明朗，建议观望等待确认。")
