"""
Tests for 调候用神 (Climate Adjustment) analyzer service.

Based on《穷通宝鉴》rules.
"""
import pytest

from bazi.domain.models import BaZi, WuXing
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.services import TiaoHouAnalyzer, SeasonType


class TestSeasonTypeClassification:
    """Tests for season type determination."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    @pytest.mark.parametrize("month,expected", [
        ("子", SeasonType.EXTREME_COLD),
        ("丑", SeasonType.EXTREME_COLD),
        ("亥", SeasonType.COLD),
        ("午", SeasonType.EXTREME_HOT),
        ("未", SeasonType.EXTREME_HOT),
        ("巳", SeasonType.HOT),
        ("寅", SeasonType.MODERATE),
        ("卯", SeasonType.MODERATE),
        ("辰", SeasonType.MODERATE),
        ("申", SeasonType.MODERATE),
        ("酉", SeasonType.MODERATE),
        ("戌", SeasonType.MODERATE),
    ])
    def test_season_classification(self, analyzer, month, expected):
        """Test that months are classified into correct season types."""
        # Create a BaZi with the test month
        bazi = BaZi.from_chinese(f"甲子甲{month}甲子甲子")
        result = analyzer.analyze(bazi)
        assert result.season_type == expected


class TestTiaoHouJiaWood:
    """Tests for 甲木 climate adjustment rules."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_jia_wood_winter_zi_month(self, analyzer):
        """甲木子月：丁先庚后，丙火佐之"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        result = analyzer.analyze(bazi)

        assert result.day_stem == HeavenlyStem.JIA
        assert result.month_branch == EarthlyBranch.ZI
        assert result.season_type == SeasonType.EXTREME_COLD
        assert HeavenlyStem.DING in result.primary_yongshen
        assert HeavenlyStem.GENG in result.secondary_yongshen
        assert HeavenlyStem.BING in result.secondary_yongshen
        assert result.urgency >= 0.8

    def test_jia_wood_winter_chou_month(self, analyzer):
        """甲木丑月：丁为必须，通根巳寅者佳"""
        bazi = BaZi.from_chinese("甲子甲丑甲子甲子")
        result = analyzer.analyze(bazi)

        assert HeavenlyStem.DING in result.primary_yongshen
        assert result.urgency >= 0.8

    def test_jia_wood_summer_wu_month(self, analyzer):
        """甲木午月：木性虚焦，癸为主要"""
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        result = analyzer.analyze(bazi)

        assert HeavenlyStem.GUI in result.primary_yongshen
        assert result.season_type == SeasonType.EXTREME_HOT


class TestTiaoHouYiWood:
    """Tests for 乙木 climate adjustment rules."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_yi_wood_winter_zi_month(self, analyzer):
        """乙木子月：专用丙火，忌癸水"""
        bazi = BaZi.from_chinese("甲子甲子乙丑甲子")
        result = analyzer.analyze(bazi)

        assert result.day_stem == HeavenlyStem.YI
        assert HeavenlyStem.BING in result.primary_yongshen
        # 癸水不应在推荐中
        assert HeavenlyStem.GUI not in result.primary_yongshen

    def test_yi_wood_summer_si_month(self, analyzer):
        """乙木巳月：专用癸水调候为急"""
        bazi = BaZi.from_chinese("甲子甲巳乙丑甲子")
        result = analyzer.analyze(bazi)

        assert HeavenlyStem.GUI in result.primary_yongshen


class TestTiaoHouBingFire:
    """Tests for 丙火 climate adjustment rules."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_bing_fire_needs_ren_water(self, analyzer):
        """丙火喜壬水辅映"""
        bazi = BaZi.from_chinese("甲子甲寅丙午甲子")
        result = analyzer.analyze(bazi)

        assert result.day_stem == HeavenlyStem.BING
        assert HeavenlyStem.REN in result.primary_yongshen


class TestTiaoHouGengMetal:
    """Tests for 庚金 climate adjustment rules."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_geng_metal_summer_wu_month(self, analyzer):
        """庚金午月：专用壬水，癸次之"""
        bazi = BaZi.from_chinese("甲子甲午庚申甲子")
        result = analyzer.analyze(bazi)

        assert result.day_stem == HeavenlyStem.GENG
        assert HeavenlyStem.REN in result.primary_yongshen

    def test_geng_metal_winter_needs_ding_fire(self, analyzer):
        """庚金冬月：水冷金寒爱丙丁"""
        bazi = BaZi.from_chinese("甲子甲亥庚申甲子")
        result = analyzer.analyze(bazi)

        # 亥月庚金需丁丙
        assert HeavenlyStem.DING in result.primary_yongshen or \
               HeavenlyStem.BING in result.primary_yongshen


class TestTiaoHouXinMetal:
    """Tests for 辛金 climate adjustment rules."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_xin_metal_needs_ren_water(self, analyzer):
        """辛金喜壬水淘洗，金白水清"""
        bazi = BaZi.from_chinese("甲子甲亥辛酉甲子")
        result = analyzer.analyze(bazi)

        assert result.day_stem == HeavenlyStem.XIN
        assert HeavenlyStem.REN in result.primary_yongshen

    def test_xin_metal_winter_needs_bing_fire(self, analyzer):
        """辛金子月：冬月辛金，不能缺丙火温暖"""
        bazi = BaZi.from_chinese("甲子甲子辛酉甲子")
        result = analyzer.analyze(bazi)

        assert HeavenlyStem.BING in result.primary_yongshen


class TestTiaoHouWuxing:
    """Tests for getting 调候用神 as WuXing."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_get_tiaohao_wuxing_winter(self, analyzer):
        """冬月调候用神多为火"""
        # 甲木子月需丁火
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing = analyzer.get_tiaohao_wuxing(bazi)
        assert wuxing == WuXing.FIRE

    def test_get_tiaohao_wuxing_summer(self, analyzer):
        """夏月调候用神多为水"""
        # 甲木午月需癸水
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        wuxing = analyzer.get_tiaohao_wuxing(bazi)
        assert wuxing == WuXing.WATER

    def test_needs_climate_adjustment_extreme(self, analyzer):
        """极端季节需要调候"""
        # 子月
        bazi_winter = BaZi.from_chinese("甲子甲子甲子甲子")
        assert analyzer.needs_climate_adjustment(bazi_winter) is True

        # 午月
        bazi_summer = BaZi.from_chinese("甲子甲午甲子甲子")
        assert analyzer.needs_climate_adjustment(bazi_summer) is True

    def test_needs_climate_adjustment_moderate(self, analyzer):
        """温和季节调候需求低"""
        # 卯月
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")
        assert analyzer.needs_climate_adjustment(bazi) is False


class TestTiaoHouUrgency:
    """Tests for urgency scoring."""

    @pytest.fixture
    def analyzer(self):
        return TiaoHouAnalyzer()

    def test_extreme_cold_high_urgency(self, analyzer):
        """极寒季节（子丑）调候急迫度高"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        result = analyzer.analyze(bazi)
        assert result.urgency >= 0.8

    def test_extreme_hot_high_urgency(self, analyzer):
        """极热季节（午未）调候急迫度高"""
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        result = analyzer.analyze(bazi)
        assert result.urgency >= 0.8

    def test_moderate_low_urgency(self, analyzer):
        """温和季节调候急迫度低"""
        bazi = BaZi.from_chinese("甲子甲辰甲子甲子")
        result = analyzer.analyze(bazi)
        assert result.urgency <= 0.4
