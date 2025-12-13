"""
BaZi Lookup Views.

Views for BaZi pattern lookup and date searching functionality.
These views handle searching for solar dates matching given BaZi patterns
and finding auspicious dates from pre-calculated CSV files.

Uses DI container for all infrastructure access (DIP-compliant).

Performance: Uses OptimizedBaziLookupService with 60-day jump algorithm
for dramatically improved lookup speed when day pillar is specified.
- Day pillar complete: 60x faster (60-day intervals)
- Day stem only: 10x faster (10-day cycle)
- Day branch only: 5x faster (12-day cycle)
"""
import csv
import datetime
import os

from django.contrib import messages
from django.shortcuts import redirect, render

from fengshui import settings
from bazi.infrastructure.di import get_container
from bazi.application.services.bazi_lookup_service import LookupCriteria


def bazi_lookup_view(request):
    """
    BaZi to Solar lookup - find all dates matching a given BaZi pattern.

    Allows users to search for solar calendar dates that match specific
    BaZi (Four Pillars) patterns. Users can specify any combination of
    Heavenly Stems and Earthly Branches for each pillar.

    Uses OptimizedBaziLookupService for dramatically improved performance
    when day pillar is specified (up to 60x faster).

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

        # Create lookup criteria
        criteria = LookupCriteria(
            year_gan=year_gan,
            year_zhi=year_zhi,
            month_gan=month_gan,
            month_zhi=month_zhi,
            day_gan=day_gan,
            day_zhi=day_zhi,
            hour_gan=hour_gan,
            hour_zhi=hour_zhi,
        )

        if not criteria.has_any_criteria:
            messages.warning(request, '请至少选择一个八字字符进行搜索')
        else:
            # Use optimized lookup service
            container = get_container()
            max_results = 10000

            results = container.bazi_lookup_service.search(
                criteria=criteria,
                start_year=start_year,
                end_year=end_year,
                max_results=max_results
            )

            # Convert LookupResult objects to dict format for template
            data = [
                {
                    'year': r.year,
                    'month': r.month,
                    'day': r.day,
                    'hour': r.hour,
                    'bazi': r.bazi
                }
                for r in results
            ]

            if len(data) >= max_results:
                messages.warning(request, f'结果过多，只显示前 {max_results} 个匹配')

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
