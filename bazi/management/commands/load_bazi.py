from django.core.management.base import BaseCommand

from bazi.utils.experiments import best_bazi_from_to


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Define command-line arguments
        parser.add_argument('start_year', type=int, help='The start year for processing Bazi data')
        parser.add_argument('end_year', type=int, help='The end year for processing Bazi data')

    def handle(self, *args, **options):
        start_year = options['start_year']
        end_year = options['end_year']

        if start_year > end_year:
            self.stdout.write(self.style.ERROR('Start year must be less than or equal to end year.'))
            return

        # Call the function with the specified years
        best_bazi_from_to(start_year, end_year)

        self.stdout.write(self.style.SUCCESS(f'Successfully processed Bazi data from {start_year} to {end_year}.'))
