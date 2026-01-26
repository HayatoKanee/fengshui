"""
Branch Relations Analysis Model.

Domain model for analyzing relationships between earthly branches in BaZi.
Includes 刑、害、破、冲、合、三合、三会、四库 etc.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from .elements import WuXing


class RelationType(Enum):
    """Types of branch relationships."""
    # 合 - Harmonies
    LIU_HE = "六合"           # Six Harmonies (pairs)
    SAN_HE = "三合"           # Three Harmonies (full)
    BAN_HE = "半合"           # Half Harmony (partial)
    SAN_HUI = "三会"          # Directional Combination

    # 冲 - Clashes
    CHONG = "冲"              # Clash

    # 刑 - Punishments
    WU_EN_XING = "无恩之刑"    # Ungrateful punishment (寅巳申)
    CHI_SHI_XING = "持势之刑"  # Bullying punishment (丑戌未)
    WU_LI_XING = "无礼之刑"    # Disrespectful punishment (子卯)
    ZI_XING = "自刑"          # Self-punishment (辰午酉亥)

    # 害 - Harms
    HAI = "害"                # Harm

    # 破 - Breaks
    PO = "破"                 # Break

    # 库 - Storage
    SI_KU = "四库"            # Four Graveyards


@dataclass(frozen=True)
class BranchRelation:
    """A single branch relationship found in the chart."""
    relation_type: RelationType
    branches: Tuple[str, ...]      # The branches involved
    pillars: Tuple[str, ...]       # Which pillars (年/月/日/时)
    element: Optional[WuXing] = None  # Resulting element for 合局
    description: str = ""          # Human-readable description


@dataclass
class BranchRelationsAnalysis:
    """
    Complete analysis of branch relationships in a BaZi chart.

    Contains all detected relationships categorized by type.
    """
    # All detected relations
    relations: List[BranchRelation] = field(default_factory=list)

    # Quick access by type
    liu_he: List[BranchRelation] = field(default_factory=list)      # 六合
    san_he: List[BranchRelation] = field(default_factory=list)      # 三合
    ban_he: List[BranchRelation] = field(default_factory=list)      # 半合
    san_hui: List[BranchRelation] = field(default_factory=list)     # 三会
    chong: List[BranchRelation] = field(default_factory=list)       # 冲
    xing: List[BranchRelation] = field(default_factory=list)        # 刑 (all types)
    hai: List[BranchRelation] = field(default_factory=list)         # 害
    po: List[BranchRelation] = field(default_factory=list)          # 破
    si_ku: List[BranchRelation] = field(default_factory=list)       # 四库

    # Specific punishment types
    zi_xing: List[BranchRelation] = field(default_factory=list)     # 自刑

    @property
    def has_san_xing(self) -> bool:
        """Check if there's a complete three-way punishment (三刑)."""
        return any(
            r.relation_type in (RelationType.WU_EN_XING, RelationType.CHI_SHI_XING)
            and len(r.branches) == 3
            for r in self.xing
        )

    @property
    def has_zi_xing(self) -> bool:
        """Check if there's self-punishment (自刑)."""
        return len(self.zi_xing) > 0

    @property
    def has_complete_san_he(self) -> bool:
        """Check if there's a complete three harmony (三合局)."""
        return len(self.san_he) > 0

    @property
    def has_complete_san_hui(self) -> bool:
        """Check if there's a complete directional combination (三会局)."""
        return len(self.san_hui) > 0

    @property
    def punishment_count(self) -> int:
        """Total number of punishment relationships."""
        return len(self.xing)

    @property
    def harmony_count(self) -> int:
        """Total number of harmony relationships (六合+三合+半合+三会)."""
        return len(self.liu_he) + len(self.san_he) + len(self.ban_he) + len(self.san_hui)

    @property
    def conflict_count(self) -> int:
        """Total number of conflict relationships (冲+刑+害+破)."""
        return len(self.chong) + len(self.xing) + len(self.hai) + len(self.po)

    def get_personality_traits(self) -> List[str]:
        """Get personality trait descriptions based on detected relations."""
        traits = []

        # 三刑
        for rel in self.xing:
            if rel.relation_type == RelationType.WU_EN_XING:
                traits.append("以怨报德、薄情寡义、叛逆抗上")
            elif rel.relation_type == RelationType.CHI_SHI_XING:
                traits.append("恃势凌人、刚愎自用")
            elif rel.relation_type == RelationType.WU_LI_XING:
                traits.append("不守礼法、易犯口舌")
            elif rel.relation_type == RelationType.ZI_XING:
                if '辰' in rel.branches:
                    traits.append("自我封闭")
                elif '午' in rel.branches:
                    traits.append("急躁冲动")
                elif '酉' in rel.branches:
                    traits.append("自我伤害倾向")
                elif '亥' in rel.branches:
                    traits.append("钻牛角尖、完美主义")

        # 三合/三会
        if self.has_complete_san_he or self.has_complete_san_hui:
            traits.append("气势强大、运势集中")

        # 害
        if self.hai:
            traits.append("易犯小人、人际关系需注意")

        return traits

    def get_fortune_impacts(self) -> List[str]:
        """Get fortune impact descriptions based on detected relations."""
        impacts = []

        # 刑
        if self.has_san_xing:
            impacts.append("三刑齐全，流年大运配合时需防灾祸")

        for rel in self.xing:
            if rel.relation_type == RelationType.WU_EN_XING:
                impacts.append("寅巳申三刑：注意车祸、官非、手术")
            elif rel.relation_type == RelationType.CHI_SHI_XING:
                impacts.append("丑戌未三刑：注意刑伤、人事纠纷")

        # 自刑
        if self.has_zi_xing:
            impacts.append("自刑：内心矛盾、自我消耗")

        # 害
        for rel in self.hai:
            impacts.append(f"{rel.branches[0]}{rel.branches[1]}害：六亲有损、小人暗算")

        # 破
        for rel in self.po:
            impacts.append(f"{rel.branches[0]}{rel.branches[1]}破：破败之象、成中有败")

        # 三合/三会
        for rel in self.san_he:
            if rel.element:
                impacts.append(f"三合{rel.element.value}局：{rel.element.value}五行力量增强")

        for rel in self.san_hui:
            if rel.element:
                impacts.append(f"三会{rel.element.value}局：方位之气汇聚，{rel.element.value}力量极强")

        return impacts


# 四库定义 - Four Graveyards
SI_KU_BRANCHES: Dict[str, WuXing] = {
    '辰': WuXing.WATER,   # 水库
    '戌': WuXing.FIRE,    # 火库
    '丑': WuXing.METAL,   # 金库
    '未': WuXing.WOOD,    # 木库
}

SI_KU_SET: FrozenSet[str] = frozenset(SI_KU_BRANCHES.keys())
