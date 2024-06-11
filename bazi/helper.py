import datetime

import openai
import os
from bazi.constants import relationships, wang_xiang_value, gan_wuxing, hidden_gan_ratios, zhi_seasons, season_phases, \
    wuxing_relations, zhi_wuxing, gan_yinyang, peiou_xingge, tigang, liu_he, wu_he, wuxing, gan_xiang_chong, \
    zhi_xiang_chong, gui_ren, tian_de, yue_de, wu_bu_yu_shi, lu_shen
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
        analysis += "•身弱者走正官运，为忌神，今年身体不好，会变成体弱多病，因为“身弱不得任财官”也。<br>"
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
            analysis += "•男命七杀两个以上，又逢七杀运，会为子女奔波i操劳，甚至受其所累。<br>"
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


def calculate_day_guiren(bazi: EightChar):
    ri_yuan = bazi.getDayGan()
    zhi = get_gan_or_zhi(bazi, 1)
    day_guiren = 0
    for i in range(len(zhi)):
        if (ri_yuan, zhi[i]) in gui_ren:
            day_guiren += 1
    return day_guiren


def calculate_year_guiren(bazi: EightChar):
    year_gan = bazi.getYearGan()
    zhi = get_gan_or_zhi(bazi, 1)
    year_guiren = 0
    for i in range(len(zhi)):
        if (year_gan, zhi[i]) in gui_ren:
            year_guiren += 1
    return year_guiren


def calculate_tian_de(bazi: EightChar):
    month_zhi = bazi.getMonthZhi()
    ganzhi = bazi.toString().split()
    ganzhi.pop(1)
    total_tian_de = 0
    for gz in ganzhi:
        for i in range(2):
            if (month_zhi, ganzhi[i]) in tian_de:
                total_tian_de += 1
    return total_tian_de


def calculate_yue_de(bazi: EightChar):
    month_zhi = bazi.getMonthZhi()
    ganzhi = bazi.toString().split()
    ganzhi.pop(1)
    total_yue_de = 0
    for gz in ganzhi:
        for i in range(2):
            if (month_zhi, ganzhi[i]) in yue_de:
                total_yue_de += 1
    return total_yue_de


def calculate_wen_chang(bazi: EightChar):
    total_wen_chang = 0
    ri_yuan = bazi.getDayGan()
    zhi = get_gan_or_zhi(bazi, 1)
    for i in range(len(zhi)):
        if (ri_yuan, zhi[i]) in gui_ren:
            total_wen_chang += 1
    return total_wen_chang


def calculate_lu_shen(bazi: EightChar):
    total_lu_shen = 0
    ri_yuan = bazi.getDayGan()
    year_gan = bazi.getYearGan()
    if (ri_yuan, bazi.getDayZhi()) in lu_shen:
        total_lu_shen += 1
    if (year_gan, bazi.getYearZhi()) in lu_shen:
        total_lu_shen += 1
    return total_lu_shen
