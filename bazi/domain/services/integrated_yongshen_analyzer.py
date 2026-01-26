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
from typing import Dict, List, Optional, Tuple

from ..models import BaZi, WuXing, DayMasterStrength, FavorableElements, WuXingStrength
from .tiaohao_analyzer import TiaoHouAnalyzer, TiaoHouResult, SeasonType
from .tongguan_analyzer import TongGuanAnalyzer, TongGuanResult


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
    """
    # Final recommendations
    yong_shen: WuXing           # 用神 - Most needed element
    xi_shen: Optional[WuXing]   # 喜神 - Supportive element
    ji_shen: WuXing             # 忌神 - Element to avoid
    chou_shen: Optional[WuXing] # 仇神 - Hostile element

    # Analysis details
    weights: MethodWeights
    scores: Dict[WuXing, WuXingScore] = field(default_factory=dict)

    # Sub-results for transparency
    fuyi_result: Optional[FavorableElements] = None
    tiaohao_result: Optional[TiaoHouResult] = None
    tongguan_result: Optional[TongGuanResult] = None

    # Analysis summary
    method_used: str = ""       # 主要采用的方法
    notes: Tuple[str, ...] = () # 分析备注


# 默认权重配置
# 基于徐乐吾的传统比例：扶抑占5分，调候占3分，通关占2分 = 50%, 30%, 20%
DEFAULT_WEIGHTS = MethodWeights(fuyi=0.50, tiaohao=0.30, tongguan=0.20)

# 极端季节权重调整：扶抑 40% + 调候 40% + 通关 20%
EXTREME_SEASON_WEIGHTS = MethodWeights(fuyi=0.40, tiaohao=0.40, tongguan=0.20)


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
    ):
        """
        Initialize the analyzer with configurable weights.

        Args:
            default_weights: Weights for moderate seasons (default: 50/30/20)
            extreme_weights: Weights for extreme seasons (default: 40/40/20)
            tiaohao_analyzer: Optional custom 调候 analyzer
            tongguan_analyzer: Optional custom 通关 analyzer
        """
        self._default_weights = default_weights or DEFAULT_WEIGHTS
        self._extreme_weights = extreme_weights or EXTREME_SEASON_WEIGHTS
        self._tiaohao = tiaohao_analyzer or TiaoHouAnalyzer()
        self._tongguan = tongguan_analyzer or TongGuanAnalyzer()

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
        is_strong: bool,
    ) -> Dict[WuXing, float]:
        """
        Calculate 扶抑法 scores for each WuXing element.

        Strong day master: favor elements that drain/control
        Weak day master: favor elements that support/generate
        """
        scores = {element: 0.0 for element in WuXing}

        if is_strong:
            # 身强喜泄克
            scores[day_master_element.generates] = 1.0     # 食伤泄秀 (最佳)
            scores[day_master_element.overcome_by] = 0.8   # 官杀制身
            scores[day_master_element.overcomes] = 0.4     # 财星耗身
            scores[day_master_element.generated_by] = -0.8  # 印星生身 (忌)
            scores[day_master_element] = -1.0              # 比劫帮身 (最忌)
        else:
            # 身弱喜生扶
            scores[day_master_element.generated_by] = 1.0  # 印星生身 (最佳)
            scores[day_master_element] = 0.8               # 比劫帮身
            scores[day_master_element.overcome_by] = -0.4  # 官杀克身
            scores[day_master_element.generates] = -0.8    # 食伤泄身 (忌)
            scores[day_master_element.overcomes] = -1.0    # 财星耗身 (最忌)

        return scores

    def _calculate_tiaohao_scores(
        self,
        tiaohao_result: TiaoHouResult,
    ) -> Dict[WuXing, float]:
        """
        Calculate 调候法 scores for each WuXing element.

        Based on《穷通宝鉴》recommendations for day stem + month branch.
        """
        scores = {element: 0.0 for element in WuXing}

        # Score primary 用神
        for i, stem in enumerate(tiaohao_result.primary_yongshen):
            # First is best, decreasing value
            score = 1.0 - (i * 0.2)
            wuxing = stem.wuxing
            scores[wuxing] = max(scores[wuxing], score)

        # Score secondary 用神
        for i, stem in enumerate(tiaohao_result.secondary_yongshen):
            score = 0.5 - (i * 0.1)
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

    def _determine_favorable_unfavorable(
        self,
        combined_scores: Dict[WuXing, float],
    ) -> Tuple[WuXing, Optional[WuXing], WuXing, Optional[WuXing]]:
        """
        Determine 用神/喜神/忌神/仇神 from combined scores.

        Returns:
            Tuple of (yong_shen, xi_shen, ji_shen, chou_shen)
        """
        # Sort by score
        sorted_elements = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Favorable: top 2
        yong_shen = sorted_elements[0][0]
        xi_shen = sorted_elements[1][0] if len(sorted_elements) > 1 else None

        # Unfavorable: bottom 2
        ji_shen = sorted_elements[-1][0]
        chou_shen = sorted_elements[-2][0] if len(sorted_elements) > 1 else None

        return yong_shen, xi_shen, ji_shen, chou_shen

    def analyze(
        self,
        bazi: BaZi,
        day_master_strength: DayMasterStrength,
        wuxing_strength: WuXingStrength | None = None,
    ) -> IntegratedYongShenResult:
        """
        Perform integrated 用神 analysis using three methods.

        Args:
            bazi: The BaZi chart to analyze
            day_master_strength: Pre-calculated day master strength
            wuxing_strength: Pre-calculated WuXing strength (optional, for 通关)

        Returns:
            IntegratedYongShenResult with final recommendations and detailed scoring
        """
        day_master_element = bazi.day_master_wuxing

        # Get 调候分析
        tiaohao_result = self._tiaohao.analyze(bazi)

        # Get 通关分析 (if wuxing_strength provided)
        tongguan_result = None
        if wuxing_strength:
            tongguan_result = self._tongguan.analyze(bazi, wuxing_strength)

        # Determine weights based on season and mode
        weights = self._get_weights(tiaohao_result.season_type)

        # Calculate individual scores
        fuyi_scores = self._calculate_fuyi_scores(
            day_master_element,
            day_master_strength.is_strong,
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

        # Determine final recommendations
        yong_shen, xi_shen, ji_shen, chou_shen = self._determine_favorable_unfavorable(
            combined_scores
        )

        # Build notes
        notes = []
        strength_desc = "身强" if day_master_strength.is_strong else "身弱"
        notes.append(f"日主{day_master_element.chinese}{strength_desc}")
        notes.append(f"季节：{tiaohao_result.season_type.value}")
        notes.append(f"扶抑{weights.fuyi:.0%}+调候{weights.tiaohao:.0%}+通关{weights.tongguan:.0%}")

        if tongguan_result and tongguan_result.has_conflict:
            notes.append(f"相战：{tongguan_result.description}")

        # Determine primary method description
        method_parts = []
        if weights.fuyi >= 0.5:
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
            weights=weights,
            scores=element_scores,
            fuyi_result=fuyi_result,
            tiaohao_result=tiaohao_result,
            tongguan_result=tongguan_result,
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
