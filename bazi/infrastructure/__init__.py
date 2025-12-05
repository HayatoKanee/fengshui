"""
BaZi Infrastructure Layer.

This layer contains adapters and repositories that implement
the domain ports, providing concrete implementations for
external dependencies (lunar_python library, Django ORM).

Note: Imports are done lazily to avoid Django configuration requirements
when only using the lunar adapter.
"""


def __getattr__(name: str):
    """Lazy import to avoid Django configuration on module load."""
    if name == "LunarPythonAdapter":
        from .adapters import LunarPythonAdapter
        return LunarPythonAdapter
    elif name == "DjangoProfileRepository":
        from .repositories import DjangoProfileRepository
        return DjangoProfileRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "LunarPythonAdapter",
    "DjangoProfileRepository",
]
