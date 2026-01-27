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
        """未月 with 甲 stem is 天德 (古诀：未月甲)."""
        result = calculator.is_tian_de(EarthlyBranch.WEI, HeavenlyStem.JIA)
        assert result is True


class TestIsTianDeHe:
    """Tests for is_tian_de_he method (天德合)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_yin_month_ren_is_tian_de_he(self, calculator):
        """寅月 with 壬 stem is 天德合 (丁壬合)."""
        result = calculator.is_tian_de_he(EarthlyBranch.YIN, HeavenlyStem.REN)
        assert result is True

    def test_chen_month_ding_is_tian_de_he(self, calculator):
        """辰月 with 丁 stem is 天德合 (壬丁合)."""
        result = calculator.is_tian_de_he(EarthlyBranch.CHEN, HeavenlyStem.DING)
        assert result is True

    def test_wei_month_ji_is_tian_de_he(self, calculator):
        """未月 with 己 stem is 天德合 (甲己合)."""
        result = calculator.is_tian_de_he(EarthlyBranch.WEI, HeavenlyStem.JI)
        assert result is True

    def test_yin_month_ding_is_not_tian_de_he(self, calculator):
        """寅月 with 丁 stem is not 天德合 (丁是天德，不是天德合)."""
        result = calculator.is_tian_de_he(EarthlyBranch.YIN, HeavenlyStem.DING)
        assert result is False

    def test_mao_month_si_is_tian_de_he(self, calculator):
        """卯月 with 巳 branch is 天德合 (申的六合是巳)."""
        result = calculator.is_tian_de_he(EarthlyBranch.MAO, EarthlyBranch.SI)
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

    def test_hai_month_jia_is_yue_de(self, calculator):
        """亥月 with 甲 stem is 月德 (亥卯未月见甲)."""
        result = calculator.is_yue_de(EarthlyBranch.HAI, HeavenlyStem.JIA)
        assert result is True

    def test_si_month_geng_is_yue_de(self, calculator):
        """巳月 with 庚 stem is 月德 (巳酉丑月见庚)."""
        result = calculator.is_yue_de(EarthlyBranch.SI, HeavenlyStem.GENG)
        assert result is True


class TestIsYueDeHe:
    """Tests for is_yue_de_he method (月德合)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_yin_month_xin_is_yue_de_he(self, calculator):
        """寅月 with 辛 stem is 月德合 (丙辛合)."""
        result = calculator.is_yue_de_he(EarthlyBranch.YIN, HeavenlyStem.XIN)
        assert result is True

    def test_hai_month_ji_is_yue_de_he(self, calculator):
        """亥月 with 己 stem is 月德合 (甲己合)."""
        result = calculator.is_yue_de_he(EarthlyBranch.HAI, HeavenlyStem.JI)
        assert result is True

    def test_zi_month_ding_is_yue_de_he(self, calculator):
        """子月 with 丁 stem is 月德合 (壬丁合)."""
        result = calculator.is_yue_de_he(EarthlyBranch.ZI, HeavenlyStem.DING)
        assert result is True

    def test_chou_month_yi_is_yue_de_he(self, calculator):
        """丑月 with 乙 stem is 月德合 (庚乙合)."""
        result = calculator.is_yue_de_he(EarthlyBranch.CHOU, HeavenlyStem.YI)
        assert result is True

    def test_yin_month_bing_is_not_yue_de_he(self, calculator):
        """寅月 with 丙 stem is not 月德合 (丙是月德，不是月德合)."""
        result = calculator.is_yue_de_he(EarthlyBranch.YIN, HeavenlyStem.BING)
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


class TestIsHongYanSha:
    """Tests for is_hong_yan_sha method (红艳煞)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_jia_wu_is_hong_yan(self, calculator):
        """甲日 with 午 branch is 红艳煞."""
        result = calculator.is_hong_yan_sha(HeavenlyStem.JIA, EarthlyBranch.WU)
        assert result is True

    def test_yi_wu_is_hong_yan(self, calculator):
        """乙日 with 午 branch is 红艳煞."""
        result = calculator.is_hong_yan_sha(HeavenlyStem.YI, EarthlyBranch.WU)
        assert result is True

    def test_bing_yin_is_hong_yan(self, calculator):
        """丙日 with 寅 branch is 红艳煞."""
        result = calculator.is_hong_yan_sha(HeavenlyStem.BING, EarthlyBranch.YIN)
        assert result is True

    def test_wu_chen_is_hong_yan(self, calculator):
        """戊日 with 辰 branch is 红艳煞."""
        result = calculator.is_hong_yan_sha(HeavenlyStem.WU, EarthlyBranch.CHEN)
        assert result is True

    def test_jia_zi_is_not_hong_yan(self, calculator):
        """甲日 with 子 branch is not 红艳煞."""
        result = calculator.is_hong_yan_sha(HeavenlyStem.JIA, EarthlyBranch.ZI)
        assert result is False


class TestIsJieSha:
    """Tests for is_jie_sha method (劫煞)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_si_is_jie_sha(self, calculator):
        """子年 with 巳 branch is 劫煞 (申子辰见巳)."""
        result = calculator.is_jie_sha(EarthlyBranch.ZI, EarthlyBranch.SI)
        assert result is True

    def test_yin_year_hai_is_jie_sha(self, calculator):
        """寅年 with 亥 branch is 劫煞 (寅午戌见亥)."""
        result = calculator.is_jie_sha(EarthlyBranch.YIN, EarthlyBranch.HAI)
        assert result is True

    def test_mao_year_shen_is_jie_sha(self, calculator):
        """卯年 with 申 branch is 劫煞 (亥卯未见申)."""
        result = calculator.is_jie_sha(EarthlyBranch.MAO, EarthlyBranch.SHEN)
        assert result is True

    def test_you_year_yin_is_jie_sha(self, calculator):
        """酉年 with 寅 branch is 劫煞 (巳酉丑见寅)."""
        result = calculator.is_jie_sha(EarthlyBranch.YOU, EarthlyBranch.YIN)
        assert result is True

    def test_zi_year_yin_is_not_jie_sha(self, calculator):
        """子年 with 寅 branch is not 劫煞 (寅是驿马)."""
        result = calculator.is_jie_sha(EarthlyBranch.ZI, EarthlyBranch.YIN)
        assert result is False


class TestIsWangShen:
    """Tests for is_wang_shen method (亡神)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_hai_is_wang_shen(self, calculator):
        """子年 with 亥 branch is 亡神 (申子辰见亥)."""
        result = calculator.is_wang_shen(EarthlyBranch.ZI, EarthlyBranch.HAI)
        assert result is True

    def test_yin_year_si_is_wang_shen(self, calculator):
        """寅年 with 巳 branch is 亡神 (寅午戌见巳)."""
        result = calculator.is_wang_shen(EarthlyBranch.YIN, EarthlyBranch.SI)
        assert result is True

    def test_mao_year_yin_is_wang_shen(self, calculator):
        """卯年 with 寅 branch is 亡神 (亥卯未见寅)."""
        result = calculator.is_wang_shen(EarthlyBranch.MAO, EarthlyBranch.YIN)
        assert result is True

    def test_you_year_shen_is_wang_shen(self, calculator):
        """酉年 with 申 branch is 亡神 (巳酉丑见申)."""
        result = calculator.is_wang_shen(EarthlyBranch.YOU, EarthlyBranch.SHEN)
        assert result is True

    def test_zi_year_si_is_not_wang_shen(self, calculator):
        """子年 with 巳 branch is not 亡神 (巳是劫煞)."""
        result = calculator.is_wang_shen(EarthlyBranch.ZI, EarthlyBranch.SI)
        assert result is False


class TestIsGuChen:
    """Tests for is_gu_chen method (孤辰)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_yin_is_gu_chen(self, calculator):
        """子年 with 寅 branch is 孤辰 (亥子丑见寅)."""
        result = calculator.is_gu_chen(EarthlyBranch.ZI, EarthlyBranch.YIN)
        assert result is True

    def test_mao_year_si_is_gu_chen(self, calculator):
        """卯年 with 巳 branch is 孤辰 (寅卯辰见巳)."""
        result = calculator.is_gu_chen(EarthlyBranch.MAO, EarthlyBranch.SI)
        assert result is True

    def test_wu_year_shen_is_gu_chen(self, calculator):
        """午年 with 申 branch is 孤辰 (巳午未见申)."""
        result = calculator.is_gu_chen(EarthlyBranch.WU, EarthlyBranch.SHEN)
        assert result is True

    def test_you_year_hai_is_gu_chen(self, calculator):
        """酉年 with 亥 branch is 孤辰 (申酉戌见亥)."""
        result = calculator.is_gu_chen(EarthlyBranch.YOU, EarthlyBranch.HAI)
        assert result is True

    def test_zi_year_xu_is_not_gu_chen(self, calculator):
        """子年 with 戌 branch is not 孤辰 (戌是寡宿)."""
        result = calculator.is_gu_chen(EarthlyBranch.ZI, EarthlyBranch.XU)
        assert result is False


class TestIsGuaSu:
    """Tests for is_gua_su method (寡宿)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_zi_year_xu_is_gua_su(self, calculator):
        """子年 with 戌 branch is 寡宿 (亥子丑见戌)."""
        result = calculator.is_gua_su(EarthlyBranch.ZI, EarthlyBranch.XU)
        assert result is True

    def test_mao_year_chou_is_gua_su(self, calculator):
        """卯年 with 丑 branch is 寡宿 (寅卯辰见丑)."""
        result = calculator.is_gua_su(EarthlyBranch.MAO, EarthlyBranch.CHOU)
        assert result is True

    def test_wu_year_chen_is_gua_su(self, calculator):
        """午年 with 辰 branch is 寡宿 (巳午未见辰)."""
        result = calculator.is_gua_su(EarthlyBranch.WU, EarthlyBranch.CHEN)
        assert result is True

    def test_you_year_wei_is_gua_su(self, calculator):
        """酉年 with 未 branch is 寡宿 (申酉戌见未)."""
        result = calculator.is_gua_su(EarthlyBranch.YOU, EarthlyBranch.WEI)
        assert result is True

    def test_zi_year_yin_is_not_gua_su(self, calculator):
        """子年 with 寅 branch is not 寡宿 (寅是孤辰)."""
        result = calculator.is_gua_su(EarthlyBranch.ZI, EarthlyBranch.YIN)
        assert result is False


class TestIsKongWang:
    """Tests for is_kong_wang method (空亡)."""

    @pytest.fixture
    def calculator(self):
        return ShenShaCalculator()

    def test_jia_zi_day_xu_is_kong_wang(self, calculator):
        """甲子日 with 戌 branch is 空亡 (甲子旬空戌亥)."""
        result = calculator.is_kong_wang("甲子", "戌")
        assert result is True

    def test_jia_zi_day_hai_is_kong_wang(self, calculator):
        """甲子日 with 亥 branch is 空亡 (甲子旬空戌亥)."""
        result = calculator.is_kong_wang("甲子", "亥")
        assert result is True

    def test_jia_xu_day_shen_is_kong_wang(self, calculator):
        """甲戌日 with 申 branch is 空亡 (甲戌旬空申酉)."""
        result = calculator.is_kong_wang("甲戌", "申")
        assert result is True

    def test_jia_shen_day_wu_is_kong_wang(self, calculator):
        """甲申日 with 午 branch is 空亡 (甲申旬空午未)."""
        result = calculator.is_kong_wang("甲申", "午")
        assert result is True

    def test_jia_zi_day_zi_is_not_kong_wang(self, calculator):
        """甲子日 with 子 branch is not 空亡."""
        result = calculator.is_kong_wang("甲子", "子")
        assert result is False

    def test_wu_chen_day_yin_is_kong_wang(self, calculator):
        """戊辰日 with 寅 branch is 空亡 (甲子旬空戌亥 - 戊辰在甲子旬，应该不是空寅卯)."""
        # 戊辰在甲子旬，空戌亥，不是空寅卯
        result = calculator.is_kong_wang("戊辰", "寅")
        assert result is False

    def test_jia_chen_day_yin_is_kong_wang(self, calculator):
        """甲辰日 with 寅 branch is 空亡 (甲辰旬空寅卯)."""
        result = calculator.is_kong_wang("甲辰", "寅")
        assert result is True


class TestSanQiRule:
    """Tests for SanQi (三奇) rule.

    三奇规则（参考《八字金书》《渊海子平》）：
    - 天上三奇：乙丙丁
    - 地上三奇：甲戊庚
    - 人中三奇：辛壬癸

    必须在连续三柱（年月日 或 月日时）中顺序出现。
    """

    def test_tian_shang_san_qi_year_month_day(self):
        """天上三奇：年月日为乙丙丁."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 乙年丙月丁日 - 天上三奇（年月日）
        bazi = BaZi.from_chinese("乙丑 丙寅 丁卯 戊辰")
        result = rule.find_matches(bazi)
        assert len(result) == 1
        assert result[0].triggered_by == "乙丙丁"

    def test_tian_shang_san_qi_month_day_hour(self):
        """天上三奇：月日时为乙丙丁."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 月日时为乙丙丁 - 天上三奇（月日时）
        bazi = BaZi.from_chinese("庚子 乙丑 丙寅 丁卯")
        result = rule.find_matches(bazi)
        assert len(result) == 1
        assert result[0].triggered_by == "乙丙丁"

    def test_di_shang_san_qi(self):
        """地上三奇：甲戊庚 顺序出现."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 甲年戊月庚日 - 地上三奇
        bazi = BaZi.from_chinese("甲子 戊寅 庚辰 壬午")
        result = rule.find_matches(bazi)
        assert len(result) == 1
        assert result[0].triggered_by == "甲戊庚"

    def test_ren_zhong_san_qi(self):
        """人中三奇：辛壬癸 顺序出现."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 辛年壬月癸日 - 人中三奇
        bazi = BaZi.from_chinese("辛丑 壬寅 癸卯 甲辰")
        result = rule.find_matches(bazi)
        assert len(result) == 1
        assert result[0].triggered_by == "辛壬癸"

    def test_no_san_qi_wrong_order(self):
        """顺序错误不是三奇."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 丁丙乙 - 逆序不是三奇
        bazi = BaZi.from_chinese("丁丑 丙寅 乙卯 甲辰")
        result = rule.find_matches(bazi)
        assert len(result) == 0

    def test_no_san_qi_scattered(self):
        """散落的三奇模式无效（必须连续三柱）."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 乙X丙丁 - 乙在年，X在月，丙在日，丁在时
        # 不符合"年月日"或"月日时"的连续三柱要求
        bazi = BaZi.from_chinese("乙丑 甲寅 丙卯 丁辰")
        result = rule.find_matches(bazi)
        # 年月日=乙甲丙，月日时=甲丙丁，都不匹配
        assert len(result) == 0

    def test_san_qi_requires_consecutive_pillars(self):
        """三奇必须在连续三柱中."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 甲乙丙丁 - 月日时=乙丙丁，是天上三奇
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        result = rule.find_matches(bazi)
        assert len(result) == 1
        assert result[0].triggered_by == "乙丙丁"

    def test_no_san_qi_random_stems(self):
        """随机天干无三奇."""
        from bazi.domain.models.shensha_rule import SanQiRule
        rule = SanQiRule()

        # 甲乙丙戊 - 年月日=甲乙丙，月日时=乙丙戊，都不匹配任何三奇
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 戊卯")
        result = rule.find_matches(bazi)
        assert len(result) == 0


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
