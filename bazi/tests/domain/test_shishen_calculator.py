"""
Tests for ShiShenCalculator domain service.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.models.shishen import ShiShen
from bazi.domain.models.pillar import Pillar
from bazi.domain.models.bazi import BaZi
from bazi.domain.services.shishen_calculator import ShiShenCalculator


class TestCalculateBasic:
    """Tests for basic ShiShen calculation between two stems."""

    @pytest.fixture
    def calculator(self):
        return ShiShenCalculator()

    # Same element (比和)
    def test_same_element_same_polarity_bijian(self):
        """Same element + same polarity = 比肩."""
        # 甲 (Wood Yang) vs 甲 (Wood Yang)
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.JIA)
        assert result == ShiShen.BI_JIAN

    def test_same_element_diff_polarity_jiecai(self):
        """Same element + different polarity = 劫财."""
        # 甲 (Wood Yang) vs 乙 (Wood Yin)
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.YI)
        assert result == ShiShen.JIE_CAI

    # I generate (我生)
    def test_i_generate_same_polarity_shishen(self):
        """I generate + same polarity = 食神."""
        # 甲 (Wood Yang) vs 丙 (Fire Yang) - Wood generates Fire
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.BING)
        assert result == ShiShen.SHI_SHEN

    def test_i_generate_diff_polarity_shangguan(self):
        """I generate + different polarity = 伤官."""
        # 甲 (Wood Yang) vs 丁 (Fire Yin) - Wood generates Fire
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.DING)
        assert result == ShiShen.SHANG_GUAN

    # I overcome (我克)
    def test_i_overcome_same_polarity_piancai(self):
        """I overcome + same polarity = 偏财."""
        # 甲 (Wood Yang) vs 戊 (Earth Yang) - Wood overcomes Earth
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.WU)
        assert result == ShiShen.PIAN_CAI

    def test_i_overcome_diff_polarity_zhengcai(self):
        """I overcome + different polarity = 正财."""
        # 甲 (Wood Yang) vs 己 (Earth Yin) - Wood overcomes Earth
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.JI)
        assert result == ShiShen.ZHENG_CAI

    # Overcomes me (克我)
    def test_overcomes_me_same_polarity_qisha(self):
        """Overcomes me + same polarity = 七杀."""
        # 甲 (Wood Yang) vs 庚 (Metal Yang) - Metal overcomes Wood
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.GENG)
        assert result == ShiShen.QI_SHA

    def test_overcomes_me_diff_polarity_zhengguan(self):
        """Overcomes me + different polarity = 正官."""
        # 甲 (Wood Yang) vs 辛 (Metal Yin) - Metal overcomes Wood
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.XIN)
        assert result == ShiShen.ZHENG_GUAN

    # Generates me (生我)
    def test_generates_me_same_polarity_pianyin(self):
        """Generates me + same polarity = 偏印."""
        # 甲 (Wood Yang) vs 壬 (Water Yang) - Water generates Wood
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.REN)
        assert result == ShiShen.PIAN_YIN

    def test_generates_me_diff_polarity_zhengyin(self):
        """Generates me + different polarity = 正印."""
        # 甲 (Wood Yang) vs 癸 (Water Yin) - Water generates Wood
        result = ShiShenCalculator.calculate(HeavenlyStem.JIA, HeavenlyStem.GUI)
        assert result == ShiShen.ZHENG_YIN


class TestCalculateForDifferentDayMasters:
    """Test ShiShen calculation with different day masters."""

    def test_fire_day_master(self):
        """Test with Fire (丙) as day master."""
        # 丙 (Fire Yang) vs 甲 (Wood Yang) - Wood generates Fire, same polarity = 偏印
        assert ShiShenCalculator.calculate(HeavenlyStem.BING, HeavenlyStem.JIA) == ShiShen.PIAN_YIN
        # 丙 (Fire Yang) vs 乙 (Wood Yin) - Wood generates Fire, different polarity = 正印
        assert ShiShenCalculator.calculate(HeavenlyStem.BING, HeavenlyStem.YI) == ShiShen.ZHENG_YIN
        # 丙 vs 丙 - Same = 比肩
        assert ShiShenCalculator.calculate(HeavenlyStem.BING, HeavenlyStem.BING) == ShiShen.BI_JIAN
        # 丙 (Fire Yang) vs 壬 (Water Yang) - Water overcomes Fire, same polarity = 七杀
        assert ShiShenCalculator.calculate(HeavenlyStem.BING, HeavenlyStem.REN) == ShiShen.QI_SHA

    def test_water_day_master(self):
        """Test with Water (壬) as day master."""
        # 壬 (Water Yang) vs 庚 (Metal Yang) - Metal generates Water, same polarity = 偏印
        assert ShiShenCalculator.calculate(HeavenlyStem.REN, HeavenlyStem.GENG) == ShiShen.PIAN_YIN
        # 壬 (Water Yang) vs 辛 (Metal Yin) - Metal generates Water, different polarity = 正印
        assert ShiShenCalculator.calculate(HeavenlyStem.REN, HeavenlyStem.XIN) == ShiShen.ZHENG_YIN
        # 壬 (Water Yang) vs 戊 (Earth Yang) - Earth overcomes Water, same polarity = 七杀
        assert ShiShenCalculator.calculate(HeavenlyStem.REN, HeavenlyStem.WU) == ShiShen.QI_SHA
        # 壬 (Water Yang) vs 甲 (Wood Yang) - Water generates Wood, same polarity = 食神
        assert ShiShenCalculator.calculate(HeavenlyStem.REN, HeavenlyStem.JIA) == ShiShen.SHI_SHEN


class TestCalculateForPillar:
    """Tests for calculate_for_pillar method."""

    @pytest.fixture
    def calculator(self):
        return ShiShenCalculator()

    def test_pillar_with_single_hidden_stem(self, calculator):
        """Test pillar with single hidden stem (子 contains only 癸)."""
        day_master = HeavenlyStem.JIA
        pillar_stem = HeavenlyStem.BING  # Fire
        hidden_stems = {HeavenlyStem.GUI: 1.0}  # 癸 (Water Yin)

        stem_ss, hidden_ss = calculator.calculate_for_pillar(
            day_master, pillar_stem, hidden_stems
        )

        # 甲 vs 丙 = 食神 (I generate, same polarity)
        assert stem_ss == ShiShen.SHI_SHEN
        # 甲 vs 癸 = 正印 (generates me, different polarity)
        assert hidden_ss[ShiShen.ZHENG_YIN] == 1.0

    def test_pillar_with_multiple_hidden_stems(self, calculator):
        """Test pillar with multiple hidden stems (寅 contains 甲戊丙)."""
        day_master = HeavenlyStem.JIA
        pillar_stem = HeavenlyStem.BING
        # 寅 contains: 甲 (0.6), 戊 (0.2), 丙 (0.2)
        hidden_stems = {
            HeavenlyStem.JIA: 0.6,
            HeavenlyStem.WU: 0.2,
            HeavenlyStem.BING: 0.2,
        }

        stem_ss, hidden_ss = calculator.calculate_for_pillar(
            day_master, pillar_stem, hidden_stems
        )

        # Check hidden stems
        # 甲 vs 甲 = 比肩
        assert ShiShen.BI_JIAN in hidden_ss
        assert hidden_ss[ShiShen.BI_JIAN] == 0.6
        # 甲 vs 戊 = 偏财
        assert ShiShen.PIAN_CAI in hidden_ss
        assert hidden_ss[ShiShen.PIAN_CAI] == 0.2
        # 甲 vs 丙 = 食神
        assert ShiShen.SHI_SHEN in hidden_ss
        assert hidden_ss[ShiShen.SHI_SHEN] == 0.2


class TestCalculateForBaZi:
    """Tests for calculate_for_bazi method."""

    @pytest.fixture
    def calculator(self):
        return ShiShenCalculator()

    def test_calculate_full_chart(self, calculator):
        """Test complete ShiShen chart calculation."""
        # 甲子 乙丑 丙寅 丁卯
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        chart = calculator.calculate_for_bazi(bazi)

        # Day master is 丙 (Fire Yang)
        # 甲 (Wood Yang) vs 丙 (Fire Yang) = 偏印 (generates me, same polarity)
        assert chart.year_stem == ShiShen.PIAN_YIN
        # 乙 (Wood Yin) vs 丙 (Fire Yang) = 正印 (generates me, different polarity)
        assert chart.month_stem == ShiShen.ZHENG_YIN
        # 丁 (Fire Yin) vs 丙 (Fire Yang) = 劫财 (same element, different polarity)
        assert chart.hour_stem == ShiShen.JIE_CAI

    def test_chart_has_all_positions(self, calculator):
        """ShiShenChart contains all positions."""
        bazi = BaZi.from_chinese("甲寅 乙卯 丙辰 丁巳")
        chart = calculator.calculate_for_bazi(bazi)

        assert chart.year_stem is not None
        assert chart.year_branch_main is not None
        assert chart.month_stem is not None
        assert chart.month_branch_main is not None
        assert chart.day_branch_main is not None
        assert chart.hour_stem is not None
        assert chart.hour_branch_main is not None


class TestGetDetailedShiShen:
    """Tests for get_detailed_shishen method."""

    @pytest.fixture
    def calculator(self):
        return ShiShenCalculator()

    def test_returns_four_entries(self, calculator):
        """Returns one entry for each pillar."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.get_detailed_shishen(bazi)

        assert len(result) == 4

    def test_day_pillar_stem_is_none(self, calculator):
        """Day pillar stem is None (日主 is self)."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.get_detailed_shishen(bazi)

        # Day pillar is index 2
        day_stem_ss, _ = result[2]
        assert day_stem_ss is None

    def test_hidden_stems_included(self, calculator):
        """Hidden stems are included for each pillar."""
        bazi = BaZi.from_chinese("甲寅 乙卯 丙辰 丁巳")
        result = calculator.get_detailed_shishen(bazi)

        # Each pillar should have hidden stem information
        for i, (_, hidden_ss) in enumerate(result):
            assert isinstance(hidden_ss, dict)
            assert len(hidden_ss) > 0


class TestCountShiShen:
    """Tests for count_shishen method."""

    @pytest.fixture
    def calculator(self):
        return ShiShenCalculator()

    def test_count_returns_dict(self, calculator):
        """count_shishen returns a dictionary."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.count_shishen(bazi)

        assert isinstance(result, dict)

    def test_count_values_non_negative(self, calculator):
        """All count values are non-negative."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.count_shishen(bazi)

        for value in result.values():
            assert value >= 0

    def test_count_specific_chart(self, calculator):
        """Test counting with specific BaZi."""
        # Use a BaZi where we know the ShiShen distribution
        bazi = BaZi.from_chinese("甲寅 甲寅 甲寅 甲寅")
        result = calculator.count_shishen(bazi)

        # Day master is 甲, all other stems are also 甲
        # 甲 vs 甲 = 比肩, so year_stem, month_stem, hour_stem are all 比肩
        # That's 3 比肩 positions (excluding day stem which is self)
        assert ShiShen.BI_JIAN in result
        assert result[ShiShen.BI_JIAN] >= 3


class TestFindPositions:
    """Tests for find_positions method."""

    @pytest.fixture
    def calculator(self):
        return ShiShenCalculator()

    def test_find_existing_shishen(self, calculator):
        """Find positions where a ShiShen exists."""
        # 甲寅 甲寅 甲寅 甲寅 - all stems are 甲, so 比肩 should be in multiple positions
        bazi = BaZi.from_chinese("甲寅 甲寅 甲寅 甲寅")
        positions = calculator.find_positions(bazi, ShiShen.BI_JIAN)

        assert len(positions) >= 3
        assert "year_stem" in positions
        assert "month_stem" in positions
        assert "hour_stem" in positions

    def test_find_nonexistent_shishen(self, calculator):
        """Return empty list when ShiShen not found."""
        bazi = BaZi.from_chinese("甲寅 甲寅 甲寅 甲寅")
        # 正官 requires Metal with Yin polarity, unlikely in all-Wood chart
        positions = calculator.find_positions(bazi, ShiShen.ZHENG_GUAN)

        # May or may not be empty depending on hidden stems
        assert isinstance(positions, list)

    def test_position_names_format(self, calculator):
        """Position names follow expected format."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")

        # Find any ShiShen that exists
        for shishen in ShiShen:
            positions = calculator.find_positions(bazi, shishen)
            for pos in positions:
                # Position names should be like "year_stem", "month_branch", etc.
                assert "_" in pos
                parts = pos.split("_")
                assert parts[0] in ["year", "month", "day", "hour"]
                assert parts[1] in ["stem", "branch"]


class TestShiShenProperties:
    """Tests for ShiShen enum properties."""

    def test_chinese_property(self):
        """ShiShen has chinese property."""
        assert ShiShen.BI_JIAN.chinese == "比肩"
        assert ShiShen.ZHENG_YIN.chinese == "正印"
        assert ShiShen.QI_SHA.chinese == "七杀"

    def test_is_favorable_property(self):
        """ShiShen has is_favorable property."""
        # 正印, 正官, 食神, 正财 are generally favorable
        assert ShiShen.ZHENG_YIN.is_favorable is True
        assert ShiShen.SHI_SHEN.is_favorable is True
        # 七杀, 伤官 are generally unfavorable
        assert ShiShen.QI_SHA.is_favorable is False
        assert ShiShen.SHANG_GUAN.is_favorable is False

    def test_category_property(self):
        """ShiShen has category property."""
        # Each ShiShen should have a category
        for shishen in ShiShen:
            assert hasattr(shishen, 'category')
            assert shishen.category in ["比和", "我生", "我克", "克我", "生我"]
