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
from django.contrib import admin
from django.urls import path
from bazi.views import *

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
    path('zeri', zeri_view, name='zeri'),
    path('bazi_detail', get_bazi_detail, name='bazi_detail'),
    path('feixing',feixing_view,name='feixing'),
    path('calendar', calendar_view, name='calendar'),
    path('calendar/data/', calendar_data, name='calendar_data'),
]
