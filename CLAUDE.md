# CLAUDE.md - AI Assistant Guidelines for FengShui BaZi Application

## Project Overview

This is a **Django 6.0+ web application** for Chinese BaZi (八字) Four Pillars of Destiny analysis. The application provides astrological calculations based on Chinese metaphysics, including birth chart analysis, calendar features, and Flying Star (FeiXing) feng shui.

**Live Domain**: myfate.org
**Deployment**: Heroku (PostgreSQL in production, SQLite locally)

---

## Architecture

The project follows **Clean Architecture / DDD (Domain-Driven Design)** principles with strict layer separation:

```
bazi/
├── domain/                     # Pure Python - NO Django dependencies
│   ├── models/                 # Entities & Value Objects (dataclasses, enums)
│   ├── services/               # Domain services (business logic)
│   ├── constants/              # Domain constants (elements, relationships)
│   ├── feixing/                # Flying Star feng shui domain
│   └── ports/                  # Interfaces (Protocols) for external dependencies
│
├── application/                # Use cases - orchestrates domain
│   ├── services/               # Application services (BaziAnalysisService, CalendarService, etc.)
│   └── content/                # Analysis text content
│
├── infrastructure/             # Adapters & Django integration
│   ├── adapters/               # Port implementations (LunarPythonAdapter)
│   ├── repositories/           # Data access (DjangoProfileRepository)
│   └── di/                     # Dependency injection container
│
├── presentation/               # Django views (thin controllers)
│   ├── views/                  # View modules (auth, bazi, calendar, profile, etc.)
│   ├── forms/                  # Django forms
│   └── presenters/             # Template data formatters
│
├── templates/                  # Django templates (Tailwind + DaisyUI + Alpine.js)
├── tests/                      # Test suite (pytest)
└── management/commands/        # Django management commands
```

### Key Architectural Principles

1. **Domain layer is pure Python** - No Django imports allowed
2. **Dependencies point inward** - Infrastructure depends on domain, not vice versa
3. **Ports & Adapters** - External dependencies accessed via Protocol interfaces
4. **Dependency Injection** - All wiring done in `infrastructure/di/container.py`

---

## Key Domain Concepts

### BaZi (八字) Terminology

| Term | Chinese | Description |
|------|---------|-------------|
| **WuXing** | 五行 | Five Elements: Wood, Fire, Earth, Metal, Water |
| **YinYang** | 阴阳 | Yin and Yang polarity |
| **HeavenlyStem** | 天干 | 10 stems: 甲乙丙丁戊己庚辛壬癸 |
| **EarthlyBranch** | 地支 | 12 branches: 子丑寅卯辰巳午未申酉戌亥 |
| **Pillar** | 柱 | One stem + one branch (e.g., 甲子) |
| **BaZi** | 八字 | Four Pillars: Year, Month, Day, Hour |
| **ShiShen** | 十神 | Ten Gods relationships |
| **ShenSha** | 神煞 | Auxiliary stars |
| **WangXiang** | 旺相休囚死 | Seasonal element strength phases |
| **DayMaster** | 日主 | The day stem, represents the self |
| **LiuNian** | 流年 | Yearly fortune analysis |
| **FeiXing** | 飞星 | Flying Star feng shui |

### Domain Models Location

- **Elements**: `bazi/domain/models/elements.py` (WuXing, YinYang, WangXiang)
- **Stems/Branches**: `bazi/domain/models/stems_branches.py`
- **Pillar**: `bazi/domain/models/pillar.py`
- **BaZi**: `bazi/domain/models/bazi.py`
- **ShiShen**: `bazi/domain/models/shishen.py`
- **ShenSha**: `bazi/domain/models/shensha.py`
- **Analysis**: `bazi/domain/models/analysis.py`

---

## Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | Django 6.0+ |
| WSGI Server | Gunicorn |
| Database | PostgreSQL (Heroku), SQLite (local) |
| Static Files | WhiteNoise |
| Lunar Calendar | lunar_python library |
| AI Integration | OpenAI (for analysis text generation) |

### Frontend
| Component | Technology |
|-----------|------------|
| CSS Framework | Tailwind CSS 4.x + DaisyUI 5.x |
| Interactivity | HTMX 2.x + Alpine.js 3.x |
| React Islands | React 19.x (for complex components) |
| Build Tool | Vite 6.x |
| Package Manager | npm |

### Testing
| Component | Technology |
|-----------|------------|
| Test Runner | pytest + pytest-django |
| Coverage | pytest-cov |
| Markers | `@pytest.mark.slow`, `@pytest.mark.integration` |

---

## Directory Structure

```
fengshui/                       # Project root
├── bazi/                       # Main Django app
│   ├── domain/                 # Pure Python domain layer
│   ├── application/            # Application services
│   ├── infrastructure/         # Adapters & DI
│   ├── presentation/           # Views & forms
│   ├── templates/              # Django templates
│   ├── tests/                  # Test suite
│   ├── templatetags/           # Custom template filters
│   ├── management/commands/    # CLI commands
│   └── models.py               # Django ORM models (UserProfile)
├── fengshui/                   # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── frontend/                   # Vite + React frontend source
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── static/                     # Static files (Vite build output)
├── theme/                      # Tailwind theme config
├── locale/                     # i18n translations (zh-hans, en)
├── data/                       # Data files (gitignored)
└── requirements.txt            # Python dependencies
```

---

## Development Workflow

### Local Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver

# In another terminal, start Vite dev server (for HMR)
cd frontend && npm run dev
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run domain tests only (no Django required)
python -m pytest bazi/tests/domain/ -v

# Run with coverage
python -m pytest --cov=bazi --cov-report=term-missing

# Run specific test file
python -m pytest bazi/tests/domain/test_wuxing_calculator.py -v

# Skip slow tests
python -m pytest -m "not slow"
```

### Building for Production

```bash
# Build frontend assets
cd frontend && npm run build

# Collect static files
python manage.py collectstatic --noinput
```

### Database Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Management Commands

```bash
# BaZi lookup (find matching dates)
python manage.py bazi_lookup

# Load BaZi data
python manage.py load_bazi

# Experiment with BaZi calculations
python manage.py bazi_experiment
```

---

## Code Conventions

### Python Style

- Use **dataclasses** for domain models with `frozen=True` for immutability
- Use **Protocol** (structural typing) for ports, not ABC
- Use **type hints** throughout
- Domain layer must have **zero Django imports**
- Follow **PEP 8** naming conventions

### Imports

```python
# Good - explicit imports
from bazi.domain.models import BaZi, Pillar, WuXing
from bazi.infrastructure.di import get_container

# Bad - wildcard imports
from bazi.domain.models import *
```

### Using the DI Container

```python
from bazi.infrastructure.di import get_container

def my_view(request):
    container = get_container()
    result = container.bazi_service.analyze(birth_data)
    calendar = container.calendar_service.generate_month(2024, 12, favorable)
```

### Views Pattern

Views should be **thin** - delegate to application services:

```python
class BaziAnalysisView(ProfileMixin, TemplateView):
    template_name = 'bazi.html'

    def post(self, request, *args, **kwargs):
        form = BirthTimeForm(request.POST)
        if form.is_valid():
            # Delegate to application service
            result = self.container.bazi_service.analyze(...)
            return render(request, self.template_name, {'result': result})
```

### Template Conventions

- Use **Tailwind CSS** utility classes
- Use **DaisyUI** components (btn, card, modal, etc.)
- Use **Alpine.js** for local state (`x-data`, `x-show`, `x-on`)
- Use **HTMX** for server-driven updates (`hx-get`, `hx-post`, `hx-target`)

---

## Important Files

| File | Purpose |
|------|---------|
| `fengshui/settings.py` | Django settings (auto-detects Heroku via DYNO env) |
| `fengshui/urls.py` | URL routing (imports from presentation layer) |
| `bazi/infrastructure/di/container.py` | DI container - composition root |
| `bazi/domain/models/__init__.py` | All domain model exports |
| `bazi/application/services/__init__.py` | All application service exports |
| `bazi/presentation/views/__init__.py` | All view exports |
| `bazi/tests/conftest.py` | Pytest fixtures |
| `pytest.ini` | Pytest configuration |
| `frontend/vite.config.ts` | Vite build configuration |
| `Procfile` | Heroku process definition |

---

## Testing Conventions

### Test Structure

```python
# bazi/tests/domain/test_wuxing_calculator.py

class TestWuXingCalculator:
    """Tests for WuXing strength calculations."""

    def test_calculate_strength_wood_in_spring(self, wuxing_calculator, sample_bazi):
        """Wood element should be strong (旺) in spring."""
        result = wuxing_calculator.calculate_strength(sample_bazi)
        assert result.wood > result.metal
```

### Fixtures

Common fixtures are defined in `bazi/tests/conftest.py`:

- `sample_bazi` - A sample BaZi chart
- `birth_data` - Standard birth data
- `wuxing_calculator` - WuXingCalculator instance
- `di_container` - Fresh DI container
- `lunar_adapter` - LunarPythonAdapter instance

### Test Markers

```python
@pytest.mark.slow
def test_expensive_operation():
    ...

@pytest.mark.integration
def test_database_operation(db):
    ...
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Dev-only key |
| `DATABASE_URL` | PostgreSQL URL (Heroku) | SQLite locally |
| `DYNO` | Heroku dyno indicator | Not set locally |
| `OPENAI_API_KEY` | OpenAI API key (optional) | None |

---

## Deployment (Heroku)

The app auto-detects Heroku via the `DYNO` environment variable:

- **DEBUG** is automatically `False` on Heroku
- **DATABASE** uses `DATABASE_URL` from Heroku Postgres
- **SSL** is enforced in production
- **Static files** served via WhiteNoise

Build process (defined in `package.json`):
```json
{
  "heroku-postbuild": "cd frontend && npm install --include=dev && npm run build"
}
```

---

## Common Tasks

### Adding a New Domain Model

1. Create model in `bazi/domain/models/`
2. Export from `bazi/domain/models/__init__.py`
3. Add tests in `bazi/tests/domain/`

### Adding a New Application Service

1. Create service in `bazi/application/services/`
2. Export from `bazi/application/services/__init__.py`
3. Wire up in `bazi/infrastructure/di/container.py`
4. Add tests in `bazi/tests/application/`

### Adding a New View

1. Create view in `bazi/presentation/views/`
2. Export from `bazi/presentation/views/__init__.py`
3. Add URL pattern in `fengshui/urls.py`
4. Create template in `bazi/templates/`

### Adding a New Template

1. Create in `bazi/templates/` (or `bazi/templates/partials/` for HTMX fragments)
2. Use Tailwind CSS + DaisyUI classes
3. Use Alpine.js for local state if needed

---

## Troubleshooting

### Import Errors

Domain layer must not import Django. Check for accidental imports:
```bash
grep -r "from django" bazi/domain/
```

### DI Container Issues

Reset container for testing:
```python
from bazi.infrastructure.di import reset_container
reset_container()
```

### Verify Container Wiring

```bash
python -c "from bazi.infrastructure.di import get_container; print(get_container())"
```

### Frontend Build Issues

```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```

---

## References

- [README.md](README.md) - Project overview
- [REFACTORING.md](REFACTORING.md) - Architecture decisions and migration history
- [Django Documentation](https://docs.djangoproject.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [DaisyUI](https://daisyui.com/)
- [HTMX](https://htmx.org/)
- [Alpine.js](https://alpinejs.dev/)
