# -*- coding: utf-8 -*-

from django.conf.urls import url
from baremetal_openstack import views

urlpatterns = [
    url(r'create_vpc', views.NeutronViews.as_view({"post": "create_vpc"}), name="create_vpc"),
    url(r'list_vpcs', views.NeutronViews.as_view({"get": "list_vpcs"}), name='list_vpcs'),
    url(r'update_vpc', views.NeutronViews.as_view({"post": "update_vpc"}), name='update_vpc'),
    url(r'delete_vpc', views.NeutronViews.as_view({"post": "delete_vpc"}), name='delete_vpc'),
    url(r'list_networks_by_vpc', views.NeutronViews.as_view({"get": "list_networks_by_vpc"}),
        name='list_networks_by_vpc'),
    url(r'add_network_by_vpc', views.NeutronViews.as_view({"post": "add_network_by_vpc"}),
        name='add_network_by_vpc'),
    url(r'update_network_by_vpc', views.NeutronViews.as_view({"post": "update_network_by_vpc"}),
        name='update_network_by_vpc'),
    url(r'delete_network_by_vpc', views.NeutronViews.as_view({"post": "delete_network_by_vpc"}),
        name='delete_network_by_vpc'),

    # firewall
    url(r'create_firewall', views.FirewallViews.as_view({"post": "create_firewall"}), name="create_firewall"),
    url(r'^list_firewalls$', views.FirewallViews.as_view({"get": "list_firewalls"}), name='list_firewalls'),
    url(r'^list_firewall_rules$', views.FirewallViews.as_view({"get": "list_firewall_rules"}), name='list_firewall_rules'),
    url(r'^update_firewall$', views.FirewallViews.as_view({"post": "update_firewall"}), name='update_firewall'),
    url(r'^delete_firewall$', views.FirewallViews.as_view({"post": "delete_firewall"}), name='delete_firewall'),
    url(r'^add_firewall_rule$', views.FirewallViews.as_view({"post": "add_firewallrule"}),
        name='create_firewallrule'),
    url(r'^update_firewallrule$', views.FirewallViews.as_view({"post": "update_firewallrule"}),
        name='update_firewall_rule'),
    url(r'^delete_firewallrule$', views.FirewallViews.as_view({"post": "delete_firewallrule"}),
        name='delete_firewall_rule'),



]
