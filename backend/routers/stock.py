"""股票数据路由"""
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import (
    classify_system_status,
    get_all_limit_up_today,
    get_lhb_detail,
    get_limit_down_pool,
    get_limit_up_pool,
    get_market_overview,
    get_realtime_quote,
    get_sector_fund_flow,
    get_stock_daily,
    get_stock_fund_flow,
    get_stock_name,
)

router = APIRouter(prefix="/api/stock", tags=["股票数据"])


import re

_STOCK_CODE_RE = re.compile(r"^\d{6}$")

def _validate_symbol(symbol: str) -> str:
    """校验股票代码格式"""
    symbol = symbol.strip()
    if not _STOCK_CODE_RE.match(symbol):
        from fastapi import HTTPException
        raise HTTPException(400, f"股票代码格式错误: {symbol}，应为6位数字")
    return symbol


class StockQuery(BaseModel):
    symbol: str


@router.post("/daily")
def stock_daily(query: StockQuery):
    """获取个股日K数据"""
    symbol = _validate_symbol(query.symbol)
    df = get_stock_daily(symbol)
    if df.empty:
        raise HTTPException(404, f"未找到股票 {query.symbol} 的数据")
    return {
        "symbol": query.symbol,
        "name": get_stock_name(query.symbol),
        "records": df.tail(120).to_dict(orient="records")
    }


@router.post("/realtime")
def stock_realtime(query: StockQuery):
    """获取个股实时行情"""
    symbol = _validate_symbol(query.symbol)
    data = get_realtime_quote(symbol)
    if not data:
        raise HTTPException(404, f"未找到股票 {query.symbol}")
    return {"symbol": query.symbol, **data}


@router.post("/fund-flow")
def stock_fund_flow(query: StockQuery):
    """获取个股资金流向"""
    symbol = _validate_symbol(query.symbol)
    data = get_stock_fund_flow(symbol)
    return {"symbol": query.symbol, "fund_flow": data}


@router.get("/market-overview")
def market_overview():
    """获取大盘概况"""
    return get_market_overview()


@router.get("/limit-up-pool")
def limit_up_pool():
    """获取今日涨停池"""
    df = get_limit_up_pool()
    if df.empty:
        return {"count": 0, "stocks": []}
    return {"count": len(df), "stocks": df.head(50).to_dict(orient="records")}


@router.get("/limit-down-pool")
def limit_down_pool():
    """获取今日跌停池"""
    df = get_limit_down_pool()
    if df.empty:
        return {"count": 0, "stocks": []}
    return {"count": len(df), "stocks": df.head(50).to_dict(orient="records")}


@router.get("/sector-flow")
def sector_fund_flow():
    """获取板块资金流向"""
    df = get_sector_fund_flow()
    if df.empty:
        return {"sectors": []}
    return {"sectors": df.head(20).to_dict(orient="records")}


@router.get("/lhb/{date}")
def lhb_detail(date: str):
    """获取龙虎榜"""
    df = get_lhb_detail(date)
    if df.empty:
        return {"items": []}
    return {"items": df.head(30).to_dict(orient="records")}


@router.get("/limit-up-count")
def limit_up_count():
    """获取今日涨停总数"""
    count = get_all_limit_up_today()
    return {"count": count}


@router.get("/system/status")
def system_status():
    """查询系统整体数据健康状态 (realtime/cache/stale/mock)"""

    daily = get_stock_daily("600519")
    dq = daily.attrs.get("_quality")

    quote = get_realtime_quote("600519")
    qd = quote.get("_quality", {})

    sources = []
    if dq:
        sources.append({"name": "stock_daily", **dq.to_dict()})
    if qd:
        sources.append({"name": "realtime_quote", **qd})

    status = classify_system_status(dq)

    return {
        "status": status,
        "sources": sources,
        "updated_at": datetime.now().isoformat(),
    }


