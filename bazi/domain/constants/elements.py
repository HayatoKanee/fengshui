"""
Five Elements (WuXing) Domain Constants.

Domain-level constants for WuXing (五行) element mappings.
These are fundamental BaZi concepts for element calculations.
"""
from typing import Dict, FrozenSet, Tuple

# 天干五行 - Heavenly Stems to WuXing
GAN_WUXING: Dict[str, str] = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

# 地支五行 - Earthly Branches to WuXing
ZHI_WUXING: Dict[str, str] = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水',
}

# 干支五行 - Combined Stems and Branches to WuXing
GANZHI_WUXING: Dict[str, str] = {**GAN_WUXING, **ZHI_WUXING}

# 天干阴阳 - Heavenly Stems Yin/Yang
GAN_YINYANG: Dict[str, str] = {
    '甲': '阳', '乙': '阴',
    '丙': '阳', '丁': '阴',
    '戊': '阳', '己': '阴',
    '庚': '阳', '辛': '阴',
    '壬': '阳', '癸': '阴',
}

# 五行列表
WUXING_LIST: FrozenSet[str] = frozenset(['木', '火', '土', '金', '水'])


def get_stem_wuxing(stem: str) -> str:
    """Get WuXing element for a Heavenly Stem."""
    return GAN_WUXING.get(stem, '')


def get_branch_wuxing(branch: str) -> str:
    """Get WuXing element for an Earthly Branch."""
    return ZHI_WUXING.get(branch, '')


def get_stem_yinyang(stem: str) -> str:
    """Get Yin/Yang polarity for a Heavenly Stem."""
    return GAN_YINYANG.get(stem, '')


# 时辰 - Chinese Hours (Shichen)
# Mapping from hour number to (name, time_range, earthly_branch)
HOUR_INFO: Dict[int, Tuple[str, str, str]] = {
    0: ("子时", "23:00-01:00", "子"),   # Zi hour (late night)
    1: ("丑时", "01:00-03:00", "丑"),   # Chou hour
    3: ("寅时", "03:00-05:00", "寅"),   # Yin hour
    5: ("卯时", "05:00-07:00", "卯"),   # Mao hour
    7: ("辰时", "07:00-09:00", "辰"),   # Chen hour
    9: ("巳时", "09:00-11:00", "巳"),   # Si hour
    11: ("午时", "11:00-13:00", "午"),  # Wu hour
    13: ("未时", "13:00-15:00", "未"),  # Wei hour
    15: ("申时", "15:00-17:00", "申"),  # Shen hour
    17: ("酉时", "17:00-19:00", "酉"),  # You hour
    19: ("戌时", "19:00-21:00", "戌"),  # Xu hour
    21: ("亥时", "21:00-23:00", "亥"),  # Hai hour
    23: ("子时", "23:00-01:00", "子"),  # Zi hour (early part)
}

# List of valid zodiac hours
ZODIAC_HOURS: Tuple[int, ...] = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21)


def get_hour_name(hour: int) -> str:
    """Get Chinese hour name for a given hour number."""
    info = HOUR_INFO.get(hour)
    return info[0] if info else ""


def get_hour_time_range(hour: int) -> str:
    """Get time range for a given hour number."""
    info = HOUR_INFO.get(hour)
    return info[1] if info else ""


def get_hour_branch(hour: int) -> str:
    """Get earthly branch for a given hour number."""
    info = HOUR_INFO.get(hour)
    return info[2] if info else ""


def get_hour_display(hour: int) -> str:
    """Get display string for a given hour (name + time range)."""
    info = HOUR_INFO.get(hour)
    if info:
        return f"{info[0]} ({info[1]})"
    return ""
