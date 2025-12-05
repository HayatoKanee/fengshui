# FengShui BaZi Application

A Django application for Chinese BaZi (八字) Four Pillars of Destiny analysis.

## Architecture

This application follows **Clean Architecture / DDD** principles:

```
bazi/
├── domain/                     # Pure Python - NO Django dependencies
│   ├── models/                 # Entities & Value Objects
│   │   ├── elements.py         # YinYang, WuXing, WangXiang
│   │   ├── stems_branches.py   # HeavenlyStem, EarthlyBranch
│   │   ├── pillar.py           # Pillar (干支 column)
│   │   ├── bazi.py             # BaZi (Four Pillars)
│   │   ├── shishen.py          # ShiShen (Ten Gods)
│   │   ├── shensha.py          # ShenSha (auxiliary stars)
│   │   └── analysis.py         # Analysis result types
│   ├── services/               # Domain services
│   │   ├── wuxing_calculator.py    # Five Elements strength
│   │   ├── shishen_calculator.py   # Ten Gods calculation
│   │   ├── day_master_analyzer.py  # Day Master analysis
│   │   └── shensha_calculator.py   # ShenSha calculation
│   └── ports/                  # Interfaces (Protocols)
│       ├── lunar_port.py       # Lunar calendar interface
│       └── profile_port.py     # User profile repository
│
├── application/                # Use cases - orchestrates domain
│   └── services/
│       ├── bazi_analysis.py    # BaZi analysis workflow
│       ├── calendar_service.py # Calendar operations
│       └── profile_service.py  # Profile management
│
├── infrastructure/             # Adapters & Django integration
│   ├── adapters/               # Port implementations
│   │   └── lunar_adapter.py    # LunarPython adapter
│   ├── repositories/           # Data access
│   │   └── profile_repository.py
│   └── di/                     # Dependency injection
│       └── container.py        # DI container
│
├── presentation/               # Django views (thin)
│   ├── views/                  # View modules
│   └── forms/                  # Django forms
│
└── tests/
    └── domain/                 # 255 tests, 95% coverage
```

## Key Concepts

### Domain Models

- **WuXing (五行)**: Five Elements - Wood, Fire, Earth, Metal, Water
- **HeavenlyStem (天干)**: 10 stems - 甲乙丙丁戊己庚辛壬癸
- **EarthlyBranch (地支)**: 12 branches - 子丑寅卯辰巳午未申酉戌亥
- **Pillar (柱)**: One stem + one branch (e.g., 甲子)
- **BaZi (八字)**: Four Pillars - Year, Month, Day, Hour

### Domain Services

- **WuXingCalculator**: Calculates Five Elements strength with seasonal adjustment
- **ShiShenCalculator**: Determines Ten Gods relationships
- **DayMasterAnalyzer**: Analyzes Day Master strength and favorable elements
- **ShenShaCalculator**: Calculates auxiliary stars (神煞)

## Running Tests

```bash
# Domain tests (no Django required)
python -m pytest bazi/tests/domain/ -v

# With coverage
python -m pytest bazi/tests/domain/ --cov=bazi/domain --cov-report=term-missing
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4.2 |
| Domain | Pure Python (dataclasses, enums) |
| Tests | pytest, pytest-cov |
| Lunar Calendar | LunarPython |

## Development

See [REFACTORING.md](REFACTORING.md) for architecture details and migration progress.
