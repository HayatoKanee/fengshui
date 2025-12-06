"""
BaZi Analysis Views.

Main views for BaZi (Four Pillars) analysis and display.
Uses DI container for all infrastructure access (DIP-compliant).
"""
import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from bazi.infrastructure.di import get_container
from bazi.presentation.presenters import BaziPresenter, get_shensha
from bazi.presentation.forms import BirthTimeForm


def _build_bazi_context(
    form,
    bazi,
    lunar,
    is_male,
    selected_year,
    profiles=None,
):
    """
    Build the template context for BaZi analysis.

    This function prepares all the data needed by the bazi.html template
    using the BaziPresenter for template-specific data formatting
    and domain services for complex analysis.
    """
    container = get_container()
    presenter = BaziPresenter()

    # Use presenter for all template-specific data formatting
    view_data = presenter.present(bazi, lunar)

    # Use domain services for complex analysis
    liunian_service = container.liunian_service
    partner_analyst = liunian_service.analyse_partner(
        view_data.hidden_gans, view_data.shishen
    )
    personality = liunian_service.analyse_personality(bazi.getMonthZhi())
    liunian_analysis = liunian_service.analyse_liunian(
        bazi, view_data.shishen, selected_year, view_data.is_strong, is_male
    )
    shensha_list = get_shensha(bazi)

    current_year = datetime.datetime.now().year
    years = range(current_year - 20, current_year + 50)

    return {
        "form": form,
        "bazi": bazi,
        "values": view_data.values,
        "hidden_gans": view_data.hidden_gans,
        "main_wuxing": view_data.main_wuxing,
        "shengxiao": view_data.shengxiao,
        "wang_xiang": view_data.wang_xiang,
        "wang_xiang_values": view_data.wang_xiang_values,
        "wuxing": view_data.wuxing,
        "yinyang": view_data.yinyang,
        "shishen": view_data.shishen,
        "gan_liang_values": view_data.gan_liang_values,
        "wuxing_value": view_data.wuxing_value,
        "sheng_hao": view_data.sheng_hao,
        "sheng_hao_percentage": view_data.sheng_hao_percentage,
        "current_year": int(selected_year),
        "is_male": is_male,
        "partner_analyst": partner_analyst,
        "liunian_analysis": liunian_analysis,
        "years": years,
        "personality": personality,
        "shensha_list": shensha_list,
        "profiles": profiles,
    }


def _get_user_profiles(request):
    """Get profiles for authenticated user via ProfileRepository."""
    if not request.user.is_authenticated:
        return None
    container = get_container()
    return container.profile_repo.get_by_user(request.user.id)


def bazi_view(request):
    """
    Main BaZi analysis view.

    Handles both:
    - GET: Display form (optionally pre-filled from profile)
    - POST: Calculate and display BaZi analysis

    Query Parameters:
        profile_id: Optional profile ID to load birth data from
        year: Optional year for LiuNian (yearly fortune) analysis
    """
    container = get_container()
    current_year = datetime.datetime.now().year
    years = range(current_year - 20, current_year + 50)

    # Check if viewing a saved profile
    profile = None
    profile_id = request.GET.get("profile_id")

    if profile_id and request.user.is_authenticated:
        # Use ProfileRepository via container (DIP-compliant)
        profile_data = container.profile_repo.get_by_id(int(profile_id))

        if profile_data and profile_data.user_id == request.user.id:
            # Calculate BaZi for the profile using LunarPort (DIP-compliant)
            is_male = profile_data.birth_data.is_male
            selected_year = request.GET.get("year", str(current_year))

            lunar, bazi = container.lunar_adapter.get_raw_lunar_and_bazi(
                profile_data.birth_data.year,
                profile_data.birth_data.month,
                profile_data.birth_data.day,
                profile_data.birth_data.hour,
                profile_data.birth_data.minute,
            )

            # Pre-fill form with profile data
            initial_data = {
                "year": profile_data.birth_data.year,
                "month": profile_data.birth_data.month,
                "day": profile_data.birth_data.day,
                "hour": profile_data.birth_data.hour,
                "minute": profile_data.birth_data.minute,
                "gender": "male" if is_male else "female",
            }
            form = BirthTimeForm(initial=initial_data)

            # Get user's other profiles for the dropdown
            profiles = _get_user_profiles(request)

            context = _build_bazi_context(
                form=form,
                bazi=bazi,
                lunar=lunar,
                is_male=is_male,
                selected_year=selected_year,
                profiles=profiles,
            )
            return render(request, "bazi.html", context)

    if request.method == "POST":
        form = BirthTimeForm(request.POST)
        if form.is_valid():
            # Extract form data
            year = form.cleaned_data['year']
            month = form.cleaned_data['month']
            day = form.cleaned_data['day']
            hour = form.cleaned_data['hour']
            minute = form.cleaned_data['minute']

            selected_year = request.POST.get("liunian", str(current_year))
            is_male = request.POST.get("gender") == "male"

            # Use LunarPort via container (DIP-compliant)
            lunar, bazi = container.lunar_adapter.get_raw_lunar_and_bazi(
                year, month, day, hour, minute
            )

            profiles = _get_user_profiles(request)

            context = _build_bazi_context(
                form=form,
                bazi=bazi,
                lunar=lunar,
                is_male=is_male,
                selected_year=selected_year,
                profiles=profiles,
            )
            return render(request, "bazi.html", context)
    else:
        # Pre-fill form if profile is available
        initial_data = {}
        if profile:
            initial_data = {
                "year": profile.birth_year,
                "month": profile.birth_month,
                "day": profile.birth_day,
                "hour": profile.birth_hour,
                "minute": profile.birth_minute,
                "gender": "male" if profile.is_male else "female",
            }
        form = BirthTimeForm(initial=initial_data)

    profiles = _get_user_profiles(request)

    return render(
        request,
        "bazi.html",
        {
            "form": form,
            "current_year": current_year,
            "years": years,
            "profiles": profiles,
        },
    )


def get_bazi_detail(request):
    """
    HTMX endpoint for BaZi detail partial.

    Returns an HTML fragment with detailed BaZi analysis
    for embedding via HTMX requests.

    POST Parameters:
        year, month, day, hour: Birth date/time
        profile_id: Optional profile ID for context
    """
    if request.method != "POST":
        return HttpResponse(status=404)

    container = get_container()

    year = request.POST.get("year")
    month = request.POST.get("month")
    day = request.POST.get("day")
    hour = request.POST.get("hour")
    profile_id = request.POST.get("profile_id")

    # Get profile if provided (via ProfileRepository - DIP-compliant)
    profile = None
    if profile_id and request.user.is_authenticated:
        profile_data = container.profile_repo.get_by_id(int(profile_id))
        if profile_data and profile_data.user_id == request.user.id:
            profile = profile_data

    # Calculate BaZi using LunarPort (DIP-compliant)
    lunar, bazi = container.lunar_adapter.get_raw_lunar_and_bazi(
        int(year), int(month), int(day), int(hour), 0
    )

    # Use presenter for template-specific data formatting
    presenter = BaziPresenter()
    view_data = presenter.present(bazi, lunar)

    # Calculate shensha
    shensha_list = get_shensha(bazi)

    # Extract individual shensha from list for template compatibility
    gui_ren = None
    tian_de = None
    yue_de = None
    wen_chang = None
    lu_shen = None
    for shensha_name, positions in shensha_list:
        if '贵人' in shensha_name:
            gui_ren = positions
        elif shensha_name == '天德贵人':
            tian_de = positions
        elif shensha_name == '月德贵人':
            yue_de = positions
        elif shensha_name == '文昌':
            wen_chang = positions
        elif shensha_name == '禄神':
            lu_shen = positions

    context = {
        "bazi": bazi,
        "wuxing": view_data.wuxing,
        "wuxing_value": view_data.wuxing_value,
        "sheng_hao": view_data.sheng_hao,
        "sheng_hao_percentage": view_data.sheng_hao_percentage,
        "gui_ren": gui_ren,
        "tian_de": tian_de,
        "yue_de": yue_de,
        "wen_chang": wen_chang,
        "lu_shen": lu_shen,
        "shensha_list": shensha_list,
    }

    html = render_to_string("partials/bazi_detail.html", context)
    return HttpResponse(html)
