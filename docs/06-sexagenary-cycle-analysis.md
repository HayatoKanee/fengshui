# Sexagenary Cycle (60甲子) Calculator Analysis

## Overview

The Sexagenary Cycle (60甲子) is the 60-combination cycle of Heavenly Stems and Earthly Branches. This calculator provides mathematical operations for pillar calculations and date matching.

**Key Files:**
- `bazi/domain/services/sexagenary_calculator.py` - Main calculator service

---

## Current Implementation

### Julian Day Number Conversion (sexagenary_calculator.py:87-142)

Gregorian ↔ JDN conversions use standard astronomical algorithms:

```python
@staticmethod
def date_to_jdn(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
```

**Analysis:** This is the standard Gregorian-to-JDN formula, mathematically correct.

### Day Sexagenary Index (sexagenary_calculator.py:144-162)

```python
def get_day_sexagenary_index(self, year: int, month: int, day: int) -> int:
    jdn = self.date_to_jdn(year, month, day)
    # Formula: S = (JDN + 9) % 60
    return (jdn + 9) % 60
```

**Analysis:** The offset `+9` aligns with the reference where Jan 27, 2019 (JDN 2458511) has S=11.

### Hour Pillar Calculation (sexagenary_calculator.py:220-236)

```python
def get_hour_pillar(self, day_stem_index: int, hour: int) -> str:
    hour_branch_index = self.HOUR_TO_BRANCH[hour]
    hour_stem_index = (day_stem_index * 2 + hour_branch_index) % 10
    return self.STEMS[hour_stem_index] + self.BRANCHES[hour_branch_index]
```

**Analysis:** This implements the standard 日上起时法 (deriving hour stem from day stem).

### Reverse Lookup Optimization (sexagenary_calculator.py:238-276)

The 60-day jump algorithm provides O(matches) instead of O(days):

```python
def find_matching_day_pillar_dates(self, target_stem, target_branch, start_date, end_date):
    target_index = self.pillar_to_sexagenary_index(target_stem, target_branch)
    start_index = self.get_day_sexagenary_index(...)

    offset = (target_index - start_index) % 60
    first_match = start_date + timedelta(days=offset)

    current = first_match
    while current <= end_date:
        yield current
        current += timedelta(days=60)
```

**Performance:** For 100-year search: ~608 iterations vs ~36,500 brute force (60x improvement).

---

## Potential Logic Errors

### 1. **KNOWN LIMITATION:** Year Pillar Ignores Lichun (sexagenary_calculator.py:371-392)

**Issue:** Year pillar calculation uses simple modular arithmetic:

```python
def get_year_pillar_index(self, year: int) -> int:
    # Note: This is a simplified calculation that doesn't account for
    # Lichun (立春). For precise year pillar, use lunar_python adapter.
    return (year - 1984) % 60

def get_year_pillar(self, year: int) -> str:
    idx = self.get_year_pillar_index(year)
    return self.STEMS[idx % 10] + self.BRANCHES[idx % 12]
```

**Problem:** Year pillar changes at Lichun (立春, around Feb 3-5), NOT January 1.

**Impact:** For dates Jan 1 - Feb 5, this returns WRONG year pillar.

**Mitigation:**
- Production code uses `lunar_python` adapter which handles Lichun
- This calculator is for internal optimizations, not user-facing results
- Comments acknowledge the limitation

**Recommendation:** Add explicit warning in method name:
```python
def get_year_pillar_simplified_no_lichun(self, year: int) -> str:
```

### 2. Hour Boundary at 23:00 (sexagenary_calculator.py:72-85)

**Issue:** Hour mapping has a day-boundary complication:

```python
HOUR_TO_BRANCH = {
    23: 0, 0: 0,   # 子 (23:00-01:00)
    1: 1, 2: 1,    # 丑 (01:00-03:00)
    # ...
}
```

**Problem:** 23:00-23:59 belongs to the NEXT day's 子时 in traditional BaZi. The current mapping returns branch correctly, but:
- If called with hour=23 for Jan 1, it returns 子
- But the DATE should be Jan 2 for pillar purposes (早子时 vs 晚子时)

**Traditional Split:**
- 早子时 (Early Zi): 00:00-00:59 of current day
- 晚子时 (Late Zi): 23:00-23:59 of previous day → counts as next day

**Impact:** Users born 23:00-23:59 may get wrong day pillar.

**Recommendation:** Document clearly or add parameter:
```python
def get_hour_pillar(self, day_stem_index: int, hour: int, use_early_zi: bool = False) -> str:
```

### 3. Month Pillar Not Implemented

**Issue:** The calculator has year, day, and hour pillar methods, but no month pillar.

**Reason:** Month pillar requires solar term (节气) calculation, which is complex and handled by `lunar_python`.

**Status:** Acceptable limitation, documented implicitly.

### 4. Pillar Validity Not Checked (sexagenary_calculator.py:197-218)

**Issue:** The `pillar_to_sexagenary_index` method doesn't validate that stem-branch combination is valid:

```python
def pillar_to_sexagenary_index(self, stem: str, branch: str) -> int:
    stem_idx = self.stem_to_index(stem)
    branch_idx = self.branch_to_index(branch)
    k = 6 * (stem_idx + 1) - 5 * (branch_idx + 1)
    if k <= 0:
        k += 60
    return k - 1
```

**Problem:** Not all stem-branch combinations are valid. Only 60 of the 120 possible combinations exist in the sexagenary cycle. For example:
- 甲子 ✓ (valid)
- 甲丑 ✗ (invalid - wrong parity)

Yang stems (甲丙戊庚壬) only pair with Yang branches (子寅辰午申戌).
Yin stems (乙丁己辛癸) only pair with Yin branches (丑卯巳未酉亥).

**Impact:** If invalid combination passed, returns a meaningless index.

**Recommendation:**
```python
def pillar_to_sexagenary_index(self, stem: str, branch: str) -> int:
    stem_idx = self.stem_to_index(stem)
    branch_idx = self.branch_to_index(branch)

    # Validate parity
    if stem_idx % 2 != branch_idx % 2:
        raise ValueError(f"Invalid pillar: {stem}{branch} (parity mismatch)")

    k = 6 * (stem_idx + 1) - 5 * (branch_idx + 1)
    # ...
```

---

## Areas for Improvement

### 1. Add Explicit Parity Validation

```python
def is_valid_pillar(self, stem: str, branch: str) -> bool:
    stem_idx = self.stem_to_index(stem)
    branch_idx = self.branch_to_index(branch)
    return stem_idx % 2 == branch_idx % 2
```

### 2. Document 早子时/晚子时 Handling

Add clear documentation about the 23:00 hour boundary:
```python
"""
Note on Zi hour (子时) boundary:
- Traditional: 晚子时 (23:00-23:59) belongs to NEXT day
- This implementation: Hour 23 maps to Zi branch but doesn't adjust date
- For birth time 23:00-23:59, caller should add 1 day before calling
"""
```

### 3. Add Month Pillar with Simplification Warning

Even if simplified, having a month pillar method with clear limitations could be useful:
```python
def get_month_pillar_simplified(self, month: int) -> str:
    """
    SIMPLIFIED month pillar - does NOT account for solar terms.
    Use lunar_python for accurate month pillar.
    """
    # Simplified mapping based on lunar month approximation
```

### 4. Cache Frequently Used Calculations

For high-volume date matching:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def date_to_jdn(self, year: int, month: int, day: int) -> int:
    # ...
```

---

## Test Coverage Gaps

1. **Edge case:** Invalid pillar combinations (e.g., 甲丑)
2. **Edge case:** Hour 23 date boundary
3. **Edge case:** Leap years in JDN calculation
4. **Edge case:** Dates before 1984 for year pillar
5. **Verification:** Cross-reference JDN calculations with known dates

---

## Mathematical Reference

### Sexagenary Index Formulas

From reference: https://ytliu0.github.io/ChineseCalendar/sexagenary.html

```
Sexagenary number S = 1 + mod(JD_noon - 11, 60)
Stem index T = 1 + mod(S-1, 10)
Branch index B = 1 + mod(S-1, 12)
```

Or directly:
```
T = 1 + mod(JD_noon - 1, 10)
B = 1 + mod(JD_noon + 1, 12)
```

### Valid Pillar Rule

For pillar to be valid: `stem_index % 2 == branch_index % 2`

| Stem Index | Valid Branch Indices |
|------------|---------------------|
| 0, 2, 4, 6, 8 (Yang) | 0, 2, 4, 6, 8, 10 |
| 1, 3, 5, 7, 9 (Yin) | 1, 3, 5, 7, 9, 11 |

---

## Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| Low | Year pillar ignores Lichun | Known, mitigated | Low (doc) |
| Medium | Hour 23 date boundary | Accuracy for 23:00 births | Low (doc) |
| Medium | No pillar validity check | Silent wrong results | Low |
| Low | No month pillar | Feature gap | High |
