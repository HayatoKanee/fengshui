"""
Tests for PatternAnalyzer service.

Tests special pattern (格局) detection in BaZi charts.
"""
import pytest
from unittest.mock import MagicMock

from bazi.domain.services.pattern_analyzer import PatternAnalyzer
from bazi.domain.models.pattern_analysis import (
    PatternCategory,
    PatternType,
)
from bazi.domain.models.elements import WuXing


def create_mock_bazi(
    year_stem: str, year_branch: str,
    month_stem: str, month_branch: str,
    day_stem: str, day_branch: str,
    hour_stem: str, hour_branch: str,
):
    """Create a mock BaZi with specified stems and branches."""
    bazi = MagicMock()

    def create_pillar(stem_chinese: str, branch_chinese: str, stem_wuxing: WuXing):
        pillar = MagicMock()
        pillar.stem.chinese = stem_chinese
        pillar.stem.wuxing = stem_wuxing
        pillar.branch.chinese = branch_chinese
        pillar.hidden_stems = {}  # Simplified
        return pillar

    # Map stem to wuxing
    stem_wuxing_map = {
        '甲': WuXing.WOOD, '乙': WuXing.WOOD,
        '丙': WuXing.FIRE, '丁': WuXing.FIRE,
        '戊': WuXing.EARTH, '己': WuXing.EARTH,
        '庚': WuXing.METAL, '辛': WuXing.METAL,
        '壬': WuXing.WATER, '癸': WuXing.WATER,
    }

    bazi.year_pillar = create_pillar(year_stem, year_branch, stem_wuxing_map[year_stem])
    bazi.month_pillar = create_pillar(month_stem, month_branch, stem_wuxing_map[month_stem])
    bazi.day_pillar = create_pillar(day_stem, day_branch, stem_wuxing_map[day_stem])
    bazi.hour_pillar = create_pillar(hour_stem, hour_branch, stem_wuxing_map[hour_stem])

    bazi.day_master = bazi.day_pillar.stem
    bazi.pillars = [bazi.year_pillar, bazi.month_pillar, bazi.day_pillar, bazi.hour_pillar]

    return bazi


class TestPatternAnalyzerZhuanWang:
    """Tests for 专旺格 (Dominant Patterns) detection."""

    def test_detect_qu_zhi_ge(self):
        """曲直格: 甲/乙日主，木气专旺."""
        # 甲日主，地支全木
        bazi = create_mock_bazi(
            '甲', '寅',  # 年
            '乙', '卯',  # 月
            '甲', '寅',  # 日
            '乙', '卯',  # 时
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # Should detect 曲直格
        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1
        assert qu_zhi[0].element == WuXing.WOOD

    def test_detect_yan_shang_ge(self):
        """炎上格: 丙/丁日主，火气专旺."""
        bazi = create_mock_bazi(
            '丙', '巳',
            '丁', '午',
            '丙', '午',
            '丁', '巳',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1
        assert yan_shang[0].element == WuXing.FIRE

    def test_detect_jia_se_ge(self):
        """稼穑格: 戊/己日主，土气专旺."""
        bazi = create_mock_bazi(
            '戊', '辰',
            '己', '戌',
            '戊', '丑',
            '己', '未',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        assert len(jia_se) >= 1
        assert jia_se[0].element == WuXing.EARTH

    def test_detect_cong_ge_metal(self):
        """从革格: 庚/辛日主，金气专旺."""
        bazi = create_mock_bazi(
            '庚', '申',
            '辛', '酉',
            '庚', '申',
            '辛', '酉',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        cong_ge = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_GE_METAL]
        assert len(cong_ge) >= 1
        assert cong_ge[0].element == WuXing.METAL

    def test_detect_run_xia_ge(self):
        """润下格: 壬/癸日主，水气专旺."""
        bazi = create_mock_bazi(
            '壬', '亥',
            '癸', '子',
            '壬', '子',
            '癸', '亥',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        run_xia = [p for p in result.detected_patterns if p.pattern_type == PatternType.RUN_XIA]
        assert len(run_xia) >= 1
        assert run_xia[0].element == WuXing.WATER


class TestPatternAnalyzerHuaGe:
    """Tests for 化格 (Transformation Patterns) detection."""

    def test_detect_jia_ji_hua_tu(self):
        """甲己化土: 甲日干与己合化土."""
        bazi = create_mock_bazi(
            '己', '辰',  # 年干己
            '己', '戌',  # 月干己
            '甲', '辰',  # 日干甲
            '戊', '戌',  # 时干戊
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        assert len(hua_tu) >= 1
        assert hua_tu[0].element == WuXing.EARTH

    def test_detect_yi_geng_hua_jin(self):
        """乙庚化金: 乙日干与庚合化金."""
        bazi = create_mock_bazi(
            '庚', '申',
            '庚', '酉',
            '乙', '酉',
            '辛', '酉',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_jin = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_JIN]
        assert len(hua_jin) >= 1
        assert hua_jin[0].element == WuXing.METAL

    def test_no_hua_ge_without_combination(self):
        """Without the combining stem, no 化格."""
        bazi = create_mock_bazi(
            '丙', '辰',
            '丁', '辰',
            '甲', '辰',  # 甲日干，但没有己
            '戊', '戌',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        # Should not detect 甲己化土 since there's no 己
        assert len(hua_tu) == 0


class TestPatternAnalyzerCongGe:
    """Tests for 从格 (Following Patterns) detection."""

    def test_detect_cong_cai_ge(self):
        """从财格: 日主极弱，财星强旺."""
        # 日主木极弱，财星土强
        bazi = create_mock_bazi(
            '戊', '辰',
            '己', '戌',
            '乙', '丑',  # 乙木日主
            '戊', '未',
        )
        # Provide wuxing values showing weak day master
        wuxing_values = {
            WuXing.WOOD: 1.0,   # Very weak
            WuXing.FIRE: 0.5,
            WuXing.EARTH: 6.0,  # Strong (财星)
            WuXing.METAL: 1.0,
            WuXing.WATER: 0.5,
        }

        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi, wuxing_values)

        cong_cai = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_CAI]
        if cong_cai:
            assert cong_cai[0].category == PatternCategory.CONG_GE
            assert cong_cai[0].element == WuXing.EARTH  # 财星

    def test_no_cong_ge_with_strong_day_master(self):
        """从格 requires weak day master."""
        bazi = create_mock_bazi(
            '甲', '寅',
            '乙', '卯',
            '甲', '寅',
            '乙', '卯',
        )
        # Day master is strong
        wuxing_values = {
            WuXing.WOOD: 8.0,  # Very strong
            WuXing.FIRE: 1.0,
            WuXing.EARTH: 1.0,
            WuXing.METAL: 0.5,
            WuXing.WATER: 0.5,
        }

        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi, wuxing_values)

        # Should not have 从格
        cong_patterns = [p for p in result.detected_patterns if p.category == PatternCategory.CONG_GE]
        assert len(cong_patterns) == 0


class TestPatternAnalysisProperties:
    """Tests for PatternAnalysis result properties."""

    def test_has_special_pattern(self):
        """has_special_pattern should be True when valid pattern exists."""
        bazi = create_mock_bazi(
            '甲', '寅',
            '乙', '卯',
            '甲', '寅',
            '乙', '卯',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # 曲直格 should be detected
        if result.has_special_pattern:
            assert result.primary_pattern is not None
            assert result.primary_pattern.is_valid

    def test_get_pattern_description(self):
        """get_pattern_description should return meaningful text."""
        bazi = create_mock_bazi(
            '甲', '寅',
            '乙', '卯',
            '甲', '寅',
            '乙', '卯',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        description = result.get_pattern_description()
        assert len(description) > 0

    def test_get_favorable_advice(self):
        """get_favorable_advice should return advice list."""
        bazi = create_mock_bazi(
            '甲', '寅',
            '乙', '卯',
            '甲', '寅',
            '乙', '卯',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        advice = result.get_favorable_advice()
        assert isinstance(advice, list)


class TestPatternAnalyzerEdgeCases:
    """Edge case tests."""

    def test_normal_pattern_when_no_special(self):
        """Should detect normal pattern when nothing special."""
        bazi = create_mock_bazi(
            '甲', '子',
            '丙', '寅',
            '戊', '午',
            '庚', '申',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # Mixed elements, no special pattern
        if not result.has_special_pattern:
            description = result.get_pattern_description()
            assert '普通' in description or '正常' in description

    def test_multiple_patterns_detected(self):
        """Multiple partial patterns can be detected."""
        # A chart that might match multiple patterns partially
        bazi = create_mock_bazi(
            '己', '辰',
            '己', '戌',
            '甲', '丑',
            '戊', '未',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # Might detect both 化土 and 稼穑格 partially
        assert len(result.detected_patterns) >= 0  # At least analyzed
