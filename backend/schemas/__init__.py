"""API 契约层 — 前后端共享的类型定义

所有 router 响应使用这里的 Pydantic 模型，
前端可以从 OpenAPI /docs 自动生成 TypeScript 类型。
"""
from .features import (
    MarketFeaturesResponse,
    StockFeaturesResponse,
)
from .market import (
    DragonIntensityResponse,
    EmotionScoresResponse,
    MarketScoresResponse,
    RiskScoresResponse,
)
from .stock import (
    MainCapitalScoresResponse,
    StockScoresQuery,
    StockScoresResponse,
    TechnicalScoresResponse,
)

__all__ = [
    "EmotionScoresResponse", "DragonIntensityResponse",
    "RiskScoresResponse", "MarketScoresResponse",
    "MainCapitalScoresResponse", "TechnicalScoresResponse",
    "StockScoresResponse", "StockScoresQuery",
    "MarketFeaturesResponse", "StockFeaturesResponse",
]
