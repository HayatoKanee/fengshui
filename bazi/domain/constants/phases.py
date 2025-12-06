"""
Seasonal Phases Domain Constants.

Domain-level constants for seasonal phase (旺相休囚死) calculations.
These determine element strength based on birth month.
"""
from typing import Dict

# 地支季节 - Earthly Branches to Seasons
ZHI_SEASONS: Dict[str, str] = {
    '寅': '春', '卯': '春', '辰': '春',
    '巳': '夏', '午': '夏', '未': '夏',
    '申': '秋', '酉': '秋', '戌': '秋',
    '亥': '冬', '子': '冬', '丑': '冬',
}

# 季节旺相 - Seasonal Phase Mappings
# Each season determines which element is in which phase
SEASON_PHASES: Dict[str, Dict[str, str]] = {
    '春': {'木': '旺', '火': '相', '水': '休', '金': '囚', '土': '死'},
    '夏': {'火': '旺', '土': '相', '木': '休', '水': '囚', '金': '死'},
    '秋': {'金': '旺', '水': '相', '土': '休', '火': '囚', '木': '死'},
    '冬': {'水': '旺', '木': '相', '金': '休', '土': '囚', '火': '死'},
}

# 旺相比例 - Phase Value Multipliers
WANG_XIANG_VALUE: Dict[str, float] = {
    '旺': 1.2,
    '相': 1.2,
    '休': 1.0,
    '囚': 0.8,
    '死': 0.8,
}


def get_season(branch: str) -> str:
    """Get season for an earthly branch."""
    return ZHI_SEASONS.get(branch, '')


def get_phase_for_element(season: str, element: str) -> str:
    """Get the phase (旺相休囚死) for an element in a given season."""
    phases = SEASON_PHASES.get(season, {})
    return phases.get(element, '')


def get_phase_value(phase: str) -> float:
    """Get the numerical multiplier for a phase."""
    return WANG_XIANG_VALUE.get(phase, 1.0)
