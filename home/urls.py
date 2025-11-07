from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_dashboard, name="account_dashboard"),
    path("account/edit/", views.account_edit, name="account_edit"),
    path("account/export.json", views.account_export_json, name="account_export_json"),
    path("accounts/", include("django.contrib.auth.urls")),
]
