# -*- coding:utf-8 -*-

import logging
import time
import datetime

import jsonpickle
from django.db import transaction
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.views import APIView
from common.api_request import RequestClient, RequestClientTwo

from baremetal_audit import audit_types
from baremetal_audit.handler import send_cloud_audit_log_single_request, send_cloud_log_notification
from BareMetalControllerBackend.conf.env import EnvConfig
from account.auth import utils as auth_utils
from account.repository import auth_models
from account.repository import serializers
from account.repository import response_serializers
from account.repository.provider_account import AccountUserProvider, AccountProjectProvider, \
    AccountEnterpriseProvider, AccountRoleProvider, AccountContractProvider, RequestInfoProvider
from baremetal_openstack.repository.nova_provider import OpenstackClientProvider
from baremetal_openstack.repository.keystone_provider import KeystoneAuth
from common.lark_common.model.common_model import ResponseObj
from common.lark_common.utils import AESCipher
from common.access_control.base import check_element_permission, AccessSet
from baremetal_openstack import handler
from account.repository.auth_models import BmUserInfo
from access_control.views import RoleListView, BaseRoleUserListView, RoleUserListView


class UserViews(viewsets.ViewSet):
    def __init__(self):
        super(UserViews, self).__init__()
        self.account_user_provider = AccountUserProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    def make_params_to_uid(self, project_id, region_name="regionOne"):
        uid = ":".join([region_name, project_id])
        return uid

    # TODO  临时新加---用于冰海和艳雷那边获取数据
    @swagger_auto_schema(
        operation_description="获取所有授权人用户信息",
        query_serializer=serializers.UidAuthorizerSrializer,
        responses={200: response_serializers.AllAuthorizerAccountInfoResponsesSerializer})
    @auth_utils.param_info_decrypt
    def view_query_all_authorizer_account(self, request):
        try:
            # 查询授权人
            uuid = request.param_info.get("uuid")
            response_obj = self.account_user_provider.query_all_authorizer_account()

            if uuid:
                project_id = uuid.split(':')[1]

                # 查找角色授权人对应id
                role_obj = auth_models.BmRole.objects.get(role_name="授权人")
                role_id = role_obj.id
                user_project_map = auth_models.BmMappingUserProject.objects.filter(project_id=project_id)

                if not user_project_map:
                    response_obj.content = []

                for user_obj in user_project_map:
                    user_info_obj = auth_models.BmUserInfo.objects.filter(id=user_obj.account_id, role_id=role_id) \
                        .first()

                    response_obj.content = []
                    if user_info_obj:
                        user_info_obj.__dict__.pop("_state")
                        response_obj.content = user_info_obj
                        break

        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 查询账户信息
    @swagger_auto_schema(
        operation_description="查询所有用户信息",
        responses={200: response_serializers.AllAccountInfoResponsesSerializer},
    )
    @auth_utils.param_info_decrypt
    def query_all_account_info(self, request):
        try:
            # 查询用户
            response_obj = self.account_user_provider.query_all_account_info()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.TokenVerifyResponsesSerializer},
                         operation_description="用户登录状态验证接口")
    @auth_utils.param_info_decrypt
    @auth_utils.token_verify_single
    def token_verify(self, request):
        response_obj = ResponseObj()
        account_id = request.META["HTTP_ACCOUNTID"]
        # 查询用户的相关信息
        user_obj = BmUserInfo.objects.filter(id=account_id).first()
        user_dict = {
            "user_id": account_id,
            "user_name": user_obj.identity_name,
            "company_id": user_obj.enterprise_id,
            "email": user_obj.account,
            "mobile": user_obj.phone_number
        }
        response_obj.content = user_dict
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(operation_description="获取云监控授权uid列表")
    def uid_list(self, request):
        # TODO 增加了多区域以后需要增加相应的uid
        response_obj = ResponseObj()
        uid_list = []
        bm_project_info_obj = auth_models.BmProject.objects.all().exclude(status="deleted").order_by("-create_at")
        project_info_list = [u.__dict__ for u in bm_project_info_obj]
        for project_detail in project_info_list:
            uid = self.make_params_to_uid(project_id=project_detail.get("id"), region_name="regionOne")
            uid_list.append(uid)

        response_obj.content = uid_list
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)

        return HttpResponse(json_data, content_type="application/json")


class AccountUserViews(viewsets.ViewSet):

    def __init__(self):
        super(AccountUserViews, self).__init__()
        # post请求参数解密
        self.aes_cipher = AESCipher()
        self.account_user_provider = AccountUserProvider()
        self.account_project_provider = AccountProjectProvider()
        self.account_enterprise_provider = AccountEnterpriseProvider()
        self.keystone_auth = KeystoneAuth()
        self.instance_provider = OpenstackClientProvider()
        self.env_config = EnvConfig()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.GetWebsocketResponsesSerializer},
                         operation_description="获取websocket接口")
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def get_websocket(self, request):
        response_obj = ResponseObj()
        account_id = request.META['HTTP_ACCOUNTID']
        timeout = self.env_config.token_timeout
        data = {'uid': account_id,
                'exp': int(time.time() + timeout)}
        token = auth_utils.encode_token(data, self.env_config.websocket_secret_key)
        ws_data = {"query_token": token.decode(encoding='utf-8')}

        return response_obj.json_serial(ws_data)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.TokenVerifyResponsesSerializer},
                         operation_description="用户登录状态验证接口")
    @auth_utils.param_info_decrypt
    @auth_utils.token_verify
    def token_verify(self, request):
        """
        # token 认证
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.RegisterSerializer,
                         responses={200: response_serializers.GetWebsocketResponsesSerializer},
                         operation_description="用户注册接口")
    @auth_utils.param_info_decrypt
    def register(self, request):
        """
        账号注册
        """
        try:
            param_info = request.param_info

            # openstack 用户创建
            name = param_info.get("account")
            password = param_info.get("password")
            email = param_info.get("account")
            default_project = param_info.get("default_project")
            description = param_info.get("description")
            self.keystone_auth.get_openstack_client_by_request(request)
            open_user_obj = self.keystone_auth.create_user(
                name=name, password=password, email=email, default_project=default_project, description=description)
            if not open_user_obj.is_ok:
                raise Exception(open_user_obj.message)

            account_id = open_user_obj.content.id
            # 注册用户
            param_info["id"] = account_id
            response_obj = self.account_user_provider.register_provider(param_info=param_info)
            if not response_obj.is_ok:
                raise Exception(response_obj.message)
            # 项目成员绑定
            if default_project:
                role_limit = response_obj.content.role.role_limit
                # 若为管理员，则为admin项目添加admin成员角色
                if role_limit >= 20:
                    open_role_response_obj = self.keystone_auth.update_role_assignment(add_user_list=[account_id],
                                                                                       remove_user_list=[],
                                                                                       project=self.env_config.openstack_admin_project_id,
                                                                                       role=auth_models.OPEN_ROLE_ADMIN)
                    if not open_role_response_obj.is_ok:
                        raise Exception("open_admin_project_user_manage", open_role_response_obj.message)

                # 更新 项目 角色成员信息
                role_response_obj = self.account_project_provider.manage_account_to_project_provider(
                    project_id=default_project, add_account_id_list=[account_id], remove_account_id_list=[])
                if not role_response_obj.is_ok:
                    raise Exception("project_user_manage", role_response_obj.message)

                # 用户授权
                base_role_user_list_obj = BaseRoleUserListView()
                role_user_list_obj = RoleUserListView()
                request.POST._mutable = True
                request.data.update({'email': email})
                if role_limit >= 20:
                    request.data.update({'level': 1})
                    base_role_user_list_obj.post(request)
                    request.data.update({'role_name': 'level_manager'})
                    role_user_list_obj.post(request)
                elif role_limit >= 10:
                    request.data.update({'level': 2})
                    base_role_user_list_obj.post(request)
                    request.data.update({'role_name': 'level_authorizener'})
                    role_user_list_obj.post(request)
                else:
                    request.data.update({'level': 3})
                    base_role_user_list_obj.post(request)

        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "账号注册失败", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.UpateUserInfoSerializer,
                         responses={200: response_serializers.UserInfoUpdateResponsesSerializer},
                         operation_description="用户更新接口")
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def user_info_update(self, request):
        """
        用户更新接口
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            # expire_page(path="query_account_info_by_keywords")
            param_dict = request.param_info
            account_id = param_dict.pop("id")
            default_project_id = param_dict.get("default_project")

            # 用户信息判断
            user_obj = auth_models.BmUserInfo.objects.filter(id=account_id).exclude(status="deleted").first()
            if not user_obj:
                return response_obj.json_exception_serial(
                    user_info="该用户不存在！",
                    admin_info="faild to find user info by id %s!" % account_id,
                    no=401
                )

            # openstack 用户信息更新
            self.keystone_auth.get_openstack_client_by_request(request)
            open_user_obj = self.keystone_auth.update_user(name_or_id=account_id, param_info=param_dict)
            if not open_user_obj.is_ok:
                json_data = jsonpickle.dumps(open_user_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            # 更新用户信息
            filter_param_info = {"id": account_id}
            response_obj = self.account_user_provider.update_account_info_provider(filter_param_info=filter_param_info,
                                                                                   param_info=param_dict)
            if not response_obj.is_ok:
                raise Exception(response_obj.message)

            # if param_dict.get("status") and param_dict.get("status") == auth_models.USER_FORBIDDEN:
            # self.account_user_provider.user_token_delete(account_id_list=[account_id])

            if default_project_id and user_obj.default_project_id != default_project_id:
                project_list_obj = self.account_project_provider.query_project_list_by_account(account_id=account_id)
                if not project_list_obj.is_ok:
                    return project_list_obj
                project_dict_list = project_list_obj.content
                project_list = []
                for project in project_dict_list:
                    project_list.append(project.get("id"))
                if default_project_id not in project_list:
                    role_limit = user_obj.role.role_limit
                    # if role_limit >= 20:
                    #     role = "admin"
                    # else:
                    #     role = "_member_"
                    role = "_member_"
                    open_role_response_obj = self.keystone_auth.update_role_assignment(
                        add_user_list=[account_id], remove_user_list=[], project=default_project_id, role=role)
                    if not open_role_response_obj.is_ok:
                        raise Exception("open_project_user_manage", open_role_response_obj.message)

                    # 更新 项目 角色成员信息
                    role_response_obj = self.account_project_provider.update_mapping_project_provider(
                        add_account_id_list=[account_id], remove_account_id_list=[], project_id=default_project_id)
                    if not role_response_obj.is_ok:
                        raise Exception("project_user_manage", role_response_obj.message)

            # 如果用户被禁用， 用户 修改密码、 用户修改邮箱，则清空token
            if (param_dict.get("account") and user_obj.account != param_dict.get("account")) or param_dict.get(
                    "password") or param_dict.get(
                "status") == auth_models.USER_FORBIDDEN:
                user_token_obj = auth_models.BmUsertoken.objects.filter(account_id=user_obj.id).first()
                if user_token_obj:
                    user_token_obj.token = ""
                    user_token_obj.save()

        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "账号更新失败", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="同意用户协议",
                         responses={200: response_serializers.UserAgreementUpdateResponsesSerializer},
                         request_body=serializers.UserAgreementUpdateSerializer)
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def user_agreement_update(self, request):
        """
            用户协议同意
        """
        response_obj = ResponseObj()
        try:
            account_id = request.param_info.get('account_id')
            user_agreement = request.param_info.get('user_agreeement')
            user_agreement_at = datetime.datetime.now()

            # 用户信息更新
            filter_param_info = {"id": account_id, "status": "active"}
            param_info = {"user_agreement": user_agreement, "user_agreement_at": user_agreement_at}
            response_obj = self.account_user_provider.update_account_info_provider(
                filter_param_info=filter_param_info,
                param_info=param_info)

        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {
                "user_info": "用户协议更新失败!",
                "admin_info": "请求参数：%s， Error: %s " % (request.param_info, str(ex))
            }

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.DeleteUserResponsesSerializer},
                         operation_description="删除用户接口",
                         request_body=serializers.DeleteUserInfoSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def user_delete(self, request):
        """
            用户信息删除
        """
        response_obj = ResponseObj()
        response_result = {}
        try:
            with transaction.atomic():
                param_info = request.param_info
                account_id_list = param_info.pop("id_list")

                # openstack 用户删除
                self.keystone_auth.get_openstack_client_by_request(request)
                for account_id in account_id_list:
                    open_user_obj = self.keystone_auth.delete_user(account_id=account_id)
                    if not open_user_obj.is_ok:
                        raise Exception(open_user_obj.message)
                    # 删除结果
                    response_result[account_id] = open_user_obj.content
                response_obj.content = response_result
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "账号删除失败！",
                                    "admin_info": {"Error": str(ex), "result": response_result}}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 账号登录
    @swagger_auto_schema(request_body=serializers.LoginSerializer,
                         responses={200: response_serializers.LoginResponsesSerializer},
                         operation_description="用户登录接口")
    @auth_utils.param_info_decrypt
    def login(self, request):
        """
            账号登录
        """
        try:
            # 清除缓存
            request.session.flush()

            email = request.param_info.get("account", request.param_info.get('email'))
            password = request.param_info.get('password')

            # 用户登录
            response_obj = self.account_user_provider.login_provider(email=email, password=password)
            if not response_obj.is_ok:
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                self.logger.error("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            user_info = response_obj.content.get("user_info")
            account_id = user_info.get("id")
            role_limit = user_info.get('role_limit')
            project_name = user_info.get('default_project_name')
            project_id = user_info.get('default_project_id')

            # openstack 登录,生成 session
            auth_obj = self.keystone_auth.get_session(username=email, password=password, project_name=project_name)
            if auth_obj.is_ok:
                request.session['token'] = auth_obj.content.auth_token
                request.session["username"] = email
                request.session['password'] = password
                request.session['project_name'] = project_name
                request.session['project_domain_name'] = "default"
                request.session['user_domain_name'] = "default"
                request.session["account_id"] = account_id
                request.session['project_id'] = project_id
                request.session['role_limit'] = role_limit

                try:
                    asset_set_obj = AccessSet()
                    request.session['role_type'] = asset_set_obj.get_role_type(request.session["account_id"])
                    response_obj.content['role_type'] = request.session['role_type']
                    print(request.session['role_type'])
                except Exception as ex:
                    print(str(ex))

                request.session.set_expiry(self.env_config.session_timeout)
                send_cloud_log_notification(project_id=project_id, user_id=account_id, service_type=audit_types.IAM,
                                            resource_id=account_id, resource_name=email, resource_type=audit_types.USER,
                                            trace_name=audit_types.LOGIN, code=200, event_type=audit_types.GLOBAL)
            else:
                response_obj = auth_obj
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "服务异常!", "admin_info": "%s " % str(ex)}
        print(type(response_obj.content))
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        print(json_data)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 项目切换
    @swagger_auto_schema(request_body=serializers.ProjectSwitchSerializer,
                         operation_description="用于在控制台的导航条处切换项目",
                         responses={200: response_serializers.ProjectSwitchResponsesSerializer}, )
    @check_element_permission
    @auth_utils.param_info_decrypt
    def project_switch(self, request):
        try:

            # email = request.param_info.get("account", request.param_info.get('email'))
            # password = request.param_info.get('password')
            email = request.session["username"]
            password = request.session['password']
            project_id = request.param_info.get('project_id')
            project_name = request.param_info.get('project_name')

            # 查询用户信息
            response_obj = self.account_user_provider.project_switch_provider(email=email, password=password)
            if not response_obj.is_ok:
                self.logger.error("Result : %s " % response_obj.message)
                raise Exception(response_obj.message)

            account_id = response_obj.content.get("id")
            role_limit = response_obj.content.get('role_limit')

            # 查询项目信息
            project_obj = auth_models.BmProject.objects.exclude(status="deleted").filter(
                id=project_id, project_name=project_name)
            if not project_obj:
                raise Exception("项目id或者项目名称不存在！")

            # openstack 登录,生成 session
            auth_obj = self.keystone_auth.get_session(username=email, password=password, project_name=project_name)
            if auth_obj.is_ok:
                # 清除缓存
                request.session.flush()
                request.session['token'] = auth_obj.content.auth_token
                request.session["username"] = email
                request.session['password'] = password
                request.session['project_name'] = project_name
                request.session['project_domain_name'] = "default"
                request.session['user_domain_name'] = "default"
                request.session["account_id"] = account_id
                request.session['project_id'] = project_id
                request.session['role_limit'] = role_limit
                request.session.set_expiry(self.env_config.session_timeout)
            else:
                response_obj = auth_obj
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "服务异常!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 账号注销
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.LogoutSerializer,
                         responses={200: response_serializers.LogoutResponsesSerializer},
                         operation_description="用户登出接口")
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def logout(self, request):
        """
            账号登出
        """
        response_obj = ResponseObj()
        project_id= request.session.get("project_id")
        account_id = request.session.get("account_id")
        email = request.session.get("username")
        try:
            account = request.param_info.get('account')

            # 清除缓存
            request.session.flush()

            # 账号token 置空
            # user_token_obj = auth_models.BmUsertoken.objects.get(account=account)
            auth_models.BmUsertoken.objects.filter(account=account).update(token="")
            # user_token_obj.token = ""
            # user_token_obj.save()

            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = " %s logout successed!" % account
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "账号登出失败", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        send_cloud_log_notification(project_id=project_id, user_id=account_id, service_type=audit_types.IAM,
                                    resource_id=account_id, resource_name=email, resource_type=audit_types.USER,
                                    trace_name=audit_types.LOGOUT, code=200, event_type=audit_types.GLOBAL)
        return HttpResponse(json_data, content_type="application/json")

    # 发起重置密码
    @swagger_auto_schema(request_body=serializers.UpdatePasswordSerializer,
                         responses={200: response_serializers.UpdatePasswdResponsesSerializer},
                         operation_description="创建密码修改所需 code， 发送邮件"
                         )
    @auth_utils.param_info_decrypt
    def update_password(self, request):
        """
            创建密码修改所需 code， 发送邮件
        """
        try:
            # 获取参数
            email = request.param_info.get("email")

            # 发送修改密码请求
            response_obj = self.account_user_provider.upadte_password_provider(email=email)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "密码重置请求失败", "admin_info": str(ex)}
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 通过邮件链接进行重置密码
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.UpdatePasswdByUserResponsesSerializer},
                         operation_description="进行验证，并修改密码",
                         request_body=serializers.UpdatePasswordByUserSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def update_password_by_user(self, request):
        """
            进行验证，并修改密码
        """
        try:
            with transaction.atomic():
                account_id = request.param_info.get("account_id")
                password = request.param_info.get('password')
                new_password = request.param_info.get('new_password')

                # 更改密码
                response_obj = self.account_user_provider.update_password_by_user_provider(
                    account_id=account_id, password=password, new_password=new_password)
                if not response_obj.is_ok:
                    json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                    self.logger.info("Result : %s " % json_data)
                    return HttpResponse(json_data, content_type="application/json")

                # openstack 用户信息更新
                admin_client = self.instance_provider.get_admin_openstack_client()
                open_user_obj = admin_client.update_user(name_or_id=account_id, **{"password": new_password})
                if not open_user_obj:
                    raise Exception(open_user_obj)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "密码更新失败", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 通过邮件链接进行重置密码
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="用户忘记密码进行验证，并修改密码接口(依赖于接口/account/update_password)",
                         responses={200: response_serializers.ConfirmUpdatePasswordResponsesSerializer},
                         request_body=serializers.ConfirmUpdatePasswordSerializer)
    # @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def confirm_update_password(self, request):
        """
            进行验证，并修改密码
        """
        try:
            with transaction.atomic():
                email = request.param_info.get("email")
                code = request.param_info.get('code')
                new_password = request.param_info.get('new_password')

                # 更改密码
                response_obj = self.account_user_provider.confirm_update_password_provider(email=email, code=code,
                                                                                           new_password=new_password)
                # openstack 用户信息更新
                admin_client = self.instance_provider.get_admin_openstack_client()
                open_user_obj = admin_client.update_user(name_or_id=email, **{"password": new_password})
                if not open_user_obj:
                    raise Exception(open_user_obj)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "密码更新失败", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有标准合同下授权人用户信息",
                         responses={200: response_serializers.AllAuthorizerAccountInfoResponsesSerializer})
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def view_query_all_authorizer_account(self, request):
        """
        授权人列表查询
        """
        try:
            # 查询授权人
            response_obj = self.account_user_provider.query_all_authorizer_account()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有框架合同下授权人用户信息",
                         query_serializer=serializers.FrameDateInfoRecordSerializer,
                         responses={200: response_serializers.AllAuthorizerAccountInfoResponsesSerializer},
                         )
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def view_query_all_frame_authorizer_account(self, request):
        """
        框架合同授权人列表查询
        """
        try:
            # 查询授权人
            contract_start_date = request.param_info.get("contract_start_date")
            response_obj = self.account_user_provider.query_all_frame_authorizer_account(
                contract_start_date=contract_start_date)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 查询账户信息
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="根据关键字查询账户信息",
                         responses={200: response_serializers.AccountInfoByKeywordsResponsesSerializer},
                         query_serializer=serializers.QueryInfoByKeywordsSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def view_query_account_info_by_keywords(self, request):
        """
        账号查询
        """
        try:
            # 查询关键字
            keywords = request.param_info.get('keywords', "")

            # 查询用户
            response_obj = self.account_user_provider.query_account_info_by_keywords(keywords=keywords)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 查询账户信息
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="账号查询",
                         responses={200: response_serializers.AccountInfoByAccountResponsesSerializer},
                         request_body=serializers.QueryUserInfoInCondition)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_account_info_in_condition(self, request):
        """
        账号查询
        """
        try:
            # 查询关键字
            param_dict = request.param_info

            # 查询用户
            response_obj = self.account_user_provider.query_account_info_in_condition(param_dict=param_dict)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 查询个人账户信息
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="查询个人账户信息",
                         responses={200: response_serializers.AccountInfoByAccountResponsesSerializer},
                         query_serializer=serializers.QueryAccountByAccountSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_account_info_by_account(self, request):
        """
        账号查询
        """
        try:
            # 查询关键字
            account_id = request.param_info.get("account_id")

            # 查询用户
            response_obj = self.account_user_provider.query_account_info_by_account(account_id=account_id)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    # 查询账户信息
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="查询所有用户信息",
                         responses={200: response_serializers.AllAccountInfoResponsesSerializer},
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_all_account_info(self, request):
        """
        账号查询
        """
        try:
            # 查询用户
            response_obj = self.account_user_provider.query_all_account_info()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取手机发送的验证码",
                         responses={200: response_serializers.PhoneCodeGetResponsesSerializer},
                         query_serializer=serializers.PhoneCodeGetSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def phone_code_get(self, request):
        """
            发送 手机验证码 code
        """
        try:
            # 查询关键字
            phone_number = request.param_info.get('phone_number')

            response_obj = self.account_user_provider.phone_code_get(phone_number=phone_number)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="验证手机发送的验证码与用户输入的验证码是否一致",
                         responses={200: response_serializers.PhoneCodeVerifyResponsesSerializer},
                         request_body=serializers.PhoneCodeVerifySerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def phone_code_verify(self, request):
        """
            code 验证
        """
        try:
            phone_number = request.param_info.get('phone_number', "")
            code = request.param_info.get("code")

            # code 验证
            param_dict = {"phone_number": phone_number, "code": code}
            response_obj = self.account_user_provider.code_verify(param_dict=param_dict)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {
                "user_info": "验证失败!",
                "admin_info": "param_info %s , Error: %s" % (request.param_info, str(ex))
            }

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="更新用户手机号(依赖于接口/account/phone_code_get)",
                         responses={200: response_serializers.PhoneUpdateResponsesSerializer},
                         request_body=serializers.PhoneUpdateSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def phone_update(self, request):
        """
            新手机号更新
        """
        try:
            account_id = request.param_info.get('account_id')
            phone_number = request.param_info.get('phone_number')
            new_phone_number = request.param_info.get('new_phone_number')
            code = request.param_info.get("code")

            # 验证码校验
            param_dict = {"phone_number": new_phone_number, "code": code}
            code_verify_obj = self.account_user_provider.code_verify(param_dict)
            if not code_verify_obj.is_ok:
                json_data = jsonpickle.dumps(code_verify_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            # 用户信息更新
            filter_param_info = {"id": account_id, "phone_number": phone_number, "status": "active"}
            param_info_of_phone = {"phone_number": new_phone_number}
            response_obj = self.account_user_provider.update_account_info_provider(filter_param_info=filter_param_info,
                                                                                   param_info=param_info_of_phone)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {
                "user_info": "手机号更新失败!",
                "admin_info": "%s " % str(ex)
            }
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取邮箱发送的验证码",
                         responses={200: response_serializers.EmailCodeGetResponsesSerializer},
                         query_serializer=serializers.EmialCodeGetSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def email_code_get(self, request):
        """
            通过邮箱获取验证码
        """
        try:
            email = request.param_info.get('email')
            response_obj = self.account_user_provider.email_code_get(email=email)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "验证码获取失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="验证邮箱发送的验证码与用户输入的验证码是否一致",
                         responses={200: response_serializers.EmailCodeVerifyResponsesSerializer},
                         request_body=serializers.EmialCodeVerifySerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def email_code_verify(self, request):
        """
            code 验证
        """
        try:
            email = request.param_info.get('email')
            code = request.param_info.get("code")

            # code 验证
            param_dict = {"email": email, "code": code}
            response_obj = self.account_user_provider.code_verify(param_dict)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {
                "user_info": "验证失败!",
                "admin_info": str(ex)
            }

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="更新用户邮箱(依赖于接口/account/email_code_get)",
                         responses={200: response_serializers.EmailUpdateResponsesSerializer},
                         request_body=serializers.EmailUpdateSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def email_update(self, request):
        """
            新邮箱更新
        """
        response_obj = ResponseObj()
        try:
            account_id = request.param_info.get('account_id')
            # email = request.param_info.get('email')
            new_email = request.param_info.get('new_email')
            code = request.param_info.get("code")

            # 邮箱查询
            user_obj = self.account_user_provider.account_email_if_exist(param_dict={"account": new_email})
            if user_obj.is_ok:
                response_obj.is_ok = False
                response_obj.message = {
                    "user_info": "邮箱修改失败，新邮箱%s已存在" % new_email,
                    "admin_info": user_obj.content
                }
                response_obj.no = 400
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            # 验证码校验
            param_dict = {"email": new_email, "code": code}
            code_verify_obj = self.account_user_provider.code_verify(param_dict=param_dict)
            if not code_verify_obj.is_ok:
                json_data = jsonpickle.dumps(code_verify_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            with transaction.atomic():
                # 用户信息更新
                filter_param_info = {"id": account_id, "status": "active"}
                param_info = {"account": new_email}
                response_obj = self.account_user_provider.update_account_info_provider(
                    filter_param_info=filter_param_info,
                    param_info=param_info)

                # openstack 用户信息更新
                admin_client = self.instance_provider.get_admin_openstack_client()
                admin_client.update_user(name_or_id=account_id, **{"name": new_email, "email": new_email})
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {
                "user_info": "邮箱更新失败!",
                "admin_info": "请求参数：%s， Error: %s " % (request.param_info, str(ex))
            }

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")


class AccountProjectViews(viewsets.ViewSet):

    def __init__(self):
        super(AccountProjectViews, self).__init__()
        # post请求参数解密
        self.aes_cipher = AESCipher()
        self.account_project_provider = AccountProjectProvider()
        self.keystone_auth = KeystoneAuth()
        self.env_config = EnvConfig()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.firewall_provider = handler.FirewallProvider()
        self.env_config = EnvConfig()
        self.request_monitor_client = RequestClientTwo(endpoint=self.env_config.monitoring_service,
                                                       api_key="")
        self.request_cmdb_asset_client = RequestClientTwo(endpoint=self.env_config.cmdb_asset_service,
                                                          api_key="")
        self.request_cmdb_customize_client = RequestClientTwo(endpoint=self.env_config.cmdb_customize_service,
                                                              api_key="")
        self.cmdb_structure_service = RequestClientTwo(endpoint=self.env_config.cmdb_structure_service,
                                                              api_key="")

    def make_params_to_uid(self, project_id, region_name="regionOne"):
        uid = ":".join([region_name, project_id])
        return uid

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="项目创建",
                         responses={200: response_serializers.ProjectCreatedResponsesSerializer},
                         request_body=serializers.CreateProjectSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def project_create(self, request):
        """
            创建项目
        """
        project_create_obj = ResponseObj()
        project_info = {}
        try:
            param_info = request.param_info
            self.logger.info("create project param %s" % param_info)

            # 项目成员列表、项目名称
            account_list = []
            if "account_list" in param_info:
                account_list = param_info.pop("account_list")
            project_name = param_info.get("project_name")

            # 查询项目是否已存在
            obj = auth_models.BmProject.objects.filter(project_name=project_name,
                                                       status__in=auth_models.PROJECT_SHOW_STATUS_LIST).first()
            if obj:
                project_create_obj.no = 409
                project_create_obj.is_ok = False
                project_create_obj.message = {"user_info": "项目{project_name}已存在!".format(project_name=project_name)}
                json_data = jsonpickle.dumps(project_create_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            # 项目创建
            with transaction.atomic():
                self.logger.info("create project param %s " % param_info)
                # 创建项目
                project_create_obj = self.account_project_provider.crate_project_provider(request=request)
                if not project_create_obj.is_ok:
                    self.logger.error("create openstack project result %s " % project_create_obj.message)
                    raise Exception("create_project", project_create_obj.message)
                self.logger.info("create openstack project result %s " % project_create_obj.content)
                project_info["id"] = param_info.get("id")
                project_info["project_id"] = param_info.get("id")

                # 更新项目成员
                if account_list:
                    self.logger.info("account add to project param %s " % param_info)
                    account_to_project_obj = self.account_project_provider.manage_account_to_project_provider(
                        project_id=param_info.get("id"), add_account_id_list=account_list)
                    if not account_to_project_obj.is_ok:
                        self.logger.error("account add to project result %s " % project_create_obj.message)
                        raise Exception("account add to project Error ", account_to_project_obj.message)
                    self.logger.info("account add to project result %s " % account_to_project_obj.content)
                    project_info["project_account_list"] = account_list

                # 网络信息初始化
                self.logger.info("create project vpc")
                vpc_result_obj = self.account_project_provider.add_vpc_to_project_provider(request)
                if not vpc_result_obj.is_ok:
                    self.logger.error("create project vpc result {result}".format(result=vpc_result_obj))
                    raise Exception("create project vpc Error ", vpc_result_obj.message)
                self.logger.info("create project vpc result {result}".format(result=vpc_result_obj))
                project_info["vpc"] = vpc_result_obj.content

                # # 初始化项目角色
                # role_list_obj = RoleListView()
                # try:
                #     project_obj = auth_models.BmProject.objects.get(project_name=project_name)
                # except auth_models.BmProject.DoesNotExist:
                #     print('can not get project info.')
                #     pass
                # request.POST._mutable = True
                # request.data.update({'project_id': project_obj.id})
                # print(request)
                # role_list_obj.post(request)

                project_create_obj.content = project_info

                # 项目创建成功，生成授权uid
                uid = self.make_params_to_uid(project_id=project_info["project_id"])
                url_param_list = ["bare-metal"]
                dict_info = {
                    "uid_list": [uid],
                }
                result = self.request_monitor_client.data(dict_param=dict_info, method="POST",
                                                          url_param_list=url_param_list)
                self.logger.info("The monitor uid Result : %s " % result.success)

                #项目创建成功，同步CMDB
                cmdb_info = {
                    "uuid": project_info["project_id"],
                    "name":project_name,
                }
                cmdb_result = self.cmdb_structure_service.server_tree(dict_param=cmdb_info, method="POST",url_param_list=[""])
                self.logger.info("The Project create cmdb sys Result : %s " % cmdb_result.success)

        except Exception as ex:
            recycle_obj = self.account_project_provider.project_resource_recycle(project_info=project_info)
            project_create_obj.no = 500
            project_create_obj.is_ok = False
            project_create_obj.message = {"user_info": "项目创建失败!",
                                          "admin_info": {"Error": str(ex),
                                                         "recycle_result": jsonpickle.dumps(recycle_obj,
                                                                                            unpicklable=False)}}
        json_data = jsonpickle.dumps(project_create_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="更新项目信息",
                         responses={200: response_serializers.ProjectRoleManageResponsesSerializer},
                         request_body=serializers.UpdateProjectInfoSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def project_update(self, request):
        """
            项目更新
        """
        response_obj = ResponseObj()

        try:
            # 项目更新
            with transaction.atomic():
                param_info = request.param_info

                # 更新openstack 项目信息
                project_id = request.param_info.get("id")
                project_name = request.param_info.get("project_name")
                description = request.param_info.get("description")
                status = request.param_info.get("status")
                self.keystone_auth.get_openstack_client_by_request(request=request)
                response_obj = self.keystone_auth.update_project(
                    project_id=project_id, project_name=project_name, description=description, status=status)
                if not response_obj.is_ok:
                    raise Exception(response_obj.message)

                # 更新项目信息
                response_obj = self.account_project_provider.update_project_provider(param_info=param_info)
                if not response_obj.is_ok:
                    raise Exception(response_obj.message)
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目更新失败!", "admin_info": str(ex)}
            print(ex)
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="项目的删除",
                         responses={200: response_serializers.ProjectDeletedResponsesSerializer},
                         request_body=serializers.DeleteListSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def project_delete(self, request):
        """
            项目删除
        """
        response_obj = ResponseObj()
        try:
            project_delete_result = []
            project_id_list = request.param_info.get("id_list")
            for project_id in project_id_list:
                self.keystone_auth.get_openstack_client_by_request(request=request)
                response_obj = self.keystone_auth.delete_project(project_id=project_id)
                if not response_obj.is_ok:
                    raise Exception(response_obj.message)
                project_delete_result.append(response_obj.content)

                # 项目删除成功，删除授权uid
                uid = self.make_params_to_uid(project_id=project_id)
                url_param_list = ["bare-metal"]
                dict_info = {
                    "uid_list": [uid],
                }
                result = self.request_monitor_client.data(dict_param=dict_info, method="DELETE",
                                                          url_param_list=url_param_list)
                self.logger.info("The monitor uid delete Result : %s " % result.success)

                #项目删除成功，同步CMDB
                url_param_list=[project_id]
                cmdb_result = self.request_cmdb_customize_client.service_tree(dict_param={}, method="DELETE",
                                                          url_param_list=url_param_list,is_add=True)
                self.logger.info("The project delete cmdb sys Result : %s " % cmdb_result.success)
            response_obj.content = project_delete_result
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目删除失败!", "admin_info": str(ex)}
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="根据关键字查询项目信息",
                         responses={200: response_serializers.ProjectKeywordsInfoResponsesSerializer},
                         query_serializer=serializers.QueryInfoByKeywordsSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def project_info_query_by_keywords(self, request):
        """
        项目查询
        """
        try:
            # 查询关键字
            keywords = request.param_info.get('keywords', "")

            # 查询 项目信息
            response_obj = self.account_project_provider.query_project_info_by_keywords(keywords=keywords)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="修改项目成员",
                         responses={200: response_serializers.ProjectRoleManageResponsesSerializer},
                         request_body=serializers.PorjectRoleManagerSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def project_role_manage(self, request):
        try:
            response_obj = ResponseObj()

            # 创建项目
            project_id = request.param_info.get("project_id")
            grant_account_list = request.param_info.get("grant_account_list", [])
            revoke_account_list = request.param_info.get("revoke_account_list", [])
            with transaction.atomic():
                # 更新 项目 角色成员信息
                role_response_obj = self.account_project_provider.update_mapping_project_provider(
                    add_account_id_list=grant_account_list, remove_account_id_list=revoke_account_list,
                    project_id=project_id)
                if not role_response_obj.is_ok:
                    raise Exception("project_user_manage", role_response_obj.message)

                # 更新openstack 项目角色成员信息
                self.keystone_auth.get_openstack_client_by_request(request=request)
                open_role_response_obj = self.keystone_auth.update_role_assignment(
                    add_user_list=grant_account_list, remove_user_list=revoke_account_list, project=project_id
                )
                if not open_role_response_obj.is_ok:
                    raise Exception("open_project_user_manage", open_role_response_obj.message)
            # 同步CMDB数据
            dict_info = {
                "service_tree_id": project_id,
                "add_user_mail_list": grant_account_list,
                "remove_user_mail_list": revoke_account_list
            }
            result = self.request_cmdb_customize_client.service_tree_user_extend(dict_param=dict_info, method="PUT")
            self.logger.info("The project_user sys Result : %s " % result.success)

            # # 修改用户权限
            # role_user_list_obj = RoleUserListView()
            # for x in grant_account_list:
            #     try:
            #         user_info = auth_models.BmUserInfo.objects.get(id=x)
            #     except auth_models.BmUserInfo.DoesNotExist:
            #         print('can not get user info.')
            #         continue
            #     request.POST._mutable = True
            #     request.data.update({'email': user_info.account})
            #     request.data.pop('project_id')
            #     if user_info.role.role_limit >= 20:
            #         request.data.update({'level': 1})
            #     elif user_info.role.role_limit >= 10:
            #         request.data.update({'level': 2})
            #     else:
            #         request.data.update({'level': 4})
            #     print(request)
            #     role_user_list_obj.post(request)
            #
            # for x in revoke_account_list:
            #     try:
            #         user_info = auth_models.BmUserInfo.objects.get(id=x)
            #     except auth_models.BmUserInfo.DoesNotExist:
            #         print('can not get user info.')
            #         continue
            #     request.POST._mutable = True
            #     request.data.update({'email': user_info.account})
            #     print(request)
            #     role_user_list_obj.delete(request)

            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = "项目成员更新成功！"
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目成员更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取项目信息",
                         responses={200: response_serializers.ProjectInfoResponsesSerializer},
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_all_project_info(self, request):
        """
         项目信息查询
        """
        try:
            # 查询 项目信息
            response_obj = self.account_project_provider.query_all_project_info()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_all_project_member_list(self, request):
        """
         项目所有成员信息查询
        """
        try:
            # 查询 项目成员信息
            response_obj = self.account_project_provider.query_all_project_member_list()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="根据项目获取项目成员",
                         responses={200: response_serializers.ProjectMemberListByProjectResponsesSerializer},
                         query_serializer=serializers.PorjectMembersListSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_project_member_list_by_project(self, request):
        """
         项目成员信息查询
        """
        try:
            project_id = request.param_info.get("project_id")
            # 查询 项目成员信息
            response_obj = self.account_project_provider.query_project_member_list_by_project(project_id=project_id)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="查询没有授权人的项目信息",
                         responses={200: response_serializers.ProjectNoAuthorizerResponsesSerializer},
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_project_list_of_no_authorizer(self, request):
        """
         用户默认项目列表信息查询
        """
        try:
            # 查询 项目成员信息
            response_obj = self.account_project_provider.query_project_list_of_no_authorizer()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="用户默认项目列表信息查询",
                         responses={200: response_serializers.ProjectListByAccountResponsesSerializer},
                         query_serializer=serializers.PorjectListOfAccountSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_project_list_by_account(self, request):
        """
         用户默认项目列表信息查询
        """
        try:
            account_id = request.param_info.get("account_id")

            # 查询 项目成员信息
            response_obj = self.account_project_provider.query_project_list_by_account(account_id=account_id)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取项目的配额信息",
                         responses={200: response_serializers.ProjectQuotaResponsesSerializer},
                         query_serializer=serializers.PorjectIdSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_project_quotas(self, request):
        """
         查询项目配额
         :returns {
            "cores": 600,
            "id": "8bbae2a9133e406f9ec6d4a89e20f6ab",
            "instances": 100,
            "key_pairs": 100,
            "metadata_items": 128,
            "ram": 5120000,
            "server_group_members": 10,
            "server_groups": 200
          }
        """
        response_obj = ResponseObj()
        try:
            project_id = request.param_info.get("project_id")

            # 查询 项目配额信息
            openstack_client = self.keystone_auth.get_openstack_client_by_request(request=request)
            self.logger.info("query project quotas ")

            compute_quotas_obj = openstack_client.get_compute_quotas(name_or_id=project_id)
            self.logger.info("query compute quotas results : %s" % compute_quotas_obj)

            network_quotas_obj = openstack_client.get_network_quotas(name_or_id=project_id)
            self.logger.info("query network quotas results : %s" % network_quotas_obj)

            volume_quotas_obj = openstack_client.get_volume_quotas(name_or_id=project_id)
            self.logger.info("query volume quotas results : %s" % volume_quotas_obj)
            response_obj.content = {
                "compute_quotas": compute_quotas_obj,
                "network_quotas": network_quotas_obj,
                "volume_quotas": volume_quotas_obj
            }
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}
            self.logger.error(response_obj.message)

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="更新项目的配额信息",
                         responses={200: response_serializers.ProjectUpdateQuotaResponsesSerializer},
                         request_body=serializers.PorjectQuotasSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def update_project_quotas(self, request):
        """
         更新项目配额
         :returns
        """
        response_obj = ResponseObj()
        try:
            project_id = request.param_info.get("project_id")
            compute_quotas_dict = request.param_info.get("compute_quotas_dict")
            network_quotas_dict = request.param_info.get("network_quotas_dict")
            volume_quotas_dict = request.param_info.get("volume_quotas_dict")

            # 查询 项目配额信息
            openstack_client = self.keystone_auth.get_openstack_client_by_request(request=request)
            self.logger.info("update project quotas")

            update_result = {}
            if compute_quotas_dict:
                self.logger.info("update compute quotas by param : %s" % compute_quotas_dict)
                compute_quotas_obj = openstack_client.set_compute_quotas(name_or_id=project_id, **compute_quotas_dict)
                update_result["compute_quotas"] = compute_quotas_obj
                self.logger.info("update compute quotas result : %s" % compute_quotas_obj)

            if network_quotas_dict:
                self.logger.info("update network quotas by param : %s" % network_quotas_dict)
                network_quotas_obj = openstack_client.set_network_quotas(name_or_id=project_id, **network_quotas_dict)
                update_result["network_quotas"] = network_quotas_obj
                self.logger.info("update network quotas result : %s" % network_quotas_obj)

            if volume_quotas_dict:
                self.logger.info("update volume quotas by param : %s" % volume_quotas_dict)
                volume_quotas_obj = openstack_client.set_volume_quotas(name_or_id=project_id, **volume_quotas_dict)
                update_result["volume_quotas"] = volume_quotas_obj
                self.logger.info("query volume quotas results : %s" % volume_quotas_obj)

            response_obj.content = update_result
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}
            self.logger.error(response_obj.message)

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")


class AccountEnterpriseViews(viewsets.ViewSet):

    def __init__(self):
        super(AccountEnterpriseViews, self).__init__()
        # post请求参数解密
        self.aes_cipher = AESCipher()
        self.account_enterprise_provider = AccountEnterpriseProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="公司的创建",
                         # responses={200: response_serializers.EnterpriseCreatedResponsesSerializer},
                         request_body=serializers.CreateEnterpriseSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def enterprise_create(self, request):
        """
            创建公司信息
        """
        try:
            param_info = request.param_info

            # 创建公司信息
            response_obj = self.account_enterprise_provider.crate_enterprise_provider(param_info=param_info)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司创建失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="更新公司信息",
                         responses={200: response_serializers.EnterpriseUpdateResponsesSerializer},
                         request_body=serializers.UpdateEnterpriseSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def enterprise_update(self, request):
        """
            公司信息更新
        """
        try:
            param_info = request.param_info

            # 公司信息更新
            response_obj = self.account_enterprise_provider.update_enterprise_provider(param_info=param_info)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="公司的删除",
                         responses={200: response_serializers.EnterpriseDeletedResponsesSerializer},
                         request_body=serializers.DeleteListSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def enterprise_delete(self, request):
        """
            公司删除
        """
        try:
            id_list = request.param_info.get("id_list")

            # 公司删除
            response_obj = self.account_enterprise_provider.enterprise_delete(id_list=id_list)
            if not response_obj.is_ok:
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司删除失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="根据关键词获取公司信息",
                         responses={200: response_serializers.EnterpriseInfoResponsesSerializer},
                         query_serializer=serializers.QueryInfoByKeywordsSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def enterprise_info_query_by_keywords(self, request):
        """
         公司信息查询
        """
        try:
            # 查询关键字
            keywords = request.param_info.get('keywords', "")

            # 查询 公司信息
            response_obj = self.account_enterprise_provider.query_enterprise_info_by_keywords(keywords=keywords)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有的公司信息",
                         responses={200: response_serializers.AllEnterpriseResponsesSerializer},
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_all_enterprise_info(self, request):
        """
         项目信息查询
        """
        try:
            # 查询 项目信息
            response_obj = self.account_enterprise_provider.query_all_enterprise_info()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")


class AccountRoleListViews(APIView):
    def put(self, request):
        return AccountRoleViews.role_update(request)

    def post(self, request):
        return AccountRoleViews.role_create(request)

    def delete(self, request):
        return AccountRoleViews.role_delete(request)

    def get(self, request):
        return AccountRoleViews.query_all_role_info(request)


class AccountRoleViews(viewsets.ViewSet):

    def __init__(self):
        super(AccountRoleViews, self).__init__()

        # post请求参数解密
        self.aes_cipher = AESCipher()
        self.account_role_provider = AccountRoleProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.RoleCreatedResponsesSerializer},
                         operation_description="创建角色",
                         request_body=serializers.CreateRoleSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def role_create(self, request):
        """
            创建角色信息
        """
        try:
            param_info = request.param_info

            # 创建角色信息
            response_obj = self.account_role_provider.crate_role_provider(param_info=param_info)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "角色创建失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.RoleUpdateResponsesSerializer},
                         operation_description="更新角色",
                         request_body=serializers.UpdateRoleSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def role_update(self, request):
        """
            角色信息更新
        """
        try:
            param_info = request.param_info

            # 角色信息更新
            response_obj = self.account_role_provider.update_role_provider(param_info=param_info)

        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "角色更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.RoleDeletedResponsesSerializer},
                         operation_description="删除角色",
                         request_body=serializers.DeleteListSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def role_delete(self, request):
        """
            角色删除
        """
        try:
            id_list = request.param_info.get("id_list")

            # 角色删除
            response_obj = self.account_role_provider.role_delete_provider(id_list=id_list)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "角色删除失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         responses={200: response_serializers.AllRoleResponsesSerializer},
                         operation_description="获取所有角色信息")
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_all_role_info(self, request):
        """
         角色信息查询
        """
        try:
            # 查询 角色信息
            response_obj = self.account_role_provider.query_all_role_info()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")


class AccountContractViews(viewsets.ViewSet):

    def __init__(self):
        super(AccountContractViews, self).__init__()

        # post请求参数解密
        self.aes_cipher = AESCipher()
        self.account_contract_provider = AccountContractProvider()
        self.account_project_provider = AccountProjectProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="合同的创建",
                         responses={200: response_serializers.ContractCreatedResponsesSerializer},
                         request_body=serializers.CreateContractSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def contract_create(self, request):
        """
            创建合同信息
        """
        try:
            param_info = request.param_info

            # 创建合同信息
            response_obj = self.account_contract_provider.crate_contract_provider(param_info=param_info)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同创建失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="合同信息的更新",
                         responses={200: response_serializers.ContractUpdateResponsesSerializer},
                         request_body=serializers.UpdateContractSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def contract_update(self, request):
        """
            合同信息更新
        """
        # from account.cache_test import expire_page_cache
        # a = expire_page_cache(view="query_all_contract_info", curreq=request)
        try:
            param_info = request.param_info

            # 合同信息更新
            response_obj = self.account_contract_provider.update_contract_provider(param_info=param_info)

        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="合同的删除",
                         responses={200: response_serializers.ContractDeletedResponsesSerializer},
                         request_body=serializers.DeleteListSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def contract_delete(self, request):
        """
            合同删除
        """
        try:
            id_list = request.param_info.get("id_list")

            # 合同删除
            response_obj = self.account_contract_provider.contract_delete(id_list=id_list)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同删除失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有的合同信息",
                         responses={200: response_serializers.AllInfoResponsesSerializer})
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_all_contract_info(self, request):
        """
         合同信息查询
        """
        try:
            # 查询合同信息
            response_obj = self.account_contract_provider.query_all_contract_info()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有的合同信息",
                         responses={200: response_serializers.AllInfoResponsesSerializer},
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_contract_info_of_authorizer(self, request):
        """
         当前项目 用户下合同信息查询
        """
        response_obj = ResponseObj()
        project_id = request.session.get("project_id")
        # identity_name = request.param_info.get("identity_name")
        try:
            project_member_obj = self.account_project_provider.query_project_authorizer(project_id=project_id)
            if not project_member_obj.is_ok:
                response_obj.is_ok = True
                response_obj.content = {"framework_contract": None, "all_contract": {}}
                response_obj.message = "改项目对应授权人！"
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                self.logger.info("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")

            # 查询合同信息
            identity_name = project_member_obj.content.get("identity_name")
            response_obj = self.account_contract_provider.query_contract_info_by_identity_name(identity_name)
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def query_contract_list_belong_to_authorizer_by_project_id(self, request):
        """
         当前项目对应授权人名下的下合同信息查询
        """
        response_obj = ResponseObj()
        project_id = request.session.get("project_id")
        self.logger.info("project id %s " % project_id)
        try:
            project_member_obj = self.account_project_provider.query_project_authorizer(project_id=project_id)
            if not project_member_obj.is_ok:
                response_obj.content = {"framework_contract": None, "all_contract": []}
                response_obj.message = project_member_obj.message
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                self.logger.error("Result : %s " % json_data)
                return HttpResponse(json_data, content_type="application/json")
            self.logger.info(project_member_obj)

            # 查询合同信息
            account_id = project_member_obj.content.get("id")
            self.logger.info("query contract info by account id %s !" % account_id)
            response_obj = self.account_contract_provider.query_contract_info_by_account_id(account_id=account_id)
        except Exception as ex:
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(operation_description="合同的终止（用于定时任务）",
                         responses={200: response_serializers.ContractTerminateResponsesSerializer})
    @auth_utils.param_info_decrypt
    def contract_terminate(self, request):
        """
            合同信息更新
        """
        try:
            # 合同信息更新
            response_obj = self.account_contract_provider.contract_terminate_provider()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(operation_description="合同的启用（用于定时任务）",
                         responses={200: response_serializers.ContractTerminateResponsesSerializer})
    @auth_utils.param_info_decrypt
    def contract_start(self, request):
        """
            合同信息更新
        """
        try:
            # 合同信息更新
            response_obj = self.account_contract_provider.contract_start_provider()
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(operation_description="还有十天将到期合同列表查询",
                         responses={200: response_serializers.ContractTenDaysTerminateResponsesSerializer},
                         query_serializer=serializers.ContractTerminatePriorDaysSerializer)
    @auth_utils.param_info_decrypt
    def contract_prior_terminate_remind(self, request):
        """
            合同到期前列表查询
        """
        try:
            # 合同到期前天数
            prior_days = request.param_info.get("prior_days", 3)

            # 合同信息查询
            response_obj = self.account_contract_provider.contract_prior_terminate_remind_provider(
                prior_days=prior_days)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同查询失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContractNumberSerializer,
                         operation_description="合同对应资源查询",
                         responses={200: response_serializers.ContractResourceResponsesSerializer})
    @auth_utils.param_info_decrypt
    def contract_resource_query_by_contract_number(self, request):
        """
            合同对应资源查询
        """
        contract_number = request.param_info.get("contract_number")
        try:
            # 合同对应资源查询
            response_obj = self.account_contract_provider.contract_resource_query_provider(
                contract_number=contract_number)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")


class RequestInfoViews(viewsets.ViewSet):
    def __init__(self):
        super(RequestInfoViews, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.request_info_provider = RequestInfoProvider()

    @swagger_auto_schema(request_body=serializers.RequestInfoRecordSerializer,
                         operation_description="用户请求记录(前端没有用到此接口，主要用于后端数据统计)")
    def request_info_record_create(self, request):
        """
        用户请求记录
        :return:
        """
        try:
            request_param = request.data
            # 合同对应资源查询
            response_obj = self.request_info_provider.request_info_record_provider(request_param)
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败!", "admin_info": str(ex)}

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")
