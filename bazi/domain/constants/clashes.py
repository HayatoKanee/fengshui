"""
Clash Relationships Domain Constants.

Domain-level constants for stem and branch clash (冲) relationships.
These are used for compatibility and day selection calculations.
"""
from typing import FrozenSet, Tuple

# 天干相冲 - Heavenly Stem Clashes
GAN_XIANG_CHONG: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '庚'), ('庚', '甲'),
    ('乙', '辛'), ('辛', '乙'),
    ('壬', '丙'), ('丙', '壬'),
    ('癸', '丁'), ('丁', '癸'),
])

# 地支相冲 - Earthly Branch Clashes
ZHI_XIANG_CHONG: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '午'), ('午', '子'),
    ('丑', '未'), ('未', '丑'),
    ('寅', '申'), ('申', '寅'),
    ('卯', '酉'), ('酉', '卯'),
    ('辰', '戌'), ('戌', '辰'),
    ('巳', '亥'), ('亥', '巳'),
])

# 五不遇时 - Wu Bu Yu Shi (Five Misfortune Hours)
# Unfavorable day stem + hour branch combinations
WU_BU_YU_SHI: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '午'), ('乙', '巳'), ('丙', '辰'), ('丁', '卯'),
    ('戊', '寅'), ('己', '丑'), ('己', '亥'), ('庚', '子'),
    ('庚', '戌'), ('辛', '酉'), ('壬', '申'), ('癸', '未'),
])


def is_gan_clash(gan1: str, gan2: str) -> bool:
    """Check if two heavenly stems clash."""
    return (gan1, gan2) in GAN_XIANG_CHONG


def is_zhi_clash(zhi1: str, zhi2: str) -> bool:
    """Check if two earthly branches clash."""
    return (zhi1, zhi2) in ZHI_XIANG_CHONG


def is_clash(char1: str, char2: str) -> bool:
    """Check if two characters (stems or branches) clash."""
    pair = (char1, char2)
    return pair in GAN_XIANG_CHONG or pair in ZHI_XIANG_CHONG


def is_wu_bu_yu_shi(day_gan: str, hour_zhi: str) -> bool:
    """Check if day stem and hour branch form Wu Bu Yu Shi."""
    return (day_gan, hour_zhi) in WU_BU_YU_SHI
