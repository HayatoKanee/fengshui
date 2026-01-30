"""
特殊格局 (Special Patterns) domain models.

八字变格/特殊格局的数据模型，包括：
- 從格 (Following Patterns)
- 專旺格 (Specialized Dominant Patterns)
- 化氣格 (Transformation Patterns)
- 兩神成象格 (Two Gods Forming Image)
- 暗沖格 (Hidden Clash Patterns)
- 暗合格 (Hidden Combination Patterns)

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .elements import WuXing


class PatternCategory(Enum):
    """特殊格局大類"""
    CONG_GE = "從格"              # Following patterns
    ZHUAN_WANG_GE = "專旺格"      # Specialized dominant patterns
    HUA_QI_GE = "化氣格"          # Transformation patterns
    LIANG_SHEN_GE = "兩神成象格"   # Two gods forming image
    AN_CHONG_GE = "暗沖格"        # Hidden clash patterns
    AN_HE_GE = "暗合格"           # Hidden combination patterns

    @property
    def chinese(self) -> str:
        return self.value


class PatternType(Enum):
    """
    特殊格局具體類型

    Each pattern type belongs to a category and has specific conditions.
    """
    # 從格 (Following Patterns)
    CONG_CAI = "從財格"        # Following Wealth
    CONG_GUAN_SHA = "從官殺格"  # Following Official/Killer
    CONG_ER = "從兒格"         # Following Child (Food/Hurting)

    # 專旺格 (Specialized Dominant Patterns)
    QU_ZHI = "曲直格"     # Wood dominant
    YAN_SHANG = "炎上格"  # Fire dominant
    JIA_SE = "稼穡格"     # Earth dominant
    CONG_GE_METAL = "從革格"  # Metal dominant
    RUN_XIA = "潤下格"    # Water dominant

    # 化氣格 (Transformation Patterns)
    HUA_MU = "化木格"     # Transform to Wood
    HUA_HUO = "化火格"    # Transform to Fire
    HUA_TU = "化土格"     # Transform to Earth
    HUA_JIN = "化金格"    # Transform to Metal
    HUA_SHUI = "化水格"   # Transform to Water

    # 兩神成象格 (Two Gods Forming Image)
    LIANG_SHEN_XIANG_CHENG = "兩神相成格"  # Two gods mutual overcoming
    LIANG_SHEN_XIANG_SHENG = "兩神相生格"  # Two gods mutual generating

    # 暗沖格 (Hidden Clash Patterns)
    DAO_CHONG_LU_MA = "倒沖祿馬格"   # Reverse clash for fortune
    FEI_TIAN_LU_MA = "飛天祿馬格"   # Flying sky fortune
    JING_LAN_CHA = "井欄叉格"       # Well railing fork

    # 暗合格 (Hidden Combination Patterns)
    AN_HE_GUAN = "暗合官格"         # Hidden combination for official

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def category(self) -> PatternCategory:
        """Get the category this pattern belongs to."""
        return _PATTERN_CATEGORIES[self]


# Pattern type to category mapping
_PATTERN_CATEGORIES = {
    # 從格
    PatternType.CONG_CAI: PatternCategory.CONG_GE,
    PatternType.CONG_GUAN_SHA: PatternCategory.CONG_GE,
    PatternType.CONG_ER: PatternCategory.CONG_GE,
    # 專旺格
    PatternType.QU_ZHI: PatternCategory.ZHUAN_WANG_GE,
    PatternType.YAN_SHANG: PatternCategory.ZHUAN_WANG_GE,
    PatternType.JIA_SE: PatternCategory.ZHUAN_WANG_GE,
    PatternType.CONG_GE_METAL: PatternCategory.ZHUAN_WANG_GE,
    PatternType.RUN_XIA: PatternCategory.ZHUAN_WANG_GE,
    # 化氣格
    PatternType.HUA_MU: PatternCategory.HUA_QI_GE,
    PatternType.HUA_HUO: PatternCategory.HUA_QI_GE,
    PatternType.HUA_TU: PatternCategory.HUA_QI_GE,
    PatternType.HUA_JIN: PatternCategory.HUA_QI_GE,
    PatternType.HUA_SHUI: PatternCategory.HUA_QI_GE,
    # 兩神成象格
    PatternType.LIANG_SHEN_XIANG_CHENG: PatternCategory.LIANG_SHEN_GE,
    PatternType.LIANG_SHEN_XIANG_SHENG: PatternCategory.LIANG_SHEN_GE,
    # 暗沖格
    PatternType.DAO_CHONG_LU_MA: PatternCategory.AN_CHONG_GE,
    PatternType.FEI_TIAN_LU_MA: PatternCategory.AN_CHONG_GE,
    PatternType.JING_LAN_CHA: PatternCategory.AN_CHONG_GE,
    # 暗合格
    PatternType.AN_HE_GUAN: PatternCategory.AN_HE_GE,
}


@dataclass(frozen=True)
class PatternYongShen:
    """
    格局用神喜忌

    用神 (Yong Shen): Primary beneficial element
    喜神 (Xi Shen): Secondary beneficial elements
    忌神 (Ji Shen): Unfavorable elements
    """
    yong_shen: WuXing
    xi_shen: List[WuXing]
    ji_shen: List[WuXing]
    bu_xi: Optional[List[WuXing]] = None  # 不喜 (disliked but not as bad as ji_shen)


@dataclass(frozen=True)
class SpecialPattern:
    """
    特殊格局結果

    按古籍規則判斷，符合條件即成格。
    """
    pattern_type: PatternType
    yong_shen_info: PatternYongShen
    description: str

    @property
    def category(self) -> PatternCategory:
        """Get the category of this pattern."""
        return self.pattern_type.category

    @property
    def chinese_name(self) -> str:
        """Get the Chinese name of the pattern."""
        return self.pattern_type.chinese


# =============================================================================
# 用神喜忌配置 (Yong Shen Configuration)
# =============================================================================

# 從格用神喜忌
CONG_GE_YONG_SHEN = {
    PatternType.CONG_CAI: PatternYongShen(
        yong_shen=WuXing.EARTH,  # Placeholder - actual depends on day master
        xi_shen=[],  # 食傷
        ji_shen=[],  # 比劫
        bu_xi=[],    # 印星
    ),
    PatternType.CONG_GUAN_SHA: PatternYongShen(
        yong_shen=WuXing.EARTH,  # Placeholder
        xi_shen=[],  # 財星
        ji_shen=[],  # 食傷
        bu_xi=[],    # 印比
    ),
    PatternType.CONG_ER: PatternYongShen(
        yong_shen=WuXing.EARTH,  # Placeholder
        xi_shen=[],  # 財星
        ji_shen=[],  # 印星
        bu_xi=[],    # 官殺
    ),
}

# 專旺格用神喜忌
ZHUAN_WANG_YONG_SHEN = {
    PatternType.QU_ZHI: PatternYongShen(
        yong_shen=WuXing.WOOD,
        xi_shen=[WuXing.WATER, WuXing.FIRE],
        ji_shen=[WuXing.METAL],
    ),
    PatternType.YAN_SHANG: PatternYongShen(
        yong_shen=WuXing.FIRE,
        xi_shen=[WuXing.WOOD, WuXing.EARTH],
        ji_shen=[WuXing.WATER],
    ),
    PatternType.JIA_SE: PatternYongShen(
        yong_shen=WuXing.EARTH,
        xi_shen=[WuXing.FIRE, WuXing.METAL],
        ji_shen=[WuXing.WOOD],
    ),
    PatternType.CONG_GE_METAL: PatternYongShen(
        yong_shen=WuXing.METAL,
        xi_shen=[WuXing.EARTH, WuXing.WATER],
        ji_shen=[WuXing.FIRE],
    ),
    PatternType.RUN_XIA: PatternYongShen(
        yong_shen=WuXing.WATER,
        xi_shen=[WuXing.METAL, WuXing.WOOD],
        ji_shen=[WuXing.EARTH],
    ),
}

# 化氣格用神喜忌
HUA_QI_YONG_SHEN = {
    PatternType.HUA_MU: PatternYongShen(
        yong_shen=WuXing.WOOD,
        xi_shen=[WuXing.WATER, WuXing.FIRE],
        ji_shen=[WuXing.METAL],
    ),
    PatternType.HUA_HUO: PatternYongShen(
        yong_shen=WuXing.FIRE,
        xi_shen=[WuXing.WOOD, WuXing.EARTH],
        ji_shen=[WuXing.WATER],
    ),
    PatternType.HUA_TU: PatternYongShen(
        yong_shen=WuXing.EARTH,
        xi_shen=[WuXing.FIRE, WuXing.METAL],
        ji_shen=[WuXing.WOOD],
    ),
    PatternType.HUA_JIN: PatternYongShen(
        yong_shen=WuXing.METAL,
        xi_shen=[WuXing.EARTH, WuXing.WATER],
        ji_shen=[WuXing.FIRE],
    ),
    PatternType.HUA_SHUI: PatternYongShen(
        yong_shen=WuXing.WATER,
        xi_shen=[WuXing.METAL, WuXing.WOOD],
        ji_shen=[WuXing.EARTH],
    ),
}
