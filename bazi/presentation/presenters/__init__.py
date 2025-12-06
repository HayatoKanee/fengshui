"""
Presentation Layer Presenters (Clean Architecture).

Presenters transform domain models to view-ready data structures.
This follows Clean Architecture's Presenter pattern for output formatting.
"""
from .bazi_presenter import BaziPresenter, BaziViewData
from .shensha_rules import get_shensha

__all__ = ["BaziPresenter", "BaziViewData", "get_shensha"]
