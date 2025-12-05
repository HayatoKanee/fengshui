# FengShui App Refactoring Plan

> **Live Document** - Track architectural refactoring progress

## Tech Stack

### Current Stack
| Layer | Technology | Status |
|-------|------------|--------|
| **Backend** | Django 4.2 | ✅ Keep |
| **CSS** | Bootstrap 5.3.1 (CDN) | ⚠️ Replace |
| **JS** | jQuery 3.7.1 | ⚠️ Replace |
| **Icons** | Bootstrap Icons | ✅ Keep or replace |
| **Interactivity** | Manual AJAX | ⚠️ Replace |
| **Build** | None (CDN) | ⚠️ Add |

### Target Stack (State-of-the-Art 2025)
| Layer | Technology | Why |
|-------|------------|-----|
| **Backend** | Django 5.x | LTS, async support |
| **CSS** | Tailwind CSS + DaisyUI | Utility-first, ~10KB purged |
| **JS** | HTMX + Alpine.js | 90% SPA functionality, 10% complexity |
| **Icons** | Heroicons or Lucide | Tailwind-native |
| **Build** | Vite (django-vite) | HMR, fast builds |
| **Dev** | django-browser-reload | Hot reload |

### Key Packages
```bash
# Backend
pip install django-tailwind django-htmx django-browser-reload whitenoise

# Frontend (via npm in theme app)
npm install tailwindcss daisyui @tailwindcss/forms
npm install -D vite
```

---

## Current State

| Metric | Value | Target |
|--------|-------|--------|
| `views.py` lines | 1281 | <200 per module |
| `helper.py` lines | 1358 | Split into services |
| Domain models | 0 | 10+ |
| Test coverage | ~0% | >80% domain |
| Code duplication | 4 functions | 0 |
| CSS framework | Bootstrap 5 | Tailwind + DaisyUI |
| JS interactivity | jQuery AJAX | HTMX + Alpine.js |

## Target Architecture

```
bazi/
├── domain/                     # Pure Python - NO Django
│   ├── models/                 # DDD Entities & Value Objects
│   ├── services/               # Domain services
│   └── ports/                  # Interfaces (Protocols)
│
├── application/                # Use cases - orchestrates domain
│   └── services/
│
├── infrastructure/             # Adapters & Django integration
│   ├── adapters/               # Port implementations
│   ├── repositories/           # Data access
│   └── di/                     # Dependency injection container
│
├── presentation/               # Django views (thin)
│   ├── views/
│   ├── api/
│   └── forms/
│
└── tests/
    ├── domain/
    ├── application/
    └── integration/
```

## Dependency Injection Strategy

### Container Setup

```python
# infrastructure/di/container.py
from dataclasses import dataclass
from domain.ports import LunarPort, ProfileRepository
from infrastructure.adapters import LunarPythonAdapter
from infrastructure.repositories import DjangoProfileRepository
from application.services import BaziAnalysisService, CalendarService

@dataclass
class Container:
    """Simple DI container - instantiate once at app startup"""

    # Adapters (infrastructure)
    lunar_adapter: LunarPort
    profile_repo: ProfileRepository

    # Application services
    bazi_service: BaziAnalysisService
    calendar_service: CalendarService

    @classmethod
    def create(cls) -> "Container":
        """Factory method - wire up all dependencies"""
        lunar = LunarPythonAdapter()
        profile_repo = DjangoProfileRepository()

        return cls(
            lunar_adapter=lunar,
            profile_repo=profile_repo,
            bazi_service=BaziAnalysisService(lunar=lunar),
            calendar_service=CalendarService(
                lunar=lunar,
                profiles=profile_repo
            ),
        )

# Singleton instance
_container: Container | None = None

def get_container() -> Container:
    """Get or create the DI container"""
    global _container
    if _container is None:
        _container = Container.create()
    return _container
```

### Usage in Views

```python
# presentation/views/bazi.py
from infrastructure.di import get_container

def bazi_view(request):
    container = get_container()

    if request.method == 'POST' and form.is_valid():
        analysis = container.bazi_service.analyze(...)
        return render(request, 'bazi.html', {'analysis': analysis})
```

### Testing with DI

```python
# tests/application/test_bazi_service.py
from domain.ports import LunarPort
from application.services import BaziAnalysisService

class MockLunarAdapter(LunarPort):
    def get_bazi(self, birth):
        return BaZi(...)  # Controlled test data

def test_bazi_analysis():
    service = BaziAnalysisService(lunar=MockLunarAdapter())
    result = service.analyze(birth_data, year=2024)
    assert result.day_master_strength == ...
```

---

## Migration Phases

### Phase 0: Quick Wins (Pre-refactor cleanup)
> **Status**: [x] Completed

- [x] Delete duplicated functions from `views.py`
  - `is_yang_gong_taboo` (use helper.py version)
  - `is_po_ri` (use helper.py version)
  - `is_si_jue_ri` (use helper.py version)
  - `is_si_li_ri` (use helper.py version)
- [x] Replace `from .helper import *` with explicit imports
- [x] Replace `from .feixing import *` with explicit imports
- [x] Replace `from bazi.views import *` in urls.py with explicit imports
- [x] Add `.gitignore` entry for `.serena/` and `data/`

### Phase 1: Domain Models
> **Status**: [x] Completed

Create pure Python domain models (no Django dependencies).

#### 1.1 Core Value Objects
- [x] `domain/models/__init__.py`
- [x] `domain/models/elements.py`
  - [x] `WuXing` enum (木火土金水)
  - [x] `YinYang` enum (阴阳)
  - [x] `WangXiang` enum (旺相休囚死)
- [x] `domain/models/stems_branches.py`
  - [x] `HeavenlyStem` enum (天干: 甲乙丙丁戊己庚辛壬癸)
  - [x] `EarthlyBranch` enum (地支: 子丑寅卯辰巳午未申酉戌亥)
  - [x] `StemBranchRelations` (六合、五合、相冲)
- [x] `domain/models/pillar.py`
  - [x] `Pillar` dataclass (frozen, immutable)

#### 1.2 BaZi Aggregate
- [x] `domain/models/bazi.py`
  - [x] `BaZi` dataclass (year, month, day, hour pillars)
  - [x] `BirthData` dataclass (input DTO)

#### 1.3 Analysis Models
- [x] `domain/models/shishen.py`
  - [x] `ShiShen` enum (十神)
  - [x] `ShiShenChart` dataclass
  - [x] `calculate_shishen()` function
- [x] `domain/models/shensha.py`
  - [x] `ShenShaType` enum (神煞类型)
  - [x] `ShenSha` dataclass (神煞)
  - [x] `ShenShaAnalysis` dataclass
- [x] `domain/models/analysis.py`
  - [x] `WuXingStrength` dataclass
  - [x] `DayMasterStrength` dataclass
  - [x] `FavorableElements` dataclass (用神/忌神)
  - [x] `BaZiAnalysis` dataclass (complete analysis result)

### Phase 2: Domain Services
> **Status**: [x] Completed

Extract business logic from helper.py into focused services.

- [x] `domain/services/__init__.py`
- [x] `domain/services/wuxing_calculator.py`
  - [x] `WuXingCalculator` class
  - [x] `get_relationship_values()` - stem/branch relationship
  - [x] `get_wang_xiang()` - seasonal strength
  - [x] `accumulate_wuxing_values()` - chart totals
  - [x] `calculate_strength()` - complete WuXingStrength
- [x] `domain/services/shishen_calculator.py`
  - [x] `ShiShenCalculator` class
  - [x] `calculate_for_bazi()` - full ShiShenChart
  - [x] `get_detailed_shishen()` - with hidden stems
  - [x] `find_positions()` - locate specific ShiShen
- [x] `domain/services/day_master_analyzer.py`
  - [x] `DayMasterAnalyzer` class
  - [x] `analyze_strength()` - DayMasterStrength
  - [x] `calculate_shenghao()` - beneficial/harmful values
  - [x] `determine_favorable_elements()` - 用神/忌神
  - [x] `full_analysis()` - complete analysis
- [x] `domain/services/shensha_calculator.py`
  - [x] `ShenShaCalculator` class
  - [x] All `is_*` checkers (天乙贵人, 天德, 月德, 文昌, etc.)
  - [x] `calculate_for_bazi()` - ShenShaAnalysis
  - [x] `get_shensha_summary()` - by category
- [ ] `domain/services/liunian_analyzer.py` (deferred - complex OpenAI dependency)
  - [ ] `analyse_liunian()`
  - [ ] `analyse_liunian_shishen()`

### Phase 3: Ports (Interfaces)
> **Status**: [x] Completed

Define abstract interfaces for external dependencies.

- [x] `domain/ports/__init__.py`
- [x] `domain/ports/lunar_port.py`
  - [x] `LunarPort` Protocol - BaZi calculation, solar/lunar conversion, jieqi
- [x] `domain/ports/profile_port.py`
  - [x] `ProfileData` data transfer object
  - [x] `ProfileRepository` Protocol - CRUD operations for user profiles

### Phase 4: Infrastructure Adapters
> **Status**: [x] Completed

Implement ports with concrete adapters.

- [x] `infrastructure/__init__.py` (lazy imports to avoid Django config on module load)
- [x] `infrastructure/adapters/__init__.py`
- [x] `infrastructure/adapters/lunar_adapter.py`
  - [x] `LunarPythonAdapter` - wraps lunar_python library
  - [x] `get_bazi()` - calculate BaZi from BirthData
  - [x] `get_bazi_from_datetime()` - calculate from datetime
  - [x] `solar_to_lunar()` / `lunar_to_solar()` - date conversions
  - [x] `get_*_pillar()` - individual pillar lookups
  - [x] `get_jieqi()` / `get_next_jieqi()` / `days_until_next_jieqi()`
  - [x] `is_earth_dominant_period()` - 土旺 period detection
- [x] `infrastructure/repositories/__init__.py`
- [x] `infrastructure/repositories/profile_repo.py`
  - [x] `DjangoProfileRepository` - wraps Django ORM UserProfile
  - [x] CRUD operations (get_by_id, get_by_user, save, delete)
  - [x] `set_default()` with atomic transaction
  - [x] `_to_profile_data()` - Django model → domain DTO conversion

### Phase 5: DI Container
> **Status**: [x] Completed

Set up dependency injection.

- [x] `infrastructure/di/__init__.py`
- [x] `infrastructure/di/container.py`
  - [x] `Container` dataclass - holds all adapters and services
  - [x] `Container.create()` factory method - composition root
  - [x] `get_container()` singleton accessor
  - [x] `reset_container()` for testing

### Phase 6: Application Services
> **Status**: [x] Completed

Create use case orchestrators.

- [x] `application/__init__.py`
- [x] `application/services/__init__.py`
- [x] `application/services/bazi_analysis.py`
  - [x] `BaziAnalysisService` - complete BaZi analysis workflow
  - [x] `BaziAnalysisResult` dataclass - comprehensive analysis DTO
  - [x] `analyze()` - full analysis from birth data
  - [x] `analyze_for_year()` - with LiuNian context
  - [x] `get_quick_summary()` - lightweight summary
- [x] `application/services/calendar_service.py`
  - [x] `CalendarService` - generate calendar with day quality
  - [x] `CalendarDay`, `CalendarMonth` dataclasses
  - [x] `DayQuality` enum (EXCELLENT, GOOD, NEUTRAL, BAD, TERRIBLE)
  - [x] `generate_month()` - month calendar with quality scores
  - [x] `get_favorable_elements_for_profile()` - convenience method
- [x] `application/services/profile_service.py`
  - [x] `ProfileService` - profile management
  - [x] `ProfileSummary` dataclass with BaZi info
  - [x] CRUD operations + set_default
- [x] Updated DI Container with application services

### Phase 7: Presentation Layer Refactor
> **Status**: [ ] Not Started

Split views.py and make views thin.

- [ ] `presentation/__init__.py`
- [ ] `presentation/views/__init__.py`
- [ ] `presentation/views/auth.py`
  - [ ] `user_login`, `user_logout`, `user_register`
- [ ] `presentation/views/profile.py`
  - [ ] `profile_list`, `add_profile`, `edit_profile`, `delete_profile`
- [ ] `presentation/views/bazi.py`
  - [ ] `bazi_view`, `get_bazi_detail`
- [ ] `presentation/views/calendar.py`
  - [ ] `calendar_view`, `calendar_data`
- [ ] `presentation/views/static_pages.py`
  - [ ] `home_view`, `tiangan_view`, `yinyang_view`, etc.
- [ ] `presentation/views/lookup.py`
  - [ ] `bazi_lookup_view`, `zeri_view`
- [ ] `presentation/forms/__init__.py`
- [ ] Move `forms.py` to `presentation/forms/`

### Phase 8: Tests
> **Status**: [ ] Not Started

Add comprehensive tests for domain layer.

- [ ] `tests/__init__.py`
- [ ] `tests/domain/__init__.py`
- [ ] `tests/domain/test_models.py`
- [ ] `tests/domain/test_wuxing_calculator.py`
- [ ] `tests/domain/test_shishen_calculator.py`
- [ ] `tests/domain/test_day_master_analyzer.py`
- [ ] `tests/application/__init__.py`
- [ ] `tests/application/test_bazi_service.py`
- [ ] `tests/integration/__init__.py`
- [ ] `tests/integration/test_views.py`

### Phase 9: Cleanup
> **Status**: [ ] Not Started

Final cleanup and documentation.

- [ ] Delete old `helper.py` (after all extractions)
- [ ] Delete old `views.py` (after all splits)
- [ ] Update imports in `urls.py`
- [ ] Update `__init__.py` exports
- [ ] Add docstrings to all public interfaces
- [ ] Update README with architecture overview

---

## Frontend Modernization Phases

### Phase 10: HTMX Integration
> **Status**: [ ] Not Started

Add HTMX for dynamic updates without full page reloads.

- [ ] `pip install django-htmx`
- [ ] Add `django_htmx` to `INSTALLED_APPS`
- [ ] Add `HtmxMiddleware` to `MIDDLEWARE`
- [ ] Update `base.html` with HTMX script
- [ ] Create `templates/partials/` directory
- [ ] Convert AJAX calls to HTMX:
  - [ ] `bazi_detail` modal → `hx-post` + `hx-target`
  - [ ] `calendar_data` → `hx-get` + `hx-swap`
  - [ ] Form submissions → `hx-post` + partial responses
- [ ] Remove jQuery AJAX code

### Phase 11: Tailwind CSS Migration
> **Status**: [ ] Not Started

Replace Bootstrap with Tailwind CSS + DaisyUI.

- [ ] `pip install django-tailwind`
- [ ] `python manage.py tailwind init` → creates `theme/` app
- [ ] `python manage.py tailwind install`
- [ ] Configure `tailwind.config.js`:
  - [ ] Add DaisyUI plugin
  - [ ] Add WuXing color palette
  - [ ] Configure content paths
- [ ] Create `bazi/static/css/wuxing.css` (custom WuXing styles)
- [ ] Update `base.html`:
  - [ ] Replace Bootstrap CDN with `{% tailwind_css %}`
  - [ ] Remove jQuery CDN
- [ ] Migrate templates (one at a time):
  - [ ] `base.html` → Tailwind layout
  - [ ] `bazi.html` → DaisyUI components
  - [ ] `calendar.html` → DaisyUI calendar
  - [ ] `bazi_lookup.html` → DaisyUI forms
  - [ ] `zeri.html` → DaisyUI tables
  - [ ] All other templates
- [ ] Remove Bootstrap classes from all templates
- [ ] Delete `language.css` or migrate to Tailwind

### Phase 12: Alpine.js + Polish
> **Status**: [ ] Not Started

Add Alpine.js for local state and polish UI.

- [ ] Add Alpine.js to `base.html`
- [ ] Convert modals to Alpine.js (`x-show`, `x-data`)
- [ ] Add dark mode toggle (DaisyUI theme switcher)
- [ ] Add loading states with Alpine.js
- [ ] Add form validation feedback
- [ ] Performance optimization:
  - [ ] Run `python manage.py tailwind build` for production
  - [ ] Verify CSS bundle size (<15KB)
  - [ ] Add `whitenoise` for static file serving
- [ ] Browser testing across devices

---

## Frontend File Structure (After Phase 12)

```
bazi/
├── static/
│   └── css/
│       └── wuxing.css              # Custom WuXing element colors
├── templates/
│   ├── base.html                   # Tailwind + HTMX + Alpine
│   ├── partials/                   # HTMX partial templates
│   │   ├── bazi_detail.html
│   │   ├── calendar_day.html
│   │   └── search_results.html
│   └── pages/
│       └── ...
theme/                              # django-tailwind app
├── static_src/
│   ├── src/
│   │   └── styles.css              # Tailwind entry point
│   ├── tailwind.config.js
│   └── package.json
└── templates/
    └── base.html                   # Optional theme base
```

### Tailwind Config Example
```javascript
// theme/static_src/tailwind.config.js
module.exports = {
  content: [
    '../templates/**/*.html',
    '../../templates/**/*.html',
    '../../bazi/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'wuxing-wood': '#228B22',
        'wuxing-fire': '#DC143C',
        'wuxing-earth': '#DAA520',
        'wuxing-metal': '#C0C0C0',
        'wuxing-water': '#1E90FF',
      }
    },
  },
  plugins: [
    require('daisyui'),
    require('@tailwindcss/forms'),
  ],
  daisyui: {
    themes: ['light', 'dark', 'cupcake'],
  },
}
```

---

## Progress Log

| Date | Phase | Changes | Notes |
|------|-------|---------|-------|
| 2025-12-05 | - | Created REFACTORING.md | Architecture plan + DI strategy |
| 2025-12-05 | - | Added frontend phases 10-12 | HTMX + Tailwind + Alpine.js |
| 2025-12-05 | 0 | Completed Phase 0 | Removed duplicates, explicit imports |
| 2025-12-05 | 1 | Completed Phase 1 | Domain models: WuXing, Pillar, BaZi, ShiShen, ShenSha |
| 2025-12-05 | 2 | Completed Phase 2 | Services: WuXingCalculator, ShiShenCalculator, DayMasterAnalyzer, ShenShaCalculator |
| 2025-12-05 | 3 | Completed Phase 3 | Ports: LunarPort, ProfileRepository, ProfileData |
| 2025-12-05 | 4 | Completed Phase 4 | Adapters: LunarPythonAdapter, DjangoProfileRepository |
| 2025-12-05 | 5 | Completed Phase 5 | DI Container: Container, get_container(), reset_container() |

---

## Design Decisions

### Why Dataclasses over Django Models for Domain?

1. **No Django dependency** - Domain can be tested without Django
2. **Immutability** - `frozen=True` prevents accidental mutations
3. **Clear separation** - Domain models != database schema
4. **Type hints** - Better IDE support and documentation

### Why Simple DI Container over Django-DI libraries?

1. **Explicit** - All wiring visible in one place
2. **No magic** - Easy to understand and debug
3. **Testable** - Easy to swap implementations
4. **Lightweight** - No additional dependencies

### Why Protocols over ABC?

1. **Structural typing** - No need to inherit
2. **More Pythonic** - Duck typing with type hints
3. **Flexible** - Easier to mock in tests

### Why Tailwind over Bootstrap?

1. **Smaller bundle** - ~10KB purged vs ~200KB Bootstrap
2. **Utility-first** - No CSS overrides, compose in HTML
3. **Customizable** - WuXing colors as first-class utilities
4. **Modern** - State-of-the-art in 2025 Django projects
5. **DaisyUI** - Pre-built components when needed

### Why HTMX over React/Vue?

1. **No build step** - Works with Django templates natively
2. **Hypermedia** - Returns HTML, not JSON (Django's strength)
3. **90/10 rule** - 90% SPA features with 10% complexity
4. **Progressive** - Enhances server-rendered HTML
5. **Single language** - All logic in Python, not duplicated in JS

### Why Alpine.js over jQuery?

1. **Declarative** - State in HTML attributes
2. **Reactive** - Automatic DOM updates
3. **Lightweight** - ~15KB vs ~90KB jQuery
4. **Modern** - Designed for server-rendered apps
5. **HTMX companion** - Perfect pairing for local UI state

---

## Files to Create

```
bazi/
├── domain/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── elements.py
│   │   ├── stems_branches.py
│   │   ├── pillar.py
│   │   ├── bazi.py
│   │   ├── shishen.py
│   │   ├── shensha.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── wuxing_calculator.py
│   │   ├── shishen_calculator.py
│   │   ├── day_master_analyzer.py
│   │   ├── shensha_calculator.py
│   │   └── liunian_analyzer.py
│   └── ports/
│       ├── __init__.py
│       ├── lunar_port.py
│       └── profile_port.py
├── application/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── bazi_analysis.py
│       ├── calendar_service.py
│       └── profile_service.py
├── infrastructure/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── lunar_adapter.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── profile_repo.py
│   └── di/
│       ├── __init__.py
│       └── container.py
├── presentation/
│   ├── __init__.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── bazi.py
│   │   ├── calendar.py
│   │   ├── static_pages.py
│   │   └── lookup.py
│   └── forms/
│       ├── __init__.py
│       └── birth_form.py
└── tests/
    ├── __init__.py
    ├── domain/
    │   └── ...
    ├── application/
    │   └── ...
    └── integration/
        └── ...
```

---

## Commands

```bash
# Run tests
python manage.py test bazi.tests

# Check for import errors after refactoring
python -c "from bazi.domain.models import BaZi"

# Verify DI container
python -c "from bazi.infrastructure.di import get_container; print(get_container())"
```
