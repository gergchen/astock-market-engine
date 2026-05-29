"""市场评分 API 契约

前端可直接从 OpenAPI /docs 或 openapi.json 生成 TypeScript 类型。
"""

from pydantic import BaseModel, Field


class EmotionScoresResponse(BaseModel):
    """情绪周期评分"""
    score: int = Field(..., description="0-100 情绪评分，主升期最高")
    stage: str = Field(..., description="阶段名：冰点期/修复期/主升期/高潮期/分歧期/退潮期")
    confidence: str = Field(..., description="置信度：高/中/低")
    all_stage_scores: dict[str, float] = Field(default_factory=dict, description="六个阶段的匹配分")
    signals: list[str] = Field(default_factory=list, description="核心信号")
    suggestion: str = Field("", description="操作建议")


class DragonIntensityResponse(BaseModel):
    """龙头强度评分"""
    score: int = Field(..., description="0-100 龙头强度")
    top_leader_score: float = Field(0, description="总龙头原始得分")
    high_board_count: int = Field(0, description="连板>=5的股数")
    top_leaders: list[dict] = Field(default_factory=list, description="Top 3 龙头")


class RiskScoresResponse(BaseModel):
    """风险评分"""
    score: int = Field(..., description="0-100 风险分，越高越危险")
    level: str = Field(..., description="风险等级：低/中/高/极高")
    factors: list[str] = Field(default_factory=list, description="风险因素")


class MarketScoresResponse(BaseModel):
    """盘面评分汇总 — GET /api/analysis/market-scores 响应"""
    emotion: EmotionScoresResponse
    dragon_intensity: DragonIntensityResponse
    risk: RiskScoresResponse
    computed_at: str = Field("", description="计算时间")
