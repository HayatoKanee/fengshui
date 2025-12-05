"""
Tests for WuXingCalculator domain service.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.elements import WuXing, WangXiang
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.models.pillar import Pillar
from bazi.domain.models.bazi import BaZi
from bazi.domain.services.wuxing_calculator import WuXingCalculator


class TestGetRelationshipValues:
    """Tests for get_relationship_values method."""

    @pytest.fixture
    def calculator(self):
        return WuXingCalculator()

    def test_same_element_wood(self):
        """Same element (Wood-Wood) returns (10, 10)."""
        result = WuXingCalculator.get_relationship_values(
            HeavenlyStem.JIA,  # Wood
            EarthlyBranch.YIN   # Wood
        )
        assert result == (10, 10)

    def test_same_element_fire(self):
        """Same element (Fire-Fire) returns (10, 10)."""
        result = WuXingCalculator.get_relationship_values(
            HeavenlyStem.BING,  # Fire
            EarthlyBranch.WU    # Fire
        )
        assert result == (10, 10)

    def test_stem_generates_branch(self):
        """Wood generates Fire: (6, 8)."""
        result = WuXingCalculator.get_relationship_values(
            HeavenlyStem.JIA,   # Wood
            EarthlyBranch.SI    # Fire
        )
        assert result == (6, 8)

    def test_stem_overcomes_branch(self):
        """Wood overcomes Earth: (4, 2)."""
        result = WuXingCalculator.get_relationship_values(
            HeavenlyStem.JIA,   # Wood
            EarthlyBranch.CHOU  # Earth
        )
        assert result == (4, 2)

    def test_branch_overcomes_stem(self):
        """Metal overcomes Wood: (2, 4)."""
        result = WuXingCalculator.get_relationship_values(
            HeavenlyStem.JIA,   # Wood
            EarthlyBranch.SHEN  # Metal
        )
        assert result == (2, 4)

    def test_branch_generates_stem(self):
        """Water generates Wood: (8, 6)."""
        result = WuXingCalculator.get_relationship_values(
            HeavenlyStem.JIA,   # Wood
            EarthlyBranch.ZI    # Water
        )
        assert result == (8, 6)


class TestGetPillarValues:
    """Tests for get_pillar_values method."""

    def test_pillar_jia_zi(self):
        """甲子 (Wood-Water) returns (8, 6) - water generates wood."""
        pillar = Pillar.from_chinese("甲子")
        result = WuXingCalculator.get_pillar_values(pillar)
        assert result == (8, 6)

    def test_pillar_jia_yin(self):
        """甲寅 (Wood-Wood) returns (10, 10) - same element."""
        pillar = Pillar.from_chinese("甲寅")
        result = WuXingCalculator.get_pillar_values(pillar)
        assert result == (10, 10)


class TestGetSeason:
    """Tests for get_season method."""

    def test_spring_yin(self):
        """寅 is spring."""
        result = WuXingCalculator.get_season(EarthlyBranch.YIN)
        assert result == "春"

    def test_spring_mao(self):
        """卯 is spring."""
        result = WuXingCalculator.get_season(EarthlyBranch.MAO)
        assert result == "春"

    def test_summer_si(self):
        """巳 is summer."""
        result = WuXingCalculator.get_season(EarthlyBranch.SI)
        assert result == "夏"

    def test_summer_wu(self):
        """午 is summer."""
        result = WuXingCalculator.get_season(EarthlyBranch.WU)
        assert result == "夏"

    def test_autumn_shen(self):
        """申 is autumn."""
        result = WuXingCalculator.get_season(EarthlyBranch.SHEN)
        assert result == "秋"

    def test_autumn_you(self):
        """酉 is autumn."""
        result = WuXingCalculator.get_season(EarthlyBranch.YOU)
        assert result == "秋"

    def test_winter_zi(self):
        """子 is winter."""
        result = WuXingCalculator.get_season(EarthlyBranch.ZI)
        assert result == "冬"

    def test_winter_hai(self):
        """亥 is winter."""
        result = WuXingCalculator.get_season(EarthlyBranch.HAI)
        assert result == "冬"

    def test_earth_branches_normal(self):
        """Earth branches (丑辰未戌) follow their season normally."""
        # 丑 follows winter
        result = WuXingCalculator.get_season(EarthlyBranch.CHOU)
        assert result == "冬"

        # 辰 follows spring
        result = WuXingCalculator.get_season(EarthlyBranch.CHEN)
        assert result == "春"

    def test_earth_dominant_period(self):
        """Earth branches become 土旺 during earth-dominant period."""
        result = WuXingCalculator.get_season(EarthlyBranch.CHOU, is_earth_dominant=True)
        assert result == "土旺"

        result = WuXingCalculator.get_season(EarthlyBranch.CHEN, is_earth_dominant=True)
        assert result == "土旺"


class TestGetWangXiang:
    """Tests for get_wang_xiang method."""

    def test_spring_wood_is_wang(self):
        """In spring, Wood is prosperous (旺)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.YIN)
        assert wang_xiang[WuXing.WOOD] == WangXiang.WANG

    def test_spring_fire_is_xiang(self):
        """In spring, Fire is prime (相)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.YIN)
        assert wang_xiang[WuXing.FIRE] == WangXiang.XIANG

    def test_spring_metal_is_qiu(self):
        """In spring, Metal is imprisoned (囚)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.YIN)
        assert wang_xiang[WuXing.METAL] == WangXiang.QIU

    def test_summer_fire_is_wang(self):
        """In summer, Fire is prosperous (旺)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.WU)
        assert wang_xiang[WuXing.FIRE] == WangXiang.WANG

    def test_autumn_metal_is_wang(self):
        """In autumn, Metal is prosperous (旺)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.YOU)
        assert wang_xiang[WuXing.METAL] == WangXiang.WANG

    def test_winter_water_is_wang(self):
        """In winter, Water is prosperous (旺)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.ZI)
        assert wang_xiang[WuXing.WATER] == WangXiang.WANG

    def test_earth_dominant_earth_is_wang(self):
        """In earth-dominant period, Earth is prosperous (旺)."""
        wang_xiang = WuXingCalculator.get_wang_xiang(EarthlyBranch.CHOU, is_earth_dominant=True)
        assert wang_xiang[WuXing.EARTH] == WangXiang.WANG


class TestCalculateWangXiangMultiplier:
    """Tests for calculate_wang_xiang_multiplier method."""

    def test_wang_multiplier(self):
        """WANG phase has 1.2 multiplier."""
        wang_xiang = {WuXing.WOOD: WangXiang.WANG}
        result = WuXingCalculator.calculate_wang_xiang_multiplier(WuXing.WOOD, wang_xiang)
        assert result == 1.2

    def test_xiang_multiplier(self):
        """XIANG phase has 1.2 multiplier."""
        wang_xiang = {WuXing.FIRE: WangXiang.XIANG}
        result = WuXingCalculator.calculate_wang_xiang_multiplier(WuXing.FIRE, wang_xiang)
        assert result == 1.2

    def test_xiu_multiplier(self):
        """XIU phase has 1.0 multiplier."""
        wang_xiang = {WuXing.WATER: WangXiang.XIU}
        result = WuXingCalculator.calculate_wang_xiang_multiplier(WuXing.WATER, wang_xiang)
        assert result == 1.0

    def test_qiu_multiplier(self):
        """QIU phase has 0.8 multiplier."""
        wang_xiang = {WuXing.METAL: WangXiang.QIU}
        result = WuXingCalculator.calculate_wang_xiang_multiplier(WuXing.METAL, wang_xiang)
        assert result == 0.8

    def test_si_multiplier(self):
        """SI phase has 0.8 multiplier."""
        wang_xiang = {WuXing.EARTH: WangXiang.SI}
        result = WuXingCalculator.calculate_wang_xiang_multiplier(WuXing.EARTH, wang_xiang)
        assert result == 0.8


class TestCalculateStrength:
    """Tests for calculate_strength method."""

    @pytest.fixture
    def calculator(self):
        return WuXingCalculator()

    def test_calculate_strength_returns_wuxing_strength(self, calculator):
        """calculate_strength returns WuXingStrength dataclass."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.calculate_strength(bazi)

        assert hasattr(result, 'raw_values')
        assert hasattr(result, 'adjusted_values')
        assert hasattr(result, 'wang_xiang')

    def test_calculate_strength_raw_values_positive(self, calculator):
        """All raw values should be non-negative."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.calculate_strength(bazi)

        for element in WuXing:
            assert result.raw_values[element] >= 0

    def test_calculate_strength_adjusted_values_positive(self, calculator):
        """All adjusted values should be non-negative."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.calculate_strength(bazi)

        for element in WuXing:
            assert result.adjusted_values[element] >= 0

    def test_calculate_strength_wood_dominant_bazi(self, calculator):
        """BaZi with many Wood elements should have high Wood value."""
        bazi = BaZi.from_chinese("甲寅 乙卯 甲寅 乙卯")  # All Wood
        result = calculator.calculate_strength(bazi)

        # Wood should be the highest
        wood_value = result.raw_values[WuXing.WOOD]
        for element in WuXing:
            if element != WuXing.WOOD:
                assert wood_value >= result.raw_values[element]

    def test_calculate_strength_seasonal_adjustment(self, calculator):
        """Seasonal adjustment affects element strength."""
        # Same BaZi in different months (month is second pillar)
        bazi_spring = BaZi.from_chinese("甲寅 甲寅 甲寅 甲寅")  # Month 寅 (spring)
        bazi_autumn = BaZi.from_chinese("甲寅 甲申 甲寅 甲寅")  # Month 申 (autumn)

        result_spring = calculator.calculate_strength(bazi_spring)
        result_autumn = calculator.calculate_strength(bazi_autumn)

        # Wood is WANG (旺) in spring, SI (死) in autumn
        assert result_spring.wang_xiang[WuXing.WOOD] == WangXiang.WANG
        assert result_autumn.wang_xiang[WuXing.WOOD] == WangXiang.SI


class TestAccumulateWuXingValues:
    """Tests for accumulate_wuxing_values method."""

    @pytest.fixture
    def calculator(self):
        return WuXingCalculator()

    def test_accumulate_returns_all_elements(self, calculator):
        """Result contains all five elements."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        wang_xiang = WuXingCalculator.get_wang_xiang(bazi.month_pillar.branch)
        result = calculator.accumulate_wuxing_values(bazi, wang_xiang)

        assert len(result) == 5
        assert set(result.keys()) == set(WuXing)

    def test_accumulate_non_negative(self, calculator):
        """All accumulated values are non-negative."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        wang_xiang = WuXingCalculator.get_wang_xiang(bazi.month_pillar.branch)
        result = calculator.accumulate_wuxing_values(bazi, wang_xiang)

        for value in result.values():
            assert value >= 0

    def test_accumulate_includes_hidden_stems(self, calculator):
        """Calculation includes hidden stems from branches."""
        # 甲子: 甲(Wood), 子 contains 癸(Water)
        bazi = BaZi.from_chinese("甲子 甲子 甲子 甲子")
        wang_xiang = WuXingCalculator.get_wang_xiang(bazi.month_pillar.branch)
        result = calculator.accumulate_wuxing_values(bazi, wang_xiang)

        # Should have Wood from stems and Water from hidden stems
        assert result[WuXing.WOOD] > 0
        assert result[WuXing.WATER] > 0
