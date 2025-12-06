"""
Calendar Views.

Views for the BaZi calendar showing day quality assessments
based on user's birth chart.

Uses domain services via the DI container for BaZi calculations.
"""
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from lunar_python import Solar

# Domain layer imports (DIP-compliant)
from bazi.domain.constants import (
    GAN_WUXING,
    GAN_XIANG_CHONG,
    GANZHI_WUXING,
    GUI_REN,
    TIAN_DE,
    WEN_CHANG,
    WUXING_RELATIONS,
    YUE_DE,
    ZHI_XIANG_CHONG,
)
from bazi.domain.models import BirthData, check_he
from bazi.infrastructure.di import get_container
from bazi.models import UserProfile


@login_required(login_url="/login/")
def calendar_view(request):
    """
    Calendar page view.

    Displays a month calendar with day quality indicators
    based on the user's selected BaZi profile.

    Requires user to have at least one profile.
    """
    profiles = UserProfile.objects.filter(user=request.user)

    if not profiles.exists():
        messages.warning(
            request, "您需要先创建八字资料才能使用日历功能。请先创建一个资料。"
        )
        return redirect("profiles")

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    return render(
        request,
        "calendar.html",
        {
            "year": current_year,
            "month": current_month,
            "years": range(current_year - 10, current_year + 11),
            "months": range(1, 13),
            "profiles": profiles,
        },
    )


def calendar_data(request):
    """
    API endpoint for calendar day quality data.

    Returns JSON with quality assessments for each day in
    the requested month, based on the user's BaZi profile.

    POST Parameters:
        year: Calendar year
        month: Calendar month (1-12)
        profile_id: Optional profile ID (uses default if not provided)

    Returns:
        JSON with days array, month/year scores, and pillar info

    TODO: This contains ~400 lines of business logic that should
    be migrated to CalendarService for better separation of concerns.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    # Parse year and month
    try:
        year = int(request.POST.get("year", datetime.datetime.now().year))
        month = int(request.POST.get("month", datetime.datetime.now().month))
    except (ValueError, TypeError):
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month

    profile_id = request.POST.get("profile_id")

    # Get user's profile
    profile = None
    if request.user.is_authenticated:
        if profile_id:
            try:
                profile = UserProfile.objects.get(id=profile_id, user=request.user)
            except UserProfile.DoesNotExist:
                pass

        # Fall back to default profile
        if not profile:
            try:
                profile = UserProfile.objects.get(user=request.user, is_default=True)
            except UserProfile.DoesNotExist:
                pass

    if not profile:
        return JsonResponse(
            {
                "error": "no_profile",
                "message": "请先选择一个八字资料才能查看择日信息",
            },
            status=400,
        )

    # Calculate days in month
    first_day = datetime.datetime(year, month, 1)
    if month == 12:
        last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
    num_days = last_day.day

    # Get profile's BaZi
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

    # Get profile's pillars
    profile_day_gan = profile_bazi.getDayGan()
    profile_day_zhi = profile_bazi.getDayZhi()
    profile_year_gan = profile_bazi.getYearGan()
    profile_year_zhi = profile_bazi.getYearZhi()
    profile_month_gan = profile_bazi.getMonthGan()
    profile_month_zhi = profile_bazi.getMonthZhi()
    profile_time_gan = profile_bazi.getTimeGan()
    profile_time_zhi = profile_bazi.getTimeZhi()

    # Collect all profile gan/zhi for conflict checking
    profile_all_gan = [
        profile_year_gan,
        profile_month_gan,
        profile_day_gan,
        profile_time_gan,
    ]
    profile_all_zhi = [
        profile_year_zhi,
        profile_month_zhi,
        profile_day_zhi,
        profile_time_zhi,
    ]

    # Get profile's day master wuxing
    if profile.day_master_wuxing:
        profile_day_wuxing = profile.day_master_wuxing
    else:
        profile_day_wuxing = GAN_WUXING.get(profile_day_gan)

    # Get favorable/unfavorable elements
    if (
        profile.is_day_master_strong is not None
        and profile.favorable_wuxing
        and profile.unfavorable_wuxing
    ):
        is_strong = profile.is_day_master_strong
        good_wuxing_list = profile.favorable_wuxing.split(",")
        bad_wuxing_list = profile.unfavorable_wuxing.split(",")
    else:
        # Calculate if not stored using domain services
        container = get_container()
        birth_data = BirthData(
            year=profile.birth_year,
            month=profile.birth_month,
            day=profile.birth_day,
            hour=profile.birth_hour,
            minute=profile.birth_minute or 0,
            is_male=getattr(profile, 'is_male', True),
        )
        summary = container.bazi_service.get_quick_summary(birth_data)
        is_strong = summary["is_strong"]
        good_wuxing_list = summary["favorable_wuxing"]
        bad_wuxing_list = summary["unfavorable_wuxing"]

        # Save for future use
        profile.day_master_wuxing = summary["day_master_wuxing"]
        profile.is_day_master_strong = is_strong
        profile.favorable_wuxing = ",".join(good_wuxing_list)
        profile.unfavorable_wuxing = ",".join(bad_wuxing_list)
        profile.save()

    # Get year and month pillars
    month_solar = Solar.fromYmdHms(year, month, 1, 12, 0, 0)
    month_lunar = month_solar.getLunar()
    month_bazi = month_lunar.getEightChar()
    month_gan = month_bazi.getMonthGan()
    month_zhi = month_bazi.getMonthZhi()
    year_gan = month_bazi.getYearGan()
    year_zhi = month_bazi.getYearZhi()

    # Calculate year-level score adjustment
    year_score_adjustment = _calculate_year_score(
        year_gan,
        year_zhi,
        profile_all_gan,
        profile_all_zhi,
        good_wuxing_list,
    )

    # Calculate month-level score adjustment
    month_score_adjustment = _calculate_month_score(
        month_gan,
        month_zhi,
        year_gan,
        year_zhi,
        profile_all_gan,
        profile_all_zhi,
        good_wuxing_list,
    )

    # Calculate quality for each day
    calendar_days = []
    for day in range(1, num_days + 1):
        day_data = _calculate_day_quality(
            year,
            month,
            day,
            year_gan,
            year_zhi,
            month_gan,
            month_zhi,
            profile_day_gan,
            profile_day_zhi,
            profile_month_zhi,
            profile_all_gan,
            profile_all_zhi,
            profile_bazi,
            good_wuxing_list,
            bad_wuxing_list,
            year_score_adjustment,
            month_score_adjustment,
        )
        calendar_days.append(day_data)

    return JsonResponse(
        {
            "days": calendar_days,
            "month_score": month_score_adjustment,
            "year_score": year_score_adjustment,
            "year": year,
            "month": month,
            "year_gan": year_gan,
            "year_zhi": year_zhi,
            "month_gan": month_gan,
            "month_zhi": month_zhi,
        }
    )


def _calculate_year_score(
    year_gan,
    year_zhi,
    profile_all_gan,
    profile_all_zhi,
    good_wuxing_list,
):
    """Calculate year-level quality adjustment score."""
    score = 0

    # Check gan conflicts
    for profile_gan in profile_all_gan:
        if (year_gan, profile_gan) in GAN_XIANG_CHONG or (
            profile_gan,
            year_gan,
        ) in GAN_XIANG_CHONG:
            score -= 0.1
            break

    # Check zhi conflicts
    for profile_zhi in profile_all_zhi:
        if (year_zhi, profile_zhi) in ZHI_XIANG_CHONG or (
            profile_zhi,
            year_zhi,
        ) in ZHI_XIANG_CHONG:
            score -= 0.1
            break

    # Check if year elements are favorable
    year_GAN_WUXING = GAN_WUXING.get(year_gan)
    year_zhi_wuxing = GANZHI_WUXING.get(year_zhi)
    if year_GAN_WUXING in good_wuxing_list or year_zhi_wuxing in good_wuxing_list:
        score += 0.1

    return score


def _calculate_month_score(
    month_gan,
    month_zhi,
    year_gan,
    year_zhi,
    profile_all_gan,
    profile_all_zhi,
    good_wuxing_list,
):
    """Calculate month-level quality adjustment score."""
    score = 0

    # Check month gan conflicts with year gan
    if (month_gan, year_gan) in GAN_XIANG_CHONG or (
        year_gan,
        month_gan,
    ) in GAN_XIANG_CHONG:
        score -= 0.2

    # Check month gan conflicts with profile
    for profile_gan in profile_all_gan:
        if (month_gan, profile_gan) in GAN_XIANG_CHONG or (
            profile_gan,
            month_gan,
        ) in GAN_XIANG_CHONG:
            score -= 0.2
            break

    # Check month zhi conflicts with year zhi
    if (month_zhi, year_zhi) in ZHI_XIANG_CHONG or (
        year_zhi,
        month_zhi,
    ) in ZHI_XIANG_CHONG:
        score -= 0.2

    # Check month zhi conflicts with profile
    for profile_zhi in profile_all_zhi:
        if (month_zhi, profile_zhi) in ZHI_XIANG_CHONG or (
            profile_zhi,
            month_zhi,
        ) in ZHI_XIANG_CHONG:
            score -= 0.2
            break

    # Check if month elements are favorable
    month_GAN_WUXING = GAN_WUXING.get(month_gan)
    month_zhi_wuxing = GANZHI_WUXING.get(month_zhi)
    if month_GAN_WUXING in good_wuxing_list or month_zhi_wuxing in good_wuxing_list:
        score += 0.1

    return score


def _calculate_day_quality(
    year,
    month,
    day,
    year_gan,
    year_zhi,
    month_gan,
    month_zhi,
    profile_day_gan,
    profile_day_zhi,
    profile_month_zhi,
    profile_all_gan,
    profile_all_zhi,
    profile_bazi,
    good_wuxing_list,
    bad_wuxing_list,
    year_score_adjustment,
    month_score_adjustment,
):
    """
    Calculate quality assessment for a single day.

    Returns dict with day info, quality, score, and reasons.
    """
    day_reasons = []
    day_score = year_score_adjustment + month_score_adjustment
    day_overall_quality = "neutral"

    # Add year/month adjustment explanations
    if year_score_adjustment != 0:
        reason_type = "good" if year_score_adjustment > 0 else "bad"
        day_reasons.append(
            {"type": reason_type, "text": f"年度因素: {year_score_adjustment:+.1f}分"}
        )

    if month_score_adjustment != 0:
        reason_type = "good" if month_score_adjustment > 0 else "bad"
        day_reasons.append(
            {"type": reason_type, "text": f"月度因素: {month_score_adjustment:+.1f}分"}
        )

    # Get day's BaZi
    date_solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
    date_lunar = date_solar.getLunar()
    date_bazi = date_lunar.getEightChar()

    # Get lunar date for display
    lunar_month = date_lunar.getMonthInChinese()
    lunar_day = date_lunar.getDayInChinese()
    lunar_date = f"{lunar_month}月{lunar_day}"

    day_gan = date_bazi.getDayGan()
    day_zhi = date_bazi.getDayZhi()

    # Check special inauspicious days using domain services
    container = get_container()
    day_score, day_overall_quality, day_reasons = _check_special_days(
        year,
        month,
        day,
        date_lunar,
        date_bazi,
        day_gan,
        day_zhi,
        day_score,
        day_overall_quality,
        day_reasons,
        container.calendar_service,
    )

    # Check conflicts with year/month
    day_score, day_overall_quality, day_reasons = _check_year_month_conflicts(
        day_gan,
        day_zhi,
        year_gan,
        year_zhi,
        month_gan,
        month_zhi,
        day_score,
        day_overall_quality,
        day_reasons,
    )

    # Check conflicts with profile
    day_score, day_overall_quality, day_reasons = _check_profile_conflicts(
        day_gan,
        day_zhi,
        profile_all_gan,
        profile_all_zhi,
        day_score,
        day_overall_quality,
        day_reasons,
    )

    # Check five element compatibility
    day_score, day_reasons = _check_wuxing_compatibility(
        day_gan,
        day_zhi,
        good_wuxing_list,
        bad_wuxing_list,
        day_score,
        day_reasons,
    )

    # Check harmonies with profile
    day_score, day_reasons = _check_harmonies(
        day_zhi,
        profile_bazi,
        day_score,
        day_reasons,
    )

    # Check auspicious stars using domain services
    day_score, day_reasons = _check_auspicious_stars(
        year,
        month,
        day,
        day_gan,
        day_zhi,
        profile_day_gan,
        profile_day_zhi,
        profile_month_zhi,
        day_score,
        day_reasons,
        container,
    )

    # Build hour quality (all neutral for now)
    day_quality = []
    for hour in [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
        day_quality.append({"hour": hour, "quality": "neutral"})

    # Default explanation for neutral days
    if day_overall_quality == "neutral" and not day_reasons:
        day_reasons.append({"type": "neutral", "text": "此日无特殊吉凶因素"})

    return {
        "day": day,
        "hours": day_quality,
        "overall_quality": day_overall_quality,
        "reasons": day_reasons,
        "lunar_date": lunar_date,
        "score": day_score,
    }


def _check_special_days(
    year,
    month,
    day,
    date_lunar,
    date_bazi,
    day_gan,
    day_zhi,
    day_score,
    day_quality,
    day_reasons,
    calendar_service,
):
    """Check for special inauspicious days using domain services."""
    # 四绝日 (Four Jue Days)
    if calendar_service.is_si_jue_ri(year, month, day):
        day_quality = "bad"
        day_score -= 2
        day_reasons.append(
            {"type": "bad", "text": "四绝日: 此日为节气前一天，为四绝日，不宜做重要事情"}
        )

    # 四离日 (Four Li Days)
    if calendar_service.is_si_li_ri(year, month, day):
        day_quality = "bad"
        day_score -= 2
        day_reasons.append(
            {"type": "bad", "text": "四离日: 此日为分至前一天，为四离日，不宜做重要事情"}
        )

    # 杨公十三忌 (Yang Gong Thirteen Taboos)
    lunar_month = date_lunar.getMonth()
    lunar_day = date_lunar.getDay()
    if calendar_service.is_yang_gong_taboo(lunar_month, lunar_day):
        day_score -= 0.5
        day_reasons.append(
            {"type": "bad", "text": "杨公十三忌: 此日为杨公忌日，不宜做重要事情"}
        )

    # 破日 (Breaking Day)
    if date_lunar.getZhiXing() == "破":
        day_quality = "bad"
        day_score -= 2
        day_reasons.append({"type": "bad", "text": "破日: 此日为破日，不宜做重要事情"})

    return day_score, day_quality, day_reasons


def _check_year_month_conflicts(
    day_gan,
    day_zhi,
    year_gan,
    year_zhi,
    month_gan,
    month_zhi,
    day_score,
    day_quality,
    day_reasons,
):
    """Check conflicts between day pillar and year/month."""
    # Day gan conflicts
    if (day_gan, year_gan) in GAN_XIANG_CHONG:
        day_quality = "bad"
        day_score -= 2
        day_reasons.append(
            {"type": "bad", "text": f"日干 {day_gan} 与年干 {year_gan} 相冲"}
        )
    if (day_gan, month_gan) in GAN_XIANG_CHONG:
        day_quality = "bad"
        day_score -= 2
        day_reasons.append(
            {"type": "bad", "text": f"日干 {day_gan} 与月干 {month_gan} 相冲"}
        )

    # Day zhi conflicts
    if (day_zhi, year_zhi) in ZHI_XIANG_CHONG:
        day_quality = "bad"
        day_score -= 2
        day_reasons.append(
            {"type": "bad", "text": f"日支 {day_zhi} 与年支 {year_zhi} 相冲"}
        )
    if (day_zhi, month_zhi) in ZHI_XIANG_CHONG:
        day_quality = "bad"
        day_score -= 2
        day_reasons.append(
            {"type": "bad", "text": f"日支 {day_zhi} 与月支 {month_zhi} 相冲"}
        )

    return day_score, day_quality, day_reasons


def _check_profile_conflicts(
    day_gan,
    day_zhi,
    profile_all_gan,
    profile_all_zhi,
    day_score,
    day_quality,
    day_reasons,
):
    """Check conflicts between day pillar and profile."""
    for profile_gan in profile_all_gan:
        if (day_gan, profile_gan) in GAN_XIANG_CHONG:
            day_quality = "bad"
            day_score -= 2
            day_reasons.append(
                {"type": "bad", "text": f"日干 {day_gan} 与八字天干 {profile_gan} 相冲"}
            )

    for profile_zhi in profile_all_zhi:
        if (day_zhi, profile_zhi) in ZHI_XIANG_CHONG:
            day_quality = "bad"
            day_score -= 2
            day_reasons.append(
                {"type": "bad", "text": f"日支 {day_zhi} 与八字地支 {profile_zhi} 相冲"}
            )

    return day_score, day_quality, day_reasons


def _check_wuxing_compatibility(
    day_gan,
    day_zhi,
    good_wuxing_list,
    bad_wuxing_list,
    day_score,
    day_reasons,
):
    """Check five element compatibility."""
    day_GAN_WUXING = GAN_WUXING.get(day_gan)
    day_zhi_wuxing = GANZHI_WUXING.get(day_zhi)

    # Bad elements
    if day_GAN_WUXING in bad_wuxing_list:
        day_score -= 0.5
        day_reasons.append(
            {"type": "bad", "text": f"日干五行 {day_GAN_WUXING} 对命主不利"}
        )
    if day_zhi_wuxing in bad_wuxing_list:
        day_score -= 0.5
        day_reasons.append(
            {"type": "bad", "text": f"日支五行 {day_zhi_wuxing} 对命主不利"}
        )

    # Good elements
    if day_GAN_WUXING in good_wuxing_list:
        day_score += 0.25
        day_reasons.append(
            {"type": "good", "text": f"日干五行 {day_GAN_WUXING} 对命主有利"}
        )
    if day_zhi_wuxing in good_wuxing_list:
        day_score += 0.25
        day_reasons.append(
            {"type": "good", "text": f"日支五行 {day_zhi_wuxing} 对命主有利"}
        )

    return day_score, day_reasons


def _check_harmonies(day_zhi, profile_bazi, day_score, day_reasons):
    """Check for harmonies (合) between day and profile."""
    for gan_zhi in profile_bazi.toString().split(" "):
        if check_he(gan_zhi, day_zhi):
            day_score += 1
            day_reasons.append(
                {"type": "good", "text": f"日支 {day_zhi} 与八字 {gan_zhi} 相合"}
            )
            break
    return day_score, day_reasons


def _check_auspicious_stars(
    year,
    month,
    day,
    day_gan,
    day_zhi,
    profile_day_gan,
    profile_day_zhi,
    profile_month_zhi,
    day_score,
    day_reasons,
    container,
):
    """Check for auspicious stars (贵人, 天德, 月德, etc.) using domain services."""
    # Get domain BaZi for this date and calculate ShenSha
    from datetime import datetime as dt
    domain_bazi = container.lunar_adapter.get_bazi_from_datetime(
        dt(year, month, day, 12, 0)
    )
    shensha_analysis = container.shensha_calculator.calculate_for_bazi(domain_bazi)

    # Check for auspicious stars from domain analysis
    shensha_types = {ss.type.name for ss in shensha_analysis.shensha_list}

    if "TIAN_DE" in shensha_types:
        day_score += 1
        day_reasons.append({"type": "good", "text": "此日有天德星"})
    if "YUE_DE" in shensha_types:
        day_score += 1
        day_reasons.append({"type": "good", "text": "此日有月德星"})
    if "WEN_CHANG" in shensha_types:
        day_score += 1
        day_reasons.append({"type": "good", "text": "此日有文昌星"})
    if "TIAN_YI_GUI_REN" in shensha_types:
        day_score += 1
        day_reasons.append({"type": "good", "text": "此日有天乙贵人"})

    # Profile interaction stars
    if (profile_day_gan, day_zhi) in GUI_REN:
        day_score += 1
        day_reasons.append(
            {
                "type": "good",
                "text": f"命主日干 {profile_day_gan} 与当日日支 {day_zhi} 贵人相见",
            }
        )
    if (day_gan, profile_day_zhi) in WEN_CHANG:
        day_score += 1
        day_reasons.append(
            {
                "type": "good",
                "text": f"命主日干 {day_gan} 与当日日支 {profile_day_zhi} 文昌相见",
            }
        )
    if (profile_month_zhi, day_gan) in TIAN_DE:
        day_score += 1
        day_reasons.append(
            {
                "type": "good",
                "text": f"命主月支 {profile_month_zhi} 与当日日干 {day_gan} 天德相见",
            }
        )
    if (profile_month_zhi, day_gan) in YUE_DE:
        day_score += 1
        day_reasons.append(
            {
                "type": "good",
                "text": f"命主月支 {profile_month_zhi} 与当日日干 {day_gan} 月德相见",
            }
        )

    return day_score, day_reasons
