"""AI 分析服务 — 向后兼容入口

实际代码已拆分到 backend/services/analysis/ 目录。
本文件保留以兼容 from backend.services.analysis_service import X 的导入。
"""
from backend.services.analysis.degraded import DEGRADED_TEMPLATE, degraded_analysis
from backend.services.analysis.llm_client import call_llm as _call_llm
from backend.services.analysis.local_rules import (
    analyze_emotion_local as _analyze_emotion_local,
)
from backend.services.analysis.local_rules import (
    analyze_main_capital_local as _analyze_main_capital_local,
)
from backend.services.analysis.local_rules import (
    local_rule_analysis as _local_rule_analysis,
)
from backend.services.analysis.prompt_builder import build_analysis_prompt as _build_analysis_prompt
from backend.services.analysis.stock_analysis import (
    analyze_stock,
)
from backend.services.analysis.stock_analysis import (
    fallback_analysis as _fallback_analysis,
)


def _call_claude(prompt: str) -> str:
    return _call_llm(prompt)


def _call_openai(prompt: str) -> str:
    return _call_llm(prompt)
