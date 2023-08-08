from django.shortcuts import render
from .forms import BirthTimeForm
from lunar_python import Lunar, Solar, EightChar, JieQi


def wuxing_relationship(input_str):
    # Define the Wuxing relationships
    relationships = {
        '生': {
            '木': '火',
            '火': '土',
            '土': '金',
            '金': '水',
            '水': '木'
        },
        '克': {
            '火': '金',
            '水': '火',
            '土': '水',
            '木': '土',
            '金': '木'
        }
    }

    # Extract the two elements from the input string
    element1, element2 = input_str[0], input_str[1]

    # Check the relationship and return the corresponding values
    if element1 == element2:
        return 10, 10
    elif relationships['生'][element1] == element2:
        return 6, 8
    elif relationships['克'][element1] == element2:
        return 4, 2
    elif relationships['克'][element2] == element1:
        return 2, 4
    elif relationships['生'][element2] == element1:
        return 8, 6


def get_gan_wuxing(gan):
    gan_wuxing = {
        '甲': '木',
        '乙': '木',
        '丙': '火',
        '丁': '火',
        '戊': '土',
        '己': '土',
        '庚': '金',
        '辛': '金',
        '壬': '水',
        '癸': '水'
    }
    return gan_wuxing.get(gan)


def get_wang_xiang_value(wang_xiang):
    wang_xiang_value = {
        '旺': 1.2,
        '相': 1.2,
        '休': 1,
        '囚': 0.8,
        '死': 0.8
    }
    return wang_xiang_value.get(wang_xiang)


def get_total_gan_value(gan, init_gan_value, sheng_val, hao_val, wang_xiang, sheng_hao_relations):
    wuxing = get_gan_wuxing(gan)
    wang_xiang_val = get_wang_xiang_value(wang_xiang.get(wuxing))
    gan_value = init_gan_value * wang_xiang_val
    if wuxing in sheng_hao_relations['有利']:
        sheng_val += gan_value
    else:
        hao_val += gan_value
    return sheng_val, hao_val


def get_total_zhi_value(zhi, init_zhi_value, sheng_val, hao_val, wang_xiang,
                        sheng_hao_relations):
    hidden_gan_ratios = {
        '子': {'癸': 1},
        '丑': {'己': 0.5, '癸': 0.3, '辛': 0.2},
        '寅': {'甲': 0.6, '丙': 0.3, '戊': 0.1},
        '卯': {'乙': 1},
        '辰': {'戊': 0.5, '乙': 0.3, '癸': 0.2},
        '巳': {'丙': 0.6, '戊': 0.3, '庚': 0.1},
        '午': {'丁': 0.5, '己': 0.5},
        '未': {'乙': 0.2, '己': 0.5, '丁': 0.3},
        '申': {'庚': 0.6, '壬': 0.3, '戊': 0.1},
        '酉': {'辛': 1},
        '戌': {'戊': 0.5, '辛': 0.3, '丁': 0.2},
        '亥': {'壬': 0.7, '甲': 0.3}
    }

    hidden_gan = hidden_gan_ratios.get(zhi, {})
    for gan, ratio in hidden_gan.items():
        wuxing = get_gan_wuxing(gan)
        wang_xiang_val = get_wang_xiang_value(wang_xiang.get(wuxing))
        zhi_value = init_zhi_value * ratio * wang_xiang_val
        if wuxing in sheng_hao_relations['有利']:
            sheng_val += zhi_value
        else:
            hao_val += zhi_value
    return sheng_val, hao_val


def get_wang_xiang(month_zhi, lunar):
    zhi_seasons = {
        '寅': '春',
        '卯': '春',
        '辰': '春',
        '巳': '夏',
        '午': '夏',
        '未': '夏',
        '申': '秋',
        '酉': '秋',
        '戌': '秋',
        '亥': '冬',
        '子': '冬',
        '丑': '冬'
    }
    season_phases = {
        '春': {'木': '旺', '火': '相', '水': '休', '金': '囚', '土': '死'},
        '夏': {'火': '旺', '土': '相', '木': '休', '水': '囚', '金': '死'},
        '秋': {'金': '旺', '水': '相', '土': '休', '火': '囚', '木': '死'},
        '冬': {'水': '旺', '木': '相', '金': '休', '土': '囚', '火': '死'},
    }
    season = zhi_seasons.get(month_zhi)
    if month_zhi in ['辰', '未', '戌', '丑']:
        if lunar.getNextJieQi(True).getSolar().subtract(lunar.getSolar()) <= 18:
            return {'土': '旺', '金': '相', '火': '休', '木': '囚', '水': '死'}
    return season_phases[season]


def get_relations(main_wuxing):
    wuxing_relations = {
        '木': {'有利': ['木', '水'], '不利': ['火', '土', '金']},
        '火': {'有利': ['火', '木'], '不利': ['土', '金', '水']},
        '土': {'有利': ['土', '火'], '不利': ['金', '水', '木']},
        '金': {'有利': ['金', '土'], '不利': ['水', '木', '火']},
        '水': {'有利': ['水', '金'], '不利': ['木', '火', '土']}
    }
    return wuxing_relations.get(main_wuxing, {})


def bazi_view(request):
    bazi = None
    if request.method == 'POST':

        form = BirthTimeForm(request.POST)
        if form.is_valid():
            solar_year = form.cleaned_data['year']
            solar_month = form.cleaned_data['month']
            solar_day = form.cleaned_data['day']
            solar_hour = form.cleaned_data['hour']
            solar_minute = form.cleaned_data['minute']
            solar = Solar.fromYmdHms(solar_year, solar_month, solar_day, solar_hour, solar_minute, 0)
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()
            main_wuxing = bazi.getDayWuXing()[0]
            sheng_hao_relations = get_relations(main_wuxing)
            sheng_value = 0
            hao_value = 0
            wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
            time_gan_value, time_zhi_value = wuxing_relationship(bazi.getTimeWuXing())
            sheng_value, hao_value = get_total_gan_value(bazi.getTimeGan(), time_gan_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            sheng_value, hao_value = get_total_zhi_value(bazi.getTimeZhi(), time_zhi_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            day_gan_value, day_zhi_value = wuxing_relationship(bazi.getDayWuXing())
            sheng_value, hao_value = get_total_gan_value(bazi.getDayGan(), day_gan_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            sheng_value, hao_value = get_total_zhi_value(bazi.getDayZhi(), day_zhi_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            month_gan_value, month_zhi_value = wuxing_relationship(bazi.getMonthWuXing())
            sheng_value, hao_value = get_total_gan_value(bazi.getMonthGan(), month_gan_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            sheng_value, hao_value = get_total_zhi_value(bazi.getMonthZhi(), month_zhi_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            year_gan_value, year_zhi_value = wuxing_relationship(bazi.getYearWuXing())
            sheng_value, hao_value = get_total_gan_value(bazi.getYearGan(), year_gan_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            sheng_value, hao_value = get_total_zhi_value(bazi.getYearZhi(), year_zhi_value, sheng_value, hao_value,
                                                         wang_xiang, sheng_hao_relations)
            print(sheng_value, hao_value)
            print(f"{sheng_value/(sheng_value+hao_value)*100:.2f}%", f"{hao_value/(sheng_value+hao_value)*100:.2f}%")
    else:
        form = BirthTimeForm()

    return render(request, 'bazi.html', {'form': form, 'bazi': bazi})
