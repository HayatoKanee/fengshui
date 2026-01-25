"""
ShenSha Registry - 神煞注册中心。

集中定义所有神煞的完整配置，包括：
- 查表数据
- 提取器配置
- 元数据（分类、吉凶）

添加新神煞只需在 SHENSHA_DEFINITIONS 中添加一个条目即可。

遵循 SOLID 原则：
- S: Registry 只负责存储和提供神煞定义
- O: 添加新神煞不需要修改其他文件
- L: 所有定义遵循相同的结构
- I: 提供精简的查询接口
- D: Calculator 依赖 Registry 抽象

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, FrozenSet, List, Tuple

if TYPE_CHECKING:
    from .bazi import BaZi
    from .pillar import Pillar

# ============================================================
# 提取器类型定义
# ============================================================

RefExtractor = Callable[["BaZi"], str]
TargetExtractor = Callable[["Pillar"], List[Tuple[str, str]]]


# ============================================================
# 提取器函数（从 shensha_rule.py 移入）
# ============================================================

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
# 神煞定义数据类
# ============================================================

@dataclass(frozen=True)
class ShenShaDefinition:
    """
    Complete definition of a ShenSha type.

    所有神煞信息在一处定义，包括：
    - 基本信息：名称、分类、吉凶
    - 计算规则：查表、提取器、位置

    Attributes:
        name: 神煞中文名称
        category: 分类（贵人、德星、桃花等）
        is_beneficial: 是否为吉星
        lookup_table: 查表数据（可选，特殊规则无需此项）
        ref_extractors: 引用提取器列表（支持多个，如桃花同时用年支和日支）
        target_extractor: 目标提取器
        positions: 检查的柱位
        exclude_positions: 排除的柱位
        is_special: 是否为特殊规则（空亡、三奇等）
    """
    name: str
    category: str
    is_beneficial: bool
    lookup_table: FrozenSet[Tuple[str, str]] | None = None
    ref_extractors: Tuple[RefExtractor, ...] = ()
    target_extractor: TargetExtractor | None = None
    positions: Tuple[str, ...] = ("year", "month", "day", "hour")
    exclude_positions: Tuple[str, ...] = ()
    is_special: bool = False


# ============================================================
# 神煞注册中心
# ============================================================

def _create_definitions() -> dict[str, ShenShaDefinition]:
    """
    Create all ShenSha definitions.

    这是添加新神煞的唯一位置。
    """
    from ..constants.shensha import (
        GUI_REN, TIAN_DE, TIAN_DE_HE, YUE_DE, YUE_DE_HE,
        WEN_CHANG, LU_SHEN, YANG_REN, TAO_HUA, HONG_YAN_SHA,
        JIANG_XING, HUA_GAI, YI_MA, JIE_SHA, WANG_SHEN,
        GU_CHEN, GUA_SU,
    )

    return {
        # ==============================================================
        # 贵人类 - Noble stars
        # ==============================================================
        "TIAN_YI_GUI_REN": ShenShaDefinition(
            name="天乙贵人",
            category="贵人",
            is_beneficial=True,
            lookup_table=GUI_REN,
            ref_extractors=(day_stem_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 德星类 - Virtue stars
        # ==============================================================
        "TIAN_DE": ShenShaDefinition(
            name="天德",
            category="德星",
            is_beneficial=True,
            lookup_table=TIAN_DE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_and_branch_target,  # 天德可能是天干或地支
        ),
        "TIAN_DE_HE": ShenShaDefinition(
            name="天德合",
            category="德星",
            is_beneficial=True,
            lookup_table=TIAN_DE_HE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_and_branch_target,
        ),
        "YUE_DE": ShenShaDefinition(
            name="月德",
            category="德星",
            is_beneficial=True,
            lookup_table=YUE_DE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_target,
        ),
        "YUE_DE_HE": ShenShaDefinition(
            name="月德合",
            category="德星",
            is_beneficial=True,
            lookup_table=YUE_DE_HE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_target,
        ),

        # ==============================================================
        # 文星类 - Literary stars
        # ==============================================================
        "WEN_CHANG": ShenShaDefinition(
            name="文昌",
            category="文星",
            is_beneficial=True,
            lookup_table=WEN_CHANG,
            ref_extractors=(day_stem_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 禄星类 - Prosperity stars
        # ==============================================================
        "LU_SHEN": ShenShaDefinition(
            name="禄神",
            category="禄星",
            is_beneficial=True,
            lookup_table=LU_SHEN,
            ref_extractors=(day_stem_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 刃星类 - Blade stars
        # ==============================================================
        "YANG_REN": ShenShaDefinition(
            name="羊刃",
            category="刃星",
            is_beneficial=False,
            lookup_table=YANG_REN,
            ref_extractors=(day_stem_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 桃花类 - Romance stars
        # ==============================================================
        "TAO_HUA": ShenShaDefinition(
            name="桃花",
            category="桃花",
            is_beneficial=False,  # 桃花属于中性偏凶
            lookup_table=TAO_HUA,
            ref_extractors=(year_branch_extractor, day_branch_extractor),  # 同时用年支和日支
            target_extractor=branch_target,
            exclude_positions=("year",),  # 年柱不查自身
        ),
        "HONG_YAN_SHA": ShenShaDefinition(
            name="红艳煞",
            category="桃花",
            is_beneficial=False,
            lookup_table=HONG_YAN_SHA,
            ref_extractors=(day_stem_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 将星类 - General stars
        # ==============================================================
        "JIANG_XING": ShenShaDefinition(
            name="将星",
            category="将星",
            is_beneficial=True,
            lookup_table=JIANG_XING,
            ref_extractors=(year_branch_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 艺术类 - Art stars
        # ==============================================================
        "HUA_GAI": ShenShaDefinition(
            name="华盖",
            category="艺术",
            is_beneficial=True,
            lookup_table=HUA_GAI,
            ref_extractors=(year_branch_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 驿马类 - Travel stars
        # ==============================================================
        "YI_MA": ShenShaDefinition(
            name="驿马",
            category="驿马",
            is_beneficial=True,  # 驿马多主变动，中性偏吉
            lookup_table=YI_MA,
            ref_extractors=(year_branch_extractor,),
            target_extractor=branch_target,
            exclude_positions=("year",),
        ),

        # ==============================================================
        # 凶煞类 - Inauspicious stars
        # ==============================================================
        "JIE_SHA": ShenShaDefinition(
            name="劫煞",
            category="凶煞",
            is_beneficial=False,
            lookup_table=JIE_SHA,
            ref_extractors=(year_branch_extractor, day_branch_extractor),
            target_extractor=branch_target,
        ),
        "WANG_SHEN": ShenShaDefinition(
            name="亡神",
            category="凶煞",
            is_beneficial=False,
            lookup_table=WANG_SHEN,
            ref_extractors=(year_branch_extractor, day_branch_extractor),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 孤寡类 - Loneliness stars
        # ==============================================================
        "GU_CHEN": ShenShaDefinition(
            name="孤辰",
            category="孤寡",
            is_beneficial=False,
            lookup_table=GU_CHEN,
            ref_extractors=(year_branch_extractor,),
            target_extractor=branch_target,
        ),
        "GUA_SU": ShenShaDefinition(
            name="寡宿",
            category="孤寡",
            is_beneficial=False,
            lookup_table=GUA_SU,
            ref_extractors=(year_branch_extractor,),
            target_extractor=branch_target,
        ),

        # ==============================================================
        # 特殊规则 - Special rules (无查表)
        # ==============================================================
        "KONG_WANG": ShenShaDefinition(
            name="空亡",
            category="空亡",
            is_beneficial=False,
            is_special=True,
        ),
        "SAN_QI": ShenShaDefinition(
            name="三奇",
            category="其他",
            is_beneficial=True,
            is_special=True,
        ),

        # ==============================================================
        # 择日专用神煞 - Day selection stars
        # ==============================================================
        "QI_SHA": ShenShaDefinition(
            name="七杀",
            category="凶煞",
            is_beneficial=False,
            is_special=True,  # 七杀需要根据十神关系判断
        ),
        "YANG_GONG_JI_RI": ShenShaDefinition(
            name="杨公忌日",
            category="凶煞",
            is_beneficial=False,
            is_special=True,
        ),
        "PO_RI": ShenShaDefinition(
            name="破日",
            category="凶煞",
            is_beneficial=False,
            is_special=True,
        ),
        "SI_JUE_RI": ShenShaDefinition(
            name="四绝日",
            category="凶煞",
            is_beneficial=False,
            is_special=True,
        ),
        "SI_LI_RI": ShenShaDefinition(
            name="四离日",
            category="凶煞",
            is_beneficial=False,
            is_special=True,
        ),
    }


class ShenShaRegistry:
    """
    Central registry for all ShenSha definitions.

    提供单一查询入口，支持：
    - 按名称获取定义
    - 获取所有定义
    - 按分类筛选
    - 获取吉星/凶星列表

    Example:
        >>> defn = ShenShaRegistry.get("TIAN_YI_GUI_REN")
        >>> defn.name
        '天乙贵人'
        >>> defn.is_beneficial
        True
    """
    _definitions: dict[str, ShenShaDefinition] | None = None

    @classmethod
    def _ensure_loaded(cls) -> None:
        """Lazy load definitions."""
        if cls._definitions is None:
            cls._definitions = _create_definitions()

    @classmethod
    def get(cls, type_name: str) -> ShenShaDefinition:
        """Get definition by type name."""
        cls._ensure_loaded()
        if type_name not in cls._definitions:
            raise KeyError(f"Unknown ShenSha type: {type_name}")
        return cls._definitions[type_name]

    @classmethod
    def all_definitions(cls) -> dict[str, ShenShaDefinition]:
        """Get all definitions."""
        cls._ensure_loaded()
        return cls._definitions.copy()

    @classmethod
    def get_by_category(cls, category: str) -> list[ShenShaDefinition]:
        """Get all definitions in a category."""
        cls._ensure_loaded()
        return [d for d in cls._definitions.values() if d.category == category]

    @classmethod
    def get_beneficial(cls) -> list[ShenShaDefinition]:
        """Get all beneficial ShenSha definitions."""
        cls._ensure_loaded()
        return [d for d in cls._definitions.values() if d.is_beneficial]

    @classmethod
    def get_table_based(cls) -> list[tuple[str, ShenShaDefinition]]:
        """Get all table-based (non-special) definitions."""
        cls._ensure_loaded()
        return [
            (name, d) for name, d in cls._definitions.items()
            if not d.is_special and d.lookup_table is not None
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear cached definitions (for testing)."""
        cls._definitions = None
