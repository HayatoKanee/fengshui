"""
Special Pattern (格局) Analysis Model.

Domain model for BaZi special patterns including:
- 从格 (Following Patterns)
- 专旺格 (Dominant Patterns)
- 化格 (Transformation Patterns)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .elements import WuXing


class PatternCategory(Enum):
    """Categories of special patterns."""
    CONG_GE = "从格"           # Following patterns (weak day master)
    ZHUAN_WANG = "专旺格"       # Dominant patterns (one element rules)
    HUA_GE = "化格"            # Transformation patterns
    NORMAL = "普通格局"         # Normal pattern (no special)


class PatternType(Enum):
    """Specific pattern types."""
    # 从格 - Following Patterns (日主极弱)
    CONG_CAI = "从财格"         # Following Wealth
    CONG_GUAN = "从官格"        # Following Authority (正官)
    CONG_SHA = "从杀格"         # Following Power (七杀)
    CONG_ER = "从儿格"          # Following Output (食伤)
    CONG_SHI = "从势格"         # Following Momentum (mixed)

    # 专旺格 - Dominant Patterns (一行独旺)
    QU_ZHI = "曲直格"           # Wood dominant (曲直仁寿格)
    YAN_SHANG = "炎上格"        # Fire dominant
    JIA_SE = "稼穑格"           # Earth dominant
    CONG_GE_METAL = "从革格"    # Metal dominant
    RUN_XIA = "润下格"          # Water dominant

    # 化格 - Transformation Patterns
    HUA_TU = "化土格"           # 甲己化土
    HUA_JIN = "化金格"          # 乙庚化金
    HUA_SHUI = "化水格"         # 丙辛化水
    HUA_MU = "化木格"           # 丁壬化木
    HUA_HUO = "化火格"          # 戊癸化火

    # 普通
    NORMAL = "普通格局"


# 专旺格对应的五行和日干要求
# 根据《子平真诠》《三命通会》等古籍，月令是专旺格成格的关键条件
ZHUAN_WANG_REQUIREMENTS = {
    PatternType.QU_ZHI: {
        'element': WuXing.WOOD,
        'day_stems': ['甲', '乙'],
        # 曲直格：生于春季(寅卯)或亥子月(水生木)，木气得令
        'valid_months': ['寅', '卯', '辰', '亥', '子'],
        # 木方局地支
        'element_branches': ['寅', '卯', '辰'],
        'name': '曲直格',
        'description': '木气专旺，仁寿之格',
    },
    PatternType.YAN_SHANG: {
        'element': WuXing.FIRE,
        'day_stems': ['丙', '丁'],
        # 炎上格：生于夏季(巳午)或寅卯月(木生火)
        'valid_months': ['巳', '午', '未', '寅', '卯'],
        # 火方局地支
        'element_branches': ['巳', '午', '未'],
        'name': '炎上格',
        'description': '火气专旺，文明之象',
    },
    PatternType.JIA_SE: {
        'element': WuXing.EARTH,
        'day_stems': ['戊', '己'],
        # 稼穑格：生于四季月(辰戌丑未)，土旺月
        'valid_months': ['辰', '戌', '丑', '未'],
        # 四库(土)地支
        'element_branches': ['辰', '戌', '丑', '未'],
        'name': '稼穑格',
        'description': '土气专旺，厚重之德',
    },
    PatternType.CONG_GE_METAL: {
        'element': WuXing.METAL,
        'day_stems': ['庚', '辛'],
        # 从革格：生于秋季(申酉)或四季土月(土生金)
        'valid_months': ['申', '酉', '戌', '丑', '辰', '未'],
        # 金方局地支
        'element_branches': ['申', '酉', '戌'],
        'name': '从革格',
        'description': '金气专旺，刚毅之质',
    },
    PatternType.RUN_XIA: {
        'element': WuXing.WATER,
        'day_stems': ['壬', '癸'],
        # 润下格：生于冬季(亥子)或申酉月(金生水)
        'valid_months': ['亥', '子', '丑', '申', '酉'],
        # 水方局地支
        'element_branches': ['亥', '子', '丑'],
        'name': '润下格',
        'description': '水气专旺，智慧之源',
    },
}

# 化格对应的天干组合和化出五行
# 根据《渊海子平》《三命通会》等古籍，化格需满足：
# 1. 日干与邻干(月干或时干)相合
# 2. 月令为化神旺相之地
# 3. 命局化神有力，无克神破化
# 4. 辰时为"逢龙而化"，更易成格
HUA_GE_COMBINATIONS = {
    ('甲', '己'): {
        'element': WuXing.EARTH,
        'type': PatternType.HUA_TU,
        'name': '甲己化土',
        # 化土需四季月(土旺)
        'valid_months': ['辰', '戌', '丑', '未'],
    },
    ('乙', '庚'): {
        'element': WuXing.METAL,
        'type': PatternType.HUA_JIN,
        'name': '乙庚化金',
        # 化金需秋季(金旺)
        'valid_months': ['申', '酉'],
    },
    ('丙', '辛'): {
        'element': WuXing.WATER,
        'type': PatternType.HUA_SHUI,
        'name': '丙辛化水',
        # 化水需冬季(水旺)
        'valid_months': ['亥', '子'],
    },
    ('丁', '壬'): {
        'element': WuXing.WOOD,
        'type': PatternType.HUA_MU,
        'name': '丁壬化木',
        # 化木需春季(木旺)
        'valid_months': ['寅', '卯'],
    },
    ('戊', '癸'): {
        'element': WuXing.FIRE,
        'type': PatternType.HUA_HUO,
        'name': '戊癸化火',
        # 化火需夏季(火旺)
        'valid_months': ['巳', '午'],
    },
}


@dataclass(frozen=True)
class SpecialPattern:
    """A detected special pattern."""
    pattern_type: PatternType
    category: PatternCategory
    element: Optional[WuXing] = None  # The dominant/transformed element
    strength: float = 0.0             # Pattern strength (0-1)
    description: str = ""
    conditions_met: List[str] = field(default_factory=list)
    conditions_failed: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Whether the pattern is fully valid."""
        return self.strength >= 0.7 and len(self.conditions_failed) == 0

    @property
    def is_partial(self) -> bool:
        """Whether the pattern is partially formed."""
        return 0.4 <= self.strength < 0.7


@dataclass
class PatternAnalysis:
    """
    Complete pattern analysis result.

    Contains detected special patterns and their characteristics.
    """
    # Primary pattern (strongest/most valid)
    primary_pattern: Optional[SpecialPattern] = None

    # All detected patterns (including partial)
    detected_patterns: List[SpecialPattern] = field(default_factory=list)

    # Analysis metadata
    day_master_strength: float = 0.5  # 0=极弱, 1=极强
    dominant_element: Optional[WuXing] = None
    dominant_element_ratio: float = 0.0

    @property
    def has_special_pattern(self) -> bool:
        """Whether a valid special pattern exists."""
        return self.primary_pattern is not None and self.primary_pattern.is_valid

    @property
    def is_cong_ge(self) -> bool:
        """Whether this is a 从格 (following pattern)."""
        return (
            self.primary_pattern is not None
            and self.primary_pattern.category == PatternCategory.CONG_GE
        )

    @property
    def is_zhuan_wang(self) -> bool:
        """Whether this is a 专旺格 (dominant pattern)."""
        return (
            self.primary_pattern is not None
            and self.primary_pattern.category == PatternCategory.ZHUAN_WANG
        )

    @property
    def is_hua_ge(self) -> bool:
        """Whether this is a 化格 (transformation pattern)."""
        return (
            self.primary_pattern is not None
            and self.primary_pattern.category == PatternCategory.HUA_GE
        )

    def get_pattern_description(self) -> str:
        """Get a human-readable description of the pattern."""
        if not self.has_special_pattern:
            return "普通格局，按正常旺衰论命"

        pattern = self.primary_pattern
        if pattern.category == PatternCategory.CONG_GE:
            return f"{pattern.pattern_type.value}：日主极弱无根，从其所向。{pattern.description}"
        elif pattern.category == PatternCategory.ZHUAN_WANG:
            return f"{pattern.pattern_type.value}：{pattern.description}"
        elif pattern.category == PatternCategory.HUA_GE:
            return f"{pattern.pattern_type.value}：天干相合化气成功。{pattern.description}"

        return pattern.description

    def get_favorable_advice(self) -> List[str]:
        """Get advice based on the pattern."""
        advice = []

        if not self.has_special_pattern:
            return ["按日主旺衰取用神"]

        pattern = self.primary_pattern

        if pattern.category == PatternCategory.CONG_GE:
            advice.append("从格宜顺不宜逆")
            advice.append(f"喜{pattern.element.value if pattern.element else '所从之神'}，忌比劫印绶")
            if pattern.pattern_type == PatternType.CONG_CAI:
                advice.append("从财格喜财官食伤，忌比劫")
            elif pattern.pattern_type == PatternType.CONG_GUAN:
                advice.append("从官格喜官印，忌伤官")
            elif pattern.pattern_type == PatternType.CONG_SHA:
                advice.append("从杀格喜杀印，忌食伤制杀")
            elif pattern.pattern_type == PatternType.CONG_ER:
                advice.append("从儿格喜食伤生财，忌印绶夺食")

        elif pattern.category == PatternCategory.ZHUAN_WANG:
            advice.append("专旺格气势专一")
            if pattern.element:
                advice.append(f"喜{pattern.element.value}及其所生之物")
                advice.append(f"忌克{pattern.element.value}之物破格")

        elif pattern.category == PatternCategory.HUA_GE:
            advice.append("化格贵在化气纯粹")
            if pattern.element:
                advice.append(f"喜{pattern.element.value}旺相之地")
                advice.append("忌化神被克破格")

        return advice
