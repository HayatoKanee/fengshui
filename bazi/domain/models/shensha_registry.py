"""
ShenSha Registry - 神煞注册中心（单一数据源）。

★★★ 添加新神煞只需在此文件中添加一个条目即可！★★★

本文件是神煞系统的唯一配置中心，包括：
- 查表数据（内联定义）
- 提取器配置
- 元数据（分类、吉凶）

遵循 SOLID 原则：
- S: Registry 只负责存储和提供神煞定义
- O: 添加新神煞不需要修改其他文件
- L: 所有定义遵循相同的结构
- I: 提供精简的查询接口
- D: Calculator 依赖 Registry 抽象

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple

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
        lookup_table: 查表数据（内联定义，特殊规则无需此项）
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
# 内联查表数据
# ============================================================

# 天乙贵人 - Heavenly Noble (Gui Ren)
_GUI_REN: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '丑'), ('戊', '丑'), ('庚', '丑'),
    ('甲', '未'), ('戊', '未'), ('庚', '未'),
    ('乙', '子'), ('己', '子'), ('乙', '申'), ('己', '申'),
    ('丙', '亥'), ('丁', '亥'), ('丙', '酉'), ('丁', '酉'),
    ('壬', '卯'), ('癸', '卯'), ('壬', '巳'), ('癸', '巳'),
    ('辛', '午'), ('辛', '寅'),
])

# 天德 - Heaven Virtue
# 古诀：寅月丁，卯月申，辰月壬，巳月辛，午月亥，未月甲，申月癸，酉月寅，戌月丙，亥月乙，子月巳，丑月庚
# 注意：卯、午、酉、子月查地支，其余月份查天干
_TIAN_DE: FrozenSet[Tuple[str, str]] = frozenset([
    ('寅', '丁'), ('卯', '申'), ('辰', '壬'), ('巳', '辛'),
    ('午', '亥'), ('未', '甲'), ('申', '癸'), ('酉', '寅'),
    ('戌', '丙'), ('亥', '乙'), ('子', '巳'), ('丑', '庚'),
])

# 天德合 - Heaven Virtue Combination (天德的五合/六合)
# 原理：天德与天干五合或地支六合者即为天德合
_TIAN_DE_HE: FrozenSet[Tuple[str, str]] = frozenset([
    # 天干五合对应
    ('寅', '壬'),  # 丁壬合
    ('辰', '丁'),  # 壬丁合
    ('巳', '丙'),  # 辛丙合
    ('未', '己'),  # 甲己合
    ('申', '戊'),  # 癸戊合
    ('戌', '辛'),  # 丙辛合
    ('亥', '庚'),  # 乙庚合
    ('丑', '乙'),  # 庚乙合
    # 地支六合对应
    ('卯', '巳'),  # 巳申合
    ('午', '寅'),  # 寅亥合
    ('酉', '亥'),  # 寅亥合
    ('子', '申'),  # 巳申合
])

# 月德 - Month Virtue
# 查法：寅午戌月见丙，亥卯未月见甲，申子辰月见壬，巳酉丑月见庚
_YUE_DE: FrozenSet[Tuple[str, str]] = frozenset([
    ('寅', '丙'), ('卯', '甲'), ('辰', '壬'), ('巳', '庚'),
    ('午', '丙'), ('未', '甲'), ('申', '壬'), ('酉', '庚'),
    ('戌', '丙'), ('亥', '甲'), ('子', '壬'), ('丑', '庚'),
])

# 月德合 - Month Virtue Combination (月德的天干五合)
# 查法：丙辛合→寅午戌月见辛，甲己合→亥卯未月见己，壬丁合→申子辰月见丁，庚乙合→巳酉丑月见乙
_YUE_DE_HE: FrozenSet[Tuple[str, str]] = frozenset([
    ('寅', '辛'), ('卯', '己'), ('辰', '丁'), ('巳', '乙'),
    ('午', '辛'), ('未', '己'), ('申', '丁'), ('酉', '乙'),
    ('戌', '辛'), ('亥', '己'), ('子', '丁'), ('丑', '乙'),
])

# 文昌 - Literary Star
_WEN_CHANG: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '巳'), ('乙', '午'), ('丙', '申'), ('丁', '酉'),
    ('戊', '申'), ('己', '酉'), ('庚', '亥'), ('辛', '子'),
    ('壬', '寅'), ('癸', '卯'),
])

# 禄神 - Prosperity Star
_LU_SHEN: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '寅'), ('乙', '卯'), ('丙', '巳'), ('戊', '巳'),
    ('丁', '午'), ('己', '午'), ('庚', '申'), ('辛', '酉'),
    ('壬', '亥'), ('癸', '子'),
])

# 羊刃 - Goat Blade
_YANG_REN: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '卯'), ('乙', '辰'), ('丙', '午'), ('戊', '午'),
    ('丁', '未'), ('己', '未'), ('庚', '酉'), ('辛', '戌'),
    ('壬', '子'), ('癸', '丑'),
])

# 桃花 - Peach Blossom (Romance Star)
_TAO_HUA: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '酉'), ('丑', '午'), ('寅', '卯'), ('卯', '子'),
    ('辰', '酉'), ('巳', '午'), ('午', '卯'), ('未', '子'),
    ('申', '酉'), ('酉', '午'), ('戌', '卯'), ('亥', '子'),
])

# 红艳煞 - Red Romance Star
_HONG_YAN_SHA: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '午'), ('乙', '午'), ('丙', '寅'), ('戊', '辰'),
    ('丁', '未'), ('己', '辰'), ('庚', '戌'), ('辛', '酉'),
    ('壬', '子'), ('癸', '申'),
])

# 将星 - General Star
_JIANG_XING: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '子'), ('午', '午'),
    ('丑', '酉'), ('未', '卯'),
    ('寅', '午'), ('申', '子'),
    ('卯', '卯'), ('酉', '酉'),
    ('辰', '子'), ('戌', '午'),
    ('巳', '酉'), ('亥', '卯'),
])

# 华盖 - Canopy Star
_HUA_GAI: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '辰'), ('午', '戌'),
    ('丑', '丑'), ('未', '未'),
    ('寅', '戌'), ('申', '辰'),
    ('卯', '未'), ('酉', '丑'),
    ('辰', '辰'), ('戌', '戌'),
    ('巳', '丑'), ('亥', '未'),
])

# 驿马 - Post Horse Star
_YI_MA: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '寅'), ('午', '申'),
    ('丑', '亥'), ('未', '巳'),
    ('寅', '申'), ('申', '寅'),
    ('卯', '巳'), ('酉', '亥'),
    ('辰', '寅'), ('戌', '申'),
    ('巳', '亥'), ('亥', '巳'),
])

# 劫煞 - Robbery Star
_JIE_SHA: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '巳'), ('丑', '寅'), ('寅', '亥'), ('卯', '申'),
    ('辰', '巳'), ('巳', '寅'), ('午', '亥'), ('未', '申'),
    ('申', '巳'), ('酉', '寅'), ('戌', '亥'), ('亥', '申'),
])

# 亡神 - Death Spirit Star
_WANG_SHEN: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '亥'), ('丑', '申'), ('寅', '巳'), ('卯', '寅'),
    ('辰', '亥'), ('巳', '申'), ('午', '巳'), ('未', '寅'),
    ('申', '亥'), ('酉', '申'), ('戌', '巳'), ('亥', '寅'),
])

# 孤辰 - Lone Star (Male Loneliness)
_GU_CHEN: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '寅'), ('丑', '寅'), ('寅', '巳'), ('卯', '巳'),
    ('辰', '巳'), ('巳', '申'), ('午', '申'), ('未', '申'),
    ('申', '亥'), ('酉', '亥'), ('戌', '亥'), ('亥', '寅'),
])

# 寡宿 - Widowhood Star (Female Loneliness)
_GUA_SU: FrozenSet[Tuple[str, str]] = frozenset([
    ('子', '戌'), ('丑', '戌'), ('寅', '丑'), ('卯', '丑'),
    ('辰', '丑'), ('巳', '辰'), ('午', '辰'), ('未', '辰'),
    ('申', '未'), ('酉', '未'), ('戌', '未'), ('亥', '戌'),
])

# 空亡（旬空）- Void/Emptiness (by day pillar)
XUN_KONG: dict[str, list[str]] = {
    # 甲子旬空戌亥
    '甲子': ['戌', '亥'], '乙丑': ['戌', '亥'], '丙寅': ['戌', '亥'], '丁卯': ['戌', '亥'],
    '戊辰': ['戌', '亥'], '己巳': ['戌', '亥'], '庚午': ['戌', '亥'], '辛未': ['戌', '亥'],
    '壬申': ['戌', '亥'], '癸酉': ['戌', '亥'],
    # 甲戌旬空申酉
    '甲戌': ['申', '酉'], '乙亥': ['申', '酉'], '丙子': ['申', '酉'], '丁丑': ['申', '酉'],
    '戊寅': ['申', '酉'], '己卯': ['申', '酉'], '庚辰': ['申', '酉'], '辛巳': ['申', '酉'],
    '壬午': ['申', '酉'], '癸未': ['申', '酉'],
    # 甲申旬空午未
    '甲申': ['午', '未'], '乙酉': ['午', '未'], '丙戌': ['午', '未'], '丁亥': ['午', '未'],
    '戊子': ['午', '未'], '己丑': ['午', '未'], '庚寅': ['午', '未'], '辛卯': ['午', '未'],
    '壬辰': ['午', '未'], '癸巳': ['午', '未'],
    # 甲午旬空辰巳
    '甲午': ['辰', '巳'], '乙未': ['辰', '巳'], '丙申': ['辰', '巳'], '丁酉': ['辰', '巳'],
    '戊戌': ['辰', '巳'], '己亥': ['辰', '巳'], '庚子': ['辰', '巳'], '辛丑': ['辰', '巳'],
    '壬寅': ['辰', '巳'], '癸卯': ['辰', '巳'],
    # 甲辰旬空寅卯
    '甲辰': ['寅', '卯'], '乙巳': ['寅', '卯'], '丙午': ['寅', '卯'], '丁未': ['寅', '卯'],
    '戊申': ['寅', '卯'], '己酉': ['寅', '卯'], '庚戌': ['寅', '卯'], '辛亥': ['寅', '卯'],
    '壬子': ['寅', '卯'], '癸丑': ['寅', '卯'],
    # 甲寅旬空子丑
    '甲寅': ['子', '丑'], '乙卯': ['子', '丑'], '丙辰': ['子', '丑'], '丁巳': ['子', '丑'],
    '戊午': ['子', '丑'], '己未': ['子', '丑'], '庚申': ['子', '丑'], '辛酉': ['子', '丑'],
    '壬戌': ['子', '丑'], '癸亥': ['子', '丑'],
}


# ============================================================
# 神煞定义（单一数据源）
# ============================================================

def _create_definitions() -> dict[str, ShenShaDefinition]:
    """
    Create all ShenSha definitions.

    ★★★ 添加新神煞只需在此处添加一个条目即可！★★★

    步骤：
    1. 在上方添加查表数据（如 _NEW_SHENSHA = frozenset([...])）
    2. 在下方添加 ShenShaDefinition 条目
    3. 完成！（enum 会自动同步，constants/shensha.py 会自动导出）
    """
    return {
        # ==============================================================
        # 贵人类 - Noble stars
        # ==============================================================
        "TIAN_YI_GUI_REN": ShenShaDefinition(
            name="天乙贵人",
            category="贵人",
            is_beneficial=True,
            lookup_table=_GUI_REN,
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
            lookup_table=_TIAN_DE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_and_branch_target,  # 天德可能是天干或地支
        ),
        "TIAN_DE_HE": ShenShaDefinition(
            name="天德合",
            category="德星",
            is_beneficial=True,
            lookup_table=_TIAN_DE_HE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_and_branch_target,
        ),
        "YUE_DE": ShenShaDefinition(
            name="月德",
            category="德星",
            is_beneficial=True,
            lookup_table=_YUE_DE,
            ref_extractors=(month_branch_extractor,),
            target_extractor=stem_target,
        ),
        "YUE_DE_HE": ShenShaDefinition(
            name="月德合",
            category="德星",
            is_beneficial=True,
            lookup_table=_YUE_DE_HE,
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
            lookup_table=_WEN_CHANG,
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
            lookup_table=_LU_SHEN,
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
            lookup_table=_YANG_REN,
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
            lookup_table=_TAO_HUA,
            ref_extractors=(year_branch_extractor, day_branch_extractor),  # 同时用年支和日支
            target_extractor=branch_target,
            exclude_positions=("year",),  # 年柱不查自身
        ),
        "HONG_YAN_SHA": ShenShaDefinition(
            name="红艳煞",
            category="桃花",
            is_beneficial=False,
            lookup_table=_HONG_YAN_SHA,
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
            lookup_table=_JIANG_XING,
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
            lookup_table=_HUA_GAI,
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
            lookup_table=_YI_MA,
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
            lookup_table=_JIE_SHA,
            ref_extractors=(year_branch_extractor, day_branch_extractor),
            target_extractor=branch_target,
        ),
        "WANG_SHEN": ShenShaDefinition(
            name="亡神",
            category="凶煞",
            is_beneficial=False,
            lookup_table=_WANG_SHEN,
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
            lookup_table=_GU_CHEN,
            ref_extractors=(year_branch_extractor,),
            target_extractor=branch_target,
        ),
        "GUA_SU": ShenShaDefinition(
            name="寡宿",
            category="孤寡",
            is_beneficial=False,
            lookup_table=_GUA_SU,
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
