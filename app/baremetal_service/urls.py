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
from baremetal_service.views import BaremetalServiceInstanceViews, BaremetalServiceBaseResource, \
    BaremetalServiceFloatingIPViews, BaremetalServiceForTimeTaskViews

urlpatterns = [

    # 服务器申请
    url(r'service_create', BaremetalServiceInstanceViews.as_view({"post": "view_create_baremetal_service"}), name='service_create'),
    url(r'service_order_query_by_account', BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_order_query_by_account"}), name='service_order_query_by_account'),
    url(r'service_order_all', BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_order_all"}), name='service_order_all'),

    url(r'service_instance_create', BaremetalServiceInstanceViews.as_view({"post": "view_baremetal_service_instance_create"}), name='instance_create'),
    url(r'service_instance_feedback', BaremetalServiceInstanceViews.as_view({"post": "view_baremetal_service_instance_feedback"}), name='instance_feedback'),
    url(r'service_order_delivery_update', BaremetalServiceInstanceViews.as_view({"post": "service_order_delivery_update"}), name='service_order_delivery_update'),
    url(r'service_machine_info_feedback', BaremetalServiceInstanceViews.as_view({"post": "service_machine_info_feedback"}), name='service_machine_info_feedback'),
    url(r'service_machine_get', BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_machine_get"}), name='service_machine_get'),
    url(r'service_order_retry', BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_retry"}), name='service_order_retry'),
    url(r'service_attached_info_of_instance', BaremetalServiceInstanceViews.as_view({"get": "service_attached_info_of_instance"}), name='service_attached_info_of_instance'),
    url(r'^monitoring_instance_list$',BaremetalServiceInstanceViews.as_view({"get": "monitoring_instance_list"}),
        name='monitoring_instance_list'),
    
    # 弹性公网IP申请服务
    url(r'floating_ip_create', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_create"}), name='floating_ip_create'),
    url(r'floating_ip_list', BaremetalServiceFloatingIPViews.as_view({"get": "floating_ip_list"}), name='floating_ip_list'),
    url(r'floating_ip_quotas_set', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_quotas_set"}), name='floating_ip_quotas_set'),
    url(r'floating_ip_attach_to_server', BaremetalServiceFloatingIPViews.as_view({"post": "attach_ip_to_server"}),
        name='attach_ip_to_server'),
    url(r'floating_ip_detach_from_server', BaremetalServiceFloatingIPViews.as_view({"post": "detach_ip_from_server"}),
        name='detachip_from_server'),
    url(r'floating_ip_delete', BaremetalServiceFloatingIPViews.as_view({"post": "floating_ip_delete"}), name='floating_ip_delete'),

    # base resource
    url(r'images_list', BaremetalServiceBaseResource.as_view({"get": "images_list"}), name='images_list'),
    url(r'flavor_list', BaremetalServiceBaseResource.as_view({"get": "flavor_list"}), name='flavor_list'),
    url(r'update_flavor_count', BaremetalServiceBaseResource.as_view({"post": "update_flavor_count"}), name='update_flavor_count'),
    url(r'qos_policy_list', BaremetalServiceBaseResource.as_view({"get": "qos_policy_list"}), name='qos_policy_list'),


    # 定时任务
    url(r'service_instance_in_use_count', BaremetalServiceForTimeTaskViews.as_view({"get": "service_instance_in_use_count"}), name='service_instance_in_use_count')
]
