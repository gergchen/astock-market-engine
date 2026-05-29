"""回测引擎核心 — 信号 → 交易 → 绩效评估"""
import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .strategies import get_strategy


@dataclass
class Trade:
    """单笔交易记录"""
    buy_date: str
    sell_date: str
    buy_price: float
    sell_price: float
    pnl_pct: float
    hold_days: int
    reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    total_trades: int
    win_count: int
    lose_count: int
    win_rate: float
    total_return: float           # 累计收益率 (小数)
    annual_return: float          # 年化收益率
    max_drawdown: float           # 最大回撤
    sharpe_ratio: float           # 夏普比率
    avg_pnl: float                # 平均单笔收益
    avg_hold_days: float          # 平均持仓天数
    trades: list[dict] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)  # [{date, value}]


def run_backtest(
    df: pd.DataFrame,
    symbol: str,
    strategy_name: str = "ma_cross",
    strategy_params: dict[str, Any] | None = None,
    initial_capital: float = 100_000,
    commission_rate: float = 0.0003,  # 万三手续费
) -> BacktestResult:
    """执行回测

    Args:
        df: K线数据 (columns: date, open, high, low, close, volume)
        symbol: 股票代码
        strategy_name: 策略名称
        strategy_params: 策略参数覆盖
        initial_capital: 初始资金
        commission_rate: 手续费率

    Returns:
        BacktestResult
    """
    df = df.copy()
    df = df.reset_index(drop=True)

    strat = get_strategy(strategy_name)
    params = {**strat["params"], **(strategy_params or {})}
    signals = strat["fn"](df, params)

    if len(signals) < 2:
        return BacktestResult(
            symbol=symbol, strategy=strategy_name,
            start_date=str(df["date"].iloc[0]) if "date" in df.columns else "",
            end_date=str(df["date"].iloc[-1]) if "date" in df.columns else "",
            total_trades=0, win_count=0, lose_count=0, win_rate=0,
            total_return=0, annual_return=0, max_drawdown=0,
            sharpe_ratio=0, avg_pnl=0, avg_hold_days=0,
        )

    # 模拟交易
    capital = initial_capital
    shares = 0
    trades = []
    equity = []
    peak = initial_capital
    max_dd = 0.0
    daily_values = []

    buy_signal_idx = 0
    for i in range(len(df)):
        # 处理信号
        while buy_signal_idx < len(signals) and signals[buy_signal_idx]["date"] == i:
            sig = signals[buy_signal_idx]
            if sig["action"] == "buy" and shares == 0:
                price = sig["price"]
                cost = price * (1 + commission_rate)
                shares = math.floor(capital / cost / 100) * 100  # A股100股整数倍
                if shares > 0:
                    capital -= shares * cost
                    trades.append({
                        "buy_date": str(df["date"].iloc[i]) if "date" in df.columns else str(i),
                        "buy_price": price,
                        "reason": sig["reason"],
                        "buy_idx": i,
                        "shares": shares,
                    })
            elif sig["action"] == "sell" and shares > 0:
                price = sig["price"]
                buy_cost = trades[-1]["shares"] * trades[-1]["buy_price"]
                if buy_cost <= 0:
                    buy_signal_idx += 1
                    continue
                revenue = shares * price * (1 - commission_rate)
                pnl = (revenue - buy_cost) / buy_cost
                capital += revenue
                trades[-1].update({
                    "sell_date": str(df["date"].iloc[i]) if "date" in df.columns else str(i),
                    "sell_price": price,
                    "pnl_pct": round(pnl, 4),
                    "hold_days": i - trades[-1]["buy_idx"],
                })
                shares = 0
                trades.append({
                    "buy_date": "", "buy_price": 0,
                    "reason": "", "buy_idx": 0, "shares": 0,
                })  # placeholder for next buy
            buy_signal_idx += 1

        # 每日权益
        current_value = capital
        if shares > 0:
            current_value += shares * float(df["close"].iloc[i])
        daily_values.append(current_value)
        peak = max(peak, current_value)
        dd = (peak - current_value) / peak
        max_dd = max(max_dd, dd)
        equity.append({
            "date": str(df["date"].iloc[i]) if "date" in df.columns else str(i),
            "value": round(current_value, 2),
        })

    # 结算
    completed = [t for t in trades if "sell_date" in t]
    wins = [t for t in completed if t.get("pnl_pct", 0) > 0]
    losses = [t for t in completed if t.get("pnl_pct", 0) <= 0]

    total_return = (daily_values[-1] - initial_capital) / initial_capital if daily_values else 0

    # 年化收益率
    trading_days = len(df)
    years = trading_days / 252
    annual_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1 if years > 0 else 0

    # 夏普比率
    if len(daily_values) > 1:
        daily_returns = np.diff(daily_values) / np.array(daily_values[:-1])
        rf_daily = 0.03 / 252  # 无风险利率 3%
        excess = daily_returns - rf_daily
        sharpe = float(np.sqrt(252) * np.mean(excess) / np.std(excess)) if np.std(excess) > 0 else 0
    else:
        sharpe = 0.0

    avg_pnl = float(np.mean([t.get("pnl_pct", 0) for t in completed])) if completed else 0
    avg_hold = float(np.mean([t.get("hold_days", 0) for t in completed])) if completed else 0

    return BacktestResult(
        symbol=symbol,
        strategy=strat["name"],
        start_date=str(df["date"].iloc[0]) if "date" in df.columns else "",
        end_date=str(df["date"].iloc[-1]) if "date" in df.columns else "",
        total_trades=len(completed),
        win_count=len(wins),
        lose_count=len(losses),
        win_rate=round(len(wins) / len(completed), 3) if completed else 0,
        total_return=round(total_return, 4),
        annual_return=round(annual_return, 4),
        max_drawdown=round(max_dd, 4),
        sharpe_ratio=round(sharpe, 3),
        avg_pnl=round(avg_pnl, 4),
        avg_hold_days=round(avg_hold, 1),
        trades=[
            {
                "buy_date": t.get("buy_date", ""),
                "sell_date": t.get("sell_date", ""),
                "buy_price": t.get("buy_price", 0),
                "sell_price": t.get("sell_price", 0),
                "pnl_pct": t.get("pnl_pct", 0),
                "hold_days": t.get("hold_days", 0),
                "reason": t.get("reason", ""),
            }
            for t in completed
        ],
        equity_curve=equity[::max(1, len(equity) // 100)],  # 降采样到100个点
    )
