"""
Special Pattern (格局) Analyzer Service.

Analyzes BaZi charts for special patterns including:
- 从格 (Following Patterns)
- 专旺格 (Dominant Patterns)
- 化格 (Transformation Patterns)

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set, TYPE_CHECKING

from ..models.pattern_analysis import (
    PatternCategory,
    PatternType,
    SpecialPattern,
    PatternAnalysis,
    ZHUAN_WANG_REQUIREMENTS,
    HUA_GE_COMBINATIONS,
)
from ..models.elements import WuXing

if TYPE_CHECKING:
    from ..models import BaZi, HeavenlyStem, EarthlyBranch


# 地支对应的主气五行
ZHI_MAIN_WUXING: Dict[str, WuXing] = {
    '寅': WuXing.WOOD, '卯': WuXing.WOOD,
    '巳': WuXing.FIRE, '午': WuXing.FIRE,
    '辰': WuXing.EARTH, '戌': WuXing.EARTH, '丑': WuXing.EARTH, '未': WuXing.EARTH,
    '申': WuXing.METAL, '酉': WuXing.METAL,
    '亥': WuXing.WATER, '子': WuXing.WATER,
}

# 天干对应五行
GAN_WUXING: Dict[str, WuXing] = {
    '甲': WuXing.WOOD, '乙': WuXing.WOOD,
    '丙': WuXing.FIRE, '丁': WuXing.FIRE,
    '戊': WuXing.EARTH, '己': WuXing.EARTH,
    '庚': WuXing.METAL, '辛': WuXing.METAL,
    '壬': WuXing.WATER, '癸': WuXing.WATER,
}

# 十神对应
SHISHEN_CATEGORIES = {
    'wealth': ['正财', '偏财'],
    'authority': ['正官'],
    'power': ['七杀'],
    'output': ['食神', '伤官'],
    'support': ['正印', '偏印'],
    'peer': ['比肩', '劫财'],
}


class PatternAnalyzer:
    """
    Analyzer for special BaZi patterns (格局).

    Detects:
    - 从格: 从财、从官、从杀、从儿、从势
    - 专旺格: 曲直、炎上、稼穑、从革、润下
    - 化格: 甲己化土、乙庚化金、丙辛化水、丁壬化木、戊癸化火
    """

    def analyze(
        self,
        bazi: BaZi,
        wuxing_values: Optional[Dict[WuXing, float]] = None,
    ) -> PatternAnalysis:
        """
        Analyze BaZi for special patterns.

        Args:
            bazi: The BaZi chart to analyze
            wuxing_values: Pre-calculated WuXing strength values (optional)

        Returns:
            PatternAnalysis with detected patterns
        """
        # Calculate element distribution if not provided
        if wuxing_values is None:
            wuxing_values = self._calculate_wuxing_distribution(bazi)

        # Calculate day master strength ratio
        total = sum(wuxing_values.values())
        day_master_element = bazi.day_master.wuxing
        day_master_value = wuxing_values.get(day_master_element, 0)
        day_master_ratio = day_master_value / total if total > 0 else 0

        # Find dominant element
        dominant_element = max(wuxing_values, key=wuxing_values.get)
        dominant_ratio = wuxing_values[dominant_element] / total if total > 0 else 0

        analysis = PatternAnalysis(
            day_master_strength=day_master_ratio,
            dominant_element=dominant_element,
            dominant_element_ratio=dominant_ratio,
        )

        # Detect patterns in order of priority
        detected = []

        # 1. Check for 化格 (Transformation patterns)
        hua_patterns = self._detect_hua_ge(bazi, wuxing_values)
        detected.extend(hua_patterns)

        # 2. Check for 专旺格 (Dominant patterns)
        zhuan_wang = self._detect_zhuan_wang(bazi, wuxing_values, day_master_ratio)
        detected.extend(zhuan_wang)

        # 3. Check for 从格 (Following patterns) - only if day master is weak
        if day_master_ratio < 0.15:  # Day master very weak
            cong_patterns = self._detect_cong_ge(bazi, wuxing_values, day_master_ratio)
            detected.extend(cong_patterns)

        analysis.detected_patterns = detected

        # Select primary pattern (strongest valid one)
        valid_patterns = [p for p in detected if p.is_valid]
        if valid_patterns:
            analysis.primary_pattern = max(valid_patterns, key=lambda p: p.strength)
        elif detected:
            # Use strongest partial pattern
            partial = [p for p in detected if p.is_partial]
            if partial:
                analysis.primary_pattern = max(partial, key=lambda p: p.strength)

        return analysis

    def _calculate_wuxing_distribution(self, bazi: BaZi) -> Dict[WuXing, float]:
        """Calculate basic WuXing distribution from the chart."""
        values: Dict[WuXing, float] = {e: 0.0 for e in WuXing}

        # Count stems (weight: 1.0)
        for pillar in bazi.pillars:
            stem_wuxing = pillar.stem.wuxing
            values[stem_wuxing] += 1.0

        # Count branches with hidden stems
        for pillar in bazi.pillars:
            for hidden_stem, ratio in pillar.hidden_stems.items():
                values[hidden_stem.wuxing] += ratio

        return values

    def _detect_hua_ge(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
    ) -> List[SpecialPattern]:
        """Detect 化格 (Transformation patterns)."""
        patterns = []

        # Get all stems
        stems = [
            bazi.year_pillar.stem.chinese,
            bazi.month_pillar.stem.chinese,
            bazi.day_pillar.stem.chinese,
            bazi.hour_pillar.stem.chinese,
        ]
        day_stem = bazi.day_pillar.stem.chinese
        month_branch = bazi.month_pillar.branch.chinese

        # Check each combination
        for (gan1, gan2), config in HUA_GE_COMBINATIONS.items():
            # Day stem must be one of the pair
            if day_stem not in (gan1, gan2):
                continue

            # Check if the other stem exists (adjacent to day stem preferred)
            other_gan = gan2 if day_stem == gan1 else gan1
            has_combination = False
            combination_positions = []

            # Check month stem (most important for 化格)
            if stems[1] == other_gan:  # Month stem
                has_combination = True
                combination_positions.append('月干')
            # Check hour stem
            if stems[3] == other_gan:  # Hour stem
                has_combination = True
                combination_positions.append('时干')
            # Check year stem (less powerful)
            if stems[0] == other_gan:
                has_combination = True
                combination_positions.append('年干')

            if not has_combination:
                continue

            # Calculate conditions
            conditions_met = []
            conditions_failed = []
            strength = 0.0

            # Condition 1: Combination exists
            conditions_met.append(f"日干{day_stem}与{','.join(combination_positions)}{other_gan}相合")
            strength += 0.3

            # Condition 2: Month branch supports transformed element
            transform_element = config['element']
            month_element = ZHI_MAIN_WUXING.get(month_branch)

            if month_element == transform_element:
                conditions_met.append(f"月支{month_branch}为{transform_element.value}，化神得令")
                strength += 0.4
            elif month_element and transform_element.generates == month_element:
                conditions_met.append(f"月支{month_branch}泄化神之气")
                strength += 0.1
            else:
                conditions_failed.append(f"月支{month_branch}不助化神{transform_element.value}")

            # Condition 3: Transformed element is strong in chart
            total = sum(wuxing_values.values())
            transform_ratio = wuxing_values.get(transform_element, 0) / total if total > 0 else 0

            if transform_ratio >= 0.3:
                conditions_met.append(f"{transform_element.value}在命局占比{transform_ratio:.0%}，化神有力")
                strength += 0.3
            elif transform_ratio >= 0.2:
                conditions_met.append(f"{transform_element.value}在命局占比{transform_ratio:.0%}")
                strength += 0.15
            else:
                conditions_failed.append(f"{transform_element.value}在命局占比过低({transform_ratio:.0%})")

            pattern = SpecialPattern(
                pattern_type=config['type'],
                category=PatternCategory.HUA_GE,
                element=transform_element,
                strength=min(strength, 1.0),
                description=config['name'],
                conditions_met=conditions_met,
                conditions_failed=conditions_failed,
            )
            patterns.append(pattern)

        return patterns

    def _detect_zhuan_wang(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
        day_master_ratio: float,
    ) -> List[SpecialPattern]:
        """Detect 专旺格 (Dominant patterns)."""
        patterns = []

        day_stem = bazi.day_pillar.stem.chinese
        branches = [
            bazi.year_pillar.branch.chinese,
            bazi.month_pillar.branch.chinese,
            bazi.day_pillar.branch.chinese,
            bazi.hour_pillar.branch.chinese,
        ]

        for pattern_type, config in ZHUAN_WANG_REQUIREMENTS.items():
            # Check day stem requirement
            if day_stem not in config['day_stems']:
                continue

            target_element = config['element']
            conditions_met = []
            conditions_failed = []
            strength = 0.0

            # Condition 1: Day stem matches
            conditions_met.append(f"日干{day_stem}为{target_element.value}")
            strength += 0.2

            # Condition 2: Count branches of target element
            target_branches = [b for b in branches if ZHI_MAIN_WUXING.get(b) == target_element]
            branch_count = len(target_branches)

            if branch_count >= 3:
                conditions_met.append(f"地支有{branch_count}个{target_element.value}支({','.join(target_branches)})")
                strength += 0.4
            elif branch_count >= 2:
                conditions_met.append(f"地支有{branch_count}个{target_element.value}支")
                strength += 0.2
            else:
                conditions_failed.append(f"地支{target_element.value}支不足(仅{branch_count}个)")

            # Condition 3: Element dominance in chart
            total = sum(wuxing_values.values())
            element_ratio = wuxing_values.get(target_element, 0) / total if total > 0 else 0

            if element_ratio >= 0.5:
                conditions_met.append(f"{target_element.value}占命局{element_ratio:.0%}，气势专旺")
                strength += 0.3
            elif element_ratio >= 0.35:
                conditions_met.append(f"{target_element.value}占命局{element_ratio:.0%}")
                strength += 0.15
            else:
                conditions_failed.append(f"{target_element.value}占比不足({element_ratio:.0%})")

            # Condition 4: No strong克神
            ke_element = target_element.overcome_by
            ke_ratio = wuxing_values.get(ke_element, 0) / total if total > 0 else 0

            if ke_ratio < 0.1:
                conditions_met.append(f"克神{ke_element.value}弱({ke_ratio:.0%})")
                strength += 0.1
            else:
                conditions_failed.append(f"克神{ke_element.value}有力({ke_ratio:.0%})，恐破格")

            pattern = SpecialPattern(
                pattern_type=pattern_type,
                category=PatternCategory.ZHUAN_WANG,
                element=target_element,
                strength=min(strength, 1.0),
                description=config['description'],
                conditions_met=conditions_met,
                conditions_failed=conditions_failed,
            )
            patterns.append(pattern)

        return patterns

    def _detect_cong_ge(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
        day_master_ratio: float,
    ) -> List[SpecialPattern]:
        """Detect 从格 (Following patterns)."""
        patterns = []

        day_master_element = bazi.day_master.wuxing
        total = sum(wuxing_values.values())

        # Check for roots (比劫/印绶)
        peer_element = day_master_element
        support_element = day_master_element.generated_by

        peer_ratio = wuxing_values.get(peer_element, 0) / total if total > 0 else 0
        support_ratio = wuxing_values.get(support_element, 0) / total if total > 0 else 0
        has_root = peer_ratio > 0.15 or support_ratio > 0.15

        if has_root:
            # Day master has root, not 从格
            return patterns

        base_conditions = [f"日主{day_master_element.value}极弱({day_master_ratio:.0%})"]

        # Check 从财格
        wealth_element = day_master_element.overcomes
        wealth_ratio = wuxing_values.get(wealth_element, 0) / total if total > 0 else 0

        if wealth_ratio >= 0.3:
            conditions_met = base_conditions.copy()
            conditions_met.append(f"财星{wealth_element.value}旺({wealth_ratio:.0%})")
            strength = 0.5 + (wealth_ratio - 0.3) + (0.15 - day_master_ratio)

            patterns.append(SpecialPattern(
                pattern_type=PatternType.CONG_CAI,
                category=PatternCategory.CONG_GE,
                element=wealth_element,
                strength=min(strength, 1.0),
                description="弃命从财，以财为用",
                conditions_met=conditions_met,
                conditions_failed=[],
            ))

        # Check 从官格
        authority_element = day_master_element.controlled_by
        authority_ratio = wuxing_values.get(authority_element, 0) / total if total > 0 else 0

        if authority_ratio >= 0.25:
            conditions_met = base_conditions.copy()
            conditions_met.append(f"官星{authority_element.value}旺({authority_ratio:.0%})")
            strength = 0.5 + (authority_ratio - 0.25) + (0.15 - day_master_ratio)

            # Distinguish 从官 vs 从杀 based on yin/yang
            # Simplified: if very strong, likely 从杀
            if authority_ratio >= 0.4:
                patterns.append(SpecialPattern(
                    pattern_type=PatternType.CONG_SHA,
                    category=PatternCategory.CONG_GE,
                    element=authority_element,
                    strength=min(strength, 1.0),
                    description="弃命从杀，以杀为用",
                    conditions_met=conditions_met,
                    conditions_failed=[],
                ))
            else:
                patterns.append(SpecialPattern(
                    pattern_type=PatternType.CONG_GUAN,
                    category=PatternCategory.CONG_GE,
                    element=authority_element,
                    strength=min(strength, 1.0),
                    description="弃命从官，以官为用",
                    conditions_met=conditions_met,
                    conditions_failed=[],
                ))

        # Check 从儿格 (食伤)
        output_element = day_master_element.generates
        output_ratio = wuxing_values.get(output_element, 0) / total if total > 0 else 0

        if output_ratio >= 0.3:
            conditions_met = base_conditions.copy()
            conditions_met.append(f"食伤{output_element.value}旺({output_ratio:.0%})")
            strength = 0.5 + (output_ratio - 0.3) + (0.15 - day_master_ratio)

            patterns.append(SpecialPattern(
                pattern_type=PatternType.CONG_ER,
                category=PatternCategory.CONG_GE,
                element=output_element,
                strength=min(strength, 1.0),
                description="从儿格，以食伤为用",
                conditions_met=conditions_met,
                conditions_failed=[],
            ))

        # Check 从势格 (mixed strong elements)
        if not patterns and day_master_ratio < 0.1:
            # No single dominant, but day master is very weak
            dominant = max(wuxing_values, key=wuxing_values.get)
            dominant_ratio = wuxing_values[dominant] / total if total > 0 else 0

            if dominant != day_master_element and dominant != support_element:
                conditions_met = base_conditions.copy()
                conditions_met.append(f"命局{dominant.value}最旺({dominant_ratio:.0%})")
                strength = 0.4 + (0.15 - day_master_ratio)

                patterns.append(SpecialPattern(
                    pattern_type=PatternType.CONG_SHI,
                    category=PatternCategory.CONG_GE,
                    element=dominant,
                    strength=min(strength, 1.0),
                    description="从势格，顺应命局强势",
                    conditions_met=conditions_met,
                    conditions_failed=[],
                ))

        return patterns
