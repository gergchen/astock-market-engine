"""降级路径和本地规则分析测试"""
import pytest
import pandas as pd


class TestDegradedAnalysis:
    """降级分析模板测试"""

    def test_degraded_analysis_basic(self):
        from backend.services.analysis.degraded import degraded_analysis
        result = degraded_analysis(
            stock_name="测试股票",
            symbol="000001",
            source="MOCK",
            confidence=0.0,
            realtime=False
        )
        assert "测试股票" in result
        assert "000001" in result
        assert "系统已降级" in result
        assert "安全模式" in result

    def test_degraded_analysis_realtime_label(self):
        from backend.services.analysis.degraded import degraded_analysis
        result = degraded_analysis(
            stock_name="测试股票",
            symbol="000001",
            source="SINA",
            confidence=0.95,
            realtime=True
        )
        assert "是" in result

    def test_degraded_analysis_non_realtime_label(self):
        from backend.services.analysis.degraded import degraded_analysis
        result = degraded_analysis(
            stock_name="测试股票",
            symbol="000001",
            source="SINA",
            confidence=0.95,
            realtime=False
        )
        assert "否" in result


class TestLocalRules:
    """本地规则引擎测试"""

    def _make_sample_df(self, pct_change=2.5, volume=1000000, close=10.0, high=10.5, low=9.5, turnover=2.0):
        """创建测试用的 DataFrame"""
        data = []
        for i in range(60):
            data.append({
                'pct_change': 0.5 if i < 59 else pct_change,
                'volume': 500000 if i < 59 else volume,
                'close': 9.5 + i * 0.01 if i < 59 else close,
                'high': 10.0 + i * 0.01 if i < 59 else high,
                'low': 9.0 + i * 0.01 if i < 59 else low,
                'turnover': 1.5 if i < 59 else turnover,
            })
        return pd.DataFrame(data)

    def test_strong_rise(self):
        from backend.services.analysis.local_rules import local_rule_analysis
        df = self._make_sample_df(pct_change=5.0, volume=2000000)
        result = local_rule_analysis(df, "测试股票", "000001", "摘要", {})
        assert "强势上涨" in result['analysis']
        assert result['data_points'] == 60

    def test_slight_rise(self):
        from backend.services.analysis.local_rules import local_rule_analysis
        df = self._make_sample_df(pct_change=1.5)
        result = local_rule_analysis(df, "测试股票", "000001", "摘要", {})
        assert "小幅上涨" in result['analysis']

    def test_slight_fall(self):
        from backend.services.analysis.local_rules import local_rule_analysis
        df = self._make_sample_df(pct_change=-1.5)
        result = local_rule_analysis(df, "测试股票", "000001", "摘要", {})
        assert "小幅下跌" in result['analysis']

    def test_large_fall(self):
        from backend.services.analysis.local_rules import local_rule_analysis
        df = self._make_sample_df(pct_change=-5.0)
        result = local_rule_analysis(df, "测试股票", "000001", "摘要", {})
        assert "大幅下跌" in result['analysis']

    def test_high_turnover_risk(self):
        from backend.services.analysis.local_rules import local_rule_analysis
        df = self._make_sample_df(turnover=8.0)
        result = local_rule_analysis(df, "测试股票", "000001", "摘要", {})
        assert "换手率偏高" in result['analysis']

    def test_result_structure(self):
        from backend.services.analysis.local_rules import local_rule_analysis
        df = self._make_sample_df()
        result = local_rule_analysis(df, "测试股票", "000001", "摘要", {})
        assert 'summary' in result
        assert 'analysis' in result
        assert 'data_points' in result


class TestMainCapitalLocal:
    """主力行为本地规则测试"""

    def test_accumulation_stage(self):
        from backend.services.analysis.local_rules import analyze_main_capital_local
        # 低位、缩量、温和换手
        result = analyze_main_capital_local(
            close=8.0, avg_close_60=10.0, vol=500000, avg_vol_20=600000,
            turnover=2.0, pct=0.5, high=8.2, low=7.8
        )
        assert 'title' in result
        assert 'content' in result
        assert 'reasons' in result

    def test_distribution_stage(self):
        from backend.services.analysis.local_rules import analyze_main_capital_local
        # 高位、放量、高换手
        result = analyze_main_capital_local(
            close=12.0, avg_close_60=10.0, vol=1500000, avg_vol_20=600000,
            turnover=6.0, pct=-2.0, high=12.5, low=11.5
        )
        assert 'title' in result
