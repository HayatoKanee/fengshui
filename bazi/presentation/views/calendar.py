"""
Calendar Views.

Views for the BaZi calendar showing day quality assessments
based on user's birth chart.

Uses DayQualityService from the application layer for all calculations.
"""
import datetime

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from bazi.presentation.views.base import BaziLoginRequiredMixin, ContainerMixin


# =============================================================================
# Class-Based Views
# =============================================================================

class CalendarPageView(BaziLoginRequiredMixin, ContainerMixin, TemplateView):
    """
    Calendar page view.

    Displays a month calendar with day quality indicators
    based on the user's selected BaZi profile.

    Requires user to have at least one profile.
    """
    template_name = 'calendar.html'

    def get(self, request, *args, **kwargs):
        """Handle GET request."""
        profiles = self.profile_repo.get_by_user(request.user.id)

        if not profiles:
            messages.warning(
                request,
                "您需要先创建八字资料才能使用日历功能。请先创建一个资料。"
            )
            return redirect("profiles")

        return super().get(request, *args, **kwargs)

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
            "profiles": self.profile_repo.get_by_user(self.request.user.id),
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
            calendar_days.append({
                "day": day_result.day,
                "hours": list(day_result.hours),
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
        """Get the user's profile by ID or default."""
        if not request.user.is_authenticated:
            return None

        if profile_id:
            profile = self.profile_repo.get_by_id(int(profile_id))
            if profile and profile.user_id == request.user.id:
                return profile

        # Fall back to default profile
        return self.profile_repo.get_default_for_user(request.user.id)

    def get(self, request):
        """Handle GET request (not allowed)."""
        return JsonResponse({"error": "Invalid request"}, status=400)


# =============================================================================
# URL-compatible function aliases (for backward compatibility)
# =============================================================================

calendar_view = CalendarPageView.as_view()
calendar_data = CalendarDataView.as_view()
