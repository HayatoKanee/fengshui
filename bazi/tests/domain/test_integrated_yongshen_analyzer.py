"""
Tests for Integrated 用神 (Favorable Elements) analyzer service.

Tests the combination of 扶抑用神 and 调候用神 methods.
"""
import pytest

from bazi.domain.models import BaZi, WuXing, DayMasterStrength
from bazi.domain.services import (
    IntegratedYongShenAnalyzer,
    IntegratedYongShenResult,
    SeasonType,
)


class TestWeightCalculation:
    """Tests for weight calculation based on season."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_extreme_cold_weights(self, analyzer):
        """极寒季节（子丑）调候权重应为60%"""
        fuyi_weight, tiaohao_weight = analyzer._get_weights(SeasonType.EXTREME_COLD)
        assert fuyi_weight == 0.4
        assert tiaohao_weight == 0.6

    def test_extreme_hot_weights(self, analyzer):
        """极热季节（午未）调候权重应为60%"""
        fuyi_weight, tiaohao_weight = analyzer._get_weights(SeasonType.EXTREME_HOT)
        assert fuyi_weight == 0.4
        assert tiaohao_weight == 0.6

    def test_cold_weights(self, analyzer):
        """较冷季节（亥）权重平衡"""
        fuyi_weight, tiaohao_weight = analyzer._get_weights(SeasonType.COLD)
        assert fuyi_weight == 0.5
        assert tiaohao_weight == 0.5

    def test_moderate_weights(self, analyzer):
        """温和季节扶抑权重应为70%"""
        fuyi_weight, tiaohao_weight = analyzer._get_weights(SeasonType.MODERATE)
        assert fuyi_weight == 0.7
        assert tiaohao_weight == 0.3


class TestFuyiScores:
    """Tests for 扶抑法 scoring."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_strong_day_master_fuyi_scores(self, analyzer):
        """身强时喜泄克，忌生扶"""
        scores = analyzer._calculate_fuyi_scores(WuXing.WOOD, is_strong=True)

        # 身强木喜火（食伤泄）和金（官杀克）
        assert scores[WuXing.FIRE] > 0  # 食伤
        assert scores[WuXing.METAL] > 0  # 官杀

        # 身强木忌水（印）和木（比劫）
        assert scores[WuXing.WATER] < 0  # 印星
        assert scores[WuXing.WOOD] < 0  # 比劫

    def test_weak_day_master_fuyi_scores(self, analyzer):
        """身弱时喜生扶，忌泄克"""
        scores = analyzer._calculate_fuyi_scores(WuXing.WOOD, is_strong=False)

        # 身弱木喜水（印）和木（比劫）
        assert scores[WuXing.WATER] > 0  # 印星
        assert scores[WuXing.WOOD] > 0  # 比劫

        # 身弱木忌火（食伤）和土（财星）
        assert scores[WuXing.FIRE] < 0  # 食伤
        assert scores[WuXing.EARTH] < 0  # 财星


class TestIntegratedAnalysis:
    """Tests for integrated analysis."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_weak_wood_winter_analysis(self, analyzer):
        """身弱甲木子月：扶抑喜水木，调候喜丁火"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(
            beneficial_value=30.0,  # 身弱
            harmful_value=70.0,
        )

        result = analyzer.analyze(bazi, strength)

        # 应该是极寒季节
        assert result.tiaohao_result.season_type == SeasonType.EXTREME_COLD

        # 权重验证
        assert result.fuyi_weight == 0.4
        assert result.tiaohao_weight == 0.6

        # 用神应该考虑调候（火）和扶抑（水/木）
        # 具体结果取决于综合评分
        assert result.yong_shen is not None
        assert result.ji_shen is not None

    def test_strong_wood_summer_analysis(self, analyzer):
        """身强甲木午月：扶抑喜火金，调候喜癸水"""
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        strength = DayMasterStrength(
            beneficial_value=70.0,  # 身强
            harmful_value=30.0,
        )

        result = analyzer.analyze(bazi, strength)

        # 应该是极热季节
        assert result.tiaohao_result.season_type == SeasonType.EXTREME_HOT

        # 权重验证
        assert result.fuyi_weight == 0.4
        assert result.tiaohao_weight == 0.6

        # 验证结果包含分析说明
        assert len(result.notes) > 0
        assert "身强" in result.notes[0]

    def test_moderate_season_fuyi_dominant(self, analyzer):
        """温和季节扶抑法为主"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")
        strength = DayMasterStrength(
            beneficial_value=30.0,
            harmful_value=70.0,
        )

        result = analyzer.analyze(bazi, strength)

        # 卯月是温和季节
        assert result.tiaohao_result.season_type == SeasonType.MODERATE

        # 扶抑权重应为70%
        assert result.fuyi_weight == 0.7
        assert result.tiaohao_weight == 0.3


class TestScoreDetails:
    """Tests for score details in results."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_scores_contain_all_elements(self, analyzer):
        """结果应包含所有五行的评分"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        assert len(result.scores) == 5
        for element in WuXing:
            assert element in result.scores
            score = result.scores[element]
            assert score.element == element

    def test_scores_have_components(self, analyzer):
        """评分应包含扶抑和调候分量"""
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        # 检查某个元素的评分
        fire_score = result.scores[WuXing.FIRE]
        assert hasattr(fire_score, 'fuyi_score')
        assert hasattr(fire_score, 'tiaohao_score')
        assert hasattr(fire_score, 'total_score')


class TestMethodUsedDescription:
    """Tests for method description."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_tiaohao_dominant_description(self, analyzer):
        """极端季节应显示调候为主"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)
        assert "调候为主" in result.method_used

    def test_fuyi_dominant_description(self, analyzer):
        """温和季节应显示扶抑为主"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)
        assert "扶抑为主" in result.method_used


class TestToFavorableElements:
    """Tests for conversion to FavorableElements."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_converts_to_favorable_elements(self, analyzer):
        """应能转换为传统FavorableElements对象"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)
        favorable = analyzer.to_favorable_elements(result)

        assert favorable.yong_shen == result.yong_shen
        assert favorable.xi_shen == result.xi_shen
        assert favorable.ji_shen == result.ji_shen
        assert favorable.chou_shen == result.chou_shen


class TestDayMasterAnalyzerIntegration:
    """Tests for DayMasterAnalyzer integration."""

    def test_day_master_analyzer_full_analysis_integrated(self):
        """DayMasterAnalyzer应能使用集成方法"""
        from bazi.domain.services import DayMasterAnalyzer

        analyzer = DayMasterAnalyzer()
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")

        # 使用传统方法
        strength_trad, favorable_trad, wuxing_trad = analyzer.full_analysis(
            bazi, use_integrated=False
        )

        # 使用集成方法
        strength_int, favorable_int, wuxing_int = analyzer.full_analysis(
            bazi, use_integrated=True
        )

        # 两种方法都应返回有效结果
        assert favorable_trad.yong_shen is not None
        assert favorable_int.yong_shen is not None

    def test_full_analysis_integrated_returns_detailed_result(self):
        """full_analysis_integrated应返回详细结果"""
        from bazi.domain.services import DayMasterAnalyzer

        analyzer = DayMasterAnalyzer()
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")

        strength, favorable, wuxing, integrated_result = analyzer.full_analysis_integrated(bazi)

        assert integrated_result is not None
        assert isinstance(integrated_result, IntegratedYongShenResult)
        assert len(integrated_result.scores) == 5
        assert len(integrated_result.notes) > 0
