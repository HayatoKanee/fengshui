"""
干支关系分析服务 (GanZhi Interaction Service)

分析天干地支之间的合会冲克刑关系，计算对五行力量的影响。

关键点：
- 合冲刑害影响的是**具体位置**的天干/地支
- 天干被合/冲 → 影响该天干的力量
- 地支被合/冲 → 影响该地支藏干的力量

力量等级排序: 三会 > 三合 > 相冲 > 相刑 > 六合 > 半合 > 相害 > 相破

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ..models import (
    WuXing,
    TianGan,
    DiZhi,
    BaZi,
    Pillar,
    RELATIONS,
)


# =============================================================================
# 位置枚举
# =============================================================================

class PillarPosition(Enum):
    """柱位"""
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"


# =============================================================================
# 力量修正常量
# =============================================================================

# 天干合化/合绊
STEM_COMBINE_TRANSFORM_REDUCTION = 0.95  # 真合化：原五行减少95%
STEM_COMBINE_BINDNG_REDUCTION = 0.50     # 合绊：原五行减少50%

# 地支六合
BRANCH_LIU_HE_TRANSFORM_REDUCTION = 0.90  # 真合化：藏干减少90%
BRANCH_LIU_HE_BINDING_REDUCTION = 0.40    # 合绊：藏干减少40%

# 地支相冲
BRANCH_CHONG_REDUCTION = 0.50  # 相冲：双方藏干减少50%

# 地支相刑
BRANCH_XING_REDUCTION = 0.30   # 相刑：藏干减少30%

# 地支相害
BRANCH_HAI_REDUCTION = 0.15    # 相害：藏干减少15%


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class StemInteraction:
    """天干关系"""
    interaction_type: str  # "wu_he_hua" (真合化), "wu_he_ban" (合绊), "chong" (冲)
    position1: PillarPosition
    position2: PillarPosition
    stem1: TianGan
    stem2: TianGan
    hua_shen: Optional[WuXing] = None  # 合化时的化神
    reduction1: float = 0.0  # stem1 的力量减少比例
    reduction2: float = 0.0  # stem2 的力量减少比例


@dataclass
class BranchInteraction:
    """地支关系"""
    interaction_type: str  # "san_hui", "san_he", "liu_he", "ban_he", "chong", "xing", "hai"
    positions: List[PillarPosition]
    branches: List[DiZhi]
    hua_shen: Optional[WuXing] = None
    reductions: Dict[PillarPosition, float] = field(default_factory=dict)  # 每个位置的减少比例
    bonus_wuxing: Optional[WuXing] = None  # 合局增强的五行
    bonus_value: float = 0.0  # 增强值


@dataclass
class PositionModifier:
    """
    位置修正器

    记录某个位置（年/月/日/时）的天干或地支藏干的力量修正
    """
    position: PillarPosition
    stem_reduction: float = 0.0        # 天干力量减少比例 (0-1)
    hidden_stem_reduction: float = 0.0  # 藏干力量减少比例 (0-1)
    reasons: List[str] = field(default_factory=list)


@dataclass
class GanZhiInteractions:
    """干支关系分析结果"""
    stem_interactions: List[StemInteraction] = field(default_factory=list)
    branch_interactions: List[BranchInteraction] = field(default_factory=list)

    # 每个位置的力量修正
    position_modifiers: Dict[PillarPosition, PositionModifier] = field(default_factory=dict)

    # 额外增加的五行力量（来自合局成功）
    wuxing_bonus: Dict[WuXing, float] = field(default_factory=dict)

    def get_stem_reduction(self, position: PillarPosition) -> float:
        """获取某位置天干的减少比例"""
        if position in self.position_modifiers:
            return self.position_modifiers[position].stem_reduction
        return 0.0

    def get_hidden_stem_reduction(self, position: PillarPosition) -> float:
        """获取某位置藏干的减少比例"""
        if position in self.position_modifiers:
            return self.position_modifiers[position].hidden_stem_reduction
        return 0.0


class GanZhiInteractionService:
    """
    干支关系分析服务

    精确计算每个位置的天干/地支受到的影响
    """

    def analyze(self, bazi: BaZi) -> GanZhiInteractions:
        """分析八字中的所有干支关系"""
        result = GanZhiInteractions()
        result.wuxing_bonus = {element: 0.0 for element in WuXing}

        # 初始化位置修正器
        for pos in PillarPosition:
            result.position_modifiers[pos] = PositionModifier(position=pos)

        # 收集天干地支
        stems = self._collect_stems(bazi)
        branches = self._collect_branches(bazi)
        month_branch = bazi.month_pillar.branch

        # 按优先级检测关系
        # 1. 天干五合
        self._detect_stem_combinations(stems, month_branch, result)

        # 2. 地支三会 (最强)
        self._detect_san_hui(branches, result)

        # 3. 地支三合
        self._detect_san_he(branches, month_branch, result)

        # 4. 地支六合
        self._detect_liu_he(branches, month_branch, result)

        # 5. 地支相冲 (可破合)
        self._detect_branch_clashes(branches, result)

        # 6. 地支相刑
        self._detect_branch_punishments(branches, result)

        # 7. 地支相害
        self._detect_branch_harms(branches, result)

        return result

    def _collect_stems(self, bazi: BaZi) -> Dict[PillarPosition, TianGan]:
        """收集天干"""
        return {
            PillarPosition.YEAR: bazi.year_pillar.stem,
            PillarPosition.MONTH: bazi.month_pillar.stem,
            PillarPosition.DAY: bazi.day_pillar.stem,
            PillarPosition.HOUR: bazi.hour_pillar.stem,
        }

    def _collect_branches(self, bazi: BaZi) -> Dict[PillarPosition, DiZhi]:
        """收集地支"""
        return {
            PillarPosition.YEAR: bazi.year_pillar.branch,
            PillarPosition.MONTH: bazi.month_pillar.branch,
            PillarPosition.DAY: bazi.day_pillar.branch,
            PillarPosition.HOUR: bazi.hour_pillar.branch,
        }

    # =========================================================================
    # 天干五合
    # =========================================================================

    def _detect_stem_combinations(
        self,
        stems: Dict[PillarPosition, TianGan],
        month_branch: DiZhi,
        result: GanZhiInteractions,
    ) -> None:
        """检测天干五合（只检测相邻天干）"""
        positions = [PillarPosition.YEAR, PillarPosition.MONTH, PillarPosition.DAY, PillarPosition.HOUR]

        for i in range(len(positions) - 1):
            pos1, pos2 = positions[i], positions[i + 1]
            stem1, stem2 = stems[pos1], stems[pos2]

            # 检查五合
            hua_shen = self._get_stem_hua_shen(stem1, stem2)
            if hua_shen is None:
                continue

            # 判断真合化还是合绊
            is_transformed = self._check_stem_transform(
                stem1, stem2, hua_shen, month_branch, stems
            )

            if is_transformed:
                reduction = STEM_COMBINE_TRANSFORM_REDUCTION
                interaction_type = "wu_he_hua"
            else:
                reduction = STEM_COMBINE_BINDNG_REDUCTION
                interaction_type = "wu_he_ban"

            interaction = StemInteraction(
                interaction_type=interaction_type,
                position1=pos1,
                position2=pos2,
                stem1=stem1,
                stem2=stem2,
                hua_shen=hua_shen if is_transformed else None,
                reduction1=reduction,
                reduction2=reduction,
            )
            result.stem_interactions.append(interaction)

            # 更新位置修正
            mod1 = result.position_modifiers[pos1]
            mod2 = result.position_modifiers[pos2]
            mod1.stem_reduction = max(mod1.stem_reduction, reduction)
            mod2.stem_reduction = max(mod2.stem_reduction, reduction)
            mod1.reasons.append(f"{stem1.chinese}{stem2.chinese}合")
            mod2.reasons.append(f"{stem1.chinese}{stem2.chinese}合")

            # 真合化时，化神获得力量
            if is_transformed:
                # 化神增强值 = 两个天干原值之和 × 转化比例
                result.wuxing_bonus[hua_shen] += 36.0 * 2 * 0.8  # 约57.6

    def _get_stem_hua_shen(self, stem1: TianGan, stem2: TianGan) -> Optional[WuXing]:
        """获取天干五合的化神"""
        pair = (stem1, stem2)
        reverse = (stem2, stem1)
        if pair in RELATIONS.WU_HE_HUA:
            return RELATIONS.WU_HE_HUA[pair]
        if reverse in RELATIONS.WU_HE_HUA:
            return RELATIONS.WU_HE_HUA[reverse]
        return None

    def _check_stem_transform(
        self,
        stem1: TianGan,
        stem2: TianGan,
        hua_shen: WuXing,
        month_branch: DiZhi,
        all_stems: Dict[PillarPosition, TianGan],
    ) -> bool:
        """检查天干是否真正合化"""
        # 1. 化神得令
        month_wuxing = month_branch.wuxing
        # 检查月支藏干本气
        month_hidden = month_branch.hidden_stems
        main_hidden = max(month_hidden, key=month_hidden.get)
        main_hidden_wuxing = main_hidden.wuxing

        hua_shen_deling = (
            hua_shen == month_wuxing or
            hua_shen == main_hidden_wuxing or
            hua_shen == month_wuxing.generates
        )
        if not hua_shen_deling:
            return False

        # 2. 无妒合
        stem_list = list(all_stems.values())
        if stem_list.count(stem1) > 1 or stem_list.count(stem2) > 1:
            return False

        # 3. 化神无克制
        for stem in all_stems.values():
            if stem not in (stem1, stem2):
                if stem.wuxing.overcomes == hua_shen:
                    return False

        return True

    # =========================================================================
    # 地支三会
    # =========================================================================

    def _detect_san_hui(
        self,
        branches: Dict[PillarPosition, DiZhi],
        result: GanZhiInteractions,
    ) -> None:
        """检测地支三会方"""
        branch_set = set(branches.values())
        pos_map = {v: k for k, v in branches.items()}

        for hua_shen, required in RELATIONS.SAN_HUI.items():
            if required.issubset(branch_set):
                positions = [pos_map[b] for b in required if b in pos_map]
                branch_list = list(required)

                interaction = BranchInteraction(
                    interaction_type="san_hui",
                    positions=positions,
                    branches=branch_list,
                    hua_shen=hua_shen,
                    bonus_wuxing=hua_shen,
                    bonus_value=72.0,  # 三会最强
                )
                result.branch_interactions.append(interaction)
                result.wuxing_bonus[hua_shen] += 72.0

    # =========================================================================
    # 地支三合
    # =========================================================================

    def _detect_san_he(
        self,
        branches: Dict[PillarPosition, DiZhi],
        month_branch: DiZhi,
        result: GanZhiInteractions,
    ) -> None:
        """检测地支三合局"""
        branch_set = set(branches.values())
        pos_map = {v: k for k, v in branches.items()}

        for hua_shen, required in RELATIONS.SAN_HE.items():
            present = branch_set & required
            if len(present) == 3:
                # 完整三合
                positions = [pos_map[b] for b in present if b in pos_map]
                is_transformed = (hua_shen == month_branch.wuxing)
                bonus = 60.0 if is_transformed else 45.0

                interaction = BranchInteraction(
                    interaction_type="san_he",
                    positions=positions,
                    branches=list(present),
                    hua_shen=hua_shen,
                    bonus_wuxing=hua_shen,
                    bonus_value=bonus,
                )
                result.branch_interactions.append(interaction)
                result.wuxing_bonus[hua_shen] += bonus

            elif len(present) == 2:
                # 半合
                positions = [pos_map[b] for b in present if b in pos_map]
                interaction = BranchInteraction(
                    interaction_type="ban_he",
                    positions=positions,
                    branches=list(present),
                    hua_shen=hua_shen,
                    bonus_wuxing=hua_shen,
                    bonus_value=30.0,
                )
                result.branch_interactions.append(interaction)
                result.wuxing_bonus[hua_shen] += 30.0

    # =========================================================================
    # 地支六合
    # =========================================================================

    def _detect_liu_he(
        self,
        branches: Dict[PillarPosition, DiZhi],
        month_branch: DiZhi,
        result: GanZhiInteractions,
    ) -> None:
        """检测地支六合"""
        positions = list(branches.keys())
        branch_list = list(branches.values())
        branch_set = set(branch_list)

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pos1, pos2 = positions[i], positions[j]
                b1, b2 = branch_list[i], branch_list[j]

                hua_shen = self._get_branch_liu_he_hua_shen(b1, b2)
                if hua_shen is None:
                    continue

                # 检查是否被冲破
                if self._is_liu_he_broken(b1, b2, branch_set):
                    continue

                is_transformed = (hua_shen == month_branch.wuxing)

                if is_transformed:
                    reduction = BRANCH_LIU_HE_TRANSFORM_REDUCTION
                    interaction_type = "liu_he_hua"
                else:
                    reduction = BRANCH_LIU_HE_BINDING_REDUCTION
                    interaction_type = "liu_he_ban"

                interaction = BranchInteraction(
                    interaction_type=interaction_type,
                    positions=[pos1, pos2],
                    branches=[b1, b2],
                    hua_shen=hua_shen if is_transformed else None,
                    reductions={pos1: reduction, pos2: reduction},
                    bonus_wuxing=hua_shen if is_transformed else None,
                    bonus_value=36.0 if is_transformed else 20.0,
                )
                result.branch_interactions.append(interaction)

                # 更新藏干减少
                mod1 = result.position_modifiers[pos1]
                mod2 = result.position_modifiers[pos2]
                mod1.hidden_stem_reduction = max(mod1.hidden_stem_reduction, reduction)
                mod2.hidden_stem_reduction = max(mod2.hidden_stem_reduction, reduction)
                mod1.reasons.append(f"{b1.chinese}{b2.chinese}合")
                mod2.reasons.append(f"{b1.chinese}{b2.chinese}合")

                if is_transformed:
                    result.wuxing_bonus[hua_shen] += 36.0

    def _get_branch_liu_he_hua_shen(self, b1: DiZhi, b2: DiZhi) -> Optional[WuXing]:
        """获取地支六合的化神"""
        pair = (b1, b2)
        reverse = (b2, b1)
        if pair in RELATIONS.LIU_HE_HUA:
            return RELATIONS.LIU_HE_HUA[pair]
        if reverse in RELATIONS.LIU_HE_HUA:
            return RELATIONS.LIU_HE_HUA[reverse]
        return None

    def _is_liu_he_broken(self, b1: DiZhi, b2: DiZhi, all_branches: Set[DiZhi]) -> bool:
        """检查六合是否被冲破"""
        for clash_pair in RELATIONS.ZHI_CHONG:
            if b1 in clash_pair:
                other = clash_pair[0] if clash_pair[1] == b1 else clash_pair[1]
                if other in all_branches and other != b2:
                    return True
            if b2 in clash_pair:
                other = clash_pair[0] if clash_pair[1] == b2 else clash_pair[1]
                if other in all_branches and other != b1:
                    return True
        return False

    # =========================================================================
    # 地支相冲
    # =========================================================================

    def _detect_branch_clashes(
        self,
        branches: Dict[PillarPosition, DiZhi],
        result: GanZhiInteractions,
    ) -> None:
        """检测地支相冲"""
        positions = list(branches.keys())
        branch_list = list(branches.values())

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pos1, pos2 = positions[i], positions[j]
                b1, b2 = branch_list[i], branch_list[j]

                if self._is_clash(b1, b2):
                    interaction = BranchInteraction(
                        interaction_type="chong",
                        positions=[pos1, pos2],
                        branches=[b1, b2],
                        reductions={
                            pos1: BRANCH_CHONG_REDUCTION,
                            pos2: BRANCH_CHONG_REDUCTION,
                        },
                    )
                    result.branch_interactions.append(interaction)

                    # 更新藏干减少
                    mod1 = result.position_modifiers[pos1]
                    mod2 = result.position_modifiers[pos2]
                    mod1.hidden_stem_reduction = max(mod1.hidden_stem_reduction, BRANCH_CHONG_REDUCTION)
                    mod2.hidden_stem_reduction = max(mod2.hidden_stem_reduction, BRANCH_CHONG_REDUCTION)
                    mod1.reasons.append(f"{b1.chinese}{b2.chinese}冲")
                    mod2.reasons.append(f"{b1.chinese}{b2.chinese}冲")

    def _is_clash(self, b1: DiZhi, b2: DiZhi) -> bool:
        """检查是否相冲"""
        return (b1, b2) in RELATIONS.ZHI_CHONG or (b2, b1) in RELATIONS.ZHI_CHONG

    # =========================================================================
    # 地支相刑
    # =========================================================================

    def _detect_branch_punishments(
        self,
        branches: Dict[PillarPosition, DiZhi],
        result: GanZhiInteractions,
    ) -> None:
        """检测地支相刑"""
        branch_set = set(branches.values())
        branch_list = list(branches.values())
        pos_map = {v: k for k, v in branches.items()}

        # 无恩之刑 (寅巳申)
        for xing_set in RELATIONS.XING_WU_EN:
            if xing_set.issubset(branch_set):
                positions = [pos_map[b] for b in xing_set if b in pos_map]
                interaction = BranchInteraction(
                    interaction_type="xing_wu_en",
                    positions=positions,
                    branches=list(xing_set),
                    reductions={p: BRANCH_XING_REDUCTION for p in positions},
                )
                result.branch_interactions.append(interaction)
                for pos in positions:
                    mod = result.position_modifiers[pos]
                    mod.hidden_stem_reduction = max(mod.hidden_stem_reduction, BRANCH_XING_REDUCTION)
                    mod.reasons.append("寅巳申刑")

        # 恃势之刑 (丑戌未)
        for xing_set in RELATIONS.XING_CHI_SHI:
            if xing_set.issubset(branch_set):
                positions = [pos_map[b] for b in xing_set if b in pos_map]
                interaction = BranchInteraction(
                    interaction_type="xing_chi_shi",
                    positions=positions,
                    branches=list(xing_set),
                    reductions={p: BRANCH_XING_REDUCTION for p in positions},
                )
                result.branch_interactions.append(interaction)
                for pos in positions:
                    mod = result.position_modifiers[pos]
                    mod.hidden_stem_reduction = max(mod.hidden_stem_reduction, BRANCH_XING_REDUCTION)
                    mod.reasons.append("丑戌未刑")

        # 无礼之刑 (子卯)
        for xing_pair in RELATIONS.XING_WU_LI:
            if xing_pair[0] in branch_set and xing_pair[1] in branch_set:
                positions = [pos_map[xing_pair[0]], pos_map[xing_pair[1]]]
                interaction = BranchInteraction(
                    interaction_type="xing_wu_li",
                    positions=positions,
                    branches=list(xing_pair),
                    reductions={p: BRANCH_XING_REDUCTION for p in positions},
                )
                result.branch_interactions.append(interaction)
                for pos in positions:
                    mod = result.position_modifiers[pos]
                    mod.hidden_stem_reduction = max(mod.hidden_stem_reduction, BRANCH_XING_REDUCTION)
                    mod.reasons.append("子卯刑")

        # 自刑 (辰午酉亥见两个)
        for branch in RELATIONS.XING_ZI:
            if branch_list.count(branch) >= 2:
                positions = [p for p, b in branches.items() if b == branch]
                interaction = BranchInteraction(
                    interaction_type="zi_xing",
                    positions=positions,
                    branches=[branch],
                    reductions={p: BRANCH_XING_REDUCTION for p in positions},
                )
                result.branch_interactions.append(interaction)
                for pos in positions:
                    mod = result.position_modifiers[pos]
                    mod.hidden_stem_reduction = max(mod.hidden_stem_reduction, BRANCH_XING_REDUCTION)
                    mod.reasons.append(f"{branch.chinese}自刑")

    # =========================================================================
    # 地支相害
    # =========================================================================

    def _detect_branch_harms(
        self,
        branches: Dict[PillarPosition, DiZhi],
        result: GanZhiInteractions,
    ) -> None:
        """检测地支相害"""
        branch_set = set(branches.values())
        pos_map = {v: k for k, v in branches.items()}

        for harm_pair in RELATIONS.ZHI_HAI:
            if harm_pair[0] in branch_set and harm_pair[1] in branch_set:
                pos1 = pos_map[harm_pair[0]]
                pos2 = pos_map[harm_pair[1]]
                interaction = BranchInteraction(
                    interaction_type="hai",
                    positions=[pos1, pos2],
                    branches=list(harm_pair),
                    reductions={
                        pos1: BRANCH_HAI_REDUCTION,
                        pos2: BRANCH_HAI_REDUCTION,
                    },
                )
                result.branch_interactions.append(interaction)

                mod1 = result.position_modifiers[pos1]
                mod2 = result.position_modifiers[pos2]
                mod1.hidden_stem_reduction = max(mod1.hidden_stem_reduction, BRANCH_HAI_REDUCTION)
                mod2.hidden_stem_reduction = max(mod2.hidden_stem_reduction, BRANCH_HAI_REDUCTION)
                mod1.reasons.append(f"{harm_pair[0].chinese}{harm_pair[1].chinese}害")
                mod2.reasons.append(f"{harm_pair[0].chinese}{harm_pair[1].chinese}害")
