# ShiShen (Ten Gods) Calculation Analysis

## Overview

The ShiShen (十神) system represents the relationships between the Day Master and other elements in a BaZi chart. These relationships indicate different aspects of life: wealth, career, relationships, resources, and peers.

**Key Files:**
- `bazi/domain/models/shishen.py` - ShiShen enum and calculation function
- `bazi/domain/services/shishen_calculator.py` - ShiShen calculation service

---

## Current Implementation

### The Ten Gods (shishen.py:16-41)

| ShiShen | Chinese | Relationship | Polarity Match |
|---------|---------|--------------|----------------|
| BI_JIAN | 比肩 | Same element | Same polarity |
| JIE_CAI | 劫财 | Same element | Opposite polarity |
| SHI_SHEN | 食神 | I generate | Same polarity |
| SHANG_GUAN | 伤官 | I generate | Opposite polarity |
| ZHENG_CAI | 正财 | I overcome | Opposite polarity |
| PIAN_CAI | 偏财 | I overcome | Same polarity |
| ZHENG_GUAN | 正官 | Overcomes me | Opposite polarity |
| QI_SHA | 七杀 | Overcomes me | Same polarity |
| ZHENG_YIN | 正印 | Generates me | Opposite polarity |
| PIAN_YIN | 偏印 | Generates me | Same polarity |

### ShiShen Chart Structure (shishen_calculator.py:98-106)

The calculator returns a `ShiShenChart` with 7 positions:
- `year_stem`, `year_branch_main`
- `month_stem`, `month_branch_main`
- `day_branch_main` (no day_stem - that's the Day Master itself)
- `hour_stem`, `hour_branch_main`

---

## Potential Logic Errors

### 1. **CRITICAL:** Only Main Hidden Stem Analyzed (shishen_calculator.py:78-90)

**Issue:** For each branch, only the primary hidden stem (highest ratio) is considered for ShiShen.

**Current Code:**
```python
year_hidden = bazi.year_pillar.hidden_stems
year_main_hidden = max(year_hidden.keys(), key=lambda k: year_hidden[k])
year_branch_ss = self.calculate(day_master, year_main_hidden)
```

**Problem:** This loses significant information:
- 丑 contains 己(0.5), 癸(0.3), 辛(0.2) - only 己 is analyzed
- 寅 contains 甲(0.6), 丙(0.3), 戊(0.1) - only 甲 is analyzed

**Impact:** Secondary hidden stems that may be significant (30% weight) are completely ignored in the main ShiShen chart.

**Example:** If Day Master is 庚 (Metal) and branch is 寅:
- 甲 (Wood, 0.6) → 偏财
- 丙 (Fire, 0.3) → 七杀 ← **Important but ignored!**
- 戊 (Earth, 0.1) → 偏印

The 30% 七杀 could significantly affect life events but is not shown.

**Recommendation:**
```python
@dataclass
class BranchShiShen:
    main: ShiShen
    all_hidden: Dict[ShiShen, float]  # Full breakdown with ratios
```

### 2. get_detailed_shishen Returns Different Structure for Day Pillar

**Issue:** The day pillar returns `(None, hidden_ss)` while others return `(stem_ss, hidden_ss)`.

**Current Code (shishen_calculator.py:122-128):**
```python
if i == 2:  # Day pillar - stem is self
    # For day pillar, stem is 日主 (self), only calculate hidden
    hidden_ss: Dict[ShiShen, float] = {}
    for hidden_stem, ratio in pillar.hidden_stems.items():
        ss = self.calculate(day_master, hidden_stem)
        hidden_ss[ss] = hidden_ss.get(ss, 0) + ratio
    result.append((None, hidden_ss))  # type: ignore
```

**Problem:**
- The `# type: ignore` comment indicates the type system knows this is inconsistent
- Callers must handle the `None` case specially
- Fragile data structure

**Recommendation:** Use a proper dataclass with explicit `Optional` handling:
```python
@dataclass
class PillarShiShen:
    stem_shishen: Optional[ShiShen]  # None for day pillar
    hidden_shishen: Dict[ShiShen, float]
    is_day_pillar: bool = False
```

### 3. ShiShen Accumulation in Hidden Stems (shishen_calculator.py:56-59)

**Issue:** When multiple hidden stems map to the same ShiShen, their ratios are accumulated.

**Current Code:**
```python
for hidden_stem, ratio in hidden_stems.items():
    ss = self.calculate(day_master, hidden_stem)
    # Accumulate if same ShiShen appears multiple times
    hidden_shishen[ss] = hidden_shishen.get(ss, 0) + ratio
```

**Analysis:** This can happen when hidden stems have the same element with different polarities:
- Example: 午 contains 丁(0.5) and 己(0.5)
- If Day Master is 甲: 丁→正财, 己→正财 (both 正财!)
- Result: {正财: 1.0}

Wait - actually this wouldn't happen because 丁 (Fire) and 己 (Earth) are different elements. Let me reconsider...

Actually, accumulation happens when:
- Two hidden stems have the same WuXing relationship AND same polarity relationship to Day Master

This is rare but possible. The current implementation handles it correctly by accumulating ratios.

---

## Areas for Improvement

### 1. Return Full Hidden Stem Breakdown

**Current:** Only main hidden stem ShiShen per branch
**Proposed:** All hidden stem ShiShens with their ratios

```python
class ShiShenChart:
    year_stem: ShiShen
    year_branch: Dict[ShiShen, float]  # Not just main
    # ... etc
```

### 2. Add Day Master Self-Reference

Currently, the day stem position is implicit (always "self"). Making it explicit would improve clarity:

```python
@dataclass
class ShiShenChart:
    day_stem: Literal["日主"]  # Or a special RI_ZHU ShiShen value
    # ...
```

### 3. Position-Based Meaning Documentation

Different positions have different life meanings:
- Year pillar: Ancestors, childhood, outer society
- Month pillar: Parents, career, authority
- Day pillar: Self and spouse
- Hour pillar: Children, subordinates, late life

**Enhancement:** Add `position_meaning` property to positions.

### 4. Favorable/Unfavorable ShiShen Classification

The model includes a classification but it's not used extensively:

```python
# From shishen.py
FAVORABLE = {ZHENG_YIN, ZHENG_GUAN, ZHENG_CAI, SHI_SHEN, BI_JIAN}
```

**Enhancement:** Add methods to count favorable/unfavorable ShiShen in a chart.

---

## Test Coverage Gaps

1. **Edge case:** Branch with only one hidden stem (子, 卯, 酉)
2. **Edge case:** Day Master comparison with itself (should never happen in normal flow)
3. **Edge case:** All four branches having the same main ShiShen
4. **Multiple positions with same ShiShen counting**

---

## Data Structure Fragility (LiuNian Integration)

The LiuNian analysis service (liunian_analysis.py:153-155) depends on the internal structure:

```python
# shishen_list[2] = ('日主', [hidden_stem_shishens for day branch])
day_branch_shishens = shishen_list[2][1]
```

**Problem:** This hardcodes:
1. Index `2` = day pillar
2. Index `[1]` = hidden stems list
3. Format as list, not dict

If `get_detailed_shishen` changes its return format, this breaks silently.

**Recommendation:** Use named access or structured types:
```python
detailed = calculator.get_detailed_shishen(bazi)
day_hidden = detailed.day_pillar.hidden_shishen
```

---

## Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| High | Only main hidden stem analyzed | Information loss | Medium |
| Medium | Inconsistent data structure for day pillar | Maintenance burden | Low |
| Medium | LiuNian depends on internal structure | Fragile integration | Medium |
| Low | No position meaning documentation | Usability | Low |
