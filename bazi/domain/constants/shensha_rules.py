"""
ShenSha Rules Factory - 神煞规则工厂。

所有神煞规则的声明式定义，复用 shensha.py 中的查表数据。
添加新神煞只需在 create_all_rules() 中添加规则实例。

遵循 SOLID 原则：
- S: 每个规则只负责一个神煞
- O: 添加新规则不需要修改计算器
- L: 所有规则实现 ShenShaRule Protocol
- I: Protocol 接口精简
- D: Calculator 依赖 Protocol 抽象
"""
from typing import List

from ..models.shensha_rule import (
    ShenShaRule,
    TableLookupRule,
    KongWangRule,
    SanQiRule,
    # Extractors
    day_stem_extractor,
    month_branch_extractor,
    year_branch_extractor,
    # Target extractors
    branch_target,
    stem_target,
    stem_and_branch_target,
)
from .shensha import (
    GUI_REN,
    TIAN_DE,
    TIAN_DE_HE,
    YUE_DE,
    WEN_CHANG,
    LU_SHEN,
    YANG_REN,
    TAO_HUA,
    HONG_YAN_SHA,
    JIANG_XING,
    HUA_GAI,
    YI_MA,
    JIE_SHA,
    WANG_SHEN,
    GU_CHEN,
    GUA_SU,
    XUN_KONG,
)


def create_all_rules() -> List[ShenShaRule]:
    """
    Create all ShenSha rule instances.

    This is the single point where all rules are defined.
    Adding a new ShenSha only requires adding a new rule here.

    Returns:
        List of all ShenSha rule instances
    """
    rules: List[ShenShaRule] = []

    # ==============================================================
    # 贵人类 - Noble stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="TIAN_YI_GUI_REN",
        lookup_table=GUI_REN,
        ref_extractor=day_stem_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 德星类 - Virtue stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="TIAN_DE",
        lookup_table=TIAN_DE,
        ref_extractor=month_branch_extractor,
        target_extractor=stem_and_branch_target,  # 天德可能是天干或地支
    ))

    rules.append(TableLookupRule(
        type_name="TIAN_DE_HE",
        lookup_table=TIAN_DE_HE,
        ref_extractor=month_branch_extractor,
        target_extractor=stem_and_branch_target,  # 天德合也可能是天干或地支
    ))

    rules.append(TableLookupRule(
        type_name="YUE_DE",
        lookup_table=YUE_DE,
        ref_extractor=month_branch_extractor,
        target_extractor=stem_target,
    ))

    # ==============================================================
    # 文星类 - Literary stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="WEN_CHANG",
        lookup_table=WEN_CHANG,
        ref_extractor=day_stem_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 禄星类 - Prosperity stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="LU_SHEN",
        lookup_table=LU_SHEN,
        ref_extractor=day_stem_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 刃星类 - Blade stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="YANG_REN",
        lookup_table=YANG_REN,
        ref_extractor=day_stem_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 桃花类 - Romance stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="TAO_HUA",
        lookup_table=TAO_HUA,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
        exclude_ref_position="year",  # 不查年柱自身
        also_use_day_branch=True,     # 同时用日支查
    ))

    rules.append(TableLookupRule(
        type_name="HONG_YAN_SHA",
        lookup_table=HONG_YAN_SHA,
        ref_extractor=day_stem_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 将星类 - General stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="JIANG_XING",
        lookup_table=JIANG_XING,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 艺术类 - Art stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="HUA_GAI",
        lookup_table=HUA_GAI,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 驿马类 - Travel stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="YI_MA",
        lookup_table=YI_MA,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
        exclude_ref_position="year",  # 不查年柱自身
    ))

    # ==============================================================
    # 凶煞类 - Inauspicious stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="JIE_SHA",
        lookup_table=JIE_SHA,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
        also_use_day_branch=True,  # 同时用日支查
    ))

    rules.append(TableLookupRule(
        type_name="WANG_SHEN",
        lookup_table=WANG_SHEN,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
        also_use_day_branch=True,  # 同时用日支查
    ))

    # ==============================================================
    # 孤寡类 - Loneliness stars
    # ==============================================================
    rules.append(TableLookupRule(
        type_name="GU_CHEN",
        lookup_table=GU_CHEN,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
    ))

    rules.append(TableLookupRule(
        type_name="GUA_SU",
        lookup_table=GUA_SU,
        ref_extractor=year_branch_extractor,
        target_extractor=branch_target,
    ))

    # ==============================================================
    # 特殊规则 - Special rules
    # ==============================================================

    # 空亡 - 需要用日柱查旬空
    rules.append(KongWangRule(xun_kong_table=XUN_KONG))

    # 三奇 - 需要检查天干序列
    rules.append(SanQiRule())

    return rules


# ============================================================
# 便捷函数
# ============================================================

def get_kong_wang_branches(day_pillar_chinese: str) -> List[str]:
    """
    获取日柱对应的空亡地支。

    Args:
        day_pillar_chinese: 日柱中文，如 "甲子"

    Returns:
        空亡的两个地支，如 ["戌", "亥"]
    """
    return XUN_KONG.get(day_pillar_chinese, [])
