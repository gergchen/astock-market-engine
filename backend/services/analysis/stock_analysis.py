"""个股分析主流程 — 串联数据获取、LLM 调用、降级逻辑"""
import logging

from .degraded import degraded_analysis
from .llm_client import call_llm
from .local_rules import local_rule_analysis
from .prompt_builder import build_analysis_prompt

logger = logging.getLogger('astock.analysis')


def analyze_stock(df, stock_name, symbol, summary, fund_flow, analysis_type, v8_scores=None):
    """主分析入口 — 优先 LLM，失败降级到本地规则"""
    quality = df.attrs.get('_quality')
    is_degraded = quality is not None and not quality.is_valid()

    if is_degraded:
        return {
            'summary': summary,
            'analysis': degraded_analysis(
                stock_name, symbol,
                source=quality.source.value if quality else 'unknown',
                confidence=quality.confidence if quality else 0,
                realtime=quality.realtime if quality else False,
            ),
            'data_points': len(df),
            'is_degraded': True,
        }

    market_data = _df_to_text(df.tail(60))
    fund_flow_text = _fund_flow_to_text(fund_flow)

    prompt = build_analysis_prompt(
        stock_name, symbol, market_data, fund_flow_text,
        analysis_type=analysis_type, v8_scores=v8_scores,
    )

    try:
        analysis_text = call_llm(prompt)
        return {
            'summary': summary,
            'analysis': analysis_text,
            'data_points': len(df),
        }
    except Exception as e:
        logger.warning('LLM 调用失败，降级到本地规则: %s', e)
        return fallback_analysis(df, stock_name, symbol, summary, fund_flow)


def fallback_analysis(df, stock_name, symbol, summary, fund_flow):
    """LLM 失败时的降级分析"""
    return local_rule_analysis(df, stock_name, symbol, summary, fund_flow)


def _df_to_text(df) -> str:
    """将 DataFrame 转为 LLM 可读的文本"""
    lines = []
    for _, row in df.iterrows():
        date = str(row.get('date', row.get('日期', '')))[:10]
        o = row.get('open', row.get('开盘', 0))
        c = row.get('close', row.get('收盘', 0))
        h = row.get('high', row.get('最高', 0))
        l = row.get('low', row.get('最低', 0))
        v = row.get('volume', row.get('成交量', 0))
        pct = row.get('pct_change', row.get('涨跌幅', 0))
        lines.append(f'{date} O:{o} C:{c} H:{h} L:{l} V:{v} 涨跌:{pct}%')
    return '\n'.join(lines)


def _fund_flow_to_text(fund_flow) -> str:
    """将资金流向转为文本"""
    if not fund_flow:
        return '暂无资金流向数据'
    if isinstance(fund_flow, dict):
        parts = []
        for k, v in fund_flow.items():
            if k != '_quality':
                parts.append(f'{k}: {v}')
        return '\n'.join(parts) if parts else '暂无资金流向数据'
    return str(fund_flow)
