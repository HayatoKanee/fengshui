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
        """
        Detect 化格 (Transformation patterns).

        根据《渊海子平》《三命通会》等古籍，化格条件极为严苛：
        1. 日干与邻干(月干或时干)相合 - 邻干优先，年干隔位力弱
        2. 月令必须是化神当旺之月 - 此为成化关键
        3. 命局化神有力，无克破
        4. 辰时"逢龙而化"更易成格
        """
        patterns = []

        # Get all stems and branches
        stems = [
            bazi.year_pillar.stem.chinese,
            bazi.month_pillar.stem.chinese,
            bazi.day_pillar.stem.chinese,
            bazi.hour_pillar.stem.chinese,
        ]
        day_stem = bazi.day_pillar.stem.chinese
        month_branch = bazi.month_pillar.branch.chinese
        hour_branch = bazi.hour_pillar.branch.chinese

        # Check each combination
        for (gan1, gan2), config in HUA_GE_COMBINATIONS.items():
            # Day stem must be one of the pair
            if day_stem not in (gan1, gan2):
                continue

            # Check if the other stem exists (adjacent to day stem preferred)
            other_gan = gan2 if day_stem == gan1 else gan1
            has_combination = False
            combination_positions = []
            adjacent_combination = False  # 邻干相合(月干或时干)

            # Check month stem (most important for 化格 - adjacent)
            if stems[1] == other_gan:
                has_combination = True
                adjacent_combination = True
                combination_positions.append('月干')
            # Check hour stem (also adjacent)
            if stems[3] == other_gan:
                has_combination = True
                adjacent_combination = True
                combination_positions.append('时干')
            # Check year stem (less powerful - not adjacent, 隔位)
            if stems[0] == other_gan:
                has_combination = True
                combination_positions.append('年干')

            if not has_combination:
                continue

            # Calculate conditions
            conditions_met = []
            conditions_failed = []
            strength = 0.0

            transform_element = config['element']
            valid_months = config.get('valid_months', [])

            # Condition 1: Combination exists (邻干优先)
            if adjacent_combination:
                conditions_met.append(f"日干{day_stem}与邻干{','.join(combination_positions)}{other_gan}相合")
                strength += 0.25
            else:
                conditions_met.append(f"日干{day_stem}与{','.join(combination_positions)}{other_gan}相合(隔位力弱)")
                strength += 0.10

            # Condition 2: Month branch MUST be transformation element's prosperous month
            # 此为化格成格之关键条件
            if month_branch in valid_months:
                conditions_met.append(f"月支{month_branch}为{transform_element.value}旺月，化神得令")
                strength += 0.35
            else:
                conditions_failed.append(
                    f"月支{month_branch}非{transform_element.value}旺月"
                    f"(需{','.join(valid_months)})，化神不得令，难以成化"
                )
                # Without proper month, 化格 is very difficult to form
                # Still continue to check for partial pattern

            # Condition 3: 逢龙而化 (辰时更易成化)
            if hour_branch == '辰':
                conditions_met.append("时支辰为龙，逢龙而化")
                strength += 0.10

            # Condition 4: Transformed element strength in chart
            total = sum(wuxing_values.values())
            transform_ratio = wuxing_values.get(transform_element, 0) / total if total > 0 else 0

            if transform_ratio >= 0.35:
                conditions_met.append(f"{transform_element.value}在命局占比{transform_ratio:.0%}，化神有力")
                strength += 0.20
            elif transform_ratio >= 0.25:
                conditions_met.append(f"{transform_element.value}在命局占比{transform_ratio:.0%}，化神尚可")
                strength += 0.10
            else:
                conditions_failed.append(f"{transform_element.value}在命局占比{transform_ratio:.0%}，化神无力")

            # Condition 5: No strong 克神 breaking transformation
            ke_element = transform_element.overcome_by
            ke_ratio = wuxing_values.get(ke_element, 0) / total if total > 0 else 0

            if ke_ratio < 0.05:
                conditions_met.append(f"无克神{ke_element.value}破化")
                strength += 0.10
            elif ke_ratio < 0.15:
                conditions_met.append(f"克神{ke_element.value}弱({ke_ratio:.0%})")
                strength += 0.05
            else:
                conditions_failed.append(f"克神{ke_element.value}有力({ke_ratio:.0%})，恐破化")

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
        """
        Detect 专旺格 (Dominant patterns).

        根据《子平真诠》《三命通会》等古籍，专旺格条件：
        1. 日干属该五行
        2. 月令(月支)为该五行得令或生扶之月
        3. 地支多该五行，成方成局
        4. 无克神破格
        """
        patterns = []

        day_stem = bazi.day_pillar.stem.chinese
        month_branch = bazi.month_pillar.branch.chinese
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
            valid_months = config.get('valid_months', [])
            element_branches = config.get('element_branches', [])
            conditions_met = []
            conditions_failed = []
            strength = 0.0

            # Condition 1: Day stem matches
            conditions_met.append(f"日干{day_stem}为{target_element.value}")
            strength += 0.15

            # Condition 2: Month branch (月令) - CRITICAL for 专旺格
            if month_branch in valid_months:
                # Check if month is the element's own month (得令) vs generating month (有气)
                month_element = ZHI_MAIN_WUXING.get(month_branch)
                if month_element == target_element:
                    conditions_met.append(f"月支{month_branch}为{target_element.value}，得令当旺")
                    strength += 0.25
                else:
                    # Generating month (like 亥子 for wood - water generates wood)
                    conditions_met.append(f"月支{month_branch}生{target_element.value}，有气")
                    strength += 0.15
            else:
                conditions_failed.append(f"月支{month_branch}非{target_element.value}旺相之月，不得月令")
                # Can still continue checking for partial pattern

            # Condition 3: Count element branches forming 方局
            target_branches = [b for b in branches if b in element_branches]
            branch_count = len(target_branches)

            # Also count branches with same main element
            same_element_branches = [b for b in branches if ZHI_MAIN_WUXING.get(b) == target_element]

            if branch_count >= 3:
                # 方局全(如木方局寅卯辰全)
                conditions_met.append(f"地支{','.join(target_branches)}成{target_element.value}方局")
                strength += 0.30
            elif len(same_element_branches) >= 3:
                conditions_met.append(f"地支有{len(same_element_branches)}个{target_element.value}支")
                strength += 0.25
            elif branch_count >= 2 or len(same_element_branches) >= 2:
                conditions_met.append(f"地支有{max(branch_count, len(same_element_branches))}个{target_element.value}支")
                strength += 0.15
            else:
                conditions_failed.append(f"地支{target_element.value}支不足，难成专旺")

            # Condition 4: Element dominance in chart
            total = sum(wuxing_values.values())
            element_ratio = wuxing_values.get(target_element, 0) / total if total > 0 else 0

            if element_ratio >= 0.50:
                conditions_met.append(f"{target_element.value}占命局{element_ratio:.0%}，气势专旺")
                strength += 0.20
            elif element_ratio >= 0.40:
                conditions_met.append(f"{target_element.value}占命局{element_ratio:.0%}，气势较旺")
                strength += 0.10
            else:
                conditions_failed.append(f"{target_element.value}占比{element_ratio:.0%}不足，气势不专")

            # Condition 5: No strong 克神 breaking the pattern
            ke_element = target_element.overcome_by
            ke_ratio = wuxing_values.get(ke_element, 0) / total if total > 0 else 0

            if ke_ratio < 0.05:
                conditions_met.append(f"无克神{ke_element.value}破格")
                strength += 0.10
            elif ke_ratio < 0.10:
                conditions_met.append(f"克神{ke_element.value}弱({ke_ratio:.0%})，不碍格局")
                strength += 0.05
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
        """
        Detect 从格 (Following patterns).

        根据《子平真诠》《渊海子平》《滴天髓》等古籍，从格条件：

        **从格共同条件:**
        1. 日主无根 - 地支藏干无比劫或强印根
        2. 天干无比劫印绶帮身
        3. 所从之神当令或成势

        **从财格:** 日主无根，财星当令成势，无印绶夺财
        **从官格:** 日主无根，正官当令成势，无伤官克官
        **从杀格:** 日主无根，七杀当令成势，无食神制杀(若有可论从杀)
        **从儿格:** 日主无根，食伤当令成势，无枭印夺食
        **从势格:** 日主无根，财官食伤混杂成势
        """
        patterns = []

        day_master_element = bazi.day_master.wuxing
        day_master_yinyang = bazi.day_master.yinyang
        month_branch = bazi.month_pillar.branch.chinese
        total = sum(wuxing_values.values())

        # === Step 1: Check if day master has root (无根检查) ===
        # 日主无根 = 地支藏干中无比劫(同五行)或印绶(生日主)强根
        peer_element = day_master_element  # 比劫
        support_element = day_master_element.generated_by  # 印绶

        # Check stems for 比劫/印绶
        stems_helping = []
        for pillar in bazi.pillars:
            stem_element = pillar.stem.wuxing
            if pillar != bazi.day_pillar:  # Skip day master itself
                if stem_element == peer_element:
                    stems_helping.append(f"{pillar.stem.chinese}(比劫)")
                elif stem_element == support_element:
                    stems_helping.append(f"{pillar.stem.chinese}(印)")

        # Check hidden stems for roots
        hidden_roots = []
        for pillar in bazi.pillars:
            for hidden_stem, ratio in pillar.hidden_stems.items():
                if ratio >= 0.3:  # Only count significant hidden stems (本气或中气)
                    if hidden_stem.wuxing == peer_element:
                        hidden_roots.append(f"{pillar.branch.chinese}藏{hidden_stem.chinese}(比劫)")
                    elif hidden_stem.wuxing == support_element:
                        hidden_roots.append(f"{pillar.branch.chinese}藏{hidden_stem.chinese}(印)")

        has_stem_help = len(stems_helping) > 0
        has_branch_root = len(hidden_roots) > 0

        # If day master has roots, not 从格
        if has_stem_help or has_branch_root:
            return patterns

        # === Step 2: Now check each type of 从格 ===
        base_conditions = ["日主无根(地支无比劫印绶本气根)"]

        # Get month branch element for 当令 check
        month_element = ZHI_MAIN_WUXING.get(month_branch)

        # --- 从财格 ---
        wealth_element = day_master_element.overcomes  # 财星 = 日主所克
        wealth_in_command = (month_element == wealth_element)

        wealth_branches = sum(1 for p in bazi.pillars if ZHI_MAIN_WUXING.get(p.branch.chinese) == wealth_element)
        wealth_stems = sum(1 for p in bazi.pillars if p.stem.wuxing == wealth_element)

        if wealth_in_command or (wealth_branches >= 2 and wealth_stems >= 1):
            conditions_met = base_conditions.copy()
            conditions_failed = []
            strength = 0.5

            if wealth_in_command:
                conditions_met.append(f"财星{wealth_element.value}当令(月支{month_branch})")
                strength += 0.25
            if wealth_branches >= 2:
                conditions_met.append(f"地支有{wealth_branches}个财星{wealth_element.value}支")
                strength += 0.15

            # Check for 印绶 breaking the pattern
            if wuxing_values.get(support_element, 0) / total > 0.1 if total > 0 else False:
                conditions_failed.append(f"有印星{support_element.value}夺财，恐不纯")
                strength -= 0.15
            else:
                conditions_met.append(f"无印星{support_element.value}夺财")
                strength += 0.10

            if not conditions_failed:
                patterns.append(SpecialPattern(
                    pattern_type=PatternType.CONG_CAI,
                    category=PatternCategory.CONG_GE,
                    element=wealth_element,
                    strength=min(max(strength, 0.0), 1.0),
                    description="弃命从财，以财为用",
                    conditions_met=conditions_met,
                    conditions_failed=conditions_failed,
                ))

        # --- 从官格/从杀格 ---
        authority_element = day_master_element.overcome_by  # 官杀 = 克日主
        authority_in_command = (month_element == authority_element)

        authority_branches = sum(1 for p in bazi.pillars if ZHI_MAIN_WUXING.get(p.branch.chinese) == authority_element)
        authority_stems = sum(1 for p in bazi.pillars if p.stem.wuxing == authority_element)

        if authority_in_command or (authority_branches >= 2 and authority_stems >= 1):
            conditions_met = base_conditions.copy()
            conditions_failed = []
            strength = 0.5

            if authority_in_command:
                conditions_met.append(f"官杀{authority_element.value}当令(月支{month_branch})")
                strength += 0.25
            if authority_branches >= 2:
                conditions_met.append(f"地支有{authority_branches}个官杀{authority_element.value}支")
                strength += 0.15

            # Determine 从官 vs 从杀 based on stem yin/yang
            # 正官 = 异性克我, 七杀 = 同性克我
            output_element = day_master_element.generates  # 食伤
            output_ratio = wuxing_values.get(output_element, 0) / total if total > 0 else 0

            # Check for 食伤 制杀
            if output_ratio > 0.15:
                conditions_failed.append(f"有食伤{output_element.value}制杀，难成从格")
                strength -= 0.2
            else:
                conditions_met.append(f"无食伤{output_element.value}制克")
                strength += 0.10

            if not conditions_failed:
                # Determine 从官 vs 从杀 by checking stems
                has_zhenguan = any(
                    p.stem.wuxing == authority_element and p.stem.yinyang != day_master_yinyang
                    for p in bazi.pillars
                )
                has_qisha = any(
                    p.stem.wuxing == authority_element and p.stem.yinyang == day_master_yinyang
                    for p in bazi.pillars
                )

                if has_qisha and not has_zhenguan:
                    patterns.append(SpecialPattern(
                        pattern_type=PatternType.CONG_SHA,
                        category=PatternCategory.CONG_GE,
                        element=authority_element,
                        strength=min(max(strength, 0.0), 1.0),
                        description="弃命从杀，以杀为用",
                        conditions_met=conditions_met,
                        conditions_failed=conditions_failed,
                    ))
                else:
                    patterns.append(SpecialPattern(
                        pattern_type=PatternType.CONG_GUAN,
                        category=PatternCategory.CONG_GE,
                        element=authority_element,
                        strength=min(max(strength, 0.0), 1.0),
                        description="弃命从官，以官为用",
                        conditions_met=conditions_met,
                        conditions_failed=conditions_failed,
                    ))

        # --- 从儿格 (食伤) ---
        output_element = day_master_element.generates  # 食伤 = 日主所生
        output_in_command = (month_element == output_element)

        output_branches = sum(1 for p in bazi.pillars if ZHI_MAIN_WUXING.get(p.branch.chinese) == output_element)
        output_stems = sum(1 for p in bazi.pillars if p.stem.wuxing == output_element)

        if output_in_command or (output_branches >= 2 and output_stems >= 1):
            conditions_met = base_conditions.copy()
            conditions_failed = []
            strength = 0.5

            if output_in_command:
                conditions_met.append(f"食伤{output_element.value}当令(月支{month_branch})")
                strength += 0.25
            if output_branches >= 2:
                conditions_met.append(f"地支有{output_branches}个食伤{output_element.value}支")
                strength += 0.15

            # Check for 枭印 夺食
            support_ratio = wuxing_values.get(support_element, 0) / total if total > 0 else 0
            if support_ratio > 0.1:
                conditions_failed.append(f"有枭印{support_element.value}夺食，破格")
                strength -= 0.2
            else:
                conditions_met.append(f"无枭印{support_element.value}夺食")
                strength += 0.10

            if not conditions_failed:
                patterns.append(SpecialPattern(
                    pattern_type=PatternType.CONG_ER,
                    category=PatternCategory.CONG_GE,
                    element=output_element,
                    strength=min(max(strength, 0.0), 1.0),
                    description="从儿格，以食伤为用",
                    conditions_met=conditions_met,
                    conditions_failed=conditions_failed,
                ))

        # --- 从势格 (财官食伤混杂成势) ---
        if not patterns:
            # Calculate combined strength of 财官食伤
            wealth_v = wuxing_values.get(wealth_element, 0)
            authority_v = wuxing_values.get(authority_element, 0)
            output_v = wuxing_values.get(output_element, 0)

            combined_ratio = (wealth_v + authority_v + output_v) / total if total > 0 else 0

            # 从势格: 财官食伤混杂但势强 (占比超过70%)
            if combined_ratio >= 0.7:
                dominant = max(
                    [(wealth_element, wealth_v), (authority_element, authority_v), (output_element, output_v)],
                    key=lambda x: x[1]
                )[0]

                patterns.append(SpecialPattern(
                    pattern_type=PatternType.CONG_SHI,
                    category=PatternCategory.CONG_GE,
                    element=dominant,
                    strength=min(0.5 + (combined_ratio - 0.7), 1.0),
                    description="从势格，财官食伤混杂成势",
                    conditions_met=base_conditions + [f"财官食伤合占{combined_ratio:.0%}，势强"],
                    conditions_failed=[],
                ))

        return patterns
