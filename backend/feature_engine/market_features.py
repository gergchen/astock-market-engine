"""盘面特征 — 一次计算，所有 Agent 共享

消除每个 Agent 独立调用 services 层的 N+1 问题，
保证同一请求内所有 Agent 使用的市场数据一致。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from backend.services import (
    get_limit_down_pool,
    get_limit_up_pool,
    get_market_overview,
    get_top_boards,
    get_zhaban_rate,
)


@dataclass
class MarketFeatures:
    """单次请求内所有盘面级特征快照"""

    # 涨停/跌停
    limit_up_count: int = 0
    limit_down_count: int = 0
    zhaban_rate: float = 0.0

    # 连板
    max_board_height: int = 0
    top_boards: list[dict[str, Any]] = field(default_factory=list)

    # 指数
    index_name: str = "上证指数"
    index_close: float = 0.0
    index_pct_change: float = 0.0

    # 涨跌比
    up_down_ratio: float = 0.0

    # 板块分布 (industry -> 涨停数)
    board_distribution: dict[str, int] = field(default_factory=dict)

    # 原始池 (Agent 需要深度分析时使用，避免二次查询)
    limit_up_pool: pd.DataFrame | None = field(default=None, repr=False)
    limit_down_pool: pd.DataFrame | None = field(default=None, repr=False)

    # 时间戳
    computed_at: str = ""

    @classmethod
    def compute(cls) -> "MarketFeatures":
        """从 services 层拉取全部盘面数据，组装为统一特征快照"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 涨停池
        up_pool = get_limit_up_pool()
        up_count = len(up_pool) if not up_pool.empty else 0

        # 跌停池
        down_pool = get_limit_down_pool()
        down_count = len(down_pool) if not down_pool.empty else 0

        # 炸板率
        zhaban = get_zhaban_rate()
        if zhaban < 0:
            zhaban = 0.0

        # 连板高度
        top = get_top_boards(10)
        max_h = top[0]["boards"] if top else 0

        # 大盘
        overview = get_market_overview()

        # 涨跌停比
        ratio = up_count / max(down_count, 1) if down_count > 0 else float(up_count)

        # 涨停分布（行业 → 数量）
        board_dist: dict[str, int] = {}
        if not up_pool.empty and "所属行业" in up_pool.columns:
            for ind in up_pool["所属行业"].dropna().astype(str):
                if ind and ind != "nan":
                    board_dist[ind] = board_dist.get(ind, 0) + 1

        return cls(
            limit_up_count=up_count,
            limit_down_count=down_count,
            zhaban_rate=round(zhaban, 4),
            max_board_height=max_h,
            top_boards=top,
            index_name=overview.get("指数", "上证指数"),
            index_close=overview.get("最新价", 0),
            index_pct_change=overview.get("涨跌幅", 0),
            up_down_ratio=round(ratio, 2),
            board_distribution=board_dist,
            limit_up_pool=up_pool if not up_pool.empty else None,
            limit_down_pool=down_pool if not down_pool.empty else None,
            computed_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        """转为可序列化 dict（不含 DataFrame）"""
        return {
            "limit_up_count": self.limit_up_count,
            "limit_down_count": self.limit_down_count,
            "zhaban_rate": self.zhaban_rate,
            "max_board_height": self.max_board_height,
            "top_boards": self.top_boards,
            "index_name": self.index_name,
            "index_close": self.index_close,
            "index_pct_change": self.index_pct_change,
            "up_down_ratio": self.up_down_ratio,
            "board_distribution": dict(
                sorted(self.board_distribution.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "computed_at": self.computed_at,
        }

    def __repr__(self) -> str:
        return (
            f"MarketFeatures(up={self.limit_up_count}, down={self.limit_down_count}, "
            f"zhaban={self.zhaban_rate:.1%}, board_max={self.max_board_height}, "
            f"index={self.index_pct_change:+.2f}%, at={self.computed_at})"
        )
