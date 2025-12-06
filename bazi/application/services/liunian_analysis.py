"""
LiuNian (Yearly Fortune) Analysis Service.

Generates Chinese text-based analysis for:
- Yearly fortune predictions (流年分析)
- Partner personality analysis (配偶性格)
- Personality analysis based on birth month (提纲)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from lunar_python import Solar

# Domain layer imports (DIP-compliant)
from bazi.domain.constants import HIDDEN_GAN_RATIOS, is_harmony
from bazi.domain.models import HeavenlyStem, ShiShen, calculate_shishen

# Application layer imports
from bazi.application.content import TIGANG_TEXT, PARTNER_TEXT
from bazi.application.services.shishen_handlers import shishen_handler

if TYPE_CHECKING:
    from lunar_python import EightChar


class LiunianAnalysisService:
    """
    Application service for complex BaZi text analysis.

    These analyses generate Chinese text for display to users.
    They are kept separate from domain services because they
    contain presentation logic (user-facing text generation).
    """

    def analyse_personality(self, month_zhi: str) -> Optional[str]:
        """
        Get personality description based on birth month branch.

        Args:
            month_zhi: The month branch (地支) in Chinese

        Returns:
            Personality description text or None
        """
        return TIGANG_TEXT.get(month_zhi)

    def analyse_partner(
        self,
        hidden_gan: List,
        shishen_list: List[Tuple[str, Dict[str, float]]],
    ) -> Optional[str]:
        """
        Analyze partner personality based on day pillar.

        Args:
            hidden_gan: List of hidden stems per pillar
            shishen_list: ShiShen list for all pillars

        Returns:
            Partner personality description
        """
        ratios = self._get_day_gan_ratio(hidden_gan, shishen_list)
        if ratios:
            first_key = list(ratios.items())[0][0]
            return PARTNER_TEXT.get(first_key)
        return None

    def analyse_liunian(
        self,
        bazi: EightChar,
        shishen: List,
        selected_year: str,
        is_strong: bool,
        is_male: bool,
    ) -> str:
        """
        Generate yearly fortune (流年) analysis.

        Args:
            bazi: The EightChar object
            shishen: ShiShen list for all pillars
            selected_year: Year to analyze
            is_strong: Whether day master is strong
            is_male: Whether the person is male

        Returns:
            HTML-formatted analysis text
        """
        daymaster_gan = bazi.getDayGan()

        solar = Solar.fromYmd(int(selected_year), 5, 5)
        lunar = solar.getLunar()
        year_bazi = lunar.getEightChar()

        year_shishen = self._get_shishen_for_year(year_bazi, daymaster_gan)

        analysis = (
            f"{year_bazi.getYearGan()}{year_bazi.getYearZhi()}年，"
            f"对应流年运：{year_shishen}（数字为地支藏干之比例）<br>"
        )
        analysis += "流年天干分析，主要对应上半年：<br>"
        analysis += self._analyse_liunian_shishen(
            year_shishen[0], bazi, shishen, year_bazi, is_strong, is_male
        )
        analysis += "流年地支分析，主要对应下半年：<br>"

        for k, v in year_shishen[1].items():
            analysis += f"{k}运(大约占{v * 100}%):<br>"
            analysis += self._analyse_liunian_shishen(
                k, bazi, shishen, year_bazi, is_strong, is_male
            )

        analysis += "流年及本命分析：<br>"
        analysis += self._analyse_yearly_combinations(
            bazi, shishen, year_bazi, is_strong, is_male
        )

        return analysis

    def _get_day_gan_ratio(
        self,
        hidden_gan: List,
        shishen_list: List,
    ) -> Dict[str, float]:
        """
        Calculate ShiShen ratio for day branch's hidden stems.

        The spouse personality is determined by the ShiShen relationship
        between the day master and the day branch's main hidden stem.

        Args:
            hidden_gan: List of hidden stem dicts per pillar
            shishen_list: List of (stem_shishen, [hidden_shishens]) per pillar

        Returns:
            Dict mapping ShiShen name to ratio (currently main stem = 1.0)
        """
        if len(hidden_gan) < 3 or len(shishen_list) < 3:
            return {}

        result = {}

        # shishen_list[2] = ('日主', [hidden_stem_shishens for day branch])
        # We need the ShiShen for the day branch's main hidden stem
        day_branch_shishens = shishen_list[2][1]  # List of hidden stem ShiShens
        if day_branch_shishens:
            # Get the first (main) hidden stem's ShiShen
            main_hidden_shishen = day_branch_shishens[0]
            if main_hidden_shishen:
                result[main_hidden_shishen] = 1.0

        return result

    def _get_shishen_for_year(
        self,
        year_bazi: EightChar,
        daymaster_gan: str,
    ) -> List:
        """Calculate ShiShen for a given year's pillars."""
        year_gan = year_bazi.getYearGan()
        year_hidden_gans = HIDDEN_GAN_RATIOS.get(year_bazi.getYearZhi(), {})

        # Convert Chinese characters to HeavenlyStem objects
        daymaster_stem = HeavenlyStem.from_chinese(daymaster_gan)
        year_stem = HeavenlyStem.from_chinese(year_gan)

        gan_shishen = calculate_shishen(daymaster_stem, year_stem)

        zhi_shishen = {}
        for gan, ratio in year_hidden_gans.items():
            hidden_stem = HeavenlyStem.from_chinese(gan)
            shishen_for_gan = calculate_shishen(daymaster_stem, hidden_stem)
            zhi_shishen[shishen_for_gan.chinese] = ratio

        return [gan_shishen.chinese, zhi_shishen]

    def _analyse_liunian_shishen(
        self,
        year_shishen: str,
        bazi: EightChar,
        shishen: List,
        year_bazi: EightChar,
        is_strong: bool,
        is_male: bool,
    ) -> str:
        """Analyze a specific ShiShen for the year."""
        handler = shishen_handler.get(year_shishen)
        if handler:
            return handler(bazi, shishen, year_bazi, is_strong, is_male)
        return ""

    def _analyse_yearly_combinations(
        self,
        bazi: EightChar,
        shishen: List,
        year_bazi: EightChar,
        is_strong: bool,
        is_male: bool,
    ) -> str:
        """Analyze combinations between yearly and natal chart."""
        analysis = ""

        if self._check_if_he_target(shishen, bazi, year_bazi, '正财'):
            analysis += "•本命正财， 被流年合， 主钱财流失大"
            if is_male:
                analysis += ", 严防婚变"
            analysis += "。<br>"

        if self._check_if_he_target(shishen, bazi, year_bazi, '偏财'):
            analysis += (
                "•本命偏财， 被流年合， 开支特别大，生意会赔钱，钱财流失大，"
                "或生意一败涂地。父亲身体欠安，情人失恋，若为野桃花，易被揭发。<br>"
            )

        if self._check_if_he_target(shishen, bazi, year_bazi, '正官'):
            analysis += (
                "•本命正官， 被流年合， 职业上会有变动或被夺，"
                "宜避免出分头，不要当老大，以免招来烦恼。<br>"
            )
            if is_male:
                analysis += "•男命正官被流年合，防名声、地位受损；或有官司缠身。<br>"
            else:
                analysis += "•女命正官被流年合，注意丈夫身体，也可能有外遇或走掉。<br>"

        if not is_male:
            analysis += self._analyse_female_specific(bazi, shishen)

        if is_strong and self._check_if_he_target(shishen, bazi, year_bazi, '七杀'):
            analysis += "•身强而本命有七杀，却被流年合，主事业上不容易发挥，活力易显不足。<br>"

        qisha_indices = self._find_shishen_indices('七杀', shishen)
        if len(qisha_indices) >= 2:
            analysis += "•命中七杀有两个以上者，精神显得委靡不振，容易有灾难、意外、官司、血光。<br>"

        if self._check_if_he_target(shishen, bazi, year_bazi, '偏印'):
            analysis += "•偏印被流运合住，母亲身体变差。<br>"

        if not is_strong and self._check_if_he_target(shishen, bazi, year_bazi, '正印'):
            analysis += "•命中所喜之正印被流年合住，特别倒霉，或母亲身体变不好。<br>"

        analysis += self._analyse_shangguan_positions(shishen)

        if self._check_if_he_target(shishen, bazi, year_bazi, '伤官'):
            analysis += (
                "•伤官被流年合，思绪比较杂乱，才华点子不现，处事不明，有点迷迷糊糊，"
                "所以若想做决定时，需要多问几个人征询意见。<br>"
            )

        if self._check_if_he_target(shishen, bazi, year_bazi, '食神'):
            analysis += "•食神被流年合，代表才华不能展现，决策容易失误，身体状况较差。<br>"
            if not is_male:
                analysis += "•食神被流年合, 女命甚至会危及子女。<br>"

        return analysis

    def _analyse_female_specific(self, bazi: EightChar, shishen: List) -> str:
        """Analyze female-specific chart features."""
        analysis = ""
        indices = self._find_shishen_indices('正官', shishen)
        gan_indices = [i for i in indices if i % 2 == 0]
        s = bazi.toString().replace(' ', '')

        daymaster_he = False
        for i in gan_indices:
            if i < len(s) and self._check_he(s[i], bazi.getDayGan()):
                daymaster_he = True

        if daymaster_he:
            analysis += "•女命日主合正官， 很重视老公。<br>"

        if len(indices) >= 2:
            analysis += "•女命有双正官者，易再婚。<br>"

        return analysis

    def _analyse_shangguan_positions(self, shishen: List) -> str:
        """Analyze ShangGuan (伤官) positions in the chart."""
        analysis = ""
        shang_guan_indices = self._find_shishen_indices('伤官', shishen)

        if 0 in shang_guan_indices and 1 in shang_guan_indices:
            analysis += "•伤官通根在年柱，代表幼年时期会受到重大创伤或过错。<br>"
        if 2 in shang_guan_indices and 3 in shang_guan_indices:
            analysis += "•伤官通根在月柱，代表青年时期会受到重大创伤或过错。<br>"
        if 4 in shang_guan_indices and 5 in shang_guan_indices:
            analysis += "•伤官通根在日柱，代表中年时期会受到重大创伤或过错。<br>"
        if 6 in shang_guan_indices and 7 in shang_guan_indices:
            analysis += "•伤官通根在时柱，代表老年时期会受到重大创伤或过错。<br>"

        return analysis

    def _check_he(self, ganzhi1: str, ganzhi2: str) -> bool:
        """Check if two characters form a harmony relationship."""
        return is_harmony(ganzhi1, ganzhi2)

    def _contain_shishen(
        self,
        target: str,
        shishen_list: List[Tuple[str, Dict]],
    ) -> bool:
        """Check if shishen_list contains a target ShiShen."""
        for main, sublist in shishen_list:
            if main == target or target in sublist:
                return True
        return False

    def _find_shishen_indices(
        self,
        target: str,
        shishen_list: List[Tuple[str, Dict]],
    ) -> List[int]:
        """Find indices where target ShiShen appears."""
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

    def _check_if_he_target(
        self,
        shishen: List,
        bazi: EightChar,
        year_bazi: EightChar,
        target: str,
    ) -> bool:
        """Check if a target ShiShen gets combined by yearly pillar."""
        if self._contain_shishen(target, shishen):
            indices = self._find_shishen_indices(target, shishen)
            s = bazi.toString().replace(' ', '')
            for i in indices:
                if i < len(s):
                    if (
                        self._check_he(year_bazi.getYearGan(), s[i])
                        or self._check_he(year_bazi.getYearZhi(), s[i])
                    ):
                        return True
        return False
