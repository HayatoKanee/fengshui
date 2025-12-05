"""
ShenSha (神煞) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ..models import (
    BaZi,
    Pillar,
    HeavenlyStem,
    EarthlyBranch,
    ShenShaType,
    ShenSha,
    ShenShaAnalysis,
)


# ShenSha lookup tables
# Format: (reference_branch_or_stem, target) -> True if match

# 天乙贵人 (Heavenly Noble) - based on day stem
_TIAN_YI_GUI_REN: Dict[HeavenlyStem, Set[EarthlyBranch]] = {
    HeavenlyStem.JIA: {EarthlyBranch.CHOU, EarthlyBranch.WEI},
    HeavenlyStem.WU: {EarthlyBranch.CHOU, EarthlyBranch.WEI},
    HeavenlyStem.GENG: {EarthlyBranch.CHOU, EarthlyBranch.WEI},
    HeavenlyStem.YI: {EarthlyBranch.ZI, EarthlyBranch.SHEN},
    HeavenlyStem.JI: {EarthlyBranch.ZI, EarthlyBranch.SHEN},
    HeavenlyStem.BING: {EarthlyBranch.HAI, EarthlyBranch.YOU},
    HeavenlyStem.DING: {EarthlyBranch.HAI, EarthlyBranch.YOU},
    HeavenlyStem.REN: {EarthlyBranch.MAO, EarthlyBranch.SI},
    HeavenlyStem.GUI: {EarthlyBranch.MAO, EarthlyBranch.SI},
    HeavenlyStem.XIN: {EarthlyBranch.WU, EarthlyBranch.YIN},
}

# 天德 (Heavenly Virtue) - based on month branch
_TIAN_DE: Dict[EarthlyBranch, HeavenlyStem] = {
    EarthlyBranch.YIN: HeavenlyStem.DING,
    EarthlyBranch.MAO: HeavenlyStem.GENG,  # Note: original was '申' but should be stem
    EarthlyBranch.CHEN: HeavenlyStem.REN,
    EarthlyBranch.SI: HeavenlyStem.XIN,
    EarthlyBranch.WU: HeavenlyStem.JIA,  # Note: original was '亥' but should be stem
    EarthlyBranch.WEI: HeavenlyStem.JIA,
    EarthlyBranch.SHEN: HeavenlyStem.GUI,
    EarthlyBranch.YOU: HeavenlyStem.BING,  # Note: original was '寅'
    EarthlyBranch.XU: HeavenlyStem.BING,
    EarthlyBranch.HAI: HeavenlyStem.YI,
    EarthlyBranch.ZI: HeavenlyStem.BING,  # Note: original was '巳'
    EarthlyBranch.CHOU: HeavenlyStem.GENG,
}

# 月德 (Monthly Virtue) - based on month branch
_YUE_DE: Dict[EarthlyBranch, HeavenlyStem] = {
    EarthlyBranch.YIN: HeavenlyStem.BING,
    EarthlyBranch.MAO: HeavenlyStem.JIA,
    EarthlyBranch.CHEN: HeavenlyStem.REN,
    EarthlyBranch.SI: HeavenlyStem.GENG,
    EarthlyBranch.WU: HeavenlyStem.BING,
    EarthlyBranch.WEI: HeavenlyStem.JIA,
    EarthlyBranch.SHEN: HeavenlyStem.REN,
    EarthlyBranch.YOU: HeavenlyStem.GENG,
    EarthlyBranch.XU: HeavenlyStem.BING,
    EarthlyBranch.HAI: HeavenlyStem.JIA,
    EarthlyBranch.ZI: HeavenlyStem.REN,
    EarthlyBranch.CHOU: HeavenlyStem.GENG,
}

# 文昌 (Literary Prosperity) - based on day stem
_WEN_CHANG: Dict[HeavenlyStem, EarthlyBranch] = {
    HeavenlyStem.JIA: EarthlyBranch.SI,
    HeavenlyStem.YI: EarthlyBranch.WU,
    HeavenlyStem.BING: EarthlyBranch.SHEN,
    HeavenlyStem.DING: EarthlyBranch.YOU,
    HeavenlyStem.WU: EarthlyBranch.SHEN,
    HeavenlyStem.JI: EarthlyBranch.YOU,
    HeavenlyStem.GENG: EarthlyBranch.HAI,
    HeavenlyStem.XIN: EarthlyBranch.ZI,
    HeavenlyStem.REN: EarthlyBranch.YIN,
    HeavenlyStem.GUI: EarthlyBranch.MAO,
}

# 禄神 (Prosperity Spirit) - based on day stem
_LU_SHEN: Dict[HeavenlyStem, EarthlyBranch] = {
    HeavenlyStem.JIA: EarthlyBranch.YIN,
    HeavenlyStem.YI: EarthlyBranch.MAO,
    HeavenlyStem.BING: EarthlyBranch.SI,
    HeavenlyStem.WU: EarthlyBranch.SI,
    HeavenlyStem.DING: EarthlyBranch.WU,
    HeavenlyStem.JI: EarthlyBranch.WU,
    HeavenlyStem.GENG: EarthlyBranch.SHEN,
    HeavenlyStem.XIN: EarthlyBranch.YOU,
    HeavenlyStem.REN: EarthlyBranch.HAI,
    HeavenlyStem.GUI: EarthlyBranch.ZI,
}

# 羊刃 (Goat Blade) - based on day stem
_YANG_REN: Dict[HeavenlyStem, EarthlyBranch] = {
    HeavenlyStem.JIA: EarthlyBranch.MAO,
    HeavenlyStem.YI: EarthlyBranch.CHEN,
    HeavenlyStem.BING: EarthlyBranch.WU,
    HeavenlyStem.WU: EarthlyBranch.WU,
    HeavenlyStem.DING: EarthlyBranch.WEI,
    HeavenlyStem.JI: EarthlyBranch.WEI,
    HeavenlyStem.GENG: EarthlyBranch.YOU,
    HeavenlyStem.XIN: EarthlyBranch.XU,
    HeavenlyStem.REN: EarthlyBranch.ZI,
    HeavenlyStem.GUI: EarthlyBranch.CHOU,
}

# 桃花 (Peach Blossom) - based on year/day branch
_TAO_HUA: Dict[EarthlyBranch, EarthlyBranch] = {
    EarthlyBranch.ZI: EarthlyBranch.YOU,
    EarthlyBranch.CHOU: EarthlyBranch.WU,
    EarthlyBranch.YIN: EarthlyBranch.MAO,
    EarthlyBranch.MAO: EarthlyBranch.ZI,
    EarthlyBranch.CHEN: EarthlyBranch.YOU,
    EarthlyBranch.SI: EarthlyBranch.WU,
    EarthlyBranch.WU: EarthlyBranch.MAO,
    EarthlyBranch.WEI: EarthlyBranch.ZI,
    EarthlyBranch.SHEN: EarthlyBranch.YOU,
    EarthlyBranch.YOU: EarthlyBranch.WU,
    EarthlyBranch.XU: EarthlyBranch.MAO,
    EarthlyBranch.HAI: EarthlyBranch.ZI,
}

# 驿马 (Traveling Horse) - based on year/day branch
_YI_MA: Dict[EarthlyBranch, EarthlyBranch] = {
    EarthlyBranch.ZI: EarthlyBranch.YIN,
    EarthlyBranch.CHOU: EarthlyBranch.HAI,
    EarthlyBranch.YIN: EarthlyBranch.SHEN,
    EarthlyBranch.MAO: EarthlyBranch.SI,
    EarthlyBranch.CHEN: EarthlyBranch.YIN,
    EarthlyBranch.SI: EarthlyBranch.HAI,
    EarthlyBranch.WU: EarthlyBranch.SHEN,
    EarthlyBranch.WEI: EarthlyBranch.SI,
    EarthlyBranch.SHEN: EarthlyBranch.YIN,
    EarthlyBranch.YOU: EarthlyBranch.HAI,
    EarthlyBranch.XU: EarthlyBranch.SHEN,
    EarthlyBranch.HAI: EarthlyBranch.SI,
}

# 华盖 (Canopy Star) - based on year/day branch
_HUA_GAI: Dict[EarthlyBranch, EarthlyBranch] = {
    EarthlyBranch.ZI: EarthlyBranch.CHEN,
    EarthlyBranch.CHOU: EarthlyBranch.CHOU,
    EarthlyBranch.YIN: EarthlyBranch.XU,
    EarthlyBranch.MAO: EarthlyBranch.WEI,
    EarthlyBranch.CHEN: EarthlyBranch.CHEN,
    EarthlyBranch.SI: EarthlyBranch.CHOU,
    EarthlyBranch.WU: EarthlyBranch.XU,
    EarthlyBranch.WEI: EarthlyBranch.WEI,
    EarthlyBranch.SHEN: EarthlyBranch.CHEN,
    EarthlyBranch.YOU: EarthlyBranch.CHOU,
    EarthlyBranch.XU: EarthlyBranch.XU,
    EarthlyBranch.HAI: EarthlyBranch.WEI,
}

# 将星 (General Star) - based on year/day branch
_JIANG_XING: Dict[EarthlyBranch, EarthlyBranch] = {
    EarthlyBranch.ZI: EarthlyBranch.ZI,
    EarthlyBranch.CHOU: EarthlyBranch.YOU,
    EarthlyBranch.YIN: EarthlyBranch.WU,
    EarthlyBranch.MAO: EarthlyBranch.MAO,
    EarthlyBranch.CHEN: EarthlyBranch.ZI,
    EarthlyBranch.SI: EarthlyBranch.YOU,
    EarthlyBranch.WU: EarthlyBranch.WU,
    EarthlyBranch.WEI: EarthlyBranch.MAO,
    EarthlyBranch.SHEN: EarthlyBranch.ZI,
    EarthlyBranch.YOU: EarthlyBranch.YOU,
    EarthlyBranch.XU: EarthlyBranch.WU,
    EarthlyBranch.HAI: EarthlyBranch.MAO,
}


class ShenShaCalculator:
    """
    Calculator for ShenSha (auxiliary stars/spirits).

    ShenSha are secondary indicators that provide additional
    information about luck, personality, and life events.
    """

    def is_tian_yi_gui_ren(self, day_stem: HeavenlyStem, branch: EarthlyBranch) -> bool:
        """Check if a branch is Heavenly Noble for this day stem."""
        targets = _TIAN_YI_GUI_REN.get(day_stem, set())
        return branch in targets

    def is_tian_de(self, month_branch: EarthlyBranch, stem: HeavenlyStem) -> bool:
        """Check if a stem is Heavenly Virtue for this month."""
        target = _TIAN_DE.get(month_branch)
        return target == stem if target else False

    def is_yue_de(self, month_branch: EarthlyBranch, stem: HeavenlyStem) -> bool:
        """Check if a stem is Monthly Virtue for this month."""
        target = _YUE_DE.get(month_branch)
        return target == stem if target else False

    def is_wen_chang(self, day_stem: HeavenlyStem, branch: EarthlyBranch) -> bool:
        """Check if a branch is Literary Prosperity for this day stem."""
        target = _WEN_CHANG.get(day_stem)
        return target == branch if target else False

    def is_lu_shen(self, day_stem: HeavenlyStem, branch: EarthlyBranch) -> bool:
        """Check if a branch is Prosperity Spirit for this day stem."""
        target = _LU_SHEN.get(day_stem)
        return target == branch if target else False

    def is_yang_ren(self, day_stem: HeavenlyStem, branch: EarthlyBranch) -> bool:
        """Check if a branch is Goat Blade for this day stem."""
        target = _YANG_REN.get(day_stem)
        return target == branch if target else False

    def is_tao_hua(self, ref_branch: EarthlyBranch, target_branch: EarthlyBranch) -> bool:
        """Check if target_branch is Peach Blossom based on year/day branch."""
        target = _TAO_HUA.get(ref_branch)
        return target == target_branch if target else False

    def is_yi_ma(self, ref_branch: EarthlyBranch, target_branch: EarthlyBranch) -> bool:
        """Check if target_branch is Traveling Horse based on year/day branch."""
        target = _YI_MA.get(ref_branch)
        return target == target_branch if target else False

    def is_hua_gai(self, ref_branch: EarthlyBranch, target_branch: EarthlyBranch) -> bool:
        """Check if target_branch is Canopy Star based on year/day branch."""
        target = _HUA_GAI.get(ref_branch)
        return target == target_branch if target else False

    def is_jiang_xing(self, ref_branch: EarthlyBranch, target_branch: EarthlyBranch) -> bool:
        """Check if target_branch is General Star based on year/day branch."""
        target = _JIANG_XING.get(ref_branch)
        return target == target_branch if target else False

    def calculate_for_bazi(self, bazi: BaZi) -> ShenShaAnalysis:
        """
        Calculate all ShenSha for a BaZi chart.

        Args:
            bazi: The BaZi chart to analyze

        Returns:
            ShenShaAnalysis containing all found ShenSha
        """
        shensha_list: List[ShenSha] = []
        day_stem = bazi.day_master
        month_branch = bazi.month_pillar.branch
        year_branch = bazi.year_pillar.branch
        day_branch = bazi.day_pillar.branch

        positions = [
            ("year", bazi.year_pillar),
            ("month", bazi.month_pillar),
            ("day", bazi.day_pillar),
            ("hour", bazi.hour_pillar),
        ]

        for pos_name, pillar in positions:
            branch = pillar.branch
            stem = pillar.stem

            # Check 天乙贵人 (based on day stem → branch)
            if self.is_tian_yi_gui_ren(day_stem, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_YI_GUI_REN,
                    position=f"{pos_name}_branch",
                    triggered_by=day_stem.chinese,
                ))

            # Check 天德 (based on month branch → stem)
            if self.is_tian_de(month_branch, stem):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE,
                    position=f"{pos_name}_stem",
                    triggered_by=month_branch.chinese,
                ))

            # Check 月德 (based on month branch → stem)
            if self.is_yue_de(month_branch, stem):
                shensha_list.append(ShenSha(
                    type=ShenShaType.YUE_DE,
                    position=f"{pos_name}_stem",
                    triggered_by=month_branch.chinese,
                ))

            # Check 文昌 (based on day stem → branch)
            if self.is_wen_chang(day_stem, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.WEN_CHANG,
                    position=f"{pos_name}_branch",
                    triggered_by=day_stem.chinese,
                ))

            # Check 禄神 (based on day stem → branch)
            if self.is_lu_shen(day_stem, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.LU_SHEN,
                    position=f"{pos_name}_branch",
                    triggered_by=day_stem.chinese,
                ))

            # Check 羊刃 (based on day stem → branch)
            if self.is_yang_ren(day_stem, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.YANG_REN,
                    position=f"{pos_name}_branch",
                    triggered_by=day_stem.chinese,
                ))

            # Check 桃花 (based on year branch → other branches)
            if pos_name != "year" and self.is_tao_hua(year_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TAO_HUA,
                    position=f"{pos_name}_branch",
                    triggered_by=year_branch.chinese,
                ))

            # Also check 桃花 based on day branch
            if pos_name not in ("year", "day") and self.is_tao_hua(day_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TAO_HUA,
                    position=f"{pos_name}_branch",
                    triggered_by=day_branch.chinese,
                ))

            # Check 驿马 (based on year branch → other branches)
            if pos_name != "year" and self.is_yi_ma(year_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.YI_MA,
                    position=f"{pos_name}_branch",
                    triggered_by=year_branch.chinese,
                ))

            # Check 华盖 (based on year branch → other branches)
            if self.is_hua_gai(year_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.HUA_GAI,
                    position=f"{pos_name}_branch",
                    triggered_by=year_branch.chinese,
                ))

            # Check 将星 (based on year branch → other branches)
            if self.is_jiang_xing(year_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.JIANG_XING,
                    position=f"{pos_name}_branch",
                    triggered_by=year_branch.chinese,
                ))

        return ShenShaAnalysis(shensha_list=shensha_list)

    def get_shensha_summary(self, bazi: BaZi) -> Dict[str, List[str]]:
        """
        Get a summary of ShenSha organized by category.

        Returns:
            Dictionary with categories as keys and lists of ShenSha names
        """
        analysis = self.calculate_for_bazi(bazi)
        summary: Dict[str, List[str]] = {
            "贵人": [],
            "德星": [],
            "文星": [],
            "禄星": [],
            "桃花": [],
            "驿马": [],
            "刃星": [],
            "艺术": [],
            "将星": [],
            "其他": [],
        }

        for ss in analysis.shensha_list:
            category = ss.type.category
            if category in summary:
                if ss.chinese not in summary[category]:
                    summary[category].append(ss.chinese)
            else:
                if ss.chinese not in summary["其他"]:
                    summary["其他"].append(ss.chinese)

        # Remove empty categories
        return {k: v for k, v in summary.items() if v}
