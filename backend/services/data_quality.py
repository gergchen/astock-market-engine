"""数据可信度追踪层 — 全链路数据质量标记

每个 service 函数返回前调用 tag_* 函数标记 source/confidence/fallback_used，
router 层根据 quality.is_valid() 决定是否允许金融推理。
"""
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd


class DataSource(str, Enum):
    """数据来源枚举，按可信度降序排列"""
    SINA = "sina"                     # 新浪财经 HTTP (实测可用)
    TENCENT = "tencent"               # 腾讯财经 HTTP (实测可用)
    CURL_EASTMONEY = "curl_eastmoney"  # curl_cffi 东财
    AKSHARE = "akshare"               # akshare 库
    CACHE = "cache"                   # TTL 缓存数据
    MOCK = "mock"                     # 模拟数据
    DEFAULT = "default"               # 硬编码默认值


# 各来源基础置信度
SOURCE_CONFIDENCE: dict[DataSource, float] = {
    DataSource.SINA: 0.95,
    DataSource.TENCENT: 0.90,
    DataSource.CURL_EASTMONEY: 0.80,
    DataSource.AKSHARE: 0.70,
    DataSource.CACHE: 0.50,
    DataSource.MOCK: 0.15,
    DataSource.DEFAULT: 0.05,
}


@dataclass
class DataQuality:
    """数据质量描述

    confidence >= 0.6 允许金融推理；
    confidence < 0.6  禁止金融推理，返回降级响应。
    """
    source: DataSource
    confidence: float = 0.0
    realtime: bool = False
    fallback_used: bool = False
    fallback_chain: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.confidence == 0.0:
            self.confidence = SOURCE_CONFIDENCE.get(self.source, 0.1)

    def is_valid(self) -> bool:
        """置信度 >= 0.6 允许金融推理"""
        return self.confidence >= 0.6

    def is_mock(self) -> bool:
        return self.source in (DataSource.MOCK, DataSource.DEFAULT)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.value,
            "confidence": round(self.confidence, 2),
            "realtime": self.realtime,
            "fallback_used": self.fallback_used,
        }


# ── 上下文跟踪器 (thread-local, 每个请求独立) ──
_quality_context: threading.local = threading.local()


def set_system_quality(q: DataQuality):
    """在请求上下文中记录系统整体数据质量"""
    _quality_context.value = q


def get_system_quality() -> DataQuality | None:
    """读取当前请求的数据质量"""
    return getattr(_quality_context, "value", None)


def pop_system_quality() -> DataQuality | None:
    """读取并清除当前请求的数据质量"""
    q = getattr(_quality_context, "value", None)
    if hasattr(_quality_context, "value"):
        del _quality_context.value
    return q


def classify_system_status(quality: DataQuality | None) -> str:
    """将 DataQuality 映射为前端状态: realtime / cache / stale / mock"""
    if quality is None:
        return "unknown"
    if quality.is_mock() or quality.confidence < 0.3:
        return "mock"
    if quality.confidence < 0.6:
        return "stale"
    if not quality.realtime:
        return "cache"
    return "realtime"


# ── 标记函数 ──

def tag_kline_df(
    df: pd.DataFrame,
    source: DataSource,
    fallback_used: bool = False,
) -> pd.DataFrame:
    """向 K-line DataFrame 添加数据质量元数据 (attrs)"""
    if df is None or df.empty:
        return df
    q = DataQuality(
        source=source,
        realtime=True,
        fallback_used=fallback_used,
    )
    df.attrs["_quality"] = q
    df.attrs["_source"] = source.value
    df.attrs["_confidence"] = q.confidence
    df.attrs["_fallback_used"] = fallback_used
    df.attrs["is_mock"] = q.is_mock()  # 兼容旧版
    return df


def quality_dict(
    data: dict,
    source: DataSource,
    fallback_used: bool = False,
) -> dict:
    """向 dict 类型返回值添加 _quality 键"""
    q = DataQuality(
        source=source,
        realtime=True,
        fallback_used=fallback_used,
    )
    data["_quality"] = q.to_dict()
    return data
