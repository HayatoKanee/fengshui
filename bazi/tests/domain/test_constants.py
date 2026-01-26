"""
Tests for domain constants (clashes, harmony, phases).

These tests verify the correctness of fundamental lookup tables
used in BaZi calculations.
"""
import pytest

from bazi.domain.constants.clashes import (
    GAN_XIANG_CHONG,
    ZHI_XIANG_CHONG,
    WU_BU_YU_SHI,
    is_gan_clash,
    is_zhi_clash,
    is_clash,
    is_wu_bu_yu_shi,
)
from bazi.domain.constants.harmony import (
    LIU_HE,
    WU_HE,
    HIDDEN_GAN_RATIOS,
    is_harmony,
)
from bazi.domain.constants.phases import (
    ZHI_SEASONS,
    SEASON_PHASES,
    WANG_XIANG_VALUE,
    get_season,
    get_phase_for_element,
    get_phase_value,
)


class TestGanXiangChong:
    """Tests for 天干相冲 (Heavenly Stem Clashes)."""

    def test_gan_clash_count(self):
        """Should have 8 pairs (4 clashes, bidirectional)."""
        assert len(GAN_XIANG_CHONG) == 8

    def test_jia_geng_clash(self):
        """甲庚相冲."""
        assert ('甲', '庚') in GAN_XIANG_CHONG
        assert ('庚', '甲') in GAN_XIANG_CHONG

    def test_yi_xin_clash(self):
        """乙辛相冲."""
        assert ('乙', '辛') in GAN_XIANG_CHONG
        assert ('辛', '乙') in GAN_XIANG_CHONG

    def test_bing_ren_clash(self):
        """壬丙相冲."""
        assert ('壬', '丙') in GAN_XIANG_CHONG
        assert ('丙', '壬') in GAN_XIANG_CHONG

    def test_ding_gui_clash(self):
        """癸丁相冲."""
        assert ('癸', '丁') in GAN_XIANG_CHONG
        assert ('丁', '癸') in GAN_XIANG_CHONG

    def test_is_gan_clash(self):
        """is_gan_clash should correctly identify clashes."""
        assert is_gan_clash('甲', '庚') is True
        assert is_gan_clash('甲', '乙') is False
        assert is_gan_clash('戊', '己') is False  # 戊己 no clash

    def test_wu_ji_no_clash(self):
        """戊己 should NOT clash (they are both earth)."""
        assert ('戊', '己') not in GAN_XIANG_CHONG
        assert ('己', '戊') not in GAN_XIANG_CHONG


class TestZhiXiangChong:
    """Tests for 地支相冲 (Earthly Branch Clashes)."""

    def test_zhi_clash_count(self):
        """Should have 12 pairs (6 clashes, bidirectional)."""
        assert len(ZHI_XIANG_CHONG) == 12

    def test_zi_wu_clash(self):
        """子午相冲."""
        assert ('子', '午') in ZHI_XIANG_CHONG
        assert ('午', '子') in ZHI_XIANG_CHONG

    def test_chou_wei_clash(self):
        """丑未相冲."""
        assert ('丑', '未') in ZHI_XIANG_CHONG
        assert ('未', '丑') in ZHI_XIANG_CHONG

    def test_yin_shen_clash(self):
        """寅申相冲."""
        assert ('寅', '申') in ZHI_XIANG_CHONG
        assert ('申', '寅') in ZHI_XIANG_CHONG

    def test_mao_you_clash(self):
        """卯酉相冲."""
        assert ('卯', '酉') in ZHI_XIANG_CHONG
        assert ('酉', '卯') in ZHI_XIANG_CHONG

    def test_chen_xu_clash(self):
        """辰戌相冲."""
        assert ('辰', '戌') in ZHI_XIANG_CHONG
        assert ('戌', '辰') in ZHI_XIANG_CHONG

    def test_si_hai_clash(self):
        """巳亥相冲."""
        assert ('巳', '亥') in ZHI_XIANG_CHONG
        assert ('亥', '巳') in ZHI_XIANG_CHONG

    def test_is_zhi_clash(self):
        """is_zhi_clash should correctly identify clashes."""
        assert is_zhi_clash('子', '午') is True
        assert is_zhi_clash('子', '丑') is False  # 六合


class TestIsClash:
    """Tests for the general is_clash function."""

    def test_is_clash_gan(self):
        """is_clash should detect stem clashes."""
        assert is_clash('甲', '庚') is True

    def test_is_clash_zhi(self):
        """is_clash should detect branch clashes."""
        assert is_clash('子', '午') is True

    def test_is_clash_false(self):
        """is_clash should return False for non-clashing pairs."""
        assert is_clash('甲', '乙') is False
        assert is_clash('子', '丑') is False


class TestWuBuYuShi:
    """Tests for 五不遇时 (Five Misfortune Hours)."""

    def test_wu_bu_yu_shi_count(self):
        """Should have 12 unfortunate day-hour combinations."""
        assert len(WU_BU_YU_SHI) == 12

    def test_is_wu_bu_yu_shi(self):
        """Test specific 五不遇时 combinations."""
        assert is_wu_bu_yu_shi('甲', '午') is True
        assert is_wu_bu_yu_shi('乙', '巳') is True
        assert is_wu_bu_yu_shi('甲', '子') is False


class TestLiuHe:
    """Tests for 六合 (Six Harmonies - Branch)."""

    def test_liu_he_count(self):
        """Should have 12 pairs (6 harmonies, bidirectional)."""
        assert len(LIU_HE) == 12

    def test_zi_chou_he(self):
        """子丑合."""
        assert ('子', '丑') in LIU_HE
        assert ('丑', '子') in LIU_HE

    def test_yin_hai_he(self):
        """寅亥合."""
        assert ('寅', '亥') in LIU_HE
        assert ('亥', '寅') in LIU_HE

    def test_mao_xu_he(self):
        """卯戌合."""
        assert ('卯', '戌') in LIU_HE
        assert ('戌', '卯') in LIU_HE

    def test_chen_you_he(self):
        """辰酉合."""
        assert ('辰', '酉') in LIU_HE
        assert ('酉', '辰') in LIU_HE

    def test_si_shen_he(self):
        """巳申合."""
        assert ('巳', '申') in LIU_HE
        assert ('申', '巳') in LIU_HE

    def test_wu_wei_he(self):
        """午未合."""
        assert ('午', '未') in LIU_HE
        assert ('未', '午') in LIU_HE


class TestWuHe:
    """Tests for 五合 (Five Harmonies - Stem)."""

    def test_wu_he_count(self):
        """Should have 10 pairs (5 harmonies, bidirectional)."""
        assert len(WU_HE) == 10

    def test_jia_ji_he(self):
        """甲己合 (化土)."""
        assert ('甲', '己') in WU_HE
        assert ('己', '甲') in WU_HE

    def test_yi_geng_he(self):
        """乙庚合 (化金)."""
        assert ('乙', '庚') in WU_HE
        assert ('庚', '乙') in WU_HE

    def test_bing_xin_he(self):
        """丙辛合 (化水)."""
        assert ('丙', '辛') in WU_HE
        assert ('辛', '丙') in WU_HE

    def test_ding_ren_he(self):
        """丁壬合 (化木)."""
        assert ('丁', '壬') in WU_HE
        assert ('壬', '丁') in WU_HE

    def test_wu_gui_he(self):
        """戊癸合 (化火)."""
        assert ('戊', '癸') in WU_HE
        assert ('癸', '戊') in WU_HE


class TestIsHarmony:
    """Tests for the general is_harmony function."""

    def test_is_harmony_liu_he(self):
        """is_harmony should detect branch harmonies."""
        assert is_harmony('子', '丑') is True

    def test_is_harmony_wu_he(self):
        """is_harmony should detect stem harmonies."""
        assert is_harmony('甲', '己') is True

    def test_is_harmony_false(self):
        """is_harmony should return False for non-harmony pairs."""
        assert is_harmony('子', '午') is False  # 冲
        assert is_harmony('甲', '庚') is False  # 冲


class TestHiddenGanRatios:
    """Tests for 地支藏干 (Hidden Stems in Branches)."""

    def test_hidden_gan_count(self):
        """Should have all 12 branches."""
        assert len(HIDDEN_GAN_RATIOS) == 12

    def test_zi_hidden_gan(self):
        """子 contains only 癸."""
        assert HIDDEN_GAN_RATIOS['子'] == {'癸': 1.0}

    def test_mao_hidden_gan(self):
        """卯 contains only 乙."""
        assert HIDDEN_GAN_RATIOS['卯'] == {'乙': 1.0}

    def test_you_hidden_gan(self):
        """酉 contains only 辛."""
        assert HIDDEN_GAN_RATIOS['酉'] == {'辛': 1.0}

    def test_chou_hidden_gan(self):
        """丑 contains 己、癸、辛."""
        assert HIDDEN_GAN_RATIOS['丑'] == {'己': 0.5, '癸': 0.3, '辛': 0.2}

    def test_yin_hidden_gan(self):
        """寅 contains 甲、丙、戊."""
        assert HIDDEN_GAN_RATIOS['寅'] == {'甲': 0.6, '丙': 0.3, '戊': 0.1}

    def test_ratios_sum_to_one(self):
        """All branch ratios should sum to 1.0."""
        for branch, ratios in HIDDEN_GAN_RATIOS.items():
            total = sum(ratios.values())
            assert abs(total - 1.0) < 0.01, f"{branch} ratios sum to {total}, not 1.0"


class TestZhiSeasons:
    """Tests for 地支季节 (Branch to Season mapping)."""

    def test_spring_branches(self):
        """寅卯辰 belong to spring."""
        assert ZHI_SEASONS['寅'] == '春'
        assert ZHI_SEASONS['卯'] == '春'
        assert ZHI_SEASONS['辰'] == '春'

    def test_summer_branches(self):
        """巳午未 belong to summer."""
        assert ZHI_SEASONS['巳'] == '夏'
        assert ZHI_SEASONS['午'] == '夏'
        assert ZHI_SEASONS['未'] == '夏'

    def test_autumn_branches(self):
        """申酉戌 belong to autumn."""
        assert ZHI_SEASONS['申'] == '秋'
        assert ZHI_SEASONS['酉'] == '秋'
        assert ZHI_SEASONS['戌'] == '秋'

    def test_winter_branches(self):
        """亥子丑 belong to winter."""
        assert ZHI_SEASONS['亥'] == '冬'
        assert ZHI_SEASONS['子'] == '冬'
        assert ZHI_SEASONS['丑'] == '冬'

    def test_get_season(self):
        """get_season should return correct season."""
        assert get_season('寅') == '春'
        assert get_season('午') == '夏'
        assert get_season('酉') == '秋'
        assert get_season('子') == '冬'


class TestSeasonPhases:
    """Tests for 旺相休囚死 (Seasonal Element Strength Phases)."""

    def test_spring_phases(self):
        """Spring (春) phases: Wood旺, Fire相, Water休, Metal囚, Earth死."""
        assert SEASON_PHASES['春']['木'] == '旺'
        assert SEASON_PHASES['春']['火'] == '相'
        assert SEASON_PHASES['春']['水'] == '休'
        assert SEASON_PHASES['春']['金'] == '囚'
        assert SEASON_PHASES['春']['土'] == '死'

    def test_summer_phases(self):
        """Summer (夏) phases: Fire旺, Earth相, Wood休, Water囚, Metal死."""
        assert SEASON_PHASES['夏']['火'] == '旺'
        assert SEASON_PHASES['夏']['土'] == '相'
        assert SEASON_PHASES['夏']['木'] == '休'
        assert SEASON_PHASES['夏']['水'] == '囚'
        assert SEASON_PHASES['夏']['金'] == '死'

    def test_autumn_phases(self):
        """Autumn (秋) phases: Metal旺, Water相, Earth休, Fire囚, Wood死."""
        assert SEASON_PHASES['秋']['金'] == '旺'
        assert SEASON_PHASES['秋']['水'] == '相'
        assert SEASON_PHASES['秋']['土'] == '休'
        assert SEASON_PHASES['秋']['火'] == '囚'
        assert SEASON_PHASES['秋']['木'] == '死'

    def test_winter_phases(self):
        """Winter (冬) phases: Water旺, Wood相, Metal休, Earth囚, Fire死."""
        assert SEASON_PHASES['冬']['水'] == '旺'
        assert SEASON_PHASES['冬']['木'] == '相'
        assert SEASON_PHASES['冬']['金'] == '休'
        assert SEASON_PHASES['冬']['土'] == '囚'
        assert SEASON_PHASES['冬']['火'] == '死'

    def test_get_phase_for_element(self):
        """get_phase_for_element should return correct phase."""
        assert get_phase_for_element('春', '木') == '旺'
        assert get_phase_for_element('夏', '火') == '旺'
        assert get_phase_for_element('秋', '金') == '旺'
        assert get_phase_for_element('冬', '水') == '旺'


class TestWangXiangValue:
    """Tests for 旺相休囚死 value mapping."""

    def test_wang_value(self):
        """旺 should have highest value."""
        assert WANG_XIANG_VALUE['旺'] == 1.2

    def test_xiang_value(self):
        """相 should have second highest value."""
        assert WANG_XIANG_VALUE['相'] == 1.2

    def test_xiu_value(self):
        """休 should have base value."""
        assert WANG_XIANG_VALUE['休'] == 1.0

    def test_qiu_value(self):
        """囚 should have reduced value."""
        assert WANG_XIANG_VALUE['囚'] == 0.8

    def test_si_value(self):
        """死 should have lowest value."""
        assert WANG_XIANG_VALUE['死'] == 0.8

    def test_get_phase_value(self):
        """get_phase_value should return multiplier for a phase."""
        assert get_phase_value('旺') == 1.2
        assert get_phase_value('休') == 1.0
        assert get_phase_value('死') == 0.8
