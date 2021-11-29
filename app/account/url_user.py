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
from django.views.decorators.cache import cache_page

from account.views import UserViews

urlpatterns = [

    url(r'^query_all_account_info', UserViews.as_view({"get": "query_all_account_info"}),
        name='query_all_account_info'),

    url(r'^view_query_all_authorizer_account', UserViews.as_view({"get": "view_query_all_authorizer_account"}),
        name='view_query_all_authorizer_account'),

    url(r'^token_verify', UserViews.as_view({"get": "token_verify"}),
        name='token_verify'),

    url(r'^uid_list', UserViews.as_view({"get": "uid_list"}),
        name='uid_list')

]
