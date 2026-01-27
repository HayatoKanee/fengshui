"""
调候用神 (Climate Adjustment) analyzer service.

Based on《穷通宝鉴》- determines favorable elements based on
the relationship between day stem and month branch (season).

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..models import BaZi, WuXing
from ..models.stems_branches import HeavenlyStem, EarthlyBranch


class SeasonType(Enum):
    """Season intensity classification."""
    EXTREME_COLD = "极寒"  # 子、丑月
    COLD = "寒"           # 亥月
    EXTREME_HOT = "极热"   # 午、未月
    HOT = "热"            # 巳月
    MODERATE = "温和"      # 寅卯辰、申酉戌


@dataclass(frozen=True)
class TiaoHouResult:
    """Result of 调候 analysis."""
    day_stem: HeavenlyStem
    month_branch: EarthlyBranch
    season_type: SeasonType
    primary_yongshen: List[HeavenlyStem]  # 主要调候用神（按优先级排序）
    secondary_yongshen: List[HeavenlyStem]  # 次要调候用神
    description: str = ""
    urgency: float = 0.0  # 调候急迫程度 0.0-1.0


# 《穷通宝鉴》调候用神表
# 格式：{日干: {月支: (主要用神列表, 次要用神列表, 说明)}}
TIAOHAO_TABLE: Dict[HeavenlyStem, Dict[EarthlyBranch, Tuple[List[str], List[str], str]]] = {
    HeavenlyStem.JIA: {
        EarthlyBranch.YIN: (["丙"], ["癸"], "春木向阳，丙火为主，癸水为佐"),
        EarthlyBranch.MAO: (["庚"], ["丙", "丁", "戊", "己"], "羊刃驾杀，专用庚金"),
        EarthlyBranch.CHEN: (["庚", "丁"], ["壬"], "用庚必须有丁，无庚用壬"),
        EarthlyBranch.SI: (["癸"], ["庚", "丁"], "调和气候，癸水为主"),
        EarthlyBranch.WU: (["癸"], ["庚", "丁"], "木性虚焦，癸为主要"),
        EarthlyBranch.WEI: (["癸"], ["庚", "丁"], "上半月用癸，下半月取庚丁"),
        EarthlyBranch.SHEN: (["庚", "丁"], ["壬"], "伤官格者可专用壬"),
        EarthlyBranch.YOU: (["庚", "丁"], ["丙"], "丙为调候，庚为主"),
        EarthlyBranch.XU: (["庚", "甲"], ["丁", "壬", "癸"], "土多用甲，木多用庚"),
        EarthlyBranch.HAI: (["庚", "丁"], ["丙", "戊"], "用庚丁，丙为调候，水众用戊"),
        EarthlyBranch.ZI: (["丁"], ["庚", "丙"], "丁先庚后，丙火佐之，支见巳寅为贵格"),
        EarthlyBranch.CHOU: (["丁"], ["庚", "丙"], "丁为必须，通根巳寅者佳"),
    },
    HeavenlyStem.YI: {
        EarthlyBranch.YIN: (["丙"], ["癸"], "取丙调候，癸水略取则足"),
        EarthlyBranch.MAO: (["丙"], ["癸"], "与正月同，忌强金"),
        EarthlyBranch.CHEN: (["癸"], ["丙", "戊"], "支成水局，专取戊土制水"),
        EarthlyBranch.SI: (["癸"], [], "专用癸水调候为急"),
        EarthlyBranch.WU: (["癸"], ["丙"], "上旬用癸，下旬丙癸兼用"),
        EarthlyBranch.WEI: (["癸"], ["丙"], "柱多金水先取丙火，忌戊己混杂"),
        EarthlyBranch.SHEN: (["丙", "癸"], ["己"], "有庚取丙癸克泄，取己土为佐"),
        EarthlyBranch.YOU: (["癸"], ["丙", "丁"], "上旬癸先丙后，下旬丙先癸后"),
        EarthlyBranch.XU: (["癸"], ["辛"], "见甲谓藤萝系松柏"),
        EarthlyBranch.HAI: (["丙"], ["戊"], "专取丙用，水多兼用戊"),
        EarthlyBranch.ZI: (["丙"], [], "专用丙火，忌癸水"),
        EarthlyBranch.CHOU: (["丙"], [], "寒谷之木，专用丙火"),
    },
    HeavenlyStem.BING: {
        EarthlyBranch.YIN: (["壬"], ["庚"], "壬水为主，庚金为佐"),
        EarthlyBranch.MAO: (["壬"], ["己"], "壬水辅映"),
        EarthlyBranch.CHEN: (["壬"], ["甲"], "壬水为用"),
        EarthlyBranch.SI: (["壬", "癸"], ["庚"], "丙不熔金，惟喜壬制"),
        EarthlyBranch.WU: (["壬"], ["庚"], "专用壬水"),
        EarthlyBranch.WEI: (["壬"], ["庚"], "壬庚并用"),
        EarthlyBranch.SHEN: (["壬"], ["戊"], "壬水为主"),
        EarthlyBranch.YOU: (["壬"], ["癸"], "壬癸皆用"),
        EarthlyBranch.XU: (["甲"], ["壬"], "甲壬并用"),
        EarthlyBranch.HAI: (["甲"], ["戊", "庚", "壬"], "甲木引丁，寒气渐增"),
        EarthlyBranch.ZI: (["壬"], ["戊", "己"], "壬戊并用"),
        EarthlyBranch.CHOU: (["壬"], ["甲"], "壬甲并用"),
    },
    HeavenlyStem.DING: {
        EarthlyBranch.YIN: (["甲"], ["庚"], "庚劈甲引丁"),
        EarthlyBranch.MAO: (["庚"], ["甲"], "庚劈甲引丁"),
        EarthlyBranch.CHEN: (["甲"], ["庚"], "一派戊土无甲，为伤官伤尽"),
        EarthlyBranch.SI: (["甲"], ["庚"], "庚劈甲引丁"),
        EarthlyBranch.WU: (["壬"], ["庚", "癸"], "壬为主，庚癸为佐"),
        EarthlyBranch.WEI: (["甲"], ["壬", "庚"], "甲壬并用"),
        EarthlyBranch.SHEN: (["甲", "庚"], ["丙", "戊"], "取庚劈甲，用丙暖金晒甲"),
        EarthlyBranch.YOU: (["甲", "庚"], ["丙", "戊"], "取庚劈甲，用丙暖金晒甲"),
        EarthlyBranch.XU: (["甲", "庚"], ["戊"], "一派戊土无甲，为伤官伤尽"),
        EarthlyBranch.HAI: (["甲"], ["庚"], "庚金劈甲引丁，甲木为尊"),
        EarthlyBranch.ZI: (["甲"], ["庚"], "庚金劈甲引丁，甲木为尊"),
        EarthlyBranch.CHOU: (["甲"], ["庚"], "庚金劈甲引丁，甲木为尊"),
    },
    HeavenlyStem.WU: {
        EarthlyBranch.YIN: (["丙"], ["甲", "癸"], "无丙照暖戊土不生"),
        EarthlyBranch.MAO: (["丙"], ["甲", "癸"], "先丙、次甲、次癸"),
        EarthlyBranch.CHEN: (["甲"], ["丙", "癸"], "戊土司令，先用甲疏"),
        EarthlyBranch.SI: (["甲"], ["丙", "癸"], "戊土建禄，先用甲疏劈"),
        EarthlyBranch.WU: (["壬"], ["甲", "丙"], "调候为急，先用壬水"),
        EarthlyBranch.WEI: (["癸"], ["丙", "甲"], "调候为急，癸不可缺"),
        EarthlyBranch.SHEN: (["丙"], ["癸", "甲"], "寒气渐增，先用丙火"),
        EarthlyBranch.YOU: (["丙"], ["癸"], "丙为主，癸为佐"),
        EarthlyBranch.XU: (["甲"], ["丙", "癸"], "土多甲优先"),
        EarthlyBranch.HAI: (["甲", "丙"], [], "二者不可缺一"),
        EarthlyBranch.ZI: (["丙"], ["甲"], "丙为主，甲佐之"),
        EarthlyBranch.CHOU: (["丙"], ["甲"], "丙为主，甲佐之"),
    },
    HeavenlyStem.JI: {
        EarthlyBranch.YIN: (["丙"], ["庚", "甲"], "忌壬水有根"),
        EarthlyBranch.MAO: (["甲"], ["癸", "丙"], "忌甲己合土方佳"),
        EarthlyBranch.CHEN: (["丙"], ["癸", "甲"], "土众者甲为优先"),
        EarthlyBranch.SI: (["癸"], ["丙"], "调候为上，癸为尊"),
        EarthlyBranch.WU: (["癸"], ["丙"], "同四月取用论"),
        EarthlyBranch.WEI: (["癸"], ["丙"], "调候不能无癸"),
        EarthlyBranch.SHEN: (["丙"], ["癸"], "丙火温土，癸水润土"),
        EarthlyBranch.YOU: (["丙"], ["癸"], "取辛辅癸"),
        EarthlyBranch.XU: (["甲"], ["丙", "癸"], "九月土盛，宜甲木疏之"),
        EarthlyBranch.HAI: (["丙"], ["甲", "戊"], "三冬己土，非丙暖不生"),
        EarthlyBranch.ZI: (["丙"], ["甲", "戊"], "三冬己土非丙暖不生"),
        EarthlyBranch.CHOU: (["丙"], ["甲", "戊"], "三冬己土非丙暖不生"),
    },
    HeavenlyStem.GENG: {
        EarthlyBranch.YIN: (["戊"], ["甲", "壬", "丙", "丁"], "用丙暖庚性"),
        EarthlyBranch.MAO: (["丁"], ["甲", "庚", "丙"], "庚金暗强，专用丁火"),
        EarthlyBranch.CHEN: (["甲", "丁"], ["壬", "癸"], "顽金宜丁，旺土用甲"),
        EarthlyBranch.SI: (["壬"], ["戊", "丙", "丁"], "丙不熔金，惟喜壬制"),
        EarthlyBranch.WU: (["壬"], ["癸"], "专用壬水，癸次之"),
        EarthlyBranch.WEI: (["丁"], ["甲"], "若支会土局，甲先丁后"),
        EarthlyBranch.SHEN: (["丁"], ["甲"], "专用丁火，甲木引丁"),
        EarthlyBranch.YOU: (["丁"], ["甲", "丙"], "用丁甲，兼用丙火调候"),
        EarthlyBranch.XU: (["甲"], ["壬"], "土厚先用甲疏，次用壬洗"),
        EarthlyBranch.HAI: (["丁", "丙"], [], "水冷金寒爱丙丁"),
        EarthlyBranch.ZI: (["丁"], ["甲", "丙"], "仍取丁甲，次取丙火照暖"),
        EarthlyBranch.CHOU: (["丙", "丁"], ["甲"], "仍取丁甲，次取丙火照暖"),
    },
    HeavenlyStem.XIN: {
        EarthlyBranch.YIN: (["己"], ["壬", "庚"], "辛金失令，取己土为生身之本"),
        EarthlyBranch.MAO: (["壬"], ["甲"], "壬水为尊"),
        EarthlyBranch.CHEN: (["壬"], ["甲"], "壬水洗淘"),
        EarthlyBranch.SI: (["壬"], ["甲", "癸"], "壬水洗淘，兼有调候之用"),
        EarthlyBranch.WU: (["壬", "己"], ["癸"], "己无壬不湿，辛无己不生"),
        EarthlyBranch.WEI: (["壬"], ["庚", "甲"], "先用壬水，取庚为佐"),
        EarthlyBranch.SHEN: (["壬"], ["甲", "戊"], "壬水为尊"),
        EarthlyBranch.YOU: (["壬"], ["甲"], "壬水淘洗"),
        EarthlyBranch.XU: (["壬"], ["甲"], "九月辛金，火土为病，水木为药"),
        EarthlyBranch.HAI: (["壬"], ["丙"], "先壬后丙，名金白水清"),
        EarthlyBranch.ZI: (["丙"], ["戊", "壬"], "冬月辛金，不能缺丙火温暖"),
        EarthlyBranch.CHOU: (["丙"], ["壬", "戊", "己"], "丙先壬后，戊己次之"),
    },
    HeavenlyStem.REN: {
        EarthlyBranch.YIN: (["戊"], ["甲", "丙"], "火多用壬"),
        EarthlyBranch.MAO: (["戊"], ["辛", "庚"], "戊辛为用"),
        EarthlyBranch.CHEN: (["甲"], ["庚"], "金多兼用丙"),
        EarthlyBranch.SI: (["壬"], ["辛", "庚", "癸"], "壬水为源"),
        EarthlyBranch.WU: (["癸"], ["庚", "辛"], "忌丁透干"),
        EarthlyBranch.WEI: (["辛"], ["甲"], "土多甲先辛后"),
        EarthlyBranch.SHEN: (["戊"], ["丁"], "二者必须有根"),
        EarthlyBranch.YOU: (["甲"], ["庚"], "水只需一位"),
        EarthlyBranch.XU: (["甲"], ["丙", "戊"], "有合者，丙先甲后"),
        EarthlyBranch.HAI: (["戊"], ["丙", "庚"], "戊丙为用"),
        EarthlyBranch.ZI: (["戊"], ["丙"], "二者不可缺一"),
        EarthlyBranch.CHOU: (["丙", "丁"], ["甲"], "上半月丙先，下半月丁甲并用"),
    },
    HeavenlyStem.GUI: {
        EarthlyBranch.YIN: (["辛"], ["丙"], "比劫重戊为先"),
        EarthlyBranch.MAO: (["庚", "辛"], [], "庚辛为用"),
        EarthlyBranch.CHEN: (["甲"], ["庚"], "金多兼用丙"),
        EarthlyBranch.SI: (["辛"], [], "辛为主"),
        EarthlyBranch.WU: (["庚", "辛"], ["壬", "癸"], "忌丁透干"),
        EarthlyBranch.WEI: (["庚", "辛"], ["壬", "癸"], "金为源"),
        EarthlyBranch.SHEN: (["丁"], [], "丁为主"),
        EarthlyBranch.YOU: (["辛"], ["丙"], "辛丙为用"),
        EarthlyBranch.XU: (["辛"], ["甲", "壬", "癸"], "辛甲为用"),
        EarthlyBranch.HAI: (["庚", "辛"], ["戊", "丁"], "木成局者，庚优先"),
        EarthlyBranch.ZI: (["丙"], ["辛"], "丙辛为用"),
        EarthlyBranch.CHOU: (["丙", "丁"], [], "上半月丙先，下半月丁甲并用"),
    },
}


def _get_season_type(month_branch: EarthlyBranch) -> SeasonType:
    """Determine season intensity from month branch."""
    if month_branch in (EarthlyBranch.ZI, EarthlyBranch.CHOU):
        return SeasonType.EXTREME_COLD
    elif month_branch == EarthlyBranch.HAI:
        return SeasonType.COLD
    elif month_branch in (EarthlyBranch.WU, EarthlyBranch.WEI):
        return SeasonType.EXTREME_HOT
    elif month_branch == EarthlyBranch.SI:
        return SeasonType.HOT
    else:
        return SeasonType.MODERATE


def _get_urgency(season_type: SeasonType) -> float:
    """Get climate adjustment urgency based on season type."""
    urgency_map = {
        SeasonType.EXTREME_COLD: 0.9,
        SeasonType.EXTREME_HOT: 0.9,
        SeasonType.COLD: 0.6,
        SeasonType.HOT: 0.6,
        SeasonType.MODERATE: 0.3,
    }
    return urgency_map[season_type]


def _stems_to_enum(stem_chars: List[str]) -> List[HeavenlyStem]:
    """Convert list of stem characters to HeavenlyStem enums."""
    return [HeavenlyStem.from_chinese(char) for char in stem_chars]


class TiaoHouAnalyzer:
    """
    调候用神分析器 - Climate adjustment favorable elements analyzer.

    Based on《穷通宝鉴》, determines favorable elements based on
    the relationship between day stem and birth season.
    """

    def analyze(self, bazi: BaZi) -> TiaoHouResult:
        """
        Analyze the 调候用神 for a given BaZi chart.

        Args:
            bazi: The BaZi chart to analyze

        Returns:
            TiaoHouResult with climate adjustment recommendations
        """
        day_stem = bazi.day_pillar.stem
        month_branch = bazi.month_pillar.branch

        # Get season type
        season_type = _get_season_type(month_branch)
        urgency = _get_urgency(season_type)

        # Look up from table
        if day_stem in TIAOHAO_TABLE and month_branch in TIAOHAO_TABLE[day_stem]:
            primary_chars, secondary_chars, description = TIAOHAO_TABLE[day_stem][month_branch]
            primary = _stems_to_enum(primary_chars)
            secondary = _stems_to_enum(secondary_chars)
        else:
            # Fallback: basic climate adjustment
            primary = []
            secondary = []
            description = "无特定调候需求"

        return TiaoHouResult(
            day_stem=day_stem,
            month_branch=month_branch,
            season_type=season_type,
            primary_yongshen=primary,
            secondary_yongshen=secondary,
            description=description,
            urgency=urgency,
        )

    def get_tiaohao_wuxing(self, bazi: BaZi) -> Optional[WuXing]:
        """
        Get the primary 调候用神 as WuXing element.

        Returns the WuXing of the most important climate adjustment element.
        """
        result = self.analyze(bazi)
        if result.primary_yongshen:
            return result.primary_yongshen[0].wuxing
        return None

    def needs_climate_adjustment(self, bazi: BaZi) -> bool:
        """
        Check if this BaZi chart urgently needs climate adjustment.

        Returns True for extreme cold (子丑) or extreme hot (午未) months.
        """
        result = self.analyze(bazi)
        return result.season_type in (SeasonType.EXTREME_COLD, SeasonType.EXTREME_HOT)
