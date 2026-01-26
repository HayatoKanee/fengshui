"""
WuXing (Five Elements) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from ..models import (
    WuXing,
    WangXiang,
    Pillar,
    BaZi,
    HeavenlyStem,
    EarthlyBranch,
    WuXingStrength,
)

if TYPE_CHECKING:
    from ..models.branch_analysis import BranchRelationsAnalysis


# ============================================================================
# 地支关系对五行力量的调整系数
# 基于传统命理：三会 > 三合 > 半合 > 六合
# 六冲双方互损
# ============================================================================

# 三会局 - 同一方位汇聚，最强
# 寅卯辰会东方木、巳午未会南方火、申酉戌会西方金、亥子丑会北方水
SAN_HUI_MULTIPLIER = 2.0  # 力量翻倍

# 三合局 - 多方来合，次强
# 申子辰合水、亥卯未合木、寅午戌合火、巳酉丑合金
SAN_HE_MULTIPLIER = 1.8  # +80%

# 半合局 - 根据类型不同
BAN_HE_SHENG_WANG_MULTIPLIER = 1.3  # 生旺半合 +30%
BAN_HE_WANG_MU_MULTIPLIER = 1.2     # 旺墓半合 +20%
BAN_HE_DEFAULT_MULTIPLIER = 1.15   # 其他半合 +15%

# 六冲 - 双方互损，根据距离
CHONG_ADJACENT_MULTIPLIER = 0.7    # 紧贴冲 -30%
CHONG_SEPARATED_MULTIPLIER = 0.8   # 隔支冲 -20%
CHONG_DISTANT_MULTIPLIER = 0.9     # 遥冲 -10%


# Season to WangXiang mapping for each element
_SEASON_PHASES: Dict[str, Dict[WuXing, WangXiang]] = {
    "春": {
        WuXing.WOOD: WangXiang.WANG,
        WuXing.FIRE: WangXiang.XIANG,
        WuXing.WATER: WangXiang.XIU,
        WuXing.METAL: WangXiang.QIU,
        WuXing.EARTH: WangXiang.SI,
    },
    "夏": {
        WuXing.FIRE: WangXiang.WANG,
        WuXing.EARTH: WangXiang.XIANG,
        WuXing.WOOD: WangXiang.XIU,
        WuXing.WATER: WangXiang.QIU,
        WuXing.METAL: WangXiang.SI,
    },
    "秋": {
        WuXing.METAL: WangXiang.WANG,
        WuXing.WATER: WangXiang.XIANG,
        WuXing.EARTH: WangXiang.XIU,
        WuXing.FIRE: WangXiang.QIU,
        WuXing.WOOD: WangXiang.SI,
    },
    "冬": {
        WuXing.WATER: WangXiang.WANG,
        WuXing.WOOD: WangXiang.XIANG,
        WuXing.METAL: WangXiang.XIU,
        WuXing.EARTH: WangXiang.QIU,
        WuXing.FIRE: WangXiang.SI,
    },
    # Earth phase (土旺) during seasonal transitions
    "土旺": {
        WuXing.EARTH: WangXiang.WANG,
        WuXing.METAL: WangXiang.XIANG,
        WuXing.FIRE: WangXiang.XIU,
        WuXing.WOOD: WangXiang.QIU,
        WuXing.WATER: WangXiang.SI,
    },
}

# Branch to season mapping
_BRANCH_SEASONS: Dict[EarthlyBranch, str] = {
    EarthlyBranch.YIN: "春",
    EarthlyBranch.MAO: "春",
    EarthlyBranch.CHEN: "春",
    EarthlyBranch.SI: "夏",
    EarthlyBranch.WU: "夏",
    EarthlyBranch.WEI: "夏",
    EarthlyBranch.SHEN: "秋",
    EarthlyBranch.YOU: "秋",
    EarthlyBranch.XU: "秋",
    EarthlyBranch.HAI: "冬",
    EarthlyBranch.ZI: "冬",
    EarthlyBranch.CHOU: "冬",
}

# Earth-dominant branches (四库)
_EARTH_BRANCHES = {EarthlyBranch.CHEN, EarthlyBranch.WEI, EarthlyBranch.XU, EarthlyBranch.CHOU}


class WuXingCalculator:
    """
    Calculator for WuXing (Five Elements) relationships and values.

    This service handles all calculations related to the Five Elements,
    including relationships, seasonal strength, and accumulated values.
    """

    @staticmethod
    def get_relationship_values(stem: HeavenlyStem, branch: EarthlyBranch) -> Tuple[int, int]:
        """
        Calculate the relationship values between a stem and branch.

        Returns:
            Tuple of (stem_value, branch_value) based on their WuXing relationship.
        """
        stem_element = stem.wuxing
        branch_element = branch.wuxing

        if stem_element == branch_element:
            return (10, 10)
        elif stem_element.generates == branch_element:
            return (6, 8)
        elif stem_element.overcomes == branch_element:
            return (4, 2)
        elif branch_element.overcomes == stem_element:
            return (2, 4)
        elif branch_element.generates == stem_element:
            return (8, 6)

        return (5, 5)  # Default fallback

    @staticmethod
    def get_pillar_values(pillar: Pillar) -> Tuple[int, int]:
        """Get relationship values for a pillar."""
        return WuXingCalculator.get_relationship_values(pillar.stem, pillar.branch)

    @staticmethod
    def get_season(month_branch: EarthlyBranch, is_earth_dominant: bool = False) -> str:
        """
        Determine the season from the month branch.

        Args:
            month_branch: The earthly branch of the month pillar
            is_earth_dominant: Whether we're in the earth-dominant period
                              (last 18 days before season change)
        """
        if is_earth_dominant and month_branch in _EARTH_BRANCHES:
            return "土旺"
        return _BRANCH_SEASONS[month_branch]

    @staticmethod
    def get_wang_xiang(month_branch: EarthlyBranch, is_earth_dominant: bool = False) -> Dict[WuXing, WangXiang]:
        """
        Get the WangXiang (seasonal strength) mapping for the current season.

        Args:
            month_branch: The earthly branch of the month pillar
            is_earth_dominant: Whether we're in the earth-dominant period
        """
        season = WuXingCalculator.get_season(month_branch, is_earth_dominant)
        return _SEASON_PHASES[season]

    @staticmethod
    def calculate_wang_xiang_multiplier(element: WuXing, wang_xiang: Dict[WuXing, WangXiang]) -> float:
        """Get the strength multiplier for an element based on season."""
        phase = wang_xiang.get(element, WangXiang.XIU)
        return phase.multiplier

    def calculate_pillar_strength(
        self,
        pillar: Pillar,
        wang_xiang: Dict[WuXing, WangXiang]
    ) -> Tuple[float, List[float]]:
        """
        Calculate the strength values for a pillar.

        Returns:
            Tuple of (stem_strength, [hidden_stem_strengths])
        """
        # Base relationship values
        stem_value, branch_value = self.get_pillar_values(pillar)

        # Apply wang_xiang multiplier to stem
        stem_multiplier = self.calculate_wang_xiang_multiplier(pillar.stem_wuxing, wang_xiang)
        stem_strength = stem_value * stem_multiplier

        # Calculate hidden stem strengths
        hidden_strengths = []
        for hidden_stem, ratio in pillar.hidden_stems.items():
            hidden_element = hidden_stem.wuxing
            hidden_multiplier = self.calculate_wang_xiang_multiplier(hidden_element, wang_xiang)
            hidden_strength = branch_value * ratio * hidden_multiplier
            hidden_strengths.append(hidden_strength)

        return (stem_strength, hidden_strengths)

    def accumulate_wuxing_values(
        self,
        bazi: BaZi,
        wang_xiang: Dict[WuXing, WangXiang]
    ) -> Dict[WuXing, float]:
        """
        Calculate the accumulated WuXing values for an entire BaZi chart.

        Args:
            bazi: The BaZi chart
            wang_xiang: The seasonal WangXiang mapping

        Returns:
            Dictionary mapping each WuXing to its accumulated strength value.
        """
        result: Dict[WuXing, float] = {element: 0.0 for element in WuXing}

        for pillar in bazi.pillars:
            # Add stem value
            stem_value, _ = self.get_pillar_values(pillar)
            stem_multiplier = self.calculate_wang_xiang_multiplier(pillar.stem_wuxing, wang_xiang)
            result[pillar.stem_wuxing] += stem_value * stem_multiplier

            # Add hidden stem values
            _, branch_value = self.get_pillar_values(pillar)
            for hidden_stem, ratio in pillar.hidden_stems.items():
                hidden_element = hidden_stem.wuxing
                hidden_multiplier = self.calculate_wang_xiang_multiplier(hidden_element, wang_xiang)
                result[hidden_element] += branch_value * ratio * hidden_multiplier

        return result

    def calculate_strength(
        self,
        bazi: BaZi,
        is_earth_dominant: bool = False
    ) -> WuXingStrength:
        """
        Calculate the complete WuXing strength analysis for a BaZi chart.

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period

        Returns:
            WuXingStrength with raw and adjusted values
        """
        # Get wang_xiang based on month branch
        wang_xiang_map = self.get_wang_xiang(bazi.month_pillar.branch, is_earth_dominant)

        # Calculate raw values (without seasonal adjustment)
        raw_values: Dict[WuXing, float] = {element: 0.0 for element in WuXing}
        for pillar in bazi.pillars:
            stem_value, branch_value = self.get_pillar_values(pillar)
            raw_values[pillar.stem_wuxing] += stem_value
            for hidden_stem, ratio in pillar.hidden_stems.items():
                raw_values[hidden_stem.wuxing] += branch_value * ratio

        # Calculate adjusted values (with seasonal adjustment)
        adjusted_values = self.accumulate_wuxing_values(bazi, wang_xiang_map)

        return WuXingStrength(
            raw_values=raw_values,
            wang_xiang=wang_xiang_map,
            adjusted_values=adjusted_values,
        )

    def apply_branch_relations(
        self,
        values: Dict[WuXing, float],
        branch_analysis: BranchRelationsAnalysis,
    ) -> Dict[WuXing, float]:
        """
        Apply branch relation adjustments to WuXing values.

        三会局、三合局增强对应五行；六冲减弱双方五行。

        Args:
            values: Current WuXing strength values
            branch_analysis: Analyzed branch relationships

        Returns:
            Adjusted WuXing values with branch relation effects
        """
        result = dict(values)  # Copy

        # 三会局 - 最强加成
        for relation in branch_analysis.san_hui:
            if relation.element:
                result[relation.element] *= SAN_HUI_MULTIPLIER

        # 三合局 - 次强加成
        for relation in branch_analysis.san_he:
            if relation.element:
                result[relation.element] *= SAN_HE_MULTIPLIER

        # 半合局
        for relation in branch_analysis.ban_he:
            if relation.element:
                # TODO: 区分生旺半合和旺墓半合
                result[relation.element] *= BAN_HE_DEFAULT_MULTIPLIER

        # 六冲 - 双方减弱
        for relation in branch_analysis.chong:
            # 根据柱位判断距离
            pillars = relation.pillars
            multiplier = self._get_chong_multiplier(pillars)

            # 获取冲的两个地支的五行
            # 从 branches 中获取，branches 是中文字符如 ('子', '午')
            for branch_char in relation.branches:
                branch = EarthlyBranch.from_chinese(branch_char)
                result[branch.wuxing] *= multiplier

        return result

    @staticmethod
    def _get_chong_multiplier(pillars: Tuple[str, ...]) -> float:
        """
        Determine the clash multiplier based on pillar positions.

        紧贴冲（年月、月日、日时）最强 -30%
        隔支冲（年日、月时）次之 -20%
        遥冲（年时）最弱 -10%
        """
        if len(pillars) != 2:
            return CHONG_SEPARATED_MULTIPLIER

        # 柱位名称到索引的映射
        pillar_index = {'年': 0, '月': 1, '日': 2, '时': 3}
        try:
            idx1 = pillar_index[pillars[0]]
            idx2 = pillar_index[pillars[1]]
            distance = abs(idx1 - idx2)

            if distance == 1:  # 紧贴
                return CHONG_ADJACENT_MULTIPLIER
            elif distance == 2:  # 隔一支
                return CHONG_SEPARATED_MULTIPLIER
            else:  # 隔两支（年时遥冲）
                return CHONG_DISTANT_MULTIPLIER
        except (KeyError, IndexError):
            return CHONG_SEPARATED_MULTIPLIER

    def calculate_strength_with_relations(
        self,
        bazi: BaZi,
        branch_analysis: BranchRelationsAnalysis,
        is_earth_dominant: bool = False,
    ) -> WuXingStrength:
        """
        Calculate WuXing strength with branch relation adjustments.

        This method extends calculate_strength by applying
        三合、三会、六冲 effects to the element strengths.

        Args:
            bazi: The BaZi chart to analyze
            branch_analysis: Pre-analyzed branch relationships
            is_earth_dominant: Whether we're in earth-dominant period

        Returns:
            WuXingStrength with branch relation adjustments applied
        """
        # First calculate base strength
        base_strength = self.calculate_strength(bazi, is_earth_dominant)

        # Apply branch relations to adjusted values
        adjusted_with_relations = self.apply_branch_relations(
            base_strength.adjusted_values,
            branch_analysis,
        )

        return WuXingStrength(
            raw_values=base_strength.raw_values,
            wang_xiang=base_strength.wang_xiang,
            adjusted_values=adjusted_with_relations,
        )
