"""
通关用神 (Mediation) analyzer service.

When two elements are in fierce conflict (相战), a mediating element
can bridge them and restore harmony.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..models import BaZi, WuXing, WuXingStrength


@dataclass(frozen=True)
class ElementConflict:
    """Represents a conflict between two elements."""
    element1: WuXing
    element2: WuXing
    strength1: float
    strength2: float
    mediator: WuXing
    severity: float  # 0.0-1.0, higher = more severe conflict
    description: str


@dataclass(frozen=True)
class TongGuanResult:
    """Result of 通关 analysis."""
    has_conflict: bool
    conflicts: Tuple[ElementConflict, ...]
    recommended_mediators: Dict[WuXing, float]  # element -> score
    primary_mediator: Optional[WuXing]
    description: str


# 通关用神表：相战 -> 通关元素
# 原理：A克B，取C通关（A生C，C生B）
TONGGUAN_TABLE: Dict[Tuple[WuXing, WuXing], WuXing] = {
    # 金木相战 -> 水通关（金生水，水生木）
    (WuXing.METAL, WuXing.WOOD): WuXing.WATER,
    (WuXing.WOOD, WuXing.METAL): WuXing.WATER,

    # 木土相战 -> 火通关（木生火，火生土）
    (WuXing.WOOD, WuXing.EARTH): WuXing.FIRE,
    (WuXing.EARTH, WuXing.WOOD): WuXing.FIRE,

    # 土水相战 -> 金通关（土生金，金生水）
    (WuXing.EARTH, WuXing.WATER): WuXing.METAL,
    (WuXing.WATER, WuXing.EARTH): WuXing.METAL,

    # 水火相战 -> 木通关（水生木，木生火）
    (WuXing.WATER, WuXing.FIRE): WuXing.WOOD,
    (WuXing.FIRE, WuXing.WATER): WuXing.WOOD,

    # 火金相战 -> 土通关（火生土，土生金）
    (WuXing.FIRE, WuXing.METAL): WuXing.EARTH,
    (WuXing.METAL, WuXing.FIRE): WuXing.EARTH,
}

# 相战描述
CONFLICT_DESCRIPTIONS: Dict[Tuple[WuXing, WuXing], str] = {
    (WuXing.METAL, WuXing.WOOD): "金木相战",
    (WuXing.WOOD, WuXing.METAL): "金木相战",
    (WuXing.WOOD, WuXing.EARTH): "木土相战",
    (WuXing.EARTH, WuXing.WOOD): "木土相战",
    (WuXing.EARTH, WuXing.WATER): "土水相战",
    (WuXing.WATER, WuXing.EARTH): "土水相战",
    (WuXing.WATER, WuXing.FIRE): "水火相战",
    (WuXing.FIRE, WuXing.WATER): "水火相战",
    (WuXing.FIRE, WuXing.METAL): "火金相战",
    (WuXing.METAL, WuXing.FIRE): "火金相战",
}


class TongGuanAnalyzer:
    """
    通关用神分析器 - Mediation favorable elements analyzer.

    Detects conflicts between elements and recommends mediating elements.

    五行相战通关口诀：
    - 金木相战，取水通关
    - 木土相战，取火通关
    - 土水相战，取金通关
    - 水火相战，取木通关
    - 火金相战，取土通关
    """

    # 判断相战的阈值
    CONFLICT_THRESHOLD = 0.15  # 两元素都至少占15%
    STRENGTH_RATIO_THRESHOLD = 0.5  # 力量比不能太悬殊（弱方至少是强方的50%）

    def analyze(
        self,
        bazi: BaZi,
        wuxing_strength: WuXingStrength,
    ) -> TongGuanResult:
        """
        Analyze for element conflicts and recommend mediators.

        Args:
            bazi: The BaZi chart to analyze
            wuxing_strength: Pre-calculated WuXing strength values

        Returns:
            TongGuanResult with conflict analysis and mediator recommendations
        """
        conflicts = self._detect_conflicts(wuxing_strength)
        mediator_scores = self._calculate_mediator_scores(conflicts)

        # Determine primary mediator
        primary_mediator = None
        if mediator_scores:
            primary_mediator = max(mediator_scores, key=mediator_scores.get)

        # Build description
        if conflicts:
            conflict_descs = [c.description for c in conflicts]
            description = "；".join(conflict_descs)
        else:
            description = "命局五行流通，无明显相战"

        return TongGuanResult(
            has_conflict=len(conflicts) > 0,
            conflicts=tuple(conflicts),
            recommended_mediators=mediator_scores,
            primary_mediator=primary_mediator,
            description=description,
        )

    def _detect_conflicts(
        self,
        wuxing_strength: WuXingStrength,
    ) -> List[ElementConflict]:
        """
        Detect element conflicts based on strength values.

        Conflict conditions:
        1. Two elements have克 relationship
        2. Both elements are relatively strong (>15% each)
        3. Forces are relatively balanced (ratio > 0.5)
        """
        conflicts = []
        values = wuxing_strength.adjusted_values
        total = wuxing_strength.total

        if total == 0:
            return conflicts

        # Check all克 relationships
        ke_pairs = [
            (WuXing.METAL, WuXing.WOOD),
            (WuXing.WOOD, WuXing.EARTH),
            (WuXing.EARTH, WuXing.WATER),
            (WuXing.WATER, WuXing.FIRE),
            (WuXing.FIRE, WuXing.METAL),
        ]

        for attacker, defender in ke_pairs:
            strength1 = values.get(attacker, 0) / total
            strength2 = values.get(defender, 0) / total

            # Check if both are significant
            if strength1 < self.CONFLICT_THRESHOLD or strength2 < self.CONFLICT_THRESHOLD:
                continue

            # Check if forces are balanced enough for "战"
            min_strength = min(strength1, strength2)
            max_strength = max(strength1, strength2)
            if max_strength > 0 and (min_strength / max_strength) < self.STRENGTH_RATIO_THRESHOLD:
                continue

            # This is a conflict
            mediator = TONGGUAN_TABLE.get((attacker, defender))
            if mediator:
                severity = min(strength1, strength2) * 2  # Higher when both are strong
                conflict = ElementConflict(
                    element1=attacker,
                    element2=defender,
                    strength1=strength1,
                    strength2=strength2,
                    mediator=mediator,
                    severity=min(severity, 1.0),
                    description=f"{CONFLICT_DESCRIPTIONS[(attacker, defender)]}，宜{mediator.chinese}通关",
                )
                conflicts.append(conflict)

        # Sort by severity
        conflicts.sort(key=lambda c: c.severity, reverse=True)
        return conflicts

    def _calculate_mediator_scores(
        self,
        conflicts: List[ElementConflict],
    ) -> Dict[WuXing, float]:
        """
        Calculate scores for each potential mediator element.

        Score is based on conflict severity.
        """
        scores: Dict[WuXing, float] = {}

        for conflict in conflicts:
            mediator = conflict.mediator
            # Accumulate scores for each mediator
            current = scores.get(mediator, 0.0)
            scores[mediator] = current + conflict.severity

        # Normalize scores to 0-1 range
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def get_tongguan_wuxing(
        self,
        bazi: BaZi,
        wuxing_strength: WuXingStrength,
    ) -> Optional[WuXing]:
        """
        Get the primary 通关用神 as WuXing element.

        Returns None if no significant conflict detected.
        """
        result = self.analyze(bazi, wuxing_strength)
        return result.primary_mediator

    def needs_mediation(
        self,
        bazi: BaZi,
        wuxing_strength: WuXingStrength,
    ) -> bool:
        """
        Check if this BaZi chart needs mediation (通关).

        Returns True if there are significant element conflicts.
        """
        result = self.analyze(bazi, wuxing_strength)
        return result.has_conflict
