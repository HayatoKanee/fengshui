"""
Application Content Package.

Contains presentation-layer text content used by application services.
This separates domain logic from user-facing text generation.
"""
from .analysis_text import TIGANG_TEXT, PARTNER_TEXT

__all__ = ["TIGANG_TEXT", "PARTNER_TEXT"]
