# -*- coding: utf-8 -*-

from django.conf.urls import url
from baremetal_openstack import views

urlpatterns = [
    # Session id url
    url(r'query_all_resource_count', views.ResourceCountViews.as_view({"get": "query_all_resource_count"}), name='query_all_resource_count')
]
