"""
势能理论实验室 (Potential Energy Lab)

用于验证和标定势能函数参数
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum

from ..models import BaZi, WuXing


@dataclass
class TestCase:
    """测试案例"""
    name: str
    bazi_str: str
    expected_yongshen: List[WuXing]  # 预期喜用神
    expected_jishen: List[WuXing]    # 预期忌神
    pattern: str                      # 格局类型
    notes: str = ""                   # 备注


@dataclass
class LabResult:
    """实验结果"""
    case: TestCase

    # 计算结果
    day_master: WuXing
    day_master_ratio: float
    wuxing_values: Dict[WuXing, float]

    # 势能分解
    E_balance: float
    E_conflict: float
    E_tiaohuo: float
    E_total: float

    # 喜用神预测
    predicted_yongshen: List[WuXing]
    predicted_jishen: List[WuXing]

    # 验证结果
    yongshen_correct: bool
    jishen_correct: bool

    # 详细梯度
    gradients: Dict[WuXing, float] = field(default_factory=dict)


class PotentialEnergyLab:
    """
    势能实验室

    功能：
    1. 计算详细的势能分解
    2. 预测喜用神
    3. 与已知案例对比验证
    4. 调整参数
    """

    def __init__(
        self,
        w_balance: float = 1.0,
        w_conflict: float = 0.3,
        w_tiaohuo: float = 0.2,
        tiaohuo_threshold: float = 0.10,  # 调候需求阈值
    ):
        self.w_balance = w_balance
        self.w_conflict = w_conflict
        self.w_tiaohuo = w_tiaohuo
        self.tiaohuo_threshold = tiaohuo_threshold

        # 五行相克矩阵 (克者, 被克者) -> 克系数
        self.ke_matrix = self._build_ke_matrix()

        # 通关五行表
        self.tongguan_map = {
            (WuXing.METAL, WuXing.WOOD): WuXing.WATER,  # 金克木，水通关
            (WuXing.WOOD, WuXing.EARTH): WuXing.FIRE,   # 木克土，火通关
            (WuXing.EARTH, WuXing.WATER): WuXing.METAL, # 土克水，金通关
            (WuXing.WATER, WuXing.FIRE): WuXing.WOOD,   # 水克火，木通关
            (WuXing.FIRE, WuXing.METAL): WuXing.EARTH,  # 火克金，土通关
        }

    def _build_ke_matrix(self) -> Dict[Tuple[WuXing, WuXing], float]:
        """构建相克矩阵"""
        克系数 = 1.0
        return {
            (WuXing.METAL, WuXing.WOOD): 克系数,
            (WuXing.WOOD, WuXing.EARTH): 克系数,
            (WuXing.EARTH, WuXing.WATER): 克系数,
            (WuXing.WATER, WuXing.FIRE): 克系数,
            (WuXing.FIRE, WuXing.METAL): 克系数,
        }

    def run_case(self, case: TestCase) -> LabResult:
        """运行单个测试案例"""
        from .wuxing_calculator import WuXingCalculator
        from .branch_analyzer import BranchAnalyzer

        # 解析八字
        bazi = BaZi.from_chinese(case.bazi_str)
        day_master = bazi.day_master.wuxing

        # 计算五行能量
        branch_analyzer = BranchAnalyzer()
        branch_result = branch_analyzer.analyze(bazi)

        wuxing_calc = WuXingCalculator()
        wuxing_result = wuxing_calc.calculate_strength_with_relations(bazi, branch_result)
        wuxing_values = wuxing_result.raw_values

        total = sum(wuxing_values.values())

        # 计算日主阵营比例
        peer = day_master
        support = day_master.generated_by
        beneficial = wuxing_values.get(peer, 0) + wuxing_values.get(support, 0)
        day_master_ratio = beneficial / total if total > 0 else 0.5

        # 确定吸引子
        attractor = self._find_attractor(bazi, wuxing_values, day_master_ratio)

        # 计算各项势能
        E_balance = self._calc_E_balance(day_master_ratio, attractor)
        E_conflict = self._calc_E_conflict(wuxing_values)
        E_tiaohuo = self._calc_E_tiaohuo(bazi, wuxing_values)

        E_total = (
            self.w_balance * E_balance +
            self.w_conflict * E_conflict +
            self.w_tiaohuo * E_tiaohuo
        )

        # 计算各五行的梯度
        gradients = self._calc_gradients(
            bazi, wuxing_values, day_master_ratio, attractor
        )

        # 预测喜用神（梯度为正的五行）
        sorted_elements = sorted(gradients.items(), key=lambda x: -x[1])
        predicted_yongshen = [e for e, g in sorted_elements if g > 0][:2]
        predicted_jishen = [e for e, g in sorted_elements if g < 0][-2:]

        # 验证
        yongshen_correct = set(predicted_yongshen[:2]) == set(case.expected_yongshen[:2])
        jishen_correct = len(set(predicted_jishen) & set(case.expected_jishen)) > 0

        return LabResult(
            case=case,
            day_master=day_master,
            day_master_ratio=day_master_ratio,
            wuxing_values=wuxing_values,
            E_balance=E_balance,
            E_conflict=E_conflict,
            E_tiaohuo=E_tiaohuo,
            E_total=E_total,
            predicted_yongshen=predicted_yongshen,
            predicted_jishen=predicted_jishen,
            yongshen_correct=yongshen_correct,
            jishen_correct=jishen_correct,
            gradients=gradients,
        )

    def _find_attractor(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
        ratio: float
    ) -> float:
        """找到吸引子位置"""
        from .branch_analyzer import BranchAnalyzer

        day_master = bazi.day_master.wuxing

        # 检查有效根
        branch_analyzer = BranchAnalyzer()
        branch_result = branch_analyzer.analyze(bazi)

        # 被吸收的地支
        absorbed_branches = set()
        for combo in branch_result.san_hui + branch_result.san_he:
            if combo.element and combo.element != day_master:
                absorbed_branches.update(combo.branches)

        # 检查天干帮助
        peer = day_master
        support = day_master.generated_by
        has_stem_help = any(
            p.stem.wuxing in (peer, support)
            for p in bazi.pillars if p != bazi.day_pillar
        )

        # 检查有效藏干根
        has_effective_root = False
        for pillar in bazi.pillars:
            branch = pillar.branch.chinese
            for hidden, r in pillar.hidden_stems.items():
                if r >= 0.3 and hidden.wuxing in (peer, support):
                    if branch not in absorbed_branches:
                        has_effective_root = True

        has_root = has_stem_help or has_effective_root

        # 判断格局
        if ratio > 0.70:
            return 1.0  # 专旺
        elif ratio < 0.25 and not has_root:
            return 0.0  # 从格
        else:
            return 0.5  # 普通

    def _calc_E_balance(self, ratio: float, attractor: float) -> float:
        """计算偏离势能"""
        return (ratio - attractor) ** 2

    def _calc_E_conflict(self, wuxing_values: Dict[WuXing, float]) -> float:
        """计算冲突势能（含通关）"""
        total = sum(wuxing_values.values())
        if total == 0:
            return 0.0

        # 归一化
        x = {e: v / total for e, v in wuxing_values.items()}

        E = 0.0
        for (克者, 被克者), 克系数 in self.ke_matrix.items():
            # 基础冲突能量
            基础冲突 = x[克者] * x[被克者] * 克系数

            # 通关降低冲突
            通关者 = self.tongguan_map.get((克者, 被克者))
            if 通关者:
                通关强度 = x.get(通关者, 0)
                冲突强度 = x[克者] + x[被克者]
                if 冲突强度 > 0:
                    通关系数 = min(1.0, 通关强度 / 冲突强度 * 2)
                else:
                    通关系数 = 0
                实际冲突 = 基础冲突 * (1 - 通关系数 * 0.5)
            else:
                实际冲突 = 基础冲突

            E += 实际冲突

        return E

    def _calc_E_tiaohuo(self, bazi: BaZi, wuxing_values: Dict[WuXing, float]) -> float:
        """计算调候势能"""
        month = bazi.month_pillar.branch.chinese
        total = sum(wuxing_values.values())
        if total == 0:
            return 0.0

        冬月 = {'亥', '子', '丑'}
        夏月 = {'巳', '午', '未'}

        火比例 = wuxing_values.get(WuXing.FIRE, 0) / total
        水比例 = wuxing_values.get(WuXing.WATER, 0) / total

        E = 0.0
        if month in 冬月:
            缺火 = max(0, self.tiaohuo_threshold - 火比例)
            E = 缺火 ** 2
        elif month in 夏月:
            缺水 = max(0, self.tiaohuo_threshold - 水比例)
            E = 缺水 ** 2

        return E

    def _calc_gradients(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
        ratio: float,
        attractor: float,
    ) -> Dict[WuXing, float]:
        """计算各五行的梯度（正值=喜用神）

        核心原则：通关加成必须服从扶抑原则
        - 身强时：通关五行若生日主，则不给加成
        - 身弱时：通关五行若克日主，则不给加成
        """
        day_master = bazi.day_master.wuxing
        peer = day_master
        support = day_master.generated_by

        gradients = {}

        # 当前总势能
        E_current = self._calc_E_balance(ratio, attractor)

        # 判断身强身弱（普通格局用0.5作为分界）
        is_strong = ratio > attractor if attractor == 0.5 else (
            attractor == 1.0  # 专旺格视为身强
        )

        for element in WuXing:
            # 模拟加入该五行后的新比例
            if element in (peer, support):
                # 有利五行，增加日主比例
                delta = 0.10
                new_ratio = (ratio + delta) / (1 + delta)
            else:
                # 不利五行，稀释日主比例
                new_ratio = ratio / 1.10

            new_ratio = max(0, min(1, new_ratio))

            # 新势能
            E_new = self._calc_E_balance(new_ratio, attractor)

            # 梯度 = 势能下降量（正值=喜用神）
            gradient = E_current - E_new

            # 从格特殊处理：区分泄和克
            # 从格喜顺不喜逆：泄秀（食伤）和财星是顺，官杀（克）是逆
            if attractor == 0.0 and gradient > 0:
                shishang = day_master.generates  # 食伤（我生者）
                caixing = day_master.generates.generates  # 财星（我生者再生）
                guansha = day_master.generated_by.generated_by  # 官杀（克我者）

                if element == shishang:
                    gradient += 0.01  # 食伤最好（泄秀）
                elif element == caixing:
                    gradient += 0.005  # 财星次好（顺泄）
                elif element == guansha:
                    gradient -= 0.01  # 官杀不喜（克日主会激起反抗）

            # 身强特殊处理：宜泄不宜克
            # 传统理论：身强用食伤泄秀为上，财星耗身次之，官杀克制为下
            # 原因：克制太猛烈，易激反；泄秀温和有效
            if is_strong and attractor == 0.5 and gradient > 0:
                shishang = day_master.generates  # 食伤（泄秀）
                caixing = day_master.generates.generates  # 财星（耗身）
                guansha = day_master.generated_by.generated_by  # 官杀（克制）

                # 身强程度影响调整幅度
                strength_factor = (ratio - 0.5) * 2  # 0~1 scale

                if element == shishang:
                    gradient += 0.02 * strength_factor  # 食伤泄秀最好
                elif element == caixing:
                    gradient += 0.015 * strength_factor  # 财星耗身次之
                elif element == guansha:
                    gradient -= 0.02 * strength_factor  # 官杀克制，强烈降权

            # 加入调候加成（身强时调候权重降低，因为泄耗优先于调候）
            month = bazi.month_pillar.branch.chinese
            tiaohuo_bonus = 0.02
            if is_strong and attractor == 0.5:
                tiaohuo_bonus = 0.005  # 身强时调候不是首要考虑

            if month in {'亥', '子', '丑'} and element == WuXing.FIRE:
                gradient += tiaohuo_bonus  # 冬天火加分
            elif month in {'巳', '午', '未'} and element == WuXing.WATER:
                gradient += tiaohuo_bonus  # 夏天水加分

            # 加入通关加成（条件性：必须服从扶抑原则）
            tongguan_bonus = self._calc_tongguan_bonus(element, wuxing_values)
            if tongguan_bonus > 0:
                # 检查是否违反扶抑原则
                violates_fuyi = self._check_fuyi_violation(
                    element, day_master, is_strong, attractor
                )
                if not violates_fuyi:
                    gradient += tongguan_bonus

            gradients[element] = gradient

        return gradients

    def _check_fuyi_violation(
        self,
        element: WuXing,
        day_master: WuXing,
        is_strong: bool,
        attractor: float,
    ) -> bool:
        """检查通关五行是否违反扶抑原则

        返回True表示违反扶抑原则，不应给通关加成
        """
        peer = day_master
        support = day_master.generated_by

        # 从格特殊处理：不检查扶抑违反
        if attractor == 0.0:
            # 从格：顺从强势五行，不需要扶抑检查
            return False

        if is_strong:
            # 身强：喜克泄耗，忌生扶
            # 如果通关五行会生日主（是印星），则违反
            if element == support:
                return True
            # 如果通关五行是比劫（同类），也违反
            if element == peer:
                return True
        else:
            # 身弱：喜生扶，忌克泄耗
            # 如果通关五行会克日主（是官杀），则违反
            if element.generates == day_master.generated_by:  # 克日主
                return True
            # 如果通关五行会泄日主（是食伤），则违反
            if day_master.generates == element:
                return True

        return False

    def _calc_tongguan_bonus(
        self,
        element: WuXing,
        wuxing_values: Dict[WuXing, float]
    ) -> float:
        """计算通关加成"""
        total = sum(wuxing_values.values())
        if total == 0:
            return 0.0

        x = {e: v / total for e, v in wuxing_values.items()}

        bonus = 0.0
        for (克者, 被克者), 通关者 in self.tongguan_map.items():
            if element == 通关者:
                # 这个五行可以通关
                冲突强度 = x[克者] * x[被克者]
                if 冲突强度 > 0.05:  # 有明显冲突
                    bonus += 冲突强度 * 0.5

        return bonus

    def print_result(self, result: LabResult):
        """打印详细结果"""
        print(f"\n{'='*60}")
        print(f"案例：{result.case.name}")
        print(f"八字：{result.case.bazi_str}")
        print(f"格局：{result.case.pattern}")
        print(f"{'='*60}")

        print(f"\n日主：{result.day_master.chinese}")
        print(f"日主阵营比例：{result.day_master_ratio:.1%}")

        print(f"\n五行能量分布：")
        total = sum(result.wuxing_values.values())
        for e in WuXing:
            v = result.wuxing_values.get(e, 0)
            pct = v / total * 100 if total > 0 else 0
            bar = '█' * int(pct / 2)
            print(f"  {e.chinese}: {v:5.1f} ({pct:4.1f}%) {bar}")

        print(f"\n势能分解：")
        print(f"  E_偏离：{result.E_balance:.4f} (权重 {self.w_balance})")
        print(f"  E_冲突：{result.E_conflict:.4f} (权重 {self.w_conflict})")
        print(f"  E_调候：{result.E_tiaohuo:.4f} (权重 {self.w_tiaohuo})")
        print(f"  E_总计：{result.E_total:.4f}")

        print(f"\n五行梯度（正=喜，负=忌）：")
        for e, g in sorted(result.gradients.items(), key=lambda x: -x[1]):
            sign = "+" if g > 0 else ""
            role = "喜" if g > 0 else "忌"
            bar = '▓' * int(abs(g) * 100) if g > 0 else '░' * int(abs(g) * 100)
            print(f"  {e.chinese}: {sign}{g:.4f} [{role}] {bar}")

        print(f"\n预测喜用神：{[e.chinese for e in result.predicted_yongshen]}")
        print(f"预期喜用神：{[e.chinese for e in result.case.expected_yongshen]}")
        print(f"喜用神正确：{'✓' if result.yongshen_correct else '✗'}")

        print(f"\n预测忌神：{[e.chinese for e in result.predicted_jishen]}")
        print(f"预期忌神：{[e.chinese for e in result.case.expected_jishen]}")

        if result.case.notes:
            print(f"\n备注：{result.case.notes}")


def run_lab():
    """运行实验室"""

    # 测试案例
    cases = [
        TestCase(
            name="姚明",
            bazi_str="庚申乙酉戊子壬戌",
            expected_yongshen=[WuXing.METAL, WuXing.WATER],
            expected_jishen=[WuXing.FIRE, WuXing.EARTH],
            pattern="假从儿格",
            notes="申酉戌三会金局，戌中戊土被吸收，从金水"
        ),
        TestCase(
            name="文天祥",
            bazi_str="丙子癸巳丙午丁酉",
            expected_yongshen=[WuXing.EARTH, WuXing.METAL],
            expected_jishen=[WuXing.WOOD, WuXing.FIRE],
            pattern="身强",
            notes="丙火生巳午月，火旺身强，喜土金泄克"
        ),
        TestCase(
            name="身弱水例",
            bazi_str="庚午己卯癸巳甲寅",
            expected_yongshen=[WuXing.METAL, WuXing.WATER],
            expected_jishen=[WuXing.FIRE, WuXing.EARTH],
            pattern="身弱",
            notes="癸水生卯月，木旺泄水，身弱喜金水"
        ),
        TestCase(
            name="平衡印旺例",
            bazi_str="甲申戊辰癸酉壬戌",
            expected_yongshen=[WuXing.METAL],
            expected_jishen=[WuXing.EARTH, WuXing.FIRE],
            pattern="平衡（偏印格）",
            notes="癸水生辰月，日主阵营49.6%接近平衡，金印通关化官杀为用"
        ),
        TestCase(
            name="调候案例-冬水",
            bazi_str="壬子癸丑甲子乙亥",
            expected_yongshen=[WuXing.FIRE, WuXing.WOOD],
            expected_jishen=[WuXing.WATER, WuXing.METAL],
            pattern="身弱需调候",
            notes="冬月水旺极寒，急需火调候"
        ),
    ]

    lab = PotentialEnergyLab()

    print("=" * 60)
    print("势能理论实验室 - 案例验证")
    print("=" * 60)

    correct_count = 0
    for case in cases:
        result = lab.run_case(case)
        lab.print_result(result)
        if result.yongshen_correct:
            correct_count += 1

    print(f"\n{'='*60}")
    print(f"总结：{correct_count}/{len(cases)} 案例预测正确")
    print(f"准确率：{correct_count/len(cases)*100:.0f}%")
    print("=" * 60)


if __name__ == "__main__":
    run_lab()
