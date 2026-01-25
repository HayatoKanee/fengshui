"""
Calendar Views.

Views for the BaZi calendar showing day quality assessments
based on user's birth chart.

Uses DayQualityService from the application layer for all calculations.
"""
import datetime

from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from bazi.presentation.views.base import ContainerMixin


# =============================================================================
# Class-Based Views
# =============================================================================

class CalendarPageView(ContainerMixin, TemplateView):
    """
    Calendar page view.

    Displays a month calendar with day quality indicators
    based on the user's selected BaZi profile.

    Works for both anonymous (local profiles) and authenticated users.
    Profile selection handled by Alpine.js store.
    """
    template_name = 'calendar.html'

    def get_context_data(self, **kwargs):
        """Build context for calendar template."""
        context = super().get_context_data(**kwargs)

        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month

        context.update({
            "year": current_year,
            "month": current_month,
            "years": range(current_year - 10, current_year + 11),
            "months": range(1, 13),
        })
        return context


class CalendarDataView(ContainerMixin, View):
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
    """

    def post(self, request):
        """Handle POST request for calendar data."""
        # Parse year and month
        try:
            year = int(request.POST.get("year", datetime.datetime.now().year))
            month = int(request.POST.get("month", datetime.datetime.now().month))
        except (ValueError, TypeError):
            year = datetime.datetime.now().year
            month = datetime.datetime.now().month

        profile_id = request.POST.get("profile_id")

        # Get user's profile
        profile = self._get_profile(request, profile_id)
        if profile is None:
            return JsonResponse(
                {
                    "error": "no_profile",
                    "message": "请先选择一个八字资料才能查看择日信息",
                },
                status=400,
            )

        # Use application service for all calculations
        day_quality_service = self.container.day_quality_service
        result = day_quality_service.calculate_month(year, month, profile)

        # Convert result to JSON-serializable format
        calendar_days = []
        for day_result in result.days:
            # Serialize hour quality results
            hours_data = []
            for hour_result in day_result.hours:
                hours_data.append({
                    "hour": hour_result.hour,
                    "hour_name": hour_result.hour_name,
                    "hour_display": hour_result.hour_display,
                    "quality": hour_result.quality,
                    "score": hour_result.score,
                    "reasons": list(hour_result.reasons),
                    "full_bazi": hour_result.full_bazi,
                    "hour_gan": hour_result.hour_gan,
                    "hour_zhi": hour_result.hour_zhi,
                })

            calendar_days.append({
                "day": day_result.day,
                "hours": hours_data,
                "overall_quality": day_result.overall_quality,
                "reasons": list(day_result.reasons),
                "lunar_date": day_result.lunar_date,
                "score": day_result.score,
            })

        return JsonResponse({
            "days": calendar_days,
            "month_score": result.month_context.month_score,
            "year_score": result.month_context.year_score,
            "year": year,
            "month": month,
            "year_gan": result.month_context.year_gan,
            "year_zhi": result.month_context.year_zhi,
            "month_gan": result.month_context.month_gan,
            "month_zhi": result.month_context.month_zhi,
        })

    def _get_profile(self, request, profile_id):
        """
        Build profile from POST data.

        Local-first architecture: Frontend always sends birth data directly
        from IndexedDB, regardless of auth status.
        """
        from bazi.domain.models import BirthData
        from bazi.domain.ports import ProfileData

        try:
            birth_year = int(request.POST.get("birth_year", 0))
            birth_month = int(request.POST.get("birth_month", 0))
            birth_day = int(request.POST.get("birth_day", 0))
            birth_hour = int(request.POST.get("birth_hour", 0))
            birth_minute = int(request.POST.get("birth_minute", 0))
            is_male = request.POST.get("is_male", "true").lower() == "true"

            if not all([birth_year, birth_month, birth_day]):
                return None

            birth_data = BirthData(
                year=birth_year,
                month=birth_month,
                day=birth_day,
                hour=birth_hour,
                minute=birth_minute,
                is_male=is_male,
            )

            return ProfileData(
                id=0,
                user_id=0,
                name="",
                birth_data=birth_data,
                is_default=False,
            )
        except (ValueError, TypeError):
            return None

    def get(self, request):
        """Handle GET request (not allowed)."""
        return JsonResponse({"error": "Invalid request"}, status=400)


# =============================================================================
# URL-compatible function aliases (for backward compatibility)
# =============================================================================

calendar_view = CalendarPageView.as_view()
calendar_data = CalendarDataView.as_view()
