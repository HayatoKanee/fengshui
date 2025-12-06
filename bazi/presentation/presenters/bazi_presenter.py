"""
BaZi Presenter (Clean Architecture).

Transforms domain models to view-ready data structures for templates.

In Clean Architecture terminology:
- Presenter: Prepares output data for the View layer
- View Model: The data structure returned (BaziViewData)

This is NOT a Hexagonal "Adapter" (which requires a Port interface).
This is a Clean Architecture Presenter for output transformation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

# Domain layer imports (DIP-compliant)
from bazi.domain.constants import (
    GAN_WUXING,
    GAN_YINYANG,
    HIDDEN_GAN_RATIOS,
    RELATIONSHIPS,
    SEASON_PHASES,
    WANG_XIANG_VALUE,
    WUXING_RELATIONS,
    ZHI_SEASONS,
    ZHI_WUXING,
)
from bazi.domain.models import (
    BaZi,
    HeavenlyStem,
    EarthlyBranch,
    Pillar,
    WuXing,
    ShiShen,
    ShiShenChart,
    WuXingStrength,
    DayMasterStrength,
    FavorableElements,
    ShenShaAnalysis,
)

if TYPE_CHECKING:
    from lunar_python import EightChar, Lunar


@dataclass
class BaziViewData:
    """
    Complete view data for BaZi templates.

    This DTO contains all data needed to render BaZi templates
    in the legacy format they expect.
    """

    # Core BaZi
    bazi: EightChar
    bazi_string: str

    # Relationship values per pillar
    values: List[Tuple[int, int]]

    # Hidden stems per pillar (dict of stem -> ratio)
    hidden_gans: List[Dict[str, float]]

    # WuXing element per position (stem, [hidden stems])
    wuxing: List[Tuple[str, List[str]]]

    # YinYang per position (stem, [hidden stems])
    yinyang: List[Tuple[str, List[str]]]

    # ShiShen per position (stem, [hidden stems])
    shishen: List[Tuple[str, List[str]]]

    # Seasonal phase mapping
    wang_xiang: Dict[str, str]

    # Seasonal phase values per position
    WANG_XIANG_VALUEs: List[Tuple[float, List[float]]]

    # Stem strength values per position
    gan_liang_values: List[Tuple[float, List[float]]]

    # Accumulated element values
    wuxing_value: Dict[str, float]

    # Beneficial/harmful totals
    sheng_hao: Tuple[float, float]

    # Beneficial/harmful percentages
    sheng_hao_percentage: Tuple[float, float]

    # Day master info
    main_wuxing: str
    is_strong: bool

    # Zodiac
    shengxiao: str

    # Sheng/Hao relations
    sheng_hao_relations: Dict[str, List[str]]


class BaziPresenter:
    """
    Clean Architecture Presenter for BaZi analysis output.

    Transforms domain objects (EightChar, Lunar) into view-ready
    data structures (BaziViewData) for Django templates.

    This follows the Presenter pattern from Clean Architecture:
    - Input: Domain objects from use case layer
    - Output: View Model (DTO) formatted for presentation

    Usage:
        presenter = BaziPresenter()
        view_data = presenter.present(bazi_eight_char, lunar)
    """

    def present(
        self,
        bazi: EightChar,
        lunar: Lunar,
    ) -> BaziViewData:
        """
        Present BaZi domain data as a view-ready structure.

        Args:
            bazi: lunar_python EightChar object
            lunar: lunar_python Lunar object

        Returns:
            BaziViewData view model with all template-ready data
        """
        bazi_string = bazi.toString()
        pillars = bazi_string.split()

        # Calculate all data
        main_wuxing = bazi.getDayWuXing()[0]
        values = self._calculate_values(pillars)
        hidden_gans = self._get_hidden_gans(pillars)
        wuxing = self._calculate_wuxing_values(pillars)
        yinyang = self._calculate_yinyang_values(pillars)
        wang_xiang = self._get_wang_xiang(bazi.getMonthZhi(), lunar)
        WANG_XIANG_VALUEs = self._calculate_WANG_XIANG_VALUEs(pillars, wang_xiang)
        gan_liang_values = self._calculate_gan_liang_values(
            values, hidden_gans, WANG_XIANG_VALUEs
        )
        wuxing_value = self._accumulate_wuxing_values(wuxing, gan_liang_values)
        sheng_hao = self._calculate_shenghao(wuxing_value, main_wuxing)
        sheng_hao_percentage = self._calculate_shenghao_percentage(
            sheng_hao[0], sheng_hao[1]
        )
        shishen = self._calculate_shishen_for_bazi(wuxing, yinyang)
        sheng_hao_relations = WUXING_RELATIONS.get(main_wuxing, {})
        shengxiao = lunar.getYearShengXiaoExact()
        is_strong = sheng_hao[0] > sheng_hao[1]

        return BaziViewData(
            bazi=bazi,
            bazi_string=bazi_string,
            values=values,
            hidden_gans=hidden_gans,
            wuxing=wuxing,
            yinyang=yinyang,
            shishen=shishen,
            wang_xiang=wang_xiang,
            WANG_XIANG_VALUEs=WANG_XIANG_VALUEs,
            gan_liang_values=gan_liang_values,
            wuxing_value=wuxing_value,
            sheng_hao=sheng_hao,
            sheng_hao_percentage=sheng_hao_percentage,
            main_wuxing=main_wuxing,
            is_strong=is_strong,
            shengxiao=shengxiao,
            sheng_hao_relations=sheng_hao_relations,
        )

    def _WUXING_RELATIONShip(self, gan: str, zhi: str) -> Tuple[int, int]:
        """Calculate relationship values between stem and branch elements."""
        element1 = GAN_WUXING.get(gan)
        element2 = ZHI_WUXING.get(zhi)

        if element1 == element2:
            return 10, 10
        elif RELATIONSHIPS['生'].get(element1) == element2:
            return 6, 8
        elif RELATIONSHIPS['克'].get(element1) == element2:
            return 4, 2
        elif RELATIONSHIPS['克'].get(element2) == element1:
            return 2, 4
        elif RELATIONSHIPS['生'].get(element2) == element1:
            return 8, 6
        return 0, 0

    def _calculate_values(
        self,
        pillars: List[str],
    ) -> List[Tuple[int, int]]:
        """Calculate relationship values for each pillar."""
        values = []
        for pillar in pillars:
            gan, zhi = pillar[0], pillar[1]
            gan_value, zhi_value = self._WUXING_RELATIONShip(gan, zhi)
            values.append((gan_value, zhi_value))
        return values

    def _get_hidden_gans(
        self,
        pillars: List[str],
    ) -> List[Dict[str, float]]:
        """Get hidden stems for each pillar's branch."""
        hidden_gans_list = []
        for pillar in pillars:
            zhi = pillar[1]
            hidden_gans = HIDDEN_GAN_RATIOS.get(zhi, {})
            hidden_gans_list.append(hidden_gans)
        return hidden_gans_list

    def _calculate_wuxing_values(
        self,
        pillars: List[str],
    ) -> List[Tuple[str, List[str]]]:
        """Get WuXing element for each position."""
        values = []
        for pillar in pillars:
            gan, zhi = pillar[0], pillar[1]
            value_for_gan = GAN_WUXING.get(gan)
            hidden_gans_for_zhi = HIDDEN_GAN_RATIOS.get(zhi, {})
            values_for_zhi = [
                GAN_WUXING.get(hidden_gan) for hidden_gan in hidden_gans_for_zhi.keys()
            ]
            values.append((value_for_gan, values_for_zhi))
        return values

    def _calculate_yinyang_values(
        self,
        pillars: List[str],
    ) -> List[Tuple[str, List[str]]]:
        """Get YinYang for each position."""
        values = []
        for pillar in pillars:
            gan, zhi = pillar[0], pillar[1]
            value_for_gan = GAN_YINYANG.get(gan)
            hidden_gans_for_zhi = HIDDEN_GAN_RATIOS.get(zhi, {})
            values_for_zhi = [
                GAN_YINYANG.get(hidden_gan)
                for hidden_gan in hidden_gans_for_zhi.keys()
            ]
            values.append((value_for_gan, values_for_zhi))
        return values

    def _get_wang_xiang(
        self,
        month_zhi: str,
        lunar: Lunar,
    ) -> Dict[str, str]:
        """Get seasonal phase mapping."""
        season = ZHI_SEASONS.get(month_zhi)
        if month_zhi in ['辰', '未', '戌', '丑']:
            next_jieqi = lunar.getNextJieQi(True)
            if next_jieqi.getSolar().subtract(lunar.getSolar()) <= 18:
                return {'土': '旺', '金': '相', '火': '休', '木': '囚', '水': '死'}
        return SEASON_PHASES.get(season, {})

    def _calculate_WANG_XIANG_VALUEs(
        self,
        pillars: List[str],
        wang_xiang: Dict[str, str],
    ) -> List[Tuple[float, List[float]]]:
        """Calculate seasonal phase values for each position."""
        WANG_XIANG_VALUEs_list = []

        for pillar in pillars:
            gan, zhi = pillar[0], pillar[1]

            # Calculate WANG_XIANG_VALUE for gan
            gan_element = GAN_WUXING.get(gan)
            wang_xiang_for_gan = wang_xiang.get(gan_element)
            WANG_XIANG_VALUE_for_gan = WANG_XIANG_VALUE.get(wang_xiang_for_gan, 1.0)

            # Calculate WANG_XIANG_VALUE for each hidden gan in zhi
            hidden_gans_for_zhi = HIDDEN_GAN_RATIOS.get(zhi, {})
            WANG_XIANG_VALUEs_for_zhi = []
            for hidden_gan in hidden_gans_for_zhi.keys():
                hidden_element = GAN_WUXING.get(hidden_gan)
                wang_xiang_for_hidden = wang_xiang.get(hidden_element)
                WANG_XIANG_VALUE_for_hidden = WANG_XIANG_VALUE.get(
                    wang_xiang_for_hidden, 1.0
                )
                WANG_XIANG_VALUEs_for_zhi.append(WANG_XIANG_VALUE_for_hidden)

            WANG_XIANG_VALUEs_list.append(
                (WANG_XIANG_VALUE_for_gan, WANG_XIANG_VALUEs_for_zhi)
            )

        return WANG_XIANG_VALUEs_list

    def _calculate_gan_liang_values(
        self,
        values: List[Tuple[int, int]],
        hidden_gans: List[Dict[str, float]],
        WANG_XIANG_VALUEs: List[Tuple[float, List[float]]],
    ) -> List[Tuple[float, List[float]]]:
        """Calculate stem strength values."""
        result = []

        for (v_gan, v_zhi), gans, (wx_gan, wx_zhis) in zip(
            values, hidden_gans, WANG_XIANG_VALUEs
        ):
            zhi_values = [
                v_zhi * g * wx for g, wx in zip(gans.values(), wx_zhis)
            ]
            result.append((v_gan * 1 * wx_gan, zhi_values))

        return result

    def _accumulate_wuxing_values(
        self,
        wuxing: List[Tuple[str, List[str]]],
        gan_liang_value: List[Tuple[float, List[float]]],
    ) -> Dict[str, float]:
        """Accumulate element values."""
        all_wuxing = ['木', '火', '土', '金', '水']
        result = {wx: 0.0 for wx in all_wuxing}

        for (wx_gan, wx_zhis), (gl_gan, gl_zhis) in zip(wuxing, gan_liang_value):
            # Add the gan value
            result[wx_gan] = result.get(wx_gan, 0) + gl_gan

            # Add the zhi values
            for wx, gl in zip(wx_zhis, gl_zhis):
                result[wx] = result.get(wx, 0) + gl

        return result

    def _calculate_shenghao(
        self,
        wuxing_value: Dict[str, float],
        main_wuxing: str,
    ) -> Tuple[float, float]:
        """Calculate beneficial and harmful totals."""
        total_beneficial = 0.0
        total_non_beneficial = 0.0
        relationship = WUXING_RELATIONS.get(main_wuxing, {})

        for beneficial in relationship.get('有利', []):
            total_beneficial += wuxing_value.get(beneficial, 0)

        for non_beneficial in relationship.get('不利', []):
            total_non_beneficial += wuxing_value.get(non_beneficial, 0)

        return total_beneficial, total_non_beneficial

    def _calculate_shenghao_percentage(
        self,
        sheng_value: float,
        hao_value: float,
    ) -> Tuple[float, float]:
        """Calculate beneficial and harmful percentages."""
        total_value = sheng_value + hao_value
        if total_value == 0:
            return 50.0, 50.0
        sheng_percentage = (sheng_value / total_value) * 100
        hao_percentage = (hao_value / total_value) * 100
        return sheng_percentage, hao_percentage

    def _calculate_shishen(
        self,
        day_master_yinyang: str,
        day_master_wuxing: str,
        stem_yinyang: str,
        stem_wuxing: str,
    ) -> str:
        """Calculate ShiShen relationship."""
        if day_master_wuxing == stem_wuxing:
            if day_master_yinyang == stem_yinyang:
                return '比肩'
            return '比劫'
        elif relationships['生'].get(day_master_wuxing) == stem_wuxing:
            if day_master_yinyang == stem_yinyang:
                return '食神'
            return '伤官'
        elif relationships['生'].get(stem_wuxing) == day_master_wuxing:
            if day_master_yinyang == stem_yinyang:
                return '偏印'
            return '正印'
        elif relationships['克'].get(day_master_wuxing) == stem_wuxing:
            if day_master_yinyang == stem_yinyang:
                return '偏财'
            return '正财'
        elif relationships['克'].get(stem_wuxing) == day_master_wuxing:
            if day_master_yinyang == stem_yinyang:
                return '七杀'
            return '正官'
        return ''

    def _calculate_shishen_for_bazi(
        self,
        wuxing: List[Tuple[str, List[str]]],
        yinyang: List[Tuple[str, List[str]]],
    ) -> List[Tuple[str, List[str]]]:
        """Calculate ShiShen for all positions."""
        day_master_wuxing = wuxing[2][0]
        day_master_yinyang = yinyang[2][0]

        shishen_list = []

        for i in range(len(wuxing)):
            stem_wuxing = wuxing[i][0]
            stem_yinyang = yinyang[i][0]
            shishen_for_gan = self._calculate_shishen(
                day_master_yinyang, day_master_wuxing, stem_yinyang, stem_wuxing
            )

            shishen_for_zhi = []
            for j, hidden_stem in enumerate(wuxing[i][1]):
                hidden_stem_yinyang = yinyang[i][1][j]
                shishen_hidden = self._calculate_shishen(
                    day_master_yinyang, day_master_wuxing, hidden_stem_yinyang, hidden_stem
                )
                shishen_for_zhi.append(shishen_hidden)

            shishen_list.append((shishen_for_gan, shishen_for_zhi))

        # Day pillar stem is "日主" (Day Master)
        shishen_list[2] = ('日主', shishen_list[2][1])

        return shishen_list
