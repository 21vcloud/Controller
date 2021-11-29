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

from account.views import AccountProjectViews
from django.views.decorators.cache import cache_page

urlpatterns = [
    # project info
    url(r'^project_create$', AccountProjectViews.as_view({"post": "project_create"}), name='project_create'),
    url(r'^project_update$', AccountProjectViews.as_view({"post": "project_update"}), name='project_update'),
    url(r'^project_delete$', AccountProjectViews.as_view({"post": "project_delete"}), name='project_delete'),
    url(r'^project_role_manage$', AccountProjectViews.as_view({"post": "project_role_manage"}), name='project_role_manage'),
    url(r'^query_all_project_info$', AccountProjectViews.as_view({"get": "query_all_project_info"}), name='query_all_project_info'),
    url(r'^project_info_query_by_keywords$', AccountProjectViews.as_view({"get": "project_info_query_by_keywords"}),
        name='project_info_query_by_keywords'),
    # url(r'^query_all_project_member_list$', AccountProjectViews.as_view({"get": "query_all_project_member_list"}), name='query_all_project_member_list'),
    url(r'^query_project_member_list_by_project$', AccountProjectViews.as_view({"get": "query_project_member_list_by_project"}), name='query_project_member_list_by_project'),
    url(r'^query_project_list_of_no_authorizer$', AccountProjectViews.as_view({"get": "query_project_list_of_no_authorizer"}),
        name='query_project_list_of_no_authorizer'),
    url(r'^query_project_list_by_account', AccountProjectViews.as_view({"get": "query_project_list_by_account"}),
        name='query_project_list_by_account'),
    url(r'^query_project_quotas', AccountProjectViews.as_view({"get": "query_project_quotas"}),
        name='query_project_quotas'),
    url(r'^update_project_quotas', AccountProjectViews.as_view({"post": "update_project_quotas"}),
        name='update_project_quotas'),
    # url(r'^query_all_user_list_to_project$', cache_page(60)(AccountProjectViews.as_view({"post": "query_all_user_list_to_project"})), name='query_all_user_list_to_project'),
]
