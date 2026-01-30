# WuXing (Five Elements) Calculation Analysis

## Overview

The WuXing (五行) calculation is the foundation of BaZi analysis. It calculates the strength and distribution of the five elements (Wood, Fire, Earth, Metal, Water) in a birth chart.

**Key Files:**
- `bazi/domain/models/elements.py` - WuXing enum and relationships
- `bazi/domain/services/wuxing_calculator.py` - Main calculation service

---

## Current Implementation

### Element Relationships (elements.py:77-97)

The generation (生) and overcoming (克) cycles are correctly implemented:

```
Generation: Wood → Fire → Earth → Metal → Water → Wood
Overcoming: Wood → Earth → Water → Fire → Metal → Wood
```

### Relationship Value Assignment (wuxing_calculator.py:89-111)

Stem-branch relationship values:

| Relationship | Stem Value | Branch Value |
|--------------|------------|--------------|
| Same element | 10 | 10 |
| Stem generates branch | 6 | 8 |
| Stem overcomes branch | 4 | 2 |
| Branch overcomes stem | 2 | 4 |
| Branch generates stem | 8 | 6 |
| **Fallback (should never happen)** | 5 | 5 |

### Seasonal Strength (WangXiang) Multipliers (elements.py:118-124)

| Phase | Chinese | Multiplier |
|-------|---------|------------|
| WANG | 旺 | 1.2x |
| XIANG | 相 | 1.2x |
| XIU | 休 | 1.0x |
| QIU | 囚 | 0.8x |
| SI | 死 | 0.8x |

### Season Mapping (wuxing_calculator.py:62-75)

| Branches | Season | Dominant Element |
|----------|--------|------------------|
| 寅卯辰 | 春 (Spring) | Wood |
| 巳午未 | 夏 (Summer) | Fire |
| 申酉戌 | 秋 (Autumn) | Metal |
| 亥子丑 | 冬 (Winter) | Water |
| 辰未戌丑 (last 18 days) | 土旺 | Earth |

---

## Potential Logic Errors

### 1. Fallback Value Concern (wuxing_calculator.py:111)

**Issue:** The fallback `return (5, 5)` should theoretically never execute because all element relationships are covered by the five cycles.

**Current Code:**
```python
return (5, 5)  # Default fallback
```

**Problem:** If this fallback executes, it indicates a logic error elsewhere, but the code silently continues with neutral values.

**Recommendation:** Replace with an explicit error:
```python
raise ValueError(f"Unexpected element relationship: {stem_element} - {branch_element}")
```

### 2. Earth-Dominant Period Not Automatically Detected (wuxing_calculator.py:119-130)

**Issue:** The `is_earth_dominant` parameter must be explicitly passed. The calculator cannot automatically determine if we're in the last 18 days of a season.

**Current Code:**
```python
def get_season(month_branch: EarthlyBranch, is_earth_dominant: bool = False) -> str:
    if is_earth_dominant and month_branch in _EARTH_BRANCHES:
        return "土旺"
```

**Problem:** This requires the caller to know when earth is dominant, which involves complex lunar calendar calculations. Most callers likely pass `False`, missing the earth-dominant adjustment.

**Recommendation:**
- Add a method to calculate earth dominance based on lunar calendar date
- Or document that this is a known simplification

### 3. Hidden Stem Weight Calculation (wuxing_calculator.py:201-206)

**Issue:** Hidden stems inherit the branch's base relationship value, not their own element's relationship to the stem.

**Current Code:**
```python
# Add hidden stem values
_, branch_value = self.get_pillar_values(pillar)
for hidden_stem, ratio in pillar.hidden_stems.items():
    hidden_element = hidden_stem.wuxing
    hidden_multiplier = self.calculate_wang_xiang_multiplier(hidden_element, wang_xiang)
    result[hidden_element] += branch_value * ratio * hidden_multiplier
```

**Analysis:** The `branch_value` comes from the stem-branch relationship, but hidden stems use this as their base. This is one interpretation of traditional BaZi but not universal.

**Alternative Approach:** Some practitioners calculate each hidden stem's relationship to the day master independently.

---

## Areas for Improvement

### 1. Add Confidence/Variance Metrics

Currently returns point values without any indication of uncertainty:
```python
WuXingStrength(
    raw_values=raw_values,
    wang_xiang=wang_xiang_map,
    adjusted_values=adjusted_values,
)
```

**Enhancement:** Add variance or confidence intervals, especially for edge cases near element balance.

### 2. Support Alternative Weighting Systems

Different BaZi schools use different weighting systems. Current implementation uses one fixed system.

**Enhancement:** Allow configurable weighting strategies via dependency injection:
```python
class WuXingCalculator:
    def __init__(self, weighting_strategy: WeightingStrategy = DefaultWeighting()):
        self._strategy = weighting_strategy
```

### 3. Validate Hidden Stem Ratios Sum to 1.0

The hidden stem ratios in `harmony.py` should always sum to 1.0:

```python
'丑': {'己': 0.5, '癸': 0.3, '辛': 0.2},  # = 1.0 ✓
'寅': {'甲': 0.6, '丙': 0.3, '戊': 0.1},  # = 1.0 ✓
```

**Enhancement:** Add validation during initialization:
```python
for branch, hidden in HIDDEN_GAN_RATIOS.items():
    assert abs(sum(hidden.values()) - 1.0) < 0.001, f"Invalid ratios for {branch}"
```

### 4. Document Seasonal Transition Boundaries

The code doesn't clarify exact boundaries for season transitions. Traditional BaZi uses solar terms (节气), not calendar months.

**Enhancement:** Add documentation explaining that lunar_python handles this in production, while the domain calculator uses month branch approximation.

---

## Test Coverage Gaps

1. **Edge case:** Exactly equal beneficial and harmful values
2. **Edge case:** All five elements have zero adjusted value (theoretical)
3. **Earth-dominant period transitions**
4. **Hidden stems with same WuXing in different pillars (accumulation)**

---

## Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| Medium | Fallback value silently continues | Logic bugs hidden | Low |
| Low | Earth-dominant period not auto-detected | Minor accuracy loss | Medium |
| Low | Single weighting system | Limits flexibility | High |
| Info | Hidden stem calculation documented | Clarity | Low |
