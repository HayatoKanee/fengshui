"""
ShenSha (神煞) calculation service.

使用声明式规则系统，遵循 SOLID 原则：

- S: Calculator 只负责协调规则执行
- O: 添加新神煞不需要修改此文件
- L: 所有规则实现 ShenShaRule Protocol
- I: 依赖精简的 Protocol 接口
- D: 依赖抽象（Protocol），不依赖具体规则实现

核心逻辑只有 3 行：
    for rule in rules:
        results.extend(rule.find_matches(bazi))
    return ShenShaAnalysis(shensha_list=results)

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

from ..models import (
    BaZi,
    ShenShaType,
    ShenSha,
    ShenShaAnalysis,
)
from ..models.shensha_rule import ShenShaRule, ShenShaRuleRegistry

if TYPE_CHECKING:
    from ..models import HeavenlyStem, EarthlyBranch


class ShenShaCalculator:
    """
    Calculator for ShenSha (auxiliary stars/spirits).

    使用声明式规则系统，核心计算逻辑极其简单：
    遍历所有规则，收集匹配结果。

    添加新神煞只需在 constants/shensha_rules.py 中添加规则，
    不需要修改此类的任何代码。

    Attributes:
        _rules: 规则列表，支持依赖注入用于测试

    Example:
        >>> calculator = ShenShaCalculator()
        >>> analysis = calculator.calculate_for_bazi(bazi)
        >>> print(analysis.beneficial)  # 吉星列表

        # 使用自定义规则（用于测试）
        >>> custom_rules = [MyTestRule()]
        >>> calculator = ShenShaCalculator(rules=custom_rules)
    """

    def __init__(self, rules: List[ShenShaRule] | None = None):
        """
        Initialize calculator with optional custom rules.

        Args:
            rules: Custom rules for testing. If None, uses default rules from registry.
        """
        self._rules = rules

    @property
    def rules(self) -> List[ShenShaRule]:
        """Get active rules (lazy loading from registry if not injected)."""
        if self._rules is None:
            self._rules = ShenShaRuleRegistry.all_rules()
        return self._rules

    def calculate_for_bazi(self, bazi: BaZi) -> ShenShaAnalysis:
        """
        Calculate all ShenSha for a BaZi chart.

        This is the core method. It simply iterates over all rules
        and collects their matches. The actual matching logic is
        encapsulated in each rule.

        Args:
            bazi: The BaZi chart to analyze

        Returns:
            ShenShaAnalysis containing all found ShenSha
        """
        results: List[ShenSha] = []

        # Core logic: just iterate over rules
        for rule in self.rules:
            results.extend(rule.find_matches(bazi))

        return ShenShaAnalysis(shensha_list=results)

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
            "凶煞": [],
            "孤寡": [],
            "空亡": [],
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

    # ==================================================================
    # 向后兼容的便捷方法
    # 这些方法保留原有 API，内部使用 constants/shensha.py 中的查表
    # ==================================================================

    def is_tian_yi_gui_ren(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if a branch is Heavenly Noble for this day stem."""
        from ..constants.shensha import GUI_REN
        return (day_stem.chinese, branch.chinese) in GUI_REN

    def is_tian_de(
        self, month_branch: "EarthlyBranch", target: "HeavenlyStem | EarthlyBranch"
    ) -> bool:
        """Check if a stem or branch is Heavenly Virtue for this month."""
        from ..constants.shensha import TIAN_DE
        return (month_branch.chinese, target.chinese) in TIAN_DE

    def is_tian_de_he(
        self, month_branch: "EarthlyBranch", target: "HeavenlyStem | EarthlyBranch"
    ) -> bool:
        """Check if a stem or branch is Heavenly Virtue Combination."""
        from ..constants.shensha import TIAN_DE_HE
        return (month_branch.chinese, target.chinese) in TIAN_DE_HE

    def is_yue_de(
        self, month_branch: "EarthlyBranch", stem: "HeavenlyStem"
    ) -> bool:
        """Check if a stem is Monthly Virtue for this month."""
        from ..constants.shensha import YUE_DE
        return (month_branch.chinese, stem.chinese) in YUE_DE

    def is_yue_de_he(
        self, month_branch: "EarthlyBranch", stem: "HeavenlyStem"
    ) -> bool:
        """Check if a stem is Monthly Virtue Combination for this month."""
        from ..constants.shensha import YUE_DE_HE
        return (month_branch.chinese, stem.chinese) in YUE_DE_HE

    def is_wen_chang(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if a branch is Literary Prosperity for this day stem."""
        from ..constants.shensha import WEN_CHANG
        return (day_stem.chinese, branch.chinese) in WEN_CHANG

    def is_lu_shen(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if a branch is Prosperity Spirit for this day stem."""
        from ..constants.shensha import LU_SHEN
        return (day_stem.chinese, branch.chinese) in LU_SHEN

    def is_yang_ren(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if a branch is Goat Blade for this day stem."""
        from ..constants.shensha import YANG_REN
        return (day_stem.chinese, branch.chinese) in YANG_REN

    def is_tao_hua(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Peach Blossom based on year/day branch."""
        from ..constants.shensha import TAO_HUA
        return (ref_branch.chinese, target_branch.chinese) in TAO_HUA

    def is_yi_ma(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Traveling Horse based on year/day branch."""
        from ..constants.shensha import YI_MA
        return (ref_branch.chinese, target_branch.chinese) in YI_MA

    def is_hua_gai(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Canopy Star based on year/day branch."""
        from ..constants.shensha import HUA_GAI
        return (ref_branch.chinese, target_branch.chinese) in HUA_GAI

    def is_jiang_xing(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is General Star based on year/day branch."""
        from ..constants.shensha import JIANG_XING
        return (ref_branch.chinese, target_branch.chinese) in JIANG_XING

    def is_jie_sha(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Robbery Star based on year/day branch."""
        from ..constants.shensha import JIE_SHA
        return (ref_branch.chinese, target_branch.chinese) in JIE_SHA

    def is_wang_shen(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Death Spirit based on year/day branch."""
        from ..constants.shensha import WANG_SHEN
        return (ref_branch.chinese, target_branch.chinese) in WANG_SHEN

    def is_gu_chen(
        self, year_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Lone Star based on year branch."""
        from ..constants.shensha import GU_CHEN
        return (year_branch.chinese, target_branch.chinese) in GU_CHEN

    def is_gua_su(
        self, year_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is Widowhood Star based on year branch."""
        from ..constants.shensha import GUA_SU
        return (year_branch.chinese, target_branch.chinese) in GUA_SU

    def is_hong_yan_sha(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if a branch is Red Romance Star for this day stem."""
        from ..constants.shensha import HONG_YAN_SHA
        return (day_stem.chinese, branch.chinese) in HONG_YAN_SHA

    def is_kong_wang(
        self, day_pillar_chinese: str, branch_chinese: str
    ) -> bool:
        """Check if a branch is in void/emptiness for this day pillar."""
        from ..constants.shensha import XUN_KONG
        kong_branches = XUN_KONG.get(day_pillar_chinese, [])
        return branch_chinese in kong_branches
