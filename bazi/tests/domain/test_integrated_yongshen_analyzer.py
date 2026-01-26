"""
Tests for Integrated 用神 (Favorable Elements) analyzer service.

Tests the combination of 扶抑用神, 调候用神, and 通关用神 methods.
"""
import pytest

from bazi.domain.models import BaZi, WuXing, DayMasterStrength, WuXingStrength, WangXiang
from bazi.domain.services import (
    IntegratedYongShenAnalyzer,
    IntegratedYongShenResult,
    SeasonType,
    MethodWeights,
)


class TestMethodWeights:
    """Tests for MethodWeights validation."""

    def test_weights_must_sum_to_one(self):
        """权重必须和为1"""
        # Valid
        weights = MethodWeights(fuyi=0.5, tiaohao=0.3, tongguan=0.2)
        assert weights.fuyi == 0.5

        # Invalid - should raise
        with pytest.raises(ValueError):
            MethodWeights(fuyi=0.5, tiaohao=0.5, tongguan=0.5)


class TestWeightCalculation:
    """Tests for weight calculation based on season."""

    @pytest.fixture
    def default_analyzer(self):
        return IntegratedYongShenAnalyzer()

    @pytest.fixture
    def custom_analyzer(self):
        """Custom weights: 30/50/20 for extreme, 40/40/20 for normal."""
        return IntegratedYongShenAnalyzer(
            default_weights=MethodWeights(fuyi=0.40, tiaohao=0.40, tongguan=0.20),
            extreme_weights=MethodWeights(fuyi=0.30, tiaohao=0.50, tongguan=0.20),
        )

    def test_default_extreme_cold_weights(self, default_analyzer):
        """默认极寒季节权重: 扶抑40% + 调候40% + 通关20%"""
        weights = default_analyzer._get_weights(SeasonType.EXTREME_COLD)
        assert weights.fuyi == 0.40
        assert weights.tiaohao == 0.40
        assert weights.tongguan == 0.20

    def test_default_moderate_weights(self, default_analyzer):
        """默认温和季节权重: 扶抑50% + 调候30% + 通关20%"""
        weights = default_analyzer._get_weights(SeasonType.MODERATE)
        assert weights.fuyi == 0.50
        assert weights.tiaohao == 0.30
        assert weights.tongguan == 0.20

    def test_custom_extreme_cold_weights(self, custom_analyzer):
        """自定义极寒季节权重"""
        weights = custom_analyzer._get_weights(SeasonType.EXTREME_COLD)
        assert weights.fuyi == 0.30
        assert weights.tiaohao == 0.50
        assert weights.tongguan == 0.20

    def test_custom_moderate_weights(self, custom_analyzer):
        """自定义温和季节权重"""
        weights = custom_analyzer._get_weights(SeasonType.MODERATE)
        assert weights.fuyi == 0.40
        assert weights.tiaohao == 0.40
        assert weights.tongguan == 0.20


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

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_analysis_without_wuxing_strength(self, analyzer):
        """不提供wuxing_strength时，通关评分为0"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)

        result = analyzer.analyze(bazi, strength, wuxing_strength=None)

        # 应该完成分析，通关评分为0
        assert result.yong_shen is not None
        for score in result.scores.values():
            assert score.tongguan_score == 0.0

    def test_analysis_with_wuxing_strength(self, analyzer):
        """提供wuxing_strength时，进行通关分析"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, strength, wuxing_strength)

        # 应该检测到金木相战，水通关
        assert result.tongguan_result is not None
        assert result.tongguan_result.has_conflict is True

    def test_extreme_season_weights_applied(self, analyzer):
        """极端季节应用正确权重"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")  # 子月极寒
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        # 子月是极寒季节
        assert result.tiaohao_result.season_type == SeasonType.EXTREME_COLD
        assert result.weights.fuyi == 0.40
        assert result.weights.tiaohao == 0.40
        assert result.weights.tongguan == 0.20

    def test_moderate_season_weights_applied(self, analyzer):
        """温和季节应用正确权重"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")  # 卯月温和
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        # 卯月是温和季节
        assert result.tiaohao_result.season_type == SeasonType.MODERATE
        assert result.weights.fuyi == 0.50
        assert result.weights.tiaohao == 0.30
        assert result.weights.tongguan == 0.20


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

    def test_scores_have_all_components(self, analyzer):
        """评分应包含扶抑、调候、通关三个分量"""
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        fire_score = result.scores[WuXing.FIRE]
        assert hasattr(fire_score, 'fuyi_score')
        assert hasattr(fire_score, 'tiaohao_score')
        assert hasattr(fire_score, 'tongguan_score')
        assert hasattr(fire_score, 'total_score')


class TestConfigurableWeights:
    """Tests for configurable weights."""

    def test_default_weights(self):
        """默认权重: 50/30/20"""
        analyzer = IntegratedYongShenAnalyzer()
        assert analyzer._default_weights.fuyi == 0.50
        assert analyzer._default_weights.tiaohao == 0.30
        assert analyzer._default_weights.tongguan == 0.20

    def test_custom_weights(self):
        """可以自定义权重"""
        custom = MethodWeights(fuyi=0.40, tiaohao=0.40, tongguan=0.20)
        analyzer = IntegratedYongShenAnalyzer(default_weights=custom)
        assert analyzer._default_weights.fuyi == 0.40
        assert analyzer._default_weights.tiaohao == 0.40

    def test_custom_weights_affect_analysis(self):
        """自定义权重影响分析结果"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")  # 温和季节
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        default = IntegratedYongShenAnalyzer()
        custom = IntegratedYongShenAnalyzer(
            default_weights=MethodWeights(fuyi=0.30, tiaohao=0.50, tongguan=0.20)
        )

        result_default = default.analyze(bazi, strength)
        result_custom = custom.analyze(bazi, strength)

        # 自定义权重的调候权重应该更高
        assert result_custom.weights.tiaohao > result_default.weights.tiaohao


class TestMethodUsedDescription:
    """Tests for method description."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_fuyi_dominant_description(self, analyzer):
        """扶抑为主时显示正确描述"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")  # 温和季节
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)
        assert "扶抑为主" in result.method_used

    def test_tongguan_mentioned_when_conflict(self, analyzer):
        """有相战时显示通关"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, strength, wuxing_strength)
        assert "通关" in result.method_used


class TestNotesContent:
    """Tests for analysis notes."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_notes_include_day_master_strength(self, analyzer):
        """备注应包含日主强弱"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "身弱" in notes_text

    def test_notes_include_season(self, analyzer):
        """备注应包含季节"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "极寒" in notes_text

    def test_notes_include_weights(self, analyzer):
        """备注应包含权重"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "扶抑" in notes_text
        assert "调候" in notes_text
        assert "通关" in notes_text

    def test_notes_include_conflict_when_present(self, analyzer):
        """有相战时备注应包含相战信息"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, strength, wuxing_strength)

        notes_text = " ".join(result.notes)
        assert "相战" in notes_text


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


class TestClassicalDerivation:
    """Tests for classical five-element relationship derivation."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_classical_derivation_wood_yongshen(self, analyzer):
        """
        验证古籍定义的五行生克推导：
        用神=木 → 喜神=水(水生木) → 忌神=金(金克木) → 仇神=土(土生金) → 闲神=火(木生火)
        """
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        # 身弱，用神应该是印星(水)或比劫(木)
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)

        result = analyzer.analyze(bazi, strength)

        # 验证五行生克关系链
        assert result.xi_shen == result.yong_shen.generated_by  # 喜神=生用神
        assert result.ji_shen == result.yong_shen.overcome_by   # 忌神=克用神
        assert result.chou_shen == result.ji_shen.generated_by  # 仇神=生忌神
        assert result.xian_shen == result.yong_shen.generates   # 闲神=用神所生

    def test_all_five_elements_covered(self, analyzer):
        """五神应覆盖全部五行"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        all_shens = {
            result.yong_shen,
            result.xi_shen,
            result.ji_shen,
            result.chou_shen,
            result.xian_shen
        }
        # 五神应该覆盖全部五行
        assert len(all_shens) == 5
        assert all_shens == set(WuXing)

    def test_notes_include_derivation_chain(self, analyzer):
        """备注应包含推导链说明"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "生用神" in notes_text
        assert "克用神" in notes_text
        assert "生忌神" in notes_text


class TestDayMasterAnalyzerIntegration:
    """Tests for DayMasterAnalyzer integration."""

    def test_full_analysis_integrated_with_tongguan(self):
        """full_analysis_integrated应包含通关分析"""
        from bazi.domain.services import DayMasterAnalyzer

        analyzer = DayMasterAnalyzer()
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")

        strength, favorable, wuxing, integrated_result = analyzer.full_analysis_integrated(bazi)

        assert integrated_result is not None
        assert isinstance(integrated_result, IntegratedYongShenResult)
        assert integrated_result.tongguan_result is not None
        assert len(integrated_result.notes) > 0

    def test_full_analysis_use_integrated_flag(self):
        """full_analysis的use_integrated标志应工作"""
        from bazi.domain.services import DayMasterAnalyzer

        analyzer = DayMasterAnalyzer()
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")

        # 传统方法
        _, favorable_trad, _ = analyzer.full_analysis(bazi, use_integrated=False)

        # 集成方法
        _, favorable_int, _ = analyzer.full_analysis(bazi, use_integrated=True)

        # 两种方法都应返回有效结果
        assert favorable_trad.yong_shen is not None
        assert favorable_int.yong_shen is not None
