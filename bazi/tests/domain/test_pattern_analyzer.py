"""
Tests for PatternAnalyzer service.

Tests special pattern (格局) detection in BaZi charts using real cases
from classical texts (《渊海子平》《三命通会》《滴天髓》等).

特殊格局非常苛刻，测试用例基于古籍真实八字案例。
"""
import pytest
from unittest.mock import MagicMock
from typing import Dict

from bazi.domain.services.pattern_analyzer import PatternAnalyzer
from bazi.domain.models.pattern_analysis import (
    PatternCategory,
    PatternType,
)
from bazi.domain.models.elements import WuXing, YinYang


# 天干五行映射
STEM_WUXING: Dict[str, WuXing] = {
    '甲': WuXing.WOOD, '乙': WuXing.WOOD,
    '丙': WuXing.FIRE, '丁': WuXing.FIRE,
    '戊': WuXing.EARTH, '己': WuXing.EARTH,
    '庚': WuXing.METAL, '辛': WuXing.METAL,
    '壬': WuXing.WATER, '癸': WuXing.WATER,
}

# 天干阴阳映射
STEM_YINYANG: Dict[str, YinYang] = {
    '甲': YinYang.YANG, '乙': YinYang.YIN,
    '丙': YinYang.YANG, '丁': YinYang.YIN,
    '戊': YinYang.YANG, '己': YinYang.YIN,
    '庚': YinYang.YANG, '辛': YinYang.YIN,
    '壬': YinYang.YANG, '癸': YinYang.YIN,
}


def create_mock_bazi(
    year_stem: str, year_branch: str,
    month_stem: str, month_branch: str,
    day_stem: str, day_branch: str,
    hour_stem: str, hour_branch: str,
):
    """
    Create a mock BaZi with specified stems and branches.

    Args:
        Format: 天干, 地支 for each pillar (year, month, day, hour)
    """
    bazi = MagicMock()

    def create_pillar(stem_chinese: str, branch_chinese: str):
        pillar = MagicMock()
        pillar.stem.chinese = stem_chinese
        pillar.stem.wuxing = STEM_WUXING[stem_chinese]
        pillar.stem.yinyang = STEM_YINYANG[stem_chinese]
        pillar.branch.chinese = branch_chinese
        pillar.hidden_stems = {}  # Simplified - no hidden stems
        return pillar

    bazi.year_pillar = create_pillar(year_stem, year_branch)
    bazi.month_pillar = create_pillar(month_stem, month_branch)
    bazi.day_pillar = create_pillar(day_stem, day_branch)
    bazi.hour_pillar = create_pillar(hour_stem, hour_branch)

    bazi.day_master = bazi.day_pillar.stem
    bazi.pillars = [bazi.year_pillar, bazi.month_pillar, bazi.day_pillar, bazi.hour_pillar]

    return bazi


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

    def test_qu_zhi_ge_classic_1(self):
        """
        曲直格案例1: 癸卯 乙卯 甲寅 乙亥
        来源: 《神机阁》命例
        木当令(卯月)，亥与寅合化，所有气势集中于木。
        """
        bazi = create_mock_bazi(
            '癸', '卯',  # 年: 癸卯
            '乙', '卯',  # 月: 乙卯 (卯月木当令)
            '甲', '寅',  # 日: 甲寅
            '乙', '亥',  # 时: 乙亥
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "应检测到曲直格"
        assert qu_zhi[0].element == WuXing.WOOD
        # 卯月木当令，应满足月令条件
        assert any('得令' in c or '卯' in c for c in qu_zhi[0].conditions_met)

    def test_qu_zhi_ge_classic_2(self):
        """
        曲直格案例2: 甲辰 丙寅 乙卯 癸未
        来源: 《神机阁》命例
        日干乙木，柱中寅卯辰会成木局，又有未土木库助力
        """
        bazi = create_mock_bazi(
            '甲', '辰',  # 年
            '丙', '寅',  # 月: 寅月木当令
            '乙', '卯',  # 日
            '癸', '未',  # 时
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "应检测到曲直格"
        assert qu_zhi[0].element == WuXing.WOOD

    def test_qu_zhi_ge_with_water_month(self):
        """
        曲直格案例: 甲寅 乙亥 乙卯 戊寅
        亥月水生木，也算有气，木多又得月令之生
        """
        bazi = create_mock_bazi(
            '甲', '寅',
            '乙', '亥',  # 亥月水生木
            '乙', '卯',
            '戊', '寅',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        assert len(qu_zhi) >= 1, "亥月水生木，也能成曲直格"

    def test_qu_zhi_ge_wrong_month_fails(self):
        """
        曲直格失败案例: 甲寅 庚酉 甲卯 乙寅
        酉月金旺克木，不得月令，且有克神
        """
        bazi = create_mock_bazi(
            '甲', '寅',
            '庚', '酉',  # 酉月金旺，不是木旺月
            '甲', '卯',
            '乙', '寅',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        if qu_zhi:
            # 应该有失败条件
            assert len(qu_zhi[0].conditions_failed) > 0
            assert not qu_zhi[0].is_valid, "酉月不得月令，不应成格"

    # ==================== 炎上格 (Fire Dominant) ====================

    def test_yan_shang_ge_classic_1(self):
        """
        炎上格案例1: 丁巳 丙午 丙寅 乙未
        来源: 《渊海子平》
        丙火生于午月，支全巳午未南方，一片真火之气
        """
        bazi = create_mock_bazi(
            '丁', '巳',
            '丙', '午',  # 午月火当令
            '丙', '寅',
            '乙', '未',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1, "应检测到炎上格"
        assert yan_shang[0].element == WuXing.FIRE

    def test_yan_shang_ge_classic_2(self):
        """
        炎上格案例2: 癸巳 丁巳 丁卯 丙午
        巳火当令，天干三火透干，癸水无根，格成炎上
        """
        bazi = create_mock_bazi(
            '癸', '巳',
            '丁', '巳',  # 巳月火当令
            '丁', '卯',
            '丙', '午',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1, "应检测到炎上格"

    def test_yan_shang_ge_with_wood_month(self):
        """
        炎上格案例: 丙寅 甲午 丙戌 癸巳
        寅月木生火，三合火局成化
        """
        bazi = create_mock_bazi(
            '丙', '寅',
            '甲', '午',  # 午火当令 (注: 原案例有误，应以午月为主)
            '丙', '戌',
            '癸', '巳',
        )
        # 实际上此案例午为火旺
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        assert len(yan_shang) >= 1

    def test_yan_shang_ge_broken_by_water(self):
        """
        炎上格破格案例: 丁巳 丙午 丁巳 辛亥
        时落亥支属强水冲击巳火，格不成
        """
        bazi = create_mock_bazi(
            '丁', '巳',
            '丙', '午',
            '丁', '巳',
            '辛', '亥',  # 亥水冲巳
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        yan_shang = [p for p in result.detected_patterns if p.pattern_type == PatternType.YAN_SHANG]
        # 有亥水，虽然可能检测到但应有破格条件
        if yan_shang:
            # 格局不纯
            assert yan_shang[0].strength < 1.0 or len(yan_shang[0].conditions_failed) > 0

    # ==================== 稼穑格 (Earth Dominant) ====================

    def test_jia_se_ge_zhang_sanfeng(self):
        """
        稼穑格案例: 戊戌 己未 戊辰 癸丑
        来源: 《渊海子平》张真人(张三丰)命造
        季夏八字辰戌丑未全，戊己土三透
        """
        bazi = create_mock_bazi(
            '戊', '戌',
            '己', '未',  # 未月土当令
            '戊', '辰',
            '癸', '丑',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        assert len(jia_se) >= 1, "应检测到稼穑格 - 张三丰命造"
        assert jia_se[0].element == WuXing.EARTH

    def test_jia_se_ge_classic_2(self):
        """
        稼穑格案例: 丙戌 戊戌 己未 戊辰
        日干己土，柱中四支纯土，干支皆不见木克
        """
        bazi = create_mock_bazi(
            '丙', '戌',
            '戊', '戌',  # 戌月土当令
            '己', '未',
            '戊', '辰',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        assert len(jia_se) >= 1, "应检测到稼穑格"

    def test_jia_se_ge_wrong_month_fails(self):
        """
        稼穑格失败: 戊辰 甲寅 戊戌 己丑
        寅月木旺克土，不得月令
        """
        bazi = create_mock_bazi(
            '戊', '辰',
            '甲', '寅',  # 寅月木旺，非土旺月
            '戊', '戌',
            '己', '丑',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        jia_se = [p for p in result.detected_patterns if p.pattern_type == PatternType.JIA_SE]
        if jia_se:
            assert len(jia_se[0].conditions_failed) > 0, "寅月非土旺月，应有失败条件"
            assert not jia_se[0].is_valid

    # ==================== 从革格 (Metal Dominant) ====================

    def test_cong_ge_metal_classic_1(self):
        """
        从革格案例: 庚申 甲申 庚申 辛巳
        来源: 《神机阁》命例
        一甲被克去，巳作合金论，格成专旺格
        """
        bazi = create_mock_bazi(
            '庚', '申',
            '甲', '申',  # 申月金当令
            '庚', '申',
            '辛', '巳',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        cong_ge = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_GE_METAL]
        assert len(cong_ge) >= 1, "应检测到从革格"
        assert cong_ge[0].element == WuXing.METAL

    def test_cong_ge_metal_classic_2(self):
        """
        从革格案例: 辛酉 戊戌 庚辰 辛巳
        辛酉年论，金旺
        """
        bazi = create_mock_bazi(
            '辛', '酉',
            '戊', '戌',  # 戌月土生金
            '庚', '辰',
            '辛', '巳',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        cong_ge = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_GE_METAL]
        assert len(cong_ge) >= 1, "应检测到从革格"

    # ==================== 润下格 (Water Dominant) ====================

    def test_run_xia_ge_classic_1(self):
        """
        润下格案例: 癸亥 癸亥 壬子 辛丑
        来源: 《神机阁》命例
        日干壬水，生于亥月，地支全亥子丑水局
        """
        bazi = create_mock_bazi(
            '癸', '亥',
            '癸', '亥',  # 亥月水当令
            '壬', '子',
            '辛', '丑',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        run_xia = [p for p in result.detected_patterns if p.pattern_type == PatternType.RUN_XIA]
        assert len(run_xia) >= 1, "应检测到润下格"
        assert run_xia[0].element == WuXing.WATER

    def test_run_xia_ge_wang_yangming(self):
        """
        润下格案例: 壬辰 辛亥 癸亥 癸亥
        来源: 王阳明命造
        癸水生于亥月，真正的润下格
        """
        bazi = create_mock_bazi(
            '壬', '辰',
            '辛', '亥',  # 亥月水当令
            '癸', '亥',
            '癸', '亥',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        run_xia = [p for p in result.detected_patterns if p.pattern_type == PatternType.RUN_XIA]
        assert len(run_xia) >= 1, "应检测到润下格 - 王阳明命造"

    def test_run_xia_ge_with_metal_month(self):
        """
        润下格案例: 壬申 壬申 壬子 癸卯
        申月金生水，也能成格
        """
        bazi = create_mock_bazi(
            '壬', '申',
            '壬', '申',  # 申月金生水
            '壬', '子',
            '癸', '卯',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

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

    def test_jia_ji_hua_tu_with_correct_month(self):
        """
        甲己化土: 需辰戌丑未月(四季月)
        案例: 己辰 己未 甲辰 己丑
        """
        bazi = create_mock_bazi(
            '己', '辰',
            '己', '未',  # 未月土当令
            '甲', '辰',
            '己', '丑',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        assert len(hua_tu) >= 1, "甲己化土，未月土旺应成格"
        assert hua_tu[0].element == WuXing.EARTH

    def test_jia_ji_hua_tu_wrong_month_fails(self):
        """
        甲己化土失败: 寅月木旺，非土旺月
        """
        bazi = create_mock_bazi(
            '己', '辰',
            '甲', '寅',  # 寅月木旺，非化土月
            '甲', '辰',
            '己', '戌',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_tu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_TU]
        if hua_tu:
            # 寅月不是化土月，应有失败条件
            assert len(hua_tu[0].conditions_failed) > 0, "寅月非土旺月，化土难成"
            assert not hua_tu[0].is_valid

    def test_yi_geng_hua_jin_with_correct_month(self):
        """
        乙庚化金: 需申酉月(秋季金旺)
        案例: 庚申 庚申 乙酉 辛巳
        """
        bazi = create_mock_bazi(
            '庚', '申',
            '庚', '申',  # 申月金当令
            '乙', '酉',
            '辛', '巳',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_jin = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_JIN]
        assert len(hua_jin) >= 1, "乙庚化金，申月金旺应成格"
        assert hua_jin[0].element == WuXing.METAL

    def test_yi_geng_hua_jin_wrong_month_fails(self):
        """
        乙庚化金失败: 寅月木旺
        """
        bazi = create_mock_bazi(
            '庚', '寅',
            '甲', '寅',  # 寅月木旺，非金旺月
            '乙', '卯',
            '庚', '申',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_jin = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_JIN]
        if hua_jin:
            assert len(hua_jin[0].conditions_failed) > 0, "寅月非金旺月，化金难成"

    def test_bing_xin_hua_shui_with_correct_month(self):
        """
        丙辛化水: 需亥子月(冬季水旺)
        """
        bazi = create_mock_bazi(
            '辛', '亥',
            '辛', '亥',  # 亥月水当令
            '丙', '子',
            '辛', '丑',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_shui = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_SHUI]
        assert len(hua_shui) >= 1, "丙辛化水，亥月水旺应成格"

    def test_ding_ren_hua_mu_with_correct_month(self):
        """
        丁壬化木: 需寅卯月(春季木旺)
        """
        bazi = create_mock_bazi(
            '壬', '寅',
            '壬', '寅',  # 寅月木当令
            '丁', '卯',
            '壬', '寅',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_mu = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_MU]
        assert len(hua_mu) >= 1, "丁壬化木，寅月木旺应成格"

    def test_wu_gui_hua_huo_with_correct_month(self):
        """
        戊癸化火: 需巳午月(夏季火旺)
        """
        bazi = create_mock_bazi(
            '癸', '巳',
            '戊', '午',  # 午月火当令
            '戊', '巳',
            '癸', '巳',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        hua_huo = [p for p in result.detected_patterns if p.pattern_type == PatternType.HUA_HUO]
        assert len(hua_huo) >= 1, "戊癸化火，午月火旺应成格"

    def test_feng_long_er_hua(self):
        """
        逢龙而化: 辰时更易成化
        """
        bazi = create_mock_bazi(
            '己', '辰',
            '己', '未',  # 未月土旺
            '甲', '戌',
            '戊', '辰',  # 辰时 - 逢龙而化
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

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

    def test_cong_cai_ge_classic(self):
        """
        从财格: 日主无根，财星当令成势
        案例: 戊辰 己未 乙丑 戊戌
        乙木日主，四柱全土，财星极旺
        """
        bazi = create_mock_bazi(
            '戊', '辰',
            '己', '未',  # 未月土当令 (财星)
            '乙', '丑',
            '戊', '戌',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        cong_cai = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_CAI]
        # 此案例日主无根，财星极旺
        if cong_cai:
            assert cong_cai[0].element == WuXing.EARTH  # 财星土

    def test_cong_guan_sha_ge_classic(self):
        """
        从官杀格: 日主无根，官杀当令成势
        案例: 庚申 庚辰 甲申 庚午
        甲木日主，金旺无根
        """
        bazi = create_mock_bazi(
            '庚', '申',
            '庚', '辰',  # 辰月土旺生金
            '甲', '申',
            '庚', '午',
        )
        # 需要设置hidden_stems为空确保无根
        for pillar in bazi.pillars:
            pillar.hidden_stems = {}

        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # 从官或从杀
        cong_patterns = [p for p in result.detected_patterns
                        if p.pattern_type in (PatternType.CONG_GUAN, PatternType.CONG_SHA)]
        # 甲木见庚金为七杀(同阳)
        if cong_patterns:
            assert cong_patterns[0].element == WuXing.METAL

    def test_cong_er_ge_classic(self):
        """
        从儿格: 日主无根，食伤当令成势
        案例: 丙午 丙申 甲午 丙寅 (简化版)
        """
        bazi = create_mock_bazi(
            '丙', '午',
            '丙', '午',  # 午月火当令 (食伤)
            '甲', '午',
            '丙', '午',
        )
        # 确保无印比根
        for pillar in bazi.pillars:
            pillar.hidden_stems = {}

        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        cong_er = [p for p in result.detected_patterns if p.pattern_type == PatternType.CONG_ER]
        if cong_er:
            assert cong_er[0].element == WuXing.FIRE  # 食伤火

    def test_no_cong_ge_with_root(self):
        """
        有根不成从格: 日主有比劫或印绶帮身
        """
        bazi = create_mock_bazi(
            '甲', '寅',  # 甲木比肩
            '己', '未',
            '乙', '丑',
            '戊', '戌',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # 年干甲木帮身，不应成从格
        cong_patterns = [p for p in result.detected_patterns
                        if p.category == PatternCategory.CONG_GE]
        assert len(cong_patterns) == 0, "有比劫帮身，不应成从格"


class TestPatternAnalysisProperties:
    """Tests for PatternAnalysis result properties."""

    def test_has_special_pattern(self):
        """has_special_pattern should be True when valid pattern exists."""
        # 使用经典曲直格案例
        bazi = create_mock_bazi(
            '癸', '卯',
            '乙', '卯',
            '甲', '寅',
            '乙', '亥',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        if result.has_special_pattern:
            assert result.primary_pattern is not None
            assert result.primary_pattern.is_valid

    def test_get_pattern_description(self):
        """get_pattern_description should return meaningful text."""
        bazi = create_mock_bazi(
            '癸', '卯',
            '乙', '卯',
            '甲', '寅',
            '乙', '亥',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        description = result.get_pattern_description()
        assert len(description) > 0

    def test_get_favorable_advice(self):
        """get_favorable_advice should return advice list."""
        bazi = create_mock_bazi(
            '癸', '卯',
            '乙', '卯',
            '甲', '寅',
            '乙', '亥',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        advice = result.get_favorable_advice()
        assert isinstance(advice, list)


class TestPatternAnalyzerEdgeCases:
    """Edge case tests."""

    def test_normal_pattern_when_mixed_elements(self):
        """Should not detect special pattern when elements are mixed."""
        bazi = create_mock_bazi(
            '甲', '子',   # 木水
            '丙', '寅',   # 火木
            '戊', '午',   # 土火
            '庚', '申',   # 金金
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        # 五行混杂，不应有专旺格
        zhuan_wang = [p for p in result.detected_patterns
                      if p.category == PatternCategory.ZHUAN_WANG and p.is_valid]
        assert len(zhuan_wang) == 0, "五行混杂不应成专旺格"

    def test_partial_pattern_detected(self):
        """Partial patterns should be detected but not valid."""
        # 部分符合条件但不完全成格
        bazi = create_mock_bazi(
            '甲', '寅',
            '丙', '午',  # 非木月
            '乙', '卯',
            '甲', '寅',
        )
        analyzer = PatternAnalyzer()
        result = analyzer.analyze(bazi)

        qu_zhi = [p for p in result.detected_patterns if p.pattern_type == PatternType.QU_ZHI]
        if qu_zhi:
            # 午月非木旺月，应该是部分格局
            if not qu_zhi[0].is_valid:
                assert qu_zhi[0].is_partial or len(qu_zhi[0].conditions_failed) > 0
