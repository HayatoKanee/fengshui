"""
Integrated 用神 (Favorable Elements) analyzer service.

Combines multiple traditional methods into a modern scoring system:
1. 扶抑用神 - Support/Suppress based on day master strength
2. 调候用神 - Climate adjustment based on season

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..models import BaZi, WuXing, DayMasterStrength, FavorableElements
from .tiaohao_analyzer import TiaoHouAnalyzer, TiaoHouResult, SeasonType


@dataclass(frozen=True)
class WuXingScore:
    """Score for a WuXing element as potential 用神."""
    element: WuXing
    fuyi_score: float = 0.0      # 扶抑法评分
    tiaohao_score: float = 0.0   # 调候法评分
    total_score: float = 0.0     # 综合评分
    reasons: Tuple[str, ...] = ()


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
    fuyi_weight: float          # 扶抑法权重
    tiaohao_weight: float       # 调候法权重
    scores: Dict[WuXing, WuXingScore] = field(default_factory=dict)

    # Sub-results for transparency
    fuyi_result: Optional[FavorableElements] = None
    tiaohao_result: Optional[TiaoHouResult] = None

    # Analysis summary
    method_used: str = ""       # 主要采用的方法
    notes: Tuple[str, ...] = () # 分析备注


class IntegratedYongShenAnalyzer:
    """
    现代综合取用神分析器 - Modern integrated favorable elements analyzer.

    Combines 扶抑用神 and 调候用神 using a weighted scoring system.

    Weighting strategy:
    - Extreme seasons (子丑午未): 扶抑 40% + 调候 60%
    - Moderate seasons: 扶抑 70% + 调候 30%
    """

    def __init__(self, tiaohao_analyzer: TiaoHouAnalyzer | None = None):
        self._tiaohao = tiaohao_analyzer or TiaoHouAnalyzer()

    def _get_weights(self, season_type: SeasonType) -> Tuple[float, float]:
        """
        Get weights for 扶抑 and 调候 based on season intensity.

        Returns:
            Tuple of (fuyi_weight, tiaohao_weight)
        """
        if season_type in (SeasonType.EXTREME_COLD, SeasonType.EXTREME_HOT):
            # 极端季节：调候优先
            return (0.4, 0.6)
        elif season_type in (SeasonType.COLD, SeasonType.HOT):
            # 较冷/较热：平衡取用
            return (0.5, 0.5)
        else:
            # 温和季节：扶抑为主
            return (0.7, 0.3)

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
    ) -> IntegratedYongShenResult:
        """
        Perform integrated 用神 analysis.

        Args:
            bazi: The BaZi chart to analyze
            day_master_strength: Pre-calculated day master strength

        Returns:
            IntegratedYongShenResult with final recommendations and detailed scoring
        """
        day_master_element = bazi.day_master_wuxing

        # Get 调候分析
        tiaohao_result = self._tiaohao.analyze(bazi)

        # Determine weights based on season
        fuyi_weight, tiaohao_weight = self._get_weights(tiaohao_result.season_type)

        # Calculate individual scores
        fuyi_scores = self._calculate_fuyi_scores(
            day_master_element,
            day_master_strength.is_strong,
        )
        tiaohao_scores = self._calculate_tiaohao_scores(tiaohao_result)

        # Combine scores with weights
        combined_scores: Dict[WuXing, float] = {}
        element_scores: Dict[WuXing, WuXingScore] = {}

        for element in WuXing:
            fuyi = fuyi_scores.get(element, 0.0)
            tiaohao = tiaohao_scores.get(element, 0.0)
            total = (fuyi * fuyi_weight) + (tiaohao * tiaohao_weight)

            combined_scores[element] = total

            # Build reasons
            reasons = []
            if fuyi > 0:
                reasons.append(f"扶抑法喜 (+{fuyi:.1f})")
            elif fuyi < 0:
                reasons.append(f"扶抑法忌 ({fuyi:.1f})")
            if tiaohao > 0:
                reasons.append(f"调候法喜 (+{tiaohao:.1f})")

            element_scores[element] = WuXingScore(
                element=element,
                fuyi_score=fuyi,
                tiaohao_score=tiaohao,
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
        notes.append(f"权重：扶抑{fuyi_weight:.0%}，调候{tiaohao_weight:.0%}")

        # Determine primary method
        if tiaohao_weight >= 0.6:
            method_used = "调候为主，扶抑为辅"
        elif fuyi_weight >= 0.6:
            method_used = "扶抑为主，调候为辅"
        else:
            method_used = "扶抑调候兼顾"

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
            fuyi_weight=fuyi_weight,
            tiaohao_weight=tiaohao_weight,
            scores=element_scores,
            fuyi_result=fuyi_result,
            tiaohao_result=tiaohao_result,
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
