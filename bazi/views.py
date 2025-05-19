import csv
import datetime
import os

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from fengshui import settings
from .forms import BirthTimeForm
from lunar_python import Lunar, Solar, EightChar, JieQi
from .constants import gan_wuxing, gan_yinyang
from .helper import *
from .feixing import *

def home_view(request):
    return render(request, 'home.html')


def tiangan_view(request):
    return render(request, 'tiangan.html')


def yinyang_view(request):
    return render(request, 'yinyang.html')


def dizhi_view(request):
    return render(request, 'dizhi.html')


def ganzhi_view(request):
    return render(request, 'ganzhi.html')


def wuxing_view(request):
    return render(request, 'wuxing.html')


def introbazi_view(request):
    return render(request, 'introbazi.html')


def get_bazi_detail(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')
        hour = request.POST.get('hour')
        solar = Solar.fromYmdHms(int(year), int(month), int(day), int(hour), 0, 0)
        lunar = solar.getLunar()
        bazi = lunar.getEightChar()
        main_wuxing = bazi.getDayWuXing()[0]
        values = calculate_values(bazi)
        hidden_gans = get_hidden_gans(bazi)
        sheng_hao_relations = get_relations(main_wuxing)
        wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
        yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
        shishen = calculate_shishen_for_bazi(wuxing, yinyang)
        wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
        wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
        gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
        shengxiao = lunar.getYearShengXiaoExact()
        wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
        sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
        sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
        gui_ren = calculate_day_guiren(bazi)
        # year_gui_ren = calculate_year_guiren(bazi)
        tian_de = calculate_tian_de(bazi)
        yue_de = calculate_yue_de(bazi)
        wen_chang = calculate_wen_chang(bazi)
        lu_shen = calculate_lu_shen(bazi)
        # Get the shensha list using the new function
        shensha_list = get_shensha(bazi)

        context = {
            'bazi': bazi,
            'wuxing': wuxing,
            'wuxing_value': wuxing_value,
            'sheng_hao': sheng_hao,
            'sheng_hao_percentage': sheng_hao_percentage,
            'gui_ren': gui_ren,
            # 'year_gui_ren': year_gui_ren,
            'tian_de': tian_de,
            'yue_de': yue_de,
            'wen_chang': wen_chang,
            'lu_shen': lu_shen,
            'shensha_list': shensha_list  # Add shensha list to the context
        }
        html = render_to_string('partials/bazi_detail.html', context)
        return HttpResponse(html)
    return HttpResponse(status=404)


def zeri_view(request):
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d')
        to_date = datetime.datetime.strptime(to_date_str, '%Y-%m-%d')

        if from_date > to_date:
            messages.warning(request, '开始日子不能晚于结束日子。')
            return redirect('zeri')

        data = []
        for year in range(from_date.year - 1, to_date.year + 2):
            csv_file_path = os.path.join(settings.DATA_DIR, f'good_bazis_{year}.csv')
            try:
                with open(csv_file_path, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        date = f'{row[0]} {row[1]} {row[2]} {row[3]}'
                        data_date = datetime.datetime.strptime(date, '%Y %m %d %H')  # Assuming first column has date
                        if from_date <= data_date <= to_date:
                            data.append(data_date)
            except FileNotFoundError:
                continue
        return render(request, 'zeri.html', {'data': data, 'from_date': from_date_str, 'to_date': to_date_str})
    return render(request, 'zeri.html')


def bazi_view(request):
    current_year = datetime.datetime.now().year
    years = range(current_year - 20, current_year + 50)
    if request.method == 'POST':
        form = BirthTimeForm(request.POST)
        if form.is_valid():
            data = extract_form_data(form)
            selected_year = request.POST.get('liunian')
            is_male = request.POST.get('gender') == 'male'
            solar = Solar.fromYmdHms(data['year'], data['month'], data['day'], data['hour'], data['minute'], 0)
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()
            main_wuxing = bazi.getDayWuXing()[0]
            values = calculate_values(bazi)
            hidden_gans = get_hidden_gans(bazi)
            sheng_hao_relations = get_relations(main_wuxing)
            wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
            yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
            shishen = calculate_shishen_for_bazi(wuxing, yinyang)
            wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
            wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
            gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
            shengxiao = lunar.getYearShengXiaoExact()
            wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
            sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
            sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
            is_strong = sheng_hao[0] > sheng_hao[1]
            partner_analyst = analyse_partner(hidden_gans, shishen)
            personality = analyse_personality(bazi.getMonthZhi())
            liunian_analysis = analyse_liunian(bazi, shishen, selected_year, is_strong, is_male)
            # Get the shensha list using the new function
            shensha_list = get_shensha(bazi)
            
            context = {
                'form': form,
                'bazi': bazi,
                'values': values,
                'hidden_gans': hidden_gans,
                'main_wuxing': main_wuxing,
                'shengxiao': shengxiao,
                'wang_xiang': wang_xiang,
                'wang_xiang_values': wang_xiang_values,
                'wuxing': wuxing,
                'yinyang': yinyang,
                'shishen': shishen,
                'gan_liang_values': gan_liang_values,
                'wuxing_value': wuxing_value,
                'sheng_hao': sheng_hao,
                'sheng_hao_percentage': sheng_hao_percentage,
                'current_year': int(selected_year),
                'is_male': is_male,
                'partner_analyst': partner_analyst,
                'liunian_analysis': liunian_analysis,
                'years': years,
                'personality': personality,
                'shensha_list': shensha_list  # Now includes all the shensha calculated by the restructured system
            }
            return render(request, 'bazi.html', context)
    else:
        form = BirthTimeForm()

    return render(request, 'bazi.html', {'form': form, 'current_year': current_year, 'years': years})

def feixing_view(request):
    center_param = request.GET.get("center", "9")
    try:
        main_center = int(center_param)
    except ValueError:
        main_center = 9

    # Build table_data: one entry for each unique grid configuration.
    table_data = []
    for star in mountains_24:
        pos = fixed_positions[star]
        # Generate a fresh main grid for each star.
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
            # Use the opposite logic if star_center is 5.
            order_main = get_flight(opp_center, yuan_long_mapping[star])
            order_opp = 'r' if order_main == 'f' else 'f'
            grid_star = generate_grid(star_center, order_opp)
            grid_opposite_star = generate_grid(opp_center, order_main)

        # Realign: Compute the shift (for outer ring) needed so that star_center ends up in the bottom-center.
        shift = get_shift(main_grid, star_center)
        # Apply the same shift to each grid.
        main_grid = rotate_outer_ring_by_steps(main_grid, shift)
        grid_star = rotate_outer_ring_by_steps(grid_star, shift)
        grid_opposite_star = rotate_outer_ring_by_steps(grid_opposite_star, shift)
        # Convert the main grid to Chinese numerals.
        main_grid_cn = [[arabic_to_chinese(n) for n in row] for row in main_grid]

        # Instead of adding duplicate grid entries, check if an identical grid_star (and grid_opposite_star)
        # has already been added. If so, record this star as the second_star.
        found = False
        for existing in table_data:
            if existing['grid_star'] == grid_star and existing['grid_opposite_star'] == grid_opposite_star:
                existing['second_star'] = star
                found = True
                break

        if not found:
            table_data.append({
                'main_grid': main_grid_cn,
                'star': star,
                'second_star': second_star,
                'grid_star': grid_star,
                'grid_opposite_star': grid_opposite_star,
            })
    context = {
        'main_center': str(main_center),
        'table_data': table_data,
    }
    return render(request, 'feixing.html', context)

