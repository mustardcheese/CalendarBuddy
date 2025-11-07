from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from calendar_app.models import Task
from .forms import UserUpdateForm


def index(request):
    """Landing page view"""
    return render(request, "home/index.html")


def signup_view(request):
    """User signup view"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created successfully for {username}!")
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "home/signup.html", {"form": form})


def login_view(request):
    """User login view"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "home/login.html", {"form": form})


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


@login_required
def account_dashboard(request):
    user = request.user
    today = timezone.now().date()

    tasks_qs = Task.objects.filter(user=user).order_by("date", "created_at")
    upcoming = tasks_qs.filter(date__gte=today)[:5]
    total_tasks = tasks_qs.count()
    this_month = tasks_qs.filter(date__month=today.month, date__year=today.year).count()

    # Simple “next week” window
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    weekly = tasks_qs.filter(date__range=[start_week, end_week])

    context = {
        "user_obj": user,
        "total_tasks": total_tasks,
        "this_month": this_month,
        "weekly_count": weekly.count(),
        "upcoming": upcoming,
        "start_week": start_week,
        "end_week": end_week,
    }
    return render(request, "home/account_dashboard.html", context)


@login_required
def account_edit(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("account_dashboard")
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, "home/account_edit.html", {"form": form})


@login_required
def account_export_json(request):
    """Export ALL user-specific data (profile + tasks) as JSON."""
    user = request.user
    tasks = list(
        Task.objects.filter(user=user)
        .order_by("date", "created_at")
        .values(
            "id",
            "title",
            "description",
            "date",
            "location",
            "color",
            "category",
            "created_at",
        )
    )
    data = {
        "user": {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
        },
        "tasks": tasks,
    }
    return JsonResponse(data, safe=True)
