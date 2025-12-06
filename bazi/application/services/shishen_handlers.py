"""
ShiShen Fortune Handlers.

Contains handler functions for analyzing different ShiShen (十神) types
in the context of yearly fortune (流年) analysis. Each handler generates
Chinese text-based analysis for a specific ShiShen type.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

# Domain layer imports (DIP-compliant)
from bazi.domain.constants import is_harmony

if TYPE_CHECKING:
    from lunar_python import EightChar


def _contain_shishen(target: str, shishen_list: List) -> bool:
    """Check if shishen_list contains a target ShiShen."""
    for main, sublist in shishen_list:
        if main == target or target in sublist:
            return True
    return False


def _find_shishen_indices(target: str, shishen_list: List) -> List[int]:
    """Find indices where target ShiShen appears.

    Returns flat indices where even indices (0,2,4,6) are main stems,
    odd indices (1,3,5,7) are hidden stems sections.
    """
    indices = []
    for pillar_idx, (main_shishen, hidden_list) in enumerate(shishen_list):
        base_idx = pillar_idx * 2
        if main_shishen == target:
            indices.append(base_idx)
        if target in hidden_list:
            indices.append(base_idx + 1)
    return indices


def handle_zheng_cai(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 正财 (Direct Wealth) fortune analysis."""
    analysis = "•流年走正财运， 未婚者有结婚之机会，已婚者太太能帮助先生，先生也较疼老婆。<br>"

    if is_harmony(bazi.getDayGan(), year_bazi.getYearGan()) or is_harmony(
        bazi.getMonthZhi(), year_bazi.getYearZhi()
    ):
        analysis += "•正财合日主或月支，在钱财或身体方面会有损失"
        if not is_male:
            analysis += "，夫妻间感情会变不好"
        analysis += "。<br>"

    if (
        not is_strong
        and _contain_shishen('正印', shishen)
        and _contain_shishen('比肩', shishen)
        and _contain_shishen('比劫', shishen)
    ):
        analysis += "•本命身弱而带有正印，比肩，比劫， 注意破财、损命。"
        if is_male:
            analysis += "太太与自己母亲不和，会有婆媳问题。"
        analysis += "<br>"

    if len(_find_shishen_indices('正财', shishen)) >= 2:
        analysis += "•财多又走财年， 很有异性缘"

    if not is_strong:
        analysis += (
            "•身弱，正财为忌神， 很会花钱，不重视钱财。<br>"
            "•要变通或较费力才会赚到钱。<br>"
            "•会有破财或桃色纠纷。<br>"
        )
    else:
        analysis += "•身强， 正财为喜神， 较有赚钱机会， 赚钱不难。<br>"
        if not (
            _contain_shishen('正财', shishen) or _contain_shishen('偏财', shishen)
        ):
            analysis += "•但本命无正财偏财， 宜从事劳力密集之行业。<br>"

    return analysis


def handle_pian_cai(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 偏财 (Indirect Wealth) fortune analysis."""
    analysis = "•流年走偏财，注意父亲身体状况，较不喜欢固定的工作，喜欢挑剔，感情亦不专。<br>"

    if not is_male and is_strong and _contain_shishen('七杀', shishen):
        analysis += "•女命身强，走偏财，本命有七杀， 风情万种， 很开放， 易入上流社会。易养小男人或赚钱养男人<br>"

    if not is_strong:
        analysis += "•身弱，走偏财，赚钱很难。<br>"
        analysis += "•身弱，偏财为忌神，宜戒色；不宜生活浮夸，钱少花一点，要懂得节约。<br>"
    else:
        analysis += "•身强，偏财为喜神，为人慷慨豪爽，懂得人情世故，交际特别好。<br>"
        analysis += "•身强，偏财为喜神，得正职，亦主财运亨通，易有横财。<br>"

    if (
        is_male
        and is_strong
        and _contain_shishen('七杀', shishen)
        and _contain_shishen('偏财', shishen)
    ):
        analysis += "•男命身强，走偏财，命中又有七杀及偏财，容易有名声与地位，但好色居多、养妾<br>"

    indices = _find_shishen_indices('偏财', shishen)
    gan_indices = [i for i in indices if i % 2 == 0]
    if len(gan_indices) > 0:
        analysis += "•偏财通根，外面养妾，偷偷摸摸。<br>"

    if not (
        _contain_shishen('正财', shishen) or _contain_shishen('偏财', shishen)
    ):
        analysis += "•走偏财运，命中无正财，偏财，为人没有金钱观念，财来财去，不知如何赚钱，亦不重视钱财。<br>"

    return analysis


def handle_zheng_guan(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 正官 (Direct Officer) fortune analysis."""
    analysis = "•走正官运时很好面子<br>"

    if (
        is_strong
        and _contain_shishen('正官', shishen)
        and _contain_shishen('七杀', shishen)
    ):
        analysis += "•身强，正官为喜神，原命又有正官和七杀，主在社会上有名望，地位。<br>"

    if (
        not is_strong
        and not _contain_shishen('正官', shishen)
        and not _contain_shishen('七杀', shishen)
    ):
        analysis += "•身弱，正官为忌神，本命没有正官和七杀，主压力特别大，精神也易紧张。<br>"

    if _contain_shishen('伤官', shishen):
        analysis += "•本命有伤官，主有血光之灾，或名声、地位有损害。<br>"

    if not is_male:
        analysis += "•女命流年走正官，会想结婚。<br>"
        if _contain_shishen('正官', shishen) and _contain_shishen('七杀', shishen):
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

    if _contain_shishen('食神', shishen):
        analysis += "•走正官运时，原命带有食神，行事上显得懒散，不积极，不带劲。<br>"

    return analysis


def handle_qi_sha(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 七杀 (Seven Killings) fortune analysis."""
    analysis = ""

    if not is_male:
        analysis += "•女命行七杀，较不得老公宠爱、婚姻比较辛苦、与老公理念较不相同。<br>"
        analysis += "•女命行七杀，异性缘好，结婚后还是一样具有男人缘，须自我控制。<br>"
        if not is_strong:
            analysis += "•女命身弱，走七杀运时会被男人欺负。<br>"
        if _contain_shishen('正官', shishen) and _contain_shishen('七杀', shishen):
            analysis += "•女命有『正官、七杀』，又逢七杀，易有外遇，容易受人欺凌，更易有感情纠纷。<br>"
    else:
        if _contain_shishen('正官', shishen):
            analysis += "•男命走七杀，本命有正官，喜欢在风月场所或在女人堆中鬼混。<br>"
        qisha_indices = _find_shishen_indices('七杀', shishen)
        if len(qisha_indices) >= 2:
            analysis += "•男命七杀两个以上，又逢七杀运，会为子女奔波操劳，甚至受其所累。<br>"

    if not is_strong:
        analysis += "•身弱行七杀，理想较难实现，容易离婚，易换工作。<br>"
        analysis += "•身弱，杀为忌神，性情上显得刚愎自用。<br>"
        if _contain_shishen('七杀', shishen):
            analysis += "•身弱，本命有七杀，又行七杀运，杀多攻身，容易挥霍无度，不知节制，爱面子。<br>"
    else:
        if _contain_shishen('七杀', shishen):
            if is_male:
                analysis += "•身强，本命有七杀，又行七杀运，杀多攻身，易遭小人陷害，破财，有血光之灾。<br>"
            else:
                analysis += "•女命身强，本命有七杀，又行七杀运，易感情生变，或讨小男人，或血光之灾。<br>"
        else:
            analysis += "•身强走七杀，在工作或事业上容易拥有地位和权威。<br>"

    return analysis


def handle_zheng_yin(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 正印 (Direct Seal) fortune analysis."""
    analysis = "•流运走正印，母亲身体状况容易变差。<br>"
    analysis += "•流运走正印，较不喜欢动，个性固执，主观强，但较有慈悲心、有佛缘。<br>"
    analysis += "•走印运时，很想购置不动产，同时亦会有机会获得祖产之机会。<br>"

    if is_strong:
        analysis += "•身强走正印，为忌神，烦恼特别多。<br>"
        if _contain_shishen('正官', shishen) and _contain_shishen('正印', shishen):
            analysis += "•身强走正印，命中有『正官，正印』，在本运内压力很大，愿望难发挥，多顾忌。<br>"
        if _contain_shishen('正财', shishen):
            analysis += "•身强，命中又有正财，逢正印运，比较容易丢掉职业，损败家业、或换行业。<br>"
    else:
        analysis += "•身弱走正印，处处逢贵人。<br>"
        analysis += "•身弱逢正印，在学术上容易出名，或特别有机会接近宗教。<br>"

    if is_male:
        if _contain_shishen('正财', shishen):
            analysis += "•男命走正印，命中又有正财，今年太太与母亲会有不和之现象发生，即婆媳不和。<br>"
    else:
        if _contain_shishen('正财', shishen):
            analysis += "•女命走正印，命中又有正财，较易与母亲顶嘴，做事得过且过。<br>"

    if _contain_shishen('正印', shishen) or _contain_shishen('偏印', shishen):
        analysis += "•八字有正印或偏印，又逢正印，做事缺乏专注力，事业易变动，说话做事，颠三倒四。<br>"

    return analysis


def handle_pian_yin(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 偏印 (Indirect Seal) fortune analysis."""
    analysis = "•流年走偏印，很想买不动产。<br>"
    analysis += "•走偏印，心性不稳定，常三心两意，比较不易成功。<br>"

    if is_strong:
        analysis += "•身强，走偏印运，喜外出结缘，爱花钱。<br>"
        analysis += "•走偏印而为忌神，母亲之健康会变不好。<br>"
        if _contain_shishen('偏印', shishen):
            analysis += "•身强，命中有偏印，又逢偏印，较多疑，想得太多，易有躁郁证、自闭症状，甚者更会自杀。<br>"
    else:
        analysis += "•身弱，走偏印运，在学业、家庭、工作上较易得贵人相助，名利两全。<br>"

    if _contain_shishen('食神', shishen):
        analysis += "•流年走偏印，本命有食神，称为『枭印夺食』，主常遭陷害，被扯后腿，做事多败少成"
        if not is_male:
            analysis += "；女命易得肿瘤"
        analysis += "。<br>"

    if _contain_shishen('正印', shishen):
        analysis += "•流年走偏印，本命有正印，人会非常主观。<br>"

    return analysis


def handle_bi_jian(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 比肩 (Shoulder to Shoulder) fortune analysis."""
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


def handle_bi_jie(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 比劫 (Rob Wealth) fortune analysis."""
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


def handle_shang_guan(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 伤官 (Hurting Officer) fortune analysis."""
    analysis = "•当走伤官运时，爱受别人夸赞，不喜欢别人批评。<br>"

    if not is_male:
        analysis += "•女命走伤官，爱管丈夫，喜叼念丈夫，句句伤丈夫之心，故易有婚变。<br>"
    else:
        analysis += "•男命走伤官，奇招主意特别多。<br>"

    if _contain_shishen('食神', shishen):
        analysis += "•走伤官，命中有食神，如果从事教育工作，可以桃李满天下。<br>"

    if _contain_shishen('正官', shishen):
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


def handle_shi_shen(
    bazi: EightChar,
    shishen: List,
    year_bazi: EightChar,
    is_strong: bool,
    is_male: bool,
) -> str:
    """Handle 食神 (Eating God) fortune analysis."""
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

    if _contain_shishen('偏印', shishen):
        analysis += "•走食神，命中带有偏印，称为『枭印夺食』，主才华施展不开，做事常会前功尽弃，多败少成，导致内心郁闷。<br>"
        analysis += "•『枭印夺食』，容易遇小人，易遭人陷害，甚至有性命之忧。<br>"
        analysis += "•『枭印夺食』，容易被人扯后腿，甚或自己也会扯别人后腿，以致误人误己。<br>"
        analysis += "•『枭印夺食』，容易遭遇意外之灾；或有隐疾复发，而发生致命危险。<br>"
        if not is_male:
            analysis += "•『枭印夺食』，女命或流产；或有妇女病及肿瘤。<br>"

    if _contain_shishen('伤官', shishen):
        analysis += "•流运走食神，命中有伤官者，主才华施展不开，多学不专，文武似兼具，但很难专精。<br>"

    if _contain_shishen('七杀', shishen):
        analysis += "•流运走食神，命中有七杀者，主权势被制住，凶不起来。<br>"

    return analysis


# Handler mapping for ShiShen types
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
    '食神': handle_shi_shen,
}
