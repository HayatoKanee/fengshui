"""
Static Page Views.

Simple views that render static educational content about
Chinese metaphysics concepts (Yin-Yang, Five Elements, etc.).

These views have no business logic - they simply render templates.
"""
from django.shortcuts import render


def home_view(request):
    """Home page view."""
    return render(request, "home.html")


def tiangan_view(request):
    """
    天干 (Heavenly Stems) educational page.

    Explains the 10 Heavenly Stems (甲乙丙丁戊己庚辛壬癸)
    and their properties in Chinese metaphysics.
    """
    return render(request, "tiangan.html")


def yinyang_view(request):
    """
    阴阳 (Yin-Yang) educational page.

    Explains the fundamental concept of Yin and Yang duality
    in Chinese philosophy and its application to BaZi.
    """
    return render(request, "yinyang.html")


def dizhi_view(request):
    """
    地支 (Earthly Branches) educational page.

    Explains the 12 Earthly Branches (子丑寅卯辰巳午未申酉戌亥)
    and their properties, including associations with animals.
    """
    return render(request, "dizhi.html")


def ganzhi_view(request):
    """
    干支 (Stems and Branches) educational page.

    Explains the 60 Jiazi (六十甲子) cycle combining
    Heavenly Stems and Earthly Branches.
    """
    return render(request, "ganzhi.html")


def wuxing_view(request):
    """
    五行 (Five Elements) educational page.

    Explains the Five Elements (Wood, Fire, Earth, Metal, Water)
    and their relationships (generating and controlling cycles).
    """
    return render(request, "wuxing.html")


def introbazi_view(request):
    """
    八字介绍 (Introduction to BaZi) educational page.

    Provides an introduction to Four Pillars of Destiny (八字)
    including how they are calculated and interpreted.
    """
    return render(request, "introbazi.html")


def shishen_view(request):
    """
    十神 (Ten Gods) educational page.

    Explains the Ten Gods relationships in BaZi - how each stem
    relates to the Day Master based on element and polarity.
    """
    return render(request, "shishen.html")


def wangxiang_view(request):
    """
    旺相休囚死 (Seasonal Element Strength) educational page.

    Explains how each of the Five Elements has different strength
    depending on the season (month branch).
    """
    return render(request, "wangxiang.html")
