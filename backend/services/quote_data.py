"""实时行情快照 + 大盘概况

数据源: 腾讯财经 HTTP (qt.gtimg.cn) — 免费、零封IP风险
降级: akshare stock_zh_a_spot_em → 默认值
"""
import json
import logging
import urllib.request
from typing import Any

import akshare as ak
import pandas as pd

from ._cache import _cache_get, _cache_set
from ._helpers import _try_akshare
from .data_quality import DataSource, quality_dict

logger = logging.getLogger("market_engine.quote")

# ── 腾讯财经实时行情 (HTTP, 实测可用) ────────────────────────────────────

def _get_market_prefix(code: str) -> str:
    """6位代码 → 腾讯市场前缀"""
    code = str(code).zfill(6)
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith("8"):
        return "bj"
    return "sz"


def _fetch_tencent_quotes(codes: list[str]) -> dict[str, dict[str, Any]]:
    """批量从腾讯财经获取实时行情 (qt.gtimg.cn)

    返回: {code: {名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额,
                  换手率, 最高, 最低, 今开, 昨收, 总市值, PE}}
    """
    if not codes:
        return {}
    prefixed = [f"{_get_market_prefix(c)}{c}" for c in codes]
    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode("gbk")
    except Exception as e:
        logger.warning("腾讯财经行情请求失败: %s", e)
        return {}

    result = {}
    for line in raw.strip().split(";"):
        if "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        code = key[2:]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        try:
            result[code] = {
                "名称": vals[1],
                "最新价": float(vals[3]) if vals[3] else 0.0,
                "昨收": float(vals[4]) if vals[4] else 0.0,
                "今开": float(vals[5]) if vals[5] else 0.0,
                "涨跌额": float(vals[31]) if vals[31] else 0.0,
                "涨跌幅": float(vals[32]) if vals[32] else 0.0,
                "最高": float(vals[33]) if vals[33] else 0.0,
                "最低": float(vals[34]) if vals[34] else 0.0,
                "成交量": int(float(vals[6]) * 100) if vals[6] else 0,  # 手→股
                "成交额": float(vals[37]) * 10000 if vals[37] else 0.0,  # 万→元
                "换手率": float(vals[38]) if vals[38] else 0.0,
                "总市值": float(vals[44]) * 1e8 if vals[44] else 0.0,  # 亿→元
                "PE": float(vals[39]) if vals[39] else 0.0,  # PE(TTM)
            }
        except (ValueError, IndexError):
            continue
    return result


# ── akshare 全市场快照 (备用) ──────────────────────────────────────────────

def _get_spot_em_df() -> pd.DataFrame | None:
    """获取全市场实时行情快照（带 30s TTL 缓存）"""
    cached = _cache_get("spot_em_df")
    if cached is not None:
        return cached
    df = _try_akshare(ak.stock_zh_a_spot_em, None)
    if df is not None:
        _cache_set("spot_em_df", df, ttl=30)
    return df


def _row_to_quote(row) -> dict[str, Any]:
    """spot DataFrame 单行 → 行情字典（安全转换）"""
    def _f(key, default=0.0):
        try:
            v = row[key]
            return float(v) if pd.notna(v) else default
        except (KeyError, TypeError, ValueError):
            return default

    return {
        "名称": str(row.get("名称", "")) if hasattr(row, "get") else str(row["名称"]),
        "最新价": _f("最新价"),
        "涨跌幅": _f("涨跌幅"),
        "涨跌额": _f("涨跌额"),
        "成交量": _f("成交量"),
        "成交额": _f("成交额"),
        "换手率": _f("换手率"),
        "最高": _f("最高"),
        "最低": _f("最低"),
        "今开": _f("今开"),
        "昨收": _f("昨收"),
        "总市值": _f("总市值"),
        "PE": _f("市盈率-动态"),
    }


# ── 实时行情接口 ──────────────────────────────────────────────────────────

def get_realtime_quote(symbol: str) -> dict[str, Any]:
    """获取单只实时行情 — 优先腾讯财经, 降级 akshare"""
    result = _fetch_tencent_quotes([symbol])
    if result and symbol in result:
        return quality_dict(result[symbol], DataSource.TENCENT)

    df = _get_spot_em_df()
    if df is not None:
        try:
            match = df[df["代码"] == symbol]
            if not match.empty:
                return quality_dict(_row_to_quote(match.iloc[0]), DataSource.AKSHARE, fallback_used=True)
        except Exception:
            pass
    return quality_dict({}, DataSource.DEFAULT, fallback_used=True)


def get_realtime_quote_map(symbols: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """批量获取实时行情 — 优先腾讯财经, 降级 akshare"""
    if symbols and len(symbols) <= 50:
        quotes = _fetch_tencent_quotes(symbols)
        if quotes:
            return {k: quality_dict(v, DataSource.TENCENT) for k, v in quotes.items()}
        return {}

    df = _get_spot_em_df()
    if df is None:
        return {}
    try:
        if symbols:
            df = df[df["代码"].isin(symbols)]
        return {str(row["代码"]): quality_dict(_row_to_quote(row), DataSource.AKSHARE, fallback_used=True)
                for _, row in df.iterrows()}
    except Exception:
        return {}


# ── 大盘概况 ──────────────────────────────────────────────────────────────

def get_market_overview() -> dict[str, Any]:
    """获取大盘概况 — 优先新浪财经指数日K, 降级腾讯, 最后默认值"""
    # 1) 新浪财经指数日K
    try:
        url = (
            "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "CN_MarketData.getKLineData?symbol=sh000001&scale=240&ma=no&datalen=2"
        )
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        resp = urllib.request.urlopen(req, timeout=10)
        rows = json.loads(resp.read().decode("gbk"))
        if rows and len(rows) >= 1:
            latest = rows[-1]
            close = float(latest["close"])
            high = float(latest["high"])
            low = float(latest["low"])
            if len(rows) >= 2:
                prev_close = float(rows[-2]["close"])
                pct = round((close - prev_close) / prev_close * 100, 2)
            else:
                pct = 0.0
            return quality_dict({"指数": "上证指数", "最新价": close, "涨跌幅": pct, "最高": high, "最低": low},
                                DataSource.SINA)
    except Exception as e:
        logger.warning("新浪指数获取失败: %s", e)

    # 2) 腾讯财经指数
    try:
        url = "https://qt.gtimg.cn/q=sh000001"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode("gbk")
        for line in raw.strip().split(";"):
            if "=" in line and '"' in line:
                vals = line.split('"')[1].split("~")
                if len(vals) >= 35:
                    return quality_dict({
                        "指数": vals[1] or "上证指数",
                        "最新价": float(vals[3]) if vals[3] else 3200.0,
                        "涨跌幅": float(vals[32]) if vals[32] else 0.0,
                        "最高": float(vals[33]) if vals[33] else 3200.0,
                        "最低": float(vals[34]) if vals[34] else 3190.0,
                    }, DataSource.TENCENT, fallback_used=True)
    except Exception as e:
        logger.warning("腾讯指数获取失败: %s", e)

    # 3) akshare 降级
    df = _try_akshare(ak.stock_zh_index_daily, None, symbol="sh000001")
    if df is not None and not df.empty:
        try:
            latest = df.iloc[-1]
            close = float(latest["close"])
            prev_close = float(df.iloc[-2]["close"]) if len(df) >= 2 else close
            pct_change = round((close - prev_close) / prev_close * 100, 2)
            return quality_dict({
                "指数": "上证指数", "最新价": close, "涨跌幅": pct_change,
                "最高": float(latest["high"]), "最低": float(latest["low"]),
            }, DataSource.AKSHARE, fallback_used=True)
        except Exception:
            pass

    return quality_dict({"指数": "上证指数", "最新价": 3200.0, "涨跌幅": 0.0, "最高": 3210.0, "最低": 3190.0},
                        DataSource.DEFAULT, fallback_used=True)
