"""
Tests for branch relationships (三合、三会、刑、害、破).

These tests verify the correctness of all branch relationship
constants and helper functions.
"""
import pytest

from bazi.domain.constants.branch_relations import (
    # 三合
    SAN_HE_TRIOS,
    SAN_HE_PAIRS,
    get_san_he_element,
    get_ban_he_element,
    # 三会
    SAN_HUI_TRIOS,
    get_san_hui_element,
    # 刑
    XING_TRIOS,
    XING_PAIRS,
    ZI_XING,
    is_xing,
    is_zi_xing,
    has_zi_xing,
    get_san_xing_type,
    # 害
    HAI_PAIRS,
    is_hai,
    # 破
    PO_PAIRS,
    is_po,
)
from bazi.domain.models.elements import WuXing


class TestSanHe:
    """Tests for 三合 (Three Harmonies)."""

    def test_san_he_trios_count(self):
        """Should have exactly 4 three-harmony combinations."""
        assert len(SAN_HE_TRIOS) == 4

    def test_san_he_fire_trio(self):
        """寅午戌 should form fire (火局)."""
        trio = frozenset({'寅', '午', '戌'})
        assert SAN_HE_TRIOS[trio] == WuXing.FIRE

    def test_san_he_metal_trio(self):
        """巳酉丑 should form metal (金局)."""
        trio = frozenset({'巳', '酉', '丑'})
        assert SAN_HE_TRIOS[trio] == WuXing.METAL

    def test_san_he_water_trio(self):
        """申子辰 should form water (水局)."""
        trio = frozenset({'申', '子', '辰'})
        assert SAN_HE_TRIOS[trio] == WuXing.WATER

    def test_san_he_wood_trio(self):
        """亥卯未 should form wood (木局)."""
        trio = frozenset({'亥', '卯', '未'})
        assert SAN_HE_TRIOS[trio] == WuXing.WOOD

    def test_get_san_he_element_complete(self):
        """get_san_he_element should return element for complete trio."""
        assert get_san_he_element(['寅', '午', '戌']) == WuXing.FIRE
        assert get_san_he_element(['巳', '酉', '丑']) == WuXing.METAL
        assert get_san_he_element(['申', '子', '辰']) == WuXing.WATER
        assert get_san_he_element(['亥', '卯', '未']) == WuXing.WOOD

    def test_get_san_he_element_with_extra_branches(self):
        """get_san_he_element should work when trio is subset of branches."""
        # Four pillars might have more branches
        assert get_san_he_element(['寅', '午', '戌', '子']) == WuXing.FIRE
        assert get_san_he_element(['申', '子', '辰', '午']) == WuXing.WATER

    def test_get_san_he_element_incomplete(self):
        """get_san_he_element should return None for incomplete trio."""
        assert get_san_he_element(['寅', '午']) is None
        assert get_san_he_element(['子', '丑', '寅']) is None

    def test_get_san_he_element_empty(self):
        """get_san_he_element should return None for empty list."""
        assert get_san_he_element([]) is None


class TestBanHe:
    """Tests for 半合 (Half Harmonies)."""

    def test_ban_he_pairs_count(self):
        """Should have 24 half-harmony pairs (6 pairs * 4 elements, bidirectional)."""
        assert len(SAN_HE_PAIRS) == 24

    def test_get_ban_he_fire(self):
        """Fire half-harmonies: 寅午, 午戌, 寅戌."""
        assert get_ban_he_element('寅', '午') == WuXing.FIRE
        assert get_ban_he_element('午', '戌') == WuXing.FIRE
        assert get_ban_he_element('寅', '戌') == WuXing.FIRE
        # Reverse order
        assert get_ban_he_element('午', '寅') == WuXing.FIRE

    def test_get_ban_he_metal(self):
        """Metal half-harmonies: 巳酉, 酉丑, 巳丑."""
        assert get_ban_he_element('巳', '酉') == WuXing.METAL
        assert get_ban_he_element('酉', '丑') == WuXing.METAL
        assert get_ban_he_element('巳', '丑') == WuXing.METAL

    def test_get_ban_he_water(self):
        """Water half-harmonies: 申子, 子辰, 申辰."""
        assert get_ban_he_element('申', '子') == WuXing.WATER
        assert get_ban_he_element('子', '辰') == WuXing.WATER
        assert get_ban_he_element('申', '辰') == WuXing.WATER

    def test_get_ban_he_wood(self):
        """Wood half-harmonies: 亥卯, 卯未, 亥未."""
        assert get_ban_he_element('亥', '卯') == WuXing.WOOD
        assert get_ban_he_element('卯', '未') == WuXing.WOOD
        assert get_ban_he_element('亥', '未') == WuXing.WOOD

    def test_get_ban_he_none(self):
        """Non-half-harmony pairs should return None."""
        assert get_ban_he_element('子', '丑') is None  # This is 六合, not 半合
        assert get_ban_he_element('寅', '申') is None  # This is 冲


class TestSanHui:
    """Tests for 三会 (Directional Combinations)."""

    def test_san_hui_trios_count(self):
        """Should have exactly 4 directional combinations."""
        assert len(SAN_HUI_TRIOS) == 4

    def test_san_hui_wood(self):
        """寅卯辰 should form wood (东方木)."""
        trio = frozenset({'寅', '卯', '辰'})
        assert SAN_HUI_TRIOS[trio] == WuXing.WOOD

    def test_san_hui_fire(self):
        """巳午未 should form fire (南方火)."""
        trio = frozenset({'巳', '午', '未'})
        assert SAN_HUI_TRIOS[trio] == WuXing.FIRE

    def test_san_hui_metal(self):
        """申酉戌 should form metal (西方金)."""
        trio = frozenset({'申', '酉', '戌'})
        assert SAN_HUI_TRIOS[trio] == WuXing.METAL

    def test_san_hui_water(self):
        """亥子丑 should form water (北方水)."""
        trio = frozenset({'亥', '子', '丑'})
        assert SAN_HUI_TRIOS[trio] == WuXing.WATER

    def test_get_san_hui_element_complete(self):
        """get_san_hui_element should return element for complete trio."""
        assert get_san_hui_element(['寅', '卯', '辰']) == WuXing.WOOD
        assert get_san_hui_element(['巳', '午', '未']) == WuXing.FIRE
        assert get_san_hui_element(['申', '酉', '戌']) == WuXing.METAL
        assert get_san_hui_element(['亥', '子', '丑']) == WuXing.WATER

    def test_get_san_hui_element_incomplete(self):
        """get_san_hui_element should return None for incomplete trio."""
        assert get_san_hui_element(['寅', '卯']) is None
        assert get_san_hui_element(['亥', '子']) is None


class TestXing:
    """Tests for 刑 (Punishments)."""

    def test_xing_trios_count(self):
        """Should have exactly 2 three-way punishment combinations."""
        assert len(XING_TRIOS) == 2

    def test_xing_wuen_zhixing(self):
        """寅巳申 should be 无恩之刑."""
        trio = frozenset({'寅', '巳', '申'})
        assert XING_TRIOS[trio] == '无恩之刑'

    def test_xing_chishi_zhixing(self):
        """丑戌未 should be 持势之刑."""
        trio = frozenset({'丑', '戌', '未'})
        assert XING_TRIOS[trio] == '持势之刑'

    def test_is_xing_wuli(self):
        """子卯 should be 无礼之刑."""
        assert is_xing('子', '卯') is True
        assert is_xing('卯', '子') is True

    def test_is_xing_wuen_pairs(self):
        """寅巳申 pairs should all be xing."""
        assert is_xing('寅', '巳') is True
        assert is_xing('巳', '申') is True
        assert is_xing('寅', '申') is True

    def test_is_xing_chishi_pairs(self):
        """丑戌未 pairs should all be xing."""
        assert is_xing('丑', '戌') is True
        assert is_xing('戌', '未') is True
        assert is_xing('丑', '未') is True

    def test_is_xing_false(self):
        """Non-punishment pairs should return False."""
        assert is_xing('子', '丑') is False  # This is 六合
        assert is_xing('子', '午') is False  # This is 冲

    def test_zi_xing_branches(self):
        """Self-punishment branches: 辰、午、酉、亥."""
        assert ZI_XING == frozenset({'辰', '午', '酉', '亥'})

    def test_is_zi_xing(self):
        """is_zi_xing should identify self-punishment branches."""
        assert is_zi_xing('辰') is True
        assert is_zi_xing('午') is True
        assert is_zi_xing('酉') is True
        assert is_zi_xing('亥') is True
        assert is_zi_xing('子') is False
        assert is_zi_xing('寅') is False

    def test_has_zi_xing_true(self):
        """has_zi_xing should detect duplicate self-punishment branches."""
        assert has_zi_xing(['辰', '辰', '午', '酉']) is True
        assert has_zi_xing(['子', '午', '午', '卯']) is True

    def test_has_zi_xing_false(self):
        """has_zi_xing should return False for no duplicates."""
        assert has_zi_xing(['辰', '午', '酉', '亥']) is False  # All different
        assert has_zi_xing(['子', '子', '丑', '寅']) is False  # 子 is not zi_xing

    def test_get_san_xing_type(self):
        """get_san_xing_type should return punishment type for complete trio."""
        assert get_san_xing_type(['寅', '巳', '申']) == '无恩之刑'
        assert get_san_xing_type(['丑', '戌', '未']) == '持势之刑'
        assert get_san_xing_type(['寅', '巳', '申', '子']) == '无恩之刑'  # With extra

    def test_get_san_xing_type_none(self):
        """get_san_xing_type should return None for incomplete trio."""
        assert get_san_xing_type(['寅', '巳']) is None
        assert get_san_xing_type(['子', '卯']) is None  # 子卯 is 无礼之刑, not 三刑


class TestHai:
    """Tests for 害 (Harms)."""

    def test_hai_pairs_count(self):
        """Should have 12 harm pairs (6 pairs, bidirectional)."""
        assert len(HAI_PAIRS) == 12

    def test_is_hai_all_pairs(self):
        """Test all six harm relationships."""
        # 子未害
        assert is_hai('子', '未') is True
        assert is_hai('未', '子') is True
        # 丑午害
        assert is_hai('丑', '午') is True
        assert is_hai('午', '丑') is True
        # 寅巳害
        assert is_hai('寅', '巳') is True
        assert is_hai('巳', '寅') is True
        # 卯辰害
        assert is_hai('卯', '辰') is True
        assert is_hai('辰', '卯') is True
        # 申亥害
        assert is_hai('申', '亥') is True
        assert is_hai('亥', '申') is True
        # 酉戌害
        assert is_hai('酉', '戌') is True
        assert is_hai('戌', '酉') is True

    def test_is_hai_false(self):
        """Non-harm pairs should return False."""
        assert is_hai('子', '丑') is False  # This is 六合
        assert is_hai('子', '午') is False  # This is 冲


class TestPo:
    """Tests for 破 (Breaks)."""

    def test_po_pairs_count(self):
        """Should have 12 break pairs (6 pairs, bidirectional)."""
        assert len(PO_PAIRS) == 12

    def test_is_po_all_pairs(self):
        """Test all six break relationships."""
        # 子酉破
        assert is_po('子', '酉') is True
        assert is_po('酉', '子') is True
        # 卯午破
        assert is_po('卯', '午') is True
        assert is_po('午', '卯') is True
        # 寅亥破
        assert is_po('寅', '亥') is True
        assert is_po('亥', '寅') is True
        # 巳申破
        assert is_po('巳', '申') is True
        assert is_po('申', '巳') is True
        # 辰丑破
        assert is_po('辰', '丑') is True
        assert is_po('丑', '辰') is True
        # 戌未破
        assert is_po('戌', '未') is True
        assert is_po('未', '戌') is True

    def test_is_po_false(self):
        """Non-break pairs should return False."""
        assert is_po('子', '丑') is False
        assert is_po('子', '午') is False  # This is 冲


class TestRelationshipOverlap:
    """Tests to verify some branches can have multiple relationships."""

    def test_yin_si_is_both_xing_and_hai(self):
        """寅巳 is both 刑 and 害."""
        assert is_xing('寅', '巳') is True
        assert is_hai('寅', '巳') is True

    def test_si_shen_is_both_xing_and_po(self):
        """巳申 is both 刑 (as part of 寅巳申) and 破."""
        assert is_xing('巳', '申') is True
        assert is_po('巳', '申') is True

    def test_yin_hai_is_both_liuhe_and_po(self):
        """寅亥 is both 六合 and 破."""
        from bazi.domain.constants import LIU_HE
        assert ('寅', '亥') in LIU_HE
        assert is_po('寅', '亥') is True
