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

# 红艳煞 - Red Romance Star
HONG_YAN_SHA: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '午'), ('乙', '午'), ('丙', '寅'), ('戊', '辰'),
    ('丁', '未'), ('己', '辰'), ('庚', '戌'), ('辛', '酉'),
    ('壬', '子'), ('癸', '申'),
])

# 将星 - General Star
JIANG_XING: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '子'), ('午', '午'),
    ('丑', '酉'), ('未', '卯'),
    ('寅', '午'), ('申', '子'),
    ('卯', '卯'), ('酉', '酉'),
    ('辰', '子'), ('戌', '午'),
    ('巳', '酉'), ('亥', '卯'),
])

# 华盖 - Canopy Star
HUA_GAI: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '辰'), ('午', '戌'),
    ('丑', '丑'), ('未', '未'),
    ('寅', '戌'), ('申', '辰'),
    ('卯', '未'), ('酉', '丑'),
    ('辰', '辰'), ('戌', '戌'),
    ('巳', '丑'), ('亥', '未'),
])

# 驿马 - Post Horse Star
YI_MA: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '寅'), ('午', '申'),
    ('丑', '亥'), ('未', '巳'),
    ('寅', '申'), ('申', '寅'),
    ('卯', '巳'), ('酉', '亥'),
    ('辰', '寅'), ('戌', '申'),
    ('巳', '亥'), ('亥', '巳'),
])

# 劫煞 - Robbery Star
JIE_SHA: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '巳'), ('丑', '寅'), ('寅', '亥'), ('卯', '申'),
    ('辰', '巳'), ('巳', '寅'), ('午', '亥'), ('未', '申'),
    ('申', '巳'), ('酉', '寅'), ('戌', '亥'), ('亥', '申'),
])

# 亡神 - Death Spirit Star
WANG_SHEN: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '亥'), ('丑', '申'), ('寅', '巳'), ('卯', '寅'),
    ('辰', '亥'), ('巳', '申'), ('午', '巳'), ('未', '寅'),
    ('申', '亥'), ('酉', '申'), ('戌', '巳'), ('亥', '寅'),
])

# 孤辰 - Lone Star (Male Loneliness)
GU_CHEN: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '寅'), ('丑', '寅'), ('寅', '巳'), ('卯', '巳'),
    ('辰', '巳'), ('巳', '申'), ('午', '申'), ('未', '申'),
    ('申', '亥'), ('酉', '亥'), ('戌', '亥'), ('亥', '寅'),
])

# 寡宿 - Widowhood Star (Female Loneliness)
GUA_SU: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '戌'), ('丑', '戌'), ('寅', '丑'), ('卯', '丑'),
    ('辰', '丑'), ('巳', '辰'), ('午', '辰'), ('未', '辰'),
    ('申', '未'), ('酉', '未'), ('戌', '未'), ('亥', '戌'),
])

# 空亡（旬空）- Void/Emptiness (by day pillar)
XUN_KONG: dict[str, list[str]] = {
    # 甲子旬空戌亥
    '甲子': ['戌', '亥'], '乙丑': ['戌', '亥'], '丙寅': ['戌', '亥'], '丁卯': ['戌', '亥'],
    '戊辰': ['戌', '亥'], '己巳': ['戌', '亥'], '庚午': ['戌', '亥'], '辛未': ['戌', '亥'],
    '壬申': ['戌', '亥'], '癸酉': ['戌', '亥'],
    # 甲戌旬空申酉
    '甲戌': ['申', '酉'], '乙亥': ['申', '酉'], '丙子': ['申', '酉'], '丁丑': ['申', '酉'],
    '戊寅': ['申', '酉'], '己卯': ['申', '酉'], '庚辰': ['申', '酉'], '辛巳': ['申', '酉'],
    '壬午': ['申', '酉'], '癸未': ['申', '酉'],
    # 甲申旬空午未
    '甲申': ['午', '未'], '乙酉': ['午', '未'], '丙戌': ['午', '未'], '丁亥': ['午', '未'],
    '戊子': ['午', '未'], '己丑': ['午', '未'], '庚寅': ['午', '未'], '辛卯': ['午', '未'],
    '壬辰': ['午', '未'], '癸巳': ['午', '未'],
    # 甲午旬空辰巳
    '甲午': ['辰', '巳'], '乙未': ['辰', '巳'], '丙申': ['辰', '巳'], '丁酉': ['辰', '巳'],
    '戊戌': ['辰', '巳'], '己亥': ['辰', '巳'], '庚子': ['辰', '巳'], '辛丑': ['辰', '巳'],
    '壬寅': ['辰', '巳'], '癸卯': ['辰', '巳'],
    # 甲辰旬空寅卯
    '甲辰': ['寅', '卯'], '乙巳': ['寅', '卯'], '丙午': ['寅', '卯'], '丁未': ['寅', '卯'],
    '戊申': ['寅', '卯'], '己酉': ['寅', '卯'], '庚戌': ['寅', '卯'], '辛亥': ['寅', '卯'],
    '壬子': ['寅', '卯'], '癸丑': ['寅', '卯'],
    # 甲寅旬空子丑
    '甲寅': ['子', '丑'], '乙卯': ['子', '丑'], '丙辰': ['子', '丑'], '丁巳': ['子', '丑'],
    '戊午': ['子', '丑'], '己未': ['子', '丑'], '庚申': ['子', '丑'], '辛酉': ['子', '丑'],
    '壬戌': ['子', '丑'], '癸亥': ['子', '丑'],
}


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
