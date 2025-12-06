"""
Factory Boy factories for BaZi application tests.

These factories generate realistic test data for Django models
and domain objects using Factory Boy and Faker.
"""
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth.models import User

from bazi.models import UserProfile
from bazi.domain.models import BirthData, Pillar, BaZi
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch

# Initialize Faker with Chinese locale for realistic names
fake = Faker('zh_CN')


# =============================================================================
# Django Model Factories
# =============================================================================

class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating test user profiles with birth data."""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    name = factory.LazyFunction(lambda: fake.name())
    birth_year = fuzzy.FuzzyInteger(1940, 2020)
    birth_month = fuzzy.FuzzyInteger(1, 12)
    birth_day = fuzzy.FuzzyInteger(1, 28)  # Safe for all months
    birth_hour = fuzzy.FuzzyInteger(0, 23)
    birth_minute = fuzzy.FuzzyInteger(0, 59)
    is_male = fuzzy.FuzzyChoice([True, False])
    is_default = False

    class Params:
        # Trait for male profile
        male = factory.Trait(is_male=True)
        # Trait for female profile
        female = factory.Trait(is_male=False)
        # Trait for default profile
        default = factory.Trait(is_default=True)

    @classmethod
    def create_with_calculated_fields(cls, **kwargs):
        """Create a profile and calculate BaZi fields."""
        from bazi.infrastructure.di import get_container

        profile = cls.create(**kwargs)
        container = get_container()

        # Calculate using the service
        birth_data = BirthData(
            year=profile.birth_year,
            month=profile.birth_month,
            day=profile.birth_day,
            hour=profile.birth_hour,
            minute=profile.birth_minute,
            is_male=profile.is_male
        )

        try:
            result = container.bazi_service.analyze(birth_data)
            profile.is_day_master_strong = result.day_master_analysis.is_strong
            profile.day_master_wuxing = result.day_master_wuxing.chinese
            profile.favorable_wuxing = ','.join(
                w.chinese for w in result.favorable_elements.favorable
            )
            profile.unfavorable_wuxing = ','.join(
                w.chinese for w in result.favorable_elements.unfavorable
            )
            profile.save()
        except Exception:
            pass  # Ignore calculation errors in test data

        return profile


# =============================================================================
# Domain Object Factories
# =============================================================================

class BirthDataFactory(factory.Factory):
    """Factory for creating BirthData domain objects."""

    class Meta:
        model = BirthData

    year = fuzzy.FuzzyInteger(1940, 2020)
    month = fuzzy.FuzzyInteger(1, 12)
    day = fuzzy.FuzzyInteger(1, 28)
    hour = fuzzy.FuzzyInteger(0, 23)
    minute = fuzzy.FuzzyInteger(0, 59)
    is_male = fuzzy.FuzzyChoice([True, False])

    class Params:
        # Trait for specific seasons
        spring = factory.Trait(month=fuzzy.FuzzyInteger(2, 4))
        summer = factory.Trait(month=fuzzy.FuzzyInteger(5, 7))
        autumn = factory.Trait(month=fuzzy.FuzzyInteger(8, 10))
        winter = factory.Trait(month=fuzzy.FuzzyInteger(11, 12))

        # Trait for male/female
        male = factory.Trait(is_male=True)
        female = factory.Trait(is_male=False)


class PillarFactory(factory.Factory):
    """Factory for creating Pillar domain objects."""

    class Meta:
        model = Pillar

    stem = fuzzy.FuzzyChoice(list(HeavenlyStem))
    branch = fuzzy.FuzzyChoice(list(EarthlyBranch))


class BaZiFactory(factory.Factory):
    """Factory for creating BaZi domain objects."""

    class Meta:
        model = BaZi

    year_pillar = factory.SubFactory(PillarFactory)
    month_pillar = factory.SubFactory(PillarFactory)
    day_pillar = factory.SubFactory(PillarFactory)
    hour_pillar = factory.SubFactory(PillarFactory)

    class Params:
        # Trait for fire day master
        fire_day_master = factory.Trait(
            day_pillar=factory.LazyFunction(
                lambda: Pillar(
                    fuzzy.FuzzyChoice([HeavenlyStem.BING, HeavenlyStem.DING]).fuzz(),
                    fuzzy.FuzzyChoice(list(EarthlyBranch)).fuzz()
                )
            )
        )

        # Trait for water day master
        water_day_master = factory.Trait(
            day_pillar=factory.LazyFunction(
                lambda: Pillar(
                    fuzzy.FuzzyChoice([HeavenlyStem.REN, HeavenlyStem.GUI]).fuzz(),
                    fuzzy.FuzzyChoice(list(EarthlyBranch)).fuzz()
                )
            )
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def create_birth_data_batch(count: int = 10, **kwargs) -> list[BirthData]:
    """Create a batch of random birth data for testing."""
    return BirthDataFactory.build_batch(count, **kwargs)


def create_profiles_for_user(user: User, count: int = 3) -> list[UserProfile]:
    """Create multiple profiles for a single user."""
    return UserProfileFactory.create_batch(count, user=user)


def create_test_user_with_profiles(profile_count: int = 3) -> tuple[User, list[UserProfile]]:
    """Create a test user with multiple profiles."""
    user = UserFactory.create()
    profiles = create_profiles_for_user(user, profile_count)
    return user, profiles
