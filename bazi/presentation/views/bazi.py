"""
BaZi Analysis Views.

Main views for BaZi (Four Pillars) analysis and display.
Uses BaziAnalysisService for business logic.
"""
import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from lunar_python import Solar

from bazi.constants import gan_wuxing, gan_yinyang
from bazi.domain.models import BirthData
from bazi.infrastructure.di import get_container
from bazi.models import UserProfile
from bazi.presentation.forms import BirthTimeForm

# Legacy helper imports for functionality not yet in domain services
# TODO: Move these to domain services
from bazi.helper import (
    accumulate_wuxing_values,
    analyse_liunian,
    analyse_partner,
    analyse_personality,
    calculate_day_guiren,
    calculate_gan_liang_value,
    calculate_lu_shen,
    calculate_shenghao,
    calculate_shenghao_percentage,
    calculate_shishen_for_bazi,
    calculate_tian_de,
    calculate_values,
    calculate_values_for_bazi,
    calculate_wang_xiang_values,
    calculate_wen_chang,
    calculate_yue_de,
    extract_form_data,
    get_hidden_gans,
    get_relations,
    get_shensha,
    get_wang_xiang,
)


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

    This adapter function prepares all the data needed by the
    bazi.html template. It uses a mix of domain services and
    legacy helper functions.

    TODO: Gradually migrate to using BaziAnalysisResult directly
    once templates are updated.
    """
    main_wuxing = bazi.getDayWuXing()[0]
    values = calculate_values(bazi)
    hidden_gans = get_hidden_gans(bazi)
    sheng_hao_relations = get_relations(main_wuxing)
    wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
    yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
    shishen = calculate_shishen_for_bazi(wuxing, yinyang)
    wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
    wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
    gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
    shengxiao = lunar.getYearShengXiaoExact()
    wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
    sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
    sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
    is_strong = sheng_hao[0] > sheng_hao[1]
    partner_analyst = analyse_partner(hidden_gans, shishen)
    personality = analyse_personality(bazi.getMonthZhi())
    liunian_analysis = analyse_liunian(bazi, shishen, selected_year, is_strong, is_male)
    shensha_list = get_shensha(bazi)

    current_year = datetime.datetime.now().year
    years = range(current_year - 20, current_year + 50)

    return {
        "form": form,
        "bazi": bazi,
        "values": values,
        "hidden_gans": hidden_gans,
        "main_wuxing": main_wuxing,
        "shengxiao": shengxiao,
        "wang_xiang": wang_xiang,
        "wang_xiang_values": wang_xiang_values,
        "wuxing": wuxing,
        "yinyang": yinyang,
        "shishen": shishen,
        "gan_liang_values": gan_liang_values,
        "wuxing_value": wuxing_value,
        "sheng_hao": sheng_hao,
        "sheng_hao_percentage": sheng_hao_percentage,
        "current_year": int(selected_year),
        "is_male": is_male,
        "partner_analyst": partner_analyst,
        "liunian_analysis": liunian_analysis,
        "years": years,
        "personality": personality,
        "shensha_list": shensha_list,
        "profiles": profiles,
    }


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
    current_year = datetime.datetime.now().year
    years = range(current_year - 20, current_year + 50)

    # Check if viewing a saved profile
    profile = None
    profile_id = request.GET.get("profile_id")

    if profile_id and request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(id=profile_id, user=request.user)

            # Calculate BaZi for the profile
            is_male = profile.is_male
            selected_year = request.GET.get("year", str(current_year))

            solar = Solar.fromYmdHms(
                profile.birth_year,
                profile.birth_month,
                profile.birth_day,
                profile.birth_hour,
                profile.birth_minute or 0,
                0,
            )
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()

            # Pre-fill form with profile data
            initial_data = {
                "year": profile.birth_year,
                "month": profile.birth_month,
                "day": profile.birth_day,
                "hour": profile.birth_hour,
                "minute": profile.birth_minute,
                "gender": "male" if profile.is_male else "female",
            }
            form = BirthTimeForm(initial=initial_data)

            # Get user's other profiles for the dropdown
            profiles = (
                UserProfile.objects.filter(user=request.user)
                if request.user.is_authenticated
                else None
            )

            context = _build_bazi_context(
                form=form,
                bazi=bazi,
                lunar=lunar,
                is_male=is_male,
                selected_year=selected_year,
                profiles=profiles,
            )
            return render(request, "bazi.html", context)

        except UserProfile.DoesNotExist:
            pass

    if request.method == "POST":
        form = BirthTimeForm(request.POST)
        if form.is_valid():
            data = extract_form_data(form)
            selected_year = request.POST.get("liunian", str(current_year))
            is_male = request.POST.get("gender") == "male"

            solar = Solar.fromYmdHms(
                data["year"],
                data["month"],
                data["day"],
                data["hour"],
                data["minute"],
                0,
            )
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()

            profiles = (
                UserProfile.objects.filter(user=request.user)
                if request.user.is_authenticated
                else None
            )

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

    profiles = (
        UserProfile.objects.filter(user=request.user)
        if request.user.is_authenticated
        else None
    )

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

    year = request.POST.get("year")
    month = request.POST.get("month")
    day = request.POST.get("day")
    hour = request.POST.get("hour")
    profile_id = request.POST.get("profile_id")

    # Get profile if provided
    profile = None
    if profile_id and request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(id=profile_id, user=request.user)
        except UserProfile.DoesNotExist:
            pass

    # Calculate BaZi
    solar = Solar.fromYmdHms(int(year), int(month), int(day), int(hour), 0, 0)
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()

    # Calculate analysis data
    main_wuxing = bazi.getDayWuXing()[0]
    values = calculate_values(bazi)
    hidden_gans = get_hidden_gans(bazi)
    wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
    yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
    wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
    wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
    gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
    wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
    sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
    sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])

    # Calculate shensha
    gui_ren = calculate_day_guiren(bazi)
    tian_de = calculate_tian_de(bazi)
    yue_de = calculate_yue_de(bazi)
    wen_chang = calculate_wen_chang(bazi)
    lu_shen = calculate_lu_shen(bazi)
    shensha_list = get_shensha(bazi)

    context = {
        "bazi": bazi,
        "wuxing": wuxing,
        "wuxing_value": wuxing_value,
        "sheng_hao": sheng_hao,
        "sheng_hao_percentage": sheng_hao_percentage,
        "gui_ren": gui_ren,
        "tian_de": tian_de,
        "yue_de": yue_de,
        "wen_chang": wen_chang,
        "lu_shen": lu_shen,
        "shensha_list": shensha_list,
    }

    html = render_to_string("partials/bazi_detail.html", context)
    return HttpResponse(html)
