"""
Profile Management Views.

Handles CRUD operations for user BaZi profiles using class-based views.
Uses ProfileRepository from the DI container (DIP-compliant).
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View

from bazi.domain.models import BirthData
from bazi.domain.ports import ProfileData
from bazi.presentation.forms import UserProfileForm
from bazi.presentation.views.base import BaseProfileView, BaziLoginRequiredMixin, ContainerMixin


class ProfileListView(ContainerMixin, ListView):
    """
    List all profiles for the current user.

    Displays a list of BaZi profiles with options to
    add, edit, delete, and set default profile.

    For anonymous users, profiles are managed client-side via Alpine.js store.
    For authenticated users, server profiles are loaded via Alpine.js API calls.
    """
    template_name = 'profiles.html'
    context_object_name = 'profiles'

    def get_queryset(self):
        """
        Return empty queryset - profiles are loaded client-side via Alpine.js.

        This allows the same template to work for both anonymous (IndexedDB)
        and authenticated (server API) users.
        """
        return []


class ProfileCreateView(BaziLoginRequiredMixin, ContainerMixin, View):
    """
    Create a new BaZi profile.

    After creation, optionally redirects to BaZi analysis page.
    """
    template_name = 'profile_form.html'

    def get(self, request):
        """Display empty form."""
        form = UserProfileForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle form submission."""
        form = UserProfileForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        cleaned = form.cleaned_data

        # Create BirthData from form
        birth_data = BirthData(
            year=cleaned['birth_year'],
            month=cleaned['birth_month'],
            day=cleaned['birth_day'],
            hour=cleaned['birth_hour'],
            minute=cleaned.get('birth_minute') or 0,
            is_male=cleaned.get('is_male', True),
        )

        # Check if this is the first profile (set as default)
        is_first = self.profile_repo.count_for_user(request.user.id) == 0

        # Create ProfileData
        profile_data = ProfileData(
            id=None,
            user_id=request.user.id,
            name=cleaned['name'],
            birth_data=birth_data,
            is_default=is_first,
        )

        # Save via repository
        saved_profile = self.profile_repo.save(profile_data)

        messages.success(request, "个人资料添加成功!")

        # Redirect to BaZi page if requested
        if 'redirect_to_bazi' in request.POST:
            return redirect(f"/bazi?profile_id={saved_profile.id}")

        return redirect('profiles')


class ProfileUpdateView(BaseProfileView):
    """
    Edit an existing BaZi profile.

    Recalculates day master strength and favorable elements
    if birth data is changed.
    """
    template_name = 'profile_form.html'

    def get(self, request, profile_id):
        """Display form with existing data."""
        profile = self.get_profile_or_404(profile_id)

        initial_data = {
            'name': profile.name,
            'birth_year': profile.birth_data.year,
            'birth_month': profile.birth_data.month,
            'birth_day': profile.birth_data.day,
            'birth_hour': profile.birth_data.hour,
            'birth_minute': profile.birth_data.minute,
            'is_male': profile.birth_data.is_male,
        }
        form = UserProfileForm(initial=initial_data)

        return render(request, self.template_name, {'form': form})

    def post(self, request, profile_id):
        """Handle form submission."""
        profile = self.get_profile_or_404(profile_id)
        form = UserProfileForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        cleaned = form.cleaned_data

        # Create updated BirthData
        birth_data = BirthData(
            year=cleaned['birth_year'],
            month=cleaned['birth_month'],
            day=cleaned['birth_day'],
            hour=cleaned['birth_hour'],
            minute=cleaned.get('birth_minute') or 0,
            is_male=cleaned.get('is_male', True),
        )

        # Create updated ProfileData (preserve ID and is_default)
        updated_profile = ProfileData(
            id=profile_id,
            user_id=request.user.id,
            name=cleaned['name'],
            birth_data=birth_data,
            is_default=profile.is_default,
        )

        # Save via repository
        self.profile_repo.save(updated_profile)

        messages.success(request, "个人资料更新成功!")
        return redirect('profiles')


class ProfileDeleteView(BaseProfileView):
    """
    Delete a BaZi profile.

    Permanently removes the profile from the database.
    """

    def get(self, request, profile_id):
        """Handle GET request to delete profile."""
        profile = self.get_profile_or_404(profile_id)
        self.profile_repo.delete(profile.id)
        messages.success(request, "个人资料已删除。")
        return redirect('profiles')

    def post(self, request, profile_id):
        """Handle POST request to delete profile."""
        return self.get(request, profile_id)


class SetDefaultProfileView(BaseProfileView):
    """
    Set a profile as the default for the user.

    Only one profile can be default at a time.
    """

    def get(self, request, profile_id):
        """Handle GET request to set default profile."""
        profile = self.get_profile_or_404(profile_id)

        # Set as default via repository
        self.profile_repo.set_default(profile_id, request.user.id)

        messages.success(request, f"已将 {profile.name} 设置为默认资料")
        return redirect('profiles')


# =============================================================================
# URL-compatible function aliases (for backward compatibility)
# =============================================================================

profile_list = ProfileListView.as_view()
add_profile = ProfileCreateView.as_view()
edit_profile = ProfileUpdateView.as_view()
delete_profile = ProfileDeleteView.as_view()
set_default_profile = SetDefaultProfileView.as_view()
