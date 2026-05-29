"""个股综合分析 Agent

整合行情数据、资金流向、主力行为识别、情绪判断，
生成完整的大白话个股分析报告。
"""
from typing import Any

from backend.agents.emotion_cycle_agent import EmotionCycleAgent
from backend.agents.main_capital_agent import MainCapitalAgent


class StockAnalysisAgent:
    """个股综合分析器"""

    def __init__(self):
        self.capital_agent = MainCapitalAgent()
        self.emotion_agent = EmotionCycleAgent()

    def analyze(self, df, fund_flow: dict[str, Any]) -> dict[str, Any]:
        """综合分析一只股票"""
        if df.empty:
            return {"error": "无数据"}

        latest = df.iloc[-1]
        recent = df.tail(60)

        # 计算均线
        ma_20 = recent["close"].rolling(20).mean().iloc[-1] if len(recent) >= 20 else recent["close"].mean()
        ma_60 = recent["close"].mean() if len(recent) >= 60 else recent["close"].mean()
        avg_vol_20 = recent["volume"].tail(20).mean() if len(recent) >= 20 else recent["volume"].mean()

        # 计算阶段最高价
        range_high = recent["high"].max()

        stock_data = {
            "close": float(latest["close"]),
            "ma_20": float(ma_20),
            "ma_60": float(ma_60),
            "volume": float(latest["volume"]),
            "avg_volume_20": float(avg_vol_20),
            "turnover": float(latest["turnover"]),
            "pct_change": float(latest["pct_change"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "range_high": float(range_high),
        }

        # 主力行为分析
        capital_result = self.capital_agent.analyze(stock_data)

        # 构建结果
        return {
            "latest_price": float(latest["close"]),
            "pct_change": float(latest["pct_change"]),
            "volume": float(latest["volume"]),
            "turnover": float(latest["turnover"]),
            "ma_20": float(ma_20),
            "ma_60": float(ma_60),
            "capital_analysis": capital_result,
            "fund_flow": fund_flow,
        }

    def generate_report(self, stock_name: str, symbol: str, analysis: dict[str, Any]) -> str:
        """生成大白话报告"""
        if "error" in analysis:
            return f"## {stock_name} 分析\n\n数据不足，无法分析。"

        p = analysis["latest_price"]
        change = analysis["pct_change"]
        cap = analysis["capital_analysis"]

        # 涨跌图标
        icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"

        report = f"""## {icon} {stock_name}（{symbol}）综合分析

### 一、当前状态
收盘 **{p:.2f}** 元，今日 **{change:+.2f}%**。
"""

        # 二、主力行为
        report += f"""
### 二、主力行为分析

**判断结果**：{cap['stage']}（置信度：{cap['confidence']}）

{cap['description']}

**关键信号**：
"""
        for reason in cap.get("details", []):
            report += f"- {reason}\n"

        # 三、均线位置
        report += f"""
### 三、技术位置
- MA20 均线：{analysis['ma_20']:.2f}
- MA60 均线：{analysis['ma_60']:.2f}
"""
        if p > analysis["ma_20"] and p > analysis["ma_60"]:
            report += "- ✅ 股价站上全部均线，趋势偏强"
        elif p < analysis["ma_20"] and p < analysis["ma_60"]:
            report += "- ❌ 股价跌破所有均线，趋势偏弱"
        else:
            report += "- ⚠️ 股价在均线之间，方向不明"

        # 四、资金流向
        ff = analysis.get("fund_flow", {})
        if ff:
            report += f"""
### 四、资金流向（{ff.get('date', '')}）
- 主力净流入：{ff.get('主力净流入', 'N/A'):.0f} 万元
- 大单净流入：{ff.get('大单净流入', 'N/A'):.0f} 万元
- 小单净流入：{ff.get('小单净流入', 'N/A'):.0f} 万元
"""
            main_flow = ff.get("主力净流入", 0)
            if main_flow > 0:
                report += "- ✅ 主力资金净流入，资金看好"
            else:
                report += "- ❌ 主力资金净流出，资金离场"

        # 五、综合建议
        cap_stage = cap['stage']
        advice = {
            "吸筹": "中线关注，可小仓跟随主力建仓，设好止损。",
            "洗盘": "持股耐心等待，洗盘结束后大概率继续上行。",
            "主升": "趋势良好可持有，但注意不要追高加仓。",
            "出货": "建议减仓或离场，保住利润为主。",
        }
        report += f"""
### 五、操作建议
{advice.get(cap_stage, '观望为主，等待明确信号。')}

---
*⚠️ 以上分析基于量价数据和资金流向，不构成投资建议。*
"""
        return report
