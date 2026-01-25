"""
ShenSha (神煞) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Set, Union

from ..models import (
    BaZi,
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
# 古诀：寅月丁。卯月申。辰月壬。巳月辛。午月亥。未月甲。
#       申月癸。酉月寅。戌月丙。亥月乙。子月巳。丑月庚。
# 注意：卯、午、酉、子月查地支，其余月份查天干
_TIAN_DE: Dict[EarthlyBranch, Union[HeavenlyStem, EarthlyBranch]] = {
    # 寅申巳亥月 - 配阴干
    EarthlyBranch.YIN: HeavenlyStem.DING,   # 寅月见丁
    EarthlyBranch.SI: HeavenlyStem.XIN,     # 巳月见辛
    EarthlyBranch.SHEN: HeavenlyStem.GUI,   # 申月见癸
    EarthlyBranch.HAI: HeavenlyStem.YI,     # 亥月见乙
    # 辰戌丑未月 - 配阳干
    EarthlyBranch.CHEN: HeavenlyStem.REN,   # 辰月见壬
    EarthlyBranch.XU: HeavenlyStem.BING,    # 戌月见丙
    EarthlyBranch.CHOU: HeavenlyStem.GENG,  # 丑月见庚
    EarthlyBranch.WEI: HeavenlyStem.JIA,    # 未月见甲
    # 子午卯酉月 - 配地支（墓库位置）
    EarthlyBranch.MAO: EarthlyBranch.SHEN,  # 卯月见申
    EarthlyBranch.WU: EarthlyBranch.HAI,    # 午月见亥
    EarthlyBranch.YOU: EarthlyBranch.YIN,   # 酉月见寅
    EarthlyBranch.ZI: EarthlyBranch.SI,     # 子月见巳
}

# 天德合 (Heavenly Virtue Combination) - 天德的合者
# 古诀：寅月壬。卯月巳。辰月丁。巳月丙。午月寅。未月己。
#       申月戊。酉月亥。戌月辛。亥月庚。子月申。丑月乙。
# 原理：天德与天干五合或地支六合者即为天德合
_TIAN_DE_HE: Dict[EarthlyBranch, Union[HeavenlyStem, EarthlyBranch]] = {
    # 天干五合对应
    EarthlyBranch.YIN: HeavenlyStem.REN,    # 丁壬合
    EarthlyBranch.CHEN: HeavenlyStem.DING,  # 壬丁合
    EarthlyBranch.SI: HeavenlyStem.BING,    # 辛丙合
    EarthlyBranch.WEI: HeavenlyStem.JI,     # 甲己合
    EarthlyBranch.SHEN: HeavenlyStem.WU,    # 癸戊合
    EarthlyBranch.XU: HeavenlyStem.XIN,     # 丙辛合
    EarthlyBranch.HAI: HeavenlyStem.GENG,   # 乙庚合
    EarthlyBranch.CHOU: HeavenlyStem.YI,    # 庚乙合
    # 地支六合对应
    EarthlyBranch.MAO: EarthlyBranch.SI,    # 巳申合
    EarthlyBranch.WU: EarthlyBranch.YIN,    # 寅亥合
    EarthlyBranch.YOU: EarthlyBranch.HAI,   # 寅亥合
    EarthlyBranch.ZI: EarthlyBranch.SHEN,   # 巳申合
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

    def is_tian_de(
        self,
        month_branch: EarthlyBranch,
        target: Union[HeavenlyStem, EarthlyBranch]
    ) -> bool:
        """
        Check if a stem or branch is Heavenly Virtue for this month.

        天德贵人查法：以月支查四柱干支
        - 寅申巳亥月配阴干
        - 辰戌丑未月配阳干
        - 子午卯酉月配地支
        """
        expected = _TIAN_DE.get(month_branch)
        if expected is None:
            return False
        # 天德可能是天干或地支，需要类型匹配
        if isinstance(expected, HeavenlyStem) and isinstance(target, HeavenlyStem):
            return expected == target
        elif isinstance(expected, EarthlyBranch) and isinstance(target, EarthlyBranch):
            return expected == target
        return False

    def is_tian_de_he(
        self,
        month_branch: EarthlyBranch,
        target: Union[HeavenlyStem, EarthlyBranch]
    ) -> bool:
        """
        Check if a stem or branch is Heavenly Virtue Combination for this month.

        天德合：天德的五合（天干）或六合（地支）对应
        效果为天德的一半
        """
        expected = _TIAN_DE_HE.get(month_branch)
        if expected is None:
            return False
        if isinstance(expected, HeavenlyStem) and isinstance(target, HeavenlyStem):
            return expected == target
        elif isinstance(expected, EarthlyBranch) and isinstance(target, EarthlyBranch):
            return expected == target
        return False

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

            # Check 天德 (based on month branch → stem or branch)
            # 天德可能是天干或地支，需要分别检查
            if self.is_tian_de(month_branch, stem):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE,
                    position=f"{pos_name}_stem",
                    triggered_by=month_branch.chinese,
                ))
            if self.is_tian_de(month_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE,
                    position=f"{pos_name}_branch",
                    triggered_by=month_branch.chinese,
                ))

            # Check 天德合 (based on month branch → stem or branch)
            if self.is_tian_de_he(month_branch, stem):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE_HE,
                    position=f"{pos_name}_stem",
                    triggered_by=month_branch.chinese,
                ))
            if self.is_tian_de_he(month_branch, branch):
                shensha_list.append(ShenSha(
                    type=ShenShaType.TIAN_DE_HE,
                    position=f"{pos_name}_branch",
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
