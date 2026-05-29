"""情绪周期判断 Agent

基于文档第二十章的量化标准，使用多维加权评分判断市场情绪阶段。
"""
from typing import Any


class EmotionCycleAgent:
    """A股情绪周期六阶段判断器 — 多维评分版"""

    STAGES = [
        {
            "name": "冰点期",
            "ideal_up": (0, 10),
            "ideal_zhaban": (0.6, 1.0),
            "ideal_board": (0, 2),
            "ideal_ratio": (0, 0.5),
            "desc": "市场极度悲观，成交量极度萎缩，无人参与",
        },
        {
            "name": "修复期",
            "ideal_up": (10, 20),
            "ideal_zhaban": (0.4, 0.6),
            "ideal_board": (3, 4),
            "ideal_ratio": (0.5, 1.5),
            "desc": "情绪开始回暖，龙头股出现，炸板率下降",
        },
        {
            "name": "主升期",
            "ideal_up": (20, 50),
            "ideal_zhaban": (0.2, 0.35),
            "ideal_board": (5, 8),
            "ideal_ratio": (1.5, 5),
            "desc": "主线明确，连板股高度提升，量能持续放大",
        },
        {
            "name": "高潮期",
            "ideal_up": (50, 999),
            "ideal_zhaban": (0, 0.2),
            "ideal_board": (8, 99),
            "ideal_ratio": (5, 999),
            "desc": "情绪极度亢奋，炸板率低，新热点不断涌现",
        },
        {
            "name": "分歧期",
            "ideal_up": (30, 50),
            "ideal_zhaban": (0.35, 0.5),
            "ideal_board": (5, 7),
            "ideal_ratio": (1, 3),
            "desc": "龙头股开始炸板，资金分歧明显，换手加剧",
        },
        {
            "name": "退潮期",
            "ideal_up": (0, 20),
            "ideal_zhaban": (0.5, 1.0),
            "ideal_board": (0, 3),
            "ideal_ratio": (0, 1),
            "desc": "主线崩塌，板块集体走弱，情绪快速降温",
        },
    ]

    def judge(
        self,
        limit_up_count: int,
        limit_down_count: int = 0,
        zhaban_rate: float | None = None,
        high_board_count: int | None = None,
        volume: float | None = None,
    ) -> dict[str, Any]:
        """判断当前情绪周期阶段 — 多维加权评分

        若 zhaban_rate / high_board_count 缺失，对应维度均分处理，
        避免缺失值被默认 0 拉偏到 "冰点期"。
        """
        best_stage, score, debug = self._find_stage(
            up_count=limit_up_count,
            down_count=limit_down_count,
            zhaban_rate=zhaban_rate,
            high_board=high_board_count,
        )
        return {
            "stage": best_stage["name"],
            "description": best_stage["desc"],
            "score": round(score, 3),
            "signals": self._get_signals(best_stage["name"], limit_up_count, zhaban_rate, high_board_count, limit_down_count),
            "suggestion": self._get_suggestion(best_stage["name"]),
            "all_scores": debug,
        }

    def _find_stage(
        self,
        up_count: int,
        down_count: int,
        zhaban_rate: float | None,
        high_board: int | None,
    ) -> tuple:
        """多维加权评分确定阶段

        Returns:
            (best_stage, best_score, {stage_name: score})
        """
        zhaban_missing = zhaban_rate is None
        board_missing = high_board is None
        ratio_missing = down_count <= 0
        ratio = 0.0 if ratio_missing else min(up_count / max(down_count, 1), 15)

        # 权重设计依据文档第二十章：涨停数 / 炸板率 / 连板高度 是判断情绪周期的三大核心维度，
        # 涨跌停比作为辅助验证维度权重最低（涨多跌少在非冰点/退潮期普遍存在，区分度有限）。
        weights = {"up": 0.45, "zhaban": 0.25, "board": 0.2, "ratio": 0.1}

        best_score = -1.0
        best_stage = self.STAGES[0]
        all_scores: dict[str, float] = {}

        for s in self.STAGES:
            score = 0.0
            # 涨停数评分（核心维度，权重最高）
            score += weights["up"] * self._range_score(up_count, s["ideal_up"])
            # 炸板率评分（缺失时均分）
            if zhaban_missing:
                score += weights["zhaban"]
            else:
                score += weights["zhaban"] * self._range_score(zhaban_rate, s["ideal_zhaban"], min_denom=0.01)
            # 连板高度评分（缺失时均分）
            if board_missing:
                score += weights["board"]
            else:
                score += weights["board"] * self._range_score(high_board, s["ideal_board"])
            # 涨跌停比评分（无跌停时均分）
            if ratio_missing:
                score += weights["ratio"]
            else:
                score += weights["ratio"] * self._range_score(ratio, s["ideal_ratio"], min_denom=0.1)

            all_scores[s["name"]] = round(score, 3)
            if score > best_score:
                best_score = score
                best_stage = s

        return best_stage, best_score, all_scores

    @staticmethod
    def _range_score(value: float, ideal_range: tuple, min_denom: float = 1.0) -> float:
        """单个维度的归一化打分：value 落入区间得 1，距离越远分越低（线性衰减）"""
        lo, hi = ideal_range
        if lo <= value <= hi:
            return 1.0
        if value < lo:
            return max(0.0, 1.0 - (lo - value) / max(lo, min_denom))
        return max(0.0, 1.0 - (value - hi) / max(hi, min_denom))

    def _get_signals(self, stage, up_count, zhaban_rate, high_board, down_count):
        signals = [f"涨停：{up_count}只"]
        if down_count > 0:
            signals.append(f"跌停：{down_count}只")
        if zhaban_rate is not None:
            signals.append(f"炸板率：{zhaban_rate:.1%}")
        if high_board:
            signals.append(f"最高连板：{high_board}板")
        return signals

    def _get_suggestion(self, stage: str) -> str:
        suggestions = {
            "冰点期": "左侧布局机会，小仓试探，关注率先企稳的个股。",
            "修复期": "逐步加仓，跟随龙头，关注率先走出板块。",
            "主升期": "重仓跟随主线，快进快出，不轻易下车。",
            "高潮期": "减仓警惕，见好就收，不追高。",
            "分歧期": "轻仓观望，不追高，等待分歧转一致。",
            "退潮期": "空仓或做空，等待冰点。现金为王。",
        }
        return suggestions.get(stage, "观望为主。")
