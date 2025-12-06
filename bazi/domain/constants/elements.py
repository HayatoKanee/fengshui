"""
Five Elements (WuXing) Domain Constants.

Domain-level constants for WuXing (五行) element mappings.
These are fundamental BaZi concepts for element calculations.
"""
from typing import Dict, FrozenSet

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
