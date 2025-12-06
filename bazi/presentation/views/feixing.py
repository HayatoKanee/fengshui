"""
FeiXing (Flying Star) Views.

Views for FeiXing/Flying Star Feng Shui calculations.
Flying Star is a system of Feng Shui that analyzes energy patterns
in buildings based on the 9 Star Ki system.
"""
from django.shortcuts import render

from bazi.infrastructure.di import get_container


def feixing_view(request):
    """
    Flying Star (FeiXing) calculation view.

    Generates Flying Star grids for all 24 mountain directions,
    showing the distribution of stars in the Lo Shu grid configuration.

    The Flying Star system uses a 3x3 grid (Lo Shu) with numbers 1-9,
    where each number represents a "star" with specific characteristics.
    The center star rotates through the grid based on time periods.

    Query Parameters:
        center (int): The center star number (1-9), defaults to 9

    Template: feixing.html

    Context:
        main_center: The center star number (string)
        table_data: List of grid configurations for each mountain direction,
                   containing:
                   - main_grid: The main Lo Shu grid in Chinese numerals
                   - star: Primary mountain direction
                   - second_star: Secondary mountain direction (if identical grid)
                   - grid_star: Mountain star distribution
                   - grid_opposite_star: Facing star distribution
    """
    center_param = request.GET.get("center", "9")
    try:
        main_center = int(center_param)
    except ValueError:
        main_center = 9

    # Get service from DI container
    container = get_container()
    table_data = container.feixing_service.generate_flying_star_charts(main_center)

    context = {
        'main_center': str(main_center),
        'table_data': table_data,
    }
    return render(request, 'feixing.html', context)
