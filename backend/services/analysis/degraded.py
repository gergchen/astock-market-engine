"""降级模板 — 数据不可用时的安全输出"""

DEGRADED_TEMPLATE = """## {stock_name}（{symbol}）— 系统已降级

当前无法获取真实行情，系统已降级到安全模式。

**数据状态**
- 数据源：{source}
- 置信度：{confidence}
- 实时性：{realtime_label}

**本次不进行以下分析：**
- 不进行主力行为分析（无真实资金流向数据）
- 不进行资金行为推断
- 不进行历史K线走势推理

**建议操作**
1. 检查行情数据源是否正常
2. 稍后刷新重试
3. 如持续异常，检查网络连接

---
*系统已自动降级到安全模式，当前展示的并非真实行情分析，不构成任何投资依据。*
"""


def degraded_analysis(stock_name: str, symbol: str, source: str, confidence: float, realtime: bool) -> str:
    """返回标准降级分析文本（替代 LLM / 本地规则分析）"""
    return DEGRADED_TEMPLATE.format(
        stock_name=stock_name,
        symbol=symbol,
        source=source,
        confidence=f'{confidence:.0%}',
        realtime_label='是' if realtime else '否',
    )
