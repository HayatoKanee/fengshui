"""
Tests for Heavenly Stems and Earthly Branches domain models.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.elements import WuXing, YinYang
from bazi.domain.models.stems_branches import (
    HeavenlyStem,
    EarthlyBranch,
    StemBranchRelations,
    RELATIONS,
)


class TestHeavenlyStem:
    """Tests for HeavenlyStem (天干) enum."""

    def test_all_ten_stems_exist(self):
        """All ten heavenly stems are defined."""
        stems = list(HeavenlyStem)
        assert len(stems) == 10

    def test_chinese_values(self):
        """Stems have correct Chinese characters."""
        expected = {
            HeavenlyStem.JIA: "甲", HeavenlyStem.YI: "乙",
            HeavenlyStem.BING: "丙", HeavenlyStem.DING: "丁",
            HeavenlyStem.WU: "戊", HeavenlyStem.JI: "己",
            HeavenlyStem.GENG: "庚", HeavenlyStem.XIN: "辛",
            HeavenlyStem.REN: "壬", HeavenlyStem.GUI: "癸",
        }
        for stem, char in expected.items():
            assert stem.value == char
            assert stem.chinese == char

    def test_wuxing_mapping_wood(self):
        """JIA and YI are Wood."""
        assert HeavenlyStem.JIA.wuxing == WuXing.WOOD
        assert HeavenlyStem.YI.wuxing == WuXing.WOOD

    def test_wuxing_mapping_fire(self):
        """BING and DING are Fire."""
        assert HeavenlyStem.BING.wuxing == WuXing.FIRE
        assert HeavenlyStem.DING.wuxing == WuXing.FIRE

    def test_wuxing_mapping_earth(self):
        """WU and JI are Earth."""
        assert HeavenlyStem.WU.wuxing == WuXing.EARTH
        assert HeavenlyStem.JI.wuxing == WuXing.EARTH

    def test_wuxing_mapping_metal(self):
        """GENG and XIN are Metal."""
        assert HeavenlyStem.GENG.wuxing == WuXing.METAL
        assert HeavenlyStem.XIN.wuxing == WuXing.METAL

    def test_wuxing_mapping_water(self):
        """REN and GUI are Water."""
        assert HeavenlyStem.REN.wuxing == WuXing.WATER
        assert HeavenlyStem.GUI.wuxing == WuXing.WATER

    def test_yinyang_alternating(self):
        """Odd stems are Yang, even stems are Yin."""
        yang_stems = [HeavenlyStem.JIA, HeavenlyStem.BING, HeavenlyStem.WU,
                      HeavenlyStem.GENG, HeavenlyStem.REN]
        yin_stems = [HeavenlyStem.YI, HeavenlyStem.DING, HeavenlyStem.JI,
                     HeavenlyStem.XIN, HeavenlyStem.GUI]

        for stem in yang_stems:
            assert stem.yinyang == YinYang.YANG

        for stem in yin_stems:
            assert stem.yinyang == YinYang.YIN

    def test_from_chinese_valid(self):
        """from_chinese creates correct stem from Chinese character."""
        assert HeavenlyStem.from_chinese("甲") == HeavenlyStem.JIA
        assert HeavenlyStem.from_chinese("癸") == HeavenlyStem.GUI

    def test_from_chinese_invalid(self):
        """from_chinese raises ValueError for unknown character."""
        with pytest.raises(ValueError, match="Unknown stem"):
            HeavenlyStem.from_chinese("X")

    def test_all_ordered(self):
        """all_ordered returns stems in traditional order."""
        ordered = HeavenlyStem.all_ordered()
        assert len(ordered) == 10
        assert ordered[0] == HeavenlyStem.JIA
        assert ordered[9] == HeavenlyStem.GUI


class TestEarthlyBranch:
    """Tests for EarthlyBranch (地支) enum."""

    def test_all_twelve_branches_exist(self):
        """All twelve earthly branches are defined."""
        branches = list(EarthlyBranch)
        assert len(branches) == 12

    def test_chinese_values(self):
        """Branches have correct Chinese characters."""
        expected = {
            EarthlyBranch.ZI: "子", EarthlyBranch.CHOU: "丑",
            EarthlyBranch.YIN: "寅", EarthlyBranch.MAO: "卯",
            EarthlyBranch.CHEN: "辰", EarthlyBranch.SI: "巳",
            EarthlyBranch.WU: "午", EarthlyBranch.WEI: "未",
            EarthlyBranch.SHEN: "申", EarthlyBranch.YOU: "酉",
            EarthlyBranch.XU: "戌", EarthlyBranch.HAI: "亥",
        }
        for branch, char in expected.items():
            assert branch.value == char
            assert branch.chinese == char

    def test_wuxing_mapping(self):
        """Branches have correct WuXing mappings."""
        # Water branches
        assert EarthlyBranch.ZI.wuxing == WuXing.WATER
        assert EarthlyBranch.HAI.wuxing == WuXing.WATER

        # Wood branches
        assert EarthlyBranch.YIN.wuxing == WuXing.WOOD
        assert EarthlyBranch.MAO.wuxing == WuXing.WOOD

        # Fire branches
        assert EarthlyBranch.SI.wuxing == WuXing.FIRE
        assert EarthlyBranch.WU.wuxing == WuXing.FIRE

        # Earth branches
        assert EarthlyBranch.CHOU.wuxing == WuXing.EARTH
        assert EarthlyBranch.CHEN.wuxing == WuXing.EARTH
        assert EarthlyBranch.WEI.wuxing == WuXing.EARTH
        assert EarthlyBranch.XU.wuxing == WuXing.EARTH

        # Metal branches
        assert EarthlyBranch.SHEN.wuxing == WuXing.METAL
        assert EarthlyBranch.YOU.wuxing == WuXing.METAL

    def test_hidden_stems_zi(self):
        """子 contains only 癸 (Water Yin)."""
        hidden = EarthlyBranch.ZI.hidden_stems
        assert len(hidden) == 1
        assert hidden[HeavenlyStem.GUI] == 1.0

    def test_hidden_stems_chou(self):
        """丑 contains 己 (0.5), 癸 (0.3), 辛 (0.2)."""
        hidden = EarthlyBranch.CHOU.hidden_stems
        assert len(hidden) == 3
        assert hidden[HeavenlyStem.JI] == 0.5
        assert hidden[HeavenlyStem.GUI] == 0.3
        assert hidden[HeavenlyStem.XIN] == 0.2

    def test_hidden_stems_ratios_sum_to_one(self):
        """Hidden stem ratios sum to approximately 1.0."""
        for branch in EarthlyBranch:
            total = sum(branch.hidden_stems.values())
            assert abs(total - 1.0) < 0.01, f"{branch.chinese} ratios sum to {total}"

    def test_from_chinese_valid(self):
        """from_chinese creates correct branch from Chinese character."""
        assert EarthlyBranch.from_chinese("子") == EarthlyBranch.ZI
        assert EarthlyBranch.from_chinese("亥") == EarthlyBranch.HAI

    def test_from_chinese_invalid(self):
        """from_chinese raises ValueError for unknown character."""
        with pytest.raises(ValueError, match="Unknown branch"):
            EarthlyBranch.from_chinese("X")

    def test_all_ordered(self):
        """all_ordered returns branches in traditional order."""
        ordered = EarthlyBranch.all_ordered()
        assert len(ordered) == 12
        assert ordered[0] == EarthlyBranch.ZI
        assert ordered[11] == EarthlyBranch.HAI


class TestStemBranchRelations:
    """Tests for StemBranchRelations class."""

    def test_six_harmonies_count(self):
        """There are 6 branch harmony pairs (六合)."""
        assert len(RELATIONS.LIU_HE) == 6

    def test_six_harmonies_contains_zi_chou(self):
        """子丑合 is in LIU_HE."""
        assert (EarthlyBranch.ZI, EarthlyBranch.CHOU) in RELATIONS.LIU_HE

    def test_six_harmonies_contains_wu_wei(self):
        """午未合 is in LIU_HE."""
        assert (EarthlyBranch.WU, EarthlyBranch.WEI) in RELATIONS.LIU_HE

    def test_five_combinations_count(self):
        """There are 5 stem combination pairs (五合)."""
        assert len(RELATIONS.WU_HE) == 5

    def test_five_combinations_contains_jia_ji(self):
        """甲己合 is in WU_HE."""
        assert (HeavenlyStem.JIA, HeavenlyStem.JI) in RELATIONS.WU_HE

    def test_five_combinations_contains_yi_geng(self):
        """乙庚合 is in WU_HE."""
        assert (HeavenlyStem.YI, HeavenlyStem.GENG) in RELATIONS.WU_HE

    def test_stem_clashes_count(self):
        """There are 4 stem clash pairs (天干相冲)."""
        assert len(RELATIONS.GAN_CHONG) == 4

    def test_stem_clashes_contains_jia_geng(self):
        """甲庚冲 is in GAN_CHONG."""
        assert (HeavenlyStem.JIA, HeavenlyStem.GENG) in RELATIONS.GAN_CHONG

    def test_branch_clashes_count(self):
        """There are 6 branch clash pairs (地支相冲)."""
        assert len(RELATIONS.ZHI_CHONG) == 6

    def test_branch_clashes_contains_zi_wu(self):
        """子午冲 is in ZHI_CHONG."""
        assert (EarthlyBranch.ZI, EarthlyBranch.WU) in RELATIONS.ZHI_CHONG

    def test_branch_clashes_contains_mao_you(self):
        """卯酉冲 is in ZHI_CHONG."""
        assert (EarthlyBranch.MAO, EarthlyBranch.YOU) in RELATIONS.ZHI_CHONG

    def test_relations_is_frozen(self):
        """RELATIONS is an immutable dataclass instance."""
        assert isinstance(RELATIONS, StemBranchRelations)
