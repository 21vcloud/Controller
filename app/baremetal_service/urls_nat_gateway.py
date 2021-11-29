# -*- coding: utf-8 -*-

from django.conf.urls import url, re_path
from rest_framework.routers import DefaultRouter

from baremetal_service.nat_view import NatGateWayViews, DnatRuleViews


urlpatterns = [
    re_path(r'^gateway$', NatGateWayViews.as_view({"post": "create", "get": "list", }),
            name="nat_gateway"),
    re_path(r'^gateway/(?P<nat_gateway_id>[0-9a-fA-F-]{1,})$', NatGateWayViews.as_view({"get": "retrieve",
                                                                                        "delete": "destroy",
                                                                                       "put": "update"}),
            name="nat_gateway"),
    re_path(r'^gateway/get_available_vpc$', NatGateWayViews.as_view({"get": "get_available_vpc"}),
            name="get_available_vpc"),
    re_path(r'^gateway/(?P<nat_gateway_id>[0-9a-fA-F-]{1,})/rule_get_ports', DnatRuleViews.as_view(
        {"get": "get_ports"}), name='rule_get_ports'),
    re_path(r'^gateway/(?P<nat_gateway_id>[0-9a-fA-F-]{1,})/rule_get_floatingips', DnatRuleViews.as_view(
        {"get": "get_floatingips"}), name="rule_get_floatingip"),
    re_path(r'^gateway/(?P<nat_gateway_id>[0-9a-fA-F-]{1,})/dnat_rule$', DnatRuleViews.as_view(
        actions={"post": "create"}), name='dnat_rule'),
    re_path(r'^gateway/(?P<nat_gateway_id>[0-9a-fA-F-]{1,})/dnat_rule/(?P<nat_rule_id>[0-9a-fA-F-]{1,})$',
            DnatRuleViews.as_view({"put": "update", "delete": "destroy", }), name='dnat_rule'),
    re_path(r'^gateway/(?P<nat_gateway_id>[0-9a-fA-F-]{1,})/dnat_rule/delete_rules', DnatRuleViews.as_view(
        {"post": "delete_rules"}, name='delet_dnat_rules'))
]