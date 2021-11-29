# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rest_api.models import AccessKey


class AccessKeyForm(admin.ModelAdmin):
    list_display = ('id', 'access_key', 'secret_key')
    search_fields = ('id', 'access_key', 'secret_key')


# admin.site.register(AccessKey, AccessKeyForm)