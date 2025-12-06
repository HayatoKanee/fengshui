"""
BaZi Lookup Management Command.

Find solar dates that match a given BaZi pattern.
"""
import csv
import os

from django.core.management.base import BaseCommand
from lunar_python import Lunar

from fengshui.settings import DATA_DIR


class Command(BaseCommand):
    """Find solar dates matching a BaZi pattern."""

    help = "Find all solar dates that match a given BaZi pattern"

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            "bazi_pattern",
            type=str,
            help=(
                'BaZi pattern to search for. Examples:\n'
                '  - Full: "甲子 乙丑 丙寅 丁卯" (exact match)\n'
                '  - Day pillar: "丙寅" (with --mode day)\n'
                '  - Partial: "甲子 * * *" (with --mode partial)'
            ),
        )
        parser.add_argument(
            "start_year",
            type=int,
            help="Start year for search (lunar year)",
        )
        parser.add_argument(
            "end_year",
            type=int,
            help="End year for search (lunar year)",
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["full", "day", "partial"],
            default="full",
            help=(
                "Match mode: "
                "'full' (exact match), "
                "'day' (day pillar only), "
                "'partial' (with * wildcards)"
            ),
        )

    def handle(self, *args, **options):
        """Execute the BaZi lookup."""
        target_bazi = options["bazi_pattern"]
        start_year = options["start_year"]
        end_year = options["end_year"]
        match_mode = options["mode"]

        if start_year > end_year:
            self.stdout.write(
                self.style.ERROR("Start year must be less than or equal to end year.")
            )
            return

        matches = []

        # Parse target based on mode
        if match_mode == "day":
            target_day_pillar = target_bazi.strip()
        elif match_mode == "partial":
            target_parts = target_bazi.split()

        self.stdout.write(
            self.style.NOTICE(f"Searching for BaZi: {target_bazi} ({match_mode} mode)")
        )
        self.stdout.write(f"Range: {start_year} to {end_year}")

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

                    if match_mode == "full":
                        is_match = bazi_str == target_bazi
                    elif match_mode == "day":
                        day_pillar = bazi_str.split()[2]
                        is_match = day_pillar == target_day_pillar
                    elif match_mode == "partial":
                        bazi_parts = bazi_str.split()
                        is_match = True
                        for target, actual in zip(target_parts, bazi_parts):
                            if target != "*" and target != actual:
                                is_match = False
                                break

                    if is_match:
                        solar_str = (
                            f"{solar.getYear()}-{solar.getMonth():02d}-"
                            f"{solar.getDay():02d} {hour:02d}:00"
                        )
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
                self.stdout.write(
                    f"Processed year {year}, found {len(matches)} matches so far"
                )

        self.stdout.write(f"\nTotal matches found: {len(matches)}")

        if matches:
            # Output to CSV
            safe_pattern = "".join(
                c if c.isalnum() or c in "_ " else "_" for c in target_bazi
            ).replace(" ", "_")
            output_path = os.path.join(
                DATA_DIR,
                f"bazi_lookup_{safe_pattern}_{start_year}_{end_year}.csv",
            )
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["solar_date", "bazi"])
                for solar_date, bazi in matches:
                    writer.writerow([solar_date, bazi])

            self.stdout.write(self.style.SUCCESS(f"Results saved to: {output_path}"))

            self.stdout.write("\nFirst 10 matches:")
            for solar_date, bazi in matches[:10]:
                self.stdout.write(f"  {solar_date} -> {bazi}")
        else:
            self.stdout.write(
                self.style.WARNING("No matches found for the given pattern.")
            )
