"""
BaZi Domain Ports (Interfaces).

These are abstract interfaces that define what the domain layer
needs from external systems. Concrete implementations (adapters)
are provided in the infrastructure layer.

Using Protocol for structural typing (duck typing with type hints).
"""
from .lunar_port import LunarPort
from .profile_port import ProfileData, ProfileRepository

__all__ = [
    "LunarPort",
    "ProfileData",
    "ProfileRepository",
]
