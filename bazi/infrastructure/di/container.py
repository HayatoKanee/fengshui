"""
Dependency Injection Container.

Simple DI container that wires up all dependencies at application startup.
This approach is explicit, easy to understand, and doesn't require
additional libraries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bazi.domain.services import (
    WuXingCalculator,
    ShiShenCalculator,
    DayMasterAnalyzer,
    ShenShaCalculator,
    BranchAnalyzer,
    PatternAnalyzer,
)
from bazi.domain.feixing import FeiXingCalculator
from bazi.infrastructure.adapters import LunarPythonAdapter

if TYPE_CHECKING:
    from bazi.domain.ports import LunarPort, ProfileRepository
    from bazi.infrastructure.repositories import DjangoProfileRepository
    from bazi.application.services import (
        BaziAnalysisService,
        CalendarService,
        DayQualityService,
        FeiXingService,
        LiunianAnalysisService,
        ProfileService,
    )
    from bazi.application.services.bazi_lookup_service import OptimizedBaziLookupService
    from bazi.domain.services.sexagenary_calculator import SexagenaryCycleCalculator


@dataclass
class Container:
    """
    Simple DI container - instantiate once at app startup.

    All dependencies are wired up in the create() factory method.
    This container holds:
    - Infrastructure adapters (ports implementations)
    - Domain services (pure business logic)
    - Application services (use case orchestrators)

    Usage in views:
        container = get_container()
        result = container.bazi_service.analyze(birth_data)
        calendar = container.calendar_service.generate_month(2024, 12, favorable)
    """

    # Infrastructure adapters (implements domain ports)
    lunar_adapter: LunarPort
    profile_repo: ProfileRepository

    # Domain services (pure business logic)
    wuxing_calculator: WuXingCalculator
    shishen_calculator: ShiShenCalculator
    day_master_analyzer: DayMasterAnalyzer
    shensha_calculator: ShenShaCalculator
    feixing_calculator: FeiXingCalculator
    sexagenary_calculator: SexagenaryCycleCalculator

    # Application services (use case orchestrators)
    bazi_service: BaziAnalysisService
    calendar_service: CalendarService
    day_quality_service: DayQualityService
    feixing_service: FeiXingService
    liunian_service: LiunianAnalysisService
    profile_service: ProfileService
    bazi_lookup_service: OptimizedBaziLookupService

    @classmethod
    def create(cls) -> Container:
        """
        Factory method - wire up all dependencies.

        This is the composition root where all dependencies are assembled.
        Call this once at application startup.
        """
        # Infrastructure adapters
        lunar = LunarPythonAdapter()

        # Import DjangoProfileRepository here to avoid Django config at module load
        from bazi.infrastructure.repositories import DjangoProfileRepository
        profile_repo = DjangoProfileRepository()

        # Domain services (no external dependencies)
        wuxing_calc = WuXingCalculator()
        shishen_calc = ShiShenCalculator()
        day_master_analyzer = DayMasterAnalyzer()
        shensha_calc = ShenShaCalculator()
        branch_analyzer = BranchAnalyzer()
        pattern_analyzer = PatternAnalyzer()
        feixing_calc = FeiXingCalculator()

        # Sexagenary calculator for optimized lookup
        from bazi.domain.services.sexagenary_calculator import SexagenaryCycleCalculator
        sexagenary_calc = SexagenaryCycleCalculator()

        # Application services (import here to avoid circular imports)
        from bazi.application.services import (
            BaziAnalysisService,
            CalendarService,
            DayQualityService,
            FeiXingService,
            LiunianAnalysisService,
            ProfileService,
        )

        bazi_service = BaziAnalysisService(
            lunar_adapter=lunar,
            wuxing_calculator=wuxing_calc,
            shishen_calculator=shishen_calc,
            day_master_analyzer=day_master_analyzer,
            shensha_calculator=shensha_calc,
            branch_analyzer=branch_analyzer,
            pattern_analyzer=pattern_analyzer,
        )

        calendar_service = CalendarService(
            lunar_adapter=lunar,
            wuxing_calculator=wuxing_calc,
            day_master_analyzer=day_master_analyzer,
        )

        day_quality_service = DayQualityService(
            lunar_adapter=lunar,
            bazi_service=bazi_service,
            calendar_service=calendar_service,
            shensha_calculator=shensha_calc,
        )

        profile_service = ProfileService(
            profile_repo=profile_repo,
            lunar_adapter=lunar,
            bazi_service=bazi_service,
        )

        liunian_service = LiunianAnalysisService()

        feixing_service = FeiXingService(calculator=feixing_calc)

        # Optimized BaZi lookup service
        from bazi.application.services.bazi_lookup_service import OptimizedBaziLookupService
        bazi_lookup_service = OptimizedBaziLookupService(lunar_adapter=lunar)

        return cls(
            lunar_adapter=lunar,
            profile_repo=profile_repo,
            wuxing_calculator=wuxing_calc,
            shishen_calculator=shishen_calc,
            day_master_analyzer=day_master_analyzer,
            shensha_calculator=shensha_calc,
            feixing_calculator=feixing_calc,
            sexagenary_calculator=sexagenary_calc,
            bazi_service=bazi_service,
            calendar_service=calendar_service,
            day_quality_service=day_quality_service,
            feixing_service=feixing_service,
            liunian_service=liunian_service,
            profile_service=profile_service,
            bazi_lookup_service=bazi_lookup_service,
        )


# Singleton instance
_container: Container | None = None


def get_container() -> Container:
    """
    Get or create the DI container singleton.

    Thread-safe for Django's typical request handling,
    as Django handles concurrent requests in separate threads
    and Python's GIL ensures atomic pointer assignments.

    Usage:
        from bazi.infrastructure.di import get_container

        def my_view(request):
            container = get_container()
            # Use container.lunar_adapter, container.wuxing_calculator, etc.
    """
    global _container
    if _container is None:
        _container = Container.create()
    return _container


def reset_container() -> None:
    """
    Reset the container singleton (useful for testing).

    In tests, call this in setUp/tearDown to get fresh instances.
    """
    global _container
    _container = None
