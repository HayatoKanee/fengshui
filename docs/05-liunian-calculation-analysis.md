# LiuNian (Yearly Fortune) Analysis

## Overview

LiuNian (流年) analysis predicts yearly fortune by examining how the year's pillar interacts with the natal BaZi chart. The year's stem primarily affects the first half of the year, while the branch affects the second half.

**Key Files:**
- `bazi/application/services/liunian_analysis.py` - Main analysis service
- `bazi/application/services/shishen_handlers.py` - ShiShen-specific handlers
- `bazi/application/content/` - Text content for interpretations

---

## Current Implementation

### Year Pillar Calculation (liunian_analysis.py:100-104)

```python
# Use actual date for year pillar calculation (respects Lichun)
solar = Solar.fromYmd(year, month, day)
lunar = solar.getLunar()
year_bazi = lunar.getEightChar()
```

**Correct:** Uses `lunar_python` to respect Lichun (立春) boundary for year pillar changes.

### Analysis Structure (liunian_analysis.py:107-128)

1. Year stem ShiShen → Upper half of year analysis
2. Year branch hidden stems ShiShen → Lower half of year analysis
3. Combination analysis → Yearly interactions with natal chart

---

## Potential Logic Errors

### 1. **CRITICAL:** Fragile Data Structure Access (liunian_analysis.py:153-160)

**Issue:** The code accesses nested tuple structures by hardcoded indices:

```python
# shishen_list[2] = ('日主', [hidden_stem_shishens for day branch])
day_branch_shishens = shishen_list[2][1]  # List of hidden stem ShiShens
if day_branch_shishens:
    main_hidden_shishen = day_branch_shishens[0]
```

**Problems:**
1. Magic number `2` for day pillar index
2. Magic index `[1]` for hidden stems
3. Assumes list structure, not dict
4. Will silently break if ShiShen calculator changes format

**Recommendation:**
```python
# Use named access or structured types
@dataclass
class PillarShiShenDetail:
    pillar_name: str
    stem_shishen: Optional[ShiShen]
    hidden_shishen: Dict[ShiShen, float]
```

### 2. String-Based ShiShen Comparison Throughout

**Issue:** All ShiShen comparisons use Chinese strings:

```python
if self._check_if_he_target(shishen, bazi, year_bazi, '正财'):
    analysis += "•本命正财..."

if self._check_if_he_target(shishen, bazi, year_bazi, '偏财'):
    analysis += "•本命偏财..."
```

**Problems:**
1. Typo risk (e.g., '正才' vs '正财')
2. No compile-time checking
3. Inconsistent with domain model using `ShiShen` enum

**Recommendation:** Use ShiShen enum:
```python
if self._check_if_he_target(shishen, bazi, year_bazi, ShiShen.ZHENG_CAI):
    ...
```

### 3. Index-Based Character Access (liunian_analysis.py:345-352)

**Issue:** Direct string index access for stem/branch positions:

```python
s = bazi.toString().replace(' ', '')  # e.g., "甲子乙丑丙寅丁卯"
for i in indices:
    if i < len(s):
        if (
            self._check_he(year_bazi.getYearGan(), s[i])
            or self._check_he(year_bazi.getYearZhi(), s[i])
        ):
```

**Problems:**
1. Assumes specific string format from `bazi.toString()`
2. Index `i` maps to character positions, not pillar positions
3. Bound checking `if i < len(s)` suggests uncertainty about format

**Recommendation:** Use structured access:
```python
pillars = [bazi.getYearGan(), bazi.getYearZhi(), ...]
for position in positions:
    char = pillars[position]
```

### 4. Mixed Domain Dependencies

**Issue:** Application service imports directly from `lunar_python`:

```python
from lunar_python import Solar
# ...
solar = Solar.fromYmd(year, month, day)
lunar = solar.getLunar()
year_bazi = lunar.getEightChar()
```

**Architecture Violation:** This bypasses the Ports & Adapters pattern. The application layer should use `LunarPort` interface, not `lunar_python` directly.

**Recommendation:**
```python
class LiunianAnalysisService:
    def __init__(self, lunar_adapter: LunarPort):
        self._lunar = lunar_adapter

    def analyse_liunian(self, ...):
        year_bazi = self._lunar.get_bazi_for_date(year, month, day)
```

### 5. _find_shishen_indices Counter Logic (liunian_analysis.py:317-333)

**Issue:** The index counter increments differently for stem and hidden stems:

```python
def _find_shishen_indices(self, target: str, shishen_list: List) -> List[int]:
    indices = []
    i = 0
    for shishen, sublist in shishen_list:
        if shishen == target:
            indices.append(i)
        i += 1  # Increment for stem
        for sub_shishen in sublist:
            if sub_shishen == target:
                indices.append(i)
        i += 1  # Increment again after all hidden stems
    return indices
```

**Problem:** Index meanings:
- 0 = year stem
- 1 = year branch (all hidden stems share same index!)
- 2 = month stem
- 3 = month branch
- ...

Multiple hidden stems in same branch get the same index. This seems intentional (all hidden stems in branch = one position), but:
- Comments don't clarify
- May cause confusion with 通根 (rooted) analysis

### 6. 通根 (Rooting) Logic (liunian_analysis.py:291-300)

**Issue:** The 伤官通根 check requires BOTH stem AND branch indices:

```python
if 0 in shang_guan_indices and 1 in shang_guan_indices:
    analysis += "•伤官通根在年柱，代表幼年时期..."
```

**Problem:** Index 1 represents ALL hidden stems in year branch. So if 伤官 appears in:
- Year stem (index 0)
- Any year branch hidden stem (index 1)

This triggers the "通根" message. This may be correct if any hidden stem makes it "rooted", but traditional 通根 requires same ShiShen in both positions.

---

## Areas for Improvement

### 1. Use Structured Types for ShiShen Analysis

**Current:** Nested tuples and lists
**Proposed:**
```python
@dataclass
class LiunianShiShenAnalysis:
    year_stem_shishen: str
    year_branch_shishen: Dict[str, float]
    affected_natal_positions: List[str]
```

### 2. Separate Text Generation from Logic

**Current:** Analysis logic and HTML text generation mixed.
**Proposed:** Return structured analysis, let presenter handle formatting:

```python
@dataclass
class LiunianAnalysisResult:
    year_pillar: str
    stem_shishen: ShiShen
    branch_shishen_ratios: Dict[ShiShen, float]
    combination_effects: List[CombinationEffect]
    warnings: List[str]

# Separate presenter
class LiunianPresenter:
    def to_html(self, result: LiunianAnalysisResult) -> str:
```

### 3. Add Gender-Specific Handler Registry

**Current:** Gender checks scattered throughout:
```python
if is_male:
    analysis += "•男命正官被流年合..."
else:
    analysis += "•女命正官被流年合..."
```

**Proposed:** Gender-aware handler registry:
```python
HANDLERS = {
    '正官': {
        'male': handle_zhengguan_male,
        'female': handle_zhengguan_female,
        'common': handle_zhengguan_common,
    }
}
```

### 4. Document Analysis Rules

The analysis contains many BaZi rules without citations:
- "正财被合，主钱财流失大"
- "七杀有两个以上者，精神显得委靡不振"
- "偏印被流运合住，母亲身体变差"

**Enhancement:** Add source references or confidence levels.

---

## Test Coverage Gaps

1. **Edge case:** LiuNian date before Lichun (Jan-Feb)
2. **Edge case:** Year pillar same as natal year pillar
3. **Edge case:** All hidden stems being same ShiShen
4. **String manipulation:** `bazi.toString()` format variations
5. **Gender-specific:** Female-specific analysis paths

---

## Calculation Flow

```
Birth BaZi + LiuNian Date
    ↓
lunar_python.getEightChar() for year pillar
    ↓
Year Stem ShiShen (upper half analysis)
    ↓
Year Branch Hidden Stems ShiShen (lower half analysis)
    ↓
Combination Check (natal ↔ yearly 合)
    ├── 正财被合 check
    ├── 偏财被合 check
    ├── 正官被合 check
    ├── 七杀 count check
    ├── 偏印被合 check
    ├── 正印被合 check (weak only)
    ├── 伤官通根 check
    └── 食神被合 check
    ↓
Gender-specific analysis
    ↓
HTML-formatted text output
```

---

## Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| High | Fragile tuple/index access | Maintenance nightmare | Medium |
| High | Direct lunar_python dependency | Architecture violation | Medium |
| Medium | String-based ShiShen comparison | Runtime errors | Low |
| Medium | Mixed logic and presentation | Testability | High |
| Low | 通根 logic unclear | Analysis accuracy | Low |
