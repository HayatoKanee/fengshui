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
            form.save()
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
    # Initial display with current year and month
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    
    # Get user profiles
    profiles = UserProfile.objects.filter(user=request.user)
    
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
        year = int(request.POST.get('year', datetime.datetime.now().year))
        month = int(request.POST.get('month', datetime.datetime.now().month))
        profile_id = request.POST.get('profile_id')
        
        # Get the number of days in the selected month
        first_day = datetime.datetime(year, month, 1)
        if month == 12:
            last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
        
        num_days = last_day.day
        
        # For each day in the month, set all to bad
        calendar_days = []
        for day in range(1, num_days + 1):
            day_quality = []
            for hour in [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
                # Set all hours to 'bad' quality
                day_quality.append({
                    'hour': hour,
                    'quality': 'bad'  # All days marked as bad
                })
                    
            calendar_days.append({
                'day': day,
                'hours': day_quality
            })
        
        return JsonResponse({'days': calendar_days})
    
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

