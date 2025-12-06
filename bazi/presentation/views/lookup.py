"""
BaZi Lookup Views.

Views for BaZi pattern lookup and date searching functionality.
These views handle searching for solar dates matching given BaZi patterns
and finding auspicious dates from pre-calculated CSV files.

Uses DI container for all infrastructure access (DIP-compliant).
"""
import csv
import datetime
import os

from django.contrib import messages
from django.shortcuts import redirect, render

from fengshui import settings
from bazi.infrastructure.di import get_container


def bazi_lookup_view(request):
    """
    BaZi to Solar lookup - find all dates matching a given BaZi pattern.

    Allows users to search for solar calendar dates that match specific
    BaZi (Four Pillars) patterns. Users can specify any combination of
    Heavenly Stems and Earthly Branches for each pillar.

    Template: bazi_lookup.html

    Context:
        data: List of matching dates with their BaZi representations
        target_bazi: The BaZi pattern being searched for
        start_year: Search range start
        end_year: Search range end
        tiangan: List of 10 Heavenly Stems
        dizhi: List of 12 Earthly Branches
        total_matches: Count of matching dates found
    """
    data = []
    target_bazi = ''
    start_year = datetime.datetime.now().year
    end_year = start_year + 100

    # 天干 (10 Heavenly Stems) and 地支 (12 Earthly Branches)
    tiangan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

    if request.method == 'POST':
        # Get the 8 individual characters from form
        year_gan = request.POST.get('year_gan', '').strip()
        year_zhi = request.POST.get('year_zhi', '').strip()
        month_gan = request.POST.get('month_gan', '').strip()
        month_zhi = request.POST.get('month_zhi', '').strip()
        day_gan = request.POST.get('day_gan', '').strip()
        day_zhi = request.POST.get('day_zhi', '').strip()
        hour_gan = request.POST.get('hour_gan', '').strip()
        hour_zhi = request.POST.get('hour_zhi', '').strip()

        start_year = int(request.POST.get('start_year', start_year))
        end_year = int(request.POST.get('end_year', end_year))

        # Validate year range
        if end_year - start_year > 2000:
            messages.warning(request, '搜索范围最多2000年')
            end_year = start_year + 2000

        if start_year > end_year:
            messages.warning(request, '开始年份不能晚于结束年份')
            return redirect('bazi_lookup')

        # Build target BaZi pattern from individual characters (display order: 时 日 月 年)
        year_pillar = year_gan + year_zhi if (year_gan or year_zhi) else ''
        month_pillar = month_gan + month_zhi if (month_gan or month_zhi) else ''
        day_pillar = day_gan + day_zhi if (day_gan or day_zhi) else ''
        hour_pillar = hour_gan + hour_zhi if (hour_gan or hour_zhi) else ''
        target_bazi = f"{hour_pillar} {day_pillar} {month_pillar} {year_pillar}"

        # Check if at least one search criterion is provided
        has_criteria = any([year_gan, year_zhi, month_gan, month_zhi,
                           day_gan, day_zhi, hour_gan, hour_zhi])

        if not has_criteria:
            messages.warning(request, '请至少选择一个八字字符进行搜索')
        else:
            container = get_container()
            data = _search_matching_dates(
                start_year, end_year,
                year_gan, year_zhi, month_gan, month_zhi,
                day_gan, day_zhi, hour_gan, hour_zhi,
                request,
                container
            )

            if not data:
                messages.info(request, f'在 {start_year}-{end_year} 年间未找到匹配的八字')

    return render(request, 'bazi_lookup.html', {
        'data': data,
        'target_bazi': target_bazi,
        'start_year': start_year,
        'end_year': end_year,
        'tiangan': tiangan,
        'dizhi': dizhi,
        'total_matches': len(data)
    })


def _search_matching_dates(
    start_year: int,
    end_year: int,
    year_gan: str,
    year_zhi: str,
    month_gan: str,
    month_zhi: str,
    day_gan: str,
    day_zhi: str,
    hour_gan: str,
    hour_zhi: str,
    request,
    container
) -> list:
    """
    Search for dates matching the given BaZi pattern.

    Iterates through all dates in the specified year range, checking
    each hour period for matching BaZi pillars.

    Uses container for DI-compliant access to lunar adapter (DIP-compliant).

    Args:
        start_year: Beginning of search range
        end_year: End of search range
        year_gan: Target year Heavenly Stem (optional)
        year_zhi: Target year Earthly Branch (optional)
        month_gan: Target month Heavenly Stem (optional)
        month_zhi: Target month Earthly Branch (optional)
        day_gan: Target day Heavenly Stem (optional)
        day_zhi: Target day Earthly Branch (optional)
        hour_gan: Target hour Heavenly Stem (optional)
        hour_zhi: Target hour Earthly Branch (optional)
        request: Django request for warning messages
        container: DI container for service access

    Returns:
        List of dictionaries containing matching dates with their BaZi
    """
    data = []
    # Chinese hour periods: 子(23-1), 丑(1-3), 寅(3-5), 卯(5-7), 辰(7-9), 巳(9-11),
    #                       午(11-13), 未(13-15), 申(15-17), 酉(17-19), 戌(19-21), 亥(21-23)
    hours = [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    max_results = 10000  # Limit results to prevent memory issues

    for year in range(start_year, end_year + 1):
        if len(data) >= max_results:
            messages.warning(request, f'结果过多，只显示前 {max_results} 个匹配')
            break

        for month in range(1, 13):
            if len(data) >= max_results:
                break

            days_in_month = _get_days_in_month(year, month)

            for day in range(1, days_in_month + 1):
                if len(data) >= max_results:
                    break

                for hour in hours:
                    if len(data) >= max_results:
                        break

                    match_result = _check_bazi_match(
                        year, month, day, hour,
                        year_gan, year_zhi, month_gan, month_zhi,
                        day_gan, day_zhi, hour_gan, hour_zhi,
                        container
                    )
                    if match_result:
                        data.append(match_result)

    return data


def _get_days_in_month(year: int, month: int) -> int:
    """Calculate the number of days in a given month."""
    if month == 12:
        last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
    return last_day.day


def _check_bazi_match(
    year: int,
    month: int,
    day: int,
    hour: int,
    year_gan: str,
    year_zhi: str,
    month_gan: str,
    month_zhi: str,
    day_gan: str,
    day_zhi: str,
    hour_gan: str,
    hour_zhi: str,
    container
) -> dict | None:
    """
    Check if a specific date/time matches the given BaZi pattern.

    Uses container for DI-compliant access to lunar adapter (DIP-compliant).

    Returns:
        Dictionary with date info and BaZi if match, None otherwise
    """
    try:
        # Get BaZi via LunarPort (DIP-compliant)
        lunar, bazi = container.lunar_adapter.get_raw_lunar_and_bazi(
            year, month, day, hour, 0
        )

        bazi_str = bazi.toString()
        bazi_parts = bazi_str.split()

        # Check each character individually
        is_match = True

        # Year pillar check (bazi_parts[0])
        if year_gan and bazi_parts[0][0] != year_gan:
            is_match = False
        if year_zhi and bazi_parts[0][1] != year_zhi:
            is_match = False

        # Month pillar check (bazi_parts[1])
        if is_match and month_gan and bazi_parts[1][0] != month_gan:
            is_match = False
        if is_match and month_zhi and bazi_parts[1][1] != month_zhi:
            is_match = False

        # Day pillar check (bazi_parts[2])
        if is_match and day_gan and bazi_parts[2][0] != day_gan:
            is_match = False
        if is_match and day_zhi and bazi_parts[2][1] != day_zhi:
            is_match = False

        # Hour pillar check (bazi_parts[3])
        if is_match and hour_gan and bazi_parts[3][0] != hour_gan:
            is_match = False
        if is_match and hour_zhi and bazi_parts[3][1] != hour_zhi:
            is_match = False

        if is_match:
            # Reverse bazi order for display: 年月日时 -> 时日月年
            bazi_display = ' '.join(reversed(bazi_parts))
            return {
                'year': year,
                'month': month,
                'day': day,
                'hour': hour,
                'bazi': bazi_display
            }
    except Exception:
        # Skip invalid dates
        pass

    return None


def zeri_view(request):
    """
    Auspicious date finder - search for pre-calculated good BaZi dates.

    Searches through CSV files containing pre-calculated auspicious dates
    to find dates within the user's specified range.

    Template: zeri.html

    Context:
        data: List of auspicious datetime objects within range
        from_date: Search range start (str)
        to_date: Search range end (str)
    """
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d')
        to_date = datetime.datetime.strptime(to_date_str, '%Y-%m-%d')

        if from_date > to_date:
            messages.warning(request, '开始日子不能晚于结束日子。')
            return redirect('zeri')

        data = _load_auspicious_dates(from_date, to_date)
        return render(request, 'zeri.html', {
            'data': data,
            'from_date': from_date_str,
            'to_date': to_date_str
        })

    return render(request, 'zeri.html')


def _load_auspicious_dates(from_date: datetime.datetime, to_date: datetime.datetime) -> list:
    """
    Load auspicious dates from CSV files within the specified date range.

    Searches through yearly CSV files (good_bazis_{year}.csv) to find
    all pre-calculated auspicious dates within the given range.

    Args:
        from_date: Start of date range
        to_date: End of date range

    Returns:
        List of datetime objects representing auspicious dates
    """
    data = []

    # Search years with padding for edge cases
    for year in range(from_date.year - 1, to_date.year + 2):
        csv_file_path = os.path.join(settings.DATA_DIR, f'good_bazis_{year}.csv')
        try:
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    date = f'{row[0]} {row[1]} {row[2]} {row[3]}'
                    # Assuming format: year month day hour
                    data_date = datetime.datetime.strptime(date, '%Y %m %d %H')
                    if from_date <= data_date <= to_date:
                        data.append(data_date)
        except FileNotFoundError:
            continue

    return data
