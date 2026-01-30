# ShenSha (Auxiliary Stars) Calculation Analysis

## Overview

ShenSha (神煞) are auxiliary stars in BaZi that provide additional information about luck, personality, and life events. They are derived from relationships between day stem/branch and other positions.

**Key Files:**
- `bazi/domain/models/shensha.py` - ShenSha types and models
- `bazi/domain/services/shensha_calculator.py` - ShenSha calculation service

---

## Current Implementation

### ShenSha Types Implemented

| Category | ShenSha | Chinese | Lookup Base |
|----------|---------|---------|-------------|
| Noble | TIAN_YI_GUI_REN | 天乙贵人 | Day stem → Branch |
| Virtue | TIAN_DE | 天德 | Month branch → Stem |
| Virtue | YUE_DE | 月德 | Month branch → Stem |
| Academic | WEN_CHANG | 文昌 | Day stem → Branch |
| Prosperity | LU_SHEN | 禄神 | Day stem → Branch |
| Challenge | YANG_REN | 羊刃 | Day stem → Branch |
| Romance | TAO_HUA | 桃花 | Year/Day branch → Branch |
| Travel | YI_MA | 驿马 | Year branch → Branch |
| Spiritual | HUA_GAI | 华盖 | Year branch → Branch |
| Leadership | JIANG_XING | 将星 | Year branch → Branch |

### Lookup Tables (shensha_calculator.py:20-173)

All lookups are implemented as dictionaries with O(1) access.

---

## Potential Logic Errors

### 1. **BUG:** 天德 (Tian De) Lookup Table Inconsistency (shensha_calculator.py:37-51)

**Issue:** Comments indicate uncertainty about the correct mapping:

```python
_TIAN_DE: Dict[EarthlyBranch, HeavenlyStem] = {
    EarthlyBranch.YIN: HeavenlyStem.DING,
    EarthlyBranch.MAO: HeavenlyStem.GENG,  # Note: original was '申' but should be stem
    EarthlyBranch.CHEN: HeavenlyStem.REN,
    EarthlyBranch.SI: HeavenlyStem.XIN,
    EarthlyBranch.WU: HeavenlyStem.JIA,  # Note: original was '亥' but should be stem
    # ... more comments about conversions
}
```

**Problem:** The comments "original was '申'" and "original was '亥'" suggest these were branches in the source, but the code converted them to stems. This could be:
1. A correct conversion (申→庚, 亥→壬)
2. An error if the original used branch-to-branch mapping

**Standard 天德 Table (for verification):**
| Month Branch | 天德 |
|--------------|------|
| 寅 | 丁 |
| 卯 | 申 (branch!) |
| 辰 | 壬 |
| 巳 | 辛 |
| 午 | 亥 (branch!) |
| 未 | 甲 |
| 申 | 癸 |
| 酉 | 寅 (branch!) |
| 戌 | 丙 |
| 亥 | 乙 |
| 子 | 巳 (branch!) |
| 丑 | 庚 |

**Analysis:** Traditional 天德 actually maps to BOTH stems and branches depending on month! The current implementation forces all to stems, which is incorrect for months 卯, 午, 酉, 子.

**Recommendation:** Use a Union type or separate dictionaries:
```python
_TIAN_DE_STEM: Dict[EarthlyBranch, HeavenlyStem] = {...}
_TIAN_DE_BRANCH: Dict[EarthlyBranch, EarthlyBranch] = {...}
```

### 2. 华盖 (Hua Gai) Checked Against Year Branch Only (shensha_calculator.py:334-339)

**Issue:** HUA_GAI should be checked against both year AND day branches, but currently only checks year branch:

```python
# Check 华盖 (based on year branch → other branches)
if self.is_hua_gai(year_branch, branch):
    shensha_list.append(ShenSha(
        type=ShenShaType.HUA_GAI,
        position=f"{pos_name}_branch",
        triggered_by=year_branch.chinese,
    ))
```

**Problem:** Traditional BaZi checks 华盖 from both year and day pillars. Missing day-branch-based checks.

**Compare to 桃花 (TAO_HUA):** TAO_HUA correctly checks both year and day branches (lines 309-323).

### 3. 驿马 (Yi Ma) Checked Against Year Branch Only (shensha_calculator.py:325-331)

**Issue:** Similar to 华盖, 驿马 should check both year and day branches:

```python
# Check 驿马 (based on year branch → other branches)
if pos_name != "year" and self.is_yi_ma(year_branch, branch):
```

**Missing:** Day-branch-based 驿马 check.

### 4. 将星 (Jiang Xing) May Create Self-Reference (shensha_calculator.py:341-347)

**Issue:** 将星 is checked on all positions including year:

```python
# Check 将星 (based on year branch → other branches)
if self.is_jiang_xing(year_branch, branch):
```

**Problem:** When `pos_name == "year"`, we're checking if year_branch forms 将星 with itself. Looking at the table:

```python
_JIANG_XING = {
    EarthlyBranch.ZI: EarthlyBranch.ZI,  # 子 → 子 (self-match!)
    EarthlyBranch.MAO: EarthlyBranch.MAO,  # 卯 → 卯 (self-match!)
    # ...
}
```

If year branch is 子, it will match itself as 将星 at the year position. This may be intentional (自刑 concept) but should be documented.

### 5. Duplicate ShenSha Detection

**Issue:** A branch could match multiple ShenSha from different triggers:

Example: 桃花 can be triggered by both year and day branches:
```python
# Lines 309-323
if pos_name != "year" and self.is_tao_hua(year_branch, branch):
    shensha_list.append(...)
if pos_name not in ("year", "day") and self.is_tao_hua(day_branch, branch):
    shensha_list.append(...)
```

The same branch could get two TAO_HUA entries with different `triggered_by` values. This is likely intentional (double 桃花 is significant), but:
- The `get_shensha_summary` deduplicates by Chinese name (line 375)
- But `shensha_list` contains duplicates

---

## Areas for Improvement

### 1. Add Missing ShenSha Types

The current implementation covers common ShenSha but misses:
- 劫煞 (Jie Sha)
- 亡神 (Wang Shen)
- 孤辰/寡宿 (Gu Chen/Gua Su)
- 红艳煞 (Hong Yan Sha)

These are defined in `ShenShaType` enum but no calculators implemented.

### 2. Separate Beneficial and Challenging ShenSha

Current categorization in `get_shensha_summary` uses fixed categories:
```python
summary = {
    "贵人": [],
    "德星": [],
    "文星": [],
    # ...
}
```

**Enhancement:** Add a method to return beneficial vs challenging ShenSha directly:
```python
def get_beneficial_shensha(self, bazi: BaZi) -> List[ShenSha]:
def get_challenging_shensha(self, bazi: BaZi) -> List[ShenSha]:
```

### 3. ShenSha Strength/Weight

Not all ShenSha are equally significant. Some practitioners assign weights:
- 天乙贵人: Very significant
- 桃花: Moderate
- 华盖: Minor for most, significant for spiritual/academic paths

**Enhancement:** Add weight property to ShenShaType.

### 4. Document Position Significance

ShenSha in different positions have different meanings:
- 桃花 in hour pillar: Late-life romance issues
- 桃花 in day branch: Spouse-related romance issues
- 驿马 in month: Career involves travel

**Enhancement:** Add position-specific interpretation guidance.

### 5. Verify Traditional Tables

Given the comments about 天德 conversion, a systematic verification against traditional sources is recommended for:
- 天德
- 月德
- All branch-based lookups

---

## Test Coverage Gaps

1. **Edge case:** All four pillars triggering the same ShenSha
2. **Edge case:** 将星 self-reference (子年子时)
3. **Edge case:** Empty result (no ShenSha found)
4. **Verification:** Cross-reference each lookup table against traditional sources
5. **天德 mixed stem/branch verification**

---

## Lookup Table Verification Needed

The following tables should be verified against traditional BaZi sources:

| Table | Lines | Concern |
|-------|-------|---------|
| _TIAN_DE | 37-51 | Comments indicate conversion uncertainty |
| _YUE_DE | 53-67 | Should be verified alongside _TIAN_DE |
| _YANG_REN | 97-109 | Critical for safety/accident predictions |

---

## Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| High | 天德 table may be incorrect | Wrong readings | Medium |
| Medium | 华盖/驿马 missing day-branch check | Incomplete analysis | Low |
| Medium | Missing ShenSha implementations | Feature gap | Medium |
| Low | 将星 self-reference not documented | Clarity | Low |
| Low | No ShenSha weighting | Analysis depth | Medium |
