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

from account.views import AccountUserViews, RequestInfoViews

urlpatterns = [
    url(r'token_verify', AccountUserViews.as_view({"get": "token_verify"}), name='token_verify'),
    url(r'register', AccountUserViews.as_view({"post": "register"}), name='register'),
    url(r'user_info_update', AccountUserViews.as_view({"post": "user_info_update"}), name='user_info_update'),
    url(r'user_delete', AccountUserViews.as_view({"post": "user_delete"}), name='user_delete'),

    url(r'login', AccountUserViews.as_view({"post": "login"}), name='login'),
    url(r'project_switch', AccountUserViews.as_view({"post": "project_switch"}), name='project_switch'),
    url(r'logout', AccountUserViews.as_view({"post": "logout"}), name='logout'),
    url(r'^update_password$', AccountUserViews.as_view({"post": "update_password"}), name='update_password'),
    url(r'^confirm_update_password',
        AccountUserViews.as_view({"post": "confirm_update_password"}),
        name='confirm_update_password_get'),

    url(r'^update_password_by_user',
        AccountUserViews.as_view({"post": "update_password_by_user"}),
        name='update_password_by_user'),
    url(r'^user_agreement_update$', AccountUserViews.as_view({"post": "user_agreement_update"}),
        name='user_agreement_update'),

    url(r'^phone_code_get$', AccountUserViews.as_view({"get": "phone_code_get"}), name='phone_code_get'),
    url(r'^phone_code_verify$', AccountUserViews.as_view({"post": "phone_code_verify"}), name='phone_code_verify'),

    # 通过邮箱进行用户验证
    url(r'^email_code_get$', AccountUserViews.as_view({"get": "email_code_get"}), name='email_code_get'),
    url(r'^email_code_verify$', AccountUserViews.as_view({"post": "email_code_verify"}), name='email_code_verify'),
    url(r'^email_update$', AccountUserViews.as_view({"post": "email_update"}), name='email_update'),

    # 更新phone
    url(r'^phone_update$', AccountUserViews.as_view({"post": "phone_update"}), name='phone_update'),

    url(r'^query_account_info_by_keywords',
        AccountUserViews.as_view({"get": "view_query_account_info_by_keywords"}),
        name='query_account_info_by_keywords'),
    # url(r'^query_account_info_in_condition',
    #     AccountUserViews.as_view({"post": "query_account_info_in_condition"}),
    #     name='query_account_info_in_condition'),
    url(r'^query_all_account_info', AccountUserViews.as_view({"get": "query_all_account_info"}),
        name='query_all_account_info'),
    url(r'^query_account_info_by_account', AccountUserViews.as_view({"get": "query_account_info_by_account"}),
        name='query_account_info_by_account'),

    url(r'^query_all_frame_authorizer_account', AccountUserViews.as_view({"get": "view_query_all_frame_authorizer_account"}),
        name='query_all_frame_authorizer_account'),

    url(r'^query_all_authorizer_account', AccountUserViews.as_view({"get": "view_query_all_authorizer_account"}),
        name='query_all_authorizer_account'),

    url(r'get_websocket', AccountUserViews.as_view({"get": "get_websocket"}), name='get_websocket'),

    url(r'^request_info_record_create', RequestInfoViews.as_view({"post": "request_info_record_create"}), name='request_info_record_create'),
]
