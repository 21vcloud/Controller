# -*- coding: utf-8 -*-
"""untitled3 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.shortcuts import redirect
from django.contrib import admin
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_api import views

from django.urls import include, path, re_path

swagger_info = openapi.Info(
    title="BareMental Controller API",
    default_version='v1',
    description="""
        BareMental Web API 主要包括如下方面因素：

        - baremental account 账号相关接口
         """,
    contact=openapi.Contact(email="wei.panlong@21vianet.com"),
    # license=openapi.License(name="BSD License"),
)

SchemaView = get_schema_view(
    # validators=['ssv', 'flex'],
    public=True,
    permission_classes=(permissions.AllowAny,),
    # permission_classes=(permissions.IsAuthenticated,),
)


def root_redirect(request):
    schema_view = 'cschema-swagger-ui'
    return redirect(schema_view, permanent=True)


urlpatterns = [

    path('admin/', admin.site.urls),


    # resource: firewalls
    re_path(r'firewalls/rules$', views.FirewallsRulesRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'})),
    re_path(r'firewalls/$', views.FirewallsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'})),


    # resource: VPCs
    re_path(r'vpcs/networks/(?P<vpc_id>\d+)$', views.VpcNetworksRestfulViews.as_view(
        actions={'get': 'list'})),
    re_path(r'vpcs/networks$', views.VpcNetworksRestfulViews.as_view(
        actions={'post': 'create', 'delete': 'destroy', 'put': 'update'})),
    re_path(r'vpcs/$', views.VpcsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'})),


    # resource: instances
    re_path(r'^instances/action_stop$', views.InstanceRestfulViews.as_view(
        actions={'post': 'instance_stop'})),
    re_path(r'^instances/action_start$', views.InstanceRestfulViews.as_view(
        actions={'post': 'instance_start'})),
    re_path(r'^instances/action_restart$', views.InstanceRestfulViews.as_view(
        actions={'post': 'instance_restart'})),
    re_path(r'^instances/flavors$', views.InstanceRestfulViews.as_view(
        actions={'get': 'flavor_list', 'put': 'update_flavor_count'})),
    re_path(r'^instances/images$', views.InstanceRestfulViews.as_view(
        actions={'get': 'images_list'})),
    re_path(r'^instances/interfaces$', views.InstanceRestfulViews.as_view(
        actions={'get': 'instance_list_interface'})),
    re_path(r'^instances/interface$', views.InterfaceAttachmentsRestfulViews.as_view(
        actions={'post': 'create', 'delete': 'destroy'})),
    re_path(r'^instances/machine$', views.InstanceRestfulViews.as_view(
        actions={'get': 'view_baremetal_service_machine_get'})),
    re_path(r'^instances/orders$', views.InstanceRestfulViews.as_view(
        actions={'get': 'view_baremetal_service_order_all'})),
    re_path(r'^instances/order$', views.ServiceOrderRestfulViews.as_view(
        actions={'get': 'list'})),
    re_path(r'^instances/ports$', views.InstanceRestfulViews.as_view(
        actions={'get': 'get_instance_ports'})),

    # 服务器相关操作
    re_path(r'^instances$', views.ServiceInstancesRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create',  'delete': 'destroy'})),
    re_path(r'^instance$',  views.ServiceInstanceRestfulViews.as_view(
        actions={'get': 'retrieve', 'put': 'update'})),

    # 挂载、卸载
    re_path(r'^instances/floating_ips$', views.FloatingIpInstancesRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'delete': 'destroy'})),
    re_path(r'^instances/volumes$', views.VolumeAttachmentsRestfulViews.as_view(
        actions={'post': 'create', 'delete': 'destroy'})),

    # resource: object storage
    re_path(r'^obs/buckets$', views.ObsBucketsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'})),
    re_path(r'^obs/bucket/(?P<container_name>[^/]+)$', views.ObsRestfulViews.as_view(
        actions={'get': 'show_bucket'})),
    re_path(r'^obs/files/(?P<container_name>\S+)/(?P<object_name>\S+)$', views.ObsFilesRestfulViews.as_view(
        actions={'get': 'retrieve'})),
    re_path(r'^obs/files$', views.ObsFilesRestfulViews.as_view(
        actions={'post': 'create'})),
    re_path(r'^obs/objects$', views.ObsObjectsRestfulViews.as_view(
        actions={'get': 'list', 'delete': 'destroy'})),
    re_path(r'^obs/object/(?P<container_name>\S+)/(?P<object_name>\S+)$', views.ObsObjectRestfulViews.as_view(
        actions={'get': 'retrieve'})),
    re_path(r'^obs/object$', views.ObsObjectRestfulViews.as_view(
        actions={'post': 'create'})),


    # resource: accounts
    re_path(r'^iam/access_login$', views.IamAccountRestfulViews.as_view(
        actions={'post': 'login'})),

    re_path(r'^iam/access_keys$', views.IamAccountRestfulViews.as_view(
        actions={'get': "retrieve_key"})),


    # resource: keypairs
    re_path(r'^keypairs$', views.KeypairsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'delete': 'destroy'})),


    # resource: floating IPs
    re_path(r'^floating_ips/firewalls$', views.FipRestfulViews.as_view(
        actions={'post': 'associate_firewall'})),
    re_path(r'^floating_ips/quotas$', views.FloatingIpQuotasRestfulViews.as_view(
        actions={'get': 'retrieve', 'put': 'update'})),
    re_path(r'^floating_ips$', views.FloatingIPsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'delete': 'destroy'})),


    # vbs
    # resource: volumes
    re_path(r'^vbs/volumes/quotas$', views.VbsRestfulViews.as_view(
        actions={'get': 'volume_quota'})),
    re_path(r'^vbs/volumes/types$', views.VbsRestfulViews.as_view(
        actions={'post': 'volume_type_list'})),
    re_path(r'^vbs/volumes$', views.VolumesRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'put': 'update', 'delete': 'destroy'})),

    # resource: volume backups
    re_path(r'^vbs/volume/backups/action_restore$', views.VbsRestfulViews.as_view(
        actions={'post': 'volume_backup_restore'})),
    re_path(r'^vbs/volume/backups$', views.VolumeBackupsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'delete': 'destroy'})),

]
