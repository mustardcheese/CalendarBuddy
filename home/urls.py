from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("signup/", views.signup_view, name="signup"),
    # ✅ Custom auth routes
    path("login/", views.login_view, name="custom_login"),
    path("logout/", views.logout_view, name="custom_logout"),
    # Account pages
    path("account/", views.account_dashboard, name="account_dashboard"),
    path("account/edit/", views.account_edit, name="account_edit"),
    path("account/export.json", views.account_export_json, name="account_export_json"),
]
