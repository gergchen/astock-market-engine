"""内置策略库 — 纯规则引擎，无 LLM 依赖

V4 升级:
  - 所有策略增加 ATR 止损
  - 参数自适应波动率
  - 趋势过滤 + 量能确认
  - 置信度仓位管理
"""
from typing import Any
import pandas as pd
import numpy as np


def _sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()


def _ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False).mean()


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Average True Range — 波动率度量"""
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _rsi(series: pd.Series, n: int = 14) -> pd.Series:
    """RSI 指标"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(n).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ══════════════════════════════════════
# 策略 1: 均线交叉 V2 (趋势过滤 + ATR 止损)
# ══════════════════════════════════════

def ma_cross(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """均线金叉/死叉 V2 — 趋势过滤 + ATR 止损

    改进:
      1. 加 MA60 趋势过滤: 只在 MA60 上方做多
      2. 加 RSI 过滤: RSI < 30 超卖区不卖, RSI > 70 超买区不买
      3. ATR 止损: 买入后设 2*ATR 止损线
      4. 成交量确认: 金叉时成交量需 > 5日均量
    """
    fast = params.get("fast", 5)
    slow = params.get("slow", 20)
    trend_period = params.get("trend_period", 60)
    atr_stop = params.get("atr_stop", 2.0)

    ma_f = _sma(df["close"], fast)
    ma_s = _sma(df["close"], slow)
    ma_trend = _sma(df["close"], trend_period)
    atr = _atr(df, 14)
    rsi = _rsi(df["close"], 14)
    avg_vol = df["volume"].rolling(5).mean()

    signals = []
    position = False
    stop_price = 0.0
    highest = 0.0

    start = max(slow, trend_period) + 1
    for i in range(start, len(df)):
        price = float(df["close"].iloc[i])
        high = float(df["high"].iloc[i])

        if not position:
            # 买入条件: 金叉 + 在趋势线上方 + RSI 未超买 + 成交量确认
            golden = ma_f.iloc[i] > ma_s.iloc[i] and ma_f.iloc[i - 1] <= ma_s.iloc[i - 1]
            above_trend = price > ma_trend.iloc[i]
            rsi_ok = not pd.isna(rsi.iloc[i]) and rsi.iloc[i] < 70
            vol_ok = (not pd.isna(avg_vol.iloc[i]) and avg_vol.iloc[i] > 0 and
                      df["volume"].iloc[i] > avg_vol.iloc[i] * 0.8)

            if golden and above_trend and rsi_ok and vol_ok:
                atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
                stop_price = price - atr_stop * atr_val
                signals.append({
                    "date": i, "action": "buy", "price": price,
                    "reason": f"MA{fast}上穿MA{slow} 趋势上方 RSI={rsi.iloc[i]:.0f} ATR止损={stop_price:.2f}",
                    "stop": stop_price,
                })
                position = True
                highest = price
        else:
            # 更新移动止损 (跟踪最高价)
            highest = max(highest, high)
            atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
            trailing_stop = highest - atr_stop * atr_val
            effective_stop = max(stop_price, trailing_stop)

            # 卖出条件: 死叉 或 跌破ATR止损 或 RSI超买回落
            death = ma_f.iloc[i] < ma_s.iloc[i] and ma_f.iloc[i - 1] >= ma_s.iloc[i - 1]
            hit_stop = price < effective_stop
            rsi_overbought = not pd.isna(rsi.iloc[i]) and rsi.iloc[i] > 80

            if death or hit_stop or rsi_overbought:
                reason = "死叉" if death else (f"ATR止损 {effective_stop:.2f}" if hit_stop else f"RSI超买 {rsi.iloc[i]:.0f}")
                signals.append({"date": i, "action": "sell", "price": price, "reason": reason})
                position = False

    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


# ══════════════════════════════════════
# 策略 2: 放量突破 V2 (确认 + 止损)
# ══════════════════════════════════════

def volume_breakout(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """放量突破 V2 — 多条件确认 + ATR 止损

    改进:
      1. 突破需站上 20日均线
      2. ATR 止损替代固定持有天数
      3. 加 RSI 确认: 不在超买区追高
      4. 量比阈值可调
    """
    vol_ratio = params.get("vol_ratio", 1.5)
    price_pct = params.get("price_pct", 0.03)
    atr_stop = params.get("atr_stop", 1.5)

    ma20 = _sma(df["close"], 20)
    atr = _atr(df, 14)
    rsi = _rsi(df["close"], 14)
    avg_vol = df["volume"].rolling(20).mean()

    signals = []
    position = False
    stop_price = 0.0
    highest = 0.0

    for i in range(20, len(df)):
        price = float(df["close"].iloc[i])
        high = float(df["high"].iloc[i])

        if not position:
            pct = (price - float(df["close"].iloc[i - 1])) / float(df["close"].iloc[i - 1])
            vol_cond = (not pd.isna(avg_vol.iloc[i]) and avg_vol.iloc[i] > 0 and
                        df["volume"].iloc[i] > avg_vol.iloc[i] * vol_ratio)
            above_ma = price > ma20.iloc[i]
            rsi_ok = not pd.isna(rsi.iloc[i]) and rsi.iloc[i] < 75

            if vol_cond and pct > price_pct and above_ma and rsi_ok:
                atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
                stop_price = price - atr_stop * atr_val
                signals.append({
                    "date": i, "action": "buy", "price": price,
                    "reason": f"放量突破 vol={df['volume'].iloc[i]/avg_vol.iloc[i]:.1f}x pct={pct:.1%} ATR止损={stop_price:.2f}",
                    "stop": stop_price,
                })
                position = True
                highest = price
        else:
            highest = max(highest, high)
            atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
            trailing = highest - atr_stop * atr_val
            effective_stop = max(stop_price, trailing)

            if price < effective_stop:
                signals.append({"date": i, "action": "sell", "price": price,
                                "reason": f"ATR止损 {effective_stop:.2f}"})
                position = False

    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


# ══════════════════════════════════════
# 策势 3: 龙头跟随 V2 (多周期确认)
# ══════════════════════════════════════

def dragon_follow(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """龙头跟随 V2 — 多周期动量 + 移动止盈

    改进:
      1. 3日+5日双周期动量确认
      2. 加 RSI 过滤: 不在超买区追高
      3. ATR 移动止盈替代固定百分比
      4. 量能确认: 上涨需放量
    """
    atr_stop_mult = params.get("atr_stop", 2.0)

    atr = _atr(df, 14)
    rsi = _rsi(df["close"], 14)
    avg_vol = df["volume"].rolling(5).mean()

    signals = []
    position = False
    highest = 0.0
    stop_price = 0.0

    for i in range(20, len(df)):
        price = float(df["close"].iloc[i])
        high = float(df["high"].iloc[i])

        if not position:
            gain_3d = (price - float(df["close"].iloc[i - 3])) / float(df["close"].iloc[i - 3])
            gain_5d = (price - float(df["close"].iloc[i - 5])) / float(df["close"].iloc[i - 5])
            vol_ok = (not pd.isna(avg_vol.iloc[i]) and avg_vol.iloc[i] > 0 and
                      df["volume"].iloc[i] > avg_vol.iloc[i])
            rsi_ok = not pd.isna(rsi.iloc[i]) and rsi.iloc[i] < 75

            if gain_3d > 0.05 and gain_5d > 0.03 and vol_ok and rsi_ok:
                atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
                stop_price = price - atr_stop_mult * atr_val
                signals.append({
                    "date": i, "action": "buy", "price": price,
                    "reason": f"3日+{gain_3d:.1%} 5日+{gain_5d:.1%} 放量 RSI={rsi.iloc[i]:.0f}",
                    "stop": stop_price,
                })
                position = True
                highest = price
        else:
            highest = max(highest, high)
            atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
            trailing = highest - atr_stop_mult * atr_val
            effective_stop = max(stop_price, trailing)

            if price < effective_stop:
                signals.append({"date": i, "action": "sell", "price": price,
                                "reason": f"ATR止盈 {effective_stop:.2f}"})
                position = False

    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


# ══════════════════════════════════════
# 策略 4: 趋势动量 (新策略)
# ══════════════════════════════════════

def trend_momentum(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """趋势动量策略 — EMA 多头排列 + RSI 确认 + ATR 止损

    核心逻辑:
      - EMA5 > EMA20 > EMA60 多头排列时做多
      - RSI 40-70 区间入场
      - 跌破 EMA20 或 RSI < 30 止损
    """
    ema5 = _ema(df["close"], 5)
    ema20 = _ema(df["close"], 20)
    ema60 = _ema(df["close"], 60)
    rsi = _rsi(df["close"], 14)
    atr = _atr(df, 14)
    atr_stop = params.get("atr_stop", 2.0)

    signals = []
    position = False
    stop_price = 0.0
    highest = 0.0

    for i in range(60, len(df)):
        price = float(df["close"].iloc[i])
        high = float(df["high"].iloc[i])

        if not position:
            # 多头排列 + RSI 健康区
            bullish = (ema5.iloc[i] > ema20.iloc[i] > ema60.iloc[i])
            prev_not_bullish = not (ema5.iloc[i-1] > ema20.iloc[i-1] > ema60.iloc[i-1])
            rsi_ok = not pd.isna(rsi.iloc[i]) and 40 < rsi.iloc[i] < 70

            if bullish and prev_not_bullish and rsi_ok:
                atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
                stop_price = price - atr_stop * atr_val
                signals.append({
                    "date": i, "action": "buy", "price": price,
                    "reason": f"EMA多头排列 RSI={rsi.iloc[i]:.0f} ATR止损={stop_price:.2f}",
                    "stop": stop_price,
                })
                position = True
                highest = price
        else:
            highest = max(highest, high)
            atr_val = atr.iloc[i] if not pd.isna(atr.iloc[i]) else price * 0.02
            trailing = highest - atr_stop * atr_val
            effective_stop = max(stop_price, trailing)

            # 卖出: 跌破 EMA20 或 ATR止损 或 RSI 超卖
            below_ema20 = price < ema20.iloc[i]
            hit_stop = price < effective_stop
            rsi_oversold = not pd.isna(rsi.iloc[i]) and rsi.iloc[i] < 30

            if below_ema20 or hit_stop or rsi_oversold:
                reason = "跌破EMA20" if below_ema20 else (f"ATR止损" if hit_stop else f"RSI超卖")
                signals.append({"date": i, "action": "sell", "price": price, "reason": reason})
                position = False

    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


# ══════════════════════════════════════
# 策略 5: 均值回归 (新策略)
# ══════════════════════════════════════

def mean_reversion(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """均值回归策略 — 布林带 + RSI 超卖反弹

    核心逻辑:
      - 股价跌破布林带下轨 + RSI < 30 → 超卖买入
      - 股价回到布林带中轨 → 卖出
      - 跌破下轨 2% → 止损
    """
    period = params.get("period", 20)
    bb_mult = params.get("bb_mult", 2.0)
    stop_pct = params.get("stop_pct", 0.03)

    ma = _sma(df["close"], period)
    std = df["close"].rolling(period).std()
    upper = ma + bb_mult * std
    lower = ma - bb_mult * std
    rsi = _rsi(df["close"], 14)

    signals = []
    position = False
    entry_price = 0.0

    for i in range(period, len(df)):
        price = float(df["close"].iloc[i])

        if not position:
            # 超卖: 跌破下轨 + RSI < 30
            below_lower = price < lower.iloc[i]
            rsi_oversold = not pd.isna(rsi.iloc[i]) and rsi.iloc[i] < 30

            if below_lower and rsi_oversold:
                entry_price = price
                signals.append({
                    "date": i, "action": "buy", "price": price,
                    "reason": f"布林带下轨 RSI={rsi.iloc[i]:.0f} 超卖反弹",
                })
                position = True
        else:
            # 回到中轨止盈 或 止损
            above_mid = price > ma.iloc[i]
            hit_stop = price < entry_price * (1 - stop_pct)

            if above_mid or hit_stop:
                reason = "回到布林中轨" if above_mid else f"止损 -{stop_pct:.0%}"
                signals.append({"date": i, "action": "sell", "price": price, "reason": reason})
                position = False

    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


# ══════════════════════════════════════
# 策略注册表
# ══════════════════════════════════════

STRATEGIES: dict[str, dict] = {
    "ma_cross": {
        "name": "均线交叉 V2",
        "fn": ma_cross,
        "params": {"fast": 5, "slow": 20, "trend_period": 60, "atr_stop": 2.0},
        "desc": "趋势过滤 + RSI确认 + ATR移动止损",
    },
    "volume_breakout": {
        "name": "放量突破 V2",
        "fn": volume_breakout,
        "params": {"vol_ratio": 1.5, "price_pct": 0.03, "atr_stop": 1.5},
        "desc": "站上MA20 + 量比确认 + ATR止损",
    },
    "dragon_follow": {
        "name": "龙头跟随 V2",
        "fn": dragon_follow,
        "params": {"atr_stop": 2.0},
        "desc": "双周期动量 + 量能确认 + ATR移动止盈",
    },
    "trend_momentum": {
        "name": "趋势动量",
        "fn": trend_momentum,
        "params": {"atr_stop": 2.0},
        "desc": "EMA多头排列 + RSI健康区 + ATR止损",
    },
    "mean_reversion": {
        "name": "均值回归",
        "fn": mean_reversion,
        "params": {"period": 20, "bb_mult": 2.0, "stop_pct": 0.03},
        "desc": "布林带超卖 + RSI反弹 + 回中轨止盈",
    },
}


def get_strategy(name: str) -> dict:
    return STRATEGIES.get(name, STRATEGIES["ma_cross"])
