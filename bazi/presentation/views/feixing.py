"""
FeiXing (Flying Star) Views.

Views for FeiXing/Flying Star Feng Shui calculations.
Flying Star is a system of Feng Shui that analyzes energy patterns
in buildings based on the 9 Star Ki system.
"""
from django.shortcuts import render

from bazi.feixing import (
    arabic_to_chinese,
    fixed_positions,
    generate_grid,
    get_flight,
    get_shift,
    mountains_24,
    rotate_outer_ring_by_steps,
    yuan_long_mapping,
)


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

    table_data = _build_flying_star_grids(main_center)

    context = {
        'main_center': str(main_center),
        'table_data': table_data,
    }
    return render(request, 'feixing.html', context)


def _build_flying_star_grids(main_center: int) -> list:
    """
    Build Flying Star grid configurations for all 24 mountain directions.

    The Flying Star system divides the compass into 24 mountains (directions),
    each 15 degrees wide. This function calculates the star distributions
    for each direction.

    Args:
        main_center: The center star number (1-9) for the main period

    Returns:
        List of grid configurations, each containing:
        - main_grid: Main Lo Shu grid in Chinese numerals
        - star: Primary mountain direction name
        - second_star: Secondary direction (if grids are identical)
        - grid_star: Mountain star grid
        - grid_opposite_star: Facing star grid

    Note:
        Identical grid configurations are merged to reduce redundancy,
        with the second direction stored in second_star.
    """
    table_data = []

    for star in mountains_24:
        pos = fixed_positions[star]
        # Generate a fresh main grid for each star
        main_grid = generate_grid(main_center, order='f')

        opp_coord = (2 - pos[0], 2 - pos[1])
        star_center = main_grid[pos[0]][pos[1]]
        opp_center = main_grid[opp_coord[0]][opp_coord[1]]
        second_star = None

        # Determine flight orders based on star_center (or opp_center if star_center == 5)
        if star_center != 5:
            order_main = get_flight(star_center, yuan_long_mapping[star])
            order_opp = 'r' if order_main == 'f' else 'f'
            grid_star = generate_grid(star_center, order_main)
            grid_opposite_star = generate_grid(opp_center, order_opp)
        else:
            # Use the opposite logic if star_center is 5
            order_main = get_flight(opp_center, yuan_long_mapping[star])
            order_opp = 'r' if order_main == 'f' else 'f'
            grid_star = generate_grid(star_center, order_opp)
            grid_opposite_star = generate_grid(opp_center, order_main)

        # Realign: Compute the shift (for outer ring) needed so that
        # star_center ends up in the bottom-center
        shift = get_shift(main_grid, star_center)

        # Apply the same shift to each grid
        main_grid = rotate_outer_ring_by_steps(main_grid, shift)
        grid_star = rotate_outer_ring_by_steps(grid_star, shift)
        grid_opposite_star = rotate_outer_ring_by_steps(grid_opposite_star, shift)

        # Convert the main grid to Chinese numerals
        main_grid_cn = [[arabic_to_chinese(n) for n in row] for row in main_grid]

        # Check for duplicate grid configurations
        found = _find_duplicate_grid(table_data, grid_star, grid_opposite_star)
        if found is not None:
            found['second_star'] = star
        else:
            table_data.append({
                'main_grid': main_grid_cn,
                'star': star,
                'second_star': second_star,
                'grid_star': grid_star,
                'grid_opposite_star': grid_opposite_star,
            })

    return table_data


def _find_duplicate_grid(table_data: list, grid_star: list, grid_opposite_star: list) -> dict | None:
    """
    Find an existing entry with identical grid configuration.

    Args:
        table_data: List of existing grid configurations
        grid_star: Mountain star grid to match
        grid_opposite_star: Facing star grid to match

    Returns:
        The matching entry if found, None otherwise
    """
    for existing in table_data:
        if (existing['grid_star'] == grid_star and
                existing['grid_opposite_star'] == grid_opposite_star):
            return existing
    return None
