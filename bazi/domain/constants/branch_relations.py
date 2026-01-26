"""
Branch Relationships Domain Constants.

地支关系常量：三合、三会、刑、害、破
These branch relationships affect BaZi analysis and strength calculations.
"""
from typing import Dict, FrozenSet, List, Tuple

from ..models.elements import WuXing


# =============================================================================
# 三合 (SAN_HE) - Three Harmonies
# =============================================================================
# Each trio combines to form a specific element (局)

SAN_HE_TRIOS: Dict[FrozenSet[str], WuXing] = {
    frozenset({'寅', '午', '戌'}): WuXing.FIRE,   # 火局
    frozenset({'巳', '酉', '丑'}): WuXing.METAL,  # 金局
    frozenset({'申', '子', '辰'}): WuXing.WATER,  # 水局
    frozenset({'亥', '卯', '未'}): WuXing.WOOD,   # 木局
}

# 半合 (BAN_HE) - Half Harmonies (any two of three)
# Each pair indicates partial formation toward the element
SAN_HE_PAIRS: Dict[Tuple[str, str], WuXing] = {
    # 火局半合
    ('寅', '午'): WuXing.FIRE, ('午', '寅'): WuXing.FIRE,
    ('午', '戌'): WuXing.FIRE, ('戌', '午'): WuXing.FIRE,
    ('寅', '戌'): WuXing.FIRE, ('戌', '寅'): WuXing.FIRE,
    # 金局半合
    ('巳', '酉'): WuXing.METAL, ('酉', '巳'): WuXing.METAL,
    ('酉', '丑'): WuXing.METAL, ('丑', '酉'): WuXing.METAL,
    ('巳', '丑'): WuXing.METAL, ('丑', '巳'): WuXing.METAL,
    # 水局半合
    ('申', '子'): WuXing.WATER, ('子', '申'): WuXing.WATER,
    ('子', '辰'): WuXing.WATER, ('辰', '子'): WuXing.WATER,
    ('申', '辰'): WuXing.WATER, ('辰', '申'): WuXing.WATER,
    # 木局半合
    ('亥', '卯'): WuXing.WOOD, ('卯', '亥'): WuXing.WOOD,
    ('卯', '未'): WuXing.WOOD, ('未', '卯'): WuXing.WOOD,
    ('亥', '未'): WuXing.WOOD, ('未', '亥'): WuXing.WOOD,
}


# =============================================================================
# 三会 (SAN_HUI) - Directional Combinations (Seasonal Trios)
# =============================================================================
# Three consecutive branches of the same season/direction

SAN_HUI_TRIOS: Dict[FrozenSet[str], WuXing] = {
    frozenset({'寅', '卯', '辰'}): WuXing.WOOD,   # 东方木 (Spring)
    frozenset({'巳', '午', '未'}): WuXing.FIRE,   # 南方火 (Summer)
    frozenset({'申', '酉', '戌'}): WuXing.METAL,  # 西方金 (Autumn)
    frozenset({'亥', '子', '丑'}): WuXing.WATER,  # 北方水 (Winter)
}


# =============================================================================
# 刑 (XING) - Punishments
# =============================================================================

# 三刑 (SAN_XING) - Three-way Punishments
XING_TRIOS: Dict[FrozenSet[str], str] = {
    frozenset({'寅', '巳', '申'}): '无恩之刑',  # Ungrateful punishment
    frozenset({'丑', '戌', '未'}): '持势之刑',  # Bullying punishment
}

# 相刑 (XIANG_XING) - Mutual Punishments (pairs)
XING_PAIRS: FrozenSet[Tuple[str, str]] = frozenset([
    # 无礼之刑 - Disrespectful punishment
    ('子', '卯'), ('卯', '子'),
    # 寅巳申三刑的两两组合
    ('寅', '巳'), ('巳', '寅'),
    ('巳', '申'), ('申', '巳'),
    ('寅', '申'), ('申', '寅'),
    # 丑戌未三刑的两两组合
    ('丑', '戌'), ('戌', '丑'),
    ('戌', '未'), ('未', '戌'),
    ('丑', '未'), ('未', '丑'),
])

# 自刑 (ZI_XING) - Self Punishments
ZI_XING: FrozenSet[str] = frozenset({'辰', '午', '酉', '亥'})


# =============================================================================
# 害 (HAI) - Harms (Six Harms)
# =============================================================================
# Branches that harm each other (破坏六合)

HAI_PAIRS: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '未'), ('未', '子'),
    ('丑', '午'), ('午', '丑'),
    ('寅', '巳'), ('巳', '寅'),
    ('卯', '辰'), ('辰', '卯'),
    ('申', '亥'), ('亥', '申'),
    ('酉', '戌'), ('戌', '酉'),
])


# =============================================================================
# 破 (PO) - Breaks (Six Breaks)
# =============================================================================
# Branches that break each other

PO_PAIRS: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '酉'), ('酉', '子'),
    ('卯', '午'), ('午', '卯'),
    ('寅', '亥'), ('亥', '寅'),
    ('巳', '申'), ('申', '巳'),
    ('辰', '丑'), ('丑', '辰'),
    ('戌', '未'), ('未', '戌'),
])


# =============================================================================
# Helper Functions
# =============================================================================

def get_san_he_element(branches: List[str]) -> WuXing | None:
    """
    Check if branches form a complete 三合 (Three Harmony).

    Args:
        branches: List of branch characters

    Returns:
        The resulting WuXing element if complete 三合, None otherwise
    """
    branch_set = frozenset(branches)
    for trio, element in SAN_HE_TRIOS.items():
        if trio.issubset(branch_set):
            return element
    return None


def get_ban_he_element(zhi1: str, zhi2: str) -> WuXing | None:
    """
    Check if two branches form a 半合 (Half Harmony).

    Args:
        zhi1: First branch character
        zhi2: Second branch character

    Returns:
        The resulting WuXing element if 半合, None otherwise
    """
    return SAN_HE_PAIRS.get((zhi1, zhi2))


def get_san_hui_element(branches: List[str]) -> WuXing | None:
    """
    Check if branches form a complete 三会 (Directional Combination).

    Args:
        branches: List of branch characters

    Returns:
        The resulting WuXing element if complete 三会, None otherwise
    """
    branch_set = frozenset(branches)
    for trio, element in SAN_HUI_TRIOS.items():
        if trio.issubset(branch_set):
            return element
    return None


def is_xing(zhi1: str, zhi2: str) -> bool:
    """
    Check if two branches form a 刑 (Punishment) relationship.

    Args:
        zhi1: First branch character
        zhi2: Second branch character

    Returns:
        True if the pair forms a punishment relationship
    """
    return (zhi1, zhi2) in XING_PAIRS


def is_zi_xing(zhi: str) -> bool:
    """
    Check if a branch is a 自刑 (Self-Punishment) branch.

    Args:
        zhi: Branch character

    Returns:
        True if the branch can self-punish
    """
    return zhi in ZI_XING


def has_zi_xing(branches: List[str]) -> bool:
    """
    Check if there are duplicate self-punishment branches.

    Args:
        branches: List of branch characters

    Returns:
        True if any self-punishment branch appears more than once
    """
    for zhi in ZI_XING:
        if branches.count(zhi) >= 2:
            return True
    return False


def is_hai(zhi1: str, zhi2: str) -> bool:
    """
    Check if two branches form a 害 (Harm) relationship.

    Args:
        zhi1: First branch character
        zhi2: Second branch character

    Returns:
        True if the pair forms a harm relationship
    """
    return (zhi1, zhi2) in HAI_PAIRS


def is_po(zhi1: str, zhi2: str) -> bool:
    """
    Check if two branches form a 破 (Break) relationship.

    Args:
        zhi1: First branch character
        zhi2: Second branch character

    Returns:
        True if the pair forms a break relationship
    """
    return (zhi1, zhi2) in PO_PAIRS


def get_san_xing_type(branches: List[str]) -> str | None:
    """
    Check if branches form a complete 三刑 (Three-way Punishment).

    Args:
        branches: List of branch characters

    Returns:
        The punishment type name if complete 三刑, None otherwise
    """
    branch_set = frozenset(branches)
    for trio, xing_type in XING_TRIOS.items():
        if trio.issubset(branch_set):
            return xing_type
    return None
