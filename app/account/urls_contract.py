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

from account.views import AccountContractViews
from django.views.decorators.cache import cache_page

urlpatterns = [
    # enterprise info
    url(r'^contract_create', AccountContractViews.as_view({"post": "contract_create"}), name='contract_create'),
    url(r'^contract_update', AccountContractViews.as_view({"post": "contract_update"}), name='contract_update'),
    url(r'^contract_delete', AccountContractViews.as_view({"post": "contract_delete"}), name='contract_delete'),
    url(r'^query_all_contract_info',
        AccountContractViews.as_view({"get": "query_all_contract_info"}),
        name='query_all_contract_info'),
    url(r'^query_contract_info_of_authorizer',
        AccountContractViews.as_view({"get": "query_contract_info_of_authorizer"}),
        name='query_contract_info_of_authorizer'),
    url(r'^query_contract_list_belong_to_authorizer_by_project_id',
        AccountContractViews.as_view({"get": "query_contract_list_belong_to_authorizer_by_project_id"}),
        name='query_contract_list_belong_to_authorizer_by_project_id'),
    url(r'^contract_terminate', AccountContractViews.as_view({"post": "contract_terminate"}), name='contract_terminate'),
    url(r'^contract_start', AccountContractViews.as_view({"post": "contract_start"}),
        name='contract_start'),
    url(r'^contract_prior_terminate_remind', AccountContractViews.as_view({"get": "contract_prior_terminate_remind"}),
        name='contract_prior_terminate_remind'),
    url(r'^contract_resource_query_by_contract_number', AccountContractViews.as_view(
        {"get": "contract_resource_query_by_contract_number"}), name='contract_resource_query_by_contract_number'),

]
