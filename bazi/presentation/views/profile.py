"""
Profile Management Views.

Handles CRUD operations for user BaZi profiles.
Uses ProfileService and ProfileRepository from the DI container (DIP-compliant).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from bazi.domain.models import BirthData
from bazi.domain.ports import ProfileData
from bazi.infrastructure.di import get_container
from bazi.presentation.forms import UserProfileForm


@login_required(login_url="/login/")
def profile_list(request):
    """
    List all profiles for the current user.

    Displays a list of BaZi profiles with options to
    add, edit, delete, and set default profile.
    Uses ProfileRepository via DI container (DIP-compliant).
    """
    container = get_container()
    profiles = container.profile_repo.get_by_user(request.user.id)
    return render(request, "profiles.html", {"profiles": profiles})


@login_required(login_url="/login/")
def add_profile(request):
    """
    Create a new BaZi profile.

    After creation, calculates and stores the day master
    strength and favorable/unfavorable elements.
    Uses ProfileRepository via DI container (DIP-compliant).
    """
    container = get_container()

    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # Extract data from form
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
            is_first = container.profile_repo.count_for_user(request.user.id) == 0

            # Create ProfileData
            profile_data = ProfileData(
                id=None,
                user_id=request.user.id,
                name=cleaned['name'],
                birth_data=birth_data,
                is_default=is_first,
            )

            # Save via repository
            saved_profile = container.profile_repo.save(profile_data)

            messages.success(request, "个人资料添加成功!")

            # Redirect to BaZi page if requested
            if "redirect_to_bazi" in request.POST:
                return redirect(f"/bazi?profile_id={saved_profile.id}")
            return redirect("profiles")
    else:
        form = UserProfileForm()

    return render(request, "profile_form.html", {"form": form})


@login_required(login_url="/login/")
def edit_profile(request, profile_id):
    """
    Edit an existing BaZi profile.

    Recalculates day master strength and favorable elements
    if birth data is changed.
    Uses ProfileRepository via DI container (DIP-compliant).
    """
    container = get_container()

    # Get profile via repository
    profile_data = container.profile_repo.get_by_id(profile_id)
    if not profile_data or profile_data.user_id != request.user.id:
        raise Http404("Profile not found")

    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # Extract data from form
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
                is_default=profile_data.is_default,
            )

            # Save via repository
            container.profile_repo.save(updated_profile)

            messages.success(request, "个人资料更新成功!")
            return redirect("profiles")
    else:
        # Pre-populate form with existing data
        initial_data = {
            'name': profile_data.name,
            'birth_year': profile_data.birth_data.year,
            'birth_month': profile_data.birth_data.month,
            'birth_day': profile_data.birth_data.day,
            'birth_hour': profile_data.birth_data.hour,
            'birth_minute': profile_data.birth_data.minute,
            'is_male': profile_data.birth_data.is_male,
        }
        form = UserProfileForm(initial=initial_data)

    return render(request, "profile_form.html", {"form": form})


@login_required(login_url="/login/")
def delete_profile(request, profile_id):
    """
    Delete a BaZi profile.

    Permanently removes the profile from the database.
    Uses ProfileRepository via DI container (DIP-compliant).
    """
    container = get_container()

    # Verify profile belongs to user before deleting
    profile_data = container.profile_repo.get_by_id(profile_id)
    if not profile_data or profile_data.user_id != request.user.id:
        raise Http404("Profile not found")

    container.profile_repo.delete(profile_id)
    messages.success(request, "个人资料已删除。")
    return redirect("profiles")


@login_required(login_url="/login/")
def set_default_profile(request, profile_id):
    """
    Set a profile as the default for the user.

    Only one profile can be default at a time. Setting a new
    default automatically unsets the previous default.
    Uses ProfileRepository via DI container (DIP-compliant).
    """
    container = get_container()

    # Verify profile belongs to user
    profile_data = container.profile_repo.get_by_id(profile_id)
    if not profile_data or profile_data.user_id != request.user.id:
        raise Http404("Profile not found")

    # Set as default via repository (handles unsetting previous default)
    container.profile_repo.set_default(profile_id, request.user.id)

    messages.success(request, f"已将 {profile_data.name} 设置为默认资料")
    return redirect("profiles")
