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
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

# Import from new presentation layer (Clean Architecture)
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
    home_view,
    bazi_view,
    wuxing_view,
    yinyang_view,
    tiangan_view,
    dizhi_view,
    ganzhi_view,
    introbazi_view,
    shishen_view,
    wangxiang_view,
    zeri_view,
    bazi_lookup_view,
    get_bazi_detail,
    liunian_partial,
    feixing_view,
    calendar_view,
    calendar_data,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    
    # Authentication URLs
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', user_login, name='register'),  # Point to login view for compatibility
    
    # Profile management URLs
    path('profiles/', profile_list, name='profiles'),
    path('profiles/add/', add_profile, name='add_profile'),
    path('profiles/edit/<int:profile_id>/', edit_profile, name='edit_profile'),
    path('profiles/delete/<int:profile_id>/', delete_profile, name='delete_profile'),
    path('profiles/default/<int:profile_id>/', set_default_profile, name='set_default_profile'),
    
    # Main app URLs
    path('bazi', bazi_view, name='bazi'),
    path('wuxing', wuxing_view, name='wuxing'),
    path('yinyang', yinyang_view, name='yinyang'),
    path('tiangan', tiangan_view, name='tiangan'),
    path('dizhi', dizhi_view, name='dizhi'),
    path('ganzhi', ganzhi_view, name='ganzhi'),
    path('introbazi', introbazi_view, name='introbazi'),
    path('shishen', shishen_view, name='shishen'),
    path('wangxiang', wangxiang_view, name='wangxiang'),
    path('zeri', zeri_view, name='zeri'),
    path('bazi_lookup', bazi_lookup_view, name='bazi_lookup'),
    path('bazi_detail', get_bazi_detail, name='bazi_detail'),
    path('liunian_partial', liunian_partial, name='liunian_partial'),
    path('feixing',feixing_view,name='feixing'),
    path('calendar', calendar_view, name='calendar'),
    path('calendar/data/', calendar_data, name='calendar_data'),
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
