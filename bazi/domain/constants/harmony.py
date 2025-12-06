"""
Harmony Relationships Domain Constants.

Domain-level constants for stem and branch harmony (合) relationships.
These are fundamental BaZi concepts used in analysis calculations.
"""
from typing import FrozenSet, Tuple

# 六合 - Six Harmonies (Branch combinations)
LIU_HE: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '丑'), ('丑', '子'),
    ('寅', '亥'), ('亥', '寅'),
    ('卯', '戌'), ('戌', '卯'),
    ('辰', '酉'), ('酉', '辰'),
    ('巳', '申'), ('申', '巳'),
    ('午', '未'), ('未', '午'),
])

# 五合 - Five Harmonies (Stem combinations)
WU_HE: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '己'), ('己', '甲'),
    ('乙', '庚'), ('庚', '乙'),
    ('丙', '辛'), ('辛', '丙'),
    ('丁', '壬'), ('壬', '丁'),
    ('戊', '癸'), ('癸', '戊'),
])

# 地支藏干比例 - Hidden Stems in Branches
HIDDEN_GAN_RATIOS = {
    '子': {'癸': 1.0},
    '丑': {'己': 0.5, '癸': 0.3, '辛': 0.2},
    '寅': {'甲': 0.6, '丙': 0.3, '戊': 0.1},
    '卯': {'乙': 1.0},
    '辰': {'戊': 0.5, '乙': 0.3, '癸': 0.2},
    '巳': {'丙': 0.6, '戊': 0.3, '庚': 0.1},
    '午': {'丁': 0.5, '己': 0.5},
    '未': {'乙': 0.2, '己': 0.5, '丁': 0.3},
    '申': {'庚': 0.6, '壬': 0.3, '戊': 0.1},
    '酉': {'辛': 1.0},
    '戌': {'戊': 0.5, '辛': 0.3, '丁': 0.2},
    '亥': {'壬': 0.7, '甲': 0.3},
}


def is_harmony(char1: str, char2: str) -> bool:
    """
    Check if two characters form a harmony (合) relationship.

    Checks both Liu He (六合, branch harmonies) and
    Wu He (五合, stem harmonies).

    Args:
        char1: First Chinese character (stem or branch)
        char2: Second Chinese character (stem or branch)

    Returns:
        True if the pair forms a harmony relationship
    """
    pair = (char1, char2)
    return pair in LIU_HE or pair in WU_HE
