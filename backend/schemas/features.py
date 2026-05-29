"""特征数据 API 契约 — 供前端调试/仪表盘使用"""

from pydantic import BaseModel, Field


class MarketFeaturesResponse(BaseModel):
    """盘面特征快照"""
    limit_up_count: int = Field(0, description="涨停数")
    limit_down_count: int = Field(0, description="跌停数")
    zhaban_rate: float = Field(0, description="炸板率")
    max_board_height: int = Field(0, description="最高连板")
    top_boards: list[dict] = Field(default_factory=list, description="连板排名 Top 10")
    index_name: str = Field("上证指数")
    index_close: float = Field(0, description="指数点位")
    index_pct_change: float = Field(0, description="指数涨跌幅")
    up_down_ratio: float = Field(0, description="涨跌停比")
    board_distribution: dict[str, int] = Field(default_factory=dict, description="行业→涨停数 Top 20")
    computed_at: str = Field("", description="计算时间")


class StockFeaturesResponse(BaseModel):
    """个股特征"""
    symbol: str
    name: str
    close: float = 0
    pct_change: float = 0
    volume: float = 0
    turnover: float = 0
    high: float = 0
    low: float = 0
    amplitude: float = 0
    ma_20: float = 0
    ma_60: float = 0
    avg_vol_20: float = 0
    range_high_60d: float = 0
    price_ratio_vs_ma60: float = 1
    vol_ratio_vs_avg20: float = 1
    cum_gain_20d: float | None = None
    cum_gain_60d: float | None = None
    main_flow: float = 0
    large_order_flow: float = 0
    small_order_flow: float = 0
    has_lower_shadow: bool = False
