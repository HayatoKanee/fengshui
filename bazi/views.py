import datetime

from django.shortcuts import render
from .forms import BirthTimeForm
from lunar_python import Lunar, Solar, EightChar, JieQi
from .constants import gan_wuxing, gan_yinyang
from .helper import extract_form_data, get_relations, get_wang_xiang, calculate_values, \
    get_hidden_gans, calculate_wang_xiang_values, calculate_values_for_bazi, calculate_gan_liang_value, \
    accumulate_wuxing_values, calculate_shenghao, calculate_shenghao_percentage, calculate_shishen_for_bazi, \
    analyse_partner, get_day_gan_ratio, analyse_personality, analyse_liunian


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
                'personality': personality
            }
            return render(request, 'bazi.html', context)
    else:
        form = BirthTimeForm()

    return render(request, 'bazi.html', {'form': form, 'current_year': current_year, 'years': years})
