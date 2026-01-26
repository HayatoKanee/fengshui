"""
ShenSha Extractors - Shared extraction functions for ShenSha rules.

提取器函数用于从八字中提取参考值和目标值，是神煞计算的核心组件。

遵循 DRY 原则，所有提取器在此定义一次，由 shensha_registry 和 shensha_rule 共享。

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Tuple

if TYPE_CHECKING:
    from .bazi import BaZi
    from .pillar import Pillar


# ============================================================
# Type Aliases
# ============================================================

RefExtractor = Callable[["BaZi"], str]
TargetExtractor = Callable[["Pillar"], List[Tuple[str, str]]]


# ============================================================
# Reference Extractors (从八字提取参考值)
# ============================================================

def day_stem_extractor(bazi: "BaZi") -> str:
    """Extract day stem (日干) as reference."""
    return bazi.day_master.chinese


def month_branch_extractor(bazi: "BaZi") -> str:
    """Extract month branch (月支) as reference."""
    return bazi.month_pillar.branch.chinese


def year_branch_extractor(bazi: "BaZi") -> str:
    """Extract year branch (年支) as reference."""
    return bazi.year_pillar.branch.chinese


def day_branch_extractor(bazi: "BaZi") -> str:
    """Extract day branch (日支) as reference."""
    return bazi.day_pillar.branch.chinese


def day_pillar_extractor(bazi: "BaZi") -> str:
    """Extract day pillar (日柱) as reference (for 空亡)."""
    return bazi.day_pillar.chinese


# ============================================================
# Target Extractors (从柱提取目标值)
# ============================================================

def branch_target(pillar: "Pillar") -> List[Tuple[str, str]]:
    """Extract only branch as target."""
    return [(pillar.branch.chinese, "branch")]


def stem_target(pillar: "Pillar") -> List[Tuple[str, str]]:
    """Extract only stem as target."""
    return [(pillar.stem.chinese, "stem")]


def stem_and_branch_target(pillar: "Pillar") -> List[Tuple[str, str]]:
    """Extract both stem and branch as targets (for 天德 etc.)."""
    return [
        (pillar.stem.chinese, "stem"),
        (pillar.branch.chinese, "branch"),
    ]


# ============================================================
# Exports
# ============================================================

__all__ = [
    # Type aliases
    "RefExtractor",
    "TargetExtractor",
    # Reference extractors
    "day_stem_extractor",
    "month_branch_extractor",
    "year_branch_extractor",
    "day_branch_extractor",
    "day_pillar_extractor",
    # Target extractors
    "branch_target",
    "stem_target",
    "stem_and_branch_target",
]
