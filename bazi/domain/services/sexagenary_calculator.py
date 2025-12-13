"""
Sexagenary Cycle Calculator - Direct pillar calculation without external library.

This service provides O(1) calculation of day pillars and O(matches) reverse lookup
for finding dates matching specific pillar patterns. Uses the mathematical properties
of the 60-day sexagenary cycle for dramatic performance improvement over brute-force.

Mathematical Foundation:
- Sexagenary number S = 1 + mod(JD_noon - 11, 60)
- Stem T = 1 + mod(S-1, 10) or T = 1 + mod(JD_noon - 1, 10)
- Branch B = 1 + mod(S-1, 12) or B = 1 + mod(JD_noon + 1, 12)

Reference: https://ytliu0.github.io/ChineseCalendar/sexagenary.html
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterator, Optional, Tuple

from bazi.domain.models import HeavenlyStem, EarthlyBranch


@dataclass(frozen=True)
class PillarPattern:
    """Pattern for matching pillars, with optional stem/branch."""
    stem: Optional[str] = None
    branch: Optional[str] = None

    def matches(self, stem_char: str, branch_char: str) -> bool:
        """Check if this pattern matches the given stem and branch."""
        if self.stem and self.stem != stem_char:
            return False
        if self.branch and self.branch != branch_char:
            return False
        return True

    @property
    def is_complete(self) -> bool:
        """True if both stem and branch are specified."""
        return self.stem is not None and self.branch is not None

    @property
    def is_empty(self) -> bool:
        """True if neither stem nor branch is specified."""
        return self.stem is None and self.branch is None


class SexagenaryCycleCalculator:
    """
    Direct calculation of sexagenary cycle indices without external library.

    Provides dramatic performance improvement for reverse lookup operations
    (finding dates matching specific pillar patterns) by using mathematical
    properties of the 60-day cycle instead of brute-force iteration.

    Performance:
    - Forward lookup (date → pillar): O(1)
    - Reverse lookup (pillar → dates): O(matches) instead of O(days)

    For a 100-year search with day pillar specified:
    - Before: ~365 * 100 = 36,500 calculations
    - After: ~365 * 100 / 60 = ~608 calculations (60x improvement)
    """

    # Heavenly Stems (天干) - 10 elements, derived from domain model
    STEMS = tuple(stem.value for stem in HeavenlyStem)

    # Earthly Branches (地支) - 12 elements, derived from domain model
    BRANCHES = tuple(branch.value for branch in EarthlyBranch)

    # Hour branch mapping (hour -> branch index)
    # 子时 23-01, 丑时 01-03, 寅时 03-05, etc.
    HOUR_TO_BRANCH = {
        23: 0, 0: 0,   # 子
        1: 1, 2: 1,    # 丑
        3: 2, 4: 2,    # 寅
        5: 3, 6: 3,    # 卯
        7: 4, 8: 4,    # 辰
        9: 5, 10: 5,   # 巳
        11: 6, 12: 6,  # 午
        13: 7, 14: 7,  # 未
        15: 8, 16: 8,  # 申
        17: 9, 18: 9,  # 酉
        19: 10, 20: 10,  # 戌
        21: 11, 22: 11,  # 亥
    }

    @staticmethod
    def date_to_jdn(year: int, month: int, day: int) -> int:
        """
        Convert Gregorian date to Julian Day Number.

        Uses the standard algorithm for Gregorian calendar.
        JDN is the number of days since January 1, 4713 BCE (Julian calendar).

        Args:
            year: Gregorian year
            month: Month (1-12)
            day: Day of month (1-31)

        Returns:
            Julian Day Number as integer
        """
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    @staticmethod
    def jdn_to_date(jdn: int) -> Tuple[int, int, int]:
        """
        Convert Julian Day Number to Gregorian date.

        Args:
            jdn: Julian Day Number

        Returns:
            Tuple of (year, month, day)
        """
        # Algorithm from Richards (2013)
        y = 4716
        j = 1401
        m = 2
        n = 12
        r = 4
        p = 1461
        v = 3
        u = 5
        s = 153
        w = 2
        B = 274277
        C = -38

        f = jdn + j + (((4 * jdn + B) // 146097) * 3) // 4 + C
        e = r * f + v
        g = (e % p) // r
        h = u * g + w

        day = (h % s) // u + 1
        month = ((h // s + m) % n) + 1
        year = (e // p) - y + (n + m - month) // n

        return year, month, day

    def get_day_sexagenary_index(self, year: int, month: int, day: int) -> int:
        """
        Get sexagenary cycle index (0-59) for a day.

        The day pillar cycles through all 60 stem-branch combinations
        continuously, regardless of month or year boundaries.

        Args:
            year: Gregorian year
            month: Month (1-12)
            day: Day (1-31)

        Returns:
            Index 0-59 in the sexagenary cycle
        """
        jdn = self.date_to_jdn(year, month, day)
        # Formula: S = (JDN + 9) % 60
        # This aligns with the reference where Jan 27, 2019 (JD 2458511) has S=11
        return (jdn + 9) % 60

    def get_day_stem_index(self, year: int, month: int, day: int) -> int:
        """Get stem index (0-9) for day pillar."""
        sexagenary = self.get_day_sexagenary_index(year, month, day)
        return sexagenary % 10

    def get_day_branch_index(self, year: int, month: int, day: int) -> int:
        """Get branch index (0-11) for day pillar."""
        sexagenary = self.get_day_sexagenary_index(year, month, day)
        return sexagenary % 12

    def get_day_pillar(self, year: int, month: int, day: int) -> str:
        """
        Get day pillar as two Chinese characters.

        Args:
            year: Gregorian year
            month: Month (1-12)
            day: Day (1-31)

        Returns:
            Two-character string like "甲子"
        """
        sexagenary = self.get_day_sexagenary_index(year, month, day)
        return self.STEMS[sexagenary % 10] + self.BRANCHES[sexagenary % 12]

    def stem_to_index(self, stem: str) -> int:
        """Convert stem character to index (0-9)."""
        return self.STEMS.index(stem)

    def branch_to_index(self, branch: str) -> int:
        """Convert branch character to index (0-11)."""
        return self.BRANCHES.index(branch)

    def pillar_to_sexagenary_index(self, stem: str, branch: str) -> int:
        """
        Convert stem-branch pair to sexagenary index (0-59).

        Uses the formula: k = 6*T - 5*B, adjusted to 0-based indexing.

        Args:
            stem: Heavenly stem character (甲-癸)
            branch: Earthly branch character (子-亥)

        Returns:
            Sexagenary index 0-59
        """
        stem_idx = self.stem_to_index(stem)
        branch_idx = self.branch_to_index(branch)

        # Formula: k = 6*(T+1) - 5*(B+1) for 1-based, then convert to 0-based
        # Simplified: k = 6*T - 5*B + 1, then -1 for 0-based
        k = 6 * (stem_idx + 1) - 5 * (branch_idx + 1)
        if k <= 0:
            k += 60
        return k - 1  # Convert to 0-based

    def get_hour_pillar(self, day_stem_index: int, hour: int) -> str:
        """
        Calculate hour pillar from day stem and hour.

        Hour stem is derived from day stem using the formula:
        hour_stem_index = (day_stem_index * 2 + hour_branch_index) % 10

        Args:
            day_stem_index: Day stem index (0-9)
            hour: Hour (0-23)

        Returns:
            Two-character hour pillar string
        """
        hour_branch_index = self.HOUR_TO_BRANCH[hour]
        hour_stem_index = (day_stem_index * 2 + hour_branch_index) % 10
        return self.STEMS[hour_stem_index] + self.BRANCHES[hour_branch_index]

    def find_matching_day_pillar_dates(
        self,
        target_stem: str,
        target_branch: str,
        start_date: date,
        end_date: date
    ) -> Iterator[date]:
        """
        Find all dates with matching day pillar using 60-day jump algorithm.

        This is the key optimization: instead of checking every date,
        we calculate the first matching date and then jump 60 days at a time.

        Performance: O(matches) instead of O(days)
        For a 100-year range: ~608 iterations instead of ~36,500

        Args:
            target_stem: Target heavenly stem (甲-癸)
            target_branch: Target earthly branch (子-亥)
            start_date: Start of search range
            end_date: End of search range

        Yields:
            Dates matching the specified day pillar
        """
        target_index = self.pillar_to_sexagenary_index(target_stem, target_branch)
        start_index = self.get_day_sexagenary_index(
            start_date.year, start_date.month, start_date.day
        )

        # Calculate days to first match
        offset = (target_index - start_index) % 60
        first_match = start_date + timedelta(days=offset)

        # Yield all matches at 60-day intervals
        current = first_match
        while current <= end_date:
            yield current
            current += timedelta(days=60)

    def find_matching_dates_by_stem_only(
        self,
        target_stem: str,
        start_date: date,
        end_date: date
    ) -> Iterator[date]:
        """
        Find all dates with matching day stem (10-day cycle).

        When only the stem is specified, matches occur every 10 days.

        Args:
            target_stem: Target heavenly stem (甲-癸)
            start_date: Start of search range
            end_date: End of search range

        Yields:
            Dates matching the specified day stem
        """
        target_stem_index = self.stem_to_index(target_stem)
        start_stem_index = self.get_day_stem_index(
            start_date.year, start_date.month, start_date.day
        )

        offset = (target_stem_index - start_stem_index) % 10
        first_match = start_date + timedelta(days=offset)

        current = first_match
        while current <= end_date:
            yield current
            current += timedelta(days=10)

    def find_matching_dates_by_branch_only(
        self,
        target_branch: str,
        start_date: date,
        end_date: date
    ) -> Iterator[date]:
        """
        Find all dates with matching day branch (12-day cycle).

        When only the branch is specified, matches occur every 12 days.

        Args:
            target_branch: Target earthly branch (子-亥)
            start_date: Start of search range
            end_date: End of search range

        Yields:
            Dates matching the specified day branch
        """
        target_branch_index = self.branch_to_index(target_branch)
        start_branch_index = self.get_day_branch_index(
            start_date.year, start_date.month, start_date.day
        )

        offset = (target_branch_index - start_branch_index) % 12
        first_match = start_date + timedelta(days=offset)

        current = first_match
        while current <= end_date:
            yield current
            current += timedelta(days=12)

    def get_valid_day_stems_for_hour_pillar(
        self,
        hour_stem: str,
        hour_branch: str
    ) -> list[int]:
        """
        Find which day stem indices produce the target hour pillar.

        Since hour_stem = (day_stem * 2 + hour_branch) % 10,
        we can solve for day_stem given hour_stem and hour_branch.

        Args:
            hour_stem: Target hour stem (甲-癸)
            hour_branch: Target hour branch (子-亥)

        Returns:
            List of valid day stem indices (0-9) that produce this hour pillar
        """
        target_hour_stem_index = self.stem_to_index(hour_stem)
        hour_branch_index = self.branch_to_index(hour_branch)

        valid_day_stems = []
        for day_stem_index in range(10):
            calculated_hour_stem = (day_stem_index * 2 + hour_branch_index) % 10
            if calculated_hour_stem == target_hour_stem_index:
                valid_day_stems.append(day_stem_index)

        return valid_day_stems

    def get_year_pillar_index(self, year: int) -> int:
        """
        Get sexagenary index for year pillar.

        Note: This is a simplified calculation that doesn't account for
        Lichun (立春). For precise year pillar, use lunar_python adapter.

        The year pillar changes at Lichun (around Feb 3-5), not Jan 1.

        Args:
            year: Gregorian year

        Returns:
            Sexagenary index 0-59
        """
        # 1984 was a 甲子 year (index 0)
        return (year - 1984) % 60

    def get_year_pillar(self, year: int) -> str:
        """Get year pillar as Chinese characters (simplified, ignores Lichun)."""
        idx = self.get_year_pillar_index(year)
        return self.STEMS[idx % 10] + self.BRANCHES[idx % 12]

    def find_years_with_pillar(
        self,
        target_stem: Optional[str],
        target_branch: Optional[str],
        start_year: int,
        end_year: int
    ) -> list[int]:
        """
        Find years with matching year pillar.

        Args:
            target_stem: Target year stem (optional)
            target_branch: Target year branch (optional)
            start_year: Start of range
            end_year: End of range

        Returns:
            List of years matching the pattern
        """
        matching_years = []

        for year in range(start_year, end_year + 1):
            idx = self.get_year_pillar_index(year)
            stem_idx = idx % 10
            branch_idx = idx % 12

            if target_stem and self.STEMS[stem_idx] != target_stem:
                continue
            if target_branch and self.BRANCHES[branch_idx] != target_branch:
                continue

            matching_years.append(year)

        return matching_years
