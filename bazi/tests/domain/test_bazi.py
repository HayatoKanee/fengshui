"""
Tests for BaZi and BirthData domain models.

Pure Python tests - NO Django dependencies.
"""
from datetime import datetime

import pytest

from bazi.domain.models.elements import WuXing
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch
from bazi.domain.models.pillar import Pillar
from bazi.domain.models.bazi import BaZi, BirthData


class TestBirthDataCreation:
    """Tests for BirthData creation and validation."""

    def test_create_basic(self):
        """Create BirthData with basic parameters."""
        birth = BirthData(year=1990, month=6, day=15, hour=12)
        assert birth.year == 1990
        assert birth.month == 6
        assert birth.day == 15
        assert birth.hour == 12
        assert birth.minute == 0  # default
        assert birth.is_male is True  # default
        assert birth.name is None  # default

    def test_create_with_all_params(self):
        """Create BirthData with all parameters."""
        birth = BirthData(
            year=1985,
            month=3,
            day=20,
            hour=14,
            minute=30,
            is_male=False,
            name="Test Person"
        )
        assert birth.is_male is False
        assert birth.name == "Test Person"
        assert birth.minute == 30

    def test_from_datetime(self):
        """Create BirthData from datetime object."""
        dt = datetime(1990, 6, 15, 12, 30)
        birth = BirthData.from_datetime(dt, is_male=False, name="Test")
        assert birth.year == 1990
        assert birth.month == 6
        assert birth.day == 15
        assert birth.hour == 12
        assert birth.minute == 30
        assert birth.is_male is False
        assert birth.name == "Test"

    def test_invalid_month_too_low(self):
        """Month below 1 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date"):
            BirthData(year=1990, month=0, day=15, hour=12)

    def test_invalid_month_too_high(self):
        """Month above 12 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date"):
            BirthData(year=1990, month=13, day=15, hour=12)

    def test_invalid_day_too_low(self):
        """Day below 1 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date"):
            BirthData(year=1990, month=6, day=0, hour=12)

    def test_invalid_day_too_high(self):
        """Day above 31 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date"):
            BirthData(year=1990, month=6, day=32, hour=12)

    def test_invalid_hour_negative(self):
        """Negative hour raises ValueError."""
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            BirthData(year=1990, month=6, day=15, hour=-1)

    def test_invalid_hour_too_high(self):
        """Hour above 23 raises ValueError."""
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            BirthData(year=1990, month=6, day=15, hour=24)

    def test_invalid_minute_negative(self):
        """Negative minute raises ValueError."""
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            BirthData(year=1990, month=6, day=15, hour=12, minute=-1)

    def test_invalid_minute_too_high(self):
        """Minute above 59 raises ValueError."""
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            BirthData(year=1990, month=6, day=15, hour=12, minute=60)

    def test_invalid_february_30(self):
        """Feb 30 raises ValueError (impossible date)."""
        with pytest.raises(ValueError, match="Invalid date"):
            BirthData(year=1990, month=2, day=30, hour=12)

    def test_invalid_leap_year_feb_29(self):
        """Feb 29 on non-leap year raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date"):
            BirthData(year=1990, month=2, day=29, hour=12)  # 1990 is not a leap year

    def test_valid_leap_year_feb_29(self):
        """Feb 29 on leap year is valid."""
        birth = BirthData(year=2000, month=2, day=29, hour=12)  # 2000 is a leap year
        assert birth.day == 29

    def test_birth_data_is_frozen(self):
        """BirthData is immutable."""
        birth = BirthData(year=1990, month=6, day=15, hour=12)
        with pytest.raises(AttributeError):
            birth.year = 2000


class TestBaZiCreation:
    """Tests for BaZi creation."""

    def test_create_from_pillars(self):
        """Create BaZi from Pillar objects."""
        bazi = BaZi(
            year_pillar=Pillar.from_chinese("甲子"),
            month_pillar=Pillar.from_chinese("乙丑"),
            day_pillar=Pillar.from_chinese("丙寅"),
            hour_pillar=Pillar.from_chinese("丁卯"),
        )
        assert str(bazi.year_pillar) == "甲子"
        assert str(bazi.day_pillar) == "丙寅"

    def test_from_chinese_with_spaces(self):
        """from_chinese works with space-separated pillars."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        assert str(bazi) == "甲子 乙丑 丙寅 丁卯"

    def test_from_chinese_without_spaces(self):
        """from_chinese works without spaces."""
        bazi = BaZi.from_chinese("甲子乙丑丙寅丁卯")
        assert str(bazi) == "甲子 乙丑 丙寅 丁卯"

    def test_from_chinese_invalid_length(self):
        """from_chinese raises ValueError for wrong length."""
        with pytest.raises(ValueError, match="requires 8 characters"):
            BaZi.from_chinese("甲子乙丑丙")

    def test_from_pillars_strings(self):
        """from_pillars creates BaZi from four pillar strings."""
        bazi = BaZi.from_pillars(
            year="甲子",
            month="乙丑",
            day="丙寅",
            hour="丁卯"
        )
        assert bazi.year_pillar.chinese == "甲子"
        assert bazi.hour_pillar.chinese == "丁卯"


class TestBaZiProperties:
    """Tests for BaZi properties."""

    @pytest.fixture
    def sample_bazi(self):
        """Create a sample BaZi for testing."""
        return BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")

    def test_str_returns_chinese(self, sample_bazi):
        """__str__ returns space-separated Chinese pillars."""
        assert str(sample_bazi) == "甲子 乙丑 丙寅 丁卯"

    def test_chinese_property(self, sample_bazi):
        """chinese property returns the same as __str__."""
        assert sample_bazi.chinese == "甲子 乙丑 丙寅 丁卯"

    def test_pillars_returns_list(self, sample_bazi):
        """pillars property returns list of all four pillars."""
        pillars = sample_bazi.pillars
        assert len(pillars) == 4
        assert pillars[0] == sample_bazi.year_pillar
        assert pillars[1] == sample_bazi.month_pillar
        assert pillars[2] == sample_bazi.day_pillar
        assert pillars[3] == sample_bazi.hour_pillar

    def test_day_master(self, sample_bazi):
        """day_master returns the day pillar's stem."""
        # Day pillar is 丙寅, so day master is 丙
        assert sample_bazi.day_master == HeavenlyStem.BING

    def test_day_master_wuxing(self, sample_bazi):
        """day_master_wuxing returns WuXing of day master."""
        # 丙 is Fire
        assert sample_bazi.day_master_wuxing == WuXing.FIRE

    def test_all_stems(self, sample_bazi):
        """all_stems returns list of four stems."""
        stems = sample_bazi.all_stems
        assert len(stems) == 4
        assert stems[0] == HeavenlyStem.JIA  # 甲
        assert stems[1] == HeavenlyStem.YI   # 乙
        assert stems[2] == HeavenlyStem.BING # 丙
        assert stems[3] == HeavenlyStem.DING # 丁

    def test_all_branches(self, sample_bazi):
        """all_branches returns list of four branches."""
        branches = sample_bazi.all_branches
        assert len(branches) == 4
        assert branches[0] == EarthlyBranch.ZI    # 子
        assert branches[1] == EarthlyBranch.CHOU  # 丑
        assert branches[2] == EarthlyBranch.YIN   # 寅
        assert branches[3] == EarthlyBranch.MAO   # 卯


class TestBaZiWuXingCount:
    """Tests for wuxing_count method."""

    def test_wuxing_count_basic(self):
        """wuxing_count returns correct element counts."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        count = bazi.wuxing_count()

        # Stems: 甲(Wood), 乙(Wood), 丙(Fire), 丁(Fire)
        # Branches: 子(Water), 丑(Earth), 寅(Wood), 卯(Wood)
        assert count[WuXing.WOOD] == 4  # 甲, 乙, 寅, 卯
        assert count[WuXing.FIRE] == 2  # 丙, 丁
        assert count[WuXing.EARTH] == 1  # 丑
        assert count[WuXing.WATER] == 1  # 子
        assert count[WuXing.METAL] == 0

    def test_wuxing_count_all_wood(self):
        """Count when heavily Wood dominated."""
        bazi = BaZi.from_chinese("甲寅 乙卯 甲寅 乙卯")
        count = bazi.wuxing_count()
        assert count[WuXing.WOOD] == 8
        assert count[WuXing.FIRE] == 0
        assert count[WuXing.EARTH] == 0
        assert count[WuXing.METAL] == 0
        assert count[WuXing.WATER] == 0

    def test_contains_all_wuxing_true(self):
        """contains_all_wuxing returns True when all five present."""
        # 甲(Wood) 子(Water) | 丙(Fire) 辰(Earth) | 庚(Metal) 寅(Wood) | 壬(Water) 午(Fire)
        bazi = BaZi.from_chinese("甲子 丙辰 庚寅 壬午")
        count = bazi.wuxing_count()
        # Wood: 甲, 寅 = 2
        # Fire: 丙, 午 = 2
        # Earth: 辰 = 1
        # Metal: 庚 = 1
        # Water: 子, 壬 = 2
        assert bazi.contains_all_wuxing() is True

    def test_contains_all_wuxing_false(self):
        """contains_all_wuxing returns False when one element missing."""
        bazi = BaZi.from_chinese("甲寅 乙卯 甲寅 乙卯")  # Only Wood
        assert bazi.contains_all_wuxing() is False


class TestBaZiImmutability:
    """Tests for BaZi immutability."""

    def test_bazi_is_frozen(self):
        """BaZi is immutable (frozen dataclass)."""
        bazi = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        with pytest.raises(AttributeError):
            bazi.year_pillar = Pillar.from_chinese("癸亥")

    def test_bazi_is_hashable(self):
        """Frozen BaZi can be used in sets and as dict keys."""
        bazi1 = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        bazi2 = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        bazi3 = BaZi.from_chinese("癸亥 壬戌 辛酉 庚申")

        bazi_set = {bazi1, bazi2, bazi3}
        assert len(bazi_set) == 2  # bazi1 == bazi2

    def test_bazi_equality(self):
        """BaZi with same pillars are equal."""
        bazi1 = BaZi.from_chinese("甲子 乙丑 丙寅 丁卯")
        bazi2 = BaZi.from_pillars("甲子", "乙丑", "丙寅", "丁卯")
        assert bazi1 == bazi2


class TestRealWorldBaZi:
    """Tests with real-world BaZi examples."""

    def test_famous_bazi_mao_zedong(self):
        """Mao Zedong's reported BaZi (approximate)."""
        # 1893年12月26日辰时 - 癸巳 甲子 丁酉 甲辰
        bazi = BaZi.from_chinese("癸巳 甲子 丁酉 甲辰")
        assert bazi.day_master == HeavenlyStem.DING
        assert bazi.day_master_wuxing == WuXing.FIRE

    def test_various_combinations(self):
        """Test various BaZi combinations work correctly."""
        test_cases = [
            "甲子 甲子 甲子 甲子",  # Same pillar repeated
            "癸亥 癸亥 癸亥 癸亥",  # All Water
            "庚申 庚申 庚申 庚申",  # All Metal
            "丙午 丙午 丙午 丙午",  # All Fire
        ]
        for chinese in test_cases:
            bazi = BaZi.from_chinese(chinese)
            assert len(bazi.pillars) == 4
            assert len(bazi.all_stems) == 4
            assert len(bazi.all_branches) == 4
