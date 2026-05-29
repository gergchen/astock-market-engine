"""回测引擎 — 策略回测 / 绩效评估

策略规则 → 历史K线数据 → 模拟交易 → 收益曲线 + 风险指标。
纯数值计算，不依赖外部 API。
"""
from .engine import BacktestResult, Trade, run_backtest
from .strategies import STRATEGIES, get_strategy

__all__ = ["run_backtest", "BacktestResult", "Trade", "STRATEGIES", "get_strategy"]
