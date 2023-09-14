import datetime

import openai
import os
from bazi.constants import relationships, wang_xiang_value, gan_wuxing, hidden_gan_ratios, zhi_seasons, season_phases, \
    wuxing_relations, zhi_wuxing, gan_yinyang, peiou_xingge, tigang, liu_he, wu_he
from lunar_python import Solar

openai.api_key = os.environ.get('OPENAI_API_KEY')


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


def analyse_liunian(bazi, shishen, selected_year, is_strong, is_male):
    daymaster_wuxing = gan_wuxing.get(bazi.getDayGan())
    daymaster_yinyang = gan_yinyang.get(bazi.getDayGan())
    solar = Solar.fromYmd(int(selected_year), 5, 5)
    lunar = solar.getLunar()
    year_bazi = lunar.getEightChar()
    year_shishen = get_shishen_for_that_year(year_bazi, daymaster_wuxing, daymaster_yinyang)
    analysis = f"{year_bazi.getYearGan()}{year_bazi.getYearZhi()}年，对应流年运：{year_shishen}（数字为地支藏干之比例）<br>"
    analysis += "流年天干分析，主要对应上半年：<br>"
    analysis += analyse_liunian_shishen(year_shishen[0], bazi, shishen, year_bazi, is_strong, is_male)
    analysis += "流年地支分析，主要对应下半年：<br>"
    for k, v in year_shishen[1].items():
        analysis += f"{k}运(大约占{v*100}%):<br>"
        analysis += analyse_liunian_shishen(k, bazi, shishen, year_bazi, is_strong, is_male)
    return analysis


def get_shishen_for_that_year(year_bazi, daymaster_wuxing, daymaster_yinyang):
    year_gan = year_bazi.getYearGan()
    year_hidden_gans = hidden_gan_ratios.get(year_bazi.getYearZhi())
    yinyang_gan = gan_yinyang.get(year_gan)
    wuxing_gan = gan_wuxing.get(year_gan)
    gan_shishen = calculate_shishen(daymaster_yinyang, daymaster_wuxing, yinyang_gan, wuxing_gan)
    zhi_shishen = {}
    for gan, ratio in year_hidden_gans.items():
        yinyang_for_gan = gan_yinyang.get(gan)
        wuxing_for_gan = gan_wuxing.get(gan)
        shishen_for_gan = calculate_shishen(daymaster_yinyang, daymaster_wuxing, yinyang_for_gan, wuxing_for_gan)
        zhi_shishen[shishen_for_gan] = ratio
    return [gan_shishen, zhi_shishen]


def check_he(ganzhi1, ganzhi2):
    return (ganzhi1, ganzhi2) in liu_he or (ganzhi2, ganzhi1) in liu_he or (ganzhi1, ganzhi2) in wu_he or (
        ganzhi2, ganzhi1) in wu_he


def contain_shishen(target, shishen_list):
    for main, sublist in shishen_list:
        if main == target or target in sublist:
            return True
    return False


def find_shishen_indices(target, shishen_list):
    indices = []
    i = 0
    for shishen, sublist in shishen_list:
        if shishen == target:
            indices.append(i)
        i += 1
        for sub_shishen in sublist:
            if sub_shishen == target:
                indices.append(i)
        i += 1
    return indices


def check_if_he_target(shishen, bazi, year_bazi, target):
    if contain_shishen(target, shishen):
        indices = find_shishen_indices(target, shishen)
        s = bazi.toString().replace(' ', '')
        for i in indices:
            if check_he(year_bazi.getYearGan(), s[i]) or check_he(year_bazi.getYearZhi(), s[i]):
                return True
    return False


def handle_zheng_cai(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = "•流年走正财运， 未婚者有结婚之机会，已婚者太太能帮助先生，先生也较疼老婆。<br>"
    if check_he(bazi.getDayGan(), year_bazi.getYearGan()) or check_he(bazi.getMonthZhi(), year_bazi.getYearZhi()):
        analysis += "•正财合日主或月支，在钱财或身体方面会有损失"
        if not is_male:
            analysis += "，夫妻间感情会变不好"
        analysis += "。<br>"
    if not is_strong and contain_shishen('正印', shishen) and contain_shishen('比肩', shishen) and \
            contain_shishen(
                '比劫', shishen):
        analysis += "•本命身弱而带有正印，比肩，比劫， 注意破财、损命。"
        if is_male:
            analysis += "太太与自己母亲不和，会有婆媳问题。"
        analysis += "<br>"
    if len(find_shishen_indices('正财', shishen)) >= 2:
        analysis += "•财多又走财年， 很有异性缘"
    if not is_strong:
        analysis += ("•身弱，正财为忌神， 很会花钱，不重视钱财。<br>"
                     "•要变通或较费力才会赚到钱。<br>"
                     "•会有破财或桃色纠纷。<br>")
    else:
        analysis += "•身强， 正财为喜神， 较有赚钱机会， 赚钱不难。<br>"
        if not (contain_shishen('正财', shishen) or contain_shishen('偏财', shishen)):
            analysis += "•但本命无正财偏财， 宜从事劳力密集之行业。<br>"
    return analysis


def handle_pian_cai(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = "•流年走偏财，注意父亲身体状况，较不喜欢固定的工作，喜欢挑剔，感情亦不专。<br>"
    if not is_male and is_strong and contain_shishen('七杀', shishen):
        analysis += "•女命身强，走偏财，本命有七杀， 风情万种， 很开放， 易入上流社会。易养小男人或赚钱养男人<br>"
    if not is_strong:
        analysis += "•身弱，走偏财，赚钱很难。<br>"
        analysis += "•身弱，偏财为忌神，宜戒色；不宜生活浮夸，钱少花一点，要懂得节约。<br>"
    else:
        analysis += "•身强，偏财为喜神，为人慷慨豪爽，懂得人情世故，交际特别好。<br>"
        analysis += "•身强，偏财为喜神，得正职，亦主财运亨通，易有横财。<br>"
    if is_male and is_strong and contain_shishen('七杀', shishen) and contain_shishen('偏财', shishen):
        analysis += "•男命身强，走偏财，命中又有七杀及偏财，容易有名声与地位，但好色居多、养妾<br>"
    indices = find_shishen_indices('偏财', shishen)
    gan_indices = [i for i in indices if i % 2 == 0]
    if len(gan_indices) > 0:
        analysis += "•偏财通根，外面养妾， 偷偷摸摸。<br>"
    if not (contain_shishen('正财', shishen) or contain_shishen('偏财', shishen)):
        analysis += "•走偏财运，命中无正财，偏财，为人没有金钱观念，财来财去，不知如何赚钱，亦不重视钱财。<br>"
    return analysis


def handle_zheng_guan(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_qi_sha(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_zheng_yin(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_pian_yin(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_bi_jian(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_bi_jie(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_bi_jie(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_shang_guan(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


def handle_shi_shen(bazi, shishen, year_bazi, is_strong, is_male):
    return ""


shishen_handler = {
    '正财': handle_zheng_cai,
    '偏财': handle_pian_cai,
    '正官': handle_zheng_guan,
    '七杀': handle_qi_sha,
    '正印': handle_zheng_yin,
    '偏印': handle_pian_yin,
    '比肩': handle_bi_jian,
    '比劫': handle_bi_jie,
    '伤官': handle_shang_guan,
    '食神': handle_shi_shen
}


def analyse_liunian_shishen(year_shishen, bazi, shishen, year_bazi, is_strong, is_male):
    handler = shishen_handler.get(year_shishen)
    analysis = handler(bazi, shishen, year_bazi, is_strong, is_male)
    if check_if_he_target(shishen, bazi, year_bazi, '正财'):
        analysis += "•本命正财， 被流年合， 主钱财流失大"
        if is_male:
            analysis += ", 严防婚变"
        analysis += "。<br>"
    if check_if_he_target(shishen, bazi, year_bazi, '偏财'):
        analysis += "•本命偏财， 被流年合， 开支特别大，生意会赔钱，钱财流失大，或生意一败涂地。父亲身体欠安，情人失恋，若为野桃花，易被揭发。<br>"

    return analysis


def analyse_personality(month_zhi):
    return tigang.get(month_zhi)
