# -*- coding:utf-8 -*-

import os
import logging

from django.http import HttpResponse
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from BareMetalControllerBackend.settings import (DATA_CFG_LIST, ROLE_CFG_LIST, USER_CFG_LIST)

from account.auth import utils as auth_utils
from account.repository.serializers import TokenParameter
from account.repository.auth_models import (BmProject, BmUserInfo, BmMappingUserProject)
from common.access_control.base import *
from common.lark_common.model.common_model import ResponseObj
from access_control.models import (RoleUser, RolePermission, Element, Role)
from access_control import serializers

# Create your views here.


class BaseClass(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.module_dir = os.path.dirname(__file__)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def get_project_obj(response_obj, project_id, project_name):
        project_obj = None
        if not (project_id or project_name):
            pass

        elif project_id:
            try:
                project_obj = BmProject.objects.get(id=project_id)
            except BmProject.DoesNotExist:
                response_obj.content = "not find project."
                response_obj.is_ok = False
                response_obj.no = 404
        else:
            try:
                project_obj = BmProject.objects.get(project_name=project_name)
            except BmProject.DoesNotExist:
                response_obj.content = "not find project."
                response_obj.is_ok = False
                response_obj.no = 404
        return response_obj, project_obj


class Console(BaseClass):
    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        query_serializer=serializers.ConsoleQueryListSerializer,
        responses={200: serializers.ConsoleListSerializer},
        operation_description="获取前台权限接口"
    )
    @auth_utils.token_verify
    # @check_element_permission
    def get(self, request):
        response_obj = ResponseObj()
        query_serializer = serializers.ConsoleQueryListSerializer(data=request.query_params.dict())
        query_serializer.is_valid(True)
        query_data = query_serializer.validated_data
        user = request.session["username"]
        element_type = query_data['type']
        owner_path = query_data['owner_path']
        project_name = query_data['project_name']
        permission_type = 'element'
        try:
            owner = BmProject.objects.get(project_name=project_name)
        except BmProject.DoesNotExist:
            response_obj.content = "Can not find project_name."
            response_obj.is_ok = False
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")
        role_id_list = RoleUser.objects.filter(
            user__account=user,
            role__owner=owner.id
        ).values_list(
            'role__id',
            flat=True
        )
        if not role_id_list:
            role_id_list = RoleUser.objects.filter(
                user__account=user
            ).values_list(
                'role__id',
                flat=True
            )

        element_uuid_list = RolePermission.objects.filter(
            role__id__in=role_id_list,
            permission__type=permission_type
        ).values_list(
            'permission__type_id',
            flat=True
        )

        res_list = Element.objects.filter(
            uuid__in=element_uuid_list
        ).filter(
            owner_path=owner_path,
            type=element_type
        ).order_by('sort_id')

        permission_list = res_list.values_list('url_path', flat=True)
        serializer = serializers.ConsoleListSerializer(res_list, many=True)
        bar_list = serializer.data
        response_obj.content = {
            "permission_list": list(permission_list),
            "bar_list": bar_list
        }
        return HttpResponse(response_obj.to_json(), content_type="application/json")


class Button(BaseClass):
    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        query_serializer=serializers.ButtonQueryListSerializer,
        operation_description="获取button权限接口"
    )
    @auth_utils.token_verify
    def get(self, request):
        response_obj = ResponseObj()
        query_serializer = serializers.ButtonQueryListSerializer(data=request.query_params.dict())
        query_serializer.is_valid(True)
        query_data = query_serializer.validated_data
        user = request.session["username"]
        owner_path = query_data['owner_path']
        project_name = query_data['project_name']
        permission_type = 'element'
        try:
            owner = BmProject.objects.get(project_name=project_name)
        except BmProject.DoesNotExist:
            response_obj.content = "Can not find project_name."
            response_obj.is_ok = False
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")
        role_id_list = RoleUser.objects.filter(
            user__account=user,
            role__owner=owner.id
        ).values_list(
            'role__id',
            flat=True
        )
        if not role_id_list:
            role_id_list = RoleUser.objects.filter(
                user__account=user
            ).values_list(
                'role__id',
                flat=True
            )

        element_uuid_list = RolePermission.objects.filter(
            role__id__in=role_id_list,
            permission__type=permission_type
        ).values_list(
            'permission__type_id',
            flat=True
        )

        res_list = Element.objects.filter(
            uuid__in=element_uuid_list
        ).filter(
            owner_path=owner_path,
            type="button"
        ).order_by('sort_id')

        element_list = Element.objects.filter(owner_path=owner_path, type="button").order_by('sort_id')

        submit_list = []
        select_list = []
        for button_info in element_list:
            if button_info in res_list:
                disable = False
            else:
                disable = True
            button_info_dict = {
                "disabled": disable,
                "element_id": button_info.element_id,
                "html_laber": button_info.html_laber,
                "id": button_info.id,
                "info": button_info.info,
                "owner_path": button_info.owner_path
            }
            button_dict = eval(button_info.info)
            if button_dict['type'] == 'submit':
                submit_list.append(button_info_dict)
            elif button_dict['type'] == 'list':
                select_list.append(button_info_dict)

        response_obj.content = {
            "submit_list": submit_list,
            "select_list": select_list
        }
        return HttpResponse(response_obj.to_json(), content_type="application/json")


class RoleListView(BaseClass):
    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        request_body=serializers.RolePostSerializer,
        responses={200: "successful"},
        operation_description="项目角色初始化"
    )
    @auth_utils.token_verify
    @check_element_permission
    def post(self, request):
        response_obj = ResponseObj()
        response_obj.content = "successful."
        response_obj.no = 200

        data_serializer = serializers.RolePostSerializer(data=request.data)
        data_serializer.is_valid(True)
        query_data = data_serializer.validated_data
        project_id = query_data.get("project_id", None)
        project_name = query_data.get("project_name", None)

        response_obj, project_obj = self.get_project_obj(response_obj, project_id, project_name)
        if not response_obj.no == 200:
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        access_set_obj = AccessSet()
        for cfg in ROLE_CFG_LIST:
            file_path = os.path.join(self.module_dir, 'management/commands/cfg/%s' % cfg)
            info_list = open(file_path, 'rb').read()
            if project_obj:
                res = access_set_obj.switch_role(cfg, eval(info_list), project_obj.id)
            else:
                res = access_set_obj.switch_role(cfg, eval(info_list))
            if not res:
                response_obj.is_ok = res
                response_obj.content = "error cfg_type."
                response_obj.no = 404
        return HttpResponse(response_obj.to_json(), content_type="application/json")

    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        request_body=serializers.RoleDeleteSerializer,
        responses={200: "successful"},
        operation_description="项目角色删除"
    )
    @auth_utils.token_verify
    @check_element_permission
    def delete(self, request):
        response_obj = ResponseObj()
        response_obj.content = "successful."
        response_obj.no = 200

        data_serializer = serializers.RoleDeleteSerializer(data=request.data)
        data_serializer.is_valid(True)
        query_data = data_serializer.validated_data
        project_id = query_data["project_id"]

        try:
            owner = BmProject.objects.get(id=project_id)
        except BmProject.DoesNotExist:
            response_obj.content = "not find project."
            response_obj.is_ok = False
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        access_set_obj = AccessSet()
        for cfg in ROLE_CFG_LIST:
            file_path = os.path.join(self.module_dir, 'management/commands/cfg/%s' % cfg)
            info_list = open(file_path, 'rb').read()
            res = access_set_obj.delete_role(eval(info_list), owner.id)
            if not res:
                response_obj.is_ok = res
                response_obj.content = "error cfg_type."
                response_obj.no = 404
        return HttpResponse(response_obj.to_json(), content_type="application/json")


class PermissionListView(BaseClass):
    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        responses={200: "successful"},
        operation_description="权限元素初始化"
    )
    @auth_utils.token_verify
    @check_element_permission
    def post(self, request):
        response_obj = ResponseObj()
        access_set_obj = AccessSet()
        response_obj.content = "successful."
        response_obj.no = 200

        for cfg in DATA_CFG_LIST:
            file_path = os.path.join(self.module_dir, 'management/commands/cfg/%s' % cfg)
            info_list = open(file_path, 'rb').read()
            res = access_set_obj.switch_data(cfg, eval(info_list))
            if not res:
                response_obj.is_ok = res
                response_obj.content = "error cfg_type."
                response_obj.no = 404
        return HttpResponse(response_obj.to_json(), content_type="application/json")


class BaseRoleUserListView(BaseClass):
    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        request_body=serializers.BaseRoleUserPostSerializer,
        responses={200: "successful"},
        operation_description="用户授权"
    )
    # @auth_utils.token_verify
    # @check_element_permission
    def post(self, request):
        response_obj = ResponseObj()
        response_obj.content = "successful."
        response_obj.no = 200

        data_serializer = serializers.BaseRoleUserPostSerializer(data=request.data)
        data_serializer.is_valid(True)
        query_data = data_serializer.validated_data
        email = query_data["email"]
        project_name = query_data.get("project_name", None)
        project_id = query_data.get("project_id", None)
        level = query_data["level"]

        response_obj, project_obj = self.get_project_obj(response_obj, project_id, project_name)
        if not response_obj.no == 200:
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        try:
            user = BmUserInfo.objects.get(account=email)
        except BmUserInfo.DoesNotExist:
            response_obj.is_ok = False
            response_obj.content = "%s user mail not find" % email
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        for cfg in USER_CFG_LIST:
            file_path = os.path.join(self.module_dir, 'management/commands/cfg/%s' % cfg)
            info_list = eval(open(file_path, 'rb').read()).get(level)
            if project_obj:
                res = AccessSet.add_role_user(user, info_list, project_obj.id)
            else:
                res = AccessSet.add_role_user(user, info_list)
            if not res:
                response_obj.is_ok = res
                response_obj.content = "error cfg_type."
                response_obj.no = 404
        return HttpResponse(response_obj.to_json(), content_type="application/json")

    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        request_body=serializers.BaseRoleUserDeleteSerializer,
        responses={200: "successful"},
        operation_description="用户授权"
    )
    @auth_utils.token_verify
    @check_element_permission
    def delete(self, request):
        response_obj = ResponseObj()
        response_obj.content = "successful."
        response_obj.no = 200

        data_serializer = serializers.BaseRoleUserDeleteSerializer(data=request.data)
        data_serializer.is_valid(True)
        query_data = data_serializer.validated_data
        email = query_data["email"]
        project_id = query_data["project_id"]

        try:
            project_obj = BmProject.objects.get(id=project_id)
        except BmProject.DoesNotExist:
            response_obj.is_ok = False
            response_obj.content = "not find project."
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        try:
            user = BmUserInfo.objects.get(account=email)
        except BmUserInfo.DoesNotExist:
            response_obj.is_ok = False
            response_obj.content = "%s user mail not find" % email
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        for cfg in USER_CFG_LIST:
            file_path = os.path.join(self.module_dir, 'management/commands/cfg/%s' % cfg)
            info_list = eval(open(file_path, 'rb').read()).get('1')
            res = AccessSet.delete_role_user(user, info_list, project_obj.id)
            if not res:
                response_obj.is_ok = res
                response_obj.content = "error cfg_type."
                response_obj.no = 404
        return HttpResponse(response_obj.to_json(), content_type="application/json")


class RoleUserListView(BaseClass):
    @swagger_auto_schema(
        manual_parameters=TokenParameter,
        request_body=serializers.RoleUserPostSerializer,
        responses={200: "successful"},
        operation_description="用户授权"
    )
    # @auth_utils.token_verify
    def post(self, request):
        response_obj = ResponseObj()
        response_obj.content = "successful."
        response_obj.no = 200

        data_serializer = serializers.RoleUserPostSerializer(data=request.data)
        data_serializer.is_valid(True)
        query_data = data_serializer.validated_data
        email = query_data["email"]
        role_name = query_data["role_name"]

        try:
            user_obj = BmUserInfo.objects.get(account=email)
        except BmUserInfo.DoesNotExist:
            response_obj.is_ok = False
            response_obj.content = "can not find user: %s." % email
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")
        try:
            role_obj = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            response_obj.is_ok = False
            response_obj.content = "can not find user: %s." % email
            response_obj.no = 404
            return HttpResponse(response_obj.to_json(), content_type="application/json")

        try:
            RoleUser.objects.create(user=user_obj, role=role_obj)
        except Exception as ex:
            print(ex)
            response_obj.is_ok = False
            response_obj.content = str(ex)
            response_obj.no = 500
            return HttpResponse(response_obj.to_json(), content_type="application/json")
        return HttpResponse(response_obj.to_json(), content_type="application/json")
