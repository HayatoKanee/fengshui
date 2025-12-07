"""
Base View Classes and Mixins.

Provides common functionality for all BaZi views including
DI container access, authentication, and profile loading.
"""
from typing import Optional, List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import View

from bazi.domain.ports import ProfileData
from bazi.infrastructure.di import get_container


class ContainerMixin:
    """
    Mixin providing access to the DI container.

    Lazily loads the container on first access and caches it
    for the lifetime of the request.

    Provides minimal shortcuts for commonly used services.
    For other services, access via self.container.service_name.
    """
    _container = None

    @property
    def container(self):
        """Get the DI container (cached per request)."""
        if self._container is None:
            self._container = get_container()
        return self._container

    @property
    def profile_repo(self):
        """Shortcut to profile repository (most commonly used)."""
        return self.container.profile_repo


class ProfileMixin(ContainerMixin):
    """
    Mixin for views that work with user profiles.

    Provides methods for loading and validating profile ownership.
    """

    def get_user_profiles(self) -> List[ProfileData]:
        """Get all profiles for the current user."""
        if not self.request.user.is_authenticated:
            return []
        return self.profile_repo.get_by_user(self.request.user.id)

    def get_profile_or_404(self, profile_id: int) -> ProfileData:
        """
        Get a profile by ID, ensuring it belongs to current user.

        Raises Http404 if profile doesn't exist or belongs to another user.
        """
        profile = self.profile_repo.get_by_id(profile_id)
        if not profile or profile.user_id != self.request.user.id:
            raise Http404("Profile not found")
        return profile

    def get_default_profile(self) -> Optional[ProfileData]:
        """Get the default profile for current user, if any."""
        if not self.request.user.is_authenticated:
            return None
        return self.profile_repo.get_default_for_user(self.request.user.id)

    def get_profile_from_request(self) -> Optional[ProfileData]:
        """
        Get profile from request parameters.

        Checks GET['profile_id'] first, then POST['profile_id'],
        then falls back to default profile.
        """
        profile_id = (
            self.request.GET.get('profile_id') or
            self.request.POST.get('profile_id')
        )

        if profile_id and self.request.user.is_authenticated:
            profile = self.profile_repo.get_by_id(int(profile_id))
            if profile and profile.user_id == self.request.user.id:
                return profile

        return self.get_default_profile()


class BaziLoginRequiredMixin(LoginRequiredMixin):
    """
    LoginRequiredMixin with custom login URL.

    Standardizes the login redirect across all views.
    """
    login_url = '/login/'


class BaseProfileView(BaziLoginRequiredMixin, ProfileMixin, View):
    """
    Base class for views that require authentication and profile access.

    Combines login requirement with profile loading utilities.
    """
    pass
