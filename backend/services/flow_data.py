"""个股资金流向 + 板块资金流向"""
from datetime import datetime
from typing import Any

import akshare as ak
import numpy as np
import pandas as pd

from ._cache import _cache_get, _cache_set, mark_mock_used
from ._helpers import _try_akshare
from .data_quality import DataSource, quality_dict


def get_stock_fund_flow(symbol: str) -> dict[str, Any]:
    """获取个股资金流向（大单/小单净流入）"""
    df = _try_akshare(
        ak.stock_individual_fund_flow,
        None,
        stock=symbol,
        market="sh" if symbol.startswith("6") else "sz"
    )
    if df is None:
        mark_mock_used(symbol)
        return quality_dict({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "主力净流入": round(np.random.uniform(-5000, 5000), 2),
            "小单净流入": round(np.random.uniform(-3000, 3000), 2),
            "中单净流入": round(np.random.uniform(-2000, 2000), 2),
            "大单净流入": round(np.random.uniform(-5000, 5000), 2),
            "超大单净流入": round(np.random.uniform(-3000, 3000), 2),
        }, DataSource.MOCK, fallback_used=True)
    try:
        latest = df.iloc[-1]
        return quality_dict({
            "date": str(latest.iloc[0]),
            "主力净流入": float(latest.iloc[1]),
            "小单净流入": float(latest.iloc[2]) if len(latest) > 2 else 0,
            "中单净流入": float(latest.iloc[3]) if len(latest) > 3 else 0,
            "大单净流入": float(latest.iloc[4]) if len(latest) > 4 else 0,
            "超大单净流入": float(latest.iloc[5]) if len(latest) > 5 else 0,
        }, DataSource.AKSHARE)
    except Exception:
        return quality_dict({}, DataSource.DEFAULT, fallback_used=True)


def get_sector_fund_flow_by_type(sector_type: str = "行业资金流向") -> pd.DataFrame:
    """获取板块资金流向（带 60s TTL 缓存）"""
    cache_key = f"sector_flow:{sector_type}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    df = _try_akshare(
        ak.stock_sector_fund_flow_rank,
        pd.DataFrame(),
        indicator="今日",
        sector_type=sector_type,
    )
    _cache_set(cache_key, df, ttl=60)
    return df


def get_sector_fund_flow() -> pd.DataFrame:
    """获取行业板块资金流向（get_sector_fund_flow_by_type 快捷方式）"""
    return get_sector_fund_flow_by_type("行业资金流向")
