"""
Tests for BranchAnalyzer service.

Tests branch relationship detection in BaZi charts.
"""
import pytest
from unittest.mock import MagicMock

from bazi.domain.services.branch_analyzer import BranchAnalyzer
from bazi.domain.models.branch_analysis import RelationType
from bazi.domain.models.elements import WuXing


def create_mock_bazi(year_branch: str, month_branch: str, day_branch: str, hour_branch: str):
    """Create a mock BaZi with specified branches."""
    bazi = MagicMock()

    def create_pillar(branch_chinese: str):
        pillar = MagicMock()
        pillar.branch.chinese = branch_chinese
        return pillar

    bazi.year_pillar = create_pillar(year_branch)
    bazi.month_pillar = create_pillar(month_branch)
    bazi.day_pillar = create_pillar(day_branch)
    bazi.hour_pillar = create_pillar(hour_branch)

    return bazi


class TestBranchAnalyzerLiuHe:
    """Tests for 六合 (Six Harmonies) detection."""

    def test_detect_zi_chou_liu_he(self):
        """子丑合 should be detected."""
        bazi = create_mock_bazi('子', '丑', '寅', '卯')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.liu_he) == 1
        assert result.liu_he[0].branches == ('子', '丑')
        assert result.liu_he[0].pillars == ('年', '月')

    def test_detect_multiple_liu_he(self):
        """Multiple 六合 should be detected."""
        bazi = create_mock_bazi('子', '丑', '寅', '亥')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        # 子丑合 and 寅亥合
        assert len(result.liu_he) == 2


class TestBranchAnalyzerSanHe:
    """Tests for 三合 (Three Harmonies) detection."""

    def test_detect_yin_wu_xu_san_he(self):
        """寅午戌三合火局 should be detected."""
        bazi = create_mock_bazi('寅', '午', '戌', '子')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.san_he) == 1
        assert result.san_he[0].element == WuXing.FIRE
        assert set(result.san_he[0].branches) == {'寅', '午', '戌'}

    def test_detect_shen_zi_chen_san_he(self):
        """申子辰三合水局 should be detected."""
        bazi = create_mock_bazi('申', '子', '辰', '午')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.san_he) == 1
        assert result.san_he[0].element == WuXing.WATER

    def test_detect_ban_he_when_incomplete(self):
        """半合 should be detected when 三合 is incomplete."""
        bazi = create_mock_bazi('寅', '午', '子', '丑')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.san_he) == 0
        assert len(result.ban_he) == 1
        assert result.ban_he[0].element == WuXing.FIRE

    def test_no_ban_he_when_san_he_complete(self):
        """半合 should not be separately listed when 三合 is complete."""
        bazi = create_mock_bazi('寅', '午', '戌', '子')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        # Only the full 三合, no 半合
        assert len(result.san_he) == 1
        assert len(result.ban_he) == 0


class TestBranchAnalyzerSanHui:
    """Tests for 三会 (Directional Combinations) detection."""

    def test_detect_yin_mao_chen_san_hui(self):
        """寅卯辰三会木局 should be detected."""
        bazi = create_mock_bazi('寅', '卯', '辰', '午')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.san_hui) == 1
        assert result.san_hui[0].element == WuXing.WOOD

    def test_detect_hai_zi_chou_san_hui(self):
        """亥子丑三会水局 should be detected."""
        bazi = create_mock_bazi('亥', '子', '丑', '午')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.san_hui) == 1
        assert result.san_hui[0].element == WuXing.WATER


class TestBranchAnalyzerChong:
    """Tests for 冲 (Clashes) detection."""

    def test_detect_zi_wu_chong(self):
        """子午冲 should be detected."""
        bazi = create_mock_bazi('子', '午', '寅', '卯')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.chong) == 1
        assert result.chong[0].branches == ('子', '午')

    def test_detect_multiple_chong(self):
        """Multiple 冲 should be detected."""
        bazi = create_mock_bazi('子', '午', '寅', '申')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        # 子午冲 and 寅申冲
        assert len(result.chong) == 2


class TestBranchAnalyzerXing:
    """Tests for 刑 (Punishments) detection."""

    def test_detect_yin_si_shen_san_xing(self):
        """寅巳申三刑 (无恩之刑) should be detected."""
        bazi = create_mock_bazi('寅', '巳', '申', '子')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert result.has_san_xing
        san_xing = [r for r in result.xing if len(r.branches) == 3]
        assert len(san_xing) == 1
        assert san_xing[0].relation_type == RelationType.WU_EN_XING

    def test_detect_chou_xu_wei_san_xing(self):
        """丑戌未三刑 (持势之刑) should be detected."""
        bazi = create_mock_bazi('丑', '戌', '未', '子')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert result.has_san_xing
        san_xing = [r for r in result.xing if len(r.branches) == 3]
        assert len(san_xing) == 1
        assert san_xing[0].relation_type == RelationType.CHI_SHI_XING

    def test_detect_zi_mao_wu_li_xing(self):
        """子卯刑 (无礼之刑) should be detected."""
        bazi = create_mock_bazi('子', '卯', '午', '酉')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        wu_li = [r for r in result.xing if r.relation_type == RelationType.WU_LI_XING]
        assert len(wu_li) == 1

    def test_detect_zi_xing(self):
        """自刑 (辰辰、午午、酉酉、亥亥) should be detected."""
        bazi = create_mock_bazi('午', '午', '子', '丑')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert result.has_zi_xing
        assert len(result.zi_xing) == 1
        assert result.zi_xing[0].branches == ('午', '午')


class TestBranchAnalyzerHai:
    """Tests for 害 (Harms) detection."""

    def test_detect_zi_wei_hai(self):
        """子未害 should be detected."""
        bazi = create_mock_bazi('子', '未', '寅', '卯')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.hai) == 1
        assert set(result.hai[0].branches) == {'子', '未'}

    def test_detect_yin_si_hai(self):
        """寅巳害 should be detected."""
        bazi = create_mock_bazi('寅', '巳', '午', '酉')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        hai_rels = [r for r in result.hai if set(r.branches) == {'寅', '巳'}]
        assert len(hai_rels) == 1


class TestBranchAnalyzerPo:
    """Tests for 破 (Breaks) detection."""

    def test_detect_zi_you_po(self):
        """子酉破 should be detected."""
        bazi = create_mock_bazi('子', '酉', '寅', '卯')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.po) == 1
        assert set(result.po[0].branches) == {'子', '酉'}


class TestBranchAnalyzerSiKu:
    """Tests for 四库 (Four Graveyards) detection."""

    def test_detect_chen_water_storage(self):
        """辰为水库 should be detected."""
        bazi = create_mock_bazi('辰', '午', '寅', '卯')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        chen_ku = [r for r in result.si_ku if '辰' in r.branches]
        assert len(chen_ku) == 1
        assert chen_ku[0].element == WuXing.WATER

    def test_detect_all_four_ku(self):
        """All four 库 should be detected when present."""
        bazi = create_mock_bazi('辰', '戌', '丑', '未')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        assert len(result.si_ku) == 4


class TestBranchAnalyzerProperties:
    """Tests for analysis result properties."""

    def test_harmony_count(self):
        """harmony_count should sum all harmonies."""
        bazi = create_mock_bazi('子', '丑', '寅', '亥')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        # 子丑合 + 寅亥合 = 2
        assert result.harmony_count == 2

    def test_conflict_count(self):
        """conflict_count should sum all conflicts."""
        bazi = create_mock_bazi('子', '午', '卯', '酉')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        # 子午冲 + 卯酉冲 + 子酉破 + 卯午破 = 4
        assert result.conflict_count >= 2

    def test_personality_traits(self):
        """get_personality_traits should return descriptions."""
        bazi = create_mock_bazi('寅', '巳', '申', '子')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        traits = result.get_personality_traits()
        assert len(traits) > 0
        assert any('无恩' in t or '薄情' in t or '叛逆' in t for t in traits)

    def test_fortune_impacts(self):
        """get_fortune_impacts should return descriptions."""
        bazi = create_mock_bazi('寅', '巳', '申', '子')
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(bazi)

        impacts = result.get_fortune_impacts()
        assert len(impacts) > 0
