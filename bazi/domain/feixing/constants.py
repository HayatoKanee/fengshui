"""
FeiXing Constants.

Constants for Flying Star Feng Shui calculations including:
- 24 Mountains (compass directions)
- Star flight patterns (Yin/Yang)
- Fixed grid positions
- Yuan Pan (Original Lo Shu grid)
- Yuan Long mappings (Heaven/Human/Earth)
"""
from typing import Dict, Tuple, List

# The 24 Mountains - compass directions in Feng Shui
# Each mountain covers 15 degrees, starting from North (子)
MOUNTAINS_24: List[str] = [
    "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙",
    "辰", "巽", "巳", "丙", "午", "丁", "未", "坤",
    "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬"
]

# Star to flight order mapping
# 阳星 (Yang stars) → 'f' (forward/顺飞)
# 阴星 (Yin stars) → 'r' (reverse/逆飞)
STAR_TO_FLIGHT: Dict[str, str] = {
    # 阳星 → Forward (顺飞)
    '乾': 'f', '巽': 'f', '艮': 'f', '坤': 'f',
    '寅': 'f', '申': 'f', '巳': 'f', '亥': 'f',
    '甲': 'f', '庚': 'f', '丙': 'f', '壬': 'f',
    # 阴星 → Reverse (逆飞)
    '子': 'r', '午': 'r', '卯': 'r', '酉': 'r',
    '辰': 'r', '戌': 'r', '丑': 'r', '未': 'r',
    '乙': 'r', '辛': 'r', '丁': 'r', '癸': 'r',
}

# Fixed positions for each mountain in the 3×3 grid
# Coordinates are (row, col) with 0-indexing
FIXED_POSITIONS: Dict[str, Tuple[int, int]] = {
    # Top-left (0,0) - Southeast
    '巽': (0, 0), '辰': (0, 0), '巳': (0, 0),
    # Top-center (0,1) - South
    '丙': (0, 1), '午': (0, 1), '丁': (0, 1),
    # Top-right (0,2) - Southwest
    '坤': (0, 2), '未': (0, 2), '申': (0, 2),
    # Middle-left (1,0) - East
    '甲': (1, 0), '卯': (1, 0), '乙': (1, 0),
    # Middle-center (1,1) is the grid center
    # Middle-right (1,2) - West
    '庚': (1, 2), '酉': (1, 2), '辛': (1, 2),
    # Bottom-left (2,0) - Northeast
    '艮': (2, 0), '丑': (2, 0), '寅': (2, 0),
    # Bottom-center (2,1) - North
    '壬': (2, 1), '子': (2, 1), '癸': (2, 1),
    # Bottom-right (2,2) - Northwest
    '乾': (2, 2), '戌': (2, 2), '亥': (2, 2),
}

# Original Lo Shu (Yuan Pan) - The base 3×3 magic square
# Sum of each row, column, and diagonal equals 15
YUAN_PAN: List[List[int]] = [
    [4, 9, 2],
    [3, 5, 7],
    [8, 1, 6]
]

# Yuan Pan position mapping: digit → (row, col)
YUAN_MAP: Dict[int, Tuple[int, int]] = {
    digit: (r, c)
    for r in range(3)
    for c in range(3)
    for digit in [YUAN_PAN[r][c]]
}

# Yuan Long mapping: Mountain → 天(Heaven)/人(Human)/地(Earth)
YUAN_LONG_MAPPING: Dict[str, str] = {
    # 阳星 categories
    '乾': '天', '巽': '天', '艮': '天', '坤': '天',
    '寅': '人', '申': '人', '巳': '人', '亥': '人',
    '甲': '地', '庚': '地', '丙': '地', '壬': '地',
    # 阴星 categories
    '子': '天', '午': '天', '卯': '天', '酉': '天',
    '辰': '地', '戌': '地', '丑': '地', '未': '地',
    '乙': '人', '辛': '人', '丁': '人', '癸': '人',
}

# Arabic to Chinese numeral mapping
ARABIC_TO_CHINESE: Dict[int, str] = {
    1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
    6: "六", 7: "七", 8: "八", 9: "九"
}

# Grid generation offsets for outer cells
# Used to calculate values in the 8 outer cells based on center
FORWARD_OFFSETS: List[int] = [1, 5, 3, 2, 7, 6, 4, 8]

# Outer ring positions in clockwise order
OUTER_POSITIONS: List[Tuple[int, int]] = [
    (0, 0), (0, 1), (0, 2),
    (1, 2), (2, 2), (2, 1),
    (2, 0), (1, 0)
]

# Grid generation positions (for filling outer cells)
GRID_POSITIONS: List[Tuple[int, int]] = [
    (0, 0),  # top-left
    (0, 1),  # top-center
    (0, 2),  # top-right
    (1, 0),  # middle-left
    (1, 2),  # middle-right
    (2, 0),  # bottom-left
    (2, 1),  # bottom-center
    (2, 2),  # bottom-right
]
