"""
Tests for Pillar domain model.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.elements import WuXing
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.models.pillar import Pillar


class TestPillarCreation:
    """Tests for Pillar creation."""

    def test_create_from_enums(self):
        """Create pillar from stem and branch enums."""
        pillar = Pillar(stem=HeavenlyStem.JIA, branch=EarthlyBranch.ZI)
        assert pillar.stem == HeavenlyStem.JIA
        assert pillar.branch == EarthlyBranch.ZI

    def test_from_chinese_valid(self):
        """from_chinese creates pillar from two characters."""
        pillar = Pillar.from_chinese("甲子")
        assert pillar.stem == HeavenlyStem.JIA
        assert pillar.branch == EarthlyBranch.ZI

    def test_from_chinese_yi_chou(self):
        """from_chinese works for 乙丑."""
        pillar = Pillar.from_chinese("乙丑")
        assert pillar.stem == HeavenlyStem.YI
        assert pillar.branch == EarthlyBranch.CHOU

    def test_from_chinese_invalid_length(self):
        """from_chinese raises ValueError for wrong length."""
        with pytest.raises(ValueError, match="must be 2 characters"):
            Pillar.from_chinese("甲")

        with pytest.raises(ValueError, match="must be 2 characters"):
            Pillar.from_chinese("甲子丑")

    def test_from_chinese_invalid_stem(self):
        """from_chinese raises ValueError for invalid stem."""
        with pytest.raises(ValueError, match="未知天干"):
            Pillar.from_chinese("X子")

    def test_from_chinese_invalid_branch(self):
        """from_chinese raises ValueError for invalid branch."""
        with pytest.raises(ValueError, match="未知地支"):
            Pillar.from_chinese("甲X")


class TestPillarProperties:
    """Tests for Pillar properties."""

    def test_str_returns_chinese(self):
        """__str__ returns Chinese representation."""
        pillar = Pillar.from_chinese("甲子")
        assert str(pillar) == "甲子"

    def test_chinese_property(self):
        """chinese property returns Chinese representation."""
        pillar = Pillar.from_chinese("丙寅")
        assert pillar.chinese == "丙寅"

    def test_stem_wuxing(self):
        """stem_wuxing returns WuXing of the stem."""
        pillar = Pillar.from_chinese("甲子")
        assert pillar.stem_wuxing == WuXing.WOOD  # 甲 is Wood

    def test_branch_wuxing(self):
        """branch_wuxing returns WuXing of the branch."""
        pillar = Pillar.from_chinese("甲子")
        assert pillar.branch_wuxing == WuXing.WATER  # 子 is Water

    def test_hidden_stems(self):
        """hidden_stems returns the branch's hidden stems."""
        pillar = Pillar.from_chinese("甲寅")
        hidden = pillar.hidden_stems
        # 寅 contains 甲 (0.6), 丙 (0.3), 戊 (0.1)
        assert HeavenlyStem.JIA in hidden
        assert hidden[HeavenlyStem.JIA] == 0.6


class TestPillarImmutability:
    """Tests for Pillar immutability."""

    def test_pillar_is_frozen(self):
        """Pillar is immutable (frozen dataclass)."""
        pillar = Pillar.from_chinese("甲子")
        with pytest.raises(AttributeError):
            pillar.stem = HeavenlyStem.YI

    def test_pillar_is_hashable(self):
        """Frozen pillar can be used in sets and as dict keys."""
        pillar1 = Pillar.from_chinese("甲子")
        pillar2 = Pillar.from_chinese("甲子")
        pillar3 = Pillar.from_chinese("乙丑")

        pillar_set = {pillar1, pillar2, pillar3}
        assert len(pillar_set) == 2  # pillar1 == pillar2

    def test_pillar_equality(self):
        """Pillars with same stem and branch are equal."""
        pillar1 = Pillar.from_chinese("甲子")
        pillar2 = Pillar(stem=HeavenlyStem.JIA, branch=EarthlyBranch.ZI)
        assert pillar1 == pillar2


class TestWuXingRelationshipValues:
    """Tests for wuxing_relationship_values method."""

    def test_same_element(self):
        """Same element returns (10, 10)."""
        # 甲寅: Wood stem, Wood branch
        pillar = Pillar.from_chinese("甲寅")
        assert pillar.stem_wuxing == WuXing.WOOD
        assert pillar.branch_wuxing == WuXing.WOOD
        assert pillar.wuxing_relationship_values() == (10, 10)

    def test_stem_generates_branch(self):
        """When stem generates branch, returns (6, 8)."""
        # 甲巳: Wood stem generates Fire branch
        pillar = Pillar.from_chinese("甲巳")
        assert pillar.stem_wuxing == WuXing.WOOD
        assert pillar.branch_wuxing == WuXing.FIRE
        assert WuXing.WOOD.generates == WuXing.FIRE
        assert pillar.wuxing_relationship_values() == (6, 8)

    def test_stem_overcomes_branch(self):
        """When stem overcomes branch, returns (4, 2)."""
        # 甲辰: Wood stem overcomes Earth branch
        pillar = Pillar.from_chinese("甲辰")
        assert pillar.stem_wuxing == WuXing.WOOD
        assert pillar.branch_wuxing == WuXing.EARTH
        assert WuXing.WOOD.overcomes == WuXing.EARTH
        assert pillar.wuxing_relationship_values() == (4, 2)

    def test_branch_overcomes_stem(self):
        """When branch overcomes stem, returns (2, 4)."""
        # 甲申: Metal branch overcomes Wood stem
        pillar = Pillar.from_chinese("甲申")
        assert pillar.stem_wuxing == WuXing.WOOD
        assert pillar.branch_wuxing == WuXing.METAL
        assert WuXing.METAL.overcomes == WuXing.WOOD
        assert pillar.wuxing_relationship_values() == (2, 4)

    def test_branch_generates_stem(self):
        """When branch generates stem, returns (8, 6)."""
        # 甲子: Water branch generates Wood stem
        pillar = Pillar.from_chinese("甲子")
        assert pillar.stem_wuxing == WuXing.WOOD
        assert pillar.branch_wuxing == WuXing.WATER
        assert WuXing.WATER.generates == WuXing.WOOD
        assert pillar.wuxing_relationship_values() == (8, 6)


class TestSixtyJiaZiCycle:
    """Tests for traditional 60-pillar cycle (六十甲子)."""

    def test_jia_zi_is_first(self):
        """甲子 is the first pillar of the cycle."""
        pillar = Pillar.from_chinese("甲子")
        assert str(pillar) == "甲子"

    def test_gui_hai_is_last(self):
        """癸亥 is the last pillar of the cycle."""
        pillar = Pillar.from_chinese("癸亥")
        assert str(pillar) == "癸亥"

    def test_various_pillars(self):
        """Various pillars from the 60 cycle work correctly."""
        test_cases = [
            ("甲子", HeavenlyStem.JIA, EarthlyBranch.ZI),
            ("乙丑", HeavenlyStem.YI, EarthlyBranch.CHOU),
            ("丙寅", HeavenlyStem.BING, EarthlyBranch.YIN),
            ("丁卯", HeavenlyStem.DING, EarthlyBranch.MAO),
            ("戊辰", HeavenlyStem.WU, EarthlyBranch.CHEN),
            ("己巳", HeavenlyStem.JI, EarthlyBranch.SI),
            ("庚午", HeavenlyStem.GENG, EarthlyBranch.WU),
            ("辛未", HeavenlyStem.XIN, EarthlyBranch.WEI),
            ("壬申", HeavenlyStem.REN, EarthlyBranch.SHEN),
            ("癸酉", HeavenlyStem.GUI, EarthlyBranch.YOU),
        ]
        for chinese, expected_stem, expected_branch in test_cases:
            pillar = Pillar.from_chinese(chinese)
            assert pillar.stem == expected_stem, f"Failed for {chinese}"
            assert pillar.branch == expected_branch, f"Failed for {chinese}"
