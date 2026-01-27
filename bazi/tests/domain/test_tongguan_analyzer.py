"""
Tests for 通关用神 (Mediation) analyzer service.

Tests element conflict detection and mediator recommendations.
"""
import pytest

from bazi.domain.models import BaZi, WuXing, WuXingStrength, WangXiang
from bazi.domain.services import TongGuanAnalyzer, TongGuanResult, ElementConflict


class TestTongGuanTable:
    """Tests for 通关 mediation table."""

    @pytest.fixture
    def analyzer(self):
        return TongGuanAnalyzer()

    def test_metal_wood_conflict_uses_water(self, analyzer):
        """金木相战，取水通关"""
        from bazi.domain.services.tongguan_analyzer import TONGGUAN_TABLE

        assert TONGGUAN_TABLE[(WuXing.METAL, WuXing.WOOD)] == WuXing.WATER
        assert TONGGUAN_TABLE[(WuXing.WOOD, WuXing.METAL)] == WuXing.WATER

    def test_wood_earth_conflict_uses_fire(self, analyzer):
        """木土相战，取火通关"""
        from bazi.domain.services.tongguan_analyzer import TONGGUAN_TABLE

        assert TONGGUAN_TABLE[(WuXing.WOOD, WuXing.EARTH)] == WuXing.FIRE
        assert TONGGUAN_TABLE[(WuXing.EARTH, WuXing.WOOD)] == WuXing.FIRE

    def test_earth_water_conflict_uses_metal(self, analyzer):
        """土水相战，取金通关"""
        from bazi.domain.services.tongguan_analyzer import TONGGUAN_TABLE

        assert TONGGUAN_TABLE[(WuXing.EARTH, WuXing.WATER)] == WuXing.METAL
        assert TONGGUAN_TABLE[(WuXing.WATER, WuXing.EARTH)] == WuXing.METAL

    def test_water_fire_conflict_uses_wood(self, analyzer):
        """水火相战，取木通关"""
        from bazi.domain.services.tongguan_analyzer import TONGGUAN_TABLE

        assert TONGGUAN_TABLE[(WuXing.WATER, WuXing.FIRE)] == WuXing.WOOD
        assert TONGGUAN_TABLE[(WuXing.FIRE, WuXing.WATER)] == WuXing.WOOD

    def test_fire_metal_conflict_uses_earth(self, analyzer):
        """火金相战，取土通关"""
        from bazi.domain.services.tongguan_analyzer import TONGGUAN_TABLE

        assert TONGGUAN_TABLE[(WuXing.FIRE, WuXing.METAL)] == WuXing.EARTH
        assert TONGGUAN_TABLE[(WuXing.METAL, WuXing.FIRE)] == WuXing.EARTH


class TestConflictDetection:
    """Tests for conflict detection."""

    @pytest.fixture
    def analyzer(self):
        return TongGuanAnalyzer()

    def _make_wuxing_strength(
        self,
        wood: float = 0,
        fire: float = 0,
        earth: float = 0,
        metal: float = 0,
        water: float = 0,
    ) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {
            WuXing.WOOD: wood,
            WuXing.FIRE: fire,
            WuXing.EARTH: earth,
            WuXing.METAL: metal,
            WuXing.WATER: water,
        }
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_no_conflict_when_one_element_dominant(self, analyzer):
        """单一元素独大时无相战"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(wood=80, water=10, fire=5, earth=3, metal=2)

        result = analyzer.analyze(bazi, wuxing_strength)

        assert result.has_conflict is False
        assert len(result.conflicts) == 0

    def test_detects_metal_wood_conflict(self, analyzer):
        """检测金木相战"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        # 金木各占30%+，且势均力敌
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        assert result.has_conflict is True
        assert len(result.conflicts) >= 1

        # 应该推荐水通关
        metal_wood_conflict = None
        for conflict in result.conflicts:
            if WuXing.METAL in (conflict.element1, conflict.element2) and \
               WuXing.WOOD in (conflict.element1, conflict.element2):
                metal_wood_conflict = conflict
                break

        assert metal_wood_conflict is not None
        assert metal_wood_conflict.mediator == WuXing.WATER

    def test_detects_water_fire_conflict(self, analyzer):
        """检测水火相战"""
        bazi = BaZi.from_chinese("丙子丙子丙子丙子")
        wuxing_strength = self._make_wuxing_strength(
            water=35, fire=35, wood=10, earth=10, metal=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        assert result.has_conflict is True

        # 应该推荐木通关
        water_fire_conflict = None
        for conflict in result.conflicts:
            if WuXing.WATER in (conflict.element1, conflict.element2) and \
               WuXing.FIRE in (conflict.element1, conflict.element2):
                water_fire_conflict = conflict
                break

        assert water_fire_conflict is not None
        assert water_fire_conflict.mediator == WuXing.WOOD

    def test_no_conflict_when_imbalanced(self, analyzer):
        """力量悬殊时不算相战"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        # 金比木强太多（金50%，木15%），不算相战
        wuxing_strength = self._make_wuxing_strength(
            wood=15, metal=50, fire=15, earth=10, water=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        # 检查金木相战是否被检测
        metal_wood_conflict = None
        for conflict in result.conflicts:
            if WuXing.METAL in (conflict.element1, conflict.element2) and \
               WuXing.WOOD in (conflict.element1, conflict.element2):
                metal_wood_conflict = conflict
                break

        # 力量比 15/50 = 0.3 < 0.5，不应检测到相战
        assert metal_wood_conflict is None


class TestMediatorRecommendation:
    """Tests for mediator recommendations."""

    @pytest.fixture
    def analyzer(self):
        return TongGuanAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        defaults = {WuXing.WOOD: 20, WuXing.FIRE: 20, WuXing.EARTH: 20,
                    WuXing.METAL: 20, WuXing.WATER: 20}
        values = {getattr(WuXing, k.upper()): v for k, v in kwargs.items()}
        for key in defaults:
            if key not in values:
                values[key] = defaults[key]
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_primary_mediator_from_strongest_conflict(self, analyzer):
        """主要通关用神来自最严重的相战"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        # 金木相战最严重，应推荐水通关
        assert result.primary_mediator == WuXing.WATER

    def test_mediator_scores_normalized(self, analyzer):
        """通关评分应在0-1范围"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        for score in result.recommended_mediators.values():
            assert 0.0 <= score <= 1.0


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def analyzer(self):
        return TongGuanAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        defaults = {WuXing.WOOD: 20, WuXing.FIRE: 20, WuXing.EARTH: 20,
                    WuXing.METAL: 20, WuXing.WATER: 20}
        values = {}
        for element in WuXing:
            key = element.name.lower()
            values[element] = kwargs.get(key, defaults[element])
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_get_tongguan_wuxing_returns_mediator(self, analyzer):
        """get_tongguan_wuxing 返回通关元素"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        mediator = analyzer.get_tongguan_wuxing(bazi, wuxing_strength)

        assert mediator == WuXing.WATER

    def test_get_tongguan_wuxing_returns_none_no_conflict(self, analyzer):
        """无相战时返回None"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=80, metal=5, fire=5, earth=5, water=5
        )

        mediator = analyzer.get_tongguan_wuxing(bazi, wuxing_strength)

        assert mediator is None

    def test_needs_mediation_true_when_conflict(self, analyzer):
        """有相战时需要通关"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        assert analyzer.needs_mediation(bazi, wuxing_strength) is True

    def test_needs_mediation_false_no_conflict(self, analyzer):
        """无相战时不需要通关"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=80, metal=5, fire=5, earth=5, water=5
        )

        assert analyzer.needs_mediation(bazi, wuxing_strength) is False


class TestConflictDescription:
    """Tests for conflict descriptions."""

    @pytest.fixture
    def analyzer(self):
        return TongGuanAnalyzer()

    def _make_wuxing_strength(self, **kwargs) -> WuXingStrength:
        """Helper to create WuXingStrength."""
        values = {element: kwargs.get(element.name.lower(), 20) for element in WuXing}
        wang_xiang = {element: WangXiang.XIU for element in WuXing}
        return WuXingStrength(
            raw_values=values,
            wang_xiang=wang_xiang,
            adjusted_values=values,
        )

    def test_description_includes_conflict_type(self, analyzer):
        """描述应包含相战类型"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        assert "金木相战" in result.description

    def test_description_includes_mediator(self, analyzer):
        """描述应包含通关用神"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=35, metal=35, fire=10, earth=10, water=10
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        assert "水" in result.description

    def test_no_conflict_description(self, analyzer):
        """无相战时的描述"""
        bazi = BaZi.from_chinese("甲子甲子甲子甲子")
        wuxing_strength = self._make_wuxing_strength(
            wood=80, metal=5, fire=5, earth=5, water=5
        )

        result = analyzer.analyze(bazi, wuxing_strength)

        assert "无明显相战" in result.description or "流通" in result.description
