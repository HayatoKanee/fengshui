"""
Branch Relations Analyzer Service.

Analyzes relationships between earthly branches in a BaZi chart.
Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

from ..models.branch_analysis import (
    BranchRelation,
    BranchRelationsAnalysis,
    RelationType,
    SI_KU_BRANCHES,
    SI_KU_SET,
)
from ..models.elements import WuXing
from ..constants.branch_relations import (
    SAN_HE_TRIOS,
    SAN_HE_PAIRS,
    SAN_HUI_TRIOS,
    XING_TRIOS,
    XING_PAIRS,
    ZI_XING,
    HAI_PAIRS,
    PO_PAIRS,
)
from ..constants.harmony import LIU_HE
from ..constants.clashes import ZHI_XIANG_CHONG

if TYPE_CHECKING:
    from ..models import BaZi


# Pillar names in Chinese
PILLAR_NAMES = ('年', '月', '日', '时')


class BranchAnalyzer:
    """
    Analyzer for branch relationships in BaZi charts.

    Detects all types of relationships:
    - 六合 (Six Harmonies)
    - 三合/半合 (Three Harmonies)
    - 三会 (Directional Combinations)
    - 冲 (Clashes)
    - 刑 (Punishments)
    - 害 (Harms)
    - 破 (Breaks)
    - 四库 (Four Graveyards)
    """

    def analyze(self, bazi: BaZi) -> BranchRelationsAnalysis:
        """
        Analyze all branch relationships in a BaZi chart.

        Args:
            bazi: The BaZi chart to analyze

        Returns:
            BranchRelationsAnalysis containing all detected relationships
        """
        # Get branches with their pillar positions
        branches_with_pillars: List[Tuple[str, str]] = [
            (bazi.year_pillar.branch.chinese, '年'),
            (bazi.month_pillar.branch.chinese, '月'),
            (bazi.day_pillar.branch.chinese, '日'),
            (bazi.hour_pillar.branch.chinese, '时'),
        ]

        branches = [b[0] for b in branches_with_pillars]

        analysis = BranchRelationsAnalysis()

        # Detect all relationships
        self._detect_liu_he(branches_with_pillars, analysis)
        self._detect_san_he(branches, branches_with_pillars, analysis)
        self._detect_san_hui(branches, branches_with_pillars, analysis)
        self._detect_chong(branches_with_pillars, analysis)
        self._detect_xing(branches, branches_with_pillars, analysis)
        self._detect_hai(branches_with_pillars, analysis)
        self._detect_po(branches_with_pillars, analysis)
        self._detect_si_ku(branches_with_pillars, analysis)

        return analysis

    def _detect_liu_he(
        self,
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 六合 (Six Harmonies)."""
        for i, (b1, p1) in enumerate(branches_with_pillars):
            for b2, p2 in branches_with_pillars[i + 1:]:
                if (b1, b2) in LIU_HE:
                    rel = BranchRelation(
                        relation_type=RelationType.LIU_HE,
                        branches=(b1, b2),
                        pillars=(p1, p2),
                        description=f"{p1}{b1}与{p2}{b2}六合"
                    )
                    analysis.liu_he.append(rel)
                    analysis.relations.append(rel)

    def _detect_san_he(
        self,
        branches: List[str],
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 三合 (Three Harmonies) and 半合 (Half Harmonies)."""
        branch_set = frozenset(branches)

        # Check for complete 三合
        for trio, element in SAN_HE_TRIOS.items():
            if trio.issubset(branch_set):
                # Find pillar positions
                pillars = tuple(
                    p for b, p in branches_with_pillars
                    if b in trio
                )
                rel = BranchRelation(
                    relation_type=RelationType.SAN_HE,
                    branches=tuple(sorted(trio)),
                    pillars=pillars,
                    element=element,
                    description=f"{''.join(sorted(trio))}三合{element.value}局"
                )
                analysis.san_he.append(rel)
                analysis.relations.append(rel)

        # Check for 半合 (only if no complete 三合 for that element)
        san_he_elements = {r.element for r in analysis.san_he}

        for i, (b1, p1) in enumerate(branches_with_pillars):
            for b2, p2 in branches_with_pillars[i + 1:]:
                if (b1, b2) in SAN_HE_PAIRS:
                    element = SAN_HE_PAIRS[(b1, b2)]
                    if element not in san_he_elements:
                        rel = BranchRelation(
                            relation_type=RelationType.BAN_HE,
                            branches=(b1, b2),
                            pillars=(p1, p2),
                            element=element,
                            description=f"{p1}{b1}与{p2}{b2}半合{element.value}局"
                        )
                        analysis.ban_he.append(rel)
                        analysis.relations.append(rel)

    def _detect_san_hui(
        self,
        branches: List[str],
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 三会 (Directional Combinations)."""
        branch_set = frozenset(branches)

        for trio, element in SAN_HUI_TRIOS.items():
            if trio.issubset(branch_set):
                pillars = tuple(
                    p for b, p in branches_with_pillars
                    if b in trio
                )
                rel = BranchRelation(
                    relation_type=RelationType.SAN_HUI,
                    branches=tuple(sorted(trio)),
                    pillars=pillars,
                    element=element,
                    description=f"{''.join(sorted(trio))}三会{element.value}局"
                )
                analysis.san_hui.append(rel)
                analysis.relations.append(rel)

    def _detect_chong(
        self,
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 冲 (Clashes)."""
        for i, (b1, p1) in enumerate(branches_with_pillars):
            for b2, p2 in branches_with_pillars[i + 1:]:
                if (b1, b2) in ZHI_XIANG_CHONG:
                    rel = BranchRelation(
                        relation_type=RelationType.CHONG,
                        branches=(b1, b2),
                        pillars=(p1, p2),
                        description=f"{p1}{b1}与{p2}{b2}相冲"
                    )
                    analysis.chong.append(rel)
                    analysis.relations.append(rel)

    def _detect_xing(
        self,
        branches: List[str],
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 刑 (Punishments) including 三刑 and 自刑."""
        branch_set = frozenset(branches)

        # Check for complete 三刑
        for trio, xing_type in XING_TRIOS.items():
            if trio.issubset(branch_set):
                pillars = tuple(
                    p for b, p in branches_with_pillars
                    if b in trio
                )
                rel_type = (
                    RelationType.WU_EN_XING
                    if xing_type == '无恩之刑'
                    else RelationType.CHI_SHI_XING
                )
                rel = BranchRelation(
                    relation_type=rel_type,
                    branches=tuple(sorted(trio)),
                    pillars=pillars,
                    description=f"{''.join(sorted(trio))}{xing_type}"
                )
                analysis.xing.append(rel)
                analysis.relations.append(rel)

        # Check for pair punishments (子卯无礼之刑)
        for i, (b1, p1) in enumerate(branches_with_pillars):
            for b2, p2 in branches_with_pillars[i + 1:]:
                if (b1, b2) in XING_PAIRS:
                    # Determine type
                    if {b1, b2} == {'子', '卯'}:
                        rel_type = RelationType.WU_LI_XING
                        desc = f"{p1}{b1}与{p2}{b2}无礼之刑"
                    elif {b1, b2}.issubset({'寅', '巳', '申'}):
                        # Part of 寅巳申, only add if not already full trio
                        if not any(len(r.branches) == 3 and r.relation_type == RelationType.WU_EN_XING for r in analysis.xing):
                            rel_type = RelationType.WU_EN_XING
                            desc = f"{p1}{b1}与{p2}{b2}相刑"
                        else:
                            continue
                    elif {b1, b2}.issubset({'丑', '戌', '未'}):
                        # Part of 丑戌未, only add if not already full trio
                        if not any(len(r.branches) == 3 and r.relation_type == RelationType.CHI_SHI_XING for r in analysis.xing):
                            rel_type = RelationType.CHI_SHI_XING
                            desc = f"{p1}{b1}与{p2}{b2}相刑"
                        else:
                            continue
                    else:
                        continue

                    rel = BranchRelation(
                        relation_type=rel_type,
                        branches=(b1, b2),
                        pillars=(p1, p2),
                        description=desc
                    )
                    analysis.xing.append(rel)
                    analysis.relations.append(rel)

        # Check for 自刑 (duplicate self-punishment branches)
        branch_counts = {}
        branch_pillars = {}
        for b, p in branches_with_pillars:
            branch_counts[b] = branch_counts.get(b, 0) + 1
            if b not in branch_pillars:
                branch_pillars[b] = []
            branch_pillars[b].append(p)

        for zhi in ZI_XING:
            if branch_counts.get(zhi, 0) >= 2:
                pillars = tuple(branch_pillars[zhi])
                rel = BranchRelation(
                    relation_type=RelationType.ZI_XING,
                    branches=(zhi, zhi),
                    pillars=pillars,
                    description=f"{zhi}见{zhi}自刑"
                )
                analysis.zi_xing.append(rel)
                analysis.xing.append(rel)
                analysis.relations.append(rel)

    def _detect_hai(
        self,
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 害 (Harms)."""
        for i, (b1, p1) in enumerate(branches_with_pillars):
            for b2, p2 in branches_with_pillars[i + 1:]:
                if (b1, b2) in HAI_PAIRS:
                    rel = BranchRelation(
                        relation_type=RelationType.HAI,
                        branches=(b1, b2),
                        pillars=(p1, p2),
                        description=f"{p1}{b1}与{p2}{b2}相害"
                    )
                    analysis.hai.append(rel)
                    analysis.relations.append(rel)

    def _detect_po(
        self,
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 破 (Breaks)."""
        for i, (b1, p1) in enumerate(branches_with_pillars):
            for b2, p2 in branches_with_pillars[i + 1:]:
                if (b1, b2) in PO_PAIRS:
                    rel = BranchRelation(
                        relation_type=RelationType.PO,
                        branches=(b1, b2),
                        pillars=(p1, p2),
                        description=f"{p1}{b1}与{p2}{b2}相破"
                    )
                    analysis.po.append(rel)
                    analysis.relations.append(rel)

    def _detect_si_ku(
        self,
        branches_with_pillars: List[Tuple[str, str]],
        analysis: BranchRelationsAnalysis
    ) -> None:
        """Detect 四库 (Four Graveyards)."""
        for b, p in branches_with_pillars:
            if b in SI_KU_SET:
                element = SI_KU_BRANCHES[b]
                rel = BranchRelation(
                    relation_type=RelationType.SI_KU,
                    branches=(b,),
                    pillars=(p,),
                    element=element,
                    description=f"{p}支{b}为{element.value}库"
                )
                analysis.si_ku.append(rel)
                analysis.relations.append(rel)
