"""
Django Profile Repository - ORM implementation of ProfileRepository.

This repository wraps the Django UserProfile model, providing
a clean interface for the domain layer without Django dependencies.
"""
from __future__ import annotations

from typing import List, Optional

from django.db import transaction

from bazi.models import UserProfile
from bazi.domain.models import BirthData
from bazi.domain.ports import ProfileData


class DjangoProfileRepository:
    """
    Repository that wraps Django ORM for profile persistence.

    Implements the ProfileRepository Protocol, converting between
    Django models and domain ProfileData objects.
    """

    def get_by_id(self, profile_id: int) -> Optional[ProfileData]:
        """
        Get a profile by its ID.

        Args:
            profile_id: The profile's database ID

        Returns:
            ProfileData if found, None otherwise
        """
        try:
            profile = UserProfile.objects.get(pk=profile_id)
            return self._to_profile_data(profile)
        except UserProfile.DoesNotExist:
            return None

    def get_by_user(self, user_id: int) -> List[ProfileData]:
        """
        Get all profiles for a user.

        Args:
            user_id: The user's database ID

        Returns:
            List of ProfileData for the user
        """
        profiles = UserProfile.objects.filter(user_id=user_id)
        return [self._to_profile_data(p) for p in profiles]

    def get_default_for_user(self, user_id: int) -> Optional[ProfileData]:
        """
        Get the default profile for a user.

        Args:
            user_id: The user's database ID

        Returns:
            Default ProfileData if exists, None otherwise
        """
        try:
            profile = UserProfile.objects.get(user_id=user_id, is_default=True)
            return self._to_profile_data(profile)
        except UserProfile.DoesNotExist:
            return None

    def save(self, profile: ProfileData) -> ProfileData:
        """
        Save a profile (create or update).

        Args:
            profile: ProfileData to save

        Returns:
            Saved ProfileData with ID populated
        """
        if profile.id is None:
            # Create new profile
            django_profile = UserProfile(
                user_id=profile.user_id,
                name=profile.name,
                birth_year=profile.birth_data.year,
                birth_month=profile.birth_data.month,
                birth_day=profile.birth_data.day,
                birth_hour=profile.birth_data.hour,
                birth_minute=profile.birth_data.minute,
                is_male=profile.birth_data.is_male,
                is_default=profile.is_default,
            )
            django_profile.save()
            return self._to_profile_data(django_profile)
        else:
            # Update existing profile
            django_profile = UserProfile.objects.get(pk=profile.id)
            django_profile.name = profile.name
            django_profile.birth_year = profile.birth_data.year
            django_profile.birth_month = profile.birth_data.month
            django_profile.birth_day = profile.birth_data.day
            django_profile.birth_hour = profile.birth_data.hour
            django_profile.birth_minute = profile.birth_data.minute
            django_profile.is_male = profile.birth_data.is_male
            django_profile.is_default = profile.is_default
            django_profile.save()
            return self._to_profile_data(django_profile)

    def delete(self, profile_id: int) -> bool:
        """
        Delete a profile by ID.

        Args:
            profile_id: The profile's database ID

        Returns:
            True if deleted, False if not found
        """
        try:
            profile = UserProfile.objects.get(pk=profile_id)
            profile.delete()
            return True
        except UserProfile.DoesNotExist:
            return False

    @transaction.atomic
    def set_default(self, profile_id: int, user_id: int) -> bool:
        """
        Set a profile as the default for a user.

        This unsets any previous default.

        Args:
            profile_id: The profile to set as default
            user_id: The user's database ID

        Returns:
            True if successful, False if profile not found
        """
        try:
            # Unset all defaults for this user
            UserProfile.objects.filter(user_id=user_id).update(is_default=False)

            # Set the new default
            profile = UserProfile.objects.get(pk=profile_id, user_id=user_id)
            profile.is_default = True
            profile.save()
            return True
        except UserProfile.DoesNotExist:
            return False

    def count_for_user(self, user_id: int) -> int:
        """
        Count profiles for a user.

        Args:
            user_id: The user's database ID

        Returns:
            Number of profiles
        """
        return UserProfile.objects.filter(user_id=user_id).count()

    def _to_profile_data(self, django_profile: UserProfile) -> ProfileData:
        """
        Convert Django UserProfile to domain ProfileData.

        Args:
            django_profile: Django UserProfile model instance

        Returns:
            Domain ProfileData object
        """
        birth_data = BirthData(
            year=django_profile.birth_year,
            month=django_profile.birth_month,
            day=django_profile.birth_day,
            hour=django_profile.birth_hour,
            minute=django_profile.birth_minute,
            is_male=django_profile.is_male,
        )

        return ProfileData(
            id=django_profile.pk,
            user_id=django_profile.user_id,
            name=django_profile.name,
            birth_data=birth_data,
            is_default=django_profile.is_default,
        )
