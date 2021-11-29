# -*- coding:utf-8 -*-
# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from django.conf.urls import url
from baremetal_service.views import BaremetalServiceFloatingIPViews

urlpatterns = [
    # 弹性公网IP申请服务
    url(r'floating_ip_create_with_order$',
        BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_create_with_order"}),
        name='floating_ip_create_with_order'),
    url(r'floating_ip_create$', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_create"}),
        name='floating_ip_create'),
    url(r'floating_ip_list$', BaremetalServiceFloatingIPViews.as_view({"get": "floating_ip_list"}),
        name='floating_ip_list'),
    url(r'floating_ip_list_no_attached$', BaremetalServiceFloatingIPViews.as_view({"get": "floating_ip_list_no_attached"}),
        name='floating_ip_list_no_attached'),
    url(r'floating_ip_quotas_set$', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_quotas_set"}),
        name='floating_ip_quotas_set'),
    url(r'floating_ip_attach_to_server$', BaremetalServiceFloatingIPViews.as_view({"post": "attach_ip_to_server"}),
        name='attach_ip_to_server'),
    url(r'floating_ip_detach_from_server$', BaremetalServiceFloatingIPViews.as_view({"post": "detach_ip_from_server"}),
        name='detach_ip_from_server'),
    url(r'floating_ip_delete', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_delete"}),
        name='floating_ip_delete'),
    url(r'floating_ip_roll_back', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_roll_back"}),
        name='floating_ip_roll_back'),

    url(r'instance_list_avaliable_to_floating_ip',
        BaremetalServiceFloatingIPViews.as_view({"get": "instance_list_avaliable_to_floating_ip"}),
        name='instance_list_avaliable_to_floating_ip'),

    url(r'floating_ip_associate_firewall',
        BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_associate_firewall"}),
        name='floating_ip_associate_firewall'),
    url(r'^floating_ip_quota$', BaremetalServiceFloatingIPViews.as_view({"get": "floating_ip_quota"}),
        name="floating_ip_quota")
]
