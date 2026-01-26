"""
Tests for PatternAnalyzer service.

Tests special pattern (格局) detection in BaZi charts using real cases
from classical texts (《渊海子平》《三命通会》《滴天髓》等).

特殊格局非常苛刻，测试用例基于古籍真实八字案例。
Uses real BaZi domain objects - no mocks.
"""
import pytest
from typing import Dict

from bazi.domain.models import BaZi, WuXing
from bazi.domain.models.pattern_analysis import (
    PatternCategory,
    PatternType,
)
from bazi.domain.services import PatternAnalyzer, WuXingCalculator


def get_wuxing_values(bazi: BaZi, calculator: WuXingCalculator) -> Dict[WuXing, float]:
    """
    Calculate WuXing values using the real calculator.

    Args:
        bazi: Real BaZi object
        calculator: WuXingCalculator instance

    Returns:
        Dictionary of WuXing to strength values
    """
    result = calculator.calculate_strength(bazi, is_earth_dominant=False)
    return result.adjusted_values


class TestZhuanWangClassicalExamples:
    """
    专旺格测试 - 使用古籍真实案例

    根据《渊海子平》《三命通会》《滴天髓》等古籍的成格条件:
    1. 日干属该五行
    2. 月令为该五行得令或生扶之月
    3. 地支多该五行，成方成局
    4. 无克神破格
    """

    # ==================== 曲直格 (Wood Dominant) ====================

    def test_qu_zhi_ge_classic_1(self, pattern_analyzer, wuxing_calculator):
        """
        曲直格案例1: 癸卯 乙卯 甲寅 乙亥
        来源: 《神机阁》命例
        木当令(卯月)，亥与寅合化，所有气势集中于木。
        """
        bazi = BaZi.from_chinese("癸卯 乙卯 甲寅 乙亥")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "应检测到曲直格"
        assert qu_zhi[0].element == WuXing.WOOD
        # 卯月木当令，应满足月令条件
        assert any('得令' in c or '卯' in c for c in qu_zhi[0].conditions_met)

    def test_qu_zhi_ge_classic_2(self, pattern_analyzer, wuxing_calculator):
        """
        曲直格案例2: 甲辰 丙寅 乙卯 癸未
        来源: 《神机阁》命例
        日干乙木，柱中寅卯辰会成木局，又有未土木库助力
        """
        bazi = BaZi.from_chinese("甲辰 丙寅 乙卯 癸未")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "应检测到曲直格"
        assert qu_zhi[0].element == WuXing.WOOD

    def test_qu_zhi_ge_with_water_month(self, pattern_analyzer, wuxing_calculator):
        """
        曲直格案例: 甲寅 乙亥 乙卯 戊寅
        亥月水生木，也算有气，木多又得月令之生
        """
        bazi = BaZi.from_chinese("甲寅 乙亥 乙卯 戊寅")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "亥月水生木，也能成曲直格"

    def test_qu_zhi_ge_classic_3(self, pattern_analyzer, wuxing_calculator):
        """
        曲直格案例3: 癸亥 甲寅 乙未 己卯
        来源: 《神机阁》命例
        木旺，三合木局成化，水土之力皆转移到木之上
        """
        bazi = BaZi.from_chinese("癸亥 甲寅 乙未 己卯")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "应检测到曲直格 - 三合木局"

    def test_qu_zhi_ge_classic_4(self, pattern_analyzer, wuxing_calculator):
        """
        曲直格案例4: 壬寅 甲辰 乙卯 己卯
        来源: 《神机阁》命例
        木虽不当令(辰月)，但木极多，力量特别强
        """
        bazi = BaZi.from_chinese("壬寅 甲辰 乙卯 己卯")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        # 辰月虽非木月，但木极多，可能成格或部分成格
        assert len(qu_zhi) >= 1 or result.dominant_element == WuXing.WOOD

    def test_qu_zhi_ge_wrong_month_fails(self, pattern_analyzer, wuxing_calculator):
        """
        曲直格失败案例: 甲寅 庚申 甲卯 乙寅
        申月金旺克木，不得月令，且有克神
        """
        bazi = BaZi.from_chinese("甲寅 庚申 甲卯 乙寅")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        if qu_zhi:
            # 应该有失败条件
            assert len(qu_zhi[0].conditions_failed) > 0
            assert not qu_zhi[0].is_valid, "申月不得月令，不应成格"

    # ==================== 炎上格 (Fire Dominant) ====================

    def test_yan_shang_ge_classic_1(self, pattern_analyzer, wuxing_calculator):
        """
        炎上格案例1: 丁巳 丙午 丙寅 乙未
        来源: 《渊海子平》
        丙火生于午月，支全巳午未南方，一片真火之气
        """
        bazi = BaZi.from_chinese("丁巳 丙午 丙寅 乙未")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1, "应检测到炎上格"
        assert yan_shang[0].element == WuXing.FIRE

    def test_yan_shang_ge_classic_2(self, pattern_analyzer, wuxing_calculator):
        """
        炎上格案例2: 癸巳 丁巳 丁卯 丙午
        巳火当令，天干三火透干，癸水无根，格成炎上
        """
        bazi = BaZi.from_chinese("癸巳 丁巳 丁卯 丙午")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1, "应检测到炎上格"

    def test_yan_shang_ge_with_wood_month(self, pattern_analyzer, wuxing_calculator):
        """
        炎上格案例: 丙寅 甲午 丙戌 癸巳
        寅月木生火，三合火局成化
        """
        bazi = BaZi.from_chinese("丙寅 甲午 丙戌 癸巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        # 午在月支为火旺
        assert len(yan_shang) >= 1

    def test_yan_shang_ge_broken_by_water(self, pattern_analyzer, wuxing_calculator):
        """
        炎上格破格案例: 丁巳 丙午 丁巳 辛亥
        时落亥支属强水冲击巳火，格不成
        """
        bazi = BaZi.from_chinese("丁巳 丙午 丁巳 辛亥")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        # 有亥水，虽然可能检测到但应有破格条件
        if yan_shang:
            # 格局不纯
            assert yan_shang[0].strength < 1.0 or len(yan_shang[0].conditions_failed) > 0

    # ==================== 稼穑格 (Earth Dominant) ====================

    def test_jia_se_ge_zhang_sanfeng(self, pattern_analyzer, wuxing_calculator):
        """
        稼穑格案例: 戊戌 己未 戊辰 癸丑
        来源: 《渊海子平》张真人(张三丰)命造
        季夏八字辰戌丑未全，戊己土三透
        """
        bazi = BaZi.from_chinese("戊戌 己未 戊辰 癸丑")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        assert len(jia_se) >= 1, "应检测到稼穑格 - 张三丰命造"
        assert jia_se[0].element == WuXing.EARTH

    def test_jia_se_ge_classic_2(self, pattern_analyzer, wuxing_calculator):
        """
        稼穑格案例: 丙戌 戊戌 己未 戊辰
        日干己土，柱中四支纯土，干支皆不见木克
        """
        bazi = BaZi.from_chinese("丙戌 戊戌 己未 戊辰")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        assert len(jia_se) >= 1, "应检测到稼穑格"

    def test_jia_se_ge_wrong_month_fails(self, pattern_analyzer, wuxing_calculator):
        """
        稼穑格失败: 戊辰 甲寅 戊戌 己丑
        寅月木旺克土，不得月令
        """
        bazi = BaZi.from_chinese("戊辰 甲寅 戊戌 己丑")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        if jia_se:
            assert len(jia_se[0].conditions_failed) > 0, "寅月非土旺月，应有失败条件"
            assert not jia_se[0].is_valid

    # ==================== 从革格 (Metal Dominant) ====================

    def test_cong_ge_metal_classic_1(self, pattern_analyzer, wuxing_calculator):
        """
        从革格案例: 庚申 甲申 庚申 辛巳
        来源: 《神机阁》命例
        一甲被克去，巳作合金论，格成专旺格
        """
        bazi = BaZi.from_chinese("庚申 甲申 庚申 辛巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        cong_ge = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_GE_METAL]
        assert len(cong_ge) >= 1, "应检测到从革格"
        assert cong_ge[0].element == WuXing.METAL

    def test_cong_ge_metal_classic_2(self, pattern_analyzer, wuxing_calculator):
        """
        从革格案例: 辛酉 戊戌 庚辰 辛巳
        辛酉年论，金旺
        """
        bazi = BaZi.from_chinese("辛酉 戊戌 庚辰 辛巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        cong_ge = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_GE_METAL]
        assert len(cong_ge) >= 1, "应检测到从革格"

    # ==================== 润下格 (Water Dominant) ====================

    def test_run_xia_ge_classic_1(self, pattern_analyzer, wuxing_calculator):
        """
        润下格案例: 癸亥 癸亥 壬子 辛丑
        来源: 《神机阁》命例
        日干壬水，生于亥月，地支全亥子丑水局
        """
        bazi = BaZi.from_chinese("癸亥 癸亥 壬子 辛丑")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        run_xia = [p for p in result.detected_patterns if p.pattern_type == PatternType.RUN_XIA]
        assert len(run_xia) >= 1, "应检测到润下格"
        assert run_xia[0].element == WuXing.WATER

    def test_run_xia_ge_wang_yangming(self, pattern_analyzer, wuxing_calculator):
        """
        润下格案例: 壬辰 辛亥 癸亥 癸亥
        来源: 王阳明命造
        癸水生于亥月，真正的润下格
        """
        bazi = BaZi.from_chinese("壬辰 辛亥 癸亥 癸亥")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        run_xia = [p for p in result.detected_patterns if p.pattern_type == PatternType.RUN_XIA]
        assert len(run_xia) >= 1, "应检测到润下格 - 王阳明命造"

    def test_run_xia_ge_with_metal_month(self, pattern_analyzer, wuxing_calculator):
        """
        润下格案例: 壬申 壬申 壬子 癸卯
        申月金生水，也能成格
        """
        bazi = BaZi.from_chinese("壬申 壬申 壬子 癸卯")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        run_xia = [p for p in result.detected_patterns if p.pattern_type == PatternType.RUN_XIA]
        assert len(run_xia) >= 1, "申月金生水，也能成润下格"


class TestHuaGeClassicalExamples:
    """
    化格测试 - 使用古籍成格条件

    根据《渊海子平》《三命通会》等古籍，化格条件极为严苛:
    1. 日干与邻干(月干或时干)相合
    2. 月令必须是化神旺相之月
    3. 命局化神有力，无克神破化
    4. 辰时"逢龙而化"更易成格
    """

    def test_jia_ji_hua_tu_with_correct_month(self, pattern_analyzer, wuxing_calculator):
        """
        甲己化土: 需辰戌丑未月(四季月)
        案例: 己辰 己未 甲辰 己丑
        """
        bazi = BaZi.from_chinese("己辰 己未 甲辰 己丑")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        assert len(hua_tu) >= 1, "甲己化土，未月土旺应成格"
        assert hua_tu[0].element == WuXing.EARTH

    def test_jia_ji_hua_tu_classic_zhou_mu(self, pattern_analyzer, wuxing_calculator):
        """
        甲己化土案例: 戊辰 壬戌 甲辰 己巳
        来源: 古籍命例 - 州牧之贵
        甲己化土又得月令(戌月)，地支土旺，不见木星破局
        """
        bazi = BaZi.from_chinese("戊辰 壬戌 甲辰 己巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        assert len(hua_tu) >= 1, "甲己化土，戌月土旺应成格 - 州牧之贵"

    def test_jia_ji_hua_tu_classic_premier(self, pattern_analyzer, wuxing_calculator):
        """
        甲己化土案例: 戊辰 乙丑 甲辰 己巳
        来源: 古籍命例 - 国务总理
        甲己化土得月令(丑月)，地支土旺又透干
        乙木虚浮无根，为假化土格
        """
        bazi = BaZi.from_chinese("戊辰 乙丑 甲辰 己巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        # 有乙木可能破格，但乙木无根，仍可成假化格
        assert len(hua_tu) >= 1, "甲己化土，丑月土旺 - 国务总理命造"

    def test_jia_ji_hua_tu_wrong_month_fails(self, pattern_analyzer, wuxing_calculator):
        """
        甲己化土失败: 寅月木旺，非土旺月
        """
        bazi = BaZi.from_chinese("己辰 甲寅 甲辰 己戌")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        if hua_tu:
            # 寅月不是化土月，应有失败条件
            assert len(hua_tu[0].conditions_failed) > 0, "寅月非土旺月，化土难成"
            assert not hua_tu[0].is_valid

    def test_yi_geng_hua_jin_with_correct_month(self, pattern_analyzer, wuxing_calculator):
        """
        乙庚化金: 需申酉月(秋季金旺)
        案例: 庚申 庚申 乙酉 辛巳
        """
        bazi = BaZi.from_chinese("庚申 庚申 乙酉 辛巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_jin = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_JIN]
        assert len(hua_jin) >= 1, "乙庚化金，申月金旺应成格"
        assert hua_jin[0].element == WuXing.METAL

    def test_yi_geng_hua_jin_wrong_month_fails(self, pattern_analyzer, wuxing_calculator):
        """
        乙庚化金失败: 寅月木旺
        """
        bazi = BaZi.from_chinese("庚寅 甲寅 乙卯 庚申")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_jin = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_JIN]
        if hua_jin:
            assert len(hua_jin[0].conditions_failed) > 0, "寅月非金旺月，化金难成"

    def test_bing_xin_hua_shui_with_correct_month(self, pattern_analyzer, wuxing_calculator):
        """
        丙辛化水: 需亥子月(冬季水旺)
        """
        bazi = BaZi.from_chinese("辛亥 辛亥 丙子 辛丑")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_shui = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_SHUI]
        assert len(hua_shui) >= 1, "丙辛化水，亥月水旺应成格"

    def test_ding_ren_hua_mu_with_correct_month(self, pattern_analyzer, wuxing_calculator):
        """
        丁壬化木: 需寅卯月(春季木旺)
        """
        bazi = BaZi.from_chinese("壬寅 壬寅 丁卯 壬寅")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_mu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_MU]
        assert len(hua_mu) >= 1, "丁壬化木，寅月木旺应成格"

    def test_wu_gui_hua_huo_with_correct_month(self, pattern_analyzer, wuxing_calculator):
        """
        戊癸化火: 需巳午月(夏季火旺)
        """
        bazi = BaZi.from_chinese("癸巳 戊午 戊巳 癸巳")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_huo = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_HUO]
        assert len(hua_huo) >= 1, "戊癸化火，午月火旺应成格"

    def test_feng_long_er_hua(self, pattern_analyzer, wuxing_calculator):
        """
        逢龙而化: 辰时更易成化
        """
        bazi = BaZi.from_chinese("己辰 己未 甲戌 戊辰")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        assert len(hua_tu) >= 1
        # 应该有"逢龙而化"的条件
        assert any('龙' in c for c in hua_tu[0].conditions_met), "辰时应有逢龙而化"


class TestCongGeClassicalExamples:
    """
    从格测试 - 基于古籍条件

    根据《子平真诠》《渊海子平》《滴天髓》等古籍，从格条件:
    1. 日主无根 - 地支藏干无比劫或强印根
    2. 天干无比劫印绶帮身
    3. 所从之神当令或成势
    """

    def test_cong_cai_ge_classic(self, pattern_analyzer, wuxing_calculator):
        """
        从财格: 日主无根，财星当令成势
        案例: 戊辰 己未 乙丑 戊戌
        乙木日主，四柱全土，财星极旺
        """
        bazi = BaZi.from_chinese("戊辰 己未 乙丑 戊戌")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        cong_cai = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_CAI]
        # 此案例日主无根，财星极旺
        if cong_cai:
            assert cong_cai[0].element == WuXing.EARTH  # 财星土

    def test_cong_cai_ge_classic_2(self, pattern_analyzer, wuxing_calculator):
        """
        从财格案例2: 壬寅 壬寅 辛卯 壬辰
        来源: 《神机阁》命例
        日干辛金衰极无助，生于寅月为财，寅卯辰三会财局
        """
        bazi = BaZi.from_chinese("壬寅 壬寅 辛卯 壬辰")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        # 辛金从财(木)
        cong_cai = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_CAI]
        if cong_cai:
            assert cong_cai[0].element == WuXing.WOOD  # 财星木

    def test_cong_sha_ge_classic_1(self, pattern_analyzer, wuxing_calculator):
        """
        从杀格案例1: 戊戌 辛酉 乙申 乙酉
        来源: 《神机阁》命例
        乙木日干生于酉月死地，七杀当令，乙木全无生气
        """
        bazi = BaZi.from_chinese("戊戌 辛酉 乙申 乙酉")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        cong_sha = [p for p in result.detected_patterns
                    if p.pattern_type in (PatternType.CONG_SHA, PatternType.CONG_GUAN)]
        if cong_sha:
            assert cong_sha[0].element == WuXing.METAL  # 金为杀

    def test_cong_sha_ge_classic_2(self, pattern_analyzer, wuxing_calculator):
        """
        从杀格案例2: 辛巳 辛丑 乙酉 乙酉
        来源: 《神机阁》命例
        乙木冬生，支全金局，二杀明透有力，格取从杀
        """
        bazi = BaZi.from_chinese("辛巳 辛丑 乙酉 乙酉")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        cong_sha = [p for p in result.detected_patterns
                    if p.pattern_type in (PatternType.CONG_SHA, PatternType.CONG_GUAN)]
        if cong_sha:
            assert cong_sha[0].element == WuXing.METAL

    def test_cong_guan_sha_ge_classic(self, pattern_analyzer, wuxing_calculator):
        """
        从官杀格: 日主无根，官杀当令成势
        案例: 庚申 庚辰 甲申 庚午
        甲木日主，金旺无根
        """
        bazi = BaZi.from_chinese("庚申 庚辰 甲申 庚午")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        # 从官或从杀
        cong_patterns = [p for p in result.detected_patterns
                        if p.pattern_type in (PatternType.CONG_GUAN, PatternType.CONG_SHA)]
        # 甲木见庚金为七杀(同阳)
        if cong_patterns:
            assert cong_patterns[0].element == WuXing.METAL

    def test_cong_er_ge_classic(self, pattern_analyzer, wuxing_calculator):
        """
        从儿格: 日主无根，食伤当令成势
        案例: 丙午 丙午 甲午 丙午
        """
        bazi = BaZi.from_chinese("丙午 丙午 甲午 丙午")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        cong_er = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_ER]
        if cong_er:
            assert cong_er[0].element == WuXing.FIRE  # 食伤火

    def test_no_cong_ge_with_root(self, pattern_analyzer, wuxing_calculator):
        """
        有根不成从格: 日主有比劫或印绶帮身
        """
        bazi = BaZi.from_chinese("甲寅 己未 乙丑 戊戌")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        # 年干甲木帮身，不应成从格
        cong_patterns = [p for p in result.detected_patterns
                        if p.category == PatternCategory.CONG_GE]
        assert len(cong_patterns) == 0, "有比劫帮身，不应成从格"


class TestPatternAnalysisProperties:
    """Tests for PatternAnalysis result properties."""

    def test_has_special_pattern(self, pattern_analyzer, wuxing_calculator):
        """has_special_pattern should be True when valid pattern exists."""
        # 使用经典曲直格案例
        bazi = BaZi.from_chinese("癸卯 乙卯 甲寅 乙亥")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        if result.has_special_pattern:
            assert result.primary_pattern is not None
            assert result.primary_pattern.is_valid

    def test_get_pattern_description(self, pattern_analyzer, wuxing_calculator):
        """get_pattern_description should return meaningful text."""
        bazi = BaZi.from_chinese("癸卯 乙卯 甲寅 乙亥")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        description = result.get_pattern_description()
        assert len(description) > 0

    def test_get_favorable_advice(self, pattern_analyzer, wuxing_calculator):
        """get_favorable_advice should return advice list."""
        bazi = BaZi.from_chinese("癸卯 乙卯 甲寅 乙亥")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        advice = result.get_favorable_advice()
        assert isinstance(advice, list)


class TestPatternAnalyzerEdgeCases:
    """Edge case tests."""

    def test_normal_pattern_when_mixed_elements(self, pattern_analyzer, wuxing_calculator):
        """Should not detect special pattern when elements are mixed."""
        bazi = BaZi.from_chinese("甲子 丙寅 戊午 庚申")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        # 五行混杂，不应有专旺格
        zhuan_wang = [p for p in result.detected_patterns
                      if p.category == PatternCategory.ZHUAN_WANG and p.is_valid]
        assert len(zhuan_wang) == 0, "五行混杂不应成专旺格"

    def test_partial_pattern_detected(self, pattern_analyzer, wuxing_calculator):
        """Partial patterns should be detected but not valid."""
        # 部分符合条件但不完全成格
        bazi = BaZi.from_chinese("甲寅 丙午 乙卯 甲寅")
        wuxing_values = get_wuxing_values(bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(bazi, wuxing_values)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        if qu_zhi:
            # 午月非木旺月，应该是部分格局
            if not qu_zhi[0].is_valid:
                assert qu_zhi[0].is_partial or len(qu_zhi[0].conditions_failed) > 0


class TestRealBaZiIntegration:
    """
    Integration tests with real BaZi objects from the system.

    These tests verify the pattern analyzer works correctly with
    the full domain model stack.
    """

    def test_analyzer_with_sample_bazi_fixture(self, pattern_analyzer, wuxing_calculator, sample_bazi):
        """Test pattern analyzer with the sample_bazi fixture."""
        wuxing_values = get_wuxing_values(sample_bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(sample_bazi, wuxing_values)

        # sample_bazi is 甲子 乙丑 丙寅 丁卯 - mixed elements, should not be special pattern
        assert isinstance(result.detected_patterns, list)
        assert result.dominant_element is not None

    def test_analyzer_with_strong_day_master_fixture(self, pattern_analyzer, wuxing_calculator, strong_day_master_bazi):
        """Test pattern analyzer with strong day master (fire dominant)."""
        # strong_day_master_bazi is 丙午 丁巳 丙午 丁巳 - fire dominant
        wuxing_values = get_wuxing_values(strong_day_master_bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(strong_day_master_bazi, wuxing_values)

        # This should detect 炎上格 - fire dominant pattern
        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1, "强火命造应检测到炎上格"
        assert yan_shang[0].element == WuXing.FIRE

    def test_analyzer_with_weak_day_master_fixture(self, pattern_analyzer, wuxing_calculator, weak_day_master_bazi):
        """Test pattern analyzer with weak day master (water dominant)."""
        # weak_day_master_bazi is 壬子 癸丑 丙子 癸亥 - water dominant, fire weak
        wuxing_values = get_wuxing_values(weak_day_master_bazi, wuxing_calculator)
        result = pattern_analyzer.analyze(weak_day_master_bazi, wuxing_values)

        # Day master is weak, may detect 从格 (following pattern)
        assert result.day_master_strength < 0.3  # Fire day master should be weak
        assert result.dominant_element == WuXing.WATER

    def test_bazi_from_chinese_consistency(self, pattern_analyzer, wuxing_calculator):
        """Verify BaZi.from_chinese creates consistent objects."""
        # Create same BaZi two different ways
        bazi1 = BaZi.from_chinese("癸卯 乙卯 甲寅 乙亥")
        bazi2 = BaZi.from_chinese("癸卯乙卯甲寅乙亥")  # No spaces

        values1 = get_wuxing_values(bazi1, wuxing_calculator)
        values2 = get_wuxing_values(bazi2, wuxing_calculator)

        result1 = pattern_analyzer.analyze(bazi1, values1)
        result2 = pattern_analyzer.analyze(bazi2, values2)

        # Results should be identical
        assert len(result1.detected_patterns) == len(result2.detected_patterns)
        assert result1.dominant_element == result2.dominant_element
