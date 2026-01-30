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
    Callable,
    FrozenSet,
    List,
    Protocol,
    Tuple,
    runtime_checkable,
)

from .shensha import PILLAR_POSITIONS

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
# Extractor Types (Functional approach for flexibility)
# ============================================================

# Type aliases for extractors
RefExtractor = Callable[["BaZi"], str]
TargetExtractor = Callable[["Pillar"], List[Tuple[str, str]]]  # [(value, position_suffix)]


# Pre-defined extractors (factory functions)
def day_stem_extractor(bazi: "BaZi") -> str:
    """Extract day stem (日干) as reference."""
    return bazi.day_master.chinese


def month_branch_extractor(bazi: "BaZi") -> str:
    """Extract month branch (月支) as reference."""
    return bazi.month_pillar.branch.chinese


def year_branch_extractor(bazi: "BaZi") -> str:
    """Extract year branch (年支) as reference."""
    return bazi.year_pillar.branch.chinese


def day_branch_extractor(bazi: "BaZi") -> str:
    """Extract day branch (日支) as reference."""
    return bazi.day_pillar.branch.chinese


def day_pillar_extractor(bazi: "BaZi") -> str:
    """Extract day pillar (日柱) as reference (for 空亡)."""
    return bazi.day_pillar.chinese


def branch_target(pillar: "Pillar") -> List[Tuple[str, str]]:
    """Extract only branch as target."""
    return [(pillar.branch.chinese, "branch")]


def stem_target(pillar: "Pillar") -> List[Tuple[str, str]]:
    """Extract only stem as target."""
    return [(pillar.stem.chinese, "stem")]


def stem_and_branch_target(pillar: "Pillar") -> List[Tuple[str, str]]:
    """Extract both stem and branch as targets (for 天德 etc.)."""
    return [
        (pillar.stem.chinese, "stem"),
        (pillar.branch.chinese, "branch"),
    ]


# ============================================================
# Table-Driven Rule Implementation
# ============================================================

@dataclass(frozen=True)
class TableLookupRule:
    """
    Generic table-driven ShenSha rule.

    Most ShenSha (90%+) can be expressed as simple table lookups:
    - Extract a reference value from BaZi (e.g., day_stem)
    - For each pillar, extract target value(s) (e.g., branch)
    - Check if (ref, target) exists in lookup table

    This dataclass captures all the variation points, allowing
    new ShenSha to be added without writing new code.

    Attributes:
        type_name: ShenShaType enum name (string for lazy resolution)
        lookup_table: FrozenSet of (ref, target) tuples
        ref_extractor: Function to extract reference from BaZi
        target_extractor: Function to extract target(s) from Pillar
        positions: Which pillar positions to check
        also_use_day_branch: Also use day branch as secondary ref (for 桃花/劫煞)
        exclude_ref_position: Exclude the position that matches ref source

    Example:
        >>> rule = TableLookupRule(
        ...     type_name="TIAN_YI_GUI_REN",
        ...     lookup_table=frozenset([("甲", "丑"), ("甲", "未"), ...]),
        ...     ref_extractor=day_stem_extractor,
        ...     target_extractor=branch_target,
        ... )
    """
    type_name: str
    lookup_table: FrozenSet[Tuple[str, str]]
    ref_extractor: RefExtractor
    target_extractor: TargetExtractor
    positions: Tuple[str, ...] = PILLAR_POSITIONS
    also_use_day_branch: bool = False
    exclude_ref_position: str | None = None  # e.g., "year" for year-branch based rules

    @property
    def shensha_type(self) -> "ShenShaType":
        """Lazy resolution of ShenShaType enum."""
        from .shensha import ShenShaType
        return ShenShaType[self.type_name]

    def find_matches(self, bazi: "BaZi") -> List["ShenSha"]:
        """
        Find all matches using table lookup.

        使用表查找匹配神煞：
        1. 主参照值（如日干）匹配所有指定柱位
        2. 若 also_use_day_branch=True，日支也作为参照值二次匹配
        """
        ref_value = self.ref_extractor(bazi)
        results = self._find_matches_with_ref(bazi, ref_value, self.exclude_ref_position)

        # 部分神煞（桃花、劫煞等）需同时以年支和日支为参照
        # Some ShenSha (TaoHua, JieSha) use both year branch and day branch as refs
        if self.also_use_day_branch:
            day_ref = bazi.day_pillar.branch.chinese
            day_matches = self._find_matches_with_ref(bazi, day_ref, exclude_position="day")
            # 去重：避免同一位置重复添加
            for match in day_matches:
                if match not in results:
                    results.append(match)

        return results

    def _find_matches_with_ref(
        self,
        bazi: "BaZi",
        ref_value: str,
        exclude_position: str | None = None,
    ) -> List["ShenSha"]:
        """
        以指定参照值查找匹配的神煞。
        Find matches using a specific reference value.

        Args:
            bazi: The BaZi chart
            ref_value: Reference value to look up (e.g., day stem Chinese char)
            exclude_position: Position to skip (e.g., "day" when ref is day branch)

        Returns:
            List of matching ShenSha
        """
        from .shensha import ShenSha

        results: List[ShenSha] = []
        for pos_name in self.positions:
            if pos_name == exclude_position:
                continue

            pillar = self._get_pillar(bazi, pos_name)
            targets = self.target_extractor(pillar)

            for target_value, position_suffix in targets:
                if (ref_value, target_value) in self.lookup_table:
                    results.append(ShenSha(
                        type=self.shensha_type,
                        position=f"{pos_name}_{position_suffix}",
                        triggered_by=ref_value,
                    ))

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

        for pos_name in PILLAR_POSITIONS:
            pillar = getattr(bazi, f"{pos_name}_pillar")
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

    三奇需要检查天干序列：
    - 天上三奇：甲戊庚 顺序出现
    - 人中三奇：壬癸辛 顺序出现
    - 地下三奇：乙丙丁 顺序出现
    """
    # 三组三奇
    san_qi_groups: Tuple[Tuple[str, str, str], ...] = (
        ("甲", "戊", "庚"),  # 天上三奇
        ("壬", "癸", "辛"),  # 人中三奇
        ("乙", "丙", "丁"),  # 地下三奇
    )

    @property
    def shensha_type(self) -> "ShenShaType":
        from .shensha import ShenShaType
        return ShenShaType.SAN_QI

    def find_matches(self, bazi: "BaZi") -> List["ShenSha"]:
        from .shensha import ShenSha

        # Get stems in order: year, month, day, hour
        stems = [
            bazi.year_pillar.stem.chinese,
            bazi.month_pillar.stem.chinese,
            bazi.day_pillar.stem.chinese,
            bazi.hour_pillar.stem.chinese,
        ]

        for group in self.san_qi_groups:
            if self._check_sequence(stems, group):
                # 三奇是整体格局，位置标记为 "chart"
                return [ShenSha(
                    type=self.shensha_type,
                    position="chart",
                    triggered_by="".join(group),
                )]

        return []

    @staticmethod
    def _check_sequence(stems: List[str], pattern: Tuple[str, str, str]) -> bool:
        """Check if pattern appears in order within stems."""
        pattern_idx = 0
        for stem in stems:
            if stem == pattern[pattern_idx]:
                pattern_idx += 1
                if pattern_idx == len(pattern):
                    return True
        return False


# ============================================================
# Rule Registry (Singleton with proper reset for testing)
# ============================================================

class ShenShaRuleRegistry:
    """
    Central registry for all ShenSha rules.

    Uses lazy initialization to avoid circular imports.
    Thread-safe through immutable rule lists after initialization.

    For testing, use clear() before tests or inject rules directly
    into ShenShaCalculator.
    """
    _instance: "ShenShaRuleRegistry | None" = None
    _rules: List[ShenShaRule] | None = None

    def __new__(cls) -> "ShenShaRuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def all_rules(cls) -> List[ShenShaRule]:
        """
        Get all registered rules (lazy initialization).

        Returns a copy to prevent external modification.
        """
        instance = cls()
        if instance._rules is None:
            instance._initialize_default_rules()
        return list(instance._rules)  # Return copy

    @classmethod
    def clear(cls) -> None:
        """
        Clear all rules and reset singleton.

        Call this in test fixtures to ensure clean state.
        """
        if cls._instance is not None:
            cls._instance._rules = None
        cls._instance = None

    def _initialize_default_rules(self) -> None:
        """Initialize default rules from factory."""
        from ..constants.shensha_rules import create_all_rules
        self._rules = create_all_rules()
