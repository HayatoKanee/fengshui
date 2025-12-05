"""
Authentication Views.

Handles user login, logout, and registration.
Uses Django's built-in authentication system.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from bazi.presentation.forms import UserRegistrationForm


def user_login(request):
    """
    User login view with auto-registration.

    If the username doesn't exist and valid credentials are provided,
    automatically creates a new user account. This provides a
    frictionless onboarding experience.

    Query Parameters:
        next: URL to redirect to after successful login
    """
    if request.user.is_authenticated:
        return redirect("home")

    # Show message if redirected from calendar (requires auth)
    next_url = request.GET.get("next", "")
    if next_url == "/calendar":
        messages.info(request, "查看日历功能需要先登录或注册")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Try to authenticate existing user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "登录成功!")
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
        else:
            # Check if username exists
            if not User.objects.filter(username=username).exists():
                # Auto-create new user (frictionless registration)
                try:
                    new_user = User.objects.create_user(
                        username=username, password=password
                    )
                    new_user.save()

                    user = authenticate(
                        request, username=username, password=password
                    )
                    login(request, user)

                    messages.success(request, "账号自动创建并登录成功!")
                    next_url = request.GET.get("next", "home")
                    return redirect(next_url)
                except Exception as e:
                    messages.error(request, f"创建账号失败: {str(e)}")
            else:
                # Username exists but password is wrong
                messages.error(request, "密码错误，请重试。")

    return render(request, "login.html")


def user_logout(request):
    """
    User logout view.

    Logs out the current user and redirects to home page.
    """
    logout(request)
    messages.success(request, "您已成功退出登录。")
    return redirect("home")


def user_register(request):
    """
    User registration view.

    Provides a formal registration form for users who prefer
    explicit account creation over auto-registration.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "注册成功，已自动登录。")
            return redirect("home")
    else:
        form = UserRegistrationForm()

    return render(request, "register.html", {"form": form})
