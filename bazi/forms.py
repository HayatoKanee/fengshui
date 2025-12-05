"""
BaZi Forms - Backward Compatibility Module.

This module provides backward compatibility for code that imports from bazi.forms.
All forms have been migrated to the presentation layer following Clean Architecture.

New imports should use:
    from bazi.presentation.forms import BirthTimeForm, UserProfileForm
    # or
    from bazi.presentation import forms

This module re-exports all forms from the presentation layer to maintain
compatibility with existing code.

Migration Status: Phase 7 of Clean Architecture refactoring complete.
See REFACTORING.md for details.
"""

# Re-export all forms from presentation layer for backward compatibility
from bazi.presentation.forms import (
    UserRegistrationForm,
    BirthTimeForm,
    UserProfileForm,
)

__all__ = [
    "UserRegistrationForm",
    "BirthTimeForm",
    "UserProfileForm",
]
