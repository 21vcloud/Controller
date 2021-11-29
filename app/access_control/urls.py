# -*- coding:utf-8 -*-

from django.urls import path
from access_control import views

urlpatterns = (
    path(r'console', views.Console.as_view()),
    path(r'button', views.Button.as_view()),
    path(r'role', views.RoleListView.as_view()),
    path(r'permission', views.PermissionListView.as_view()),
    path(r'base_role_user', views.BaseRoleUserListView.as_view()),
    path(r'role_user', views.RoleUserListView.as_view()),
)
