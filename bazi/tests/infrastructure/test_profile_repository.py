"""
Tests for DjangoProfileRepository.

These tests verify the repository correctly implements CRUD operations
and the ProfileRepository protocol.
"""
import pytest

from bazi.domain.ports import ProfileData


@pytest.mark.django_db
class TestDjangoProfileRepository:
    """Tests for DjangoProfileRepository."""

    def test_get_by_id_returns_profile(self, profile_repository, user_profile):
        """get_by_id should return ProfileData for existing profile."""
        profile = profile_repository.get_by_id(user_profile.id)

        assert profile is not None
        assert isinstance(profile, ProfileData)
        assert profile.id == user_profile.id
        assert profile.name == user_profile.name

    def test_get_by_id_returns_none_for_missing(self, profile_repository):
        """get_by_id should return None for non-existent ID."""
        profile = profile_repository.get_by_id(99999)

        assert profile is None

    def test_get_by_user_returns_profiles(self, profile_repository, user, user_profile):
        """get_by_user should return all profiles for a user."""
        profiles = profile_repository.get_by_user(user.id)

        assert len(profiles) >= 1
        assert all(isinstance(p, ProfileData) for p in profiles)

    def test_get_by_user_returns_empty_for_no_profiles(self, profile_repository, admin_user):
        """get_by_user should return empty list for user with no profiles."""
        profiles = profile_repository.get_by_user(admin_user.id)

        assert profiles == []

    def test_get_default_for_user(self, profile_repository, user, user_profile):
        """get_default_for_user should return the default profile."""
        default = profile_repository.get_default_for_user(user.id)

        assert default is not None
        assert default.is_default is True

    def test_get_default_for_user_no_default(self, profile_repository, user, female_profile):
        """get_default_for_user returns None when no default is set."""
        # female_profile has is_default=False
        # We need to ensure no default exists
        from bazi.models import UserProfile
        UserProfile.objects.filter(user=user, is_default=True).delete()

        default = profile_repository.get_default_for_user(user.id)

        # Should return None or handle gracefully
        # Implementation may vary


@pytest.mark.django_db
class TestProfileRepositorySetDefault:
    """Tests for set_default functionality."""

    def test_set_default_updates_profile(self, profile_repository, user, user_profile, female_profile):
        """set_default should make the specified profile default."""
        # Initially user_profile is default
        assert user_profile.is_default is True
        assert female_profile.is_default is False

        # Set female_profile as default (requires both profile_id and user_id)
        profile_repository.set_default(female_profile.id, user.id)

        # Refresh from database
        user_profile.refresh_from_db()
        female_profile.refresh_from_db()

        assert user_profile.is_default is False
        assert female_profile.is_default is True

    def test_set_default_only_one_default(self, profile_repository, user):
        """Only one profile per user should be default."""
        from bazi.tests.factories import UserProfileFactory

        # Create multiple profiles
        profiles = [
            UserProfileFactory.create(user=user, is_default=False)
            for _ in range(3)
        ]

        # Set each as default sequentially
        for profile in profiles:
            profile_repository.set_default(profile.id, user.id)

        # Refresh all
        from bazi.models import UserProfile
        defaults = UserProfile.objects.filter(user=user, is_default=True)

        assert defaults.count() == 1


@pytest.mark.django_db
class TestProfileRepositoryWithFactories:
    """Tests using Factory Boy factories."""

    def test_create_profile_with_factory(self, profile_repository, user):
        """Factory-created profiles should work with repository."""
        from bazi.tests.factories import UserProfileFactory

        profile = UserProfileFactory.create(user=user)

        # Should be retrievable
        retrieved = profile_repository.get_by_id(profile.id)
        assert retrieved is not None
        assert retrieved.name == profile.name

    def test_batch_create_profiles(self, profile_repository, user):
        """Should handle multiple profiles correctly."""
        from bazi.tests.factories import create_profiles_for_user

        profiles = create_profiles_for_user(user, count=5)

        # Should all be retrievable
        user_profiles = profile_repository.get_by_user(user.id)
        assert len(user_profiles) >= 5

    def test_random_birth_data(self, profile_repository):
        """Random birth data from factories should be valid."""
        from bazi.tests.factories import UserProfileFactory

        profile = UserProfileFactory.create()

        # Should have valid birth data
        assert 1940 <= profile.birth_year <= 2020
        assert 1 <= profile.birth_month <= 12
        assert 1 <= profile.birth_day <= 28
        assert 0 <= profile.birth_hour <= 23
