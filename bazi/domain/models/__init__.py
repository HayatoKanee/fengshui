"""
BaZi Domain Models.

Pure Python domain models - NO Django dependencies.
"""
from .elements import (
    WuXing,
    WuXingRelation,
    YinYang,
    WangXiang,
    get_wuxing_relation,
    RELATIONSHIP_WEIGHTS,
)
from .stems_branches import (
    # Primary names (干支 pinyin)
    TianGan,
    DiZhi,
    GanZhiRelations,
    RELATIONS,
    check_he,
    # Backward compatibility aliases
    HeavenlyStem,
    EarthlyBranch,
    StemBranchRelations,
)
from .pillar import Pillar
from .bazi import BaZi, BirthData
from .shishen import (
    ShiShen,
    ShiShenChart,
    calculate_shishen,
)
from .shensha import (
    ShenShaType,
    ShenSha,
    ShenShaAnalysis,
)
from .analysis import (
    WuXingStrength,
    DayMasterStrength,
    FavorableElements,
    BaZiAnalysis,
)
from .pattern import (
    PatternCategory,
    PatternType,
    PatternYongShen,
    SpecialPattern,
    ZHUAN_WANG_YONG_SHEN,
    HUA_QI_YONG_SHEN,
)

__all__ = [
    # Elements (五行)
    "WuXing",
    "WuXingRelation",
    "YinYang",
    "WangXiang",
    "get_wuxing_relation",
    "RELATIONSHIP_WEIGHTS",
    # Stems and Branches (干支) - Primary names
    "TianGan",
    "DiZhi",
    "GanZhiRelations",
    "RELATIONS",
    "check_he",
    # Backward compatibility aliases
    "HeavenlyStem",
    "EarthlyBranch",
    "StemBranchRelations",
    # Pillar
    "Pillar",
    # BaZi
    "BaZi",
    "BirthData",
    # ShiShen
    "ShiShen",
    "ShiShenChart",
    "calculate_shishen",
    # ShenSha
    "ShenShaType",
    "ShenSha",
    "ShenShaAnalysis",
    # Analysis
    "WuXingStrength",
    "DayMasterStrength",
    "FavorableElements",
    "BaZiAnalysis",
    # Pattern (特殊格局)
    "PatternCategory",
    "PatternType",
    "PatternYongShen",
    "SpecialPattern",
    "ZHUAN_WANG_YONG_SHEN",
    "HUA_QI_YONG_SHEN",
]
