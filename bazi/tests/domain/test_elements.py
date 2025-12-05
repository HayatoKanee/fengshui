"""
Tests for Five Elements (WuXing), YinYang, and WangXiang domain models.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.elements import WuXing, YinYang, WangXiang


class TestYinYang:
    """Tests for YinYang enum."""

    def test_values(self):
        """YinYang enum has correct values."""
        assert YinYang.YANG.value == "阳"
        assert YinYang.YIN.value == "阴"

    def test_chinese_property(self):
        """chinese property returns the Chinese character."""
        assert YinYang.YANG.chinese == "阳"
        assert YinYang.YIN.chinese == "阴"

    def test_opposite_yang_to_yin(self):
        """YANG opposite is YIN."""
        assert YinYang.YANG.opposite == YinYang.YIN

    def test_opposite_yin_to_yang(self):
        """YIN opposite is YANG."""
        assert YinYang.YIN.opposite == YinYang.YANG

    def test_opposite_is_involutive(self):
        """Opposite of opposite returns original."""
        assert YinYang.YANG.opposite.opposite == YinYang.YANG
        assert YinYang.YIN.opposite.opposite == YinYang.YIN


class TestWuXing:
    """Tests for WuXing (Five Elements) enum."""

    def test_all_elements_exist(self):
        """All five elements are defined."""
        elements = [WuXing.WOOD, WuXing.FIRE, WuXing.EARTH, WuXing.METAL, WuXing.WATER]
        assert len(elements) == 5

    def test_chinese_values(self):
        """Elements have correct Chinese characters."""
        assert WuXing.WOOD.value == "木"
        assert WuXing.FIRE.value == "火"
        assert WuXing.EARTH.value == "土"
        assert WuXing.METAL.value == "金"
        assert WuXing.WATER.value == "水"

    def test_chinese_property(self):
        """chinese property returns the Chinese character."""
        assert WuXing.WOOD.chinese == "木"
        assert WuXing.FIRE.chinese == "火"

    def test_from_chinese_valid(self):
        """from_chinese creates correct element from Chinese character."""
        assert WuXing.from_chinese("木") == WuXing.WOOD
        assert WuXing.from_chinese("火") == WuXing.FIRE
        assert WuXing.from_chinese("土") == WuXing.EARTH
        assert WuXing.from_chinese("金") == WuXing.METAL
        assert WuXing.from_chinese("水") == WuXing.WATER

    def test_from_chinese_invalid(self):
        """from_chinese raises ValueError for unknown character."""
        with pytest.raises(ValueError, match="Unknown element"):
            WuXing.from_chinese("X")

    # Generation cycle tests (生): Wood → Fire → Earth → Metal → Water → Wood
    def test_generation_cycle_complete(self):
        """Generation cycle is complete (五行相生)."""
        assert WuXing.WOOD.generates == WuXing.FIRE
        assert WuXing.FIRE.generates == WuXing.EARTH
        assert WuXing.EARTH.generates == WuXing.METAL
        assert WuXing.METAL.generates == WuXing.WATER
        assert WuXing.WATER.generates == WuXing.WOOD

    def test_generation_cycle_is_closed(self):
        """Following generation 5 times returns to original."""
        element = WuXing.WOOD
        for _ in range(5):
            element = element.generates
        assert element == WuXing.WOOD

    # Overcoming cycle tests (克): Wood → Earth → Water → Fire → Metal → Wood
    def test_overcoming_cycle_complete(self):
        """Overcoming cycle is complete (五行相克)."""
        assert WuXing.WOOD.overcomes == WuXing.EARTH
        assert WuXing.EARTH.overcomes == WuXing.WATER
        assert WuXing.WATER.overcomes == WuXing.FIRE
        assert WuXing.FIRE.overcomes == WuXing.METAL
        assert WuXing.METAL.overcomes == WuXing.WOOD

    def test_overcoming_cycle_is_closed(self):
        """Following overcoming 5 times returns to original."""
        element = WuXing.WOOD
        for _ in range(5):
            element = element.overcomes
        assert element == WuXing.WOOD

    # Reverse relationships
    def test_generated_by_is_inverse_of_generates(self):
        """generated_by is the inverse of generates."""
        for element in WuXing:
            generator = element.generated_by
            assert generator.generates == element

    def test_overcome_by_is_inverse_of_overcomes(self):
        """overcome_by is the inverse of overcomes."""
        for element in WuXing:
            conqueror = element.overcome_by
            assert conqueror.overcomes == element

    # Beneficial and harmful elements
    def test_beneficial_includes_self_and_parent(self):
        """Beneficial elements include self and the element that generates it."""
        assert WuXing.FIRE.beneficial == {WuXing.FIRE, WuXing.WOOD}
        assert WuXing.METAL.beneficial == {WuXing.METAL, WuXing.EARTH}

    def test_harmful_includes_child_overcome_and_overcome_by(self):
        """Harmful elements include child, what it overcomes, and what overcomes it."""
        # Wood's harmful: Fire (child), Earth (overcomes), Metal (overcome_by)
        assert WuXing.WOOD.harmful == {WuXing.FIRE, WuXing.EARTH, WuXing.METAL}

    def test_beneficial_and_harmful_partition(self):
        """Each element appears in exactly one of beneficial or harmful sets."""
        for element in WuXing:
            # beneficial + harmful should have 5 elements (all WuXing)
            all_related = element.beneficial | element.harmful
            assert len(all_related) == 5
            # No overlap
            assert len(element.beneficial & element.harmful) == 0


class TestWangXiang:
    """Tests for WangXiang (seasonal strength phases)."""

    def test_all_phases_exist(self):
        """All five phases are defined."""
        phases = [WangXiang.WANG, WangXiang.XIANG, WangXiang.XIU, WangXiang.QIU, WangXiang.SI]
        assert len(phases) == 5

    def test_chinese_values(self):
        """Phases have correct Chinese characters."""
        assert WangXiang.WANG.value == "旺"
        assert WangXiang.XIANG.value == "相"
        assert WangXiang.XIU.value == "休"
        assert WangXiang.QIU.value == "囚"
        assert WangXiang.SI.value == "死"

    def test_chinese_property(self):
        """chinese property returns the Chinese character."""
        assert WangXiang.WANG.chinese == "旺"
        assert WangXiang.SI.chinese == "死"

    def test_multiplier_strong_phases(self):
        """WANG and XIANG have 1.2 multiplier."""
        assert WangXiang.WANG.multiplier == 1.2
        assert WangXiang.XIANG.multiplier == 1.2

    def test_multiplier_neutral_phase(self):
        """XIU has 1.0 multiplier."""
        assert WangXiang.XIU.multiplier == 1.0

    def test_multiplier_weak_phases(self):
        """QIU and SI have 0.8 multiplier."""
        assert WangXiang.QIU.multiplier == 0.8
        assert WangXiang.SI.multiplier == 0.8

    def test_multiplier_hierarchy(self):
        """Multipliers follow strength hierarchy."""
        assert WangXiang.WANG.multiplier == WangXiang.XIANG.multiplier
        assert WangXiang.WANG.multiplier > WangXiang.XIU.multiplier
        assert WangXiang.XIU.multiplier > WangXiang.QIU.multiplier
        assert WangXiang.QIU.multiplier == WangXiang.SI.multiplier
