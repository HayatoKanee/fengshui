#!/usr/bin/env python3
"""
Standalone script to run BaZi probability experiment.
Run with: python run_bazi_experiment.py
"""

import os
import csv
import statistics
from collections import Counter
from lunar_python import Lunar

# Set data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def bazi_probability_experiment(start_year, end_year):
    """
    Analyze BaZi distribution over a range of years.
    Outputs CSV with frequency counts and statistical summary.
    """
    bazi_counter = Counter()
    day_pillar_counter = Counter()  # Just 日柱
    total_hours = 0

    print(f'Starting BaZi probability experiment: {start_year} to {end_year}')

    for year in range(start_year, end_year + 1):
        lunar = Lunar.fromYmdHms(year, 1, 1, 0, 0, 0)

        while lunar.getYear() == year:
            # Check all 12 时辰 (hours: 0, 1, 3, 5, ..., 21, 23)
            for hour in [0] + list(range(1, 23, 2)) + [23]:
                bazi = Lunar.fromYmdHms(
                    year, lunar.getMonth(), lunar.getDay(), hour, 0, 0
                ).getEightChar()

                bazi_str = bazi.toString()  # Full 八字: "甲子 乙丑 丙寅 丁卯"
                bazi_counter[bazi_str] += 1

                # Extract day pillar (日柱) - 3rd element
                day_pillar = bazi_str.split()[2]
                day_pillar_counter[day_pillar] += 1

                total_hours += 1

            # Move to next day
            i = 1
            next_lunar = lunar.next(i)
            while next_lunar.toString() == lunar.toString():
                i += 1
                next_lunar = lunar.next(i)
            if next_lunar.getMonth() < lunar.getMonth():
                break
            lunar = next_lunar

        if year % 100 == 0:
            print(f'Processed year {year}')

    print(f'Finished processing. Total hours: {total_hours}')

    # Output full BaZi CSV
    full_bazi_path = os.path.join(DATA_DIR, f"bazi_probability_{start_year}_{end_year}.csv")
    with open(full_bazi_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['bazi', 'count', 'percentage'])
        for bazi, count in bazi_counter.most_common():
            percentage = (count / total_hours) * 100
            writer.writerow([bazi, count, f'{percentage:.6f}'])

    # Output day pillar CSV
    day_pillar_path = os.path.join(DATA_DIR, f"day_pillar_probability_{start_year}_{end_year}.csv")
    with open(day_pillar_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['day_pillar', 'count', 'percentage'])
        for pillar, count in day_pillar_counter.most_common():
            percentage = (count / total_hours) * 100
            writer.writerow([pillar, count, f'{percentage:.6f}'])

    # Calculate statistics
    counts = list(bazi_counter.values())
    day_counts = list(day_pillar_counter.values())

    stats = {
        'total_hours': total_hours,
        'unique_bazi': len(bazi_counter),
        'unique_day_pillars': len(day_pillar_counter),
        'full_bazi': {
            'mean': statistics.mean(counts),
            'median': statistics.median(counts),
            'stdev': statistics.stdev(counts) if len(counts) > 1 else 0,
            'min': min(counts),
            'max': max(counts),
            'most_common': bazi_counter.most_common(10),
            'least_common': bazi_counter.most_common()[-10:],
        },
        'day_pillar': {
            'mean': statistics.mean(day_counts),
            'median': statistics.median(day_counts),
            'stdev': statistics.stdev(day_counts) if len(day_counts) > 1 else 0,
            'min': min(day_counts),
            'max': max(day_counts),
            'most_common': day_pillar_counter.most_common(10),
            'least_common': day_pillar_counter.most_common()[-10:],
        }
    }

    # Output summary
    summary_path = os.path.join(DATA_DIR, f"bazi_probability_summary_{start_year}_{end_year}.txt")
    with open(summary_path, "w", encoding='utf-8') as f:
        f.write(f"BaZi Probability Experiment: {start_year} - {end_year}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Total hours analyzed: {total_hours:,}\n")
        f.write(f"Unique full BaZi combinations: {len(bazi_counter):,}\n")
        f.write(f"Unique day pillars: {len(day_pillar_counter)}\n\n")

        f.write(f"Full BaZi Statistics:\n")
        f.write(f"  Mean count: {stats['full_bazi']['mean']:.2f}\n")
        f.write(f"  Median count: {stats['full_bazi']['median']:.2f}\n")
        f.write(f"  Std deviation: {stats['full_bazi']['stdev']:.2f}\n")
        f.write(f"  Min count: {stats['full_bazi']['min']}\n")
        f.write(f"  Max count: {stats['full_bazi']['max']}\n")
        f.write(f"  Ratio (max/min): {stats['full_bazi']['max']/stats['full_bazi']['min']:.2f}\n\n")

        f.write(f"Top 10 Most Common BaZi:\n")
        for bazi, count in stats['full_bazi']['most_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {bazi}: {count:,} ({pct:.4f}%)\n")

        f.write(f"\nTop 10 Least Common BaZi:\n")
        for bazi, count in stats['full_bazi']['least_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {bazi}: {count:,} ({pct:.4f}%)\n")

        f.write(f"\nDay Pillar Statistics:\n")
        f.write(f"  Mean count: {stats['day_pillar']['mean']:.2f}\n")
        f.write(f"  Median count: {stats['day_pillar']['median']:.2f}\n")
        f.write(f"  Std deviation: {stats['day_pillar']['stdev']:.2f}\n")
        f.write(f"  Min count: {stats['day_pillar']['min']}\n")
        f.write(f"  Max count: {stats['day_pillar']['max']}\n")
        f.write(f"  Ratio (max/min): {stats['day_pillar']['max']/stats['day_pillar']['min']:.2f}\n\n")

        f.write(f"Top 10 Most Common Day Pillars:\n")
        for pillar, count in stats['day_pillar']['most_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {pillar}: {count:,} ({pct:.4f}%)\n")

        f.write(f"\nTop 10 Least Common Day Pillars:\n")
        for pillar, count in stats['day_pillar']['least_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {pillar}: {count:,} ({pct:.4f}%)\n")

    print(f"\nOutput files:")
    print(f"  Full BaZi CSV: {full_bazi_path}")
    print(f"  Day Pillar CSV: {day_pillar_path}")
    print(f"  Summary: {summary_path}")

    return stats


def bazi_to_solar(target_bazi, start_year, end_year, match_mode='full'):
    """
    Find all solar dates that match a given BaZi pattern.

    Args:
        target_bazi: BaZi pattern to search for, e.g.:
            - Full: "甲子 乙丑 丙寅 丁卯" (matches exact 4 pillars)
            - Day pillar only: "丙寅" (matches any with this day pillar)
            - Partial: "甲子 * * *" (matches year pillar only, * = wildcard)
        start_year: Start year (lunar)
        end_year: End year (lunar)
        match_mode: 'full' (exact match), 'day' (day pillar only), 'partial' (with wildcards)

    Returns:
        List of matching (solar_date, bazi) tuples
    """
    matches = []

    # Parse target based on mode
    if match_mode == 'day':
        target_day_pillar = target_bazi.strip()
    elif match_mode == 'partial':
        target_parts = target_bazi.split()

    print(f'Searching for BaZi: {target_bazi} ({match_mode} mode)')
    print(f'Range: {start_year} to {end_year}')

    for year in range(start_year, end_year + 1):
        lunar = Lunar.fromYmdHms(year, 1, 1, 0, 0, 0)

        while lunar.getYear() == year:
            for hour in [0] + list(range(1, 23, 2)) + [23]:
                bazi = Lunar.fromYmdHms(
                    year, lunar.getMonth(), lunar.getDay(), hour, 0, 0
                ).getEightChar()

                bazi_str = bazi.toString()
                solar = lunar.getSolar()

                is_match = False

                if match_mode == 'full':
                    is_match = (bazi_str == target_bazi)
                elif match_mode == 'day':
                    day_pillar = bazi_str.split()[2]
                    is_match = (day_pillar == target_day_pillar)
                elif match_mode == 'partial':
                    bazi_parts = bazi_str.split()
                    is_match = True
                    for i, (target, actual) in enumerate(zip(target_parts, bazi_parts)):
                        if target != '*' and target != actual:
                            is_match = False
                            break

                if is_match:
                    solar_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d} {hour:02d}:00"
                    matches.append((solar_str, bazi_str))

            # Move to next day
            i = 1
            next_lunar = lunar.next(i)
            while next_lunar.toString() == lunar.toString():
                i += 1
                next_lunar = lunar.next(i)
            if next_lunar.getMonth() < lunar.getMonth():
                break
            lunar = next_lunar

        if year % 100 == 0:
            print(f'Processed year {year}, found {len(matches)} matches so far')

    print(f'\nTotal matches found: {len(matches)}')

    # Output to CSV
    output_path = os.path.join(DATA_DIR, f"bazi_to_solar_{start_year}_{end_year}.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['solar_date', 'bazi'])
        for solar_date, bazi in matches:
            writer.writerow([solar_date, bazi])

    print(f'Results saved to: {output_path}')

    return matches


def print_usage():
    print("""
Usage:
  python run_bazi_experiment.py experiment [start_year] [end_year]
      Run probability experiment (default: 2025-4025)

  python run_bazi_experiment.py find <bazi> [start_year] [end_year] [mode]
      Find solar dates matching a BaZi pattern

      Modes:
        full    - Exact match of all 4 pillars (default)
        day     - Match day pillar only
        partial - Match with wildcards (* for any pillar)

      Examples:
        python run_bazi_experiment.py find "甲子 乙丑 丙寅 丁卯" 2025 2100
        python run_bazi_experiment.py find "丙寅" 2025 2100 day
        python run_bazi_experiment.py find "甲子 * * *" 2025 2100 partial
""")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == 'experiment':
        start = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
        end = int(sys.argv[3]) if len(sys.argv) > 3 else 4025

        print(f"Running experiment from {start} to {end}")
        stats = bazi_probability_experiment(start, end)

        print(f"\n=== Quick Summary ===")
        print(f"Total hours: {stats['total_hours']:,}")
        print(f"Unique BaZi: {stats['unique_bazi']:,}")
        print(f"Max/Min ratio: {stats['full_bazi']['max']/stats['full_bazi']['min']:.2f}")

    elif command == 'find':
        if len(sys.argv) < 3:
            print("Error: BaZi pattern required")
            print_usage()
            sys.exit(1)

        target_bazi = sys.argv[2]
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 2025
        end = int(sys.argv[4]) if len(sys.argv) > 4 else 2100
        mode = sys.argv[5] if len(sys.argv) > 5 else 'full'

        matches = bazi_to_solar(target_bazi, start, end, mode)

        if matches:
            print(f"\nFirst 10 matches:")
            for solar_date, bazi in matches[:10]:
                print(f"  {solar_date} -> {bazi}")

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
