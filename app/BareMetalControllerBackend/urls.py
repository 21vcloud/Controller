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
from django.conf.urls import include
from django.conf.urls import url
from django.shortcuts import redirect
from django.contrib import admin
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

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

    url(r'^21vianet_cloud/dev/cached/api/$', SchemaView.with_ui('swagger', cache_timeout=None), name='cschema-swagger-ui'),
    # url(r'^$', root_redirect),
    # url(r'^admin/', admin.site.urls),
    url(r'^service/', include('baremetal_service.urls'), name='service'),
    url(r'^service_ip/', include('baremetal_service.urls_floating_ip'), name='service_ip'),
    url(r'^service_volume/', include('baremetal_service.urls_volume'), name='service_volume'),
    url(r'^service_object/', include('baremetal_service.urls_object'), name='object'),
    url(r'^service_material/', include('baremetal_service.urls_material'), name='material'),
    url(r'^sbw/', include('baremetal_service.urls_bandwidth'), name='shared_bandwidth'),
    url(r'^lb/', include('baremetal_service.urls_loadbalancer'), name='load_balancer'),
    url(r'nat/', include('baremetal_service.urls_nat_gateway'), name='natgateway'),

    # dashboard
    url(r'^baremental/', include('baremetal_dashboard.urls'), name='baremental'),
    #
    # # account
    url(r'^account/', include('account.urls'), name='account'),
    url(r'^account_user/', include('account.url_user'), name='account_user'),
    url(r'^account_project/', include('account.urls_project'), name='project'),
    url(r'^account_enterprise/', include('account.urls_enterprise'), name='enterprise'),
    url(r'^account_role/', include('account.urls_role'), name='role'),
    url(r'^account_contract/', include('account.urls_contract'), name='urls_contract'),

    # openstack
    url(r'^auth/', include('baremetal_openstack.urls'), name='auth'),
    url(r'^nova/', include('baremetal_openstack.urls_nova'), name='nova'),
    url(r'^neutron/', include('baremetal_openstack.urls_neutron'), name='neutron'),

    url(r'^access_control/', include('access_control.urls'), name='access'),

    url(r'^general/', include('general_feature.urls'), name='general_feature'),

    # Audit
    url(r'^audit/', include('baremetal_audit.urls'), name='audit'),

    # REST Service APIs
    url(r'^v1/', include('rest_api.urls'), name='rest api'),

]
