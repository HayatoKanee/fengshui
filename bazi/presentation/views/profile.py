"""
Profile Management Views.

Handles CRUD operations for user BaZi profiles.
Uses ProfileService from the DI container for business logic.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bazi.domain.models import BirthData
from bazi.infrastructure.di import get_container
from bazi.models import UserProfile
from bazi.presentation.forms import UserProfileForm

# Legacy imports for calculate_and_save_profile_attributes
# TODO: Move this logic into ProfileService
from lunar_python import Solar
from bazi.constants import gan_wuxing, wuxing_relations
from bazi.helper import (
    accumulate_wuxing_values,
    calculate_gan_liang_value,
    calculate_shenghao,
    calculate_values,
    calculate_values_for_bazi,
    calculate_wang_xiang_values,
    get_hidden_gans,
    get_wang_xiang,
)


def _calculate_and_save_profile_attributes(profile):
    """
    Calculate and save day master strength and favorable elements.

    This is a temporary adapter function that bridges the old helper.py
    functions with the new profile model. In the future, this logic
    should be moved into ProfileService.

    TODO: Migrate to ProfileService after extending domain services.
    """
    try:
        # Create Solar and Lunar objects from profile birth information
        profile_solar = Solar.fromYmdHms(
            profile.birth_year,
            profile.birth_month,
            profile.birth_day,
            profile.birth_hour,
            profile.birth_minute or 0,
            0,
        )
        profile_lunar = profile_solar.getLunar()
        profile_bazi = profile_lunar.getEightChar()

        # Get day master wuxing
        profile_day_gan = profile_bazi.getDayGan()
        profile_day_wuxing = gan_wuxing.get(profile_day_gan)
        profile.day_master_wuxing = profile_day_wuxing

        # Calculate if day master is strong or weak
        values = calculate_values(profile_bazi)
        hidden_gans = get_hidden_gans(profile_bazi)
        wang_xiang = get_wang_xiang(profile_bazi.getMonthZhi(), profile_lunar)
        wang_xiang_values = calculate_wang_xiang_values(profile_bazi, wang_xiang)
        gan_liang_values = calculate_gan_liang_value(
            values, hidden_gans, wang_xiang_values
        )
        wuxing_value = accumulate_wuxing_values(
            calculate_values_for_bazi(profile_bazi, gan_wuxing), gan_liang_values
        )
        sheng_hao = calculate_shenghao(wuxing_value, profile_day_wuxing)
        is_strong = sheng_hao[0] > sheng_hao[1]
        profile.is_day_master_strong = is_strong

        # Determine favorable and unfavorable elements
        if is_strong:
            # Strong day master: elements that control it are good
            good_wuxing_list = wuxing_relations[profile_day_wuxing]["不利"]
            bad_wuxing_list = wuxing_relations[profile_day_wuxing]["有利"]
        else:
            # Weak day master: elements that generate it are good
            good_wuxing_list = wuxing_relations[profile_day_wuxing]["有利"]
            bad_wuxing_list = wuxing_relations[profile_day_wuxing]["不利"]

        # Store as comma-separated string
        profile.favorable_wuxing = ",".join(good_wuxing_list)
        profile.unfavorable_wuxing = ",".join(bad_wuxing_list)
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
