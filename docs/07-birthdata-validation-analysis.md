# BirthData Validation Analysis

## Overview

BirthData is the input value object for BaZi calculations. It represents birth time information and should validate input data before it's used in calculations.

**Key Files:**
- `bazi/domain/models/bazi.py` - BirthData dataclass

---

## Current Implementation

### BirthData Structure (bazi.py:17-31)

```python
@dataclass(frozen=True)
class BirthData:
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    is_male: bool = True
    name: Optional[str] = None
```

### Current Validation (bazi.py:32-41)

```python
def __post_init__(self):
    """Validate birth data."""
    if not (1 <= self.month <= 12):
        raise ValueError(f"Month must be 1-12, got: {self.month}")
    if not (1 <= self.day <= 31):
        raise ValueError(f"Day must be 1-31, got: {self.day}")
    if not (0 <= self.hour <= 23):
        raise ValueError(f"Hour must be 0-23, got: {self.hour}")
    if not (0 <= self.minute <= 59):
        raise ValueError(f"Minute must be 0-59, got: {self.minute}")
```

---

## Potential Logic Errors

### 1. **CRITICAL:** Day-of-Month Validation Missing

**Issue:** The validation allows invalid dates like February 31, April 31, etc.

**Current Code:**
```python
if not (1 <= self.day <= 31):
    raise ValueError(f"Day must be 1-31, got: {self.day}")
```

**Problem:** This only checks day is 1-31, but doesn't validate against the actual month:
- February 30, 31 → Allowed ✗
- April 31, June 31, etc. → Allowed ✗
- February 29 in non-leap years → Allowed ✗

**Impact:** Invalid BirthData can be created, potentially causing:
- Downstream calculation errors
- Confusing error messages from `lunar_python`
- Database corruption if persisted

**Recommendation:**
```python
from calendar import monthrange

def __post_init__(self):
    """Validate birth data."""
    if not (1 <= self.month <= 12):
        raise ValueError(f"Month must be 1-12, got: {self.month}")

    # Validate day against actual month
    _, max_day = monthrange(self.year, self.month)
    if not (1 <= self.day <= max_day):
        raise ValueError(
            f"Day must be 1-{max_day} for {self.year}/{self.month}, got: {self.day}"
        )

    if not (0 <= self.hour <= 23):
        raise ValueError(f"Hour must be 0-23, got: {self.hour}")
    if not (0 <= self.minute <= 59):
        raise ValueError(f"Minute must be 0-59, got: {self.minute}")
```

### 2. Year Range Not Validated

**Issue:** No validation on year range.

**Problems:**
- Year 0 or negative years → Allowed
- Very old years (pre-1900) → May cause `lunar_python` issues
- Future years (2100+) → May exceed calendar calculations

**Recommendation:**
```python
# Reasonable year range for BaZi calculations
MIN_YEAR = 1900
MAX_YEAR = 2100

if not (MIN_YEAR <= self.year <= MAX_YEAR):
    raise ValueError(f"Year must be {MIN_YEAR}-{MAX_YEAR}, got: {self.year}")
```

### 3. No Leap Year Validation for February

**Issue:** Related to #1, February 29 in non-leap years is accepted.

**Example:**
```python
BirthData(year=2023, month=2, day=29)  # 2023 is not a leap year!
```

This passes current validation but would cause errors later.

### 4. Minute Precision Not Used

**Issue:** `minute` field exists but doesn't affect BaZi calculations.

**Analysis:**
- Hour pillar uses 2-hour blocks
- Minute only matters for hour boundary cases (e.g., 10:59 vs 11:01)
- Currently, minute is stored but not used in calculations

**Questions:**
- Should minute affect hour pillar when crossing boundary?
- Should we document that minute is optional/unused?

---

## Areas for Improvement

### 1. Add Comprehensive Date Validation

```python
from datetime import date

def __post_init__(self):
    try:
        date(self.year, self.month, self.day)
    except ValueError as e:
        raise ValueError(f"Invalid date: {self.year}-{self.month}-{self.day}") from e
```

### 2. Add Factory Method with Validation

```python
@classmethod
def create(
    cls,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    is_male: bool = True,
    name: Optional[str] = None,
) -> BirthData:
    """Create BirthData with full validation."""
    # All validation here
    return cls(year, month, day, hour, minute, is_male, name)
```

### 3. Add Type Hints for Optional Fields

```python
minute: int = 0  # Currently only used for display, not calculation
is_male: bool = True  # Affects some LiuNian analysis
name: Optional[str] = None  # Display only
```

### 4. Add Convenience Properties

```python
@property
def datetime(self) -> datetime:
    """Return as datetime object."""
    return datetime(self.year, self.month, self.day, self.hour, self.minute)

@property
def date_str(self) -> str:
    """Return formatted date string."""
    return f"{self.year}-{self.month:02d}-{self.day:02d}"

@property
def time_str(self) -> str:
    """Return formatted time string."""
    return f"{self.hour:02d}:{self.minute:02d}"
```

### 5. Add Timezone Awareness (Future Enhancement)

BaZi should be calculated based on local solar time, not UTC or timezone-adjusted time. Currently, timezone is not considered.

```python
@dataclass(frozen=True)
class BirthData:
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    is_male: bool = True
    name: Optional[str] = None
    longitude: Optional[float] = None  # For true solar time calculation
    timezone: Optional[str] = None  # For reference only
```

---

## Test Coverage Gaps

1. **Edge case:** February 29 in leap year (valid)
2. **Edge case:** February 29 in non-leap year (invalid)
3. **Edge case:** Day 31 in 30-day months (invalid)
4. **Edge case:** Hour 23 (晚子时 boundary)
5. **Edge case:** Year boundaries (1900, 2100)
6. **Edge case:** Negative years
7. **Edge case:** Very large years (overflow)

---

## Comparison with from_datetime Method

The `from_datetime` classmethod (bazi.py:43-54) bypasses direct validation:

```python
@classmethod
def from_datetime(cls, dt: datetime, is_male: bool = True, name: Optional[str] = None) -> BirthData:
    return cls(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        is_male=is_male,
        name=name,
    )
```

**Analysis:** Since `datetime` is already a valid date, this is safe. The validation in `__post_init__` will still run but should always pass for valid `datetime` inputs.

---

## Validation Strategy Comparison

| Approach | Pros | Cons |
|----------|------|------|
| Current (basic ranges) | Fast, simple | Allows invalid dates |
| Full date validation | Correct | Slightly slower |
| External validation | Thin model | Validation can be bypassed |

**Recommendation:** Full date validation in `__post_init__` is the safest approach for a value object.

---

## Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| High | Day-of-month not validated | Invalid data accepted | Low |
| Medium | Year range not validated | Edge case failures | Low |
| Medium | February 29 leap year | Invalid data accepted | Low |
| Low | Minute field unused | Unclear purpose | Low (doc) |
| Future | Timezone/longitude | True solar time | High |
