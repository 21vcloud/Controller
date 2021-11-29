# -*- coding: utf-8 -*-
import logging

from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from account.auth import utils as auth_utils
from account.repository import serializers as auth_serializers

from baremetal_audit.serializer import BaremetalAuditListSerializer
from baremetal_audit.handler import get_cloud_audit_api, get_userinfo_by_project
from common import utils
from common.lark_common.model.common_model import ResponseObj


class AuditViews(viewsets.ViewSet):

    def __init__(self):
        self.logger = logging.getLogger('request_info')

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         query_serializer=BaremetalAuditListSerializer)
    @utils.param_info
    @auth_utils.token_verify
    @utils.check_request_params(['page_no', 'page_size', 'sort', 'order_by',
                                 'start_time', 'end_time', 'service_type',
                                 'resource_type', 'resource_name', 'trace_type',
                                 'region', 'event_type', 'user_id', 'account_id',
                                 'trace_name'])
    def list(self, request):
        response_obj = ResponseObj()
        result = {}
        project_id = request.session.get('project_id')

        param_info = request.param_info.dict()
        param_info['project_id'] = project_id

        try:
            audit_response = get_cloud_audit_api().list_audit_log(**param_info)

            if audit_response.get("is_ok"):
                result['page'] = audit_response.get('page')
                result['data'] = audit_response.get('data')
            else:
                return response_obj.json_exception_serial(user_info="获取日志失败",
                                                          admin_info=audit_response.get('admin_info'), no=500)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="获取日志失败", admin_info=str(e), no=500)

        return response_obj.json_serial(info=result)

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter)
    @utils.param_info
    @auth_utils.token_verify
    def list_user(self, request):
        response_obj = ResponseObj()

        project_id = request.session.get('project_id')

        try:
            users = get_userinfo_by_project(project_id)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="获取当前项目下用户失败", admin_info=str(e), no=500)
        return response_obj.json_serial(users)
