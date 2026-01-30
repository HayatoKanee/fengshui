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

from typing import Dict, FrozenSet, List, Tuple, TYPE_CHECKING

from ..models import (
    BaZi,
    ShenShaAnalysis,
)
from ..models.shensha import get_all_categories
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
        results = []
        for rule in self.rules:
            results.extend(rule.find_matches(bazi))
        return ShenShaAnalysis(shensha_list=results)

    def get_shensha_summary(self, bazi: BaZi) -> Dict[str, List[str]]:
        """
        Get a summary of ShenSha organized by category.

        Categories are derived from SHENSHA_CATEGORIES - single source of truth.

        Returns:
            Dictionary with categories as keys and lists of ShenSha names
        """
        analysis = self.calculate_for_bazi(bazi)

        # Initialize from single source of truth
        summary: Dict[str, List[str]] = {cat: [] for cat in get_all_categories()}

        for ss in analysis.shensha_list:
            category = ss.type.category
            if ss.chinese not in summary[category]:
                summary[category].append(ss.chinese)

        # Remove empty categories
        return {k: v for k, v in summary.items() if v}

    # ==================================================================
    # Generic lookup method for backward compatibility
    # ==================================================================

    def check_in_table(
        self,
        table: FrozenSet[Tuple[str, str]],
        ref: "HeavenlyStem | EarthlyBranch",
        target: "HeavenlyStem | EarthlyBranch",
    ) -> bool:
        """
        Generic table lookup for any ShenSha.

        This single method replaces all individual is_xxx() methods.
        All lookup tables are in constants/shensha.py.

        Args:
            table: The lookup table (e.g., GUI_REN, TAO_HUA)
            ref: Reference stem/branch (e.g., day_stem, year_branch)
            target: Target stem/branch to check

        Returns:
            True if (ref, target) exists in table

        Example:
            >>> from bazi.domain.constants.shensha import GUI_REN, TAO_HUA
            >>> calculator.check_in_table(GUI_REN, day_stem, branch)
            >>> calculator.check_in_table(TAO_HUA, year_branch, target_branch)
        """
        return (ref.chinese, target.chinese) in table

    # ==================================================================
    # Convenience methods using check_in_table (backward compatibility)
    # These are thin wrappers - logic is NOT duplicated
    # ==================================================================

    def is_tian_yi_gui_ren(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if branch is 天乙贵人 for this day stem."""
        from ..constants.shensha import GUI_REN
        return self.check_in_table(GUI_REN, day_stem, branch)

    def is_tian_de(
        self, month_branch: "EarthlyBranch", target: "HeavenlyStem | EarthlyBranch"
    ) -> bool:
        """Check if target is 天德 for this month."""
        from ..constants.shensha import TIAN_DE
        return self.check_in_table(TIAN_DE, month_branch, target)

    def is_tian_de_he(
        self, month_branch: "EarthlyBranch", target: "HeavenlyStem | EarthlyBranch"
    ) -> bool:
        """Check if target is 天德合 for this month."""
        from ..constants.shensha import TIAN_DE_HE
        return self.check_in_table(TIAN_DE_HE, month_branch, target)

    def is_yue_de(
        self, month_branch: "EarthlyBranch", stem: "HeavenlyStem"
    ) -> bool:
        """Check if stem is 月德 for this month."""
        from ..constants.shensha import YUE_DE
        return self.check_in_table(YUE_DE, month_branch, stem)

    def is_wen_chang(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if branch is 文昌 for this day stem."""
        from ..constants.shensha import WEN_CHANG
        return self.check_in_table(WEN_CHANG, day_stem, branch)

    def is_lu_shen(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if branch is 禄神 for this day stem."""
        from ..constants.shensha import LU_SHEN
        return self.check_in_table(LU_SHEN, day_stem, branch)

    def is_yang_ren(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if branch is 羊刃 for this day stem."""
        from ..constants.shensha import YANG_REN
        return self.check_in_table(YANG_REN, day_stem, branch)

    def is_tao_hua(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 桃花 for this ref branch."""
        from ..constants.shensha import TAO_HUA
        return self.check_in_table(TAO_HUA, ref_branch, target_branch)

    def is_yi_ma(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 驿马 for this ref branch."""
        from ..constants.shensha import YI_MA
        return self.check_in_table(YI_MA, ref_branch, target_branch)

    def is_hua_gai(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 华盖 for this ref branch."""
        from ..constants.shensha import HUA_GAI
        return self.check_in_table(HUA_GAI, ref_branch, target_branch)

    def is_jiang_xing(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 将星 for this ref branch."""
        from ..constants.shensha import JIANG_XING
        return self.check_in_table(JIANG_XING, ref_branch, target_branch)

    def is_jie_sha(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 劫煞 for this ref branch."""
        from ..constants.shensha import JIE_SHA
        return self.check_in_table(JIE_SHA, ref_branch, target_branch)

    def is_wang_shen(
        self, ref_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 亡神 for this ref branch."""
        from ..constants.shensha import WANG_SHEN
        return self.check_in_table(WANG_SHEN, ref_branch, target_branch)

    def is_gu_chen(
        self, year_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 孤辰 for this year branch."""
        from ..constants.shensha import GU_CHEN
        return self.check_in_table(GU_CHEN, year_branch, target_branch)

    def is_gua_su(
        self, year_branch: "EarthlyBranch", target_branch: "EarthlyBranch"
    ) -> bool:
        """Check if target_branch is 寡宿 for this year branch."""
        from ..constants.shensha import GUA_SU
        return self.check_in_table(GUA_SU, year_branch, target_branch)

    def is_hong_yan_sha(
        self, day_stem: "HeavenlyStem", branch: "EarthlyBranch"
    ) -> bool:
        """Check if branch is 红艳煞 for this day stem."""
        from ..constants.shensha import HONG_YAN_SHA
        return self.check_in_table(HONG_YAN_SHA, day_stem, branch)

    def is_kong_wang(
        self, day_pillar_chinese: str, branch_chinese: str
    ) -> bool:
        """
        Check if branch is 空亡 for this day pillar.

        Note: This uses different logic (list lookup) so cannot use check_in_table.
        """
        from ..constants.shensha import XUN_KONG
        kong_branches = XUN_KONG.get(day_pillar_chinese, [])
        return branch_chinese in kong_branches
