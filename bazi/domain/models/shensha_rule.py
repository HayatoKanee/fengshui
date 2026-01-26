"""
ShenSha Rule Protocol and Implementations.

使用 Protocol 模式定义神煞规则接口，实现 SOLID 原则：

- S: 每个规则类只负责一个神煞的判断
- O: 添加新神煞只需添加新规则，不修改计算器
- L: 所有规则实现相同 Protocol，可互换
- I: Protocol 接口精简，只有必要方法
- D: Calculator 依赖 Protocol 抽象，不依赖具体实现

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    FrozenSet,
    List,
    Protocol,
    Tuple,
    runtime_checkable,
)

# Import extractors from shared module (DRY principle)
from .shensha_extractors import (
    RefExtractor,
    TargetExtractor,
    day_stem_extractor,
    month_branch_extractor,
    year_branch_extractor,
    day_branch_extractor,
    day_pillar_extractor,
    branch_target,
    stem_target,
    stem_and_branch_target,
)

if TYPE_CHECKING:
    from .bazi import BaZi
    from .pillar import Pillar
    from .shensha import ShenSha, ShenShaType


# ============================================================
# Protocol Definition (Interface)
# ============================================================

@runtime_checkable
class ShenShaRule(Protocol):
    """
    Protocol for ShenSha rules.

    所有神煞规则必须实现此接口。使用 Protocol 而非 ABC，
    支持结构化子类型（structural subtyping / duck typing）。

    Example:
        >>> class MyRule:
        ...     @property
        ...     def shensha_type(self) -> ShenShaType: ...
        ...     def find_matches(self, bazi: BaZi) -> List[ShenSha]: ...
        >>> isinstance(MyRule(), ShenShaRule)  # True
    """

    @property
    def shensha_type(self) -> "ShenShaType":
        """The ShenSha type this rule detects."""
        ...

    def find_matches(self, bazi: "BaZi") -> List["ShenSha"]:
        """
        Find all occurrences of this ShenSha in a BaZi chart.

        Args:
            bazi: The BaZi chart to analyze

        Returns:
            List of ShenSha instances found (may be empty)
        """
        ...


# ============================================================
# Table-Driven Rule Implementation
# ============================================================

@dataclass(frozen=True)
class TableLookupRule:
    """
    Generic table-driven ShenSha rule.

    Most ShenSha (90%+) can be expressed as simple table lookups:
    - Extract reference value(s) from BaZi (e.g., day_stem, year_branch)
    - For each pillar, extract target value(s) (e.g., branch)
    - Check if (ref, target) exists in lookup table

    This dataclass captures all the variation points, allowing
    new ShenSha to be added without writing new code.

    Attributes:
        type_name: ShenShaType enum name (string for lazy resolution)
        lookup_table: FrozenSet of (ref, target) tuples
        ref_extractors: Tuple of functions to extract reference from BaZi
                       (supports multiple, e.g., both year_branch and day_branch for 桃花)
        target_extractor: Function to extract target(s) from Pillar
        positions: Which pillar positions to check
        exclude_positions: Positions to exclude (e.g., ("year",) for 驿马)

    Example:
        >>> rule = TableLookupRule(
        ...     type_name="TIAN_YI_GUI_REN",
        ...     lookup_table=frozenset([("甲", "丑"), ("甲", "未"), ...]),
        ...     ref_extractors=(day_stem_extractor,),
        ...     target_extractor=branch_target,
        ... )

        # Multiple ref extractors (桃花同时用年支和日支)
        >>> rule = TableLookupRule(
        ...     type_name="TAO_HUA",
        ...     lookup_table=TAO_HUA,
        ...     ref_extractors=(year_branch_extractor, day_branch_extractor),
        ...     target_extractor=branch_target,
        ...     exclude_positions=("year",),
        ... )
    """
    type_name: str
    lookup_table: FrozenSet[Tuple[str, str]]
    ref_extractors: Tuple[RefExtractor, ...]
    target_extractor: TargetExtractor
    positions: Tuple[str, ...] = ("year", "month", "day", "hour")
    exclude_positions: Tuple[str, ...] = ()

    @property
    def shensha_type(self) -> "ShenShaType":
        """Lazy resolution of ShenShaType enum."""
        from .shensha import ShenShaType
        return ShenShaType[self.type_name]

    def find_matches(self, bazi: "BaZi") -> List["ShenSha"]:
        """Find all matches using table lookup."""
        from .shensha import ShenSha

        results: List[ShenSha] = []

        # Iterate over all ref extractors
        for ref_extractor in self.ref_extractors:
            ref_value = ref_extractor(bazi)

            # Check each position
            for pos_name in self.positions:
                if pos_name in self.exclude_positions:
                    continue

                pillar = self._get_pillar(bazi, pos_name)
                targets = self.target_extractor(pillar)

                for target_value, position_suffix in targets:
                    if (ref_value, target_value) in self.lookup_table:
                        new_shensha = ShenSha(
                            type=self.shensha_type,
                            position=f"{pos_name}_{position_suffix}",
                            triggered_by=ref_value,
                        )
                        # Avoid duplicates
                        if new_shensha not in results:
                            results.append(new_shensha)

        return results

    @staticmethod
    def _get_pillar(bazi: "BaZi", pos_name: str) -> "Pillar":
        """Get pillar by position name."""
        return getattr(bazi, f"{pos_name}_pillar")


# ============================================================
# Special Rule Implementations
# ============================================================

@dataclass(frozen=True)
class KongWangRule:
    """
    空亡 (Void/Emptiness) rule.

    空亡需要特殊处理：以日柱确定旬空，检查四柱地支是否落入空亡。
    不能用简单的 (ref, target) 表查找。
    """
    xun_kong_table: dict[str, List[str]] = field(default_factory=dict)

    @property
    def shensha_type(self) -> "ShenShaType":
        from .shensha import ShenShaType
        return ShenShaType.KONG_WANG

    def find_matches(self, bazi: "BaZi") -> List["ShenSha"]:
        from .shensha import ShenSha

        results: List[ShenSha] = []
        day_pillar = bazi.day_pillar.chinese
        kong_branches = self.xun_kong_table.get(day_pillar, [])

        if not kong_branches:
            return results

        positions = [
            ("year", bazi.year_pillar),
            ("month", bazi.month_pillar),
            ("day", bazi.day_pillar),
            ("hour", bazi.hour_pillar),
        ]

        for pos_name, pillar in positions:
            if pillar.branch.chinese in kong_branches:
                results.append(ShenSha(
                    type=self.shensha_type,
                    position=f"{pos_name}_branch",
                    triggered_by=day_pillar,
                ))

        return results


@dataclass(frozen=True)
class SanQiRule:
    """
    三奇 (Three Wonders) rule.

    三奇需要检查天干在连续三柱中顺序出现：
    - 天上三奇：乙丙丁（年月日 或 月日时）
    - 地上三奇：甲戊庚（年月日 或 月日时）
    - 人中三奇：辛壬癸（年月日 或 月日时）

    关键规则（参考《八字金书》《渊海子平》）：
    1. 必须在连续三柱中顺序出现（年月日 或 月日时）
    2. 顺序不可颠倒，否则不算三奇
    3. 不可散落在四柱中（如年-X-日-时）

    "凡三奇需要顺，有不依次者，亦得半力"
    """
    # 三组三奇
    san_qi_groups: Tuple[Tuple[str, str, str], ...] = (
        ("乙", "丙", "丁"),  # 天上三奇
        ("甲", "戊", "庚"),  # 地上三奇
        ("辛", "壬", "癸"),  # 人中三奇
    )

    @property
    def shensha_type(self) -> "ShenShaType":
        from .shensha import ShenShaType
        return ShenShaType.SAN_QI

    def find_matches(self, bazi: "BaZi") -> List["ShenSha"]:
        from .shensha import ShenSha

        # Get stems in order: year, month, day, hour
        stems = (
            bazi.year_pillar.stem.chinese,
            bazi.month_pillar.stem.chinese,
            bazi.day_pillar.stem.chinese,
            bazi.hour_pillar.stem.chinese,
        )

        # 检查年月日 或 月日时 是否匹配三奇（必须连续三柱）
        year_month_day = (stems[0], stems[1], stems[2])
        month_day_hour = (stems[1], stems[2], stems[3])

        for group in self.san_qi_groups:
            if year_month_day == group or month_day_hour == group:
                return [ShenSha(
                    type=self.shensha_type,
                    position="chart",
                    triggered_by="".join(group),
                )]

        return []


# ============================================================
# Rule Registry
# ============================================================

class ShenShaRuleRegistry:
    """
    Central registry for all ShenSha rules.

    Provides a single point of access to all rule instances.
    Supports dependency injection by allowing custom rule sets.
    """
    _rules: List[ShenShaRule] = []
    _initialized: bool = False

    @classmethod
    def register(cls, rule: ShenShaRule) -> ShenShaRule:
        """Register a rule instance."""
        cls._rules.append(rule)
        return rule

    @classmethod
    def all_rules(cls) -> List[ShenShaRule]:
        """Get all registered rules."""
        if not cls._initialized:
            cls._initialize_default_rules()
        return cls._rules.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all rules (for testing)."""
        cls._rules = []
        cls._initialized = False

    @classmethod
    def _initialize_default_rules(cls) -> None:
        """Initialize default rules from Registry."""
        from .shensha_registry import ShenShaRegistry, _XUN_KONG

        rules: List[ShenShaRule] = []

        # Generate table-based rules from Registry
        for type_name, defn in ShenShaRegistry.get_table_based():
            rules.append(TableLookupRule(
                type_name=type_name,
                lookup_table=defn.lookup_table,
                ref_extractors=defn.ref_extractors,
                target_extractor=defn.target_extractor,
                positions=defn.positions,
                exclude_positions=defn.exclude_positions,
            ))

        # Add special rules
        rules.append(KongWangRule(xun_kong_table=_XUN_KONG))
        rules.append(SanQiRule())

        cls._rules = rules
        cls._initialized = True
