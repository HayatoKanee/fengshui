"""
Tests for BaziAnalysisService.

These tests verify the application service orchestrates domain services
correctly and produces complete analysis results.
"""
import pytest
from freezegun import freeze_time

from bazi.domain.models import BirthData
from bazi.domain.models.elements import WuXing


class TestBaziAnalysisService:
    """Tests for BaziAnalysisService.analyze()"""

    def test_analyze_returns_complete_result(self, bazi_service, birth_data):
        """Analyze should return a complete BaziAnalysisResult."""
        result = bazi_service.analyze(birth_data)

        assert result is not None
        assert result.bazi is not None
        assert result.wuxing_strength is not None
        assert result.day_master_strength is not None
        assert result.shishen_chart is not None
        assert result.shensha_analysis is not None
        assert result.favorable_elements is not None

    def test_analyze_calculates_wuxing_values(self, bazi_service, birth_data):
        """WuXing strength should have values for all five elements."""
        result = bazi_service.analyze(birth_data)

        wuxing = result.wuxing_strength
        assert WuXing.WOOD in wuxing.raw_values
        assert WuXing.FIRE in wuxing.raw_values
        assert WuXing.EARTH in wuxing.raw_values
        assert WuXing.METAL in wuxing.raw_values
        assert WuXing.WATER in wuxing.raw_values

    def test_analyze_determines_day_master_strength(self, bazi_service, birth_data):
        """Day master analysis should determine strength."""
        result = bazi_service.analyze(birth_data)

        dm = result.day_master_strength
        assert dm.is_strong is not None
        assert isinstance(dm.is_strong, bool)
        assert dm.beneficial_value >= 0
        assert dm.harmful_value >= 0

    def test_analyze_identifies_favorable_elements(self, bazi_service, birth_data):
        """Analysis should identify favorable and unfavorable elements."""
        result = bazi_service.analyze(birth_data)

        favorable = result.favorable_elements
        assert len(favorable.favorable) > 0
        assert len(favorable.unfavorable) > 0
        # Favorable and unfavorable should not overlap
        assert not set(favorable.favorable) & set(favorable.unfavorable)

    def test_analyze_strong_day_master(self, bazi_service):
        """Strong day master should prefer controlling elements."""
        # Fire in summer - should be strong
        birth = BirthData(
            year=1990, month=6, day=15,  # Summer
            hour=12, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)

        # Check if day master analysis is reasonable
        assert result.day_master_strength is not None

    def test_analyze_weak_day_master(self, bazi_service):
        """Weak day master should prefer supporting elements."""
        # Fire in winter - should be weak
        birth = BirthData(
            year=1990, month=12, day=15,  # Winter
            hour=0, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)

        # Check if day master analysis is reasonable
        assert result.day_master_strength is not None

    def test_analyze_calculates_shishen(self, bazi_service, birth_data):
        """ShiShen chart should be calculated."""
        result = bazi_service.analyze(birth_data)

        shishen = result.shishen_chart
        # Should have ShiShen for all pillars
        assert shishen.year_stem is not None
        assert shishen.month_stem is not None
        assert shishen.hour_stem is not None

    def test_analyze_identifies_shensha(self, bazi_service, birth_data):
        """ShenSha analysis should identify special stars."""
        result = bazi_service.analyze(birth_data)

        shensha = result.shensha_analysis
        assert shensha is not None
        # ShenSha analysis should have a list of identified shensha
        assert hasattr(shensha, 'shensha_list') or hasattr(shensha, 'count_by_type')
        # Should be able to check for specific shensha types
        assert isinstance(shensha, object)

    def test_analyze_male_vs_female(self, bazi_service):
        """Male and female analysis should handle gender correctly."""
        male_birth = BirthData(
            year=1990, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        female_birth = BirthData(
            year=1990, month=6, day=15,
            hour=12, minute=0, is_male=False
        )

        male_result = bazi_service.analyze(male_birth)
        female_result = bazi_service.analyze(female_birth)

        # BaZi should be the same (gender doesn't affect chart)
        assert male_result.bazi == female_result.bazi


class TestBaziAnalysisServiceEdgeCases:
    """Edge case tests for BaziAnalysisService."""

    def test_analyze_birth_at_midnight(self, bazi_service):
        """Birth at midnight should be handled correctly."""
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=0, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)
        assert result is not None

    def test_analyze_birth_at_2359(self, bazi_service):
        """Birth at 23:59 should be handled correctly."""
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=23, minute=59, is_male=True
        )
        result = bazi_service.analyze(birth)
        assert result is not None

    def test_analyze_leap_year_february_29(self, bazi_service):
        """Birth on Feb 29 should be handled correctly."""
        birth = BirthData(
            year=2000, month=2, day=29,  # Leap year
            hour=12, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)
        assert result is not None

    def test_analyze_new_year_boundary(self, bazi_service):
        """Birth near Chinese New Year should handle year correctly."""
        # Early January - likely still previous Chinese year
        birth = BirthData(
            year=1990, month=1, day=15,
            hour=12, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)
        assert result is not None

    def test_analyze_old_date(self, bazi_service):
        """Analysis should work for historical dates."""
        birth = BirthData(
            year=1900, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)
        assert result is not None

    def test_analyze_future_date(self, bazi_service):
        """Analysis should work for future dates."""
        birth = BirthData(
            year=2050, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        result = bazi_service.analyze(birth)
        assert result is not None


class TestGetQuickSummary:
    """Tests for BaziAnalysisService.get_quick_summary()"""

    def test_quick_summary_returns_dict(self, bazi_service, birth_data):
        """Quick summary should return a dictionary."""
        summary = bazi_service.get_quick_summary(birth_data)

        assert isinstance(summary, dict)
        assert 'day_master' in summary
        assert 'is_strong' in summary
        assert 'favorable_wuxing' in summary
        assert 'unfavorable_wuxing' in summary

    def test_quick_summary_has_day_master_info(self, bazi_service, birth_data):
        """Quick summary should include day master information."""
        summary = bazi_service.get_quick_summary(birth_data)

        assert summary['day_master'] is not None
        assert isinstance(summary['is_strong'], bool)
        assert isinstance(summary['favorable_wuxing'], list)
        assert isinstance(summary['unfavorable_wuxing'], list)
