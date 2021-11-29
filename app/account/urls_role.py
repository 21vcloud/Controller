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

from account.views import AccountRoleViews, AccountRoleListViews
from django.views.decorators.cache import cache_page

urlpatterns = [
    # enterprise info
    url(r'^role_create', AccountRoleViews.as_view({"post": "role_create"}), name='role_create'),
    url(r'^role_update', AccountRoleViews.as_view({"post": "role_update"}), name='role_update'),
    url(r'^role_delete', AccountRoleViews.as_view({"post": "role_delete"}), name='role_delete'),
    url(r'^query_all_role_info',
        AccountRoleViews.as_view({"get": "query_all_role_info"}),
        name='query_all_role_info'),

    # restful
    url(r'^role', AccountRoleListViews.as_view()),
]
