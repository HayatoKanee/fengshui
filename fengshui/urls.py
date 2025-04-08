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
from bazi.views import bazi_view, home_view, wuxing_view, tiangan_view, yinyang_view, dizhi_view, ganzhi_view, \
    introbazi_view, zeri_view, get_bazi_detail, feixing_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
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
]
