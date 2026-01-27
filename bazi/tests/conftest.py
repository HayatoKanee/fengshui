"""
Pytest fixtures for BaZi application tests.

This module provides reusable fixtures for testing across the application,
including Django models, domain objects, and service instances.
"""
import pytest
from datetime import datetime
from django.contrib.auth.models import User

from bazi.domain.models import BirthData, BaZi, Pillar
from bazi.domain.models.elements import WuXing, YinYang
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.models.analysis import FavorableElements


# =============================================================================
# Django Fixtures (require @pytest.mark.django_db)
# =============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def user_profile(db, user):
    """Create a test user profile with birth data."""
    from bazi.models import UserProfile
    return UserProfile.objects.create(
        user=user,
        name='张三',
        birth_year=1990,
        birth_month=6,
        birth_day=15,
        birth_hour=12,
        birth_minute=30,
        is_male=True,
        is_default=True
    )


@pytest.fixture
def female_profile(db, user):
    """Create a female test profile."""
    from bazi.models import UserProfile
    return UserProfile.objects.create(
        user=user,
        name='李四',
        birth_year=1985,
        birth_month=3,
        birth_day=8,
        birth_hour=6,
        birth_minute=0,
        is_male=False,
        is_default=False
    )


# =============================================================================
# Domain Fixtures (no database required)
# =============================================================================

@pytest.fixture
def birth_data():
    """Standard birth data for testing."""
    return BirthData(
        year=1990,
        month=6,
        day=15,
        hour=12,
        minute=30,
        is_male=True
    )


@pytest.fixture
def birth_data_female():
    """Female birth data for testing."""
    return BirthData(
        year=1985,
        month=3,
        day=8,
        hour=6,
        minute=0,
        is_male=False
    )


@pytest.fixture
def sample_pillar():
    """A sample pillar (甲子 - Jia Zi)."""
    return Pillar(
        stem=HeavenlyStem.JIA,
        branch=EarthlyBranch.ZI
    )


@pytest.fixture
def sample_bazi():
    """A sample BaZi chart for testing.

    甲子年 乙丑月 丙寅日 丁卯时
    """
    return BaZi(
        year_pillar=Pillar(HeavenlyStem.JIA, EarthlyBranch.ZI),
        month_pillar=Pillar(HeavenlyStem.YI, EarthlyBranch.CHOU),
        day_pillar=Pillar(HeavenlyStem.BING, EarthlyBranch.YIN),
        hour_pillar=Pillar(HeavenlyStem.DING, EarthlyBranch.MAO)
    )


@pytest.fixture
def strong_day_master_bazi():
    """BaZi with a strong day master (fire in summer).

    丙午年 丁巳月 丙午日 丁巳时
    Day master 丙 (Fire) with lots of fire support.
    """
    return BaZi(
        year_pillar=Pillar(HeavenlyStem.BING, EarthlyBranch.WU),
        month_pillar=Pillar(HeavenlyStem.DING, EarthlyBranch.SI),
        day_pillar=Pillar(HeavenlyStem.BING, EarthlyBranch.WU),
        hour_pillar=Pillar(HeavenlyStem.DING, EarthlyBranch.SI)
    )


@pytest.fixture
def weak_day_master_bazi():
    """BaZi with a weak day master (fire in winter).

    壬子年 癸丑月 丙子日 癸亥时
    Day master 丙 (Fire) surrounded by water.
    """
    return BaZi(
        year_pillar=Pillar(HeavenlyStem.REN, EarthlyBranch.ZI),
        month_pillar=Pillar(HeavenlyStem.GUI, EarthlyBranch.CHOU),
        day_pillar=Pillar(HeavenlyStem.BING, EarthlyBranch.ZI),
        hour_pillar=Pillar(HeavenlyStem.GUI, EarthlyBranch.HAI)
    )


@pytest.fixture
def favorable_elements():
    """Sample favorable elements for testing."""
    return FavorableElements(
        yong_shen=WuXing.FIRE,
        xi_shen=WuXing.WOOD,
        ji_shen=WuXing.WATER,
        chou_shen=WuXing.METAL
    )


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
def di_container():
    """Get the DI container with all services."""
    from bazi.infrastructure.di import get_container, reset_container
    reset_container()  # Ensure fresh container
    return get_container()


@pytest.fixture
def bazi_service(di_container):
    """Get the BaZi analysis service."""
    return di_container.bazi_service


@pytest.fixture
def calendar_service(di_container):
    """Get the calendar service."""
    return di_container.calendar_service


@pytest.fixture
def profile_service(di_container):
    """Get the profile service."""
    return di_container.profile_service


@pytest.fixture
def wuxing_calculator():
    """Get a WuXing calculator instance."""
    from bazi.domain.services import WuXingCalculator
    return WuXingCalculator()


@pytest.fixture
def shishen_calculator():
    """Get a ShiShen calculator instance."""
    from bazi.domain.services import ShiShenCalculator
    return ShiShenCalculator()


@pytest.fixture
def day_master_analyzer():
    """Get a day master analyzer instance."""
    from bazi.domain.services import DayMasterAnalyzer
    return DayMasterAnalyzer()


@pytest.fixture
def shensha_calculator():
    """Get a ShenSha calculator instance."""
    from bazi.domain.services import ShenShaCalculator
    return ShenShaCalculator()


@pytest.fixture
def branch_analyzer():
    """Get a branch analyzer instance."""
    from bazi.domain.services import BranchAnalyzer
    return BranchAnalyzer()


@pytest.fixture
def pattern_analyzer():
    """Get a pattern analyzer instance."""
    from bazi.domain.services import PatternAnalyzer
    return PatternAnalyzer()


# =============================================================================
# Infrastructure Fixtures
# =============================================================================

@pytest.fixture
def lunar_adapter():
    """Get the lunar adapter."""
    from bazi.infrastructure.adapters import LunarPythonAdapter
    return LunarPythonAdapter()


@pytest.fixture
def profile_repository(db):
    """Get the profile repository."""
    from bazi.infrastructure.repositories import DjangoProfileRepository
    return DjangoProfileRepository()
