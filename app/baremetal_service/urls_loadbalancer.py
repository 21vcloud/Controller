# -*- coding: utf-8 -*-

from django.conf.urls import url, re_path
from baremetal_service import views

urlpatterns = [
    # Load_Balancers
    re_path(r'^load_balancers/(?P<loadbalancer_id>[0-9a-zA-Z-]{1,})$', views.LoadBalanceRestfulViews.as_view(
        actions={'delete': 'destroy', 'put': 'update', 'get': 'show_load_balancers'})),
    re_path(r'^load_balancers$', views.LoadBalanceRestfulViews.as_view(actions={'get': 'list', 'post': 'create'})),

    # Flavor
    re_path(r'^flavors$', views.FlavorRestfulViews.as_view(
        actions={'get': 'list'})),

    # 绑定  解绑
    re_path(r'^attach_ip_to_lb$', views.BindPublicIPRestfulViews.as_view(
        actions={'post': 'create'})),
    re_path(r'^detach_ip_to_lb$', views.UnBandPublicIPRestfulViews.as_view(
        actions={'post': 'destroy'})),

    # 可用的弹性公网IP列表
    url(r'^available_ip_to_lb$', views.AvailablePublicIPRestfulViews.as_view({"get": "available_ip_to_lb"}),
        name='available_ip_to_lb'),

    # Listeners
    re_path(r'^listeners/(?P<listener_id>[0-9a-zA-Z-]{1,})$', views.ListenersRestfulViews.as_view(
        actions={'put': 'update', 'delete': 'destroy'})),
    # re_path(r'^sni_listeners$', views.ListenersRestfulViews.as_view(actions={'post': 'create_sni'})),
    re_path(r'^listeners$', views.ListenersRestfulViews.as_view(actions={'post': 'create'})),

    # L7 Policies and Rules
    re_path(r'^listeners/(?P<listener_id>[0-9a-zA-Z-]{1,})/policies$', views.PoliciesRestfulViews.as_view(
        actions={'post': 'create', 'get': 'retrieve'})),
    re_path(r'^policies/(?P<l7policy_id>[0-9a-zA-Z-]{1,})$', views.PoliciesRestfulViews.as_view(
        actions={'put': 'update', 'delete': 'destroy'})),
    re_path(r'^policies$', views.PoliciesRestfulViews.as_view(
        actions={'get': 'list'})),

    # L7 Pool Members
    re_path(r'^pools/(?P<pool_id>[0-9a-zA-Z-]{1,})/members/(?P<member_id>[0-9a-zA-Z-]{1,})$',
            views.PoolMembersRestfulViews.as_view(actions={'put': 'update', 'delete': 'destroy'})),
    re_path(r'^pools/(?P<pool_id>[0-9a-zA-Z-]{1,})/members$',
            views.PoolMembersRestfulViews.as_view(actions={'post': 'attach_pool', 'get': 'list'})),

    # L7 Pools
    re_path(r'^pools/(?P<pool_id>[0-9a-zA-Z-]{1,})/(?P<loadbalancer_id>[0-9a-zA-Z-]{1,})$',
            views.PoolsRestfulViews.as_view(
                actions={'get': 'retrieve', 'put': 'update'})),
    re_path(r'^pools/(?P<pool_id>[0-9a-zA-Z-]{1,})$', views.PoolsRestfulViews.as_view(
        actions={'delete': 'destroy'})),
    re_path(r'^pools$', views.PoolsRestfulViews.as_view(actions={'get': 'list', 'post': 'create'})),

    # L7 Health Monitor
    re_path(r'^pools/(?P<pool_id>[0-9a-zA-Z-]{1,})/health_monitors/(?P<healthmonitor_id>[0-9a-zA-Z-]{1,})$',
            views.HealthMonitorRestfulViews.as_view(
                actions={'put': 'update'})),
    re_path(r'^health_monitors/(?P<healthmonitor_id>[0-9a-zA-Z-]{1,})$',
            views.HealthMonitorRestfulViews.as_view(actions={'get': 'retrieve', 'delete': 'destroy'})),
    re_path(r'^health_monitors$', views.HealthMonitorRestfulViews.as_view(actions={'post': 'create'})),

    # TODO
    # Barbican Service
    re_path(r'^secrets$', views.SecretsRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create'})),
    re_path(r'^certificates/(?P<certificate_id>[0-9a-zA-Z-]{1,})$', views.CertificatesRestfulViews.as_view(
        actions={'delete': 'destroy'})),
    re_path(r'^certificates$', views.CertificatesRestfulViews.as_view(
        actions={'get': 'list', 'post': 'create', 'put': 'update'})),
    re_path(r'^quotas$', views.ProjectQuotasRestfulViews.as_view(
        actions={'get': 'list'})),

    # 获取负载均衡器下的资源池，针对对应监听器协议进行过滤，并且不绑定任何listener
    # url(r'available_pool_to_listener', views.AvailablePoolRestfulViews.as_view({"get": "available_pool_to_listener"}),
    #     name='available_pool_to_listener'),
    re_path(
        r'^available_pool_to_listener/(?P<loadbalancer_id>[0-9a-zA-Z-]{1,})/(?P<listener_protocol>[0-9a-zA-Z-]{1,})$',
        views.AvailablePoolRestfulViews.as_view(
            actions={'get': 'available_pool_to_listener'}))

]
