"""个股日K 行情数据 + 股票名称查询

数据源优先级: 新浪财经 → 腾讯财经 → curl_cffi(东财) → akshare → 模拟
"""
import json
import logging
import urllib.request
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

from ._helpers import _generate_mock_data, _try_akshare
from .data_quality import DataSource, tag_kline_df

logger = logging.getLogger("market_engine.data")

# ── 新浪财经日K (HTTP, 实测可用) ──────────────────────────────────────────

def _fetch_stock_daily_sina(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """新浪财经日K线 — 返回中文列名 DataFrame, volume 单位=股"""
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        sina_sym = f"{prefix}{symbol}"
        url = (
            "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            f"CN_MarketData.getKLineData?symbol={sina_sym}&scale=240&ma=no&datalen=400"
        )
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode("gbk")
        rows = json.loads(raw)
        if not rows or not isinstance(rows, list):
            return pd.DataFrame()

        prev_close = None
        data = []
        for r in rows:
            close_val = float(r["close"])
            pct = round((close_val / prev_close - 1) * 100, 2) if prev_close and prev_close > 0 else 0.0
            chg = round(close_val - prev_close, 2) if prev_close else 0.0
            prev_close = close_val
            d = {
                "日期": r["day"],
                "开盘": float(r["open"]),
                "收盘": close_val,
                "最高": float(r["high"]),
                "最低": float(r["low"]),
                "成交量": int(float(r["volume"])),  # 股
                "成交额": 0.0,
                "振幅": round((float(r["high"]) - float(r["low"])) / float(r["open"]) * 100, 2),
                "涨跌幅": pct,
                "涨跌额": chg,
                "换手率": 0.0,
                "股票代码": symbol,
            }
            data.append(d)

        df = pd.DataFrame(data)
        if not df.empty and start_date:
            df = df[df["日期"] >= start_date[:4] + "-" + start_date[4:6] + "-" + start_date[6:8]]
        if not df.empty and end_date:
            df = df[df["日期"] <= end_date[:4] + "-" + end_date[4:6] + "-" + end_date[6:8]]
        return df
    except Exception as e:
        logger.warning("新浪财经日K获取失败 (symbol=%s): %s", symbol, e)
        return pd.DataFrame()


# ── 腾讯财经日K (HTTP, 实测可用) ──────────────────────────────────────────

def _fetch_stock_daily_tencent(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """腾讯财经日K线 — 返回中文列名 DataFrame, volume 单位=手"""
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        tencent_sym = f"{prefix}{symbol}"
        url = (
            "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
            f"param={tencent_sym},day,,,400,qfq"
        )
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode("utf-8")
        j = json.loads(raw)

        code_data = j.get("data", {}).get(tencent_sym, {})
        klines = code_data.get("qfqday") or code_data.get("day") or []
        if not klines:
            return pd.DataFrame()

        data = []
        prev_close = None
        for k in klines:
            # 格式: [date, open, close, high, low, volume(手)]
            date_str, o, c, h, l, v = k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
            pct = round((c / prev_close - 1) * 100, 2) if prev_close and prev_close > 0 else 0.0
            chg = round(c - prev_close, 2) if prev_close else 0.0
            amp = round((h - l) / o * 100, 2) if o > 0 else 0.0
            prev_close = c
            data.append({
                "日期": date_str,
                "开盘": o,
                "收盘": c,
                "最高": h,
                "最低": l,
                "成交量": int(v * 100),  # 手 → 股
                "成交额": 0.0,
                "振幅": amp,
                "涨跌幅": pct,
                "涨跌额": chg,
                "换手率": 0.0,
                "股票代码": symbol,
            })

        df = pd.DataFrame(data)
        if not df.empty and start_date:
            sd = start_date[:4] + "-" + start_date[4:6] + "-" + start_date[6:8]
            df = df[df["日期"] >= sd]
        if not df.empty and end_date:
            ed = end_date[:4] + "-" + end_date[4:6] + "-" + end_date[6:8]
            df = df[df["日期"] <= ed]
        return df
    except Exception as e:
        logger.warning("腾讯财经日K获取失败 (symbol=%s): %s", symbol, e)
        return pd.DataFrame()


# ── 腾讯财经实时估值 (换手率补充) ─────────────────────────────────────────

def _fetch_turnover_tencent(symbol: str) -> float:
    """从腾讯财经获取换手率（用于补充新浪/腾讯日K缺失的换手率字段）"""
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        url = f"https://qt.gtimg.cn/q={prefix}{symbol}"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        resp = urllib.request.urlopen(req, timeout=5)
        raw = resp.read().decode("gbk")
        for line in raw.strip().split(";"):
            if "=" in line and '"' in line:
                vals = line.split('"')[1].split("~")
                if len(vals) >= 39:
                    return float(vals[38]) if vals[38] else 0.0
        return 0.0
    except Exception:
        return 0.0


# ── curl_cffi 东财 (备用) ─────────────────────────────────────────────────

def _fetch_stock_daily_curl(
    symbol: str,
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "",
) -> pd.DataFrame:
    """使用 curl_cffi 获取东方财富日K数据（绕过标准 requests 连接问题）"""
    try:
        from curl_cffi import requests as curl_requests

        market_code = 1 if symbol.startswith("6") else 0
        adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": period_dict.get(period, "101"),
            "fqt": adjust_dict.get(adjust, "0"),
            "secid": f"{market_code}.{symbol}",
            "beg": start_date,
            "end": end_date,
        }
        r = curl_requests.get(url, params=params, impersonate="chrome", timeout=15)
        data_json = r.json()
        if not (data_json.get("data") and data_json["data"].get("klines")):
            return pd.DataFrame()

        temp_df = pd.DataFrame(
            [item.split(",") for item in data_json["data"]["klines"]]
        )
        temp_df["股票代码"] = symbol
        temp_df.columns = [
            "日期", "开盘", "收盘", "最高", "最低",
            "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率",
            "股票代码",
        ]
        for col in ["开盘", "收盘", "最高", "最低", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce").astype("int64")
        temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date

        return temp_df[
            ["日期", "股票代码", "开盘", "收盘", "最高", "最低",
             "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]
        ]
    except Exception as e:
        logger.warning("curl_cffi 获取行情失败 (symbol=%s): %s", symbol, e)
        return pd.DataFrame()


# ── 主入口: 多源降级链 ────────────────────────────────────────────────────

def get_stock_daily(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> pd.DataFrame:
    """获取个股日K行情数据

    优先级: 新浪财经 → 腾讯财经 → curl_cffi(东财) → akshare → 模拟
    """
    start = start_date or (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    end = end_date or datetime.now().strftime("%Y%m%d")

    df = pd.DataFrame()

    # 1) 新浪财经 HTTP (实测可用, 无封IP风险)
    df = _fetch_stock_daily_sina(symbol, start_date=start, end_date=end)
    source_tag = (DataSource.SINA, False)

    # 2) 腾讯财经 HTTP
    if df is None or df.empty:
        df = _fetch_stock_daily_tencent(symbol, start_date=start, end_date=end)
        source_tag = (DataSource.TENCENT, True)

    # 3) curl_cffi 东财
    if df is None or df.empty:
        df = _fetch_stock_daily_curl(symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        source_tag = (DataSource.CURL_EASTMONEY, True)

    # 4) akshare
    if df is None or df.empty:
        df = _try_akshare(
            ak.stock_zh_a_hist, None,
            symbol=symbol, period="daily",
            start_date=start, end_date=end, adjust="qfq"
        )
        source_tag = (DataSource.AKSHARE, True)

    # 5) 全部失败，使用模拟数据
    if df is None or df.empty:
        df = _generate_mock_data(symbol, days=120)
        source_tag = (DataSource.MOCK, True)

    # 补充换手率（新浪和腾讯日K不含换手率，从腾讯实时接口获取最新值作为参考）
    if df is not None and not df.empty and "换手率" in df.columns:
        last_turnover = df["换手率"].iloc[-1] if len(df) > 0 else 0.0
        if last_turnover == 0.0 or pd.isna(last_turnover):
            t = _fetch_turnover_tencent(symbol)
            if t > 0:
                df.at[df.index[-1], "换手率"] = t

    # 统一列名为英文
    if df is None or df.empty:
        df = _generate_mock_data(symbol, days=120)
        source_tag = (DataSource.MOCK, True)

    chinese_cols = list(df.columns)
    en_cols = ["date", "open", "close", "high", "low", "volume", "amount",
               "amplitude", "pct_change", "change", "turnover"]
    if len(chinese_cols) != len(en_cols):
        cn_map = {
            "日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
            "最低": "low", "成交量": "volume", "成交额": "amount",
            "振幅": "amplitude", "涨跌幅": "pct_change", "涨跌额": "change",
            "换手率": "turnover",
        }
        mapped = []
        for c in chinese_cols:
            mapped.append(cn_map.get(c, c))
        df.columns = mapped
    else:
        df.columns = en_cols

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # 标记数据质量
    return tag_kline_df(df, source_tag[0], fallback_used=source_tag[1])


_NAME_MAP = {
    "600519": "贵州茅台", "000858": "五粮液", "300750": "宁德时代",
    "002594": "比亚迪", "601012": "隆基绿能", "000333": "美的集团",
    "600036": "招商银行", "601318": "中国平安", "000001": "平安银行",
    "002415": "海康威视", "600276": "恒瑞医药", "300059": "东方财富",
    "002115": "三维通信", "601015": "陕西黑猫",
}


def get_stock_name(symbol: str) -> str:
    """获取股票名称（多数据源轮询）"""
    # 1. 硬编码映射
    if symbol in _NAME_MAP:
        return _NAME_MAP[symbol]
    # 2. 新浪财经实时行情 API（轻量，实测可用）
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        url = f"http://hq.sinajs.cn/list={prefix}{symbol}"
        req = urllib.request.Request(url)
        req.add_header("Referer", "https://finance.sina.com.cn")
        resp = urllib.request.urlopen(req, timeout=5)
        raw = resp.read().decode("gbk")
        # 返回格式: var hq_str_sh601015="陕西黑猫,...
        if '"' in raw:
            quoted = raw.split('"')[1] if raw.count('"') >= 2 else ""
            name = quoted.split(",")[0] if quoted else ""
            if name:
                return name
    except Exception:
        pass
    # 3. akshare 全量查询
    df = _try_akshare(ak.stock_zh_a_spot_em, None)
    if df is not None:
        try:
            match = df[df["代码"] == symbol]
            if not match.empty:
                return str(match.iloc[0]["名称"])
        except Exception:
            pass
    # 4. 返回代码作为兜底
    return symbol
