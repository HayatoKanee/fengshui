"""
Five Elements Relationships Domain Constants.

Domain-level constants for WuXing (五行) generation and control cycles,
and favorable/unfavorable element relationships.
"""
from typing import Dict, List, FrozenSet, Tuple

# 五行生克 - Generation and Control Cycles
WUXING_SHENG: Dict[str, str] = {
    '木': '火',  # Wood generates Fire
    '火': '土',  # Fire generates Earth
    '土': '金',  # Earth generates Metal
    '金': '水',  # Metal generates Water
    '水': '木',  # Water generates Wood
}

WUXING_KE: Dict[str, str] = {
    '火': '金',  # Fire controls Metal
    '水': '火',  # Water controls Fire
    '土': '水',  # Earth controls Water
    '木': '土',  # Wood controls Earth
    '金': '木',  # Metal controls Wood
}

# Combined relationships dict (legacy format compatibility)
RELATIONSHIPS: Dict[str, Dict[str, str]] = {
    '生': WUXING_SHENG,
    '克': WUXING_KE,
}

# 五行关系 - Favorable/Unfavorable relationships for each element
WUXING_RELATIONS: Dict[str, Dict[str, List[str]]] = {
    '木': {'有利': ['木', '水'], '不利': ['火', '土', '金']},
    '火': {'有利': ['火', '木'], '不利': ['土', '金', '水']},
    '土': {'有利': ['土', '火'], '不利': ['金', '水', '木']},
    '金': {'有利': ['金', '土'], '不利': ['水', '木', '火']},
    '水': {'有利': ['水', '金'], '不利': ['木', '火', '土']},
}


def generates(element: str) -> str:
    """Get the element that this element generates."""
    return WUXING_SHENG.get(element, '')


def controls(element: str) -> str:
    """Get the element that this element controls."""
    return WUXING_KE.get(element, '')


def is_favorable(day_master: str, target: str) -> bool:
    """Check if target element is favorable for day master."""
    relations = WUXING_RELATIONS.get(day_master, {})
    return target in relations.get('有利', [])


def is_unfavorable(day_master: str, target: str) -> bool:
    """Check if target element is unfavorable for day master."""
    relations = WUXING_RELATIONS.get(day_master, {})
    return target in relations.get('不利', [])
