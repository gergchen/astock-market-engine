"""AI 分析服务 — 从 analysis_service.py 拆分的模块化版本

保留向后兼容：from backend.services.analysis_service import X 仍然可用。
"""
from .degraded import DEGRADED_TEMPLATE, degraded_analysis
from .llm_client import call_llm
from .local_rules import analyze_emotion_local, analyze_main_capital_local, local_rule_analysis
from .prompt_builder import build_analysis_prompt
from .stock_analysis import analyze_stock, fallback_analysis

__all__ = [
    "degraded_analysis",
    "DEGRADED_TEMPLATE",
    "build_analysis_prompt",
    "call_llm",
    "local_rule_analysis",
    "analyze_main_capital_local",
    "analyze_emotion_local",
    "analyze_stock",
    "fallback_analysis",
]
