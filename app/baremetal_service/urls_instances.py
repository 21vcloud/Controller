# -*- coding: utf-8 -*-

from django.conf.urls import url


from baremetal_service import views
from baremetal_service.views import BaremetalServiceInstanceViews, BaremetalServiceBaseResource
from baremetal_openstack.views import InstanceViews as NovaInstanceViews
from rest_api.views import ServiceInstancesRestfulViews, ServiceInstanceRestfulViews, ServiceOrderRestfulViews

urlpatterns = [
    # service related
    # url(r'c_s_instances',
    #     BaremetalServiceInstanceViews.as_view({"post": "view_baremetal_service_instance_create"}),
    #     name='instance_create'),
    # url(r'fd_instances',
    #     BaremetalServiceInstanceViews.as_view({"put": "view_baremetal_service_instance_feedback"}),
    #     name='instance_feedback'),
    url(r'v1/flavor', BaremetalServiceBaseResource.as_view({"put": "update_flavor_count"}), name='update_flavor_count'),
    url(r'v1/images', BaremetalServiceBaseResource.as_view({"get": "images_list"}), name='images_list'),
    url(r'v1/flavors', BaremetalServiceBaseResource.as_view({"get": "flavor_list"}), name='flavor_list'),
    url(r'v1/qos_policies', BaremetalServiceBaseResource.as_view({"get": "qos_policy_list"}), name='qos_policy_list'),


    # server related
    # GET
    url(r'v1/interface_attachments', NovaInstanceViews.as_view({"get": "instance_list_interface"}),
        name='instance_list_interface'),
    url(r'v1/ports', NovaInstanceViews.as_view({"get": "get_instance_ports"}), name="get_instance_ports"),
    # url(r'instances$', views.InstanceViews.as_view({"get": "instance_list"}), name='instance_list'),
    # url(r'instance', views.InstanceViews.as_view(
    #     {"get": "instance_list_by_os_active"}), name='instance_list_by_os_active'),
    url(r'v1/orders', BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_order_all"}), name='service_order_all'),
    url(r'v1/machine', BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_machine_get"}), name='service_machine_get'),
    # url(r'a_order',
    #     BaremetalServiceInstanceViews.as_view({"get": "view_baremetal_service_order_query_by_account"}),
    #     name='service_order_query_by_account'),

    # POST
    url(r'v1/services', BaremetalServiceInstanceViews.as_view({"post": "view_create_baremetal_service"}), name='service_create'),
    # url(r'c_instance', views.InstanceViews.as_view(), name='instance_create'),
    url(r'v1/instance_stop', NovaInstanceViews.as_view({"post": "instance_stop"}), name='instance_stop'),
    url(r'v1/instance_start', NovaInstanceViews.as_view({"post": "instance_start"}), name='instance_start'),
    url(r'v1/instance_restart', NovaInstanceViews.as_view({"post": "instance_restart"}), name='instance_restart'),
    # url(r'v1/interface_attachment', views.InstanceViews.as_view({"post": "instance_attach_interface"}),
    #     name='instance_attach_interface'),

    # DELETE
    # url(r'd_instance', views.InstanceViews.as_view({"delete": "instance_delete"}), name='instance_delete'),
    # url(r'v1/interface_detachment', views.InstanceViews.as_view({"delete": "instance_detach_interface"}),
    #     name='instance_detach_interface'),

    # PUT
    url(r'v1/machines', BaremetalServiceInstanceViews.as_view({"put": "service_machine_info_feedback"}), name='service_machine_info_feedback'),
    # url(r'order', BaremetalServiceInstanceViews.as_view({"put": "service_order_delivery_update"}), name='service_order_delivery_update'),

    # all-in REST API
    url(r'v1/instances', ServiceInstancesRestfulViews.as_view()),
    url(r'v1/instance', ServiceInstanceRestfulViews.as_view()),
    url(r'v1/order', BaremetalServiceInstanceViews.as_view(actions={'get': 'view_baremetal_service_order_query_by_account'})),
    url(r'v1/interface_attachment', NovaInstanceViews.as_view(actions={'post': 'instance_attach_interface', 'delete': 'instance_detach_interface'})),
    
    
    ]