# BaZi Calculation Analysis Summary

## Overview

This document summarizes the analysis of BaZi (八字) calculation logic in the FengShui application, identifying potential logic errors, areas for improvement, and recommended priorities.

---

## Document Index

| # | Document | Focus Area |
|---|----------|------------|
| 01 | [WuXing Calculation](01-wuxing-calculation-analysis.md) | Five Elements strength calculation |
| 02 | [ShiShen Calculation](02-shishen-calculation-analysis.md) | Ten Gods relationship calculation |
| 03 | [ShenSha Calculation](03-shensha-calculation-analysis.md) | Auxiliary stars calculation |
| 04 | [Day Master Analysis](04-day-master-analysis.md) | Strength and favorable elements |
| 05 | [LiuNian Calculation](05-liunian-calculation-analysis.md) | Yearly fortune analysis |
| 06 | [Sexagenary Cycle](06-sexagenary-cycle-analysis.md) | 60-cycle date calculations |
| 07 | [BirthData Validation](07-birthdata-validation-analysis.md) | Input validation |

---

## Critical Issues (High Priority)

### 1. BirthData Validation Missing Day-of-Month Check
**File:** `bazi/domain/models/bazi.py:32-41`
**Impact:** Allows invalid dates like Feb 31
**Fix:** Add `calendar.monthrange` validation

### 2. 天德 (Tian De) Lookup Table Possibly Incorrect
**File:** `bazi/domain/services/shensha_calculator.py:37-51`
**Impact:** Wrong ShenSha detection
**Fix:** Verify against traditional sources

### 3. LiuNian Uses Fragile Index-Based Access
**File:** `bazi/application/services/liunian_analysis.py:153-160`
**Impact:** Breaks if ShiShen data structure changes
**Fix:** Use structured types with named access

---

## Medium Priority Issues

### 4. ShiShen Only Uses Main Hidden Stem
**File:** `bazi/domain/services/shishen_calculator.py:78-90`
**Impact:** Loses 30-40% of hidden stem information
**Fix:** Return full hidden stem breakdown with ratios

### 5. LiuNian Direct lunar_python Dependency
**File:** `bazi/application/services/liunian_analysis.py:14`
**Impact:** Violates Clean Architecture
**Fix:** Use LunarPort interface

### 6. 华盖/驿马 Missing Day-Branch Check
**File:** `bazi/domain/services/shensha_calculator.py:325-339`
**Impact:** Incomplete ShenSha detection
**Fix:** Add day-branch-based checks like 桃花

### 7. Day Master 50% Threshold Edge Case
**File:** `bazi/domain/models/analysis.py:79`
**Impact:** Exactly 50% classified as strong
**Fix:** Consider neutral category or `> 50`

---

## Low Priority Issues

### 8. WuXing Fallback Value Silent
**File:** `bazi/domain/services/wuxing_calculator.py:111`
**Impact:** Logic bugs hidden
**Fix:** Replace with explicit error

### 9. Year Pillar Ignores Lichun
**File:** `bazi/domain/services/sexagenary_calculator.py:371-392`
**Impact:** Known, mitigated by lunar_python
**Fix:** Document clearly

### 10. Hour 23 Date Boundary Not Documented
**File:** `bazi/domain/services/sexagenary_calculator.py:72-85`
**Impact:** Possible wrong day pillar for 23:00 births
**Fix:** Document 早子时/晚子时 handling

---

## Recommended Action Plan

### Phase 1: Critical Fixes (Immediate)
1. Add day-of-month validation to BirthData
2. Verify and fix 天德 lookup table
3. Refactor LiuNian to use structured types

### Phase 2: Accuracy Improvements
4. Return full hidden stem ShiShen breakdown
5. Add day-branch checks for 华盖/驿马
6. Review Day Master threshold logic

### Phase 3: Architecture Cleanup
7. Replace fallback values with errors
8. Move lunar_python usage behind LunarPort
9. Add comprehensive documentation

### Phase 4: Enhancements
10. Add special pattern detection (从格, 化格)
11. Implement missing ShenSha types
12. Add confidence metrics to analyses

---

## Calculation Flow Diagram

```
User Input (BirthData)
    ↓
Validation ← ISSUE: Missing day-of-month check
    ↓
lunar_python Adapter
    ↓
BaZi (4 Pillars)
    ↓
┌─────────────────────────────────────────────────────────┐
│                 WuXing Calculation                       │
│  Season → WangXiang → Element Strength                  │
│  ISSUE: Earth-dominant period not auto-detected         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                 Day Master Analysis                      │
│  Beneficial vs Harmful → Strong/Weak → Favorable        │
│  ISSUE: 50% boundary, no special patterns               │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                 ShiShen Calculation                      │
│  Day Master vs Each Position → Ten Gods                 │
│  ISSUE: Only main hidden stem analyzed                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                 ShenSha Calculation                      │
│  Lookup Tables → Auxiliary Stars                        │
│  ISSUE: 天德 table may be incorrect                     │
└─────────────────────────────────────────────────────────┘
    ↓
BaZiAnalysis Result
    ↓
┌─────────────────────────────────────────────────────────┐
│                 LiuNian Analysis                         │
│  Yearly Pillar × Natal Chart → Fortune                  │
│  ISSUE: Fragile data structure access                   │
└─────────────────────────────────────────────────────────┘
```

---

## Test Coverage Summary

| Component | Current Coverage | Gaps |
|-----------|-----------------|------|
| WuXing Calculator | Good | Earth-dominant period |
| Day Master Analyzer | Good | 50% boundary, special patterns |
| ShiShen Calculator | Good | Multiple hidden stems |
| ShenSha Calculator | Partial | Table verification |
| Sexagenary Calculator | Good | Pillar validity |
| BirthData | Partial | Invalid dates |
| LiuNian | Unknown | Fragile structures |

---

## Architecture Notes

### Strengths
- Clean separation between domain and application layers
- Pure Python domain (no Django dependencies)
- Ports & Adapters pattern for external dependencies
- Frozen dataclasses for immutability

### Areas for Improvement
- Some application services bypass ports (LiuNian → lunar_python)
- String-based comparisons instead of enum types in places
- Missing type validation in some lookup operations

---

## References

- Traditional BaZi texts for table verification
- lunar_python library documentation
- [Sexagenary calculation reference](https://ytliu0.github.io/ChineseCalendar/sexagenary.html)
