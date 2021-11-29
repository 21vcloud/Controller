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
from django.urls import path
from django.views.decorators.cache import cache_page
from general_feature import views

urlpatterns = [
    # enterprise info
    path(r'monitor_alarm', views.MessageSend.as_view()),
    # url(r'^contract_create', AccountContractViews.as_view({"post": "contract_create"}), name='contract_create'),
]
