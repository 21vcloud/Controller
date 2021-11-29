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

from account.views import AccountEnterpriseViews
from django.views.decorators.cache import cache_page

urlpatterns = [
    # enterprise info
    url(r'^enterprise_create', AccountEnterpriseViews.as_view({"post": "enterprise_create"}), name='enterprise_create'),
    url(r'^enterprise_update', AccountEnterpriseViews.as_view({"post": "enterprise_update"}), name='enterprise_update'),
    url(r'^enterprise_delete', AccountEnterpriseViews.as_view({"post": "enterprise_delete"}), name='enterprise_delete'),
    url(r'^query_all_enterprise_info', AccountEnterpriseViews.as_view({"get": "query_all_enterprise_info"}),
        name='query_all_enterprise_info'),
    url(r'^enterprise_info_query_by_keywords',
        cache_page(60)(AccountEnterpriseViews.as_view({"get": "enterprise_info_query_by_keywords"})),
        name='enterprise_info_query_by_keywords'),
]
