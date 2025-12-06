"""
Domain Constants Package.

Contains domain-level constants and pure functions that don't depend
on external infrastructure.
"""
from .harmony import (
    LIU_HE,
    WU_HE,
    HIDDEN_GAN_RATIOS,
    is_harmony,
)

from .elements import (
    GAN_WUXING,
    ZHI_WUXING,
    GANZHI_WUXING,
    GAN_YINYANG,
    WUXING_LIST,
    get_stem_wuxing,
    get_branch_wuxing,
    get_stem_yinyang,
)

from .relationships import (
    WUXING_SHENG,
    WUXING_KE,
    RELATIONSHIPS,
    WUXING_RELATIONS,
    generates,
    controls,
    is_favorable,
    is_unfavorable,
)

from .phases import (
    ZHI_SEASONS,
    SEASON_PHASES,
    WANG_XIANG_VALUE,
    get_season,
    get_phase_for_element,
    get_phase_value,
)

from .clashes import (
    GAN_XIANG_CHONG,
    ZHI_XIANG_CHONG,
    WU_BU_YU_SHI,
    is_gan_clash,
    is_zhi_clash,
    is_clash,
    is_wu_bu_yu_shi,
)

from .shensha import (
    GUI_REN,
    TIAN_DE,
    YUE_DE,
    WEN_CHANG,
    LU_SHEN,
    YANG_REN,
    TAO_HUA,
    HONG_YAN_SHA,
    JIANG_XING,
    HUA_GAI,
    YI_MA,
    JIE_SHA,
    WANG_SHEN,
    GU_CHEN,
    GUA_SU,
    XUN_KONG,
    has_gui_ren,
    has_tian_de,
    has_yue_de,
    has_wen_chang,
)

__all__ = [
    # Harmony
    "LIU_HE",
    "WU_HE",
    "HIDDEN_GAN_RATIOS",
    "is_harmony",
    # Elements
    "GAN_WUXING",
    "ZHI_WUXING",
    "GANZHI_WUXING",
    "GAN_YINYANG",
    "WUXING_LIST",
    "get_stem_wuxing",
    "get_branch_wuxing",
    "get_stem_yinyang",
    # Relationships
    "WUXING_SHENG",
    "WUXING_KE",
    "RELATIONSHIPS",
    "WUXING_RELATIONS",
    "generates",
    "controls",
    "is_favorable",
    "is_unfavorable",
    # Phases
    "ZHI_SEASONS",
    "SEASON_PHASES",
    "WANG_XIANG_VALUE",
    "get_season",
    "get_phase_for_element",
    "get_phase_value",
    # Clashes
    "GAN_XIANG_CHONG",
    "ZHI_XIANG_CHONG",
    "WU_BU_YU_SHI",
    "is_gan_clash",
    "is_zhi_clash",
    "is_clash",
    "is_wu_bu_yu_shi",
    # ShenSha
    "GUI_REN",
    "TIAN_DE",
    "YUE_DE",
    "WEN_CHANG",
    "LU_SHEN",
    "YANG_REN",
    "TAO_HUA",
    "HONG_YAN_SHA",
    "JIANG_XING",
    "HUA_GAI",
    "YI_MA",
    "JIE_SHA",
    "WANG_SHEN",
    "GU_CHEN",
    "GUA_SU",
    "XUN_KONG",
    "has_gui_ren",
    "has_tian_de",
    "has_yue_de",
    "has_wen_chang",
]
