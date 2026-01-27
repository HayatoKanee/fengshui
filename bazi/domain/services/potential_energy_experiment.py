"""
八字势能理论实验 (BaZi Potential Energy Theory Experiment)

目的：验证势能函数和吸引子假设

核心假设：
1. 命局状态可以用势能函数 E(x) 描述
2. 不同格局对应不同的吸引子（势能最低点）
3. 喜用神是能降低势能的五行
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum

from ..models import BaZi, WuXing


class AttractorType(Enum):
    """吸引子类型（格局类型）"""
    NORMAL = "normal"      # 普通格局，吸引子在 ~50%
    CONG_GE = "cong_ge"    # 从格，吸引子在 ~0%
    ZHUAN_WANG = "zhuan_wang"  # 专旺格，吸引子在 ~100%


@dataclass
class PotentialEnergyResult:
    """势能计算结果"""
    # 当前状态
    day_master_ratio: float  # 日主阵营占比 (0-1)

    # 吸引子
    attractor_type: AttractorType
    attractor_position: float  # 吸引子位置 (0-1)

    # 势能
    total_energy: float
    balance_energy: float  # 平衡项势能
    flow_energy: float     # 流通项势能
    season_energy: float   # 调候项势能

    # 各五行的梯度（负梯度方向 = 喜用神）
    gradients: Dict[WuXing, float]

    # 喜用神排名
    yongshen_ranked: List[WuXing]


class PotentialEnergyCalculator:
    """
    势能计算器 - 实验版本

    势能函数：
    E(x) = E_balance + λ₁ * E_flow + λ₂ * E_season

    其中：
    - E_balance = (ratio - attractor)²  偏离吸引子的代价
    - E_flow = 流通阻塞的代价
    - E_season = 调候偏离的代价
    """

    def __init__(
        self,
        lambda_flow: float = 0.3,
        lambda_season: float = 0.2,
    ):
        self.lambda_flow = lambda_flow
        self.lambda_season = lambda_season

        # 五行相互作用矩阵 (生克关系)
        # W[i][j] > 0 表示 i 生 j 或 j 生 i（有利）
        # W[i][j] < 0 表示 i 克 j 或 j 克 i（不利）
        self.interaction_matrix = self._build_interaction_matrix()

    def _build_interaction_matrix(self) -> Dict[Tuple[WuXing, WuXing], float]:
        """构建五行相互作用矩阵"""
        W = {}

        for e1 in WuXing:
            for e2 in WuXing:
                if e1 == e2:
                    W[(e1, e2)] = 0.0
                elif e1.generates == e2 or e2.generates == e1:
                    # 相生关系 - 正向耦合
                    W[(e1, e2)] = 1.0
                elif e1.overcomes == e2 or e2.overcomes == e1:
                    # 相克关系 - 负向耦合
                    W[(e1, e2)] = -0.5
                else:
                    W[(e1, e2)] = 0.0

        return W

    def calculate(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
    ) -> PotentialEnergyResult:
        """计算势能"""

        day_master = bazi.day_master.wuxing
        total = sum(wuxing_values.values())

        # 1. 计算日主阵营占比
        # 日主阵营 = 比劫(同五行) + 印绶(生我)
        peer = day_master
        support = day_master.generated_by

        beneficial = wuxing_values.get(peer, 0) + wuxing_values.get(support, 0)
        ratio = beneficial / total if total > 0 else 0.5

        # 2. 确定吸引子
        attractor_type, attractor_pos = self._find_attractor(bazi, wuxing_values, ratio)

        # 3. 计算各项势能
        E_balance = self._calculate_balance_energy(ratio, attractor_pos)
        E_flow = self._calculate_flow_energy(wuxing_values)
        E_season = self._calculate_season_energy(bazi, wuxing_values)

        E_total = (
            E_balance +
            self.lambda_flow * E_flow +
            self.lambda_season * E_season
        )

        # 4. 计算各五行的梯度
        gradients = self._calculate_gradients(
            bazi, wuxing_values, ratio, attractor_pos
        )

        # 5. 排序得到喜用神
        yongshen_ranked = sorted(
            gradients.keys(),
            key=lambda e: gradients[e],
            reverse=True  # 梯度越正（能降低势能越多）越好
        )

        return PotentialEnergyResult(
            day_master_ratio=ratio,
            attractor_type=attractor_type,
            attractor_position=attractor_pos,
            total_energy=E_total,
            balance_energy=E_balance,
            flow_energy=E_flow,
            season_energy=E_season,
            gradients=gradients,
            yongshen_ranked=yongshen_ranked,
        )

    def _find_attractor(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
        current_ratio: float,
    ) -> Tuple[AttractorType, float]:
        """
        找到命局的吸引子

        关键逻辑：
        - 如果日主有有效根气（未被吸收）→ 普通格局，吸引子在 0.5
        - 如果日主无根或根被吸收 → 从格，吸引子在 0.0
        - 如果日主极强 → 专旺格，吸引子在 1.0

        注意：假从格的吸引子也在 0（顺势而从）
        """
        has_effective_root, absorbed_info = self._check_effective_root(bazi)

        # 专旺格判断
        if current_ratio > 0.70:
            if self._check_zhuan_wang(bazi, wuxing_values):
                return AttractorType.ZHUAN_WANG, 1.0

        # 从格判断（真从或假从）
        # 假从格：有根但被吸收，current_ratio < 0.25
        # 真从格：无根，current_ratio < 0.15
        if not has_effective_root:
            if current_ratio < 0.25:
                return AttractorType.CONG_GE, 0.0

        # 默认普通格局
        return AttractorType.NORMAL, 0.5

    def _check_effective_root(self, bazi: BaZi) -> Tuple[bool, List[str]]:
        """
        检查日主是否有有效根气

        返回: (是否有有效根, 吸收信息列表)

        有效根 = 未被三会/三合局吸收的根
        """
        from .branch_analyzer import BranchAnalyzer

        day_master = bazi.day_master.wuxing
        peer = day_master
        support = day_master.generated_by

        # 检测三会/三合局
        branch_analyzer = BranchAnalyzer()
        branch_result = branch_analyzer.analyze(bazi)

        # 找被吸收的地支
        absorbed_branches = set()
        absorbed_element = None
        for combo in branch_result.san_hui + branch_result.san_he:
            if combo.element and combo.element != day_master:
                absorbed_branches.update(combo.branches)
                absorbed_element = combo.element

        # 检查天干是否有帮助
        for pillar in bazi.pillars:
            if pillar != bazi.day_pillar:
                if pillar.stem.wuxing in (peer, support):
                    return True, []  # 天干有帮助，有有效根

        # 检查藏干根气
        absorbed_info = []
        has_unabsorbed_root = False

        for pillar in bazi.pillars:
            branch_chinese = pillar.branch.chinese
            for hidden_stem, ratio in pillar.hidden_stems.items():
                if ratio >= 0.3:  # 本气或中气
                    if hidden_stem.wuxing in (peer, support):
                        if branch_chinese in absorbed_branches:
                            # 根被吸收
                            absorbed_info.append(
                                f"{branch_chinese}藏{hidden_stem.chinese}被{absorbed_element.chinese if absorbed_element else ''}局吸收"
                            )
                        else:
                            # 有效根
                            has_unabsorbed_root = True

        return has_unabsorbed_root, absorbed_info

    def _check_zhuan_wang(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
    ) -> bool:
        """检查是否专旺格"""
        day_master = bazi.day_master.wuxing
        total = sum(wuxing_values.values())
        dm_ratio = wuxing_values.get(day_master, 0) / total if total > 0 else 0

        # 简单判断：日主五行占比超过 50%
        return dm_ratio > 0.50

    def _calculate_balance_energy(
        self,
        ratio: float,
        attractor: float,
    ) -> float:
        """
        计算平衡项势能

        E_balance = (ratio - attractor)²

        ratio 越接近 attractor，势能越低
        """
        return (ratio - attractor) ** 2

    def _calculate_flow_energy(
        self,
        wuxing_values: Dict[WuXing, float],
    ) -> float:
        """
        计算流通项势能

        基于五行相互作用矩阵
        E_flow = -Σᵢⱼ Wᵢⱼ xᵢ xⱼ

        流通顺畅时（相生多）能量低
        阻塞时（相克多）能量高
        """
        total = sum(wuxing_values.values())
        if total == 0:
            return 0.0

        # 归一化
        normalized = {e: v / total for e, v in wuxing_values.items()}

        energy = 0.0
        for e1 in WuXing:
            for e2 in WuXing:
                if e1 != e2:
                    w = self.interaction_matrix.get((e1, e2), 0)
                    x1 = normalized.get(e1, 0)
                    x2 = normalized.get(e2, 0)
                    energy -= w * x1 * x2  # 负号：相生降低能量

        return energy

    def _calculate_season_energy(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
    ) -> float:
        """
        计算调候项势能

        - 冬天缺火 → 势能高
        - 夏天缺水 → 势能高
        """
        month_branch = bazi.month_pillar.branch.chinese
        total = sum(wuxing_values.values())
        if total == 0:
            return 0.0

        # 冬月 (亥子丑)
        winter_months = {'亥', '子', '丑'}
        # 夏月 (巳午未)
        summer_months = {'巳', '午', '未'}

        fire_ratio = wuxing_values.get(WuXing.FIRE, 0) / total
        water_ratio = wuxing_values.get(WuXing.WATER, 0) / total

        energy = 0.0

        if month_branch in winter_months:
            # 冬天需要火，火越少势能越高
            energy += (0.2 - fire_ratio) ** 2 if fire_ratio < 0.2 else 0
        elif month_branch in summer_months:
            # 夏天需要水，水越少势能越高
            energy += (0.2 - water_ratio) ** 2 if water_ratio < 0.2 else 0

        return energy

    def _calculate_gradients(
        self,
        bazi: BaZi,
        wuxing_values: Dict[WuXing, float],
        current_ratio: float,
        attractor: float,
    ) -> Dict[WuXing, float]:
        """
        计算各五行的梯度

        梯度 = 加入该五行后势能的变化
        负梯度（势能下降）= 喜用神
        正梯度（势能上升）= 忌神

        返回：正值表示喜用神（能降低势能）
        """
        day_master = bazi.day_master.wuxing
        gradients = {}

        # 计算当前势能
        current_E = self._calculate_balance_energy(current_ratio, attractor)

        for element in WuXing:
            # 模拟加入该五行后的新比例
            new_ratio = self._simulate_add_element(
                current_ratio, element, day_master
            )

            # 计算新势能
            new_E = self._calculate_balance_energy(new_ratio, attractor)

            # 梯度 = 当前势能 - 新势能（正值表示势能下降，是喜用神）
            gradients[element] = current_E - new_E

        return gradients

    def _simulate_add_element(
        self,
        current_ratio: float,
        element: WuXing,
        day_master: WuXing,
    ) -> float:
        """
        模拟加入某五行后日主比例的变化

        简化假设：
        - 比劫（同五行）增加日主阵营
        - 印绶（生我）增加日主阵营
        - 其他降低日主阵营比例
        """
        peer = day_master
        support = day_master.generated_by

        # 假设加入的五行占总量的 10%
        delta = 0.10

        if element == peer or element == support:
            # 有利五行，增加日主比例
            new_ratio = (current_ratio + delta) / (1 + delta)
        else:
            # 不利五行，稀释日主比例
            new_ratio = current_ratio / (1 + delta)

        return max(0.0, min(1.0, new_ratio))

    def visualize_potential_curve(
        self,
        attractor: float = 0.5,
        title: str = "势能曲线",
    ) -> str:
        """
        生成势能曲线的 ASCII 可视化

        用于验证势能函数的形状
        """
        width = 60
        height = 15

        # 计算各点的势能
        points = []
        for i in range(width):
            ratio = i / (width - 1)
            E = self._calculate_balance_energy(ratio, attractor)
            points.append((ratio, E))

        # 找到最大势能用于归一化
        max_E = max(p[1] for p in points)

        # 生成 ASCII 图
        lines = [f"\n{title} (吸引子位置: {attractor:.0%})"]
        lines.append("势能")
        lines.append("  │")

        for row in range(height - 1, -1, -1):
            threshold = row / (height - 1) * max_E
            line = "  │"
            for ratio, E in points:
                if E >= threshold:
                    line += "█"
                else:
                    line += " "
            lines.append(line)

        # X 轴
        lines.append("  └" + "─" * width)
        lines.append("   0%                    50%                   100%")
        lines.append("                    日主阵营比例")

        return "\n".join(lines)


def run_experiment():
    """运行实验"""
    from ..models import BaZi
    from .wuxing_calculator import WuXingCalculator
    from .branch_analyzer import BranchAnalyzer

    print("=" * 60)
    print("八字势能理论实验 (BaZi Potential Energy Experiment)")
    print("=" * 60)

    calculator = PotentialEnergyCalculator()
    wuxing_calc = WuXingCalculator()
    branch_analyzer = BranchAnalyzer()

    # 测试案例
    test_cases = [
        ("姚明", "庚申乙酉戊子壬戌", "假从儿格，预期吸引子接近0%"),
        ("文天祥", "丙子癸巳丙午丁酉", "身强火旺，预期吸引子在50%"),
        ("身弱水", "庚午己卯癸巳甲寅", "身弱，预期吸引子在50%，喜金水"),
    ]

    for name, bazi_str, description in test_cases:
        print(f"\n{'─' * 60}")
        print(f"案例：{name}")
        print(f"八字：{bazi_str}")
        print(f"说明：{description}")
        print("─" * 60)

        bazi = BaZi.from_chinese(bazi_str)
        branch_result = branch_analyzer.analyze(bazi)
        wuxing_result = wuxing_calc.calculate_strength_with_relations(bazi, branch_result)

        result = calculator.calculate(bazi, wuxing_result.raw_values)

        print(f"\n日主：{bazi.day_master.chinese} ({bazi.day_master.wuxing.chinese})")
        print(f"日主阵营比例：{result.day_master_ratio:.1%}")
        print(f"吸引子类型：{result.attractor_type.value}")
        print(f"吸引子位置：{result.attractor_position:.0%}")
        print(f"\n势能分解：")
        print(f"  平衡项：{result.balance_energy:.4f}")
        print(f"  流通项：{result.flow_energy:.4f}")
        print(f"  调候项：{result.season_energy:.4f}")
        print(f"  总势能：{result.total_energy:.4f}")
        print(f"\n喜用神排名（势能梯度）：")
        for i, element in enumerate(result.yongshen_ranked):
            gradient = result.gradients[element]
            sign = "+" if gradient > 0 else ""
            role = "喜" if gradient > 0 else "忌"
            print(f"  {i+1}. {element.chinese} ({sign}{gradient:.4f}) - {role}")

    # 可视化不同吸引子的势能曲线
    print("\n" + "=" * 60)
    print("势能曲线可视化")
    print("=" * 60)

    print(calculator.visualize_potential_curve(0.5, "普通格局势能曲线"))
    print(calculator.visualize_potential_curve(0.0, "从格势能曲线"))
    print(calculator.visualize_potential_curve(1.0, "专旺格势能曲线"))


if __name__ == "__main__":
    run_experiment()
