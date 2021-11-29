# -*- coding: utf-8 -*-

from django.conf.urls import url

from baremetal_service.bw_views import BmSharedBandwidthsViews, BmSharedBandwidthViews, BmSharedBandwidthFipViews
from baremetal_service.views import BaremetalServiceFloatingIPViews

urlpatterns = [

    # 共享带宽实例管理
    # 功能：购买，列表，编辑，详情，删除/批量删除

    # resource: shared_bandwidths_order
    # 功能：购买
    url(r'^shared_bandwidths_order$', BmSharedBandwidthsViews.as_view(
        actions={'post': 'create'})),

    # resource: shared_bandwidths
    # 功能：列表，编辑，删除/批量删除
    url(r'^shared_bandwidths$', BmSharedBandwidthsViews.as_view(
        actions={'get': 'list', 'put': 'update', 'post': 'destroy'})),

    # resource: shared_bandwidth
    # 功能：搜索详情
    url(r'shared_bandwidth$', BmSharedBandwidthViews.as_view(
        actions={'post': 'search'})),

    # resource: floating IP
    # 功能：添加弹性公网IP，移除弹性公网IP
    url(r'^shared_bandwidth/(?P<bandwidth_id>[0-9a-fA-F-]{1,})/floating_ips$',
        BmSharedBandwidthFipViews.as_view(actions={'get': "list_bandwidth_floatingips"})),
    url(r'^floating_ip/(?P<floating_ip_id>[0-9a-fA-F-]{1,})/shared_bandwidths$',
        BmSharedBandwidthFipViews.as_view(actions={'get': "list_floatingip_bandwidths"})),

    url(r'^shared_bandwidth/(?P<bandwidth_id>[0-9a-fA-F-]{1,})/attach_floating_ips$',
        BmSharedBandwidthFipViews.as_view(actions={'post': 'attach'},
                                          name='bandwidth_attach_floatingips')),

    url(r'^shared_bandwidth/(?P<bandwidth_id>[0-9a-fA-F-]{1,})/detach_floating_ips$',
        BmSharedBandwidthFipViews.as_view(actions={'post': 'detach'},
                                          name='bandwidth_detach_floatingips')),

    # 裸金属平台中涉及的更新：弹性公网IP（floating_ip）
    # 功能：列表，删除
    url(r'^floating_ips$', BaremetalServiceFloatingIPViews.as_view(
        actions={'get': 'floating_ip_list', 'delete': 'floating_ip_delete'})),

]
