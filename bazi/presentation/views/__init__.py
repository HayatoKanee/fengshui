"""
Presentation Layer Views.

All views are organized by domain:
- auth.py: Authentication (login, logout, register)
- profile.py: User profile management
- bazi.py: BaZi analysis views
- calendar.py: Calendar and date selection
- static_pages.py: Static content pages
- lookup.py: BaZi lookup tools
- feixing.py: Flying Stars (玄空飞星)

Views follow the "thin view" pattern:
- Handle HTTP request/response
- Validate input via forms
- Delegate business logic to application services
- Prepare context for templates
"""
from .auth import user_login, user_logout, user_register
from .profile import (
    profile_list,
    add_profile,
    edit_profile,
    delete_profile,
    set_default_profile,
)
from .bazi import bazi_view, get_bazi_detail
from .calendar import calendar_view, calendar_data
from .static_pages import (
    home_view,
    tiangan_view,
    yinyang_view,
    dizhi_view,
    ganzhi_view,
    wuxing_view,
    introbazi_view,
)
from .lookup import bazi_lookup_view, zeri_view
from .feixing import feixing_view

__all__ = [
    # Auth
    "user_login",
    "user_logout",
    "user_register",
    # Profile
    "profile_list",
    "add_profile",
    "edit_profile",
    "delete_profile",
    "set_default_profile",
    # BaZi
    "bazi_view",
    "get_bazi_detail",
    # Calendar
    "calendar_view",
    "calendar_data",
    # Static pages
    "home_view",
    "tiangan_view",
    "yinyang_view",
    "dizhi_view",
    "ganzhi_view",
    "wuxing_view",
    "introbazi_view",
    # Lookup
    "bazi_lookup_view",
    "zeri_view",
    # FeiXing
    "feixing_view",
]
