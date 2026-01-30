"""
Tests for ShenShaCalculator domain service.

Pure Python tests - NO Django dependencies.
"""
import pytest

from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.models.shensha import ShenShaType, ShenSha, ShenShaAnalysis
from bazi.domain.models.bazi import BaZi
from bazi.domain.services.shensha_calculator import ShenShaCalculator


class TestIsTianYiGuiRen:
    """Tests for is_tian_yi_gui_ren method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_jia_chou_is_tian_yi(self, calculator):
        """甲日 with 丑 branch is 天乙贵人."""
        result = calculator.is_tian_yi_gui_ren(HeavenlyStem.JIA, EarthlyBranch.CHOU)
        assert result is True

    def test_jia_wei_is_tian_yi(self, calculator):
        """甲日 with 未 branch is 天乙贵人."""
        result = calculator.is_tian_yi_gui_ren(HeavenlyStem.JIA, EarthlyBranch.WEI)
        assert result is True

    def test_jia_zi_is_not_tian_yi(self, calculator):
        """甲日 with 子 branch is not 天乙贵人."""
        result = calculator.is_tian_yi_gui_ren(HeavenlyStem.JIA, EarthlyBranch.ZI)
        assert result is False

    def test_yi_zi_is_tian_yi(self, calculator):
        """乙日 with 子 branch is 天乙贵人."""
        result = calculator.is_tian_yi_gui_ren(HeavenlyStem.YI, EarthlyBranch.ZI)
        assert result is True

    def test_bing_hai_is_tian_yi(self, calculator):
        """丙日 with 亥 branch is 天乙贵人."""
        result = calculator.is_tian_yi_gui_ren(HeavenlyStem.BING, EarthlyBranch.HAI)
        assert result is True


class TestIsTianDe:
    """Tests for is_tian_de method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_yin_month_ding_is_tian_de(self, calculator):
        """寅月 with 丁 stem is 天德."""
        result = calculator.is_tian_de(EarthlyBranch.YIN, HeavenlyStem.DING)
        assert result is True

    def test_yin_month_jia_is_not_tian_de(self, calculator):
        """寅月 with 甲 stem is not 天德."""
        result = calculator.is_tian_de(EarthlyBranch.YIN, HeavenlyStem.JIA)
        assert result is False

    def test_wei_month_jia_is_tian_de(self, calculator):
        """未月 with 甲 stem is 天德."""
        result = calculator.is_tian_de(EarthlyBranch.WEI, HeavenlyStem.JIA)
        assert result is True


class TestIsYueDe:
    """Tests for is_yue_de method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_yin_month_bing_is_yue_de(self, calculator):
        """寅月 with 丙 stem is 月德."""
        result = calculator.is_yue_de(EarthlyBranch.YIN, HeavenlyStem.BING)
        assert result is True

    def test_yin_month_jia_is_not_yue_de(self, calculator):
        """寅月 with 甲 stem is not 月德."""
        result = calculator.is_yue_de(EarthlyBranch.YIN, HeavenlyStem.JIA)
        assert result is False


class TestIsWenChang:
    """Tests for is_wen_chang method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_jia_si_is_wen_chang(self, calculator):
        """甲日 with 巳 branch is 文昌."""
        result = calculator.is_wen_chang(HeavenlyStem.JIA, EarthlyBranch.SI)
        assert result is True

    def test_jia_wu_is_not_wen_chang(self, calculator):
        """甲日 with 午 branch is not 文昌."""
        result = calculator.is_wen_chang(HeavenlyStem.JIA, EarthlyBranch.WU)
        assert result is False

    def test_yi_wu_is_wen_chang(self, calculator):
        """乙日 with 午 branch is 文昌."""
        result = calculator.is_wen_chang(HeavenlyStem.YI, EarthlyBranch.WU)
        assert result is True


class TestIsLuShen:
    """Tests for is_lu_shen method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_jia_yin_is_lu_shen(self, calculator):
        """甲日 with 寅 branch is 禄神 (甲禄在寅)."""
        result = calculator.is_lu_shen(HeavenlyStem.JIA, EarthlyBranch.YIN)
        assert result is True

    def test_jia_mao_is_not_lu_shen(self, calculator):
        """甲日 with 卯 branch is not 禄神."""
        result = calculator.is_lu_shen(HeavenlyStem.JIA, EarthlyBranch.MAO)
        assert result is False

    def test_yi_mao_is_lu_shen(self, calculator):
        """乙日 with 卯 branch is 禄神 (乙禄在卯)."""
        result = calculator.is_lu_shen(HeavenlyStem.YI, EarthlyBranch.MAO)
        assert result is True


class TestIsYangRen:
    """Tests for is_yang_ren method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_jia_mao_is_yang_ren(self, calculator):
        """甲日 with 卯 branch is 羊刃."""
        result = calculator.is_yang_ren(HeavenlyStem.JIA, EarthlyBranch.MAO)
        assert result is True

    def test_jia_yin_is_not_yang_ren(self, calculator):
        """甲日 with 寅 branch is not 羊刃."""
        result = calculator.is_yang_ren(HeavenlyStem.JIA, EarthlyBranch.YIN)
        assert result is False


class TestIsTaoHua:
    """Tests for is_tao_hua method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_you_is_tao_hua(self, calculator):
        """子年 with 酉 branch is 桃花."""
        result = calculator.is_tao_hua(EarthlyBranch.ZI, EarthlyBranch.YOU)
        assert result is True

    def test_zi_year_wu_is_not_tao_hua(self, calculator):
        """子年 with 午 branch is not 桃花."""
        result = calculator.is_tao_hua(EarthlyBranch.ZI, EarthlyBranch.WU)
        assert result is False

    def test_yin_year_mao_is_tao_hua(self, calculator):
        """寅年 with 卯 branch is 桃花."""
        result = calculator.is_tao_hua(EarthlyBranch.YIN, EarthlyBranch.MAO)
        assert result is True


class TestIsYiMa:
    """Tests for is_yi_ma method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_yin_is_yi_ma(self, calculator):
        """子年 with 寅 branch is 驿马."""
        result = calculator.is_yi_ma(EarthlyBranch.ZI, EarthlyBranch.YIN)
        assert result is True

    def test_zi_year_mao_is_not_yi_ma(self, calculator):
        """子年 with 卯 branch is not 驿马."""
        result = calculator.is_yi_ma(EarthlyBranch.ZI, EarthlyBranch.MAO)
        assert result is False


class TestIsHuaGai:
    """Tests for is_hua_gai method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_chen_is_hua_gai(self, calculator):
        """子年 with 辰 branch is 华盖."""
        result = calculator.is_hua_gai(EarthlyBranch.ZI, EarthlyBranch.CHEN)
        assert result is True

    def test_zi_year_xu_is_not_hua_gai(self, calculator):
        """子年 with 戌 branch is not 华盖."""
        result = calculator.is_hua_gai(EarthlyBranch.ZI, EarthlyBranch.XU)
        assert result is False


class TestIsJiangXing:
    """Tests for is_jiang_xing method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_zi_is_jiang_xing(self, calculator):
        """子年 with 子 branch is 将星."""
        result = calculator.is_jiang_xing(EarthlyBranch.ZI, EarthlyBranch.ZI)
        assert result is True

    def test_zi_year_wu_is_not_jiang_xing(self, calculator):
        """子年 with 午 branch is not 将星."""
        result = calculator.is_jiang_xing(EarthlyBranch.ZI, EarthlyBranch.WU)
        assert result is False


class TestCalculateForBaZi:
    """Tests for calculate_for_bazi method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_returns_shensha_analysis(self, calculator):
        """calculate_for_bazi returns ShenShaAnalysis."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.calculate_for_bazi(bazi)

        assert isinstance(result, ShenShaAnalysis)
        assert hasattr(result, 'shensha_list')

    def test_shensha_list_contains_shensha(self, calculator):
        """Result contains ShenSha objects."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.calculate_for_bazi(bazi)

        for ss in result.shensha_list:
            assert isinstance(ss, ShenSha)
            assert hasattr(ss, 'type')
            assert hasattr(ss, 'position')

    def test_finds_lu_shen_in_correct_position(self, calculator):
        """Finds 禄神 when day stem matches branch."""
        # 丙寅 has 丙 day stem, and 寅 is not 禄 for 丙 (丙禄在巳)
        # Let's use a chart with 丙巳 day pillar
        bazi = BaZi.from_chinese("甲子 乙丑 丙巳 丁卯")
        result = calculator.calculate_for_bazi(bazi)

        # Should find 禄神 in day branch
        lu_shen_positions = [
            ss for ss in result.shensha_list
            if ss.type == ShenShaType.LU_SHEN
        ]
        assert len(lu_shen_positions) > 0
        assert any("day_branch" in ss.position for ss in lu_shen_positions)

    def test_finds_tian_yi_gui_ren(self, calculator):
        """Finds 天乙贵人 correctly."""
        # 甲日 with 丑 or 未 is 天乙贵人
        # BaZi with 甲日 and 丑 branch somewhere
        bazi = BaZi.from_chinese("甲丑 乙丑 甲寅 丁卯")
        result = calculator.calculate_for_bazi(bazi)

        # Should find 天乙贵人
        tian_yi = [
            ss for ss in result.shensha_list
            if ss.type == ShenShaType.TIAN_YI_GUI_REN
        ]
        # Day master is 甲, and 丑 appears in year and month
        assert len(tian_yi) > 0


class TestGetShenshaSummary:
    """Tests for get_shensha_summary method."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_returns_dict(self, calculator):
        """get_shensha_summary returns a dictionary."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.get_shensha_summary(bazi)

        assert isinstance(result, dict)

    def test_values_are_lists(self, calculator):
        """Dictionary values are lists of strings."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.get_shensha_summary(bazi)

        for value in result.values():
            assert isinstance(value, list)
            for item in value:
                assert isinstance(item, str)

    def test_no_empty_categories(self, calculator):
        """Summary excludes categories with no ShenSha."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.get_shensha_summary(bazi)

        for key, value in result.items():
            assert len(value) > 0, f"Category {key} should not be empty"

    def test_no_duplicates_in_category(self, calculator):
        """Each ShenSha appears only once per category."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = calculator.get_shensha_summary(bazi)

        for key, value in result.items():
            assert len(value) == len(set(value)), f"Category {key} has duplicates"


class TestShenShaTypeProperties:
    """Tests for ShenShaType enum properties."""

    def test_chinese_property(self):
        """ShenShaType has chinese property."""
        assert ShenShaType.TIAN_YI_GUI_REN.chinese == "天乙贵人"
        assert ShenShaType.TAO_HUA.chinese == "桃花"
        assert ShenShaType.YANG_REN.chinese == "羊刃"

    def test_is_beneficial_property(self):
        """ShenShaType has is_beneficial property."""
        # Beneficial stars
        assert ShenShaType.TIAN_YI_GUI_REN.is_beneficial is True
        assert ShenShaType.WEN_CHANG.is_beneficial is True
        assert ShenShaType.LU_SHEN.is_beneficial is True
        # Challenging stars
        assert ShenShaType.YANG_REN.is_beneficial is False

    def test_category_property(self):
        """ShenShaType has category property."""
        assert ShenShaType.TIAN_YI_GUI_REN.category == "贵人"
        assert ShenShaType.TAO_HUA.category == "桃花"
        assert ShenShaType.YI_MA.category == "驿马"


class TestShenShaModel:
    """Tests for ShenSha dataclass."""

    def test_create_shensha(self):
        """Can create ShenSha instance."""
        ss = ShenSha(
            type=ShenShaType.TIAN_YI_GUI_REN,
            position="year_branch",
            triggered_by="甲",
        )
        assert ss.type == ShenShaType.TIAN_YI_GUI_REN
        assert ss.position == "year_branch"
        assert ss.triggered_by == "甲"

    def test_shensha_chinese_property(self):
        """ShenSha has chinese property via type."""
        ss = ShenSha(
            type=ShenShaType.TAO_HUA,
            position="month_branch",
            triggered_by="子",
        )
        assert ss.chinese == "桃花"


class TestShenShaAnalysisModel:
    """Tests for ShenShaAnalysis dataclass."""

    def test_create_analysis(self):
        """Can create ShenShaAnalysis instance."""
        shensha_list = [
            ShenSha(
                type=ShenShaType.TIAN_YI_GUI_REN,
                position="year_branch",
                triggered_by="甲",
            ),
            ShenSha(
                type=ShenShaType.WEN_CHANG,
                position="hour_branch",
                triggered_by="甲",
            ),
        ]
        analysis = ShenShaAnalysis(shensha_list=shensha_list)

        assert len(analysis.shensha_list) == 2

    def test_analysis_count_by_type_method(self):
        """ShenShaAnalysis has count_by_type method."""
        shensha_list = [
            ShenSha(
                type=ShenShaType.TIAN_YI_GUI_REN,
                position="year_branch",
                triggered_by="甲",
            ),
            ShenSha(
                type=ShenShaType.TIAN_YI_GUI_REN,
                position="month_branch",
                triggered_by="甲",
            ),
            ShenSha(
                type=ShenShaType.WEN_CHANG,
                position="hour_branch",
                triggered_by="甲",
            ),
        ]
        analysis = ShenShaAnalysis(shensha_list=shensha_list)

        counts = analysis.count_by_type()
        assert counts[ShenShaType.TIAN_YI_GUI_REN] == 2
        assert counts[ShenShaType.WEN_CHANG] == 1

    def test_analysis_has_method(self):
        """ShenShaAnalysis has 'has' method."""
        shensha_list = [
            ShenSha(
                type=ShenShaType.TIAN_YI_GUI_REN,
                position="year_branch",
                triggered_by="甲",
            ),
        ]
        analysis = ShenShaAnalysis(shensha_list=shensha_list)

        assert analysis.has(ShenShaType.TIAN_YI_GUI_REN) is True
        assert analysis.has(ShenShaType.TAO_HUA) is False

    def test_analysis_beneficial_property(self):
        """ShenShaAnalysis has beneficial property."""
        shensha_list = [
            ShenSha(
                type=ShenShaType.TIAN_YI_GUI_REN,  # beneficial
                position="year_branch",
                triggered_by="甲",
            ),
            ShenSha(
                type=ShenShaType.YANG_REN,  # challenging
                position="day_branch",
                triggered_by="甲",
            ),
        ]
        analysis = ShenShaAnalysis(shensha_list=shensha_list)

        beneficial = analysis.beneficial
        assert len(beneficial) == 1
        assert beneficial[0].type == ShenShaType.TIAN_YI_GUI_REN
