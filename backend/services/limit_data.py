"""涨停池 / 跌停池 / 龙虎榜数据"""
from datetime import datetime

import akshare as ak
import pandas as pd

from ._cache import _cache_get, _cache_set
from ._helpers import _try_akshare
from .data_quality import DataSource, tag_kline_df


def get_limit_up_pool() -> pd.DataFrame:
    """获取今日涨停股池（带 60s TTL 缓存）"""
    cached = _cache_get("limit_up_pool")
    if cached is not None:
        return cached
    df = _try_akshare(ak.stock_zt_pool_em, pd.DataFrame())
    if df is not None and not df.empty:
        df = tag_kline_df(df, DataSource.AKSHARE)
    else:
        df = tag_kline_df(pd.DataFrame(), DataSource.MOCK, fallback_used=True)
    _cache_set("limit_up_pool", df, ttl=60)
    return df


def get_limit_down_pool() -> pd.DataFrame:
    """获取今日跌停股池（带 60s TTL 缓存）"""
    cached = _cache_get("limit_down_pool")
    if cached is not None:
        return cached
    df = _try_akshare(ak.stock_zt_pool_dtgc_em, pd.DataFrame())
    if df is not None and not df.empty:
        df = tag_kline_df(df, DataSource.AKSHARE)
    else:
        df = tag_kline_df(pd.DataFrame(), DataSource.MOCK, fallback_used=True)
    _cache_set("limit_down_pool", df, ttl=60)
    return df


def get_lhb_detail(date: str | None = None) -> pd.DataFrame:
    """获取龙虎榜详情"""
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    df = _try_akshare(ak.stock_lhb_detail_em, pd.DataFrame(), date=date)
    if df is not None and not df.empty:
        return tag_kline_df(df, DataSource.AKSHARE)
    return tag_kline_df(pd.DataFrame(), DataSource.MOCK, fallback_used=True)
