"""个股评分 API 契约"""

from pydantic import BaseModel, Field


class StockScoresQuery(BaseModel):
    """个股评分请求"""
    symbol: str = Field(..., min_length=6, max_length=6, description="股票代码，如 600519")


class MainCapitalScoresResponse(BaseModel):
    """主力行为评分"""
    score: int = Field(..., description="0-100，主升=90，出货=15")
    stage: str = Field(..., description="阶段：吸筹/洗盘/主升/出货")
    confidence: str = Field(..., description="置信度：高/中/低")
    all_stage_scores: dict[str, float] = Field(default_factory=dict, description="四阶段匹配分")
    factors: list[str] = Field(default_factory=list, description="判断依据")
    advice: str = Field("", description="操作建议")


class TechnicalScoresResponse(BaseModel):
    """技术面评分"""
    score: int = Field(..., description="0-100 技术面综合分")
    trend_score: int = Field(..., description="趋势分 0-40")
    volume_score: int = Field(..., description="量能分 0-30")
    position_score: int = Field(..., description="位置分 0-30")
    factors: list[str] = Field(default_factory=list, description="技术面信号")


class StockScoresResponse(BaseModel):
    """个股评分汇总 — POST /api/analysis/stock-scores 响应"""
    symbol: str
    name: str
    main_capital: MainCapitalScoresResponse
    technical: TechnicalScoresResponse
    composite: int = Field(..., description="综合评分 0-100")
