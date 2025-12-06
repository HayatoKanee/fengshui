"""
Domain Constants Package.

Contains domain-level constants and pure functions that don't depend
on external infrastructure.
"""
from .harmony import (
    LIU_HE,
    WU_HE,
    HIDDEN_GAN_RATIOS,
    is_harmony,
)

__all__ = [
    "LIU_HE",
    "WU_HE",
    "HIDDEN_GAN_RATIOS",
    "is_harmony",
]
