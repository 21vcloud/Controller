# -*- coding: utf-8 -*-

from django.conf.urls import url


from baremetal_service import views


urlpatterns = [
    # VPC
    url(r'v1/vpcs', views.VpcsViews.as_view()),

    # VPC Network
    url(r'v1/networks', views.VpcNetworksViews.as_view()),

    ]