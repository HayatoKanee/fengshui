"""
Day Quality Service.

Application service for calculating day quality assessments
based on profile conflicts, wuxing compatibility, and auspicious stars.

This service was extracted from the presentation layer to follow
Clean Architecture principles (business logic belongs in application layer).
"""
from dataclasses import dataclass
from datetime import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

from bazi.domain.constants import (
    GAN_WUXING,
    GANZHI_WUXING,
    GUI_REN,
    TIAN_DE,
    WEN_CHANG,
    YUE_DE,
    is_gan_clash,
    is_zhi_clash,
)
from bazi.domain.models import BirthData, check_he
from bazi.domain.ports import LunarPort, ProfileData

# Type checking imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bazi.application.services import BaziAnalysisService, CalendarService
    from bazi.domain.services import ShenShaCalculator


# =============================================================================
# Data Transfer Objects
# =============================================================================

@dataclass(frozen=True)
class ProfileContext:
    """Context data extracted from a user profile for calendar calculations."""
    profile_id: int
    birth_data: BirthData
    all_gan: Tuple[str, ...]
    all_zhi: Tuple[str, ...]
    day_gan: str
    day_zhi: str
    month_zhi: str
    day_wuxing: str
    good_wuxing: Tuple[str, ...]
    bad_wuxing: Tuple[str, ...]
    is_strong: bool
    profile_bazi: Any  # Raw lunar_python bazi object (temporary until fully abstracted)


@dataclass(frozen=True)
class MonthContext:
    """Context data for the current month being calculated."""
    year: int
    month: int
    year_gan: str
    year_zhi: str
    month_gan: str
    month_zhi: str
    year_score: float
    month_score: float


@dataclass(frozen=True)
class DayQualityResult:
    """Result of a single day quality calculation."""
    day: int
    hours: Tuple[Dict[str, Any], ...]
    overall_quality: str
    reasons: Tuple[Dict[str, str], ...]
    lunar_date: str
    score: float


@dataclass(frozen=True)
class MonthResult:
    """Result of a complete month quality calculation."""
    year: int
    month: int
    days: Tuple[DayQualityResult, ...]
    month_context: MonthContext
    profile_context: ProfileContext


# =============================================================================
# Constants
# =============================================================================

# Hours to calculate quality for (Chinese zodiac hours)
ZODIAC_HOURS = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23)

# Score adjustments
SCORE_YEAR_CONFLICT = -0.1
SCORE_YEAR_FAVORABLE = 0.1
SCORE_MONTH_CONFLICT = -0.2
SCORE_MONTH_FAVORABLE = 0.1
SCORE_SPECIAL_DAY_PENALTY = -2.0
SCORE_YANG_GONG_PENALTY = -0.5
SCORE_DAY_CONFLICT = -2.0
SCORE_BAD_WUXING = -0.5
SCORE_GOOD_WUXING = 0.25
SCORE_HARMONY = 1.0
SCORE_AUSPICIOUS_STAR = 1.0


# =============================================================================
# Day Quality Service
# =============================================================================

class DayQualityService:
    """
    Service for calculating day quality assessments.

    Encapsulates all the business logic for determining day quality
    based on profile conflicts, wuxing compatibility, and auspicious stars.

    This is an application service that orchestrates domain services
    to produce calendar quality assessments.
    """

    def __init__(
        self,
        lunar_adapter: LunarPort,
        bazi_service: "BaziAnalysisService",
        calendar_service: "CalendarService",
        shensha_calculator: "ShenShaCalculator",
    ):
        """
        Initialize the day quality service.

        Args:
            lunar_adapter: Adapter for lunar calendar calculations
            bazi_service: Service for BaZi analysis
            calendar_service: Service for calendar taboo checks
            shensha_calculator: Calculator for shensha (special stars)
        """
        self._lunar = lunar_adapter
        self._bazi = bazi_service
        self._calendar = calendar_service
        self._shensha = shensha_calculator

    def build_profile_context(self, profile: ProfileData) -> ProfileContext:
        """
        Build profile context from a ProfileData object.

        Args:
            profile: ProfileData from repository

        Returns:
            ProfileContext with all calculated values
        """
        # Get profile's BaZi via lunar adapter
        profile_lunar, profile_bazi = self._lunar.get_raw_lunar_and_bazi(
            profile.birth_data.year,
            profile.birth_data.month,
            profile.birth_data.day,
            profile.birth_data.hour,
            profile.birth_data.minute or 0,
        )

        # Extract pillars
        all_gan = (
            profile_bazi.getYearGan(),
            profile_bazi.getMonthGan(),
            profile_bazi.getDayGan(),
            profile_bazi.getTimeGan(),
        )
        all_zhi = (
            profile_bazi.getYearZhi(),
            profile_bazi.getMonthZhi(),
            profile_bazi.getDayZhi(),
            profile_bazi.getTimeZhi(),
        )

        # Calculate favorable elements via BaZi service
        birth_data = BirthData(
            year=profile.birth_data.year,
            month=profile.birth_data.month,
            day=profile.birth_data.day,
            hour=profile.birth_data.hour,
            minute=profile.birth_data.minute or 0,
            is_male=profile.birth_data.is_male,
        )
        summary = self._bazi.get_quick_summary(birth_data)

        return ProfileContext(
            profile_id=profile.id,
            birth_data=birth_data,
            all_gan=all_gan,
            all_zhi=all_zhi,
            day_gan=profile_bazi.getDayGan(),
            day_zhi=profile_bazi.getDayZhi(),
            month_zhi=profile_bazi.getMonthZhi(),
            day_wuxing=GAN_WUXING.get(profile_bazi.getDayGan()),
            good_wuxing=tuple(summary["favorable_wuxing"]),
            bad_wuxing=tuple(summary["unfavorable_wuxing"]),
            is_strong=summary["is_strong"],
            profile_bazi=profile_bazi,
        )

    def build_month_context(
        self,
        year: int,
        month: int,
        profile_ctx: ProfileContext,
    ) -> MonthContext:
        """
        Build month context with score adjustments.

        Args:
            year: Calendar year
            month: Calendar month
            profile_ctx: Profile context data

        Returns:
            MonthContext with year/month pillars and scores
        """
        # Get year and month pillars
        month_lunar, month_bazi = self._lunar.get_raw_lunar_and_bazi(
            year, month, 1, 12, 0
        )
        month_gan = month_bazi.getMonthGan()
        month_zhi = month_bazi.getMonthZhi()
        year_gan = month_bazi.getYearGan()
        year_zhi = month_bazi.getYearZhi()

        # Calculate score adjustments
        year_score = self._calculate_year_score(year_gan, year_zhi, profile_ctx)
        month_score = self._calculate_month_score(
            month_gan, month_zhi, year_gan, year_zhi, profile_ctx
        )

        return MonthContext(
            year=year,
            month=month,
            year_gan=year_gan,
            year_zhi=year_zhi,
            month_gan=month_gan,
            month_zhi=month_zhi,
            year_score=year_score,
            month_score=month_score,
        )

    def calculate_day(
        self,
        day: int,
        month_ctx: MonthContext,
        profile_ctx: ProfileContext,
    ) -> DayQualityResult:
        """
        Calculate quality assessment for a single day.

        Args:
            day: Day of month (1-31)
            month_ctx: Month context with pillars and scores
            profile_ctx: Profile context data

        Returns:
            DayQualityResult with quality assessment
        """
        day_reasons: List[Dict[str, str]] = []
        day_score = month_ctx.year_score + month_ctx.month_score
        day_quality = "neutral"

        # Add year/month adjustment explanations
        if month_ctx.year_score != 0:
            reason_type = "good" if month_ctx.year_score > 0 else "bad"
            day_reasons.append({
                "type": reason_type,
                "text": f"年度因素: {month_ctx.year_score:+.1f}分"
            })

        if month_ctx.month_score != 0:
            reason_type = "good" if month_ctx.month_score > 0 else "bad"
            day_reasons.append({
                "type": reason_type,
                "text": f"月度因素: {month_ctx.month_score:+.1f}分"
            })

        # Get day's BaZi
        date_lunar, date_bazi = self._lunar.get_raw_lunar_and_bazi(
            month_ctx.year, month_ctx.month, day, 12, 0
        )

        # Get lunar date for display
        lunar_month = date_lunar.getMonthInChinese()
        lunar_day = date_lunar.getDayInChinese()
        lunar_date = f"{lunar_month}月{lunar_day}"

        day_gan = date_bazi.getDayGan()
        day_zhi = date_bazi.getDayZhi()

        # Run all quality checks
        day_score, day_quality, day_reasons = self._check_special_days(
            month_ctx.year, month_ctx.month, day,
            date_lunar, date_bazi, day_gan, day_zhi,
            day_score, day_quality, day_reasons,
        )

        day_score, day_quality, day_reasons = self._check_year_month_conflicts(
            day_gan, day_zhi, month_ctx,
            day_score, day_quality, day_reasons,
        )

        day_score, day_quality, day_reasons = self._check_profile_conflicts(
            day_gan, day_zhi, profile_ctx,
            day_score, day_quality, day_reasons,
        )

        day_score, day_reasons = self._check_wuxing_compatibility(
            day_gan, day_zhi, profile_ctx,
            day_score, day_reasons,
        )

        day_score, day_reasons = self._check_harmonies(
            day_zhi, profile_ctx,
            day_score, day_reasons,
        )

        day_score, day_reasons = self._check_auspicious_stars(
            month_ctx.year, month_ctx.month, day,
            day_gan, day_zhi, profile_ctx,
            day_score, day_reasons,
        )

        # Build hour quality using constant
        hours = tuple(
            {"hour": h, "quality": "neutral"}
            for h in ZODIAC_HOURS
        )

        # Default explanation for neutral days
        if day_quality == "neutral" and not day_reasons:
            day_reasons.append({"type": "neutral", "text": "此日无特殊吉凶因素"})

        return DayQualityResult(
            day=day,
            hours=hours,
            overall_quality=day_quality,
            reasons=tuple(day_reasons),
            lunar_date=lunar_date,
            score=day_score,
        )

    def calculate_month(
        self,
        year: int,
        month: int,
        profile: ProfileData,
    ) -> MonthResult:
        """
        Calculate quality assessments for all days in a month.

        Args:
            year: Calendar year
            month: Calendar month (1-12)
            profile: ProfileData from repository

        Returns:
            MonthResult with all day assessments and context
        """
        import datetime

        # Build contexts
        profile_ctx = self.build_profile_context(profile)
        month_ctx = self.build_month_context(year, month, profile_ctx)

        # Calculate days in month
        first_day = datetime.datetime(year, month, 1)
        if month == 12:
            last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
        num_days = last_day.day

        # Calculate quality for each day
        days = []
        for day in range(1, num_days + 1):
            day_result = self.calculate_day(day, month_ctx, profile_ctx)
            days.append(day_result)

        return MonthResult(
            year=year,
            month=month,
            days=tuple(days),
            month_context=month_ctx,
            profile_context=profile_ctx,
        )

    # =========================================================================
    # Private calculation methods
    # =========================================================================

    def _calculate_year_score(
        self,
        year_gan: str,
        year_zhi: str,
        profile_ctx: ProfileContext,
    ) -> float:
        """Calculate year-level quality adjustment score."""
        score = 0.0

        # Check gan conflicts
        for profile_gan in profile_ctx.all_gan:
            if is_gan_clash(year_gan, profile_gan):
                score += SCORE_YEAR_CONFLICT
                break

        # Check zhi conflicts
        for profile_zhi in profile_ctx.all_zhi:
            if is_zhi_clash(year_zhi, profile_zhi):
                score += SCORE_YEAR_CONFLICT
                break

        # Check if year elements are favorable
        year_gan_wuxing = GAN_WUXING.get(year_gan)
        year_zhi_wuxing = GANZHI_WUXING.get(year_zhi)
        if year_gan_wuxing in profile_ctx.good_wuxing or year_zhi_wuxing in profile_ctx.good_wuxing:
            score += SCORE_YEAR_FAVORABLE

        return score

    def _calculate_month_score(
        self,
        month_gan: str,
        month_zhi: str,
        year_gan: str,
        year_zhi: str,
        profile_ctx: ProfileContext,
    ) -> float:
        """Calculate month-level quality adjustment score."""
        score = 0.0

        # Check month gan conflicts with year gan
        if is_gan_clash(month_gan, year_gan):
            score += SCORE_MONTH_CONFLICT

        # Check month gan conflicts with profile
        for profile_gan in profile_ctx.all_gan:
            if is_gan_clash(month_gan, profile_gan):
                score += SCORE_MONTH_CONFLICT
                break

        # Check month zhi conflicts with year zhi
        if is_zhi_clash(month_zhi, year_zhi):
            score += SCORE_MONTH_CONFLICT

        # Check month zhi conflicts with profile
        for profile_zhi in profile_ctx.all_zhi:
            if is_zhi_clash(month_zhi, profile_zhi):
                score += SCORE_MONTH_CONFLICT
                break

        # Check if month elements are favorable
        month_gan_wuxing = GAN_WUXING.get(month_gan)
        month_zhi_wuxing = GANZHI_WUXING.get(month_zhi)
        if month_gan_wuxing in profile_ctx.good_wuxing or month_zhi_wuxing in profile_ctx.good_wuxing:
            score += SCORE_MONTH_FAVORABLE

        return score

    def _check_special_days(
        self,
        year: int,
        month: int,
        day: int,
        date_lunar: Any,
        date_bazi: Any,
        day_gan: str,
        day_zhi: str,
        day_score: float,
        day_quality: str,
        day_reasons: List[Dict],
    ) -> Tuple[float, str, List[Dict]]:
        """Check for special inauspicious days."""
        # 四绝日 (Four Jue Days)
        if self._calendar.is_si_jue_ri(year, month, day):
            day_quality = "bad"
            day_score += SCORE_SPECIAL_DAY_PENALTY
            day_reasons.append({
                "type": "bad",
                "text": "四绝日: 此日为节气前一天，为四绝日，不宜做重要事情"
            })

        # 四离日 (Four Li Days)
        if self._calendar.is_si_li_ri(year, month, day):
            day_quality = "bad"
            day_score += SCORE_SPECIAL_DAY_PENALTY
            day_reasons.append({
                "type": "bad",
                "text": "四离日: 此日为分至前一天，为四离日，不宜做重要事情"
            })

        # 杨公十三忌 (Yang Gong Thirteen Taboos)
        lunar_month = date_lunar.getMonth()
        lunar_day = date_lunar.getDay()
        if self._calendar.is_yang_gong_taboo(lunar_month, lunar_day):
            day_score += SCORE_YANG_GONG_PENALTY
            day_reasons.append({
                "type": "bad",
                "text": "杨公十三忌: 此日为杨公忌日，不宜做重要事情"
            })

        # 破日 (Breaking Day)
        if date_lunar.getZhiXing() == "破":
            day_quality = "bad"
            day_score += SCORE_SPECIAL_DAY_PENALTY
            day_reasons.append({
                "type": "bad",
                "text": "破日: 此日为破日，不宜做重要事情"
            })

        return day_score, day_quality, day_reasons

    def _check_year_month_conflicts(
        self,
        day_gan: str,
        day_zhi: str,
        month_ctx: MonthContext,
        day_score: float,
        day_quality: str,
        day_reasons: List[Dict],
    ) -> Tuple[float, str, List[Dict]]:
        """Check conflicts between day pillar and year/month."""
        # Day gan conflicts
        if is_gan_clash(day_gan, month_ctx.year_gan):
            day_quality = "bad"
            day_score += SCORE_DAY_CONFLICT
            day_reasons.append({
                "type": "bad",
                "text": f"日干 {day_gan} 与年干 {month_ctx.year_gan} 相冲"
            })
        if is_gan_clash(day_gan, month_ctx.month_gan):
            day_quality = "bad"
            day_score += SCORE_DAY_CONFLICT
            day_reasons.append({
                "type": "bad",
                "text": f"日干 {day_gan} 与月干 {month_ctx.month_gan} 相冲"
            })

        # Day zhi conflicts
        if is_zhi_clash(day_zhi, month_ctx.year_zhi):
            day_quality = "bad"
            day_score += SCORE_DAY_CONFLICT
            day_reasons.append({
                "type": "bad",
                "text": f"日支 {day_zhi} 与年支 {month_ctx.year_zhi} 相冲"
            })
        if is_zhi_clash(day_zhi, month_ctx.month_zhi):
            day_quality = "bad"
            day_score += SCORE_DAY_CONFLICT
            day_reasons.append({
                "type": "bad",
                "text": f"日支 {day_zhi} 与月支 {month_ctx.month_zhi} 相冲"
            })

        return day_score, day_quality, day_reasons

    def _check_profile_conflicts(
        self,
        day_gan: str,
        day_zhi: str,
        profile_ctx: ProfileContext,
        day_score: float,
        day_quality: str,
        day_reasons: List[Dict],
    ) -> Tuple[float, str, List[Dict]]:
        """Check conflicts between day pillar and profile."""
        for profile_gan in profile_ctx.all_gan:
            if is_gan_clash(day_gan, profile_gan):
                day_quality = "bad"
                day_score += SCORE_DAY_CONFLICT
                day_reasons.append({
                    "type": "bad",
                    "text": f"日干 {day_gan} 与八字天干 {profile_gan} 相冲"
                })

        for profile_zhi in profile_ctx.all_zhi:
            if is_zhi_clash(day_zhi, profile_zhi):
                day_quality = "bad"
                day_score += SCORE_DAY_CONFLICT
                day_reasons.append({
                    "type": "bad",
                    "text": f"日支 {day_zhi} 与八字地支 {profile_zhi} 相冲"
                })

        return day_score, day_quality, day_reasons

    def _check_wuxing_compatibility(
        self,
        day_gan: str,
        day_zhi: str,
        profile_ctx: ProfileContext,
        day_score: float,
        day_reasons: List[Dict],
    ) -> Tuple[float, List[Dict]]:
        """Check five element compatibility."""
        day_gan_wuxing = GAN_WUXING.get(day_gan)
        day_zhi_wuxing = GANZHI_WUXING.get(day_zhi)

        # Bad elements
        if day_gan_wuxing in profile_ctx.bad_wuxing:
            day_score += SCORE_BAD_WUXING
            day_reasons.append({
                "type": "bad",
                "text": f"日干五行 {day_gan_wuxing} 对命主不利"
            })
        if day_zhi_wuxing in profile_ctx.bad_wuxing:
            day_score += SCORE_BAD_WUXING
            day_reasons.append({
                "type": "bad",
                "text": f"日支五行 {day_zhi_wuxing} 对命主不利"
            })

        # Good elements
        if day_gan_wuxing in profile_ctx.good_wuxing:
            day_score += SCORE_GOOD_WUXING
            day_reasons.append({
                "type": "good",
                "text": f"日干五行 {day_gan_wuxing} 对命主有利"
            })
        if day_zhi_wuxing in profile_ctx.good_wuxing:
            day_score += SCORE_GOOD_WUXING
            day_reasons.append({
                "type": "good",
                "text": f"日支五行 {day_zhi_wuxing} 对命主有利"
            })

        return day_score, day_reasons

    def _check_harmonies(
        self,
        day_zhi: str,
        profile_ctx: ProfileContext,
        day_score: float,
        day_reasons: List[Dict],
    ) -> Tuple[float, List[Dict]]:
        """Check for harmonies (合) between day and profile."""
        for gan_zhi in profile_ctx.profile_bazi.toString().split(" "):
            if check_he(gan_zhi, day_zhi):
                day_score += SCORE_HARMONY
                day_reasons.append({
                    "type": "good",
                    "text": f"日支 {day_zhi} 与八字 {gan_zhi} 相合"
                })
                break
        return day_score, day_reasons

    def _check_auspicious_stars(
        self,
        year: int,
        month: int,
        day: int,
        day_gan: str,
        day_zhi: str,
        profile_ctx: ProfileContext,
        day_score: float,
        day_reasons: List[Dict],
    ) -> Tuple[float, List[Dict]]:
        """Check for auspicious stars."""
        # Get domain BaZi for this date and calculate ShenSha
        domain_bazi = self._lunar.get_bazi_from_datetime(
            dt(year, month, day, 12, 0)
        )
        shensha_analysis = self._shensha.calculate_for_bazi(domain_bazi)

        # Check for auspicious stars from domain analysis
        shensha_types = {ss.type.name for ss in shensha_analysis.shensha_list}

        if "TIAN_DE" in shensha_types:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({"type": "good", "text": "此日有天德星"})
        if "YUE_DE" in shensha_types:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({"type": "good", "text": "此日有月德星"})
        if "WEN_CHANG" in shensha_types:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({"type": "good", "text": "此日有文昌星"})
        if "TIAN_YI_GUI_REN" in shensha_types:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({"type": "good", "text": "此日有天乙贵人"})

        # Profile interaction stars
        if (profile_ctx.day_gan, day_zhi) in GUI_REN:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({
                "type": "good",
                "text": f"命主日干 {profile_ctx.day_gan} 与当日日支 {day_zhi} 贵人相见",
            })
        if (day_gan, profile_ctx.day_zhi) in WEN_CHANG:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({
                "type": "good",
                "text": f"命主日干 {day_gan} 与当日日支 {profile_ctx.day_zhi} 文昌相见",
            })
        if (profile_ctx.month_zhi, day_gan) in TIAN_DE:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({
                "type": "good",
                "text": f"命主月支 {profile_ctx.month_zhi} 与当日日干 {day_gan} 天德相见",
            })
        if (profile_ctx.month_zhi, day_gan) in YUE_DE:
            day_score += SCORE_AUSPICIOUS_STAR
            day_reasons.append({
                "type": "good",
                "text": f"命主月支 {profile_ctx.month_zhi} 与当日日干 {day_gan} 月德相见",
            })

        return day_score, day_reasons
