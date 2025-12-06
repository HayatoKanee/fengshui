"""
Profile Management Views.

Handles CRUD operations for user BaZi profiles.
Uses BaziAnalysisService from the DI container for business logic.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bazi.domain.models import BirthData
from bazi.infrastructure.di import get_container
from bazi.models import UserProfile
from bazi.presentation.forms import UserProfileForm


def _calculate_and_save_profile_attributes(profile):
    """
    Calculate and save day master strength and favorable elements.

    Uses BaziAnalysisService to perform domain calculations.
    """
    try:
        container = get_container()

        # Create BirthData from profile
        birth_data = BirthData(
            year=profile.birth_year,
            month=profile.birth_month,
            day=profile.birth_day,
            hour=profile.birth_hour,
            minute=profile.birth_minute or 0,
            is_male=getattr(profile, 'is_male', True),
        )

        # Get quick summary from BaziAnalysisService
        summary = container.bazi_service.get_quick_summary(birth_data)

        # Store results in profile
        profile.day_master_wuxing = summary["day_master_wuxing"]
        profile.is_day_master_strong = summary["is_strong"]
        profile.favorable_wuxing = ",".join(summary["favorable_wuxing"])
        profile.unfavorable_wuxing = ",".join(summary["unfavorable_wuxing"])

    except Exception as e:
        # Log error but don't stop profile creation
        print(f"Error calculating profile attributes: {str(e)}")


@login_required(login_url="/login/")
def profile_list(request):
    """
    List all profiles for the current user.

    Displays a list of BaZi profiles with options to
    add, edit, delete, and set default profile.
    """
    profiles = UserProfile.objects.filter(user=request.user)
    return render(request, "profiles.html", {"profiles": profiles})


@login_required(login_url="/login/")
def add_profile(request):
    """
    Create a new BaZi profile.

    After creation, calculates and stores the day master
    strength and favorable/unfavorable elements.
    """
    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user

            # Set as default if first profile
            user_profiles_count = UserProfile.objects.filter(
                user=request.user
            ).count()
            if user_profiles_count == 0:
                profile.is_default = True

            # Calculate BaZi attributes before saving
            _calculate_and_save_profile_attributes(profile)
            profile.save()

            messages.success(request, "个人资料添加成功!")

            # Redirect to BaZi page if requested
            if "redirect_to_bazi" in request.POST:
                return redirect(f"/bazi?profile_id={profile.id}")
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
    """
    profile = get_object_or_404(
        UserProfile, id=profile_id, user=request.user
    )

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            updated_profile = form.save(commit=False)

            # Recalculate BaZi attributes
            _calculate_and_save_profile_attributes(updated_profile)
            updated_profile.save()

            messages.success(request, "个人资料更新成功!")
            return redirect("profiles")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "profile_form.html", {"form": form})


@login_required(login_url="/login/")
def delete_profile(request, profile_id):
    """
    Delete a BaZi profile.

    Permanently removes the profile from the database.
    """
    profile = get_object_or_404(
        UserProfile, id=profile_id, user=request.user
    )
    profile.delete()
    messages.success(request, "个人资料已删除。")
    return redirect("profiles")


@login_required(login_url="/login/")
def set_default_profile(request, profile_id):
    """
    Set a profile as the default for the user.

    Only one profile can be default at a time. Setting a new
    default automatically unsets the previous default.
    """
    profile = get_object_or_404(
        UserProfile, id=profile_id, user=request.user
    )

    # Clear default from all other profiles
    UserProfile.objects.filter(user=request.user).update(is_default=False)

    # Set this profile as default
    profile.is_default = True
    profile.save()

    messages.success(request, f"已将 {profile.name} 设置为默认资料")
    return redirect("profiles")
