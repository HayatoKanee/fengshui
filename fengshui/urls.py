"""
URL configuration for fengshui project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView


def health_check(request):
    """Simple health check endpoint for container orchestration."""
    return HttpResponse("ok", content_type="text/plain")

# Import from presentation layer (Clean Architecture)
from bazi.presentation import (
    # Auth views
    user_login,
    user_logout,
    # Profile views
    profile_list,
    add_profile,
    edit_profile,
    delete_profile,
    set_default_profile,
    # Main app views
    bazi_view,
    zeri_view,
    bazi_lookup_view,
    get_bazi_detail,
    liunian_partial,
    feixing_view,
    calendar_view,
    calendar_data,
    # API views
    profile_api,
    profile_batch_api,
    profile_detail_api,
    profile_default_api,
)

urlpatterns = [
    path('health/', health_check, name='health'),  # Container health check
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='bazi', permanent=False), name='home'),

    # Seamless login/signup (auto-creates account if user doesn't exist)
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # django-allauth for password reset, email verification, social auth
    path('accounts/', include('allauth.urls')),

    # Profile management URLs
    path('profiles/', profile_list, name='profiles'),
    path('profiles/add/', add_profile, name='add_profile'),
    path('profiles/edit/<int:profile_id>/', edit_profile, name='edit_profile'),
    path('profiles/delete/<int:profile_id>/', delete_profile, name='delete_profile'),
    path('profiles/default/<int:profile_id>/', set_default_profile, name='set_default_profile'),

    # Main app URLs
    path('bazi', bazi_view, name='bazi'),
    path('zeri', zeri_view, name='zeri'),
    path('bazi_lookup', bazi_lookup_view, name='bazi_lookup'),
    path('bazi_detail', get_bazi_detail, name='bazi_detail'),
    path('liunian_partial', liunian_partial, name='liunian_partial'),
    path('feixing', feixing_view, name='feixing'),
    path('calendar', calendar_view, name='calendar'),
    path('calendar/data/', calendar_data, name='calendar_data'),

    # Redirects: Old educational pages → docs.myfate.org
    path('yinyang', RedirectView.as_view(url='https://docs.myfate.org/basics/yinyang/', permanent=True)),
    path('wuxing', RedirectView.as_view(url='https://docs.myfate.org/basics/wuxing/', permanent=True)),
    path('tiangan', RedirectView.as_view(url='https://docs.myfate.org/basics/tiangan/', permanent=True)),
    path('dizhi', RedirectView.as_view(url='https://docs.myfate.org/basics/dizhi/', permanent=True)),
    path('ganzhi', RedirectView.as_view(url='https://docs.myfate.org/basics/ganzhi/', permanent=True)),
    path('introbazi', RedirectView.as_view(url='https://docs.myfate.org/basics/bazi/', permanent=True)),
    path('wangxiang', RedirectView.as_view(url='https://docs.myfate.org/advanced/wangxiang/', permanent=True)),
    path('shishen', RedirectView.as_view(url='https://docs.myfate.org/advanced/shishen/', permanent=True)),
    path('shenghao', RedirectView.as_view(url='https://docs.myfate.org/advanced/shenghao/', permanent=True)),

    # Profile REST API (for frontend storage sync)
    path('api/profiles/', profile_api, name='api_profiles'),
    path('api/profiles/batch/', profile_batch_api, name='api_profiles_batch'),
    path('api/profiles/<int:profile_id>/', profile_detail_api, name='api_profile_detail'),
    path('api/profiles/<int:profile_id>/default/', profile_default_api, name='api_profile_default'),
]

# i18n URL for language switching
urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]

# Add browser-reload for development hot-reloading
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
