"""
BaZi Research and Experiment Utilities.

Contains functions for generating "good BaZi" dates and running
probability experiments. These are research/utility functions
used by management commands and standalone scripts.
"""
from __future__ import annotations

import csv
import os
from typing import TYPE_CHECKING, List

from lunar_python import Lunar, EightChar

from bazi.domain.constants import (
    GAN_XIANG_CHONG,
    WU_BU_YU_SHI,
    GANZHI_WUXING,
    ZHI_XIANG_CHONG,
)
from fengshui.settings import DATA_DIR

if TYPE_CHECKING:
    pass


def best_bazi_from_to(start_year: int, end_year: int) -> None:
    """
    Generate "good BaZi" dates for a range of years.

    Outputs CSV files in DATA_DIR for each year containing dates
    that meet the criteria for a "good" BaZi.

    Args:
        start_year: First year to process
        end_year: Last year to process (inclusive)
    """
    for year in range(start_year, end_year + 1):
        print(f'processing year {year}')
        best_bazi_in_year(year)
        print(f'finish year {year}')


def best_bazi_in_year(year: int) -> None:
    """
    Generate "good BaZi" dates for a single year.

    Outputs a CSV file with all date-hour combinations that
    meet the criteria for a "good" BaZi.

    Args:
        year: The lunar year to process
    """
    lunar = Lunar.fromYmdHms(year, 1, 1, 0, 0, 0)
    file_path = os.path.join(DATA_DIR, f"good_bazis_{year}.csv")

    with open(file_path, "w", newline='') as csvfile:
        bazi_writer = csv.writer(csvfile)

        while lunar.getYear() == year:
            solar = lunar.getSolar()

            # Check hour 0 (子时 early)
            bazi_0 = Lunar.fromYmdHms(
                year, lunar.getMonth(), lunar.getDay(), 0, 0, 0
            ).getEightChar()
            if is_bazi_good(bazi_0, 0):
                bazi_writer.writerow([
                    solar.getYear(), solar.getMonth(), solar.getDay(), 0
                ])

            # Check odd hours (1, 3, 5, ..., 21)
            for hour in range(1, 23, 2):
                bazi = Lunar.fromYmdHms(
                    year, lunar.getMonth(), lunar.getDay(), hour, 0, 0
                ).getEightChar()
                if is_bazi_good(bazi, hour):
                    bazi_writer.writerow([
                        solar.getYear(), solar.getMonth(), solar.getDay(), hour
                    ])

            # Check hour 23 (子时 late)
            bazi_23 = Lunar.fromYmdHms(
                year, lunar.getMonth(), lunar.getDay(), 23, 0, 0
            ).getEightChar()
            if is_bazi_good(bazi_23, 23):
                bazi_writer.writerow([
                    solar.getYear(), solar.getMonth(), solar.getDay(), 23
                ])

            # Move to next day
            i = 1
            next_lunar = lunar.next(i)
            while next_lunar.toString() == lunar.toString():
                i += 1
                next_lunar = lunar.next(i)
            if next_lunar.getMonth() < lunar.getMonth():
                break
            lunar = next_lunar


def is_bazi_good(bazi: EightChar, hour: int) -> bool:
    """
    Determine if a BaZi meets the criteria for being "good".

    A "good" BaZi must:
    - Contain all five elements (五行俱全)
    - Not have 五不遇时 (Wu Bu Yu Shi)
    - Not have clashing stems (天干相冲)
    - Not have clashing branches (地支相冲)

    Args:
        bazi: The EightChar to evaluate
        hour: The hour (for 五不遇时 check)

    Returns:
        True if the BaZi is "good"
    """
    return (
        is_bazi_contain_all_wuxing(bazi)
        and not is_wu_bu_yu_shi_check(bazi, hour)
        and not tian_gan_or_di_zhi_xiang_chong(bazi, 0)
        and not tian_gan_or_di_zhi_xiang_chong(bazi, 1)
    )


def is_bazi_contain_all_wuxing(bazi: EightChar) -> bool:
    """
    Check if a BaZi contains all five elements.

    Args:
        bazi: The EightChar to check

    Returns:
        True if all five elements are present
    """
    wuxing_count = {'金': 0, '木': 0, '水': 0, '火': 0, '土': 0}

    for pillar in bazi.toString().split():
        for char in pillar:
            element = GANZHI_WUXING.get(char)
            if element:
                wuxing_count[element] += 1

    return all(count > 0 for count in wuxing_count.values())


def is_wu_bu_yu_shi_check(bazi: EightChar, hour: int) -> bool:
    """
    Check if a BaZi has 五不遇时 (Wu Bu Yu Shi).

    This is a taboo condition where the day stem and hour branch
    form an unfavorable combination.

    Args:
        bazi: The EightChar to check
        hour: The hour (for special 戊日子时 check)

    Returns:
        True if the condition is present (unfavorable)
    """
    if (bazi.getDayGan(), bazi.getTimeZhi()) in WU_BU_YU_SHI:
        return True

    # Special case: 戊日子时 after 23:00
    if bazi.getDayGan() == '戊' and bazi.getTimeZhi() == '子' and hour >= 23:
        return True

    return False


def tian_gan_or_di_zhi_xiang_chong(bazi: EightChar, check_gan: int = 0) -> bool:
    """
    Check if stems or branches clash within the BaZi.

    Args:
        bazi: The EightChar to check
        check_gan: 0 to check stems (天干), 1 to check branches (地支)

    Returns:
        True if there are clashing pairs
    """
    clashing_pairs = GAN_XIANG_CHONG if check_gan == 0 else ZHI_XIANG_CHONG
    chars = _get_gan_or_zhi(bazi, check_gan)

    for i in range(len(chars)):
        for j in range(i + 1, len(chars)):
            if (chars[i], chars[j]) in clashing_pairs:
                return True

    return False


def _get_gan_or_zhi(bazi: EightChar, get_gan: int = 0) -> List[str]:
    """
    Extract stems or branches from a BaZi.

    Args:
        bazi: The EightChar
        get_gan: 0 for stems, 1 for branches

    Returns:
        List of stem or branch characters
    """
    result = []
    for ganzhi in bazi.toString().split():
        result.append(ganzhi[get_gan])
    return result
