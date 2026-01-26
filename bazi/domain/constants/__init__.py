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
    HOUR_INFO,
    ZODIAC_HOURS,
    get_stem_wuxing,
    get_branch_wuxing,
    get_stem_yinyang,
    get_hour_name,
    get_hour_time_range,
    get_hour_branch,
    get_hour_display,
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
    TIAN_DE_HE,
    YUE_DE,
    YUE_DE_HE,
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
    "HOUR_INFO",
    "ZODIAC_HOURS",
    "get_stem_wuxing",
    "get_branch_wuxing",
    "get_stem_yinyang",
    "get_hour_name",
    "get_hour_time_range",
    "get_hour_branch",
    "get_hour_display",
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
    "TIAN_DE_HE",
    "YUE_DE",
    "YUE_DE_HE",
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
]
