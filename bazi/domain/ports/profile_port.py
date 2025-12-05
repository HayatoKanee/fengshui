"""
Profile Repository Port - Interface for user profile persistence.

This port abstracts the Django ORM for profile storage,
allowing the domain to work with any persistence mechanism.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import List, Optional, Protocol

from ..models import BirthData


class ProfileData:
    """
    Profile data transfer object.

    This is a plain Python class (not Django model) that represents
    profile data as it flows through the domain layer.
    """

    def __init__(
        self,
        id: Optional[int],
        user_id: int,
        name: str,
        birth_data: BirthData,
        is_default: bool = False,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.birth_data = birth_data
        self.is_default = is_default

    def __repr__(self) -> str:
        return f"ProfileData(id={self.id}, name={self.name!r})"


class ProfileRepository(Protocol):
    """
    Protocol for profile persistence operations.

    This interface abstracts the Django ORM UserProfile model,
    allowing the domain to work without Django dependencies.
    """

    @abstractmethod
    def get_by_id(self, profile_id: int) -> Optional[ProfileData]:
        """
        Get a profile by its ID.

        Args:
            profile_id: The profile's database ID

        Returns:
            ProfileData if found, None otherwise
        """
        ...

    @abstractmethod
    def get_by_user(self, user_id: int) -> List[ProfileData]:
        """
        Get all profiles for a user.

        Args:
            user_id: The user's database ID

        Returns:
            List of ProfileData for the user
        """
        ...

    @abstractmethod
    def get_default_for_user(self, user_id: int) -> Optional[ProfileData]:
        """
        Get the default profile for a user.

        Args:
            user_id: The user's database ID

        Returns:
            Default ProfileData if exists, None otherwise
        """
        ...

    @abstractmethod
    def save(self, profile: ProfileData) -> ProfileData:
        """
        Save a profile (create or update).

        Args:
            profile: ProfileData to save

        Returns:
            Saved ProfileData with ID populated
        """
        ...

    @abstractmethod
    def delete(self, profile_id: int) -> bool:
        """
        Delete a profile by ID.

        Args:
            profile_id: The profile's database ID

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    def set_default(self, profile_id: int, user_id: int) -> bool:
        """
        Set a profile as the default for a user.

        This should unset any previous default.

        Args:
            profile_id: The profile to set as default
            user_id: The user's database ID

        Returns:
            True if successful, False if profile not found
        """
        ...

    @abstractmethod
    def count_for_user(self, user_id: int) -> int:
        """
        Count profiles for a user.

        Args:
            user_id: The user's database ID

        Returns:
            Number of profiles
        """
        ...
