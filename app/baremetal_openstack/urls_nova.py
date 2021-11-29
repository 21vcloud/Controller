# -*- coding: utf-8 -*-

from django.conf.urls import url
from baremetal_openstack import views

urlpatterns = [
    #
    url(r'get_server_serial_console', views.InstanceViews.as_view({"get": "get_server_serial_console"}),
        name='get_server_serial_console'),

    url(r'get_instance_ports', views.InstanceViews.as_view({"get": "get_instance_ports"}), name="get_instance_ports"),

    # Session id url
    url(r'instance_create', views.InstanceViews.as_view({"post": "instance_create"}), name='instance_create'),
    url(r'instance_stop', views.InstanceViews.as_view({"post": "instance_stop"}), name='instance_stop'),
    url(r'instance_start', views.InstanceViews.as_view({"post": "instance_start"}), name='instance_start'),
    url(r'instance_restart', views.InstanceViews.as_view({"post": "instance_restart"}), name='instance_restart'),
    url(r'^instance_list$', views.InstanceViews.as_view({"get": "instance_list"}), name='instance_list'),
    url(r'^instance_list_not_in_slb_pool$', views.InstanceViews.as_view({"get": "instance_list_not_in_slb_pool"}),
        name='instance_list_not_in_slb_pool'),
    url(r'instance_delete', views.InstanceViews.as_view({"post": "instance_delete"}), name='instance_delete'),
    url(r'instance_list_by_os_active', views.InstanceViews.as_view(
        {"get": "instance_list_by_os_active"}), name='instance_list_by_os_active'),

    # url(r'volume_create', views.VolumeViews.as_view({"post": "volume_create"}), name='volume_create'),
    # url(r'volume_attach', views.VolumeViews.as_view({"post": "volume_attach"}), name='volume_attach'),
    url(r'keypair_create', views.KeyPairViews.as_view({"post": "keypair_create"}), name='keypair_create'),
    url(r'keypair_update', views.KeyPairViews.as_view({"post": "keypair_update"}), name='keypair_update'),
    url(r'keypair_delete', views.KeyPairViews.as_view({"post": "keypair_delete"}), name='keypair_delete'),
    url(r'keypair_list', views.KeyPairViews.as_view({"get": "keypair_list"}), name='keypair_list'),
    url(r'instance_attach_interface', views.InstanceViews.as_view({"post": "instance_attach_interface"}),
        name='instance_attach_interface'),
    url(r'instance_detach_interface', views.InstanceViews.as_view({"post": "instance_detach_interface"}),
        name='instance_detach_interface'),
    url(r'instance_list_interface', views.InstanceViews.as_view({"get": "instance_list_interface"}),
        name='instance_list_interface')
]
