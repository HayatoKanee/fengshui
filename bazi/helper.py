from bazi.constants import relationships, wang_xiang_value, gan_wuxing, hidden_gan_ratios, zhi_seasons, season_phases, \
    wuxing_relations, zhi_wuxing


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


def calculate_wu_xing_for_bazi(bazi):
    wu_xing_values = []

    for item in bazi.toString().split():
        gan, zhi = item[0], item[1]

        # Determine wu_xing for gan
        wu_xing_for_gan = gan_wuxing.get(gan)

        # Determine wu_xing for each hidden gan in zhi
        hidden_gans_for_zhi = hidden_gan_ratios.get(zhi)
        wu_xing_values_for_zhi = []
        for hidden_gan in hidden_gans_for_zhi.keys():
            wu_xing_for_hidden_gan = gan_wuxing.get(hidden_gan)
            wu_xing_values_for_zhi.append(wu_xing_for_hidden_gan)

        wu_xing_values.append((wu_xing_for_gan, wu_xing_values_for_zhi))

    return wu_xing_values


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
