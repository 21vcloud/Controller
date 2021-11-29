# -*- coding: utf-8 -*-

from rest_framework import serializers


class BaremetalAuditListSerializer(serializers.Serializer):
    page_no = serializers.IntegerField(default=1)
    page_size = serializers.IntegerField(default=20)
    sort = serializers.CharField(default="desc")
    order_by = serializers.CharField(default='time')
    start_time = serializers.CharField(required=False)
    end_time = serializers.CharField(required=False)
    service_type = serializers.CharField(required=False)
    resource_type = serializers.CharField(required=False)
    resource_name = serializers.CharField(required=False)
    trace_type = serializers.CharField(required=False)
    region = serializers.CharField(required=False)
    event_type = serializers.CharField(required=False)
    user_id = serializers.CharField(required=False)
