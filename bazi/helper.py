import openai
import os
from bazi.constants import relationships, wang_xiang_value, gan_wuxing, hidden_gan_ratios, zhi_seasons, season_phases, \
    wuxing_relations, zhi_wuxing, gan_yinyang, peiou_xingge, tigang

openai.api_key = os.environ.get('OPENAI_API_KEY')
print(openai.api_key)


def wuxing_relationship(gan, zhi):
    element1, element2 = gan_wuxing.get(gan), zhi_wuxing.get(zhi)

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


def calculate_values(bazi):
    values = []
    for item in bazi.toString().split():
        gan_value, zhi_value = wuxing_relationship(item[0], item[1])
        values.append((gan_value, zhi_value))
    return values


def calculate_shenghao(wuxing_value, main_wuxing):
    total_beneficial = 0
    total_non_beneficial = 0
    relationship = wuxing_relations.get(main_wuxing)
    total_beneficial += sum(wuxing_value.get(beneficial, 0) for beneficial in relationship['有利'])
    total_non_beneficial += sum(wuxing_value.get(non_beneficial, 0) for non_beneficial in relationship['不利'])

    return total_beneficial, total_non_beneficial


def calculate_shenghao_percentage(sheng_value, hao_value):
    total_value = sheng_value + hao_value
    sheng_percentage = (sheng_value / total_value) * 100
    hao_percentage = (hao_value / total_value) * 100
    return sheng_percentage, hao_percentage


def get_hidden_gans(bazi):
    hidden_gans_list = []
    for item in bazi.toString().split():
        zhi = item[1]
        hidden_gans = hidden_gan_ratios.get(zhi, {})
        hidden_gans_list.append(hidden_gans)
    return hidden_gans_list


def get_wang_xiang(month_zhi, lunar):
    season = zhi_seasons.get(month_zhi)
    if month_zhi in ['辰', '未', '戌', '丑']:
        if lunar.getNextJieQi(True).getSolar().subtract(lunar.getSolar()) <= 18:
            return {'土': '旺', '金': '相', '火': '休', '木': '囚', '水': '死'}
    return season_phases[season]


def calculate_wang_xiang_values(bazi, wang_xiang):
    wang_xiang_values = []

    for item in bazi.toString().split():
        gan, zhi = item[0], item[1]

        # Calculate wang_xiang_value for gan
        wang_xiang_for_gan = wang_xiang.get(gan_wuxing.get(gan))
        wang_xiang_value_for_gan = wang_xiang_value.get(wang_xiang_for_gan)

        # Calculate wang_xiang_value for each hidden gan in zhi
        hidden_gans_for_zhi = hidden_gan_ratios.get(zhi)
        wang_xiang_values_for_zhi = []
        for hidden_gan in hidden_gans_for_zhi.keys():
            wang_xiang_for_hidden_gan = wang_xiang.get(gan_wuxing.get(hidden_gan))
            wang_xiang_value_for_hidden_gan = wang_xiang_value.get(wang_xiang_for_hidden_gan)
            wang_xiang_values_for_zhi.append(wang_xiang_value_for_hidden_gan)

        wang_xiang_values.append((wang_xiang_value_for_gan, wang_xiang_values_for_zhi))

    return wang_xiang_values


def calculate_gan_liang_value(values, hidden_gans, wang_xiang_values):
    result = []

    for (v_gan, v_zhi), gans, (wx_gan, wx_zhis) in zip(values, hidden_gans, wang_xiang_values):
        zhi_values = [v_zhi * g * wx for g, wx in zip(gans.values(), wx_zhis)]
        result.append((v_gan * 1 * wx_gan, zhi_values))

    return result


def accumulate_wuxing_values(wuxing, gan_liang_value):
    all_wuxing = ['木', '火', '土', '金', '水']
    result = {wx: 0 for wx in all_wuxing}

    for (wx_gan, wx_zhis), (gl_gan, gl_zhis) in zip(wuxing, gan_liang_value):
        # Add the gan value
        result[wx_gan] = result.get(wx_gan, 0) + gl_gan

        # Add the zhi values
        for wx, gl in zip(wx_zhis, gl_zhis):
            result[wx] = result.get(wx, 0) + gl

    return result


def calculate_values_for_bazi(bazi, dict):
    values = []

    for item in bazi.toString().split():
        gan, zhi = item[0], item[1]

        # Determine value for gan
        value_for_gan = dict.get(gan)

        # Determine value for each hidden gan in zhi
        hidden_gans_for_zhi = hidden_gan_ratios.get(zhi)
        values_for_zhi = []
        for hidden_gan in hidden_gans_for_zhi.keys():
            value_for_hidden_gan = dict.get(hidden_gan)
            values_for_zhi.append(value_for_hidden_gan)

        values.append((value_for_gan, values_for_zhi))

    return values


def calculate_shishen(day_master_yinyang, day_master_wuxing, stem_yinyang, stem_wuxing):
    if day_master_wuxing == stem_wuxing:
        if day_master_yinyang == stem_yinyang:
            return '比肩'
        return '比劫'
    elif relationships['生'][day_master_wuxing] == stem_wuxing:
        if day_master_yinyang == stem_yinyang:
            return '食神'
        return '伤官'
    elif relationships['生'][stem_wuxing] == day_master_wuxing:
        if day_master_yinyang == stem_yinyang:
            return '偏印'
        return '正印'
    elif relationships['克'][day_master_wuxing] == stem_wuxing:
        if day_master_yinyang == stem_yinyang:
            return '偏财'
        return '正财'
    elif relationships['克'][stem_wuxing] == day_master_wuxing:
        if day_master_yinyang == stem_yinyang:
            return '正官'
        return '偏官'


def calculate_shishen_for_bazi(wuxing, yinyang):
    day_master_wuxing = wuxing[2][0]
    day_master_yinyang = yinyang[2][0]

    shishen_list = []

    for i in range(len(wuxing)):
        stem_wuxing = wuxing[i][0]
        stem_yinyang = yinyang[i][0]
        shishen_for_gan = calculate_shishen(day_master_yinyang, day_master_wuxing, stem_yinyang, stem_wuxing)
        shishen_for_zhi = []
        for hidden_stem in wuxing[i][1]:
            hidden_stem_yinyang = yinyang[i][1][wuxing[i][1].index(hidden_stem)]
            shishen_hidden = calculate_shishen(day_master_yinyang, day_master_wuxing, hidden_stem_yinyang, hidden_stem)
            shishen_for_zhi.append(shishen_hidden)

        shishen_list.append((shishen_for_gan, shishen_for_zhi))
    shishen_list[2] = ('日主', shishen_list[2][1])
    return shishen_list


def get_relations(main_wuxing):
    return wuxing_relations.get(main_wuxing, {})


def extract_form_data(form):
    """Extract data from the form."""
    return {
        'year': form.cleaned_data['year'],
        'month': form.cleaned_data['month'],
        'day': form.cleaned_data['day'],
        'hour': form.cleaned_data['hour'],
        'minute': form.cleaned_data['minute']
    }


def get_day_gan_ratio(hidden_gan, shishen_list):
    day_master_ratios = hidden_gan[2]
    shishen = shishen_list[2][1]
    shishen_ratios = {}
    for key, value in day_master_ratios.items():
        shishen_key = shishen[list(day_master_ratios.keys()).index(key)]
        shishen_ratios[shishen_key] = value

    return shishen_ratios


def analyse_partner(hidden_gan, shishen_list):
    ratios = get_day_gan_ratio(hidden_gan, shishen_list)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that can craft nuanced descriptions based on given ratios and "
                        "predefined text."},
            {"role": "user",
             "content": f"Based on the following descriptions: {peiou_xingge} and the given ratios: {ratios}, craft a "
                        f"nuanced description of the person in chinese. "}
        ]
    )

    return response.choices[0].message.content


def analyse_personality(month_zhi):
    return tigang.get(month_zhi)
