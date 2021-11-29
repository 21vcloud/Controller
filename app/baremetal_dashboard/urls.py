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

from baremetal_dashboard.views import FrontEndViews,BaremetalViews

urlpatterns = [
    url(r'get_info_by_key', FrontEndViews.as_view({"get": "get_info_by_key"}), name='get_info_by_key'),
    url(r'^contact_to_us$', FrontEndViews.as_view({"post": "view_contact_to_us"}), name='contact_to_us'),
    url(r'baremetal_list', BaremetalViews.as_view({"get": "baremetal_list"}), name='baremetal_list'),
    url(r'^contact_to_us_for_discount$', FrontEndViews.as_view({"post": "view_contact_to_us_for_discount"}), name='contact_to_us_for_discount'),
]
