"""
ShenSha (神煞) Stars Domain Constants - 向后兼容层。

★★★ 注意：此文件现在从 shensha_registry 重新导出数据！★★★

添加新神煞请修改：
- models/shensha_registry.py

此文件保持向后兼容，供旧代码使用。
新代码应直接使用 ShenShaRegistry。
"""
from typing import FrozenSet, List, Tuple

# 从 registry 导入所有查表数据
from ..models.shensha_registry import (
    _GUI_REN,
    _TIAN_DE,
    _TIAN_DE_HE,
    _YUE_DE,
    _YUE_DE_HE,
    _WEN_CHANG,
    _LU_SHEN,
    _YANG_REN,
    _TAO_HUA,
    _HONG_YAN_SHA,
    _JIANG_XING,
    _HUA_GAI,
    _YI_MA,
    _JIE_SHA,
    _WANG_SHEN,
    _GU_CHEN,
    _GUA_SU,
    XUN_KONG,
)

# 重新导出（保持旧API）
GUI_REN: FrozenSet[Tuple[str, str]] = _GUI_REN
TIAN_DE: FrozenSet[Tuple[str, str]] = _TIAN_DE
TIAN_DE_HE: FrozenSet[Tuple[str, str]] = _TIAN_DE_HE
YUE_DE: FrozenSet[Tuple[str, str]] = _YUE_DE
YUE_DE_HE: FrozenSet[Tuple[str, str]] = _YUE_DE_HE
WEN_CHANG: FrozenSet[Tuple[str, str]] = _WEN_CHANG
LU_SHEN: FrozenSet[Tuple[str, str]] = _LU_SHEN
YANG_REN: FrozenSet[Tuple[str, str]] = _YANG_REN
TAO_HUA: FrozenSet[Tuple[str, str]] = _TAO_HUA
HONG_YAN_SHA: FrozenSet[Tuple[str, str]] = _HONG_YAN_SHA
JIANG_XING: FrozenSet[Tuple[str, str]] = _JIANG_XING
HUA_GAI: FrozenSet[Tuple[str, str]] = _HUA_GAI
YI_MA: FrozenSet[Tuple[str, str]] = _YI_MA
JIE_SHA: FrozenSet[Tuple[str, str]] = _JIE_SHA
WANG_SHEN: FrozenSet[Tuple[str, str]] = _WANG_SHEN
GU_CHEN: FrozenSet[Tuple[str, str]] = _GU_CHEN
GUA_SU: FrozenSet[Tuple[str, str]] = _GUA_SU
