"""
Pillar (柱) domain model - a stem-branch pair.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .elements import WuXing, get_wuxing_relation, RELATIONSHIP_WEIGHTS
from .stems_branches import HeavenlyStem, EarthlyBranch


@dataclass(frozen=True)
class Pillar:
    """
    A single pillar (柱) consisting of a Heavenly Stem and Earthly Branch.

    Represents one of the four pillars in BaZi: Year, Month, Day, Hour.
    Immutable value object.
    """
    stem: HeavenlyStem
    branch: EarthlyBranch

    def __str__(self) -> str:
        """Return Chinese representation (e.g., '甲子')."""
        return f"{self.stem.chinese}{self.branch.chinese}"

    @property
    def chinese(self) -> str:
        """Chinese representation of the pillar."""
        return str(self)

    @property
    def stem_wuxing(self) -> WuXing:
        """Five Element of the stem."""
        return self.stem.wuxing

    @property
    def branch_wuxing(self) -> WuXing:
        """Five Element of the branch."""
        return self.branch.wuxing

    @property
    def hidden_stems(self) -> Dict[HeavenlyStem, float]:
        """Hidden stems within the branch with their ratios."""
        return self.branch.hidden_stems

    @classmethod
    def from_chinese(cls, chars: str) -> Pillar:
        """
        Create a Pillar from Chinese characters.

        Args:
            chars: Two-character string like '甲子'

        Returns:
            Pillar instance

        Raises:
            ValueError: If characters are invalid
        """
        if len(chars) != 2:
            raise ValueError(f"Pillar must be 2 characters, got: {chars}")

        stem = HeavenlyStem.from_chinese(chars[0])
        branch = EarthlyBranch.from_chinese(chars[1])
        return cls(stem=stem, branch=branch)

    def wuxing_relationship_values(self) -> tuple[int, int]:
        """
        Calculate the WuXing relationship values between stem and branch.

        Returns:
            Tuple of (stem_value, branch_value) based on their relationship.
        """
        relation = get_wuxing_relation(self.stem_wuxing, self.branch_wuxing)
        return RELATIONSHIP_WEIGHTS[relation]
