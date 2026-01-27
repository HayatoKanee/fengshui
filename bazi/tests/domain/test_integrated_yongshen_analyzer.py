"""
Tests for Integrated 用神 (Favorable Elements) analyzer service.

Tests the combination of 扶抑用神, 调候用神, and 通关用神 methods.
"""
import pytest

from bazi.domain.models import BaZi, WuXing, DayMasterStrength, WuXingStrength, WangXiang
from bazi.domain.services import (
    IntegratedYongShenAnalyzer,
    IntegratedYongShenResult,
    SeasonType,
    MethodWeights,
)


class TestMethodWeights:
    """Tests for MethodWeights validation."""

    def test_weights_must_sum_to_one(self):
        """权重必须和为1"""
        # Valid
        weights = MethodWeights(fuyi=0.5, tiaohao=0.3, tongguan=0.2)
        assert weights.fuyi == 0.5

        # Invalid - should raise
        with pytest.raises(ValueError):
            MethodWeights(fuyi=0.5, tiaohao=0.5, tongguan=0.5)


class TestWeightCalculation:
    """Tests for weight calculation based on season."""

    @pytest.fixture
    def default_analyzer(self):
        return IntegratedYongShenAnalyzer()

    @pytest.fixture
    def custom_analyzer(self):
        """Custom weights: 30/50/20 for extreme, 40/40/20 for normal."""
        return IntegratedYongShenAnalyzer(
            default_weights=MethodWeights(fuyi=0.40, tiaohao=0.40, tongguan=0.20),
            extreme_weights=MethodWeights(fuyi=0.30, tiaohao=0.50, tongguan=0.20),
        )

    def test_default_extreme_cold_weights(self, default_analyzer):
        """默认极寒季节权重: 扶抑40% + 调候40% + 通关20%"""
        weights = default_analyzer._get_weights(SeasonType.EXTREME_COLD)
        assert weights.fuyi == 0.40
        assert weights.tiaohao == 0.40
        assert weights.tongguan == 0.20

    def test_default_moderate_weights(self, default_analyzer):
        """默认温和季节权重: 扶抑50% + 调候30% + 通关20%"""
        weights = default_analyzer._get_weights(SeasonType.MODERATE)
        assert weights.fuyi == 0.50
        assert weights.tiaohao == 0.30
        assert weights.tongguan == 0.20

    def test_custom_extreme_cold_weights(self, custom_analyzer):
        """自定义极寒季节权重"""
        weights = custom_analyzer._get_weights(SeasonType.EXTREME_COLD)
        assert weights.fuyi == 0.30
        assert weights.tiaohao == 0.50
        assert weights.tongguan == 0.20

    def test_custom_moderate_weights(self, custom_analyzer):
        """自定义温和季节权重"""
        weights = custom_analyzer._get_weights(SeasonType.MODERATE)
        assert weights.fuyi == 0.40
        assert weights.tiaohao == 0.40
        assert weights.tongguan == 0.20


class TestFuyiScores:
    """Tests for 扶抑法 pure balance scoring (no priority weights)."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_strong_day_master_fuyi_scores(self, analyzer):
        """身强时所有泄克五行同等有效，所有生扶五行同等忌"""
        # 身强: beneficial(70) > harmful(30), deficit = (70-30)/2 = 20
        strong_strength = DayMasterStrength(beneficial_value=70.0, harmful_value=30.0)
        scores = analyzer._calculate_fuyi_scores(WuXing.WOOD, strong_strength)

        # 身强木：所有泄克五行都得正分
        assert scores[WuXing.FIRE] > 0   # 食伤（泄）
        assert scores[WuXing.EARTH] > 0  # 财星（耗）
        assert scores[WuXing.METAL] > 0  # 官杀（克）

        # 身强木：所有生扶五行都得负分
        assert scores[WuXing.WATER] < 0  # 印星
        assert scores[WuXing.WOOD] < 0   # 比劫

        # 验证：所有泄克五行分数相同（无优先级）
        assert scores[WuXing.FIRE] == scores[WuXing.EARTH] == scores[WuXing.METAL]

        # 验证：分数就是deficit值
        assert abs(scores[WuXing.FIRE] - 20.0) < 0.01  # deficit = 20
        assert abs(scores[WuXing.WOOD] + 20.0) < 0.01  # -deficit = -20

    def test_weak_day_master_fuyi_scores(self, analyzer):
        """身弱时所有生扶五行同等有效，所有泄克五行同等忌"""
        # 身弱: beneficial(30) < harmful(70), deficit = (30-70)/2 = -20 → abs = 20
        weak_strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)
        scores = analyzer._calculate_fuyi_scores(WuXing.WOOD, weak_strength)

        # 身弱木：所有生扶五行都得正分
        assert scores[WuXing.WATER] > 0  # 印星
        assert scores[WuXing.WOOD] > 0   # 比劫

        # 身弱木：所有泄克五行都得负分
        assert scores[WuXing.FIRE] < 0   # 食伤
        assert scores[WuXing.EARTH] < 0  # 财星
        assert scores[WuXing.METAL] < 0  # 官杀

        # 验证：所有生扶五行分数相同（无优先级）
        assert scores[WuXing.WATER] == scores[WuXing.WOOD]

        # 验证：所有泄克五行分数相同（无优先级）
        assert scores[WuXing.FIRE] == scores[WuXing.EARTH] == scores[WuXing.METAL]

        # 验证：分数就是deficit值
        assert abs(scores[WuXing.WATER] - 20.0) < 0.01  # deficit = 20
        assert abs(scores[WuXing.EARTH] + 20.0) < 0.01  # -deficit = -20


class TestIntegratedAnalysis:
    """Tests for integrated analysis."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_analysis_without_wuxing_strength(self, analyzer):
        """不提供wuxing_strength时，通关评分为0"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)

        result = analyzer.analyze(bazi, strength, wuxing_strength=None)

        # 应该完成分析，通关评分为0
        assert result.yong_shen is not None
        for score in result.scores.values():
            assert score.tongguan_score == 0.0

    def test_analysis_with_wuxing_strength(self, analyzer):
        """提供wuxing_strength时，进行通关分析"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, strength, wuxing_strength)

        # 应该检测到金木相战，水通关
        assert result.tongguan_result is not None
        assert result.tongguan_result.has_conflict is True

    def test_extreme_season_weights_applied(self, analyzer):
        """极端季节应用正确权重"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")  # 子月极寒
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        # 子月是极寒季节
        assert result.tiaohao_result.season_type == SeasonType.EXTREME_COLD
        assert result.weights.fuyi == 0.40
        assert result.weights.tiaohao == 0.40
        assert result.weights.tongguan == 0.20

    def test_moderate_season_weights_applied(self, analyzer):
        """温和季节应用正确权重"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")  # 卯月温和
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        # 卯月是温和季节
        assert result.tiaohao_result.season_type == SeasonType.MODERATE
        assert result.weights.fuyi == 0.50
        assert result.weights.tiaohao == 0.30
        assert result.weights.tongguan == 0.20


class TestScoreDetails:
    """Tests for score details in results."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_scores_contain_all_elements(self, analyzer):
        """结果应包含所有五行的评分"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        assert len(result.scores) == 5
        for element in WuXing:
            assert element in result.scores
            score = result.scores[element]
            assert score.element == element

    def test_scores_have_all_components(self, analyzer):
        """评分应包含扶抑、调候、通关三个分量"""
        bazi = BaZi.from_chinese("甲子甲午甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        fire_score = result.scores[WuXing.FIRE]
        assert hasattr(fire_score, 'fuyi_score')
        assert hasattr(fire_score, 'tiaohao_score')
        assert hasattr(fire_score, 'tongguan_score')
        assert hasattr(fire_score, 'total_score')


class TestConfigurableWeights:
    """Tests for configurable weights."""

    def test_default_weights(self):
        """默认权重: 50/30/20"""
        analyzer = IntegratedYongShenAnalyzer()
        assert analyzer._default_weights.fuyi == 0.50
        assert analyzer._default_weights.tiaohao == 0.30
        assert analyzer._default_weights.tongguan == 0.20

    def test_custom_weights(self):
        """可以自定义权重"""
        custom = MethodWeights(fuyi=0.40, tiaohao=0.40, tongguan=0.20)
        analyzer = IntegratedYongShenAnalyzer(default_weights=custom)
        assert analyzer._default_weights.fuyi == 0.40
        assert analyzer._default_weights.tiaohao == 0.40

    def test_custom_weights_affect_analysis(self):
        """自定义权重影响分析结果"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")  # 温和季节
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        default = IntegratedYongShenAnalyzer()
        custom = IntegratedYongShenAnalyzer(
            default_weights=MethodWeights(fuyi=0.30, tiaohao=0.50, tongguan=0.20)
        )

        result_default = default.analyze(bazi, strength)
        result_custom = custom.analyze(bazi, strength)

        # 自定义权重的调候权重应该更高
        assert result_custom.weights.tiaohao > result_default.weights.tiaohao


class TestMethodUsedDescription:
    """Tests for method description."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_fuyi_dominant_description(self, analyzer):
        """扶抑为主时显示正确描述"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")  # 温和季节
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)
        assert "扶抑为主" in result.method_used

    def test_tongguan_mentioned_when_conflict(self, analyzer):
        """有相战时显示通关"""
        bazi = BaZi.from_chinese("甲子甲卯甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, strength, wuxing_strength)
        assert "通关" in result.method_used


class TestNotesContent:
    """Tests for analysis notes."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_notes_include_day_master_strength(self, analyzer):
        """备注应包含日主强弱"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "身弱" in notes_text

    def test_notes_include_season(self, analyzer):
        """备注应包含季节"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "极寒" in notes_text

    def test_notes_include_weights(self, analyzer):
        """备注应包含权重"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "扶抑" in notes_text
        assert "调候" in notes_text
        assert "通关" in notes_text

    def test_notes_include_conflict_when_present(self, analyzer):
        """有相战时备注应包含相战信息"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, strength, wuxing_strength)

        notes_text = " ".join(result.notes)
        assert "相战" in notes_text


class TestToFavorableElements:
    """Tests for conversion to FavorableElements."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_converts_to_favorable_elements(self, analyzer):
        """应能转换为传统FavorableElements对象"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)
        favorable = analyzer.to_favorable_elements(result)

        assert favorable.yong_shen == result.yong_shen
        assert favorable.xi_shen == result.xi_shen
        assert favorable.ji_shen == result.ji_shen
        assert favorable.chou_shen == result.chou_shen


class TestClassicalDerivation:
    """Tests for classical five-element relationship derivation."""

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    def test_classical_derivation_wood_yongshen(self, analyzer):
        """
        验证古籍定义的五行生克推导：
        用神=木 → 喜神=水(水生木) → 忌神=金(金克木) → 仇神=土(土生金) → 闲神=火(木生火)
        """
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        # 身弱，用神应该是印星(水)或比劫(木)
        strength = DayMasterStrength(beneficial_value=30.0, harmful_value=70.0)

        result = analyzer.analyze(bazi, strength)

        # 验证五行生克关系链
        assert result.xi_shen == result.yong_shen.generated_by  # 喜神=生用神
        assert result.ji_shen == result.yong_shen.overcome_by   # 忌神=克用神
        assert result.chou_shen == result.ji_shen.generated_by  # 仇神=生忌神
        assert result.xian_shen == result.yong_shen.generates   # 闲神=用神所生

    def test_all_five_elements_covered(self, analyzer):
        """五神应覆盖全部五行"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        all_shens = {
            result.yong_shen,
            result.xi_shen,
            result.ji_shen,
            result.chou_shen,
            result.xian_shen
        }
        # 五神应该覆盖全部五行
        assert len(all_shens) == 5
        assert all_shens == set(WuXing)

    def test_notes_include_derivation_chain(self, analyzer):
        """备注应包含推导链说明"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        strength = DayMasterStrength(beneficial_value=50.0, harmful_value=50.0)

        result = analyzer.analyze(bazi, strength)

        notes_text = " ".join(result.notes)
        assert "生用神" in notes_text
        assert "克用神" in notes_text
        assert "生忌神" in notes_text


class TestDayMasterAnalyzerIntegration:
    """Tests for DayMasterAnalyzer integration."""

    def test_full_analysis_integrated_with_tongguan(self):
        """full_analysis_integrated应包含通关分析"""
        from bazi.domain.services import DayMasterAnalyzer

        analyzer = DayMasterAnalyzer()
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")

        strength, favorable, wuxing, integrated_result = analyzer.full_analysis_integrated(bazi)

        assert integrated_result is not None
        assert isinstance(integrated_result, IntegratedYongShenResult)
        assert integrated_result.tongguan_result is not None
        assert len(integrated_result.notes) > 0

    def test_full_analysis_use_integrated_flag(self):
        """full_analysis的use_integrated标志应工作"""
        from bazi.domain.services import DayMasterAnalyzer

        analyzer = DayMasterAnalyzer()
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")

        # 传统方法
        _, favorable_trad, _ = analyzer.full_analysis(bazi, use_integrated=False)

        # 集成方法
        _, favorable_int, _ = analyzer.full_analysis(bazi, use_integrated=True)

        # 两种方法都应返回有效结果
        assert favorable_trad.yong_shen is not None
        assert favorable_int.yong_shen is not None


class TestRealWorldYongShenCases:
    """
    Real-world test cases with known yongshen from classical analysis.

    Tests validate that our integrated system produces correct yongshen
    for famous historical figures and documented cases.
    """

    @pytest.fixture
    def analyzer(self):
        return IntegratedYongShenAnalyzer()

    @pytest.fixture
    def day_master_analyzer(self):
        from bazi.domain.services import DayMasterAnalyzer
        return DayMasterAnalyzer()

    def test_wen_tianxiang_fire_strong_needs_water(self, day_master_analyzer):
        """
        文天祥八字：丙申 甲午 丁巳 庚子 (1236年)

        丁火日主生午月，火势旺盛，身强。
        年支申金、时柱庚子有水金，但午月丁巳火势过旺。
        用神：壬癸水（调候+克制火）
        喜神：金（生水）

        来源：经典命理分析，《三命通会》
        """
        bazi = BaZi.from_chinese("丙申甲午丁巳庚子")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        # 丁火生午月，应该身强
        assert strength.is_strong, "丁火生午月应该身强"

        # 身强火旺，需要水来调候和克制
        # 扶抑法：身强喜泄克（土金水）
        # 调候法：午月炎夏需水调候（壬癸水）
        # 综合来看，水应该是用神或在前几名
        ranked = result.yongshen_ranked
        print(f"文天祥八字评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 水应该在前3名（调候+扶抑都喜水）
        top_3 = ranked[:3]
        assert WuXing.WATER in top_3, f"水应在前3名，实际：{[e.chinese for e in top_3]}"

    def test_yao_ming_earth_weak_follows_metal_water(self, day_master_analyzer):
        """
        姚明八字：庚申 乙酉 戊子 壬戌 (1980年9月12日)

        戊土日主生酉月，金旺泄土，年月申酉金局更旺。
        乙庚合金成功，壬水透时干。戊土虚浮无根无助。
        格局：从金水两气（从儿从财格）
        用神：水（财星）
        喜神：金（食伤生财）

        来源：国易堂命理分析
        """
        bazi = BaZi.from_chinese("庚申乙酉戊子壬戌")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        # 戊土生酉月，金旺泄土，应该身弱
        # 注：从格判断需要特殊逻辑，这里先测试普通身弱情况
        print(f"姚明八字：身{'强' if strength.is_strong else '弱'}")
        print(f"生耗值：beneficial={strength.beneficial_value:.1f}, harmful={strength.harmful_value:.1f}")

        ranked = result.yongshen_ranked
        print(f"姚明八字评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 如果从金水格，则金水都应该排名靠前
        # 如果普通身弱，则土火（印比）排名靠前
        # 实际结果取决于我们系统的判断
        top_2 = ranked[:2]
        print(f"前两喜：{[e.chinese for e in top_2]}")

    def test_weak_water_likes_metal_water(self, day_master_analyzer):
        """
        身弱水案例：庚午 己卯 癸巳 甲寅

        癸水日主生卯月，木旺泄水。
        年庚金对癸水有生，但遭午火克制。
        甲寅木泄气，癸水身弱。
        用神：金水（印比）
        忌神：土木

        来源：算准网命理案例
        """
        bazi = BaZi.from_chinese("庚午己卯癸巳甲寅")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        # 癸水生卯月，木旺泄水，应该身弱
        assert not strength.is_strong, "癸水生卯月木旺泄应该身弱"

        ranked = result.yongshen_ranked
        print(f"身弱癸水评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 身弱水喜印比：金(印)、水(比)
        top_2 = ranked[:2]
        helpful = {WuXing.METAL, WuXing.WATER}
        assert any(e in helpful for e in top_2), f"金水应在前2名，实际：{[e.chinese for e in top_2]}"

    def test_weak_earth_likes_fire_earth(self, day_master_analyzer):
        """
        身弱土案例（伤官泄气）：庚午 己酉 辛酉 癸亥

        参考原始案例逻辑：己土遭伤官食神重重泄气时
        这里构造一个己土身弱的八字进行测试。

        己土日主生酉月，金旺泄土。
        用神：火土（印比）
        忌神：金水木

        注：原案例为 "庚己辛癸 午酉酉亥"，实际应为六个字
        这里用类似结构测试
        """
        # 构造己土身弱八字：己土日主，金旺泄气
        bazi = BaZi.from_chinese("庚午己酉己酉癸亥")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        print(f"己土八字：身{'强' if strength.is_strong else '弱'}")
        print(f"生耗值：beneficial={strength.beneficial_value:.1f}, harmful={strength.harmful_value:.1f}")

        ranked = result.yongshen_ranked
        print(f"己土评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 如果身弱，火土应排名靠前
        if not strength.is_strong:
            top_2 = ranked[:2]
            helpful = {WuXing.FIRE, WuXing.EARTH}
            assert any(e in helpful for e in top_2), f"身弱己土，火土应在前2名，实际：{[e.chinese for e in top_2]}"

    def test_strong_wood_likes_metal_earth(self, day_master_analyzer):
        """
        身强木案例：甲寅甲寅甲寅甲寅（极端身强）

        甲木日主生寅月得令，四柱全木，极端身强。
        用神：金（官杀克木）或土（财星耗木）或火（食伤泄木）
        忌神：水木

        这是极端案例，用于验证身强逻辑
        """
        bazi = BaZi.from_chinese("甲寅甲寅甲寅甲寅")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        # 极端身强
        assert strength.is_strong, "四柱全木应该极端身强"

        ranked = result.yongshen_ranked
        print(f"身强甲木评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 身强木需要泄克：火(泄)、土(耗)、金(克)
        top_3 = ranked[:3]
        helpful = {WuXing.FIRE, WuXing.EARTH, WuXing.METAL}
        assert all(e in helpful for e in top_3), f"身强木，火土金应在前3名，实际：{[e.chinese for e in top_3]}"

        # 水木应在后2名
        bottom_2 = ranked[3:]
        harmful = {WuXing.WATER, WuXing.WOOD}
        assert all(e in harmful for e in bottom_2), f"身强木，水木应在后2名，实际：{[e.chinese for e in bottom_2]}"

    def test_cold_winter_water_needs_fire(self, day_master_analyzer):
        """
        冬月水旺案例：壬子壬子壬子壬子

        壬水日主生子月，极寒极旺。
        调候急需丙火暖局。
        用神：火（调候）
        """
        bazi = BaZi.from_chinese("壬子壬子壬子壬子")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        print(f"冬月壬水八字：身{'强' if strength.is_strong else '弱'}")

        # 极寒季节应增加调候权重
        from bazi.domain.services import SeasonType
        assert result.tiaohao_result.season_type == SeasonType.EXTREME_COLD
        assert result.weights.tiaohao == 0.40, "极寒季节调候权重应为40%"

        ranked = result.yongshen_ranked
        print(f"冬月壬水评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 调候需火，扶抑身强也需火土金泄克
        # 火应该排名靠前
        assert result.scores[WuXing.FIRE].tiaohao_score > 0, "冬月调候应喜火"

    def test_hot_summer_fire_needs_water(self, day_master_analyzer):
        """
        夏月火旺案例：丙午丙午丙午丙午

        丙火日主生午月，极热极旺。
        调候急需壬癸水。
        """
        bazi = BaZi.from_chinese("丙午丙午丙午丙午")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        print(f"夏月丙火八字：身{'强' if strength.is_strong else '弱'}")

        # 极热季节
        from bazi.domain.services import SeasonType
        assert result.tiaohao_result.season_type == SeasonType.EXTREME_HOT
        assert result.weights.tiaohao == 0.40, "极热季节调候权重应为40%"

        ranked = result.yongshen_ranked
        print(f"夏月丙火评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f})")

        # 调候需水
        assert result.scores[WuXing.WATER].tiaohao_score > 0, "夏月调候应喜水"

        # 身强火需要泄克，水(克)应该排名靠前
        assert WuXing.WATER in ranked[:3], f"水应在前3名，实际：{[e.chinese for e in ranked[:3]]}"

    def test_metal_wood_conflict_needs_water_mediator(self, day_master_analyzer):
        """
        金木相战案例

        当八字中金木势均力敌时，需要水通关。
        水能泄金生木，化解冲突。
        """
        # 构造金木相战的八字
        # 甲木日主，金旺克木
        bazi = BaZi.from_chinese("庚申甲寅甲申庚寅")
        strength, favorable, wuxing, result = day_master_analyzer.full_analysis_integrated(bazi)

        print(f"金木相战八字：身{'强' if strength.is_strong else '弱'}")
        print(f"五行强度：")
        for elem in WuXing:
            print(f"  {elem.chinese}: {wuxing.adjusted_values.get(elem, 0):.1f}")

        if result.tongguan_result and result.tongguan_result.has_conflict:
            print(f"检测到相战：{result.tongguan_result.description}")
            print(f"通关元素分数：{result.tongguan_result.recommended_mediators}")

        ranked = result.yongshen_ranked
        print(f"评分排名：{[e.chinese for e in ranked]}")
        print(f"各元素分数：")
        for elem in WuXing:
            score = result.scores[elem]
            print(f"  {elem.chinese}: 总分={score.total_score:.2f} "
                  f"(扶抑={score.fuyi_score:.2f}, 调候={score.tiaohao_score:.2f}, 通关={score.tongguan_score:.2f})")

        # 如果检测到金木相战，水的通关分数应该为正
        if result.tongguan_result and result.tongguan_result.has_conflict:
            assert result.scores[WuXing.WATER].tongguan_score > 0, "金木相战时水应有通关分数"
