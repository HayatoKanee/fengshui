import datetime
from collections import Counter
import statistics

import openai
import os
from bazi.constants import *
from lunar_python import Solar, Lunar, EightChar
import csv

from fengshui.settings import DATA_DIR

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
            return '七杀'
        return '正官'


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


# def analyse_partner(hidden_gan, shishen_list):
#     ratios = get_day_gan_ratio(hidden_gan, shishen_list)
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system",
#              "content": "You are a helpful assistant that can craft nuanced descriptions based on given ratios and "
#                         "predefined text."},
#             {"role": "user",
#              "content": f"Based on the following descriptions: {peiou_xingge} and the given ratios: {ratios}, craft a "
#                         f"nuanced description of the person in chinese. "}
#         ]
#     )
#
#     return response.choices[0].message.content

def analyse_partner(hidden_gan, shishen_list):
    ratios = get_day_gan_ratio(hidden_gan, shishen_list)
    return peiou_xingge.get(list(ratios.items())[0][0])


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
        analysis += f"{k}运(大约占{v * 100}%):<br>"
        analysis += analyse_liunian_shishen(k, bazi, shishen, year_bazi, is_strong, is_male)
    analysis += "流年及本命分析：<br>"
    if check_if_he_target(shishen, bazi, year_bazi, '正财'):
        analysis += "•本命正财， 被流年合， 主钱财流失大"
        if is_male:
            analysis += ", 严防婚变"
        analysis += "。<br>"
    if check_if_he_target(shishen, bazi, year_bazi, '偏财'):
        analysis += "•本命偏财， 被流年合， 开支特别大，生意会赔钱，钱财流失大，或生意一败涂地。父亲身体欠安，情人失恋，若为野桃花，易被揭发。<br>"
    zheng_guan_he = check_if_he_target(shishen, bazi, year_bazi, '正官')
    if zheng_guan_he:
        analysis += "•本命正官， 被流年合， 职业上会有变动或被夺，宜避免出分头，不要当老大，以免招来烦恼。<br>"
        if is_male:
            analysis += "•男命正官被流年合，防名声、地位受损；或有官司缠身。<br>"
        else:
            analysis += "•女命正官被流年合，注意丈夫身体，也可能有外遇或走掉。<br>"

    if not is_male:
        indices = find_shishen_indices('正官', shishen)
        gan_indices = [i for i in indices if i % 2 == 0]
        s = bazi.toString().replace(' ', '')
        daymaster_he = False
        for i in gan_indices:
            if check_he(s[i], bazi.getDayGan()):
                daymaster_he = True
        if daymaster_he:
            analysis += "•女命日主合正官， 很重视老公。<br>"
        if len(indices) >= 2:
            analysis += "•女命有双正官者，易再婚。<br>"
    if is_strong and check_if_he_target(shishen, bazi, year_bazi, '七杀'):
        analysis += "•身强而本命有七杀，却被流年合，主事业上不容易发挥，活力易显不足。<br>"
    qisha_indices = find_shishen_indices('七杀', shishen)
    if len(qisha_indices) >= 2:
        analysis += "•命中七杀有两个以上者，精神显得委靡不振，容易有灾难、意外、官司、血光。<br>"
    if check_if_he_target(shishen, bazi, year_bazi, '偏印'):
        analysis += "•偏印被流运合住，母亲身体变差。<br>"
    if not is_strong and check_if_he_target(shishen, bazi, year_bazi, '正印'):
        analysis += "•命中所喜之正印被流年合住，特别倒霉，或母亲身体变不好。<br>"
    shang_guan_indices = find_shishen_indices('伤官', shishen)
    if 0 in shang_guan_indices and 1 in shang_guan_indices:
        analysis += "•伤官通根在年柱，代表幼年时期会受到重大创伤或过错。<br>"
    if 2 in shang_guan_indices and 3 in shang_guan_indices:
        analysis += "•伤官通根在月柱，代表青年时期会受到重大创伤或过错。<br>"
    if 4 in shang_guan_indices and 5 in shang_guan_indices:
        analysis += "•伤官通根在年柱，代表中年时期会受到重大创伤或过错。<br>"
    if 6 in shang_guan_indices and 7 in shang_guan_indices:
        analysis += "•伤官通根在年柱，代表老年时期会受到重大创伤或过错。<br>"
    if check_if_he_target(shishen, bazi, year_bazi, '伤官'):
        analysis += "•伤官被流年合，思绪比较杂乱，才华点子不现，处事不明，有点迷迷糊糊，所以若想做决定时，需要多问几个人征询意见。<br>"
    if check_if_he_target(shishen, bazi, year_bazi, '食神'):
        analysis += "•食神被流年合，代表才华不能展现，决策容易失误，身体状况较差。<br>"
        if not is_male:
            analysis += "•食神被流年合, 女命甚至会危及子女。<br>"
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
        analysis += "•偏财通根，外面养妾，偷偷摸摸。<br>"
    if not (contain_shishen('正财', shishen) or contain_shishen('偏财', shishen)):
        analysis += "•走偏财运，命中无正财，偏财，为人没有金钱观念，财来财去，不知如何赚钱，亦不重视钱财。<br>"
    return analysis


def handle_zheng_guan(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = "•走正官运时很好面子<br>"
    if is_strong and contain_shishen('正官', shishen) and contain_shishen('七杀', shishen):
        analysis += "•身强，正官为喜神，原命又有正官和七杀，主在社会上有名望，地位。<br>"
    if not is_strong and not contain_shishen('正官', shishen) and not contain_shishen('七杀', shishen):
        analysis += "•身弱，正官为忌神，本命没有正官和七杀，主压力特别大，精神也易紧张。<br>"
    if contain_shishen('伤官', shishen):
        analysis += "•本命有伤官，主有血光之灾，或名声、地位有损害。<br>"
    if not is_male:
        analysis += "•女命流年走正官，会想结婚。<br>"
        if contain_shishen('正官', shishen) and contain_shishen('七杀', shishen):
            analysis += "•女命带正官，七杀，行运逢正官，易有桃色纠纷或红杏出墙。<br>"
    if not is_strong:
        analysis += "•身弱者走正官运，为忌神，今年身体不好，会变成体弱多病，因为'身弱不得任财官'也。<br>"
        analysis += "•身弱者走正官运，为忌神，家庭、学业或工作压力会感觉特别大，处事较优柔寡断，做事欠周圆，缺乏自信，魄力不足。<br>"
        analysis += "•身弱者走正官运，为忌神，注意是非或降职丢官之事情发生。<br>"
        if not is_male:
            analysis += "•女命易受丈夫所累，或有婚姻恋爱之烦恼。<br>"
    else:
        analysis += "•身强遇正官为喜神，见官得官，不得官禄，也会得地位。<br>"
        if not is_male:
            analysis += "•女命较重视丈夫。<br>"
    if contain_shishen('食神', shishen):
        analysis += "•走正官运时，原命带有食神，行事上显得懒散，不积极，不带劲。<br>"

    return analysis


def handle_qi_sha(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = ""
    if not is_male:
        analysis += "•女命行七杀，较不得老公宠爱、婚姻比较辛苦、与老公理念较不相同。<br>"
        analysis += "•女命行七杀，异性缘好，结婚后还是一样具有男人缘，须自我控制。<br>"
        if not is_strong:
            analysis += "•女命身弱，走七杀运时会被男人欺负。<br>"
        if contain_shishen('正官', shishen) and contain_shishen('七杀', shishen):
            analysis += "•女命有『正官、七杀』，又逢七杀，易有外遇，容易受人欺凌，更易有感情纠纷。<br>"
    else:
        if contain_shishen('正官', shishen):
            analysis += "•男命走七杀，本命有正官，喜欢在风月场所或在女人堆中鬼混。<br>"
        qisha_indices = find_shishen_indices('七杀', shishen)
        if len(qisha_indices) >= 2:
            analysis += "•男命七杀两个以上，又逢七杀运，会为子女奔波操劳，甚至受其所累。<br>"
    if not is_strong:
        analysis += "•身弱行七杀，理想较难实现，容易离婚，易换工作。<br>"
        analysis += "•身弱，杀为忌神，性情上显得刚愎自用。<br>"
        if contain_shishen('七杀', shishen):
            analysis += "•身弱，本命有七杀，又行七杀运，杀多攻身，容易挥霍无度，不知节制，爱面子。<br>"
    else:
        if contain_shishen('七杀', shishen):
            if is_male:
                analysis += "•身强，本命有七杀，又行七杀运，杀多攻身，易遭小人陷害，破财，有血光之灾。<br>"
            else:
                analysis += "•女命身强，本命有七杀，又行七杀运，易感情生变，或讨小男人，或血光之灾。<br>"
        else:
            analysis += "•身强走七杀，在工作或事业上容易拥有地位和权威。<br>"
    return analysis


def handle_zheng_yin(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = "•流运走正印，母亲身体状况容易变差。<br>"
    analysis += "•流运走正印，较不喜欢动，个性固执，主观强，但较有慈悲心、有佛缘。<br>"
    analysis += "•走印运时，很想购置不动产，同时亦会有机会获得祖产之机会。<br>"
    if is_strong:
        analysis += "•身强走正印，为忌神，烦恼特别多。<br>"
        if contain_shishen('正官', shishen) and contain_shishen('正印', shishen):
            analysis += "•身强走正印，命中有『正官，正印』，在本运内压力很大，愿望难发挥，多顾忌。<br>"
        if contain_shishen('正财', shishen):
            analysis += "•身强，命中又有正财，逢正印运，比较容易丢掉职业，损败家业、或换行业。<br>"
    else:
        analysis += "•身弱走正印，处处逢贵人。<br>"
        analysis += "•身弱逢正印，在学术上容易出名，或特别有机会接近宗教。<br>"
    if is_male:
        if contain_shishen('正财', shishen):
            analysis += "•男命走正印，命中又有正财，今年太太与母亲会有不和之现象发生，即婆媳不和。<br>"
    else:
        if contain_shishen('正财', shishen):
            analysis += "•女命走正印，命中又有正财，较易与母亲顶嘴，做事得过且过。<br>"
    if contain_shishen('正印', shishen) or contain_shishen('偏印', shishen):
        analysis += "•八字有正印或偏印，又逢正印，做事缺乏专注力，事业易变动，说话做事，颠三倒四。<br>"

    return analysis


def handle_pian_yin(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = "•流年走偏印，很想买不动产。<br>"
    analysis += "•走偏印，心性不稳定，常三心两意，比较不易成功。<br>"
    if is_strong:
        analysis += "•身强，走偏印运，喜外出结缘，爱花钱。<br>"
        analysis += "•走偏印而为忌神，母亲之健康会变不好。<br>"
        if contain_shishen('偏印', shishen):
            analysis += "•身强，命中有偏印，又逢偏印，较多疑，想得太多，易有躁郁证、自闭症状，甚者更会自杀。<br>"
    else:
        analysis += "•身弱，走偏印运，在学业、家庭、工作上较易得贵人相助，名利两全。<br>"
    if contain_shishen('食神', shishen):
        analysis += "•流年走偏印，本命有食神，称为『枭印夺食』，主常遭陷害，被扯后腿，做事多败少成"
        if not is_male:
            analysis += "；女命易得肿瘤"
        analysis += "。<br>"
    if contain_shishen('正印', shishen):
        analysis += "•流年走偏印，本命有正印，人会非常主观。<br>"
    return analysis


def handle_bi_jian(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = ""
    if is_strong:
        analysis += "•走比肩而为忌神，钱尽量不要借人，防有去无回。人情包袱重，容易引起感情困扰。<br>"
        analysis += "•与人相处易有意见，在人事上会有较多之冲突发生。<br>"
        analysis += "•尽量不要与人合伙，以免遭朋友或合伙人拖累。<br>"
        analysis += "•此阶段财运不佳，钱不够花。<br>"
        analysis += "•容易有官司、词讼、刑妻、不顺之事。<br>"
    else:
        analysis += "•走比肩而为喜神，易与跟兄弟、朋友、同行『合作创业』，而且受到他们的帮助<br>"
    return analysis


def handle_bi_jie(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = ""
    if is_strong:
        analysis += "•走比劫而为忌神，钱不要借人，钱拿出去便拿不回来。<br>"
        analysis += "•人情包袱重，需放人情困扰。<br>"
        analysis += "•感情生活脆弱，容易有失恋、离婚之事情发生。<br>"
        analysis += "•容易流失机会，所以当见有机会时更宜妥善把握。<br>"
        analysis += "•此阶段财运不佳，故不宜经商，或扩大投资规模，更不宜从事投机行业，以免赔钱。<br>"
        analysis += "•不要与人合伙做生意，容易引发是非纠纷。<br>"
        analysis += "•财运不佳，钱总是不够花。<br>"
    else:
        analysis += "•走比肩而为喜神，思维清晰，能言善道，应变力强，富社交能力。<br>"
        analysis += "•与兄弟、姐妹、朋友、或同辈间感情融洽，又能得到他们的帮助。<br>"
        analysis += "•财源广进，反事顺利。<br>"
    return analysis


def handle_shang_guan(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = "•当走伤官运时，爱受别人夸赞，不喜欢别人批评。<br>"
    if not is_male:
        analysis += "•女命走伤官，爱管丈夫，喜叼念丈夫，句句伤丈夫之心，故易有婚变。<br>"
    else:
        analysis += "•男命走伤官，奇招主意特别多。<br>"
    if contain_shishen('食神', shishen):
        analysis += "•走伤官，命中有食神，如果从事教育工作，可以桃李满天下。<br>"
    if contain_shishen('正官', shishen):
        analysis += "•流年伤官，命中有正官，即『伤官见官』，主会有血光之灾、官司；更不要替人作担保，因事情会出现反复，较难成功。<br>"
    if not is_strong:
        analysis += "•身弱，伤官为忌神，易亏钱；情绪、脾气会特别差。<br>"
        analysis += "•身弱，伤官为忌神，人较偏激、任性、夸大。<br>"
        analysis += "•身弱，伤官为忌神，性欲会较开放，注意因情欲惹祸，容易有血光、官司、破财、车祸。<br>"
        if is_male:
            analysis += "•身弱，伤官为忌神，男命易跟儿女不合。<br>"
        else:
            analysis += "•身弱，伤官为忌神，女命感情易有波动。<br>"
        analysis += "•伤官为忌神时，你给予帮助最多的人，往往也是最容易陷害你的人。<br>"
        analysis += "•伤官为忌神时，自己才华特别多，但难以贯彻，有大事难成之叹！考试运亦差。<br>"
        analysis += "•伤官为忌神时，容易伤财，故要尽量避免去投资。<br>"
        analysis += "•伤官为忌神时，做得再多，也是一样无人欣赏。<br>"
    else:
        analysis += "•身强，伤官为喜神，人变得很有才华，头脑好，学习能力强，追求完美，但缺乏耐性。<br>"
        analysis += "•伤官为喜神，是标准的批评家，做事很有魄力，一定要执行到底，完成为止。<br>"
        analysis += "•身强，伤官为喜神，人特别聪明，富感性。<br>"
        analysis += "•身强，伤官为喜神，情场得意。<br>"
        if not is_male:
            analysis += "•伤官为喜神，女命容易怀胎生孩子<br>"
    return analysis


def handle_shi_shen(bazi, shishen, year_bazi, is_strong, is_male):
    analysis = ""
    if not is_strong:
        analysis += "•身弱，食神为忌神，缺乏活动力，心情不佳，没远景，没有坚持力。<br>"
        analysis += "•食神为忌神时，身体易长出疾病，尤宜预防消化系统方面之疾病。<br>"
        if not is_male:
            analysis += "•食神为忌神时，女命容易怀孕，但亦容易流产。因为女命是以『伤官、食神』来论子息，故女命走食神，怀孕机会较多。<br>"
    else:
        analysis += "•身强，食神为喜神，主自己反应灵敏，多巧思，适合研究及发明工作，学习能力强。<br>"
        analysis += "•食神为喜神时，朋友皆友善。<br>"
        analysis += "•食神为喜神时，口欲特别佳，吃美食的机会特别多，须注意体型发胖。<br>"
        if is_male:
            analysis += "•食神为喜神时，男命易喜女色，或女性缘分佳。<br>"
        analysis += "•食神为喜神时，作食易被表扬、或受到赞赏，容易成为名人。<br>"
    if contain_shishen('偏印', shishen):
        analysis += "•走食神，命中带有偏印，称为『枭印夺食』，主才华施展不开，做事常会前功尽弃，多败少成，导致内心郁闷。<br>"
        analysis += "•『枭印夺食』，容易遇小人，易遭人陷害，甚至有性命之忧。<br>"
        analysis += "•『枭印夺食』，容易被人扯后腿，甚或自己也会扯别人后腿，以致误人误己。<br>"
        analysis += "•『枭印夺食』，容易遭遇意外之灾；或有隐疾复发，而发生致命危险。<br>"
        if not is_male:
            analysis += "•『枭印夺食』，女命或流产；或有妇女病及肿瘤。<br>"
    if contain_shishen('伤官', shishen):
        analysis += "•流运走食神，命中有伤官者，主才华施展不开，多学不专，文武似兼具，但很难专精。<br>"
    if contain_shishen('七杀', shishen):
        analysis += "•流运走食神，命中有七杀者，主权势被制住，凶不起来。<br>"

    return analysis


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
    return analysis


def analyse_personality(month_zhi):
    return tigang.get(month_zhi)


def best_bazi_from_to(start_year, end_year):
    for year in range(start_year, end_year + 1):
        print('processing year' + str(year))
        best_bazi_in_year(year)
        print('finish year ' + str(year))


def bazi_probability_experiment(start_year, end_year):
    """
    Analyze BaZi distribution over a range of years.
    Outputs CSV with frequency counts and statistical summary.
    """
    bazi_counter = Counter()
    day_pillar_counter = Counter()  # Just 日柱
    total_hours = 0

    print(f'Starting BaZi probability experiment: {start_year} to {end_year}')

    for year in range(start_year, end_year + 1):
        lunar = Lunar.fromYmdHms(year, 1, 1, 0, 0, 0)

        while lunar.getYear() == year:
            # Check all 12 时辰 (hours: 0, 1, 3, 5, ..., 21, 23)
            for hour in [0] + list(range(1, 23, 2)) + [23]:
                bazi = Lunar.fromYmdHms(
                    year, lunar.getMonth(), lunar.getDay(), hour, 0, 0
                ).getEightChar()

                bazi_str = bazi.toString()  # Full 八字: "甲子 乙丑 丙寅 丁卯"
                bazi_counter[bazi_str] += 1

                # Extract day pillar (日柱) - 3rd element
                day_pillar = bazi_str.split()[2]
                day_pillar_counter[day_pillar] += 1

                total_hours += 1

            # Move to next day
            i = 1
            next_lunar = lunar.next(i)
            while next_lunar.toString() == lunar.toString():
                i += 1
                next_lunar = lunar.next(i)
            if next_lunar.getMonth() < lunar.getMonth():
                break
            lunar = next_lunar

        if year % 100 == 0:
            print(f'Processed year {year}')

    print(f'Finished processing. Total hours: {total_hours}')

    # Output full BaZi CSV
    full_bazi_path = os.path.join(DATA_DIR, f"bazi_probability_{start_year}_{end_year}.csv")
    with open(full_bazi_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['bazi', 'count', 'percentage'])
        for bazi, count in bazi_counter.most_common():
            percentage = (count / total_hours) * 100
            writer.writerow([bazi, count, f'{percentage:.6f}'])

    # Output day pillar CSV
    day_pillar_path = os.path.join(DATA_DIR, f"day_pillar_probability_{start_year}_{end_year}.csv")
    with open(day_pillar_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['day_pillar', 'count', 'percentage'])
        for pillar, count in day_pillar_counter.most_common():
            percentage = (count / total_hours) * 100
            writer.writerow([pillar, count, f'{percentage:.6f}'])

    # Calculate statistics
    counts = list(bazi_counter.values())
    day_counts = list(day_pillar_counter.values())

    stats = {
        'total_hours': total_hours,
        'unique_bazi': len(bazi_counter),
        'unique_day_pillars': len(day_pillar_counter),
        'full_bazi': {
            'mean': statistics.mean(counts),
            'median': statistics.median(counts),
            'stdev': statistics.stdev(counts) if len(counts) > 1 else 0,
            'min': min(counts),
            'max': max(counts),
            'most_common': bazi_counter.most_common(10),
            'least_common': bazi_counter.most_common()[-10:],
        },
        'day_pillar': {
            'mean': statistics.mean(day_counts),
            'median': statistics.median(day_counts),
            'stdev': statistics.stdev(day_counts) if len(day_counts) > 1 else 0,
            'min': min(day_counts),
            'max': max(day_counts),
            'most_common': day_pillar_counter.most_common(10),
            'least_common': day_pillar_counter.most_common()[-10:],
        }
    }

    # Output summary
    summary_path = os.path.join(DATA_DIR, f"bazi_probability_summary_{start_year}_{end_year}.txt")
    with open(summary_path, "w", encoding='utf-8') as f:
        f.write(f"BaZi Probability Experiment: {start_year} - {end_year}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Total hours analyzed: {total_hours:,}\n")
        f.write(f"Unique full BaZi combinations: {len(bazi_counter):,}\n")
        f.write(f"Unique day pillars: {len(day_pillar_counter)}\n\n")

        f.write(f"Full BaZi Statistics:\n")
        f.write(f"  Mean count: {stats['full_bazi']['mean']:.2f}\n")
        f.write(f"  Median count: {stats['full_bazi']['median']:.2f}\n")
        f.write(f"  Std deviation: {stats['full_bazi']['stdev']:.2f}\n")
        f.write(f"  Min count: {stats['full_bazi']['min']}\n")
        f.write(f"  Max count: {stats['full_bazi']['max']}\n")
        f.write(f"  Ratio (max/min): {stats['full_bazi']['max']/stats['full_bazi']['min']:.2f}\n\n")

        f.write(f"Top 10 Most Common BaZi:\n")
        for bazi, count in stats['full_bazi']['most_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {bazi}: {count:,} ({pct:.4f}%)\n")

        f.write(f"\nTop 10 Least Common BaZi:\n")
        for bazi, count in stats['full_bazi']['least_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {bazi}: {count:,} ({pct:.4f}%)\n")

        f.write(f"\nDay Pillar Statistics:\n")
        f.write(f"  Mean count: {stats['day_pillar']['mean']:.2f}\n")
        f.write(f"  Median count: {stats['day_pillar']['median']:.2f}\n")
        f.write(f"  Std deviation: {stats['day_pillar']['stdev']:.2f}\n")
        f.write(f"  Min count: {stats['day_pillar']['min']}\n")
        f.write(f"  Max count: {stats['day_pillar']['max']}\n")
        f.write(f"  Ratio (max/min): {stats['day_pillar']['max']/stats['day_pillar']['min']:.2f}\n\n")

        f.write(f"Top 10 Most Common Day Pillars:\n")
        for pillar, count in stats['day_pillar']['most_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {pillar}: {count:,} ({pct:.4f}%)\n")

        f.write(f"\nTop 10 Least Common Day Pillars:\n")
        for pillar, count in stats['day_pillar']['least_common']:
            pct = (count / total_hours) * 100
            f.write(f"  {pillar}: {count:,} ({pct:.4f}%)\n")

    print(f"\nOutput files:")
    print(f"  Full BaZi CSV: {full_bazi_path}")
    print(f"  Day Pillar CSV: {day_pillar_path}")
    print(f"  Summary: {summary_path}")

    return stats


def best_bazi_in_year(year):
    lunar = Lunar.fromYmdHms(year, 1, 1, 0, 0, 0)
    file_path = os.path.join(DATA_DIR, f"good_bazis_{year}.csv")
    with open(file_path, "w", newline='') as csvfile:
        bazi_writer = csv.writer(csvfile)
        while lunar.getYear() == year:
            solar = lunar.getSolar()
            if is_bazi_good(Lunar.fromYmdHms(year, lunar.getMonth(), lunar.getDay(), 0, 0, 0).getEightChar(), 0):
                bazi_writer.writerow([solar.getYear(), solar.getMonth(), solar.getDay(), 0])
            for i in range(1, 23, 2):
                if is_bazi_good(Lunar.fromYmdHms(year, lunar.getMonth(), lunar.getDay(), i, 0, 0).getEightChar(),
                                i):
                    bazi_writer.writerow([solar.getYear(), solar.getMonth(), solar.getDay(), i])
            if is_bazi_good(Lunar.fromYmdHms(year, lunar.getMonth(), lunar.getDay(), 23, 0, 0).getEightChar(), 23):
                bazi_writer.writerow([solar.getYear(), solar.getMonth(), solar.getDay(), 23])
            i = 1
            next_lunar = lunar.next(i)
            while next_lunar.toString() == lunar.toString():
                i += 1
                next_lunar = lunar.next(i)
            if next_lunar.getMonth() < lunar.getMonth():
                break
            lunar = next_lunar


def is_bazi_good(bazi: EightChar, hour):
    return is_bazi_contain_all_wuxing(bazi) and not is_wu_bu_yu_shi(bazi, hour) and not tian_gan_or_di_zhi_xiang_chong(
        bazi,
        0) and not tian_gan_or_di_zhi_xiang_chong(
        bazi, 1)


def is_bazi_contain_all_wuxing(bazi: EightChar):
    wuxing_big_number = {'金': 0, '木': 0, '水': 0, '火': 0, '土': 0}
    for tiangan in bazi.toString().split():
        for char in tiangan:
            wuxing_big_number[wuxing[char]] += 1
    for num in wuxing_big_number.values():
        if num == 0:
            return False
    return True


def is_wu_bu_yu_shi(bazi: EightChar, hour):
    # return relationships['克'][gan_wuxing[bazi.getTimeGan()]] == gan_wuxing[bazi.getDayGan()] and gan_yinyang[
    #     bazi.getTimeGan()] == gan_yinyang[bazi.getDayGan()]
    if (bazi.getDayGan(), bazi.getTimeZhi()) in wu_bu_yu_shi:
        return True
    if bazi.getDayGan() == '戊' and bazi.getTimeZhi() == '子' and hour >= 23:
        return True
    return False


def tian_gan_or_di_zhi_xiang_chong(bazi: EightChar, get_gan=0):
    clashing_pair = {0: gan_xiang_chong, 1: zhi_xiang_chong}
    gan = get_gan_or_zhi(bazi, get_gan)
    for i in range(len(gan)):
        for j in range(i + 1, len(gan)):
            if (gan[i], gan[j]) in clashing_pair[get_gan]:
                return True
    return False


def get_gan_or_zhi(bazi: EightChar, get_gan=0):
    gan_or_zhi = []
    for ganzhi in bazi.toString().split():
        gan_or_zhi.append(ganzhi[get_gan])
    return gan_or_zhi


# --- 通用神煞计数函数 ---
def count_shensha(main, zhi_list, table):
    count = 0
    for z in zhi_list:
        if (main, z) in table:
            count += 1
    return count


# --- 重构后的神煞计数函数 ---
# 天德贵人: 以月支对比四柱天干
# 参考表: tian_de
# main: 月支, zhi_list: 四柱天干

def calculate_tian_de(bazi):
    month_zhi = bazi.getMonthZhi()
    gan_list = get_gan_or_zhi(bazi, 0)
    return count_shensha(month_zhi, gan_list, tian_de)

# 月德贵人: 以月支对比四柱天干
# 参考表: yue_de
# main: 月支, zhi_list: 四柱天干

def calculate_yue_de(bazi):
    month_zhi = bazi.getMonthZhi()
    gan_list = get_gan_or_zhi(bazi, 0)
    return count_shensha(month_zhi, gan_list, yue_de)

# 天乙贵人（日干）: 以日干对比四柱地支
# 参考表: gui_ren
# main: 日干, zhi_list: 四柱地支

def calculate_day_guiren(bazi):
    day_gan = bazi.getDayGan()
    zhi_list = get_gan_or_zhi(bazi, 1)
    return count_shensha(day_gan, zhi_list, gui_ren)

# 天乙贵人（年干）: 以年干对比四柱地支
# 参考表: gui_ren
# main: 年干, zhi_list: 四柱地支

def calculate_year_guiren(bazi):
    year_gan = bazi.getYearGan()
    zhi_list = get_gan_or_zhi(bazi, 1)
    return count_shensha(year_gan, zhi_list, gui_ren)

# 禄神: 以日干对比四柱地支
# 参考表: lu_shen
# main: 日干, zhi_list: 四柱地支

def calculate_lu_shen(bazi):
    day_gan = bazi.getDayGan()
    zhi_list = get_gan_or_zhi(bazi, 1)
    return count_shensha(day_gan, zhi_list, lu_shen)

# 文昌: 以日干对比四柱地支
# 参考表: wen_chang
# main: 日干, zhi_list: 四柱地支

def calculate_wen_chang(bazi):
    day_gan = bazi.getDayGan()
    zhi_list = get_gan_or_zhi(bazi, 1)
    return count_shensha(day_gan, zhi_list, wen_chang)

# --- 羊刃: 以日干对比四柱地支
# 参考表: yang_ren
# main: 日干, zhi_list: 四柱地支

def calculate_yang_ren(bazi):
    day_gan = bazi.getDayGan()
    zhi_list = get_gan_or_zhi(bazi, 1)
    return count_shensha(day_gan, zhi_list, yang_ren)

# --- 红艳煞: 以日干对比四柱地支
# 参考表: hong_yan_sha
# main: 日干, zhi_list: 四柱地支

def calculate_hong_yan_sha(bazi):
    day_gan = bazi.getDayGan()
    zhi_list = get_gan_or_zhi(bazi, 1)
    return count_shensha(day_gan, zhi_list, hong_yan_sha)

# --- 神煞判定函数（保持不变，自动用新实现） ---
def is_tian_de(bazi):
    return calculate_tian_de(bazi) > 0

def is_yue_de(bazi):
    return calculate_yue_de(bazi) > 0

def is_tian_yue_erde(bazi):
    return calculate_tian_de(bazi) > 0 and calculate_yue_de(bazi) > 0

def is_tian_yi_guiren(bazi):
    return calculate_day_guiren(bazi) > 0 or calculate_year_guiren(bazi) > 0

def is_lu_shen(bazi):
    return calculate_lu_shen(bazi) > 0

def is_wen_chang(bazi):
    return calculate_wen_chang(bazi) > 0

def is_yang_ren(bazi):
    return calculate_yang_ren(bazi) > 0

def is_hong_yan_sha(bazi):
    return calculate_hong_yan_sha(bazi) > 0

# --- 三奇: 四柱天干中有顺序出现的三奇组合
# 组合：乙丙丁、甲戊庚、壬癸辛，且顺序相连

def is_san_qi(bazi):
    gan_list = get_gan_or_zhi(bazi, 0)
    san_qi_groups = [
        ['乙', '丙', '丁'],
        ['甲', '戊', '庚'],
        ['壬', '癸', '辛'],
    ]
    for i in range(len(gan_list) - 2):
        sub = gan_list[i:i+3]
        if sub in san_qi_groups:
            return True
    return False

# --- 辅助函数：从地支列表中排除指定地支
def filter_zhi_from_list(zhi_list, zhi_to_exclude):
    return [z for z in zhi_list if z != zhi_to_exclude]

# --- 将星: 以日支或年支对比四柱地支
# 参考表: jiang_xing
# main: 日支或年支, zhi_list: 四柱地支(排除主支)

def calculate_jiang_xing(bazi):
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    
    # 从地支列表中排除日支和年支
    day_zhi_list = filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    
    count_day = count_shensha(day_zhi, day_zhi_list, jiang_xing)
    count_year = count_shensha(year_zhi, year_zhi_list, jiang_xing)
    return count_day + count_year

def is_jiang_xing(bazi):
    return calculate_jiang_xing(bazi) > 0

# --- 华盖: 以日支或年支对比四柱地支
# 参考表: hua_gai
# main: 日支或年支, zhi_list: 四柱地支(排除主支)

def calculate_hua_gai(bazi):
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    
    # 从地支列表中排除日支和年支
    day_zhi_list = filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    
    count_day = count_shensha(day_zhi, day_zhi_list, hua_gai)
    count_year = count_shensha(year_zhi, year_zhi_list, hua_gai)
    return count_day + count_year

def is_hua_gai(bazi):
    return calculate_hua_gai(bazi) > 0

# --- 驿马: 以日支或年支对比四柱地支
# 参考表: yi_ma）
# main: 日支或年支, zhi_list: 四柱地支(排除主支)

def calculate_yi_ma(bazi):
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    
    # 从地支列表中排除日支和年支
    day_zhi_list = filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    
    count_day = count_shensha(day_zhi, day_zhi_list, yi_ma)
    count_year = count_shensha(year_zhi, year_zhi_list, yi_ma)
    return count_day + count_year

def is_yi_ma(bazi):
    return calculate_yi_ma(bazi) > 0

# --- 劫煞: 以日支或年支对比四柱地支
# 参考表: jie_sha
# main: 日支或年支, zhi_list: 四柱地支(排除主支)

def calculate_jie_sha(bazi):
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    
    # 从地支列表中排除日支和年支
    day_zhi_list = filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    
    count_day = count_shensha(day_zhi, day_zhi_list, jie_sha)
    count_year = count_shensha(year_zhi, year_zhi_list, jie_sha)
    return count_day + count_year

def is_jie_sha(bazi):
    return calculate_jie_sha(bazi) > 0

# --- 亡神: 以日支或年支对比四柱地支
# 参考表: wang_shen
# main: 日支或年支, zhi_list: 四柱地支(排除主支)

def calculate_wang_shen(bazi):
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    
    # 从地支列表中排除日支和年支
    day_zhi_list = filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    
    count_day = count_shensha(day_zhi, day_zhi_list, wang_shen)
    count_year = count_shensha(year_zhi, year_zhi_list, wang_shen)
    return count_day + count_year

def is_wang_shen(bazi):
    return calculate_wang_shen(bazi) > 0

# --- 桃花: 以日支或年支对比四柱地支
# 参考表: tao_hua
# main: 日支或年支, zhi_list: 四柱地支(排除主支)

def calculate_tao_hua(bazi):
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    
    # 从地支列表中排除日支和年支
    day_zhi_list = filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    
    count_day = count_shensha(day_zhi, day_zhi_list, tao_hua)
    count_year = count_shensha(year_zhi, year_zhi_list, tao_hua)
    return count_day + count_year

def is_tao_hua(bazi):
    return calculate_tao_hua(bazi) > 0

# --- 孤辰: 以年支对比四柱地支
# 参考表: gu_chen
# main: 年支, zhi_list: 四柱地支(排除主支)

def calculate_gu_chen(bazi):
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    return count_shensha(year_zhi, year_zhi_list, gu_chen)

def is_gu_chen(bazi):
    return calculate_gu_chen(bazi) > 0

# --- 寡宿: 以年支对比四柱地支
# 参考表: gou_xiu
# main: 年支, zhi_list: 四柱地支(排除主支)

def calculate_gua_su(bazi):
    year_zhi = bazi.getYearZhi()
    all_zhi = get_gan_or_zhi(bazi, 1)
    year_zhi_list = filter_zhi_from_list(all_zhi, year_zhi)
    return count_shensha(year_zhi, year_zhi_list, gua_su)

def is_gua_su(bazi):
    return calculate_gua_su(bazi) > 0

# --- 空亡: 以日支对比四柱地支
# 参考表: kong_wang
# main: 日支, zhi_list: 四柱地支(排除主支)
def is_kong_wang(bazi):
    day_ganzhi = bazi.getDayGan() + bazi.getDayZhi()  # 日柱
    kong_list = xun_kong.get(day_ganzhi)
    if not kong_list:
        return False
    year_zhi = bazi.getYearZhi()
    month_zhi = bazi.getMonthZhi()
    time_zhi = bazi.getTimeZhi()
    
    return (year_zhi in kong_list) or (month_zhi in kong_list) or (time_zhi in kong_list)

# --- 神煞注册表 ---
SHENSHA_RULES = [
    {
        "name": "天德贵人",
        "desc": "吉神，贵人扶持，主仁慈、聪明、善良，遵纪守法，一生是非少，逢凶化吉，女命主善良贤慧，配贵夫",
        "checker": is_tian_de,
        "use": "月支+其他"
    },
    {
        "name": "月德贵人",
        "desc": "吉神，贵人扶持，月德是阴德，其功效隐密，月德入命，主福分深厚，长寿，不犯官刑。为人多仁慈敏慧，能逢凶化吉，去灾招祥，然人命若带月德，亦需本身勤勉自助，才能在紧要关头获得天助。",
        "checker": is_yue_de,
        "use": "月支+其他"
    },
    {
        "name": "天月二德",
        "desc": "大吉，凡八字中有天月二德，其人恺悌慈祥，待人至诚仁厚。",
        "checker": is_tian_yue_erde,
        "use": "月支+其他"
    },
    {
        "name": "天乙贵人",
        "desc": "吉神，贵人扶持，若人遇之主荣名早达，成事多助，官禄易进。",
        "checker": is_tian_yi_guiren,
        "use": "日干/年干+地支"
    },
    {
        "name": "禄神",
        "desc": "吉神，主衣禄充足，但要按喜忌神分，若禄为忌神则为凶煞（有空会增加判断逻辑）",
        "checker": is_lu_shen,
        "use": "日干+地支"
    },
    {
        "name": "文昌",
        "desc": "吉神，主生性聪明，文笔极好，逢凶化吉。",
        "checker": is_wen_chang,
        "use": "日干+地支"
    },
    {
        "name": "羊刃",
        "desc": "煞神，主性格刚烈、易有冲突、遇事易极端，若为忌神则主灾祸、血光、刑伤。",
        "checker": is_yang_ren,
        "use": "日干+地支"
    },
    {
        "name": "红艳煞",
        "desc": "煞神，主异性缘分强、情感丰富，若为忌神则主感情纠纷、桃色是非。",
        "checker": is_hong_yan_sha,
        "use": "日干+地支"
    }
    ,
    {
        "name": "三奇",
        "desc": "吉神，主聪明才智、机遇佳，遇三奇者多有贵人相助、事业顺利。三奇为四柱天干中顺序出现的乙丙丁、甲戊庚、壬癸辛。",
        "checker": is_san_qi,
        "use": "四柱天干顺序"
    },
    {
        "name": "将星",
        "desc": "主权力、领导、威严，为吉神，遇之主贵人相助、官位提升。",
        "checker": is_jiang_xing,
        "use": "日支或年支+地支"
    },
    {
        "name": "华盖",
        "desc": "主文学艺术才华、清高独立，为双面神，既主才华横溢，亦主孤独清高。",
        "checker": is_hua_gai,
        "use": "日支或年支+地支"
    },
    {
        "name": "驿马",
        "desc": "主奔波、流动、变化，为双面神，既主事业拓展、旅行，亦主漂泊不定。",
        "checker": is_yi_ma,
        "use": "日支或年支+地支"
    },
    {
        "name": "劫煞",
        "desc": "主劫难、变故、突发事件，为凶煞，遇之多有突发变动、灾祸。",
        "checker": is_jie_sha,
        "use": "日支或年支+地支"
    },
    {
        "name": "亡神",
        "desc": "主损失、破财、不详，为凶煞，遇之多有损失、不祥之事。",
        "checker": is_wang_shen,
        "use": "日支或年支+地支"
    },
    {
        "name": "桃花",
        "desc": "主感情、姻缘、异性缘，为双面神，既主良缘美姻，亦主情感纠纷。",
        "checker": is_tao_hua,
        "use": "日支或年支+地支"
    },
    {
        "name": "孤辰",
        "desc": "主孤独、独立，感情路较坎坷，适合晚婚，男忌孤辰。",
        "checker": is_gu_chen,
        "use": "日支+地支"
    },
    {
        "name": "寡宿",
        "desc": "主清冷、孤寡，女性遇之婚姻不顺，男性则性格孤僻，女忌寡宿。",
        "checker": is_gua_su,
        "use": "日支+地支"
    },
    {
        "name": "空亡",
        "desc": "如吉神落空亡，则吉力减半，如凶神落空亡，则凶力大减。",
        "checker": is_kong_wang,
        "use": "日柱+地支"
    }
]
    
def get_shensha(bazi):
    """
    根据八字计算神煞
    :param bazi: 包含年、月、日、时柱干支的对象
    :return: 神煞列表（名称+解释）
    """
    shensha_list = []
    for rule in SHENSHA_RULES:
        if rule["checker"](bazi):
            shensha_list.append((rule["name"], rule["desc"]))
    return shensha_list



def is_yang_gong_taboo(lunar_date):
    """Check if a lunar date is one of the Yang Gong Thirteen Taboos (杨公十三忌)"""
    month = lunar_date.getMonth()
    day = lunar_date.getDay()
    
    yang_gong_taboos = [
        (1, 13),  # 正月十三
        (2, 11),  # 二月十一
        (3, 9),   # 三月初九
        (4, 7),   # 四月初七
        (5, 5),   # 五月初五
        (6, 3),   # 六月初三
        (7, 1),   # 七月初一
        (7, 29),  # 七月二十九
        (8, 27),  # 八月二十七
        (9, 25),  # 九月二十五
        (10, 23), # 十月二十三
        (11, 21), # 十一月二十一
        (12, 19)  # 十二月十九
    ]
    
    return (month, day) in yang_gong_taboos

def is_po_ri(lunar_date):
    """Check if a lunar date is a breaking day (破日)
    Each lunar month has a specific earthly branch that is considered a breaking day.
    """
    month = lunar_date.getMonth()
    day_zhi = lunar_date.getDayZhi()
    
    # Mapping of lunar month to breaking day earthly branch
    po_ri_mapping = {
        1: '申',  # 正月破日 - 申日
        2: '酉',  # 二月破日 - 酉日
        3: '戌',  # 三月破日 - 戌日
        4: '亥',  # 四月破日 - 亥日
        5: '子',  # 五月破日 - 子日
        6: '丑',  # 六月破日 - 丑日
        7: '寅',  # 七月破日 - 寅日
        8: '卯',  # 八月破日 - 卯日
        9: '辰',  # 九月破日 - 辰日
        10: '巳', # 十月破日 - 巳日
        11: '午', # 十一月破日 - 午日
        12: '未'  # 十二月破日 - 未日
    }
    
    # Check if the day's earthly branch matches the breaking day for this lunar month
    return day_zhi == po_ri_mapping.get(month)

def is_si_jue_ri(date_solar):
    """Check if a date is one of the '四绝日' (Four "Jue" Days)
    These are the days before Li Chun, Li Xia, Li Qiu, and Li Dong
    """
    # Get the solar date
    year = date_solar.getYear()
    
    # Get the JieQi table for this year
    lunar = date_solar.getLunar()
    jieqi_table = lunar.getJieQiTable()
    
    # The four "Jue" days are the days before:
    # 立春 (Li Chun), 立夏 (Li Xia), 立秋 (Li Qiu), 立冬 (Li Dong)
    jue_dates = []
    
    for jieqi_name in ["立春", "立夏", "立秋", "立冬"]:
        if jieqi_name in jieqi_table:
            jieqi_date = jieqi_table[jieqi_name]
            # Get the day before
            jue_date = jieqi_date.next(-1)
            jue_dates.append(jue_date.toString())
    
    # Check if the current date is one of the "Jue" days
    current_date_str = f"{date_solar.getYear()}-{date_solar.getMonth():02d}-{date_solar.getDay():02d}"
    return current_date_str in jue_dates

def is_si_li_ri(date_solar):
    """Check if a date is one of the '四离日' (Four "Li" Days)
    These are the days before Chun Fen, Xia Zhi, Qiu Fen, and Dong Zhi
    """
    # Get the solar date
    year = date_solar.getYear()
    
    # Get the JieQi table for this year
    lunar = date_solar.getLunar()
    jieqi_table = lunar.getJieQiTable()
    
    # The four "Li" days are the days before:
    # 春分 (Chun Fen), 夏至 (Xia Zhi), 秋分 (Qiu Fen), 冬至 (Dong Zhi)
    li_dates = []
    
    for jieqi_name in ["春分", "夏至", "秋分", "冬至"]:
        if jieqi_name in jieqi_table:
            jieqi_date = jieqi_table[jieqi_name]
            # Get the day before
            li_date = jieqi_date.next(-1)
            li_dates.append(li_date.toString())
    
    # Check if the current date is one of the "Li" days
    current_date_str = f"{date_solar.getYear()}-{date_solar.getMonth():02d}-{date_solar.getDay():02d}"
    return current_date_str in li_dates



