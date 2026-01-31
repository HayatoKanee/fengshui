"""
Tests for DayMasterAnalyzer domain service.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.elements import WuXing
from bazi.domain.models.bazi import BaZi
from bazi.domain.models.analysis import DayMasterStrength, FavorableElements
from bazi.domain.services.day_master_analyzer import DayMasterAnalyzer, calculate_shenghao
from bazi.domain.services.wuxing_calculator import WuXingCalculator


class TestCalculateShenghao:
    """Tests for calculate_shenghao method."""

    @pytest.fixture
    def analyzer(self):
        return DayMasterAnalyzer()

    def test_wood_day_master(self, analyzer):
        """Test shenghao for Wood day master."""
        # Wood: beneficial = Water, Wood; harmful = Fire, Earth, Metal
        wuxing_values = {
            WuXing.WOOD: 20.0,
            WuXing.FIRE: 15.0,
            WuXing.EARTH: 10.0,
            WuXing.METAL: 5.0,
            WuXing.WATER: 10.0,
        }

        beneficial, harmful = calculate_shenghao(
            wuxing_values, WuXing.WOOD
        )

        # Wood beneficial: Water (10) + Wood (20) = 30
        assert beneficial == 30.0
        # Wood harmful: Fire (15) + Earth (10) + Metal (5) = 30
        assert harmful == 30.0

    def test_fire_day_master(self, analyzer):
        """Test shenghao for Fire day master."""
        # Fire: beneficial = Wood, Fire; harmful = Earth, Metal, Water
        wuxing_values = {
            WuXing.WOOD: 10.0,
            WuXing.FIRE: 20.0,
            WuXing.EARTH: 15.0,
            WuXing.METAL: 5.0,
            WuXing.WATER: 10.0,
        }

        beneficial, harmful = calculate_shenghao(
            wuxing_values, WuXing.FIRE
        )

        # Fire beneficial: Wood (10) + Fire (20) = 30
        assert beneficial == 30.0
        # Fire harmful: Earth (15) + Metal (5) + Water (10) = 30
        assert harmful == 30.0

    def test_empty_wuxing_values(self, analyzer):
        """Test with empty/zero wuxing values."""
        wuxing_values = {element: 0.0 for element in WuXing}

        beneficial, harmful = calculate_shenghao(
            wuxing_values, WuXing.WOOD
        )

        assert beneficial == 0.0
        assert harmful == 0.0

    def test_missing_elements(self, analyzer):
        """Test with some elements missing from dict."""
        # Only Wood and Fire present
        wuxing_values = {
            WuXing.WOOD: 20.0,
            WuXing.FIRE: 15.0,
        }

        beneficial, harmful = calculate_shenghao(
            wuxing_values, WuXing.WOOD
        )

        # Water is missing but beneficial - treated as 0
        assert beneficial == 20.0  # Only Wood
        assert harmful == 15.0  # Only Fire


class TestAnalyzeStrength:
    """Tests for analyze_strength method."""

    @pytest.fixture
    def analyzer(self):
        return DayMasterAnalyzer()

    def test_returns_day_master_strength(self, analyzer):
        """analyze_strength returns DayMasterStrength dataclass."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = analyzer.analyze_strength(bazi)

        assert isinstance(result, DayMasterStrength)
        assert hasattr(result, 'beneficial_value')
        assert hasattr(result, 'harmful_value')

    def test_strength_values_non_negative(self, analyzer):
        """Beneficial and harmful values are non-negative."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = analyzer.analyze_strength(bazi)

        assert result.beneficial_value >= 0
        assert result.harmful_value >= 0

    def test_strong_day_master(self, analyzer):
        """Test BaZi with strong day master."""
        # 甲寅 甲寅 甲寅 甲寅 - all Wood, should be very strong for Wood day master
        # But the day master is 甲 which is Wood
        # Wait, this BaZi has all Wood, and day master needs Water and Wood support
        # So this should be strong
        bazi = BaZi.from_chinese("甲寅 甲寅 甲寅 甲寅")
        result = analyzer.analyze_strength(bazi)

        # Should be strong (beneficial >= 50%)
        assert result.is_strong

    def test_earth_dominant_flag(self, analyzer):
        """Test with earth_dominant flag affects analysis."""
        bazi = BaZi.from_chinese("戊辰 戊辰 戊辰 戊辰")

        result_normal = analyzer.analyze_strength(bazi, is_earth_dominant=False)
        result_earth = analyzer.analyze_strength(bazi, is_earth_dominant=True)

        # Results may differ based on earth dominant period
        # Both should return valid DayMasterStrength
        assert isinstance(result_normal, DayMasterStrength)
        assert isinstance(result_earth, DayMasterStrength)


class TestDayMasterStrengthModel:
    """Tests for DayMasterStrength model properties."""

    def test_total_calculation(self):
        """total is sum of beneficial and harmful."""
        strength = DayMasterStrength(
            beneficial_value=60.0,
            harmful_value=40.0,
        )
        assert strength.total == 100.0

    def test_beneficial_percentage(self):
        """beneficial_percentage is correct percentage."""
        strength = DayMasterStrength(
            beneficial_value=60.0,
            harmful_value=40.0,
        )
        assert strength.beneficial_percentage == 60.0

    def test_harmful_percentage(self):
        """harmful_percentage complements beneficial."""
        strength = DayMasterStrength(
            beneficial_value=60.0,
            harmful_value=40.0,
        )
        assert strength.harmful_percentage == 40.0

    def test_zero_total_returns_50_percent(self):
        """When total is 0, return 50% beneficial."""
        strength = DayMasterStrength(
            beneficial_value=0.0,
            harmful_value=0.0,
        )
        assert strength.beneficial_percentage == 50.0

    def test_is_strong_at_50_percent(self):
        """is_strong is True at exactly 50%."""
        strength = DayMasterStrength(
            beneficial_value=50.0,
            harmful_value=50.0,
        )
        assert strength.is_strong is True

    def test_is_strong_above_50_percent(self):
        """is_strong is True above 50%."""
        strength = DayMasterStrength(
            beneficial_value=60.0,
            harmful_value=40.0,
        )
        assert strength.is_strong is True

    def test_is_weak_below_50_percent(self):
        """is_strong is False below 50%."""
        strength = DayMasterStrength(
            beneficial_value=40.0,
            harmful_value=60.0,
        )
        assert strength.is_strong is False

    def test_strength_level_strong(self):
        """strength_level returns 身强 for >= 50%."""
        # 75% beneficial
        strength = DayMasterStrength(beneficial_value=75.0, harmful_value=25.0)
        assert strength.strength_level == "身强"

        # 60% beneficial
        strength = DayMasterStrength(beneficial_value=60.0, harmful_value=40.0)
        assert strength.strength_level == "身强"

        # Exactly 50% (threshold)
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)
        assert strength.strength_level == "身强"

    def test_strength_level_weak(self):
        """strength_level returns 身弱 for < 50%."""
        # 35% beneficial
        strength = DayMasterStrength(beneficial_value=35.0, harmful_value=65.0)
        assert strength.strength_level == "身弱"

        # 20% beneficial
        strength = DayMasterStrength(beneficial_value=20.0, harmful_value=80.0)
        assert strength.strength_level == "身弱"


class TestDetermineFavorableElements:
    """Tests for determine_favorable_elements method."""

    @pytest.fixture
    def analyzer(self):
        return DayMasterAnalyzer()

    def test_strong_day_master_elements(self, analyzer):
        """Strong day master needs draining elements."""
        bazi = BaZi.from_chinese("甲寅 甲寅 甲寅 甲寅")  # Wood day master
        strength = DayMasterStrength(
            beneficial_value=70.0,
            harmful_value=30.0,
        )

        favorable = analyzer.determine_favorable_elements(bazi, strength)

        # Strong Wood needs: Fire (generates from Wood = drains)
        assert favorable.yong_shen == WuXing.WOOD.generates  # Fire
        # Strong Wood avoids: Water (generates Wood = feeds)
        assert favorable.ji_shen == WuXing.WOOD.generated_by  # Water

    def test_weak_day_master_elements(self, analyzer):
        """Weak day master needs supporting elements."""
        bazi = BaZi.from_chinese("甲子 甲子 甲子 甲子")  # Wood day master
        strength = DayMasterStrength(
            beneficial_value=30.0,
            harmful_value=70.0,
        )

        favorable = analyzer.determine_favorable_elements(bazi, strength)

        # Weak Wood needs: Water (generates Wood = feeds)
        assert favorable.yong_shen == WuXing.WOOD.generated_by  # Water
        # Weak Wood avoids: Fire (Wood generates Fire = drains)
        assert favorable.ji_shen == WuXing.WOOD.generates  # Fire

    def test_returns_favorable_elements_dataclass(self, analyzer):
        """determine_favorable_elements returns FavorableElements."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        strength = DayMasterStrength(
            beneficial_value=50.0,
            harmful_value=50.0,
        )

        result = analyzer.determine_favorable_elements(bazi, strength)

        assert isinstance(result, FavorableElements)
        assert hasattr(result, 'yong_shen')
        assert hasattr(result, 'xi_shen')
        assert hasattr(result, 'ji_shen')


class TestFavorableElementsModel:
    """Tests for FavorableElements model properties."""

    def test_favorable_list(self):
        """favorable property returns list of good elements."""
        fe = FavorableElements(
            yong_shen=WuXing.WATER,
            xi_shen=WuXing.WOOD,
            ji_shen=WuXing.FIRE,
            chou_shen=WuXing.EARTH,
        )

        assert WuXing.WATER in fe.favorable
        assert WuXing.WOOD in fe.favorable
        assert len(fe.favorable) == 2

    def test_favorable_without_xi_shen(self):
        """favorable works when xi_shen is None."""
        fe = FavorableElements(
            yong_shen=WuXing.WATER,
            xi_shen=None,
            ji_shen=WuXing.FIRE,
        )

        assert fe.favorable == [WuXing.WATER]

    def test_unfavorable_list(self):
        """unfavorable property returns list of bad elements."""
        fe = FavorableElements(
            yong_shen=WuXing.WATER,
            xi_shen=WuXing.WOOD,
            ji_shen=WuXing.FIRE,
            chou_shen=WuXing.EARTH,
        )

        assert WuXing.FIRE in fe.unfavorable
        assert WuXing.EARTH in fe.unfavorable
        assert len(fe.unfavorable) == 2

    def test_unfavorable_without_chou_shen(self):
        """unfavorable works when chou_shen is None."""
        fe = FavorableElements(
            yong_shen=WuXing.WATER,
            xi_shen=WuXing.WOOD,
            ji_shen=WuXing.FIRE,
            chou_shen=None,
        )

        assert fe.unfavorable == [WuXing.FIRE]


class TestFullAnalysis:
    """Tests for full_analysis method."""

    @pytest.fixture
    def analyzer(self):
        return DayMasterAnalyzer()

    def test_returns_tuple_of_three(self, analyzer):
        """full_analysis returns three-element tuple."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = analyzer.full_analysis(bazi)

        assert len(result) == 3

    def test_returns_correct_types(self, analyzer):
        """full_analysis returns correct types."""
        from bazi.domain.models.analysis import WuXingStrength

        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        dm_strength, favorable, wuxing_strength = analyzer.full_analysis(bazi)

        assert isinstance(dm_strength, DayMasterStrength)
        assert isinstance(favorable, FavorableElements)
        assert isinstance(wuxing_strength, WuXingStrength)

    def test_full_analysis_integration(self, analyzer):
        """Test that full_analysis components are internally consistent."""
        bazi = BaZi.from_chinese("甲寅 乙卯 丙辰 丁巳")
        dm_strength, favorable, wuxing_strength = analyzer.full_analysis(bazi)

        # Day master's element should match bazi
        dm_element = bazi.day_master_wuxing

        # Check that favorable elements relate to day master
        if dm_strength.is_strong:
            # Yong shen should drain the day master
            assert favorable.yong_shen == dm_element.generates
        else:
            # Yong shen should feed the day master
            assert favorable.yong_shen == dm_element.generated_by


class TestCustomWuXingCalculator:
    """Tests for dependency injection of WuXingCalculator."""

    def test_default_calculator(self):
        """Analyzer creates default WuXingCalculator."""
        analyzer = DayMasterAnalyzer()
        assert analyzer._wuxing_calc is not None
        assert isinstance(analyzer._wuxing_calc, WuXingCalculator)

    def test_injected_calculator(self):
        """Analyzer accepts custom WuXingCalculator."""
        custom_calc = WuXingCalculator()
        analyzer = DayMasterAnalyzer(wuxing_calculator=custom_calc)

        assert analyzer._wuxing_calc is custom_calc
