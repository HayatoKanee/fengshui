"""
ShenSha (神煞) Stars Domain Constants.

Domain-level constants for auspicious and inauspicious stars
used in day selection and chart analysis.
"""
from typing import FrozenSet, Tuple

# 天乙贵人 - Heavenly Noble (Gui Ren)
GUI_REN: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '丑'), ('戊', '丑'), ('庚', '丑'),
    ('甲', '未'), ('戊', '未'), ('庚', '未'),
    ('乙', '子'), ('己', '子'), ('乙', '申'), ('己', '申'),
    ('丙', '亥'), ('丁', '亥'), ('丙', '酉'), ('丁', '酉'),
    ('壬', '卯'), ('癸', '卯'), ('壬', '巳'), ('癸', '巳'),
    ('辛', '午'), ('辛', '寅'),
])

# 天德 - Heaven Virtue
TIAN_DE: FrozenSet[Tuple[str, str]] = frozenset([
    ('寅', '丁'), ('卯', '申'), ('辰', '壬'), ('巳', '辛'),
    ('午', '亥'), ('未', '甲'), ('申', '癸'), ('酉', '寅'),
    ('戌', '丙'), ('亥', '乙'), ('子', '巳'), ('丑', '庚'),
])

# 月德 - Month Virtue
YUE_DE: FrozenSet[Tuple[str, str]] = frozenset([
    ('寅', '丙'), ('卯', '甲'), ('辰', '壬'), ('巳', '庚'),
    ('午', '丙'), ('未', '申'), ('申', '壬'), ('酉', '庚'),
    ('戌', '丙'), ('亥', '甲'), ('子', '壬'), ('丑', '庚'),
])

# 文昌 - Literary Star
WEN_CHANG: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '巳'), ('乙', '午'), ('丙', '申'), ('丁', '酉'),
    ('戊', '申'), ('己', '酉'), ('庚', '亥'), ('辛', '子'),
    ('壬', '寅'), ('癸', '卯'),
])

# 禄神 - Prosperity Star
LU_SHEN: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '寅'), ('乙', '卯'), ('丙', '巳'), ('戊', '巳'),
    ('丁', '午'), ('己', '午'), ('庚', '申'), ('辛', '酉'),
    ('壬', '亥'), ('癸', '子'),
])

# 羊刃 - Goat Blade
YANG_REN: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '卯'), ('乙', '辰'), ('丙', '午'), ('戊', '午'),
    ('丁', '未'), ('己', '未'), ('庚', '酉'), ('辛', '戌'),
    ('壬', '子'), ('癸', '丑'),
])

# 桃花 - Peach Blossom (Romance Star)
TAO_HUA: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '酉'), ('丑', '午'), ('寅', '卯'), ('卯', '子'),
    ('辰', '酉'), ('巳', '午'), ('午', '卯'), ('未', '子'),
    ('申', '酉'), ('酉', '午'), ('戌', '卯'), ('亥', '子'),
])


def has_gui_ren(day_gan: str, target_zhi: str) -> bool:
    """Check if day stem and target branch form Gui Ren relationship."""
    return (day_gan, target_zhi) in GUI_REN


def has_tian_de(month_zhi: str, target_gan: str) -> bool:
    """Check if month branch and target stem form Tian De relationship."""
    return (month_zhi, target_gan) in TIAN_DE


def has_yue_de(month_zhi: str, target_gan: str) -> bool:
    """Check if month branch and target stem form Yue De relationship."""
    return (month_zhi, target_gan) in YUE_DE


def has_wen_chang(day_gan: str, target_zhi: str) -> bool:
    """Check if day stem and target branch form Wen Chang relationship."""
    return (day_gan, target_zhi) in WEN_CHANG
