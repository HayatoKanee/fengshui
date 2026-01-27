"""
Integrated 用神 (Favorable Elements) analyzer service.

Combines three traditional methods into a modern scoring system:
1. 扶抑用神 - Support/Suppress based on day master strength
2. 调候用神 - Climate adjustment based on season
3. 通关用神 - Mediation for element conflicts

Default weights: 扶抑 50% + 调候 30% + 通关 20%
Based on traditional proportion: 扶抑占5分，调候占3分，通关占2分 (徐乐吾)

Weights are configurable and can be adjusted based on season.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from ..models import BaZi, WuXing, DayMasterStrength, FavorableElements, WuXingStrength
from ..models.stems_branches import HeavenlyStem
from ..models.pattern_analysis import PatternAnalysis, PatternCategory, SpecialPattern
from .tiaohao_analyzer import TiaoHouAnalyzer, TiaoHouResult, SeasonType
from .tongguan_analyzer import TongGuanAnalyzer, TongGuanResult
from .pattern_analyzer import PatternAnalyzer


@dataclass(frozen=True)
class WuXingScore:
    """Score for a WuXing element as potential 用神."""
    element: WuXing
    fuyi_score: float = 0.0       # 扶抑法评分
    tiaohao_score: float = 0.0    # 调候法评分
    tongguan_score: float = 0.0   # 通关法评分
    total_score: float = 0.0      # 综合评分
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MethodWeights:
    """Weights for each analysis method."""
    fuyi: float      # 扶抑权重
    tiaohao: float   # 调候权重
    tongguan: float  # 通关权重

    def __post_init__(self):
        # Verify weights sum to 1.0
        total = self.fuyi + self.tiaohao + self.tongguan
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class IntegratedYongShenResult:
    """
    Result of integrated 用神 analysis.

    Contains both the final recommendation and detailed scoring
    for transparency and debugging.

    Classical definitions (《子平真诠》):
    - 用神: Element with highest beneficial score (最需要的五行)
    - 喜神: Element that generates 用神 (生用神者为喜神)
    - 忌神: Element that controls 用神 (克用神者为忌神)
    - 仇神: Element that generates 忌神 (生忌神者为仇神)
    - 闲神: Remaining element, what 用神 generates (用神所生)

    Yin/Yang distinction (《穷通宝鉴》):
    - "用甲木的时候，绝对不可以用乙木" - Specific stems matter
    - yongshen_stems provides specific HeavenlyStem recommendations preserving Yin/Yang
    """
    # Final recommendations (based on classical five-element relationships)
    yong_shen: WuXing           # 用神 - Most needed element (highest score)
    xi_shen: WuXing             # 喜神 - Generates 用神 (生用神)
    ji_shen: WuXing             # 忌神 - Controls 用神 (克用神)
    chou_shen: WuXing           # 仇神 - Generates 忌神 (生忌神)
    xian_shen: WuXing           # 闲神 - 用神 generates (用神所生)

    # Analysis details (required field - must come before defaults)
    weights: MethodWeights

    # Multiple yongshen support (ranked by score)
    # 《穷通宝鉴》: "大抵甲庚丁一组，三个是黄金搭档"
    yongshen_ranked: Tuple[WuXing, ...] = ()  # All elements ranked by score (favorable to unfavorable)

    # HeavenlyStem-level recommendations (preserving Yin/Yang)
    # Primary stems from 调候 analysis (e.g., 丁火 not just 火)
    yongshen_stems: Tuple[HeavenlyStem, ...] = ()  # Specific stems (primary)
    secondary_stems: Tuple[HeavenlyStem, ...] = () # Secondary stems

    # Detailed scores
    scores: Dict[WuXing, WuXingScore] = field(default_factory=dict)

    # Sub-results for transparency
    fuyi_result: Optional[FavorableElements] = None
    tiaohao_result: Optional[TiaoHouResult] = None
    tongguan_result: Optional[TongGuanResult] = None
    pattern_result: Optional[PatternAnalysis] = None  # 特殊格局分析

    # Analysis summary
    method_used: str = ""       # 主要采用的方法
    notes: Tuple[str, ...] = () # 分析备注


# 默认权重配置
# 基于徐乐吾的传统比例：扶抑占5分，调候占3分，通关占2分 = 50%, 30%, 20%
DEFAULT_WEIGHTS = MethodWeights(fuyi=0.50, tiaohao=0.30, tongguan=0.20)

# 极端季节权重调整：扶抑 40% + 调候 40% + 通关 20%
EXTREME_SEASON_WEIGHTS = MethodWeights(fuyi=0.40, tiaohao=0.40, tongguan=0.20)

# ============================================================================
# 扶抑法说明 - 纯平衡计算，无优先级权重
#
# 原理：生耗值的差值直接告诉我们需要补多少
# - deficit = (beneficial - harmful) / 2
# - 身强(deficit>0)：所有泄克五行(食伤、财星、官杀)同等有效
# - 身弱(deficit<0)：所有生扶五行(印星、比劫)同等有效
#
# 各法分工：
# - 扶抑法：纯平衡计算（需要多少点）
# - 调候法：季节偏好（哪个天干更适合，保留阴阳）
# - 通关法：化解相战（五行冲突时的桥梁）
# ============================================================================

# ============================================================================
# 调候法评分常量
# Based on《穷通宝鉴》priority rankings
# ============================================================================
# Primary yongshen scores (most important)
TIAOHAO_PRIMARY_SCORES = (1.0, 0.85, 0.7)  # First 3 primary stems
# Secondary yongshen scores
TIAOHAO_SECONDARY_SCORES = (0.5, 0.4, 0.3)  # First 3 secondary stems


class IntegratedYongShenAnalyzer:
    """
    现代综合取用神分析器 - Modern integrated favorable elements analyzer.

    Combines 扶抑用神, 调候用神, and 通关用神 using a weighted scoring system.

    Default weights (based on 徐乐吾):
    - Standard: 扶抑 50% + 调候 30% + 通关 20%
    - Extreme seasons (子丑午未): 扶抑 40% + 调候 40% + 通关 20%

    Weights are configurable via constructor.
    """

    def __init__(
        self,
        default_weights: MethodWeights | None = None,
        extreme_weights: MethodWeights | None = None,
        tiaohao_analyzer: TiaoHouAnalyzer | None = None,
        tongguan_analyzer: TongGuanAnalyzer | None = None,
        pattern_analyzer: PatternAnalyzer | None = None,
    ):
        """
        Initialize the analyzer with configurable weights.

        Args:
            default_weights: Weights for moderate seasons (default: 50/30/20)
            extreme_weights: Weights for extreme seasons (default: 40/40/20)
            tiaohao_analyzer: Optional custom 调候 analyzer
            tongguan_analyzer: Optional custom 通关 analyzer
            pattern_analyzer: Optional custom pattern analyzer for 从格/专旺格
        """
        self._default_weights = default_weights or DEFAULT_WEIGHTS
        self._extreme_weights = extreme_weights or EXTREME_SEASON_WEIGHTS
        self._tiaohao = tiaohao_analyzer or TiaoHouAnalyzer()
        self._tongguan = tongguan_analyzer or TongGuanAnalyzer()
        self._pattern = pattern_analyzer or PatternAnalyzer()

    def _get_weights(self, season_type: SeasonType) -> MethodWeights:
        """
        Get weights for each method based on season.

        Extreme seasons (极寒/极热) use extreme_weights,
        others use default_weights.

        Returns:
            MethodWeights with fuyi, tiaohao, and tongguan weights
        """
        if season_type in (SeasonType.EXTREME_COLD, SeasonType.EXTREME_HOT):
            return self._extreme_weights
        else:
            return self._default_weights

    def _calculate_fuyi_scores(
        self,
        day_master_element: WuXing,
        day_master_strength: DayMasterStrength,
    ) -> Dict[WuXing, float]:
        """
        Calculate 扶抑法 scores for each WuXing element.

        Pure balance calculation - no priority weights.
        The deficit value represents how much of each element type is needed.

        Principle:
        - 身强: ALL 泄克 elements (食伤、财星、官杀) equally help balance
        - 身弱: ALL 生扶 elements (印星、比劫) equally help balance

        The differentiation between elements comes from:
        - 调候法: seasonal preferences (e.g., 冬用丙火)
        - 通关法: conflict resolution (e.g., 金木相战用水)

        Example:
            beneficial=70, harmful=30 → 身强
            deficit = (70-30)/2 = 20 → need 20 points of 泄克
            All 泄克 elements get +20, all 生扶 elements get -20

        Args:
            day_master_element: The day master's WuXing
            day_master_strength: Contains beneficial/harmful values

        Returns:
            Dict mapping each WuXing to its fuyi score (deficit value)
        """
        scores = {element: 0.0 for element in WuXing}

        beneficial = day_master_strength.beneficial_value
        harmful = day_master_strength.harmful_value

        # 计算达到平衡需要多少点
        # 正值=身强需泄克, 负值=身弱需生扶
        deficit = (beneficial - harmful) / 2

        if deficit > 0:
            # 身强：需要泄克来平衡
            # 所有泄克五行都能帮助平衡，分数相同
            scores[day_master_element.generates] = deficit      # 食伤（泄）
            scores[day_master_element.overcomes] = deficit      # 财星（耗）
            scores[day_master_element.overcome_by] = deficit    # 官杀（克）
            # 生扶五行是忌神
            scores[day_master_element.generated_by] = -deficit  # 印星
            scores[day_master_element] = -deficit               # 比劫
        else:
            # 身弱：需要生扶来平衡
            deficit = abs(deficit)
            scores[day_master_element.generated_by] = deficit   # 印星（生）
            scores[day_master_element] = deficit                # 比劫（扶）
            # 泄克五行是忌神
            scores[day_master_element.generates] = -deficit     # 食伤
            scores[day_master_element.overcomes] = -deficit     # 财星
            scores[day_master_element.overcome_by] = -deficit   # 官杀

        return scores

    def _calculate_tiaohao_scores(
        self,
        tiaohao_result: TiaoHouResult,
    ) -> Dict[WuXing, float]:
        """
        Calculate 调候法 scores for each WuXing element.

        Based on《穷通宝鉴》recommendations for day stem + month branch.
        Uses TIAOHAO_PRIMARY_SCORES and TIAOHAO_SECONDARY_SCORES constants.
        """
        scores = {element: 0.0 for element in WuXing}

        # Score primary 用神 using predefined constants
        for i, stem in enumerate(tiaohao_result.primary_yongshen):
            if i < len(TIAOHAO_PRIMARY_SCORES):
                score = TIAOHAO_PRIMARY_SCORES[i]
            else:
                # Fallback for more than 3 primary yongshen (rare)
                score = TIAOHAO_PRIMARY_SCORES[-1] * 0.8
            wuxing = stem.wuxing
            scores[wuxing] = max(scores[wuxing], score)

        # Score secondary 用神 using predefined constants
        for i, stem in enumerate(tiaohao_result.secondary_yongshen):
            if i < len(TIAOHAO_SECONDARY_SCORES):
                score = TIAOHAO_SECONDARY_SCORES[i]
            else:
                # Fallback for more than 3 secondary yongshen
                score = TIAOHAO_SECONDARY_SCORES[-1] * 0.8
            wuxing = stem.wuxing
            scores[wuxing] = max(scores[wuxing], score)

        return scores

    def _calculate_tongguan_scores(
        self,
        tongguan_result: TongGuanResult,
    ) -> Dict[WuXing, float]:
        """
        Calculate 通关法 scores for each WuXing element.

        Based on detected element conflicts and their mediators.
        """
        scores = {element: 0.0 for element in WuXing}

        # Use the mediator scores directly
        for element, score in tongguan_result.recommended_mediators.items():
            scores[element] = score

        return scores

    def _calculate_cong_ge_scores(
        self,
        day_master_element: WuXing,
        pattern: SpecialPattern,
    ) -> Dict[WuXing, float]:
        """
        Calculate scores for 从格 (Following patterns).

        从格的取用神原则与扶抑格相反：
        - 扶抑格：身弱补印比，身强用泄克
        - 从格：顺从所从之势，不可逆势补印比

        从财格：以财为用，食伤生财为喜，忌印比（因印克食伤，比劫夺财）
        从儿格：以食伤为用，比劫生食伤为喜，忌印（枭印夺食）
        从官/从杀格：以官杀为用，财生官为喜，忌食伤（伤官见官）
        从势格：以最旺者为用

        Args:
            day_master_element: The day master's WuXing
            pattern: The detected 从格 pattern

        Returns:
            Dict mapping each WuXing to its score (normalized around 50)
        """
        scores = {element: 0.0 for element in WuXing}

        # 从格的强度决定分数基准
        base_score = 50.0 * pattern.strength

        cong_element = pattern.element  # 所从之五行

        # 食伤 = 日主所生, 财 = 日主所克, 官杀 = 克日主, 印 = 生日主, 比劫 = 日主
        output_element = day_master_element.generates      # 食伤
        wealth_element = day_master_element.overcomes      # 财星
        authority_element = day_master_element.overcome_by  # 官杀
        support_element = day_master_element.generated_by   # 印绶
        peer_element = day_master_element                   # 比劫

        # 根据从格类型设置分数
        from ..models.pattern_analysis import PatternType

        if pattern.pattern_type == PatternType.CONG_CAI:
            # 从财格：财为用神，食伤生财为喜，忌印比
            scores[wealth_element] = base_score           # 财（用神）
            scores[output_element] = base_score * 0.8     # 食伤（喜神，生财）
            scores[authority_element] = base_score * 0.3  # 官杀（中性，护财）
            scores[support_element] = -base_score * 0.8   # 印（忌，克食伤）
            scores[peer_element] = -base_score            # 比劫（大忌，夺财）

        elif pattern.pattern_type == PatternType.CONG_ER:
            # 从儿格：食伤为用神，比劫生食伤可用，忌印夺食
            scores[output_element] = base_score           # 食伤（用神）
            scores[wealth_element] = base_score * 0.8     # 财（喜神，泄食伤之气）
            scores[peer_element] = base_score * 0.5       # 比劫（中性，可生食伤）
            scores[support_element] = -base_score         # 印（大忌，枭印夺食）
            scores[authority_element] = -base_score * 0.6 # 官杀（忌，克比劫断食伤之源）

        elif pattern.pattern_type in (PatternType.CONG_GUAN, PatternType.CONG_SHA):
            # 从官/从杀格：官杀为用神，财生官为喜，忌食伤
            scores[authority_element] = base_score        # 官杀（用神）
            scores[wealth_element] = base_score * 0.8     # 财（喜神，生官杀）
            scores[support_element] = base_score * 0.3    # 印（中性，化官杀）
            scores[output_element] = -base_score          # 食伤（大忌，伤官见官）
            scores[peer_element] = -base_score * 0.6      # 比劫（忌，抗官杀）

        elif pattern.pattern_type == PatternType.CONG_SHI:
            # 从势格：财官食伤混杂，以最旺者为用
            # 顺势而行，忌印比
            scores[cong_element] = base_score             # 所从五行（用神）
            scores[cong_element.generates] = base_score * 0.6  # 所从五行所生（喜）
            scores[support_element] = -base_score * 0.8   # 印（忌）
            scores[peer_element] = -base_score            # 比劫（大忌）

        return scores

    def _calculate_hua_ge_scores(
        self,
        day_master_element: WuXing,
        pattern: SpecialPattern,
    ) -> Dict[WuXing, float]:
        """
        Calculate scores for 化格 (Transformation patterns).

        化格的取用神原则：
        - 化神（合化之五行）为用神
        - 生化神者为喜神
        - 克化神者为忌神

        例：甲己化土，土为用神，火(生土)为喜神，木(克土)为忌神

        Args:
            day_master_element: The day master's WuXing
            pattern: The detected 化格 pattern

        Returns:
            Dict mapping each WuXing to its score (normalized around 50)
        """
        scores = {element: 0.0 for element in WuXing}

        # 化格的强度决定分数基准
        base_score = 50.0 * pattern.strength

        # 化神五行（合化后的五行）
        hua_element = pattern.element

        # 化格用神逻辑：
        # 用神 = 化神（合化之五行）
        # 喜神 = 生化神者
        # 忌神 = 克化神者
        # 仇神 = 生忌神者

        scores[hua_element] = base_score                      # 化神（用神）
        scores[hua_element.generated_by] = base_score * 0.8   # 生化神者（喜神）
        scores[hua_element.generates] = base_score * 0.5      # 化神所生（闲神，泄秀）
        scores[hua_element.overcome_by] = -base_score         # 克化神者（大忌）
        scores[hua_element.overcomes] = -base_score * 0.6     # 化神所克（小忌）

        return scores

    def _determine_favorable_unfavorable(
        self,
        combined_scores: Dict[WuXing, float],
    ) -> Tuple[WuXing, Optional[WuXing], WuXing, Optional[WuXing], Optional[WuXing]]:
        """
        Determine 用神/喜神/忌神/仇神/闲神 based on classical five-element relationships.

        Traditional definitions (《子平真诠》):
        - 用神: Element with highest beneficial score
        - 喜神: Element that generates 用神 (生用神者为喜神)
        - 忌神: Element that controls 用神 (克用神者为忌神)
        - 仇神: Element that generates 忌神 (生忌神者为仇神)
        - 闲神: Remaining element (用神 generates)

        Returns:
            Tuple of (yong_shen, xi_shen, ji_shen, chou_shen, xian_shen)
        """
        # 用神: Highest score
        sorted_elements = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        yong_shen = sorted_elements[0][0]

        # Classical five-element derivation:
        # 喜神 = 生用神者 (what generates 用神)
        xi_shen = yong_shen.generated_by

        # 忌神 = 克用神者 (what controls 用神)
        ji_shen = yong_shen.overcome_by

        # 仇神 = 生忌神者 (what generates 忌神)
        chou_shen = ji_shen.generated_by

        # 闲神 = 用神所生者 (what 用神 generates)
        xian_shen = yong_shen.generates

        return yong_shen, xi_shen, ji_shen, chou_shen, xian_shen

    def analyze(
        self,
        bazi: BaZi,
        day_master_strength: DayMasterStrength,
        wuxing_strength: WuXingStrength | None = None,
    ) -> IntegratedYongShenResult:
        """
        Perform integrated 用神 analysis using three methods.

        Now includes special pattern (从格/专旺格) detection:
        - If a valid 从格 is detected, uses 从格-specific scoring
        - Otherwise uses normal 扶抑+调候+通关 scoring

        Args:
            bazi: The BaZi chart to analyze
            day_master_strength: Pre-calculated day master strength
            wuxing_strength: Pre-calculated WuXing strength (optional, for 通关)

        Returns:
            IntegratedYongShenResult with final recommendations and detailed scoring
        """
        day_master_element = bazi.day_master_wuxing

        # Step 1: Detect special patterns (从格/专旺格/化格)
        wuxing_values = None
        if wuxing_strength:
            wuxing_values = wuxing_strength.adjusted_values
        pattern_result = self._pattern.analyze(bazi, wuxing_values)

        # Check if we have a valid special pattern (从格 or 化格)
        is_special_pattern = False
        special_pattern: Optional[SpecialPattern] = None
        if pattern_result.primary_pattern:
            primary = pattern_result.primary_pattern
            if primary.is_valid and primary.category in (
                PatternCategory.CONG_GE,
                PatternCategory.HUA_GE,
            ):
                is_special_pattern = True
                special_pattern = primary

        # Get 调候分析
        tiaohao_result = self._tiaohao.analyze(bazi)

        # Get 通关分析 (if wuxing_strength provided)
        tongguan_result = None
        if wuxing_strength:
            tongguan_result = self._tongguan.analyze(bazi, wuxing_strength)

        # Determine weights based on season and mode
        weights = self._get_weights(tiaohao_result.season_type)

        # Calculate individual scores
        # 从格/化格 uses special scoring, otherwise use normal 扶抑
        if is_special_pattern and special_pattern:
            if special_pattern.category == PatternCategory.CONG_GE:
                # 从格：使用专门的评分逻辑
                fuyi_scores = self._calculate_cong_ge_scores(
                    day_master_element,
                    special_pattern,
                )
            else:
                # 化格：使用化格评分逻辑
                fuyi_scores = self._calculate_hua_ge_scores(
                    day_master_element,
                    special_pattern,
                )
        else:
            # 普通格局：扶抑法基于生耗值失衡比例
            fuyi_scores = self._calculate_fuyi_scores(
                day_master_element,
                day_master_strength,
            )

        tiaohao_scores = self._calculate_tiaohao_scores(tiaohao_result)
        tongguan_scores = (
            self._calculate_tongguan_scores(tongguan_result)
            if tongguan_result
            else {element: 0.0 for element in WuXing}
        )

        # Combine scores with weights
        combined_scores: Dict[WuXing, float] = {}
        element_scores: Dict[WuXing, WuXingScore] = {}

        for element in WuXing:
            fuyi = fuyi_scores.get(element, 0.0)
            tiaohao = tiaohao_scores.get(element, 0.0)
            tongguan = tongguan_scores.get(element, 0.0)

            total = (
                (fuyi * weights.fuyi) +
                (tiaohao * weights.tiaohao) +
                (tongguan * weights.tongguan)
            )

            combined_scores[element] = total

            # Build reasons
            reasons = []
            if fuyi > 0:
                reasons.append(f"扶抑喜(+{fuyi:.1f})")
            elif fuyi < 0:
                reasons.append(f"扶抑忌({fuyi:.1f})")
            if tiaohao > 0:
                reasons.append(f"调候喜(+{tiaohao:.1f})")
            if tongguan > 0:
                reasons.append(f"通关喜(+{tongguan:.1f})")

            element_scores[element] = WuXingScore(
                element=element,
                fuyi_score=fuyi,
                tiaohao_score=tiaohao,
                tongguan_score=tongguan,
                total_score=total,
                reasons=tuple(reasons),
            )

        # Determine final recommendations using classical five-element relationships
        yong_shen, xi_shen, ji_shen, chou_shen, xian_shen = self._determine_favorable_unfavorable(
            combined_scores
        )

        # Generate ranked list of all elements (favorable to unfavorable)
        sorted_elements = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        yongshen_ranked = tuple(elem for elem, _ in sorted_elements)

        # Extract HeavenlyStem-level recommendations from 调候 (preserving Yin/Yang)
        # 《穷通宝鉴》: "用甲木的时候，绝对不可以用乙木"
        yongshen_stems = tuple(tiaohao_result.primary_yongshen)
        secondary_stems = tuple(tiaohao_result.secondary_yongshen)

        # Build notes
        notes = []
        strength_desc = "身强" if day_master_strength.is_strong else "身弱"
        notes.append(f"日主{day_master_element.chinese}{strength_desc}")

        # Add special pattern information if detected
        if is_special_pattern and special_pattern:
            notes.append(f"格局：{special_pattern.description}（{special_pattern.pattern_type.value}）")
            notes.append(f"化/从五行：{special_pattern.element.chinese}")
        elif pattern_result.regular_pattern:
            notes.append(f"格局：{pattern_result.regular_pattern.pattern_type.value}")

        notes.append(f"季节：{tiaohao_result.season_type.value}")

        if not is_special_pattern:
            notes.append(f"扶抑{weights.fuyi:.0%}+调候{weights.tiaohao:.0%}+通关{weights.tongguan:.0%}")

        if tongguan_result and tongguan_result.has_conflict:
            notes.append(f"相战：{tongguan_result.description}")

        # Add classical derivation explanation
        notes.append(f"用神{yong_shen.chinese}→喜神{xi_shen.chinese}(生用神)→忌神{ji_shen.chinese}(克用神)→仇神{chou_shen.chinese}(生忌神)")

        # Add specific stem recommendations if available
        if yongshen_stems:
            stem_chars = "、".join(s.chinese for s in yongshen_stems)
            notes.append(f"调候用神（天干）：{stem_chars}")

        # Determine primary method description
        method_parts = []
        if is_special_pattern and special_pattern:
            method_parts.append(f"特殊格局（{special_pattern.pattern_type.value}）")
        elif weights.fuyi >= 0.5:
            method_parts.append("扶抑为主")
        elif weights.tiaohao >= 0.5:
            method_parts.append("调候为主")
        else:
            method_parts.append("扶抑调候兼顾")

        if tongguan_result and tongguan_result.has_conflict:
            method_parts.append("兼通关")

        method_used = "，".join(method_parts)

        # Build traditional FavorableElements for compatibility
        fuyi_result = FavorableElements(
            yong_shen=yong_shen,
            xi_shen=xi_shen,
            ji_shen=ji_shen,
            chou_shen=chou_shen,
        )

        return IntegratedYongShenResult(
            yong_shen=yong_shen,
            xi_shen=xi_shen,
            ji_shen=ji_shen,
            chou_shen=chou_shen,
            xian_shen=xian_shen,
            weights=weights,
            yongshen_ranked=yongshen_ranked,
            yongshen_stems=yongshen_stems,
            secondary_stems=secondary_stems,
            scores=element_scores,
            fuyi_result=fuyi_result,
            tiaohao_result=tiaohao_result,
            tongguan_result=tongguan_result,
            pattern_result=pattern_result,
            method_used=method_used,
            notes=tuple(notes),
        )

    def to_favorable_elements(
        self,
        result: IntegratedYongShenResult,
    ) -> FavorableElements:
        """
        Convert IntegratedYongShenResult to traditional FavorableElements.

        For backwards compatibility with existing code.
        """
        return FavorableElements(
            yong_shen=result.yong_shen,
            xi_shen=result.xi_shen,
            ji_shen=result.ji_shen,
            chou_shen=result.chou_shen,
        )
