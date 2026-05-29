"""内置策略库 — 纯规则引擎，无 LLM 依赖

每个策略是一个函数: (df, params) → List[signal]
  signal: {"date": index, "action": "buy"|"sell", "price": float, "reason": str}
"""
from typing import Any

import pandas as pd


def _sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()


def ma_cross(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """均线金叉/死叉策略
    params: {"fast": 5, "slow": 20}
    金叉买入，死叉卖出
    """
    fast = params.get("fast", 5)
    slow = params.get("slow", 20)
    ma_f = _sma(df["close"], fast)
    ma_s = _sma(df["close"], slow)

    signals = []
    position = False
    for i in range(slow, len(df)):
        if not position and ma_f.iloc[i] > ma_s.iloc[i] and ma_f.iloc[i - 1] <= ma_s.iloc[i - 1]:
            signals.append({"date": i, "action": "buy", "price": float(df["close"].iloc[i]),
                            "reason": f"MA{fast}上穿MA{slow} 金叉"})
            position = True
        elif position and ma_f.iloc[i] < ma_s.iloc[i] and ma_f.iloc[i - 1] >= ma_s.iloc[i - 1]:
            signals.append({"date": i, "action": "sell", "price": float(df["close"].iloc[i]),
                            "reason": f"MA{fast}下穿MA{slow} 死叉"})
            position = False
    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


def volume_breakout(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """放量突破策略
    params: {"vol_ratio": 1.5, "price_pct": 0.03, "hold_days": 5}
    成交量>均量*ratio 且当日涨幅>pct 时买入，持有hold_days天后卖出
    """
    vol_ratio = params.get("vol_ratio", 1.5)
    price_pct = params.get("price_pct", 0.03)
    hold_days = params.get("hold_days", 5)
    avg_vol = df["volume"].rolling(20).mean()

    signals = []
    pending_sell = 0
    for i in range(20, len(df)):
        if pending_sell > 0:
            pending_sell -= 1
            if pending_sell == 0:
                signals.append({"date": i, "action": "sell",
                                "price": float(df["close"].iloc[i]), "reason": f"持有{hold_days}天到期"})
            continue
        pct = (df["close"].iloc[i] - df["close"].iloc[i - 1]) / df["close"].iloc[i - 1]
        if (df["volume"].iloc[i] > avg_vol.iloc[i] * vol_ratio and pct > price_pct):
            signals.append({"date": i, "action": "buy", "price": float(df["close"].iloc[i]),
                            "reason": f"放量突破 vol={df['volume'].iloc[i]/avg_vol.iloc[i]:.1f}x pct={pct:.1%}"})
            pending_sell = hold_days
    if pending_sell > 0:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


def dragon_follow(df: pd.DataFrame, params: dict[str, Any]) -> list[dict]:
    """龙头跟随策略
    params: {"trailing_stop": 0.05, "entry_pct": 0.05}
    连续上涨>entry_pct后追入，回撤>trailing_stop止盈
    """
    trailing_stop = params.get("trailing_stop", 0.05)
    entry_pct = params.get("entry_pct", 0.05)

    signals = []
    position = False
    highest = 0.0
    for i in range(5, len(df)):
        if not position:
            gain_3d = (df["close"].iloc[i] - df["close"].iloc[i - 3]) / df["close"].iloc[i - 3]
            if gain_3d > entry_pct:
                signals.append({"date": i, "action": "buy", "price": float(df["close"].iloc[i]),
                                "reason": f"3日涨幅{gain_3d:.1%} 追入"})
                position = True
                highest = float(df["close"].iloc[i])
        else:
            highest = max(highest, float(df["high"].iloc[i]))
            if float(df["close"].iloc[i]) < highest * (1 - trailing_stop):
                signals.append({"date": i, "action": "sell", "price": float(df["close"].iloc[i]),
                                "reason": f"回撤>{trailing_stop:.0%} 止盈"})
                position = False
                highest = 0.0
    if position:
        signals.append({"date": len(df) - 1, "action": "sell",
                        "price": float(df["close"].iloc[-1]), "reason": "回测结束平仓"})
    return signals


# 策略注册表
STRATEGIES: dict[str, dict] = {
    "ma_cross": {
        "name": "均线交叉",
        "fn": ma_cross,
        "params": {"fast": 5, "slow": 20},
        "desc": "短期均线上穿长期均线买入，下穿卖出",
    },
    "volume_breakout": {
        "name": "放量突破",
        "fn": volume_breakout,
        "params": {"vol_ratio": 1.5, "price_pct": 0.03, "hold_days": 5},
        "desc": "成交量放大且股价突破时买入，固定周期持有",
    },
    "dragon_follow": {
        "name": "龙头跟随",
        "fn": dragon_follow,
        "params": {"trailing_stop": 0.05, "entry_pct": 0.05},
        "desc": "追涨强势股，移动止盈",
    },
}


def get_strategy(name: str) -> dict:
    return STRATEGIES.get(name, STRATEGIES["ma_cross"])
