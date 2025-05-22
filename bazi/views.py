import csv
import datetime
import os
import json

from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from fengshui import settings
from .forms import BirthTimeForm, UserRegistrationForm, UserProfileForm
from .models import UserProfile
from lunar_python import Lunar, Solar, EightChar, JieQi
from .constants import gan_wuxing, gan_yinyang
from .helper import *
from .feixing import *

# Authentication Views
def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    # Add message if redirected from calendar
    next_url = request.GET.get('next', '')
    if next_url == '/calendar':
        messages.info(request, "查看日历功能需要先登录或注册")
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # User exists and credentials are correct, log them in
            login(request, user)
            messages.success(request, "登录成功!")
            
            # Redirect to next page if provided, otherwise home
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            # Check if the username exists
            if not User.objects.filter(username=username).exists():
                # Username doesn't exist, create a new user
                try:
                    new_user = User.objects.create_user(username=username, password=password)
                    new_user.save()
                    
                    # Authenticate with the new user
                    user = authenticate(request, username=username, password=password)
                    login(request, user)
                    
                    messages.success(request, "账号自动创建并登录成功!")
                    next_url = request.GET.get('next', 'home')
                    return redirect(next_url)
                except Exception as e:
                    messages.error(request, f"创建账号失败: {str(e)}")
            else:
                # Username exists but password is incorrect
                messages.error(request, "密码错误，请重试。")
            
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, "您已成功退出登录。")
    return redirect('home')

def user_register(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "注册成功，已自动登录。")
            return redirect('home')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'register.html', {'form': form})

# Profile Management Views
@login_required(login_url='/login/')
def profile_list(request):
    profiles = UserProfile.objects.filter(user=request.user)
    return render(request, 'profiles.html', {'profiles': profiles})

@login_required(login_url='/login/')
def add_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            
            # Check if this is the user's first profile and set it as default if so
            user_profiles_count = UserProfile.objects.filter(user=request.user).count()
            if user_profiles_count == 0:
                profile.is_default = True
            
            # Calculate and save day master strength and favorable elements
            calculate_and_save_profile_attributes(profile)
                
            profile.save()
            messages.success(request, "个人资料添加成功!")
            
            # Check if we should redirect to bazi page with the new profile
            if 'redirect_to_bazi' in request.POST:
                return redirect(f'/bazi?profile_id={profile.id}')
            return redirect('profiles')
    else:
        form = UserProfileForm()
        
    return render(request, 'profile_form.html', {'form': form})

@login_required(login_url='/login/')
def edit_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            updated_profile = form.save(commit=False)
            
            # Recalculate and save day master strength and favorable elements
            calculate_and_save_profile_attributes(updated_profile)
            
            updated_profile.save()
            messages.success(request, "个人资料更新成功!")
            return redirect('profiles')
    else:
        form = UserProfileForm(instance=profile)
        
    return render(request, 'profile_form.html', {'form': form})

@login_required(login_url='/login/')
def delete_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id, user=request.user)
    profile.delete()
    messages.success(request, "个人资料已删除。")
    return redirect('profiles')

@login_required(login_url='/login/')
def set_default_profile(request, profile_id):
    # Get the profile we want to set as default
    profile = get_object_or_404(UserProfile, id=profile_id, user=request.user)
    
    # Clear default status from all other user profiles
    UserProfile.objects.filter(user=request.user).update(is_default=False)
    
    # Set the selected profile as default
    profile.is_default = True
    profile.save()
    
    messages.success(request, f"已将 {profile.name} 设置为默认资料")
    
    # Redirect back to profiles page
    return redirect('profiles')

def home_view(request):
    return render(request, 'home.html')


def tiangan_view(request):
    return render(request, 'tiangan.html')


def yinyang_view(request):
    return render(request, 'yinyang.html')


def dizhi_view(request):
    return render(request, 'dizhi.html')


def ganzhi_view(request):
    return render(request, 'ganzhi.html')


def wuxing_view(request):
    return render(request, 'wuxing.html')


def introbazi_view(request):
    return render(request, 'introbazi.html')


def get_bazi_detail(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        month = request.POST.get('month')
        day = request.POST.get('day')
        hour = request.POST.get('hour')
        profile_id = request.POST.get('profile_id')
        
        # Get the profile if profile_id is provided
        profile = None
        if profile_id and request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(id=profile_id, user=request.user)
            except UserProfile.DoesNotExist:
                pass
        
        solar = Solar.fromYmdHms(int(year), int(month), int(day), int(hour), 0, 0)
        lunar = solar.getLunar()
        bazi = lunar.getEightChar()
        main_wuxing = bazi.getDayWuXing()[0]
        values = calculate_values(bazi)
        hidden_gans = get_hidden_gans(bazi)
        sheng_hao_relations = get_relations(main_wuxing)
        wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
        yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
        shishen = calculate_shishen_for_bazi(wuxing, yinyang)
        wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
        wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
        gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
        shengxiao = lunar.getYearShengXiaoExact()
        wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
        sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
        sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
        gui_ren = calculate_day_guiren(bazi)
        # year_gui_ren = calculate_year_guiren(bazi)
        tian_de = calculate_tian_de(bazi)
        yue_de = calculate_yue_de(bazi)
        wen_chang = calculate_wen_chang(bazi)
        lu_shen = calculate_lu_shen(bazi)
        # Get the shensha list using the new function
        shensha_list = get_shensha(bazi)
        
        if profile:
            birth_solar = Solar.fromYmdHms(profile.birth_year, profile.birth_month, 
                                          profile.birth_day, profile.birth_hour, 
                                          profile.birth_minute or 0, 0)
            birth_lunar = birth_solar.getLunar()
            birth_bazi = birth_lunar.getEightChar()
            

        context = {
            'bazi': bazi,
            'wuxing': wuxing,
            'wuxing_value': wuxing_value,
            'sheng_hao': sheng_hao,
            'sheng_hao_percentage': sheng_hao_percentage,
            'gui_ren': gui_ren,
            # 'year_gui_ren': year_gui_ren,
            'tian_de': tian_de,
            'yue_de': yue_de,
            'wen_chang': wen_chang,
            'lu_shen': lu_shen,
            'shensha_list': shensha_list,  # Add shensha list to the context
        }
        html = render_to_string('partials/bazi_detail.html', context)
        return HttpResponse(html)
    return HttpResponse(status=404)



@login_required(login_url='/login/')
def calendar_view(request):
    """
    View for the calendar tab where users can select a date and see its quality.
    Requires user to be logged in.
    """
    # Get user profiles
    profiles = UserProfile.objects.filter(user=request.user)
    
    # Check if user has any profiles
    if not profiles.exists():
        messages.warning(request, "您需要先创建八字资料才能使用日历功能。请先创建一个资料。")
        return redirect('profiles')
    
    # Initial display with current year and month
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    
    return render(request, 'calendar.html', {
        'year': current_year,
        'month': current_month,
        'years': range(current_year - 10, current_year + 11),
        'months': range(1, 13),
        'profiles': profiles
    })


def calendar_data(request):
    """API endpoint to get calendar day quality data"""
    if request.method == 'POST':
        # Get year and month from request, or use current if not provided
        try:
            year = int(request.POST.get('year', datetime.datetime.now().year))
            month = int(request.POST.get('month', datetime.datetime.now().month))
        except (ValueError, TypeError):
            # Default to current year and month if invalid values
            year = datetime.datetime.now().year
            month = datetime.datetime.now().month
            
        profile_id = request.POST.get('profile_id')
        
        # Get profile information
        profile = None
        if request.user.is_authenticated:
            if profile_id:
                try:
                    profile = UserProfile.objects.get(id=profile_id, user=request.user)
                except UserProfile.DoesNotExist:
                    pass
            
            # If no profile specified or not found, try to use default profile
            if not profile:
                try:
                    profile = UserProfile.objects.get(user=request.user, is_default=True)
                except UserProfile.DoesNotExist:
                    pass
        
        # If still no profile, return an error
        if not profile:
            return JsonResponse({
                'error': 'no_profile',
                'message': '请先选择一个八字资料才能查看择日信息'
            }, status=400)
            
        # Get the number of days in the selected month
        first_day = datetime.datetime(year, month, 1)
        if month == 12:
            last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
        
        num_days = last_day.day
        
        calendar_days = []
        
        # Get profile's bazi
        profile_solar = Solar.fromYmdHms(profile.birth_year, profile.birth_month, profile.birth_day, 
                                  profile.birth_hour, profile.birth_minute or 0, 0)
        profile_lunar = profile_solar.getLunar()
        profile_bazi = profile_lunar.getEightChar()
        
        # Get profile's main elements and attributes
        profile_day_gan = profile_bazi.getDayGan()
        profile_day_zhi = profile_bazi.getDayZhi()
        
        # Use stored day master wuxing or calculate it if not available
        if profile.day_master_wuxing:
            profile_day_wuxing = profile.day_master_wuxing
        else:
            profile_day_wuxing = gan_wuxing.get(profile_day_gan)
        
        # Check if we have stored values for day master strength and favorable elements
        if profile.is_day_master_strong is not None and profile.favorable_wuxing and profile.unfavorable_wuxing:
            # Use stored values
            is_strong = profile.is_day_master_strong
            good_wuxing_list = profile.favorable_wuxing.split(',')
            bad_wuxing_list = profile.unfavorable_wuxing.split(',')
        else:
            # Calculate if the day master is strong or weak
            values = calculate_values(profile_bazi)
            hidden_gans = get_hidden_gans(profile_bazi)
            wang_xiang = get_wang_xiang(profile_bazi.getMonthZhi(), profile_lunar)
            wang_xiang_values = calculate_wang_xiang_values(profile_bazi, wang_xiang)
            gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
            wuxing_value = accumulate_wuxing_values(calculate_values_for_bazi(profile_bazi, gan_wuxing), gan_liang_values)
            sheng_hao = calculate_shenghao(wuxing_value, profile_day_wuxing)
            is_strong = sheng_hao[0] > sheng_hao[1]
            
            # 平衡法: If day master is strong, we want to weaken it; if weak, strengthen it
            # Get favorable and unfavorable elements based on balance method
            if is_strong:
                # If day master is strong, elements that control it are good, elements that generate it are bad
                good_wuxing_list = wuxing_relations[profile_day_wuxing]['不利']
                bad_wuxing_list = wuxing_relations[profile_day_wuxing]['有利']
            else:
                # If day master is weak, elements that generate it are good, elements that control it are bad
                good_wuxing_list = wuxing_relations[profile_day_wuxing]['有利']
                bad_wuxing_list = wuxing_relations[profile_day_wuxing]['不利']
            
            # Save these values for future use
            profile.is_day_master_strong = is_strong
            profile.day_master_wuxing = profile_day_wuxing
            profile.favorable_wuxing = ','.join(good_wuxing_list)
            profile.unfavorable_wuxing = ','.join(bad_wuxing_list)
            profile.save()
        
        # Get profile's four pillars
        profile_year_gan = profile_bazi.getYearGan()
        profile_year_zhi = profile_bazi.getYearZhi()
        profile_month_gan = profile_bazi.getMonthGan()
        profile_month_zhi = profile_bazi.getMonthZhi()
        profile_time_gan = profile_bazi.getTimeGan()
        profile_time_zhi = profile_bazi.getTimeZhi()
        
        # Get all profile gan/zhi for checking conflicts
        profile_all_gan = [profile_year_gan, profile_month_gan, profile_day_gan, profile_time_gan]
        profile_all_zhi = [profile_year_zhi, profile_month_zhi, profile_day_zhi, profile_time_zhi]

        # Get current month and year information
        month_solar = Solar.fromYmdHms(year, month, 1, 12, 0, 0)
        month_lunar = month_solar.getLunar()
        month_bazi = month_lunar.getEightChar()
        month_gan = month_bazi.getMonthGan()
        month_zhi = month_bazi.getMonthZhi()
        year_gan = month_bazi.getYearGan()
        year_zhi = month_bazi.getYearZhi()
        
        # Check for year-level quality
        year_score_adjustment = 0  # Initialize year score adjustment
        
        # Check if year gan/zhi conflicts with profile
        for profile_gan in profile_all_gan:
            if (year_gan, profile_gan) in gan_xiang_chong or (profile_gan, year_gan) in gan_xiang_chong:
                year_score_adjustment -= 0.1  # Apply -0.1 penalty for year conflicts
                break
                
        for profile_zhi in profile_all_zhi:
            if (year_zhi, profile_zhi) in zhi_xiang_chong or (profile_zhi, year_zhi) in zhi_xiang_chong:
                year_score_adjustment -= 0.1  # Apply -0.1 penalty for year conflicts
                break
        
        # Check if year's elements are favorable
        year_gan_wuxing = gan_wuxing.get(year_gan)
        year_zhi_wuxing = wuxing.get(year_zhi)
        
        # Check if year elements are favorable
        if year_gan_wuxing in good_wuxing_list or year_zhi_wuxing in good_wuxing_list:
            year_score_adjustment += 0.1  # Add 0.1 bonus for favorable year elements
        
        # Check for month-level quality
        month_score_adjustment = 0  # Initialize month score adjustment
        
        # Check if month gan conflicts with year gan
        if (month_gan, year_gan) in gan_xiang_chong or (year_gan, month_gan) in gan_xiang_chong:
            month_score_adjustment -= 0.2  # Apply -0.2 penalty for month conflicts
            
        # Check if month gan conflicts with any of profile's gan
        for profile_gan in profile_all_gan:
            if (month_gan, profile_gan) in gan_xiang_chong or (profile_gan, month_gan) in gan_xiang_chong:
                month_score_adjustment -= 0.2  # Apply -0.2 penalty for month conflicts
                break
                
        # Check if month zhi conflicts with year zhi
        if (month_zhi, year_zhi) in zhi_xiang_chong or (year_zhi, month_zhi) in zhi_xiang_chong:
            month_score_adjustment -= 0.2  # Apply -0.2 penalty for month conflicts
            
        # Check if month zhi conflicts with any of profile's zhi
        for profile_zhi in profile_all_zhi:
            if (month_zhi, profile_zhi) in zhi_xiang_chong or (profile_zhi, month_zhi) in zhi_xiang_chong:
                month_score_adjustment -= 0.2  # Apply -0.2 penalty for month conflicts
                break
        
        # Check if month's elements are favorable
        month_gan_wuxing = gan_wuxing.get(month_gan)
        month_zhi_wuxing = wuxing.get(month_zhi)
        
        if month_gan_wuxing in good_wuxing_list or month_zhi_wuxing in good_wuxing_list:
            month_score_adjustment += 0.1  # Add 0.1 bonus for favorable month elements

        # For each day in the month, evaluate compatibility
        for day in range(1, num_days + 1):
            day_quality = []
            day_reasons = []
            
            # Get the day's basic information (at noon for general day evaluation)
            date_solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
            date_lunar = date_solar.getLunar()
            date_bazi = date_lunar.getEightChar()
            
            # Get lunar date information
            lunar_month = date_lunar.getMonthInChinese()
            lunar_day = date_lunar.getDayInChinese()
            lunar_date = f"{lunar_month}月{lunar_day}"
            
            # Initialize day score with year and month adjustments
            day_score = year_score_adjustment + month_score_adjustment
            
            # Add explanation for year/month adjustments if they're not zero
            if year_score_adjustment != 0:
                if year_score_adjustment > 0:
                    day_reasons.append({
                        'type': 'good',
                        'text': f'年度因素: {year_score_adjustment:+.1f}分'
                    })
                else:
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'年度因素: {year_score_adjustment:+.1f}分'
                    })
            
            if month_score_adjustment != 0:
                if month_score_adjustment > 0:
                    day_reasons.append({
                        'type': 'good',
                        'text': f'月度因素: {month_score_adjustment:+.1f}分'
                    })
                else:
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'月度因素: {month_score_adjustment:+.1f}分'
                    })
                
            # General day-level checks (for day pillar)
            day_gan = date_bazi.getDayGan()
            day_zhi = date_bazi.getDayZhi()
            
            # Initialize day quality as neutral
            day_overall_quality = 'neutral'

            # Check for 四绝日 (Four "Jue" Days)
            if is_si_jue_ri(date_solar):
                day_overall_quality = 'bad'
                day_score -= 2  # -2 for "Jue" Day
                day_reasons.append({
                    'type': 'bad',
                    'text': '四绝日: 此日为节气前一天，为四绝日，不宜做重要事情'
                })
            
            # Check for 四离日 (Four "Li" Days)
            if is_si_li_ri(date_solar):
                day_overall_quality = 'bad'
                day_score -= 2  # -2 for "Li" Day
                day_reasons.append({
                    'type': 'bad',
                    'text': '四离日: 此日为分至前一天，为四离日，不宜做重要事情'
                })
            # Check for Yang Gong Thirteen Taboos (杨公十三忌)
            if is_yang_gong_taboo(date_lunar):
                day_score -= 0.5  # -0.5 for Yang Gong Taboos
                day_reasons.append({
                    'type': 'bad',
                    'text': '杨公十三忌: 此日为杨公忌日，不宜做重要事情'
                })
            
            # Check for Breaking Day (破日)
            if date_lunar.getZhiXing() == '破':
                day_overall_quality = 'bad'
                day_score -= 2  # -2 for Breaking Day
                day_reasons.append({
                    'type': 'bad',
                    'text': f'破日: 此日为破日"，不宜做重要事情'
                })
            
            # Check if day gan conflicts with year gan or month gan
            if (day_gan, year_gan) in gan_xiang_chong or (day_gan, month_gan) in gan_xiang_chong:
                day_overall_quality = 'bad'
                day_score -= 2  # -2 for conflicts (冲)
                if (day_gan, year_gan) in gan_xiang_chong:
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'日干 {day_gan} 与年干 {year_gan} 相冲'
                    })
                if (day_gan, month_gan) in gan_xiang_chong:
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'日干 {day_gan} 与月干 {month_gan} 相冲'
                    })
                
            # Check if day zhi conflicts with year zhi or month zhi
            if (day_zhi, year_zhi) in zhi_xiang_chong or (day_zhi, month_zhi) in zhi_xiang_chong:
                day_overall_quality = 'bad'
                day_score -= 2  # -2 for conflicts (冲)
                if (day_zhi, year_zhi) in zhi_xiang_chong:
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'日支 {day_zhi} 与年支 {year_zhi} 相冲'
                    })
                if (day_zhi, month_zhi) in zhi_xiang_chong:
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'日支 {day_zhi} 与月支 {month_zhi} 相冲'
                    })
                
            # Check if day pillar conflicts with profile
            for profile_gan in profile_all_gan:
                if (day_gan, profile_gan) in gan_xiang_chong:
                    day_overall_quality = 'bad'
                    day_score -= 2  # -2 for conflicts (冲)
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'日干 {day_gan} 与八字天干 {profile_gan} 相冲'
                    })
            
            for profile_zhi in profile_all_zhi:
                if (day_zhi, profile_zhi) in zhi_xiang_chong:
                    day_overall_quality = 'bad'
                    day_score -= 2  # -2 for conflicts (冲)
                    day_reasons.append({
                        'type': 'bad',
                        'text': f'日支 {day_zhi} 与八字地支 {profile_zhi} 相冲'
                    })
            
            
            # Check five element compatibility
            day_gan_wuxing = gan_wuxing.get(day_gan)
            day_zhi_wuxing = wuxing.get(day_zhi)
            
            # Check if day's element is unfavorable based on balance method
            if day_gan_wuxing in bad_wuxing_list:
                day_score -= 0.5  # -0.5 for unfavorable five elements
                day_reasons.append({
                    'type': 'bad',
                    'text': f'日干五行 {day_gan_wuxing} 对命主不利'
                })
            if day_zhi_wuxing in bad_wuxing_list:
                day_score -= 0.5  # -0.5 for unfavorable five elements
                day_reasons.append({
                    'type': 'bad',
                    'text': f'日支五行 {day_zhi_wuxing} 对命主不利'
                })

        
            # Check for harmony (3 harmony, 6 harmony)
            for gan_zhi in profile_bazi.toString().split(' '):
                if check_he(gan_zhi, day_zhi):
                    day_score += 1  # +1 for auspicious harmonies
                    day_reasons.append({
                        'type': 'good',
                        'text': f'日支 {day_zhi} 与八字 {gan_zhi} 相合'
                    })
                    break
            
            # Check for auspicious stars
            if is_tian_de(date_bazi):
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': '此日有天德星'
                })
            if is_yue_de(date_bazi):
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': '此日有月德星'
                })
            if is_wen_chang(date_bazi):
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': '此日有文昌星'
                })
            if is_tian_yi_guiren(date_bazi):
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': '此日有天乙贵人'
                })
                
            if (profile_day_gan, day_zhi) in gui_ren:
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': f'命主日干 {profile_day_gan} 与当日日支 {day_zhi} 贵人相见'
                })
                
            if (day_gan, profile_day_zhi) in wen_chang:
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': f'命主日干 {day_gan} 与当日日支 {profile_day_zhi} 文昌相见'
                })
                
            if (profile_month_zhi, day_gan) in tian_de:
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': f'命主月支 {profile_month_zhi} 与当日日干 {day_gan} 天德相见'
                })
                
            if (profile_month_zhi, day_gan) in yue_de:
                day_score += 1  # +1 for auspicious stars
                day_reasons.append({
                    'type': 'good',
                    'text': f'命主月支 {profile_month_zhi} 与当日日干 {day_gan} 月德相见'
                })
                
            # Check if day's element is favorable based on balance method
            if day_gan_wuxing in good_wuxing_list:
                day_score += 0.25  # +0.25 for favorable five elements
                day_reasons.append({
                    'type': 'good',
                    'text': f'日干五行 {day_gan_wuxing} 对命主有利'
                })
                
            if day_zhi_wuxing in good_wuxing_list:
                day_score += 0.25  # +0.25 for favorable five elements
                day_reasons.append({
                    'type': 'good',
                    'text': f'日支五行 {day_zhi_wuxing} 对命主有利'
                })
            
            
            for hour in [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
                # Always set to neutral for hours as per user's change
                day_quality.append({
                    'hour': hour,
                    'quality': 'neutral'
                })
            
            # If no reasons found for neutral days, add a default explanation
            if day_overall_quality == 'neutral' and not day_reasons:
                day_reasons.append({
                    'type': 'neutral',
                    'text': '此日无特殊吉凶因素'
                })
            

            
            calendar_days.append({
                'day': day,
                'hours': day_quality,
                'overall_quality': day_overall_quality,
                'reasons': day_reasons,
                'lunar_date': lunar_date,
                'score': day_score
            })
        
        return JsonResponse({
            'days': calendar_days,
            'month_score': month_score_adjustment,
            'year_score': year_score_adjustment,
            'year': year,
            'month': month,
            'year_gan': year_gan,
            'year_zhi': year_zhi,
            'month_gan': month_gan,
            'month_zhi': month_zhi
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)



def zeri_view(request):
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        from_date = datetime.datetime.strptime(from_date_str, '%Y-%m-%d')
        to_date = datetime.datetime.strptime(to_date_str, '%Y-%m-%d')

        if from_date > to_date:
            messages.warning(request, '开始日子不能晚于结束日子。')
            return redirect('zeri')

        data = []
        for year in range(from_date.year - 1, to_date.year + 2):
            csv_file_path = os.path.join(settings.DATA_DIR, f'good_bazis_{year}.csv')
            try:
                with open(csv_file_path, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        date = f'{row[0]} {row[1]} {row[2]} {row[3]}'
                        data_date = datetime.datetime.strptime(date, '%Y %m %d %H')  # Assuming first column has date
                        if from_date <= data_date <= to_date:
                            data.append(data_date)
            except FileNotFoundError:
                continue
        return render(request, 'zeri.html', {'data': data, 'from_date': from_date_str, 'to_date': to_date_str})
    return render(request, 'zeri.html')


def bazi_view(request):
    current_year = datetime.datetime.now().year
    years = range(current_year - 20, current_year + 50)
    
    # Check if viewing a saved profile
    profile = None
    profile_id = request.GET.get('profile_id')
    if profile_id and request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(id=profile_id, user=request.user)
            
            # Automatically calculate and display bazi details for the selected profile
            is_male = profile.is_male
            selected_year = request.GET.get('year', str(current_year))
            
            # Set up Solar and get bazi information
            solar = Solar.fromYmdHms(profile.birth_year, profile.birth_month, profile.birth_day, 
                                   profile.birth_hour, profile.birth_minute or 0, 0)
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()
            
            # Calculate all the necessary values
            main_wuxing = bazi.getDayWuXing()[0]
            values = calculate_values(bazi)
            hidden_gans = get_hidden_gans(bazi)
            sheng_hao_relations = get_relations(main_wuxing)
            wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
            yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
            shishen = calculate_shishen_for_bazi(wuxing, yinyang)
            wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
            wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
            gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
            shengxiao = lunar.getYearShengXiaoExact()
            wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
            sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
            sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
            is_strong = sheng_hao[0] > sheng_hao[1]
            partner_analyst = analyse_partner(hidden_gans, shishen)
            personality = analyse_personality(bazi.getMonthZhi())
            liunian_analysis = analyse_liunian(bazi, shishen, selected_year, is_strong, is_male)
            shensha_list = get_shensha(bazi)
            
            # Pre-fill the form with profile data
            initial_data = {
                'year': profile.birth_year,
                'month': profile.birth_month,
                'day': profile.birth_day,
                'hour': profile.birth_hour,
                'minute': profile.birth_minute,
                'gender': 'male' if profile.is_male else 'female'
            }
            form = BirthTimeForm(initial=initial_data)
            
            # Return the complete context with calculated bazi details
            context = {
                'form': form,
                'bazi': bazi,
                'values': values,
                'hidden_gans': hidden_gans,
                'main_wuxing': main_wuxing,
                'shengxiao': shengxiao,
                'wang_xiang': wang_xiang,
                'wang_xiang_values': wang_xiang_values,
                'wuxing': wuxing,
                'yinyang': yinyang,
                'shishen': shishen,
                'gan_liang_values': gan_liang_values,
                'wuxing_value': wuxing_value,
                'sheng_hao': sheng_hao,
                'sheng_hao_percentage': sheng_hao_percentage,
                'current_year': int(selected_year),
                'is_male': is_male,
                'partner_analyst': partner_analyst,
                'liunian_analysis': liunian_analysis,
                'years': years,
                'personality': personality,
                'shensha_list': shensha_list,
                'profiles': UserProfile.objects.filter(user=request.user) if request.user.is_authenticated else None
            }
            return render(request, 'bazi.html', context)
        except UserProfile.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = BirthTimeForm(request.POST)
        if form.is_valid():
            data = extract_form_data(form)
            selected_year = request.POST.get('liunian')
            is_male = request.POST.get('gender') == 'male'
            solar = Solar.fromYmdHms(data['year'], data['month'], data['day'], data['hour'], data['minute'], 0)
            lunar = solar.getLunar()
            bazi = lunar.getEightChar()
            main_wuxing = bazi.getDayWuXing()[0]
            values = calculate_values(bazi)
            hidden_gans = get_hidden_gans(bazi)
            sheng_hao_relations = get_relations(main_wuxing)
            wuxing = calculate_values_for_bazi(bazi, gan_wuxing)
            yinyang = calculate_values_for_bazi(bazi, gan_yinyang)
            shishen = calculate_shishen_for_bazi(wuxing, yinyang)
            wang_xiang = get_wang_xiang(bazi.getMonthZhi(), lunar)
            wang_xiang_values = calculate_wang_xiang_values(bazi, wang_xiang)
            gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
            shengxiao = lunar.getYearShengXiaoExact()
            wuxing_value = accumulate_wuxing_values(wuxing, gan_liang_values)
            sheng_hao = calculate_shenghao(wuxing_value, main_wuxing)
            sheng_hao_percentage = calculate_shenghao_percentage(sheng_hao[0], sheng_hao[1])
            is_strong = sheng_hao[0] > sheng_hao[1]
            partner_analyst = analyse_partner(hidden_gans, shishen)
            personality = analyse_personality(bazi.getMonthZhi())
            liunian_analysis = analyse_liunian(bazi, shishen, selected_year, is_strong, is_male)
            # Get the shensha list using the new function
            shensha_list = get_shensha(bazi)
            
            context = {
                'form': form,
                'bazi': bazi,
                'values': values,
                'hidden_gans': hidden_gans,
                'main_wuxing': main_wuxing,
                'shengxiao': shengxiao,
                'wang_xiang': wang_xiang,
                'wang_xiang_values': wang_xiang_values,
                'wuxing': wuxing,
                'yinyang': yinyang,
                'shishen': shishen,
                'gan_liang_values': gan_liang_values,
                'wuxing_value': wuxing_value,
                'sheng_hao': sheng_hao,
                'sheng_hao_percentage': sheng_hao_percentage,
                'current_year': int(selected_year),
                'is_male': is_male,
                'partner_analyst': partner_analyst,
                'liunian_analysis': liunian_analysis,
                'years': years,
                'personality': personality,
                'shensha_list': shensha_list,
                'profiles': UserProfile.objects.filter(user=request.user) if request.user.is_authenticated else None
            }
            return render(request, 'bazi.html', context)
    else:
        # Pre-fill the form with profile data if available
        initial_data = {}
        if profile:
            initial_data = {
                'year': profile.birth_year,
                'month': profile.birth_month,
                'day': profile.birth_day,
                'hour': profile.birth_hour,
                'minute': profile.birth_minute,
                'gender': 'male' if profile.is_male else 'female'
            }
        form = BirthTimeForm(initial=initial_data)

    return render(request, 'bazi.html', {
        'form': form, 
        'current_year': current_year, 
        'years': years,
        'profiles': UserProfile.objects.filter(user=request.user) if request.user.is_authenticated else None
    })

def feixing_view(request):
    center_param = request.GET.get("center", "9")
    try:
        main_center = int(center_param)
    except ValueError:
        main_center = 9

    # Build table_data: one entry for each unique grid configuration.
    table_data = []
    for star in mountains_24:
        pos = fixed_positions[star]
        # Generate a fresh main grid for each star.
        main_grid = generate_grid(main_center, order='f')

        opp_coord = (2 - pos[0], 2 - pos[1])
        star_center = main_grid[pos[0]][pos[1]]
        opp_center = main_grid[opp_coord[0]][opp_coord[1]]
        second_star = None

        # Determine flight orders based on star_center (or opp_center if star_center == 5)
        if star_center != 5:
            order_main = get_flight(star_center, yuan_long_mapping[star])
            order_opp = 'r' if order_main == 'f' else 'f'
            grid_star = generate_grid(star_center, order_main)
            grid_opposite_star = generate_grid(opp_center, order_opp)
        else:
            # Use the opposite logic if star_center is 5.
            order_main = get_flight(opp_center, yuan_long_mapping[star])
            order_opp = 'r' if order_main == 'f' else 'f'
            grid_star = generate_grid(star_center, order_opp)
            grid_opposite_star = generate_grid(opp_center, order_main)

        # Realign: Compute the shift (for outer ring) needed so that star_center ends up in the bottom-center.
        shift = get_shift(main_grid, star_center)
        # Apply the same shift to each grid.
        main_grid = rotate_outer_ring_by_steps(main_grid, shift)
        grid_star = rotate_outer_ring_by_steps(grid_star, shift)
        grid_opposite_star = rotate_outer_ring_by_steps(grid_opposite_star, shift)
        # Convert the main grid to Chinese numerals.
        main_grid_cn = [[arabic_to_chinese(n) for n in row] for row in main_grid]

        # Instead of adding duplicate grid entries, check if an identical grid_star (and grid_opposite_star)
        # has already been added. If so, record this star as the second_star.
        found = False
        for existing in table_data:
            if existing['grid_star'] == grid_star and existing['grid_opposite_star'] == grid_opposite_star:
                existing['second_star'] = star
                found = True
                break

        if not found:
            table_data.append({
                'main_grid': main_grid_cn,
                'star': star,
                'second_star': second_star,
                'grid_star': grid_star,
                'grid_opposite_star': grid_opposite_star,
            })
    context = {
        'main_center': str(main_center),
        'table_data': table_data,
    }
    return render(request, 'feixing.html', context)

def calculate_and_save_profile_attributes(profile):
    """Calculate and save day master strength and favorable/unfavorable elements for a profile"""
    try:
        # Create Solar and Lunar objects from profile birth information
        profile_solar = Solar.fromYmdHms(profile.birth_year, profile.birth_month, profile.birth_day, 
                                        profile.birth_hour, profile.birth_minute or 0, 0)
        profile_lunar = profile_solar.getLunar()
        profile_bazi = profile_lunar.getEightChar()
        
        # Get day master wuxing
        profile_day_gan = profile_bazi.getDayGan()
        profile_day_wuxing = gan_wuxing.get(profile_day_gan)
        profile.day_master_wuxing = profile_day_wuxing
        
        # Calculate if day master is strong or weak
        values = calculate_values(profile_bazi)
        hidden_gans = get_hidden_gans(profile_bazi)
        wang_xiang = get_wang_xiang(profile_bazi.getMonthZhi(), profile_lunar)
        wang_xiang_values = calculate_wang_xiang_values(profile_bazi, wang_xiang)
        gan_liang_values = calculate_gan_liang_value(values, hidden_gans, wang_xiang_values)
        wuxing_value = accumulate_wuxing_values(calculate_values_for_bazi(profile_bazi, gan_wuxing), gan_liang_values)
        sheng_hao = calculate_shenghao(wuxing_value, profile_day_wuxing)
        is_strong = sheng_hao[0] > sheng_hao[1]
        profile.is_day_master_strong = is_strong
        
        # Determine favorable and unfavorable elements based on day master strength
        if is_strong:
            # If day master is strong, elements that control it are good, elements that generate it are bad
            good_wuxing_list = wuxing_relations[profile_day_wuxing]['不利']
            bad_wuxing_list = wuxing_relations[profile_day_wuxing]['有利']
        else:
            # If day master is weak, elements that generate it are good, elements that control it are bad
            good_wuxing_list = wuxing_relations[profile_day_wuxing]['有利']
            bad_wuxing_list = wuxing_relations[profile_day_wuxing]['不利']
        
        # Store as comma-separated string
        profile.favorable_wuxing = ','.join(good_wuxing_list)
        profile.unfavorable_wuxing = ','.join(bad_wuxing_list)
    except Exception as e:
        # If calculation fails, log error but don't stop the profile creation/update
        print(f"Error calculating profile attributes: {str(e)}")
        # Keep attributes as None/null in database

def is_yang_gong_taboo(lunar_date):
    """Check if a lunar date is one of the Yang Gong Thirteen Taboos (杨公十三忌)"""
    month = lunar_date.getMonth()
    day = lunar_date.getDay()
    
    yang_gong_taboos = [
        (1, 13),  # 正月十三
        (2, 11),  # 二月十一
        (3, 9),   # 三月初九
        (4, 7),   # 四月初七
        (5, 5),   # 五月初五
        (6, 3),   # 六月初三
        (7, 1),   # 七月初一
        (7, 29),  # 七月二十九
        (8, 27),  # 八月二十七
        (9, 25),  # 九月二十五
        (10, 23), # 十月二十三
        (11, 21), # 十一月二十一
        (12, 19)  # 十二月十九
    ]
    
    return (month, day) in yang_gong_taboos

def is_po_ri(lunar_date):
    """Check if a lunar date is a breaking day (破日)
    Each lunar month has a specific earthly branch that is considered a breaking day.
    """
    month = lunar_date.getMonth()
    day_zhi = lunar_date.getDayZhi()
    
    # Mapping of lunar month to breaking day earthly branch
    po_ri_mapping = {
        1: '申',  # 正月破日 - 申日
        2: '酉',  # 二月破日 - 酉日
        3: '戌',  # 三月破日 - 戌日
        4: '亥',  # 四月破日 - 亥日
        5: '子',  # 五月破日 - 子日
        6: '丑',  # 六月破日 - 丑日
        7: '寅',  # 七月破日 - 寅日
        8: '卯',  # 八月破日 - 卯日
        9: '辰',  # 九月破日 - 辰日
        10: '巳', # 十月破日 - 巳日
        11: '午', # 十一月破日 - 午日
        12: '未'  # 十二月破日 - 未日
    }
    
    # Check if the day's earthly branch matches the breaking day for this lunar month
    return day_zhi == po_ri_mapping.get(month)

def is_si_jue_ri(date_solar):
    """Check if a date is one of the '四绝日' (Four "Jue" Days)
    These are the days before Li Chun, Li Xia, Li Qiu, and Li Dong
    """
    # Get the solar date
    year = date_solar.getYear()
    
    # Get the JieQi table for this year
    lunar = date_solar.getLunar()
    jieqi_table = lunar.getJieQiTable()
    
    # The four "Jue" days are the days before:
    # 立春 (Li Chun), 立夏 (Li Xia), 立秋 (Li Qiu), 立冬 (Li Dong)
    jue_dates = []
    
    for jieqi_name in ["立春", "立夏", "立秋", "立冬"]:
        if jieqi_name in jieqi_table:
            jieqi_date = jieqi_table[jieqi_name]
            # Get the day before
            jue_date = jieqi_date.next(-1)
            jue_dates.append(jue_date.toString())
    
    # Check if the current date is one of the "Jue" days
    current_date_str = f"{date_solar.getYear()}-{date_solar.getMonth():02d}-{date_solar.getDay():02d}"
    return current_date_str in jue_dates

def is_si_li_ri(date_solar):
    """Check if a date is one of the '四离日' (Four "Li" Days)
    These are the days before Chun Fen, Xia Zhi, Qiu Fen, and Dong Zhi
    """
    # Get the solar date
    year = date_solar.getYear()
    
    # Get the JieQi table for this year
    lunar = date_solar.getLunar()
    jieqi_table = lunar.getJieQiTable()
    
    # The four "Li" days are the days before:
    # 春分 (Chun Fen), 夏至 (Xia Zhi), 秋分 (Qiu Fen), 冬至 (Dong Zhi)
    li_dates = []
    
    for jieqi_name in ["春分", "夏至", "秋分", "冬至"]:
        if jieqi_name in jieqi_table:
            jieqi_date = jieqi_table[jieqi_name]
            # Get the day before
            li_date = jieqi_date.next(-1)
            li_dates.append(li_date.toString())
    
    # Check if the current date is one of the "Li" days
    current_date_str = f"{date_solar.getYear()}-{date_solar.getMonth():02d}-{date_solar.getDay():02d}"
    return current_date_str in li_dates

