"""akshare 安全调用封装 + mock 数据生成

上层模块通过 _try_akshare 调用 akshare，自动处理异常。
"""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from ._cache import mark_mock_used
from .data_quality import DataSource, tag_kline_df

logger = logging.getLogger("market_engine.data")


def _try_akshare(func, default_return, *args, **kwargs):
    """安全调用 akshare，失败时返回默认值"""
    try:
        result = func(*args, **kwargs)
        if result is None or (isinstance(result, pd.DataFrame) and result.empty):
            return default_return
        return result
    except Exception as e:
        logger.warning("akshare 调用失败 (func=%s, symbol=%s, args=%s): %s",
                       func.__name__, kwargs.get("symbol", ""), str(args), e)
        return default_return


def _generate_mock_data(symbol: str, days: int = 120) -> pd.DataFrame:
    """生成模拟数据用于演示/开发"""
    mark_mock_used(symbol)
    logger.warning("⚠️ 使用模拟数据（非真实行情），symbol=%s", symbol)
    np.random.seed(hash(symbol) % (2 ** 31))
    end = datetime.now()
    dates = [end - timedelta(days=i) for i in range(days, 0, -1)]

    base_price = 10.0 + (hash(symbol) % 200)
    prices = [base_price]
    for _ in range(days - 1):
        change = np.random.normal(0.001, 0.025)
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, d in enumerate(dates):
        c = prices[i]
        o = c * (1 + np.random.normal(0, 0.01))
        h = max(o, c) * (1 + abs(np.random.normal(0, 0.005)))
        l = min(o, c) * (1 - abs(np.random.normal(0, 0.005)))
        v = np.random.exponential(500000)
        amt = v * c
        amp = (h - l) / o * 100
        pct = (c / prices[i - 1] - 1) * 100 if i > 0 else 0
        chg = c - prices[i - 1] if i > 0 else 0
        turn = np.random.uniform(0.5, 5)

        data.append({
            "date": d, "open": round(o, 2), "close": round(c, 2),
            "high": round(h, 2), "low": round(l, 2),
            "volume": int(v), "amount": round(amt, 2),
            "amplitude": round(amp, 2), "pct_change": round(pct, 2),
            "change": round(chg, 2), "turnover": round(turn, 2),
        })

    df = pd.DataFrame(data)
    return tag_kline_df(df, DataSource.MOCK, fallback_used=True)
