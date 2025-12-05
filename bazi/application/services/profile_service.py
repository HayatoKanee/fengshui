"""
Profile Application Service.

Handles user profile management operations, including
creating, updating, and analyzing profiles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from bazi.domain.models import BirthData, WuXing
from bazi.domain.ports import ProfileData

if TYPE_CHECKING:
    from bazi.domain.ports import ProfileRepository, LunarPort
    from bazi.application.services.bazi_analysis import BaziAnalysisService


@dataclass
class ProfileSummary:
    """
    Summary of a user profile with quick BaZi info.

    Used for profile lists and selection dropdowns.
    """

    id: int
    name: str
    birth_data: BirthData
    is_default: bool
    bazi_chinese: Optional[str] = None
    day_master_wuxing: Optional[str] = None
    is_day_master_strong: Optional[bool] = None

    @property
    def display_birth(self) -> str:
        """Formatted birth date/time for display."""
        bd = self.birth_data
        return f"{bd.year}年{bd.month}月{bd.day}日 {bd.hour}时{bd.minute}分"


class ProfileService:
    """
    Application service for user profile management.

    Handles CRUD operations for user profiles and integrates
    with BaZi analysis for profile enrichment.

    Usage:
        service = ProfileService(profile_repo, lunar_adapter)
        profiles = service.get_user_profiles(user_id)
        profile = service.create_profile(user_id, name, birth_data)
    """

    def __init__(
        self,
        profile_repo: ProfileRepository,
        lunar_adapter: Optional[LunarPort] = None,
        bazi_service: Optional[BaziAnalysisService] = None,
    ):
        """
        Initialize the profile service.

        Args:
            profile_repo: Repository for profile persistence
            lunar_adapter: Adapter for BaZi calculation (optional)
            bazi_service: Service for full BaZi analysis (optional)
        """
        self._repo = profile_repo
        self._lunar = lunar_adapter
        self._bazi_service = bazi_service

    def get_user_profiles(self, user_id: int) -> List[ProfileSummary]:
        """
        Get all profiles for a user with quick BaZi info.

        Args:
            user_id: The user's database ID

        Returns:
            List of ProfileSummary with basic BaZi information
        """
        profiles = self._repo.get_by_user(user_id)
        summaries = []

        for profile in profiles:
            summary = self._to_summary(profile)
            summaries.append(summary)

        return summaries

    def get_profile(self, profile_id: int) -> Optional[ProfileSummary]:
        """
        Get a single profile by ID.

        Args:
            profile_id: The profile's database ID

        Returns:
            ProfileSummary if found, None otherwise
        """
        profile = self._repo.get_by_id(profile_id)
        if profile:
            return self._to_summary(profile)
        return None

    def get_default_profile(self, user_id: int) -> Optional[ProfileSummary]:
        """
        Get the default profile for a user.

        Args:
            user_id: The user's database ID

        Returns:
            Default ProfileSummary if exists, None otherwise
        """
        profile = self._repo.get_default_for_user(user_id)
        if profile:
            return self._to_summary(profile)
        return None

    def create_profile(
        self,
        user_id: int,
        name: str,
        birth_data: BirthData,
        is_default: bool = False,
    ) -> ProfileSummary:
        """
        Create a new profile for a user.

        Args:
            user_id: The user's database ID
            name: Profile name
            birth_data: Birth date/time information
            is_default: Whether this should be the default profile

        Returns:
            Created ProfileSummary
        """
        # If this is set as default, unset existing default
        if is_default:
            existing_default = self._repo.get_default_for_user(user_id)
            if existing_default:
                self._repo.set_default(existing_default.id, user_id)

        profile = ProfileData(
            id=None,
            user_id=user_id,
            name=name,
            birth_data=birth_data,
            is_default=is_default,
        )

        saved = self._repo.save(profile)
        return self._to_summary(saved)

    def update_profile(
        self,
        profile_id: int,
        name: Optional[str] = None,
        birth_data: Optional[BirthData] = None,
    ) -> Optional[ProfileSummary]:
        """
        Update an existing profile.

        Args:
            profile_id: The profile's database ID
            name: New name (optional)
            birth_data: New birth data (optional)

        Returns:
            Updated ProfileSummary if found, None otherwise
        """
        existing = self._repo.get_by_id(profile_id)
        if not existing:
            return None

        updated = ProfileData(
            id=existing.id,
            user_id=existing.user_id,
            name=name if name is not None else existing.name,
            birth_data=birth_data if birth_data is not None else existing.birth_data,
            is_default=existing.is_default,
        )

        saved = self._repo.save(updated)
        return self._to_summary(saved)

    def delete_profile(self, profile_id: int) -> bool:
        """
        Delete a profile.

        Args:
            profile_id: The profile's database ID

        Returns:
            True if deleted, False if not found
        """
        return self._repo.delete(profile_id)

    def set_default_profile(self, profile_id: int, user_id: int) -> bool:
        """
        Set a profile as the default for a user.

        Args:
            profile_id: The profile to set as default
            user_id: The user's database ID

        Returns:
            True if successful, False if profile not found
        """
        return self._repo.set_default(profile_id, user_id)

    def get_profile_count(self, user_id: int) -> int:
        """
        Count profiles for a user.

        Args:
            user_id: The user's database ID

        Returns:
            Number of profiles
        """
        return self._repo.count_for_user(user_id)

    def _to_summary(self, profile: ProfileData) -> ProfileSummary:
        """
        Convert ProfileData to ProfileSummary with BaZi info.

        Args:
            profile: ProfileData from repository

        Returns:
            ProfileSummary with optional BaZi information
        """
        bazi_chinese = None
        day_master_wuxing = None
        is_strong = None

        # Calculate BaZi info if lunar adapter is available
        if self._lunar:
            bazi = self._lunar.get_bazi(profile.birth_data)
            bazi_chinese = bazi.chinese
            day_master_wuxing = bazi.day_master_wuxing.value

            # Calculate strength if bazi service is available
            if self._bazi_service:
                result = self._bazi_service.analyze(profile.birth_data)
                is_strong = result.is_day_master_strong

        return ProfileSummary(
            id=profile.id,
            name=profile.name,
            birth_data=profile.birth_data,
            is_default=profile.is_default,
            bazi_chinese=bazi_chinese,
            day_master_wuxing=day_master_wuxing,
            is_day_master_strong=is_strong,
        )
