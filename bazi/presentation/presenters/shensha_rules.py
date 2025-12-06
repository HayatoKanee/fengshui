"""
ShenSha Rules for View Layer.

Contains ShenSha detection rules and descriptions for template display.
This module provides comprehensive ShenSha analysis with Chinese descriptions.
"""
from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

from bazi.constants import (
    gui_ren,
    gu_chen,
    gua_su,
    hong_yan_sha,
    hua_gai,
    jie_sha,
    jiang_xing,
    lu_shen,
    tao_hua,
    tian_de,
    wang_shen,
    wen_chang,
    xun_kong,
    yang_ren,
    yi_ma,
    yue_de,
)

if TYPE_CHECKING:
    from lunar_python import EightChar


def _get_gan_or_zhi(bazi: EightChar, get_gan: int = 0) -> List[str]:
    """Extract stems (get_gan=0) or branches (get_gan=1) from BaZi."""
    gan_or_zhi = []
    for ganzhi in bazi.toString().split():
        gan_or_zhi.append(ganzhi[get_gan])
    return gan_or_zhi


def _count_shensha(main: str, zhi_list: List[str], table: set) -> int:
    """Count matches in a shensha table."""
    count = 0
    for z in zhi_list:
        if (main, z) in table:
            count += 1
    return count


def _filter_zhi_from_list(zhi_list: List[str], zhi_to_exclude: str) -> List[str]:
    """Filter out a specific branch from a list."""
    return [z for z in zhi_list if z != zhi_to_exclude]


# --- Individual ShenSha detection functions ---

def _calculate_tian_de(bazi: EightChar) -> int:
    """天德贵人: month branch vs four pillar stems."""
    month_zhi = bazi.getMonthZhi()
    gan_list = _get_gan_or_zhi(bazi, 0)
    return _count_shensha(month_zhi, gan_list, tian_de)


def _calculate_yue_de(bazi: EightChar) -> int:
    """月德贵人: month branch vs four pillar stems."""
    month_zhi = bazi.getMonthZhi()
    gan_list = _get_gan_or_zhi(bazi, 0)
    return _count_shensha(month_zhi, gan_list, yue_de)


def _calculate_day_guiren(bazi: EightChar) -> int:
    """天乙贵人（日干）: day stem vs four pillar branches."""
    day_gan = bazi.getDayGan()
    zhi_list = _get_gan_or_zhi(bazi, 1)
    return _count_shensha(day_gan, zhi_list, gui_ren)


def _calculate_year_guiren(bazi: EightChar) -> int:
    """天乙贵人（年干）: year stem vs four pillar branches."""
    year_gan = bazi.getYearGan()
    zhi_list = _get_gan_or_zhi(bazi, 1)
    return _count_shensha(year_gan, zhi_list, gui_ren)


def _calculate_lu_shen(bazi: EightChar) -> int:
    """禄神: day stem vs four pillar branches."""
    day_gan = bazi.getDayGan()
    zhi_list = _get_gan_or_zhi(bazi, 1)
    return _count_shensha(day_gan, zhi_list, lu_shen)


def _calculate_wen_chang(bazi: EightChar) -> int:
    """文昌: day stem vs four pillar branches."""
    day_gan = bazi.getDayGan()
    zhi_list = _get_gan_or_zhi(bazi, 1)
    return _count_shensha(day_gan, zhi_list, wen_chang)


def _calculate_yang_ren(bazi: EightChar) -> int:
    """羊刃: day stem vs four pillar branches."""
    day_gan = bazi.getDayGan()
    zhi_list = _get_gan_or_zhi(bazi, 1)
    return _count_shensha(day_gan, zhi_list, yang_ren)


def _calculate_hong_yan_sha(bazi: EightChar) -> int:
    """红艳煞: day stem vs four pillar branches."""
    day_gan = bazi.getDayGan()
    zhi_list = _get_gan_or_zhi(bazi, 1)
    return _count_shensha(day_gan, zhi_list, hong_yan_sha)


def _calculate_jiang_xing(bazi: EightChar) -> int:
    """将星: day/year branch vs other branches."""
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)

    day_zhi_list = _filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)

    count_day = _count_shensha(day_zhi, day_zhi_list, jiang_xing)
    count_year = _count_shensha(year_zhi, year_zhi_list, jiang_xing)
    return count_day + count_year


def _calculate_hua_gai(bazi: EightChar) -> int:
    """华盖: day/year branch vs other branches."""
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)

    day_zhi_list = _filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)

    count_day = _count_shensha(day_zhi, day_zhi_list, hua_gai)
    count_year = _count_shensha(year_zhi, year_zhi_list, hua_gai)
    return count_day + count_year


def _calculate_yi_ma(bazi: EightChar) -> int:
    """驿马: day/year branch vs other branches."""
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)

    day_zhi_list = _filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)

    count_day = _count_shensha(day_zhi, day_zhi_list, yi_ma)
    count_year = _count_shensha(year_zhi, year_zhi_list, yi_ma)
    return count_day + count_year


def _calculate_jie_sha(bazi: EightChar) -> int:
    """劫煞: day/year branch vs other branches."""
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)

    day_zhi_list = _filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)

    count_day = _count_shensha(day_zhi, day_zhi_list, jie_sha)
    count_year = _count_shensha(year_zhi, year_zhi_list, jie_sha)
    return count_day + count_year


def _calculate_wang_shen(bazi: EightChar) -> int:
    """亡神: day/year branch vs other branches."""
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)

    day_zhi_list = _filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)

    count_day = _count_shensha(day_zhi, day_zhi_list, wang_shen)
    count_year = _count_shensha(year_zhi, year_zhi_list, wang_shen)
    return count_day + count_year


def _calculate_tao_hua(bazi: EightChar) -> int:
    """桃花: day/year branch vs other branches."""
    day_zhi = bazi.getDayZhi()
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)

    day_zhi_list = _filter_zhi_from_list(all_zhi, day_zhi)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)

    count_day = _count_shensha(day_zhi, day_zhi_list, tao_hua)
    count_year = _count_shensha(year_zhi, year_zhi_list, tao_hua)
    return count_day + count_year


def _calculate_gu_chen(bazi: EightChar) -> int:
    """孤辰: year branch vs other branches."""
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)
    return _count_shensha(year_zhi, year_zhi_list, gu_chen)


def _calculate_gua_su(bazi: EightChar) -> int:
    """寡宿: year branch vs other branches."""
    year_zhi = bazi.getYearZhi()
    all_zhi = _get_gan_or_zhi(bazi, 1)
    year_zhi_list = _filter_zhi_from_list(all_zhi, year_zhi)
    return _count_shensha(year_zhi, year_zhi_list, gua_su)


# --- Boolean checker functions ---

def _is_tian_de(bazi: EightChar) -> bool:
    return _calculate_tian_de(bazi) > 0


def _is_yue_de(bazi: EightChar) -> bool:
    return _calculate_yue_de(bazi) > 0


def _is_tian_yue_erde(bazi: EightChar) -> bool:
    return _calculate_tian_de(bazi) > 0 and _calculate_yue_de(bazi) > 0


def _is_tian_yi_guiren(bazi: EightChar) -> bool:
    return _calculate_day_guiren(bazi) > 0 or _calculate_year_guiren(bazi) > 0


def _is_lu_shen(bazi: EightChar) -> bool:
    return _calculate_lu_shen(bazi) > 0


def _is_wen_chang(bazi: EightChar) -> bool:
    return _calculate_wen_chang(bazi) > 0


def _is_yang_ren(bazi: EightChar) -> bool:
    return _calculate_yang_ren(bazi) > 0


def _is_hong_yan_sha(bazi: EightChar) -> bool:
    return _calculate_hong_yan_sha(bazi) > 0


def _is_san_qi(bazi: EightChar) -> bool:
    """三奇: sequential three-stem combination in pillars."""
    gan_list = _get_gan_or_zhi(bazi, 0)
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


def _is_jiang_xing(bazi: EightChar) -> bool:
    return _calculate_jiang_xing(bazi) > 0


def _is_hua_gai(bazi: EightChar) -> bool:
    return _calculate_hua_gai(bazi) > 0


def _is_yi_ma(bazi: EightChar) -> bool:
    return _calculate_yi_ma(bazi) > 0


def _is_jie_sha(bazi: EightChar) -> bool:
    return _calculate_jie_sha(bazi) > 0


def _is_wang_shen(bazi: EightChar) -> bool:
    return _calculate_wang_shen(bazi) > 0


def _is_tao_hua(bazi: EightChar) -> bool:
    return _calculate_tao_hua(bazi) > 0


def _is_gu_chen(bazi: EightChar) -> bool:
    return _calculate_gu_chen(bazi) > 0


def _is_gua_su(bazi: EightChar) -> bool:
    return _calculate_gua_su(bazi) > 0


def _is_kong_wang(bazi: EightChar) -> bool:
    """空亡: day pillar vs other branches."""
    day_ganzhi = bazi.getDayGan() + bazi.getDayZhi()
    kong_list = xun_kong.get(day_ganzhi)
    if not kong_list:
        return False
    year_zhi = bazi.getYearZhi()
    month_zhi = bazi.getMonthZhi()
    time_zhi = bazi.getTimeZhi()
    return year_zhi in kong_list or month_zhi in kong_list or time_zhi in kong_list


# --- ShenSha Rules Registry ---

SHENSHA_RULES = [
    {
        "name": "天德贵人",
        "desc": "吉神，贵人扶持，主仁慈、聪明、善良，遵纪守法，一生是非少，逢凶化吉，女命主善良贤慧，配贵夫",
        "checker": _is_tian_de,
    },
    {
        "name": "月德贵人",
        "desc": "吉神，贵人扶持，月德是阴德，其功效隐密，月德入命，主福分深厚，长寿，不犯官刑。为人多仁慈敏慧，能逢凶化吉，去灾招祥，然人命若带月德，亦需本身勤勉自助，才能在紧要关头获得天助。",
        "checker": _is_yue_de,
    },
    {
        "name": "天月二德",
        "desc": "大吉，凡八字中有天月二德，其人恺悌慈祥，待人至诚仁厚。",
        "checker": _is_tian_yue_erde,
    },
    {
        "name": "天乙贵人",
        "desc": "吉神，贵人扶持，若人遇之主荣名早达，成事多助，官禄易进。",
        "checker": _is_tian_yi_guiren,
    },
    {
        "name": "禄神",
        "desc": "吉神，主衣禄充足，但要按喜忌神分，若禄为忌神则为凶煞（有空会增加判断逻辑）",
        "checker": _is_lu_shen,
    },
    {
        "name": "文昌",
        "desc": "吉神，主生性聪明，文笔极好，逢凶化吉。",
        "checker": _is_wen_chang,
    },
    {
        "name": "羊刃",
        "desc": "煞神，主性格刚烈、易有冲突、遇事易极端，若为忌神则主灾祸、血光、刑伤。",
        "checker": _is_yang_ren,
    },
    {
        "name": "红艳煞",
        "desc": "煞神，主异性缘分强、情感丰富，若为忌神则主感情纠纷、桃色是非。",
        "checker": _is_hong_yan_sha,
    },
    {
        "name": "三奇",
        "desc": "吉神，主聪明才智、机遇佳，遇三奇者多有贵人相助、事业顺利。三奇为四柱天干中顺序出现的乙丙丁、甲戊庚、壬癸辛。",
        "checker": _is_san_qi,
    },
    {
        "name": "将星",
        "desc": "主权力、领导、威严，为吉神，遇之主贵人相助、官位提升。",
        "checker": _is_jiang_xing,
    },
    {
        "name": "华盖",
        "desc": "主文学艺术才华、清高独立，为双面神，既主才华横溢，亦主孤独清高。",
        "checker": _is_hua_gai,
    },
    {
        "name": "驿马",
        "desc": "主奔波、流动、变化，为双面神，既主事业拓展、旅行，亦主漂泊不定。",
        "checker": _is_yi_ma,
    },
    {
        "name": "劫煞",
        "desc": "主劫难、变故、突发事件，为凶煞，遇之多有突发变动、灾祸。",
        "checker": _is_jie_sha,
    },
    {
        "name": "亡神",
        "desc": "主损失、破财、不详，为凶煞，遇之多有损失、不祥之事。",
        "checker": _is_wang_shen,
    },
    {
        "name": "桃花",
        "desc": "主感情、姻缘、异性缘，为双面神，既主良缘美姻，亦主情感纠纷。",
        "checker": _is_tao_hua,
    },
    {
        "name": "孤辰",
        "desc": "主孤独、独立，感情路较坎坷，适合晚婚，男忌孤辰。",
        "checker": _is_gu_chen,
    },
    {
        "name": "寡宿",
        "desc": "主清冷、孤寡，女性遇之婚姻不顺，男性则性格孤僻，女忌寡宿。",
        "checker": _is_gua_su,
    },
    {
        "name": "空亡",
        "desc": "如吉神落空亡，则吉力减半，如凶神落空亡，则凶力大减。",
        "checker": _is_kong_wang,
    },
]


def get_shensha(bazi: EightChar) -> List[Tuple[str, str]]:
    """
    Calculate ShenSha for a BaZi chart.

    Args:
        bazi: lunar_python EightChar object

    Returns:
        List of tuples: [(name, description), ...]
    """
    shensha_list = []
    for rule in SHENSHA_RULES:
        if rule["checker"](bazi):
            shensha_list.append((rule["name"], rule["desc"]))
    return shensha_list
