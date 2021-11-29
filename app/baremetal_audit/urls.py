# -*- coding: utf-8 -*-

from django.conf.urls import url
from baremetal_audit import views

urlpatterns = [
    # Session id url
    url(r'log', views.AuditViews.as_view({"get": "list"}), name='get_audit_log'),
    url(r'users', views.AuditViews.as_view({"get": "list_user"}), name="get_user_by_project")
]
