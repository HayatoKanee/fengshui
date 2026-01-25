"""
ShenSha Rules - 神煞规则便捷函数。

规则现在由 ShenShaRegistry 自动生成。
此文件保留便捷函数供外部使用。

添加新神煞请修改：
1. constants/shensha.py - 添加查表数据
2. models/shensha_registry.py - 在 SHENSHA_DEFINITIONS 中添加定义

只需 2 步即可完成！
"""
from typing import List

from .shensha import XUN_KONG


def get_kong_wang_branches(day_pillar_chinese: str) -> List[str]:
    """
    获取日柱对应的空亡地支。

    Args:
        day_pillar_chinese: 日柱中文，如 "甲子"

    Returns:
        空亡的两个地支，如 ["戌", "亥"]

    Example:
        >>> get_kong_wang_branches("甲子")
        ['戌', '亥']
        >>> get_kong_wang_branches("甲戌")
        ['申', '酉']
    """
    return XUN_KONG.get(day_pillar_chinese, [])
