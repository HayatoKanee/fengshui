from django.shortcuts import render
from .forms import BirthTimeForm
from lunar_python import Lunar, Solar, EightChar, JieQi

from .helper import extract_form_data, get_relations, get_wang_xiang, calculate_values, \
    get_hidden_gans, calculate_wang_xiang_values, calculate_wu_xing_for_bazi, calculate_gan_liang_value, \
    accumulate_wuxing_values, calculate_shenghao, calculate_shenghao_percentage


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


def bazi_view(request):
    if request.method == 'POST':

        form = BirthTimeForm(request.POST)
        if form.is_valid():
            data = extract_form_data(form)
            solar = Solar.fromYmdHms(data['year'], data['month'], data['day'], data['hour'], data['minute'], 0)
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()
            main_wuxing = bazi.getDayWuXing()[0]
            values = calculate_values(bazi)
            hidden_gans = get_hidden_gans(bazi)
            sheng_hao_relations = get_relations(main_wuxing)
            wuxing = calculate_wu_xing_for_bazi(bazi)
            wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
            wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
            gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
            shengxiao = lunar.getYearShengXiaoExact()
            wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
            sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
            sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
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
                'gan_liang_values': gan_liang_values,
                'wuxing_value': wuxing_value,
                'sheng_hao': sheng_hao,
                'sheng_hao_percentage': sheng_hao_percentage
            }
            return render(request, 'bazi.html', context)
    else:
        form = BirthTimeForm()

    return render(request, 'bazi.html', {'form': form})
