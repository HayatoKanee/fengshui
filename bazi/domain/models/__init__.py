"""
BaZi Domain Models.

Pure Python domain models - NO Django dependencies.
"""
from .elements import (
    WuXing,
    YinYang,
    WangXiang,
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
from .branch_analysis import (
    RelationType,
    BranchRelation,
    BranchRelationsAnalysis,
    SI_KU_BRANCHES,
    SI_KU_SET,
)
from .pattern_analysis import (
    PatternCategory,
    PatternType,
    SpecialPattern,
    RegularPattern,
    PatternAnalysis,
    REGULAR_PATTERN_SHISHEN_MAP,
)

__all__ = [
    # Elements
    "WuXing",
    "YinYang",
    "WangXiang",
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
    # Branch Relations
    "RelationType",
    "BranchRelation",
    "BranchRelationsAnalysis",
    "SI_KU_BRANCHES",
    "SI_KU_SET",
    # Pattern Analysis
    "PatternCategory",
    "PatternType",
    "SpecialPattern",
    "RegularPattern",
    "PatternAnalysis",
    "REGULAR_PATTERN_SHISHEN_MAP",
]
