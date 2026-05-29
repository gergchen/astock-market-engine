"""财报数据"""
from typing import Any

import akshare as ak
import pandas as pd

from ._helpers import _try_akshare
from .data_quality import DataSource, quality_dict


def get_stock_financial(symbol: str) -> dict[str, Any]:
    """获取财报数据摘要"""
    df = _try_akshare(ak.stock_financial_abstract, None, symbol=symbol)
    if df is not None and not df.empty:
        try:
            latest = df.iloc[-1]
            return quality_dict({
                "报告期": str(latest.iloc[0]),
                "营业收入": float(latest.iloc[1]) if pd.notna(latest.iloc[1]) else 0,
                "净利润": float(latest.iloc[2]) if pd.notna(latest.iloc[2]) else 0,
            }, DataSource.AKSHARE)
        except Exception:
            pass
    return quality_dict({}, DataSource.DEFAULT, fallback_used=True)
