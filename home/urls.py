from django.urls import path
from . import views, group_views

urlpatterns = [
    path("", views.index, name="home"),
    path("signup/", views.signup_view, name="signup"),
    # Custom auth routes
    path("login/", views.login_view, name="custom_login"),
    path("logout/", views.logout_view, name="custom_logout"),
    # Account pages
    path("account/", views.account_dashboard, name="account_dashboard"),
    path("account/edit/", views.account_edit, name="account_edit"),
    path("account/export.json", views.account_export_json, name="account_export_json"),
    # Group management
    path("groups/", group_views.group_list, name="group_list"),
    path("groups/create/", group_views.group_create, name="group_create"),
    path("groups/<int:group_id>/", group_views.group_detail, name="group_detail"),
    path("groups/<int:group_id>/add-member/", group_views.group_add_member, name="group_add_member"),
    path("groups/<int:group_id>/remove-member/<int:user_id>/", group_views.group_remove_member, name="group_remove_member"),
    path("groups/<int:group_id>/assign-task/", group_views.assign_task, name="assign_task"),
    path("my-assigned-tasks/", group_views.my_assigned_tasks, name="my_assigned_tasks"),
]
