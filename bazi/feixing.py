# --- Dictionaries defining flight codes and fixed grid positions ---

# Mapping each star to its flight method:
# 阳星 (e.g. '乾', '巽', ...) → 'f' (forward, 顺飞)
# 阴星 (e.g. '子', '午', ...) → 'r' (reverse, 逆飞)
star_to_flight = {
    # 阳星 → 'f'
    '乾': 'f', '巽': 'f', '艮': 'f', '坤': 'f',
    '寅': 'f', '申': 'f', '巳': 'f', '亥': 'f',
    '甲': 'f', '庚': 'f', '丙': 'f', '壬': 'f',

    # 阴星 → 'r'
    '子': 'r', '午': 'r', '卯': 'r', '酉': 'r',
    '辰': 'r', '戌': 'r', '丑': 'r', '未': 'r',
    '乙': 'r', '辛': 'r', '丁': 'r', '癸': 'r'
}


# Fixed positions for each star in the 3×3 grid.
# Coordinates are given as (row, col) with 0-indexing:
fixed_positions = {
    # ───────── Top-left corner (0,0) ─────────
    '巽': (0, 0), '辰': (0, 0), '巳': (0, 0),
    # ───────── Top-center (0,1) ─────────
    '丙': (0, 1), '午': (0, 1), '丁': (0, 1),
    # ───────── Top-right corner (0,2) ─────────
    '坤': (0, 2), '未': (0, 2), '申': (0, 2),
    # ───────── Middle-left (1,0) ─────────
    '甲': (1, 0), '卯': (1, 0), '乙': (1, 0),
    # Middle cell (1,1) is used as the grid center (大运中心)
    # ───────── Middle-right (1,2) ─────────
    '庚': (1, 2), '酉': (1, 2), '辛': (1, 2),
    # ───────── Bottom-left corner (2,0) ─────────
    '艮': (2, 0), '丑': (2, 0), '寅': (2, 0),
    # ───────── Bottom-center (2,1) ─────────
    '壬': (2, 1), '子': (2, 1), '癸': (2, 1),
    # ───────── Bottom-right corner (2,2) ─────────
    '乾': (2, 2), '戌': (2, 2), '亥': (2, 2)
}


yuan_pan = [
    [4, 9, 2],
    [3, 5, 7],
    [8, 1, 6]
]
yuan_map = {}
for r in range(3):
    for c in range(3):
        digit = yuan_pan[r][c]
        yuan_map[digit] = (r, c)
yuan_long_mapping = {
    '乾': '天', '巽': '天', '艮': '天', '坤': '天',
    '寅': '人', '申': '人', '巳': '人', '亥': '人',
    '甲': '地', '庚': '地', '丙': '地', '壬': '地',

    # 阴星 → 'r'
    '子': '天', '午': '天', '卯': '天', '酉': '天',
    '辰': '地', '戌': '地', '丑': '地', '未': '地',
    '乙': '人', '辛': '人', '丁': '人', '癸': '人'
}
# --- The grid-generation function ---

def generate_grid(center, order='f'):
    """
    Generate a 3×3 grid using:
       - center: the middle number (1-9)
       - order: 'f' for forward (顺飞) or 'r' for reverse (逆飞).

    The eight outer cells are computed with fixed offsets using the formula:
         ((center - 1 - offset) % 9) + 1

    When center=9, the forward order (顺飞) grid is:
         8 4 6
         7 9 2
         3 5 1

    For reverse (逆飞), the offsets are taken in reverse order.
    """
    # Validate center digit
    if not (1 <= center <= 9):
        raise ValueError("Center must be between 1 and 9.")

    # The order of positions for the eight outer cells:
    positions = [
        (0, 0),  # top-left
        (0, 1),  # top-center
        (0, 2),  # top-right
        (1, 0),  # middle-left
        (1, 2),  # middle-right
        (2, 0),  # bottom-left
        (2, 1),  # bottom-center
        (2, 2)  # bottom-right
    ]

    # Fixed offsets for forward order.
    forward_offsets = [1, 5, 3, 2, 7, 6, 4, 8]

    # Select offsets based on the specified flight order:
    if order == 'f':
        offsets = forward_offsets
    elif order == 'r':
        offsets = forward_offsets[::-1]
    else:
        raise ValueError("Order must be 'f' (forward) or 'r' (reverse).")

    # Create an empty 3×3 grid (initialize with zeros)
    grid = [[0 for _ in range(3)] for _ in range(3)]

    # Set the center cell
    grid[1][1] = center

    # Fill the outer cells using the offsets:
    for (r, c), offset in zip(positions, offsets):
        grid[r][c] = ((center - 1 - offset) % 9) + 1

    return grid


def print_grid(grid):
    """Utility function to neatly print a 3×3 grid."""
    for row in grid:
        print(" ".join(str(x) for x in row))


# --- Main Logic for Generating All Charts (大运 and 小运) ---
def get_keys_from_value(d, target_value):
    """
    Return a list of keys from dictionary `d` that have the value `target_value`.
    """
    return [key for key, value in d.items() if value == target_value]

def get_flight(number,yuan_long):
    stars = get_keys_from_value(fixed_positions, yuan_map[number])
    for s in stars:
        if yuan_long_mapping[s] == yuan_long:
            return star_to_flight[s]

def arabic_to_chinese(num):
    """Convert an Arabic numeral (1–9) to a Chinese numeral."""
    mapping = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
               6: "六", 7: "七", 8: "八", 9: "九"}
    return mapping.get(num, str(num))