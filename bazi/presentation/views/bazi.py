"""
BaZi Analysis Views.

Main views for BaZi (Four Pillars) analysis and display.
Uses DI container for all infrastructure access (DIP-compliant).
"""
import datetime
from datetime import date
from typing import Any, Dict, Optional

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView, View

from bazi.presentation.presenters import BaziPresenter, get_shensha
from bazi.presentation.presenters.shensha_rules import (
    _calculate_day_guiren,
    _calculate_year_guiren,
    _calculate_tian_de,
    _calculate_yue_de,
    _calculate_wen_chang,
    _calculate_lu_shen,
)
from bazi.presentation.forms import BirthTimeForm
from bazi.presentation.views.base import ContainerMixin, ProfileMixin
from bazi.domain.models import BaZi as DomainBaZi, WuXing


class BaziContextBuilder(ContainerMixin):
    """
    Builder for BaZi template context.

    Encapsulates all the complex logic for building the context
    data needed by the bazi.html template.
    """

    def __init__(self):
        self.presenter = BaziPresenter()
        self.current_year = datetime.datetime.now().year

    def _analyze_patterns(self, bazi_eight_char, wuxing_value: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze BaZi patterns (格局分析).

        Converts lunar_python BaZi to domain BaZi and runs pattern analysis.

        Args:
            bazi_eight_char: lunar_python EightChar object
            wuxing_value: WuXing strength values (string keys like '木', '火')

        Returns:
            Dict with pattern analysis data for templates
        """
        from bazi.domain.services import PatternAnalyzer

        # Convert lunar_python BaZi to domain BaZi
        bazi_string = bazi_eight_char.toString()  # e.g., "甲子 乙丑 丙寅 丁卯"
        domain_bazi = DomainBaZi.from_chinese(bazi_string)

        # Convert string wuxing_value keys to WuXing enum
        wuxing_values = {
            WuXing.WOOD: wuxing_value.get('木', 0),
            WuXing.FIRE: wuxing_value.get('火', 0),
            WuXing.EARTH: wuxing_value.get('土', 0),
            WuXing.METAL: wuxing_value.get('金', 0),
            WuXing.WATER: wuxing_value.get('水', 0),
        }

        # Run pattern analysis
        analyzer = PatternAnalyzer()
        pattern_result = analyzer.analyze(domain_bazi, wuxing_values)

        # Format results for template
        context = {
            'has_special_pattern': pattern_result.has_special_pattern,
            'special_pattern_name': None,
            'special_pattern_desc': None,
            'special_pattern_advice': [],
            'regular_pattern_name': None,
            'regular_pattern_desc': None,
            'favorable_elements': None,
        }

        # Special pattern info
        if pattern_result.has_special_pattern:
            pattern = pattern_result.primary_pattern
            context['special_pattern_name'] = pattern.pattern_type.value
            context['special_pattern_desc'] = pattern_result.get_pattern_description()
            context['special_pattern_advice'] = pattern_result.get_favorable_advice()

            # Get special pattern favorable elements
            favorable = pattern_result.get_special_favorable_elements(domain_bazi.day_master_wuxing)
            if favorable:
                yong, xi, ji, chou = favorable
                context['favorable_elements'] = {
                    'yong_shen': yong.value,  # 用神
                    'xi_shen': xi.value,      # 喜神
                    'ji_shen': ji.value,      # 忌神
                    'chou_shen': chou.value,  # 仇神
                }

        # Regular pattern info (正格)
        if pattern_result.regular_pattern:
            context['regular_pattern_name'] = pattern_result.regular_pattern.name
            context['regular_pattern_desc'] = pattern_result.regular_pattern.description
            context['regular_pattern_shishen'] = pattern_result.regular_pattern.shishen

        return context

    def _get_liunian_year_options(self, birth_year: int = None) -> list:
        """
        Generate year options with 干支 for the dropdown.

        Returns a wide range of years with their corresponding 干支 (GanZhi) names.
        If birth_year is provided, starts from birth year; otherwise starts 100 years back.

        Args:
            birth_year: Optional birth year to start the range from

        Returns:
            List of (year, ganzhi) tuples
        """
        from bazi.domain.services.sexagenary_calculator import SexagenaryCycleCalculator
        calculator = SexagenaryCycleCalculator()

        # Wide range: from birth year (or 100 years back) to 100 years forward
        start_year = birth_year if birth_year else self.current_year - 100
        end_year = self.current_year + 100

        options = []
        for year in range(start_year, end_year + 1):
            ganzhi = calculator.get_year_pillar(year)
            options.append((year, ganzhi))

        return options

    def build(
        self,
        form: BirthTimeForm,
        bazi,
        lunar,
        is_male: bool,
        liunian_year: int,
        profiles=None,
    ) -> Dict[str, Any]:
        """
        Build the template context for BaZi analysis.

        Args:
            form: The birth time form
            bazi: The lunar_python EightChar object
            lunar: The lunar_python Lunar object
            is_male: Whether the person is male
            liunian_year: Year for LiuNian analysis
            profiles: Optional list of user profiles

        Returns:
            Dict with all template context data
        """
        # Use presenter for all template-specific data formatting
        view_data = self.presenter.present(bazi, lunar)

        # Use Feb 10 of the selected year (safely after Lichun ~Feb 3-5)
        # This ensures we get the correct Chinese year pillar
        liunian_date = date(liunian_year, 2, 10)

        # Get year pillar for the liunian year
        lunar_adapter = self.container.lunar_adapter
        liunian_year_pillar = lunar_adapter.get_year_pillar(
            liunian_date.year, liunian_date.month, liunian_date.day
        )

        # Get Lichun date for the selected year
        lichun_dates = lunar_adapter.get_jieqi_dates(liunian_year, ["立春"])
        lichun_date = lichun_dates[0] if lichun_dates else None

        # Use application services for complex analysis via container
        liunian_service = self.container.liunian_service
        partner_analyst = liunian_service.analyse_partner(
            view_data.hidden_gans, view_data.shishen
        )
        personality = liunian_service.analyse_personality(bazi.getMonthZhi())
        liunian_analysis = liunian_service.analyse_liunian(
            bazi, view_data.shishen, liunian_date, view_data.is_strong, is_male
        )
        shensha_list = get_shensha(bazi)

        # Generate year dropdown options (starting from birth year)
        birth_year = form.cleaned_data.get('year') if form.is_valid() else None
        liunian_year_options = self._get_liunian_year_options(birth_year)

        # Pattern analysis (格局分析)
        pattern_context = self._analyze_patterns(bazi, view_data.wuxing_value)

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
            "liunian_year_options": liunian_year_options,
            "selected_liunian_year": liunian_year,
            "liunian_year_pillar": liunian_year_pillar.chinese,
            "lichun_date": lichun_date.strftime("%Y-%m-%d") if lichun_date else "N/A",
            "today_date": date.today().strftime("%Y-%m-%d"),
            "is_male": is_male,
            "partner_analyst": partner_analyst,
            "liunian_analysis": liunian_analysis,
            "personality": personality,
            "shensha_list": shensha_list,
            "profiles": profiles,
            # Pattern analysis (格局分析)
            **pattern_context,
        }


class BaziAnalysisView(ProfileMixin, TemplateView):
    """
    Main BaZi analysis view.

    Handles both:
    - GET: Display form (optionally pre-filled from profile)
    - POST: Calculate and display BaZi analysis

    Query Parameters:
        profile_id: Optional profile ID to load birth data from
        year: Optional year for LiuNian (yearly fortune) analysis
    """
    template_name = 'bazi.html'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Build base context with form and year range."""
        context = super().get_context_data(**kwargs)
        current_year = datetime.datetime.now().year

        context.update({
            'form': BirthTimeForm(),
            'current_year': current_year,
            'years': range(current_year - 20, current_year + 50),
            'profiles': self.get_user_profiles(),
        })
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET request - display form or profile analysis."""
        current_year = datetime.datetime.now().year
        profile_id = request.GET.get('profile_id')

        # Check if viewing a saved profile
        if profile_id and request.user.is_authenticated:
            profile = self.profile_repo.get_by_id(int(profile_id))

            if profile and profile.user_id == request.user.id:
                return self._render_profile_analysis(request, profile, current_year)

        # Default: show empty form
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle POST request - calculate and display BaZi."""
        current_year = datetime.datetime.now().year
        form = BirthTimeForm(request.POST)

        if not form.is_valid():
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)

        # Extract form data
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']
        day = form.cleaned_data['day']
        hour = form.cleaned_data['hour']
        minute = form.cleaned_data['minute']

        is_male = request.POST.get('gender') == 'male'

        # Use current year as default for liunian analysis
        liunian_year = date.today().year

        # Calculate BaZi
        lunar, bazi = self.container.lunar_adapter.get_raw_lunar_and_bazi(
            year, month, day, hour, minute
        )

        # Build context
        builder = BaziContextBuilder()
        context = builder.build(
            form=form,
            bazi=bazi,
            lunar=lunar,
            is_male=is_male,
            liunian_year=liunian_year,
            profiles=self.get_user_profiles(),
        )

        return render(request, self.template_name, context)

    def _render_profile_analysis(self, request, profile, current_year: int):
        """Render analysis for a saved profile."""
        is_male = profile.birth_data.is_male

        # Use current year as default for liunian analysis
        liunian_year = date.today().year

        # Calculate BaZi for the profile
        lunar, bazi = self.container.lunar_adapter.get_raw_lunar_and_bazi(
            profile.birth_data.year,
            profile.birth_data.month,
            profile.birth_data.day,
            profile.birth_data.hour,
            profile.birth_data.minute,
        )

        # Pre-fill form with profile data
        initial_data = {
            'year': profile.birth_data.year,
            'month': profile.birth_data.month,
            'day': profile.birth_data.day,
            'hour': profile.birth_data.hour,
            'minute': profile.birth_data.minute,
            'gender': 'male' if is_male else 'female',
        }
        form = BirthTimeForm(initial=initial_data)

        # Build context
        builder = BaziContextBuilder()
        context = builder.build(
            form=form,
            bazi=bazi,
            lunar=lunar,
            is_male=is_male,
            liunian_year=liunian_year,
            profiles=self.get_user_profiles(),
        )

        return render(request, self.template_name, context)


class BaziDetailView(ProfileMixin, View):
    """
    HTMX endpoint for BaZi detail partial.

    Returns an HTML fragment with detailed BaZi analysis
    for embedding via HTMX requests.
    """

    def post(self, request):
        """Handle POST request - return BaZi detail partial."""
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')
        hour = request.POST.get('hour')
        profile_id = request.POST.get('profile_id')

        if not all([year, month, day, hour]):
            return HttpResponse(status=400)

        # Get profile if provided
        profile = None
        if profile_id and request.user.is_authenticated:
            profile = self.profile_repo.get_by_id(int(profile_id))
            if profile and profile.user_id != request.user.id:
                profile = None

        # Calculate BaZi
        lunar, bazi = self.container.lunar_adapter.get_raw_lunar_and_bazi(
            int(year), int(month), int(day), int(hour), 0
        )

        # Use presenter for template-specific data formatting
        presenter = BaziPresenter()
        view_data = presenter.present(bazi, lunar)

        # Calculate shensha
        shensha_list = get_shensha(bazi)

        # Calculate individual shensha counts
        shensha_counts = self._calculate_shensha_counts(bazi)

        context = {
            'bazi': bazi,
            'wuxing': view_data.wuxing,
            'wuxing_value': view_data.wuxing_value,
            'sheng_hao': view_data.sheng_hao,
            'sheng_hao_percentage': view_data.sheng_hao_percentage,
            'shensha_list': shensha_list,
            **shensha_counts,
        }

        html = render_to_string('partials/bazi_detail.html', context)
        return HttpResponse(html)

    def _calculate_shensha_counts(self, bazi) -> Dict[str, int]:
        """Calculate individual shensha counts for template display."""
        # 贵人 combines both day and year guiren
        gui_ren_count = _calculate_day_guiren(bazi) + _calculate_year_guiren(bazi)

        return {
            'gui_ren': gui_ren_count,
            'tian_de': _calculate_tian_de(bazi),
            'yue_de': _calculate_yue_de(bazi),
            'wen_chang': _calculate_wen_chang(bazi),
            'lu_shen': _calculate_lu_shen(bazi),
        }


class LiunianPartialView(ContainerMixin, View):
    """
    HTMX endpoint for dynamic LiuNian (yearly fortune) analysis.

    Returns an HTML fragment with updated liunian analysis when the
    user changes the year dropdown, without requiring a page refresh.
    """

    def get(self, request):
        """Handle GET request - return updated liunian partial."""
        liunian_year_str = request.GET.get('liunian_year')
        birth_year = request.GET.get('birth_year')
        birth_month = request.GET.get('birth_month')
        birth_day = request.GET.get('birth_day')
        birth_hour = request.GET.get('birth_hour')
        birth_minute = request.GET.get('birth_minute', '0')
        is_male_str = request.GET.get('is_male', 'True')

        # Validate required parameters
        if not all([liunian_year_str, birth_year, birth_month, birth_day, birth_hour]):
            return HttpResponse(status=400)

        # Parse the liunian year and birth data
        try:
            liunian_year = int(liunian_year_str)
            birth_year = int(birth_year)
            birth_month = int(birth_month)
            birth_day = int(birth_day)
            birth_hour = int(birth_hour)
            birth_minute = int(birth_minute) if birth_minute else 0
        except ValueError:
            return HttpResponse(status=400)

        is_male = is_male_str.lower() == 'true'

        # Use Feb 10 of the selected year (safely after Lichun)
        liunian_date = date(liunian_year, 2, 10)

        # Reconstruct bazi from birth data
        lunar_adapter = self.container.lunar_adapter
        lunar, bazi = lunar_adapter.get_raw_lunar_and_bazi(
            birth_year, birth_month, birth_day, birth_hour, birth_minute
        )

        # Get year pillar for the selected liunian year
        liunian_year_pillar = lunar_adapter.get_year_pillar(
            liunian_date.year, liunian_date.month, liunian_date.day
        )

        # Get Lichun date for the selected year
        lichun_dates = lunar_adapter.get_jieqi_dates(liunian_year, ["立春"])
        lichun_date = lichun_dates[0] if lichun_dates else None

        # Use presenter for template-specific data formatting
        presenter = BaziPresenter()
        view_data = presenter.present(bazi, lunar)

        # Get liunian analysis
        liunian_service = self.container.liunian_service
        liunian_analysis = liunian_service.analyse_liunian(
            bazi, view_data.shishen, liunian_date, view_data.is_strong, is_male
        )

        context = {
            'selected_liunian_year': liunian_year,
            'liunian_year_pillar': liunian_year_pillar.chinese,
            'lichun_date': lichun_date.strftime('%Y-%m-%d') if lichun_date else 'N/A',
            'liunian_analysis': liunian_analysis,
        }

        html = render_to_string('partials/liunian_content.html', context)
        return HttpResponse(html)


# =============================================================================
# URL-compatible function aliases (for backward compatibility)
# =============================================================================

bazi_view = BaziAnalysisView.as_view()
get_bazi_detail = BaziDetailView.as_view()
liunian_partial = LiunianPartialView.as_view()
