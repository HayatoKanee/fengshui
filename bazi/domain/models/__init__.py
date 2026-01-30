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
)
from .stems_branches import (
    HeavenlyStem,
    EarthlyBranch,
    StemBranchRelations,
    RELATIONS,
    check_he,
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

__all__ = [
    # Elements
    "WuXing",
    "WuXingRelation",
    "YinYang",
    "WangXiang",
    "get_wuxing_relation",
    # Stems and Branches
    "HeavenlyStem",
    "EarthlyBranch",
    "StemBranchRelations",
    "RELATIONS",
    "check_he",
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
]
