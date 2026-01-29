"""
BaZi Presentation Layer.

This layer contains views and forms for handling HTTP requests
and rendering responses. Views follow the "thin view" pattern -
they handle HTTP concerns and delegate business logic to
application services via the DI container.

Architecture:
    HTTP Request → View → Application Service → Domain Service → Response

Usage:
    from bazi.presentation import bazi_view, calendar_view
    # or
    from bazi.presentation.views import bazi_view
"""
from .views import (
    # Auth views
    user_login,
    user_logout,
    user_register,
    # Profile views
    profile_list,
    add_profile,
    edit_profile,
    delete_profile,
    set_default_profile,
    # BaZi views
    bazi_view,
    get_bazi_detail,
    liunian_partial,
    # Calendar views
    calendar_view,
    calendar_data,
    # Static pages
    home_view,
    tiangan_view,
    yinyang_view,
    dizhi_view,
    ganzhi_view,
    wuxing_view,
    introbazi_view,
    feixing_view,
    # Lookup views
    bazi_lookup_view,
    zeri_view,
    # API views
    profile_api,
    profile_batch_api,
    profile_detail_api,
    profile_default_api,
)

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
    "liunian_partial",
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
    "feixing_view",
    # Lookup
    "bazi_lookup_view",
    "zeri_view",
    # API
    "profile_api",
    "profile_batch_api",
    "profile_detail_api",
    "profile_default_api",
]
