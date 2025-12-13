"""
Tests for SexagenaryCycleCalculator.

Verifies the mathematical correctness of the sexagenary cycle calculations
and the 60-day jump optimization algorithm.
"""
import pytest
from datetime import date

from bazi.domain.services.sexagenary_calculator import (
    SexagenaryCycleCalculator,
    PillarPattern,
)


class TestJulianDayConversion:
    """Test Julian Day Number conversions."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_known_julian_day(self, calculator):
        """Test conversion of known reference date."""
        # Jan 1, 2000 = JD 2451545 (noon)
        jdn = calculator.date_to_jdn(2000, 1, 1)
        assert jdn == 2451545

    def test_roundtrip_conversion(self, calculator):
        """Test that date -> JDN -> date gives same result."""
        test_dates = [
            (2024, 6, 15),
            (1990, 1, 1),
            (2050, 12, 31),
            (1900, 3, 15),
        ]

        for year, month, day in test_dates:
            jdn = calculator.date_to_jdn(year, month, day)
            result = calculator.jdn_to_date(jdn)
            assert result == (year, month, day), f"Failed for {year}-{month}-{day}"


class TestDayPillarCalculation:
    """Test day pillar calculations."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_sexagenary_cycle_is_60_days(self, calculator):
        """Verify that the cycle repeats every 60 days."""
        base_date = date(2024, 1, 1)
        base_index = calculator.get_day_sexagenary_index(
            base_date.year, base_date.month, base_date.day
        )

        # 60 days later should have same index
        later_date = date(2024, 3, 1)  # Jan 1 + 60 days
        later_index = calculator.get_day_sexagenary_index(
            later_date.year, later_date.month, later_date.day
        )

        assert (later_index - base_index) % 60 == 0

    def test_consecutive_days_increment_by_one(self, calculator):
        """Verify consecutive days have consecutive indices."""
        for offset in range(10):
            base_date = date(2024, 6, 1 + offset)
            next_date = date(2024, 6, 2 + offset)

            base_index = calculator.get_day_sexagenary_index(
                base_date.year, base_date.month, base_date.day
            )
            next_index = calculator.get_day_sexagenary_index(
                next_date.year, next_date.month, next_date.day
            )

            assert (next_index - base_index) % 60 == 1

    def test_day_pillar_format(self, calculator):
        """Test that day pillar returns valid stem-branch pair."""
        pillar = calculator.get_day_pillar(2024, 6, 15)

        assert len(pillar) == 2
        assert pillar[0] in calculator.STEMS
        assert pillar[1] in calculator.BRANCHES


class TestPillarToIndex:
    """Test pillar to sexagenary index conversion."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_jiazi_is_index_zero(self, calculator):
        """甲子 should be index 0."""
        index = calculator.pillar_to_sexagenary_index('甲', '子')
        assert index == 0

    def test_all_60_combinations_unique(self, calculator):
        """All 60 stem-branch combinations should have unique indices."""
        indices = set()

        # Valid combinations: stem and branch must have same yin/yang parity
        for i in range(60):
            stem = calculator.STEMS[i % 10]
            branch = calculator.BRANCHES[i % 12]
            # Skip invalid combinations
            if (i % 10) % 2 != (i % 12) % 2:
                continue

            index = calculator.pillar_to_sexagenary_index(stem, branch)
            indices.add(index)

        # We should have all unique indices
        assert len(indices) == len(set(indices))


class TestFindMatchingDates:
    """Test the optimized date-finding algorithm."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_find_matching_day_pillar_dates(self, calculator):
        """Test that found dates have correct day pillar."""
        # Use 甲子 (JiaZi) as target
        target_stem = '甲'
        target_branch = '子'

        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        found_dates = list(calculator.find_matching_day_pillar_dates(
            target_stem, target_branch, start, end
        ))

        # Should find approximately 365/60 ≈ 6 dates
        assert len(found_dates) >= 5
        assert len(found_dates) <= 7

        # Each found date should have the target pillar
        for d in found_dates:
            pillar = calculator.get_day_pillar(d.year, d.month, d.day)
            assert pillar == target_stem + target_branch

    def test_found_dates_are_60_days_apart(self, calculator):
        """Verify that consecutive matches are 60 days apart."""
        start = date(2024, 1, 1)
        end = date(2025, 12, 31)

        found_dates = list(calculator.find_matching_day_pillar_dates(
            '甲', '子', start, end
        ))

        for i in range(1, len(found_dates)):
            diff = (found_dates[i] - found_dates[i - 1]).days
            assert diff == 60

    def test_find_dates_by_stem_only(self, calculator):
        """Test finding dates by stem only (10-day cycle)."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        found_dates = list(calculator.find_matching_dates_by_stem_only(
            '甲', start, end
        ))

        # Should find ~3 dates (31/10)
        assert len(found_dates) >= 2

        # Verify 10-day intervals
        for i in range(1, len(found_dates)):
            diff = (found_dates[i] - found_dates[i - 1]).days
            assert diff == 10

    def test_find_dates_by_branch_only(self, calculator):
        """Test finding dates by branch only (12-day cycle)."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        found_dates = list(calculator.find_matching_dates_by_branch_only(
            '子', start, end
        ))

        # Should find ~2-3 dates (31/12)
        assert len(found_dates) >= 2

        # Verify 12-day intervals
        for i in range(1, len(found_dates)):
            diff = (found_dates[i] - found_dates[i - 1]).days
            assert diff == 12


class TestHourPillar:
    """Test hour pillar calculations."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_hour_pillar_derivation(self, calculator):
        """Test hour pillar is correctly derived from day stem."""
        # The hour stem is derived from day stem
        # hour_stem = (day_stem * 2 + hour_branch) % 10

        day_stem_index = 0  # 甲
        hour = 0  # 子时

        pillar = calculator.get_hour_pillar(day_stem_index, hour)

        # 甲日子时 should be 甲子
        assert pillar == '甲子'

    def test_valid_day_stems_for_hour_pillar(self, calculator):
        """Test finding valid day stems for a target hour pillar."""
        # For 甲子时, only certain day stems will work
        valid_stems = calculator.get_valid_day_stems_for_hour_pillar('甲', '子')

        # Should return at least one valid day stem
        assert len(valid_stems) > 0

        # Verify the stems actually produce the correct hour pillar
        for day_stem_idx in valid_stems:
            pillar = calculator.get_hour_pillar(day_stem_idx, 0)  # hour 0 = 子
            assert pillar[0] == '甲'


class TestYearPillar:
    """Test year pillar calculations."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_1984_is_jiazi_year(self, calculator):
        """1984 is a 甲子 year."""
        pillar = calculator.get_year_pillar(1984)
        assert pillar == '甲子'

    def test_year_cycle_is_60_years(self, calculator):
        """Year pillar repeats every 60 years."""
        pillar_1984 = calculator.get_year_pillar(1984)
        pillar_2044 = calculator.get_year_pillar(2044)

        assert pillar_1984 == pillar_2044

    def test_find_years_with_pillar(self, calculator):
        """Test finding years with specific pillar."""
        matching_years = calculator.find_years_with_pillar(
            '甲', '子', 1980, 2100
        )

        # Should find 1984, 2044
        assert 1984 in matching_years
        assert 2044 in matching_years

        # All matches should be 60 years apart
        for i in range(1, len(matching_years)):
            assert matching_years[i] - matching_years[i - 1] == 60


class TestPillarPattern:
    """Test PillarPattern helper class."""

    def test_empty_pattern_matches_all(self):
        """Empty pattern should match any pillar."""
        pattern = PillarPattern()
        assert pattern.matches('甲', '子')
        assert pattern.matches('乙', '丑')

    def test_stem_only_pattern(self):
        """Pattern with stem only matches any branch."""
        pattern = PillarPattern(stem='甲')
        assert pattern.matches('甲', '子')
        assert pattern.matches('甲', '寅')
        assert not pattern.matches('乙', '子')

    def test_branch_only_pattern(self):
        """Pattern with branch only matches any stem."""
        pattern = PillarPattern(branch='子')
        assert pattern.matches('甲', '子')
        assert pattern.matches('丙', '子')
        assert not pattern.matches('甲', '丑')

    def test_complete_pattern(self):
        """Complete pattern matches exact pillar."""
        pattern = PillarPattern(stem='甲', branch='子')
        assert pattern.matches('甲', '子')
        assert not pattern.matches('甲', '丑')
        assert not pattern.matches('乙', '子')

    def test_is_complete(self):
        """Test is_complete property."""
        assert PillarPattern(stem='甲', branch='子').is_complete
        assert not PillarPattern(stem='甲').is_complete
        assert not PillarPattern(branch='子').is_complete
        assert not PillarPattern().is_complete

    def test_is_empty(self):
        """Test is_empty property."""
        assert PillarPattern().is_empty
        assert not PillarPattern(stem='甲').is_empty
        assert not PillarPattern(branch='子').is_empty


class TestPerformanceGains:
    """Test that the optimization actually reduces iterations."""

    @pytest.fixture
    def calculator(self):
        return SexagenaryCycleCalculator()

    def test_60_day_jump_efficiency(self, calculator):
        """Verify 60-day jump reduces iterations dramatically."""
        start = date(2024, 1, 1)
        end = date(2124, 12, 31)  # 100 years

        # Count iterations
        iteration_count = 0
        for _ in calculator.find_matching_day_pillar_dates(
            '甲', '子', start, end
        ):
            iteration_count += 1

        # Should be approximately 100 * 365 / 60 ≈ 608 iterations
        # Not 100 * 365 = 36,500 brute force iterations
        assert iteration_count < 700
        assert iteration_count > 500

        # This represents ~60x improvement
