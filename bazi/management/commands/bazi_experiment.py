"""
BaZi Probability Experiment Management Command.

Analyzes BaZi distribution over a range of years and outputs statistics.
"""
import csv
import os
import statistics
from collections import Counter

from django.core.management.base import BaseCommand
from lunar_python import Lunar

from fengshui.settings import DATA_DIR


class Command(BaseCommand):
    """Run BaZi probability experiment over a range of years."""

    help = "Analyze BaZi distribution and output probability statistics"

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            "start_year",
            type=int,
            help="The start year for processing (lunar year)",
        )
        parser.add_argument(
            "end_year",
            type=int,
            help="The end year for processing (lunar year)",
        )

    def handle(self, *args, **options):
        """Execute the BaZi probability experiment."""
        start_year = options["start_year"]
        end_year = options["end_year"]

        if start_year > end_year:
            self.stdout.write(
                self.style.ERROR("Start year must be less than or equal to end year.")
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Starting BaZi probability experiment: {start_year} to {end_year}"
            )
        )

        bazi_counter = Counter()
        day_pillar_counter = Counter()
        total_hours = 0

        for year in range(start_year, end_year + 1):
            lunar = Lunar.fromYmdHms(year, 1, 1, 0, 0, 0)

            while lunar.getYear() == year:
                # Check all 12 时辰 (hours: 0, 1, 3, 5, ..., 21, 23)
                for hour in [0] + list(range(1, 23, 2)) + [23]:
                    bazi = Lunar.fromYmdHms(
                        year, lunar.getMonth(), lunar.getDay(), hour, 0, 0
                    ).getEightChar()

                    bazi_str = bazi.toString()
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
                self.stdout.write(f"Processed year {year}")

        self.stdout.write(f"Finished processing. Total hours: {total_hours}")

        # Output full BaZi CSV
        full_bazi_path = os.path.join(
            DATA_DIR, f"bazi_probability_{start_year}_{end_year}.csv"
        )
        with open(full_bazi_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["bazi", "count", "percentage"])
            for bazi, count in bazi_counter.most_common():
                percentage = (count / total_hours) * 100
                writer.writerow([bazi, count, f"{percentage:.6f}"])

        # Output day pillar CSV
        day_pillar_path = os.path.join(
            DATA_DIR, f"day_pillar_probability_{start_year}_{end_year}.csv"
        )
        with open(day_pillar_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["day_pillar", "count", "percentage"])
            for pillar, count in day_pillar_counter.most_common():
                percentage = (count / total_hours) * 100
                writer.writerow([pillar, count, f"{percentage:.6f}"])

        # Calculate statistics
        counts = list(bazi_counter.values())
        day_counts = list(day_pillar_counter.values())

        stats = {
            "total_hours": total_hours,
            "unique_bazi": len(bazi_counter),
            "unique_day_pillars": len(day_pillar_counter),
            "full_bazi": {
                "mean": statistics.mean(counts),
                "median": statistics.median(counts),
                "stdev": statistics.stdev(counts) if len(counts) > 1 else 0,
                "min": min(counts),
                "max": max(counts),
                "most_common": bazi_counter.most_common(10),
                "least_common": bazi_counter.most_common()[-10:],
            },
            "day_pillar": {
                "mean": statistics.mean(day_counts),
                "median": statistics.median(day_counts),
                "stdev": statistics.stdev(day_counts) if len(day_counts) > 1 else 0,
                "min": min(day_counts),
                "max": max(day_counts),
                "most_common": day_pillar_counter.most_common(10),
                "least_common": day_pillar_counter.most_common()[-10:],
            },
        }

        # Output summary
        summary_path = os.path.join(
            DATA_DIR, f"bazi_probability_summary_{start_year}_{end_year}.txt"
        )
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"BaZi Probability Experiment: {start_year} - {end_year}\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Total hours analyzed: {total_hours:,}\n")
            f.write(f"Unique full BaZi combinations: {len(bazi_counter):,}\n")
            f.write(f"Unique day pillars: {len(day_pillar_counter)}\n\n")

            f.write("Full BaZi Statistics:\n")
            f.write(f"  Mean count: {stats['full_bazi']['mean']:.2f}\n")
            f.write(f"  Median count: {stats['full_bazi']['median']:.2f}\n")
            f.write(f"  Std deviation: {stats['full_bazi']['stdev']:.2f}\n")
            f.write(f"  Min count: {stats['full_bazi']['min']}\n")
            f.write(f"  Max count: {stats['full_bazi']['max']}\n")
            f.write(
                f"  Ratio (max/min): "
                f"{stats['full_bazi']['max']/stats['full_bazi']['min']:.2f}\n\n"
            )

            f.write("Top 10 Most Common BaZi:\n")
            for bazi, count in stats["full_bazi"]["most_common"]:
                pct = (count / total_hours) * 100
                f.write(f"  {bazi}: {count:,} ({pct:.4f}%)\n")

            f.write("\nTop 10 Least Common BaZi:\n")
            for bazi, count in stats["full_bazi"]["least_common"]:
                pct = (count / total_hours) * 100
                f.write(f"  {bazi}: {count:,} ({pct:.4f}%)\n")

            f.write("\nDay Pillar Statistics:\n")
            f.write(f"  Mean count: {stats['day_pillar']['mean']:.2f}\n")
            f.write(f"  Median count: {stats['day_pillar']['median']:.2f}\n")
            f.write(f"  Std deviation: {stats['day_pillar']['stdev']:.2f}\n")
            f.write(f"  Min count: {stats['day_pillar']['min']}\n")
            f.write(f"  Max count: {stats['day_pillar']['max']}\n")
            f.write(
                f"  Ratio (max/min): "
                f"{stats['day_pillar']['max']/stats['day_pillar']['min']:.2f}\n\n"
            )

            f.write("Top 10 Most Common Day Pillars:\n")
            for pillar, count in stats["day_pillar"]["most_common"]:
                pct = (count / total_hours) * 100
                f.write(f"  {pillar}: {count:,} ({pct:.4f}%)\n")

            f.write("\nTop 10 Least Common Day Pillars:\n")
            for pillar, count in stats["day_pillar"]["least_common"]:
                pct = (count / total_hours) * 100
                f.write(f"  {pillar}: {count:,} ({pct:.4f}%)\n")

        self.stdout.write(self.style.SUCCESS("\nOutput files:"))
        self.stdout.write(f"  Full BaZi CSV: {full_bazi_path}")
        self.stdout.write(f"  Day Pillar CSV: {day_pillar_path}")
        self.stdout.write(f"  Summary: {summary_path}")

        self.stdout.write(self.style.SUCCESS("\n=== Quick Summary ==="))
        self.stdout.write(f"Total hours: {stats['total_hours']:,}")
        self.stdout.write(f"Unique BaZi: {stats['unique_bazi']:,}")
        self.stdout.write(
            f"Max/Min ratio: "
            f"{stats['full_bazi']['max']/stats['full_bazi']['min']:.2f}"
        )
