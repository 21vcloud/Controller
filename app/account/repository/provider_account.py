# -*- coding:utf-8 -*-
import time
import datetime
from django.db.models import Q
from django.db import transaction
from BareMetalControllerBackend.conf.env import env_config
from account.auth import utils as auth_utils
from account.repository import auth_models
from baremetal_service.repository import service_model
from common.emial_server import send_email as helper_send_email
from common.lark_common import random_object_id
from common.lark_common.model.common_model import ResponseObj
from common.short_message_server.send_short_message import ProviderShortMessageNotification
from common.lark_common.utils import AESCipher
from common.utils import get_admin_client
from baremetal_openstack import handler
from baremetal_openstack.repository.keystone_provider import KeystoneAuth
from baremetal_openstack.repository.nova_provider import OpenstackClientProvider

monitor_alarm_email = "email"
monitor_alarm_message = "sms"


# 用户相关接口
class AccountUserProvider(object):

    def __init__(self):
        self.aes_cipher = AESCipher()
        self.short_message_notification = ProviderShortMessageNotification()
        self.account_project_provider = AccountProjectProvider()

    @staticmethod
    def token_verify_provider(token_info):
        response_obj = ResponseObj()
        try:
            # 是否过期
            token, client_time = token_info.split("|", maxsplit=1)
            if float(client_time) + float(env_config.token_timeout) * 60 < time.time():
                response_obj.no = 401
                response_obj.is_ok = False
                response_obj.message = {"user_info": "token 超期"}
                return response_obj

            # 查询数据库
            user_token_obj = auth_models.BmUsertoken.objects.filter(token=token_info).first()
            if not user_token_obj:
                response_obj.no = 401
                response_obj.is_ok = False
                response_obj.message = {"user_info": "token 不存在"}
                return response_obj

            # 账号信息查询
            account = user_token_obj.account
            user_info = auth_models.BmUserInfo.objects.values("id", "identity_name", "account").get(
                account=account, status=auth_models.USER_ACTIVE)

            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = user_info
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "token 验证失败", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def email_code_verify_provider(email, code):
        response_obj = ResponseObj()
        try:
            #  code 格式验证
            if not code or "|" not in code:
                response_obj.message = {"user_info": "验证码不存在", "admin_info": "code : %s" % code}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            # code 是否超期验证
            code_info, client_time = code.split("|", maxsplit=1)
            if float(client_time) + float(env_config.code_timeout) < time.time():
                response_obj.message = {"user_info": "验证码%s已超期" % code}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            # 是否已被调用
            if auth_utils.visited_keys.get(email) == code:
                response_obj.message = {"user_info": "验证码%s已被使用" % code}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            # 数据库查询，code是否正确
            confirm = auth_models.BmEmailCode.objects.filter(email=email, code=code).first()
            if not confirm:
                response_obj.message = {"user_info": "邮箱 %s 对应验证码 %s 不存在!" % (email, code)}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = "email code verified success!"
            # 标识为已被使用
            auth_utils.visited_keys[email] = code
        except Exception as ex:
            response_obj.message = {"user_info": "邮箱 %s 验证失败" % email, "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def code_verify(param_dict):
        """

        :param param_dict: {"email": "", "phone_number":"", "code":""}
        :return:
        """
        response_obj = ResponseObj()
        try:
            # 数据库查询，code是否正确
            # confirm = auth_models.BmVerifyCode.objects.filter(phone_number=phone_number, code=code).first()
            confirm = auth_models.BmVerifyCode.objects.filter(**param_dict).first()
            if not confirm:
                response_obj.message = {"user_info": "验证码不存在!", "admin_info": "查询信息 %s" % param_dict}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            # 是否已被调用 code == confirm.ctime
            code = param_dict.get("code")
            ctime = confirm.ctime
            if auth_utils.visited_keys.get(code) == ctime:
                response_obj.message = {"user_info": "验证码%s已被使用，请重新申请验证码!" % code}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = "Verified success!"

            # # 标识为已被使用
            auth_utils.visited_keys[code] = confirm.ctime
        except Exception as ex:
            response_obj.message = {
                "user_info": "验证码错误!",
                "admin_info": "参数信息 %s， Error %s" % (param_dict, str(ex))
            }
            response_obj.is_ok = False
            response_obj.no = 505

        return response_obj

    def register_provider(self, param_info):
        response_obj = ResponseObj()
        try:
            account = param_info.get("account")
            # 查询是否已注册
            # obj = auth_models.BmUserInfo.objects.filter(account=account).first()
            param_dict = {"account": account}
            verify_obj = self.account_email_if_exist(param_dict=param_dict)
            if verify_obj.is_ok:
                return verify_obj

            # 查询项目信息
            if param_info.get("default_project"):
                param_info["default_project"] = auth_models.BmProject.objects.get(
                    id=param_info.get("default_project"), status__in=auth_models.PROJECT_SHOW_STATUS_LIST)

            # 公司信息
            if param_info.get("enterprise"):
                param_info["enterprise"] = auth_models.BmEnterprise.objects.get(
                    id=param_info.get("enterprise"), status="active")

            # 角色信息
            if param_info.get("role"):
                param_info["role"] = auth_models.BmRole.objects.get(
                    id=param_info.get("role"), status="active")

            # 更新数据库
            param_info["status"] = "active"
            param_info["password"] = self.aes_cipher.encrypt(param_info["password"])
            user_info_obj = auth_models.BmUserInfo.objects.create(**param_info)

            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = user_info_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "账号注册失败", "admin_info": str(ex)}
        return response_obj

    def login_provider(self, email, password):
        response_obj = ResponseObj()
        try:
            # 查询用户是否存在
            encrypt_password = self.aes_cipher.encrypt(password)
            user_info_obj = auth_models.BmUserInfo.objects.filter(
                account=email, password__in=[password, encrypt_password]).exclude(status="deleted")

            user_obj = user_info_obj.values(
                "id", "account", "identity_name", "status", "role__role_limit", "user_agreement").first()
            if not user_obj:
                response_obj.no = 204
                response_obj.is_ok = False
                response_obj.message = {"user_info": "账号不存在或密码不正确。", "admin_info": "Fail to login! Error:"}
                return response_obj

            if user_obj.get("status") == "forbidden":
                response_obj.no = 204
                response_obj.is_ok = False
                response_obj.message = {"user_info": "账号被禁用，请确认。", "admin_info": "Fail to login! Error:"}
                return response_obj

            account_id = user_obj.get("id")

            # 获取关联项目信息
            project_id_list = auth_models.BmMappingUserProject.objects.values_list('project_id', flat=True).filter(
                account_id=account_id).exclude(status="deleted")
            if not project_id_list:
                raise Exception("无关联项目！{message}".format(message=project_id_list))

            # 默认项目信息
            default_project_obj = user_info_obj.values("default_project_id", "default_project__status",
                                                       "default_project__project_name").first()

            # [default_project_obj, dict()][default_project_obj == None]
            # 为下述操作保持统一
            if not default_project_obj:
                default_project_obj = dict()
            user_obj["default_project_name"] = default_project_obj.get("default_project__project_name")
            user_obj["default_project_id"] = default_project_obj.get("default_project_id")

            # 如果默认项目被禁用或不存在，该用户没在默认项目成员中，则赋值一个新的项目信息。
            # if (not default_project_obj) or (
            #         default_project_obj.get("default_project_id") not in project_id_list) or (
            #         default_project_obj.get("default_project__status") != auth_models.PROJECT_AVTIVE):
            if (default_project_obj.get("default_project_id") not in project_id_list) or (
                    default_project_obj.get("default_project__status") != auth_models.PROJECT_AVTIVE):
                project_obj = auth_models.BmProject.objects.filter(id__in=project_id_list,
                                                                   status=auth_models.PROJECT_AVTIVE).exclude(
                    id=default_project_obj.get("default_project_id")).first()
                if not project_obj:
                    raise Exception(
                        "Could not find active project in user project mapping list {mapping_id_list}".format(
                            mapping_id_list=project_id_list))
                user_obj["default_project_name"] = project_obj.project_name
                user_obj["default_project_id"] = project_obj.id

            # 角色关联
            user_obj["role_limit"] = user_obj.pop("role__role_limit")

            # 为账号生成token
            token_info = auth_utils.info_encryption(email)
            # token 更新或创建
            auth_models.BmUsertoken.objects.update_or_create(
                account_id=account_id, defaults={"token": token_info, "account": email}
            )

            # token信息
            account_id = user_obj['id']
            timeout = env_config.token_timeout
            data = {'uid': account_id,
                    'exp': int(time.time() + timeout)}
            token = auth_utils.encode_token(data, env_config.websocket_secret_key)
            user_obj['query_token'] = token.decode(encoding='utf-8')
            response_obj.content = {"token": token_info, "user_info": user_obj}
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "登录失败!", "admin_info": "%s " % str(ex)}
        return response_obj

    def project_switch_provider(self, email, password):
        response_obj = ResponseObj()
        try:
            # 查询用户是否存在
            new_password = self.aes_cipher.encrypt(password)
            user_obj = auth_models.BmUserInfo.objects.values(
                "id", "account", "identity_name", "status", "role__role_limit", "default_project_id",
                "default_project__project_name").filter(
                account=email, password__in=[new_password, password]).exclude(status="deleted").first()
            if not user_obj:
                response_obj.no = 204
                response_obj.is_ok = False
                response_obj.message = {"user_info": "账号不存在或密码不正确。", "admin_info": "Fail to login! Error:"}
                return response_obj

            if user_obj.get("status") == "forbidden":
                response_obj.no = 204
                response_obj.is_ok = False
                response_obj.message = {"user_info": "账号被禁用，请确认。", "admin_info": "Fail to login! Error:"}
                return response_obj

            # # 为账号生成token
            # token_info = auth_utils.info_encryption(email)
            # # token 更新或创建
            # auth_models.BmUsertoken.objects.update_or_create(account_id=user_obj.get("id"),
            #                                                  defaults={"token": token_info, "account": email})

            # 关联信息查询
            user_obj["role_limit"] = user_obj.pop("role__role_limit")
            user_obj["default_project_name"] = user_obj.pop("default_project__project_name")
            account_id = user_obj['id']
            timeout = env_config.token_timeout
            data = {'uid': account_id,
                    'exp': int(time.time() + timeout)}
            token = auth_utils.encode_token(data, env_config.websocket_secret_key)
            user_obj['query_token'] = token.decode(encoding='utf-8')
            response_obj.content = user_obj
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "登录失败!", "admin_info": "%s " % str(ex)}
        return response_obj

    def upadte_password_provider(self, email):
        response_obj = ResponseObj()
        try:
            # 邮箱验证是否存在
            # user_info_obj = auth_models.BmUserInfo.objects.filter(account=email).first()
            # if not user_info_obj:
            param_dict = {"account": email}
            verify_obj = self.account_info_verify(param_dict=param_dict)
            if not verify_obj.is_ok:
                return verify_obj

            # 账号邮箱生成code
            code = auth_utils.info_encryption(email)

            # 发送更新密码邮件
            response = self.__send_update_password_email(email, code)
            if not response.is_ok:
                return response

            # 更新code 数据库信息
            auth_models.BmEmailCode.objects.update_or_create(email=email, defaults={"code": code})

            response_obj.content = {"email": email, "code": code}
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "密码重置请求发送失败！", "admin_info": str(ex)}
        return response_obj

    def confirm_update_password_provider(self, email, code, new_password):
        response_obj = ResponseObj()
        try:
            # 验证码校验
            code_response_obj = self.email_code_verify_provider(email=email, code=code)
            if not code_response_obj.is_ok:
                return code_response_obj

            # update new password
            new_password = self.aes_cipher.encrypt(new_password)
            auth_models.BmUserInfo.objects.filter(account=email).update(password=new_password)
            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = "Password reset success!"
        except Exception as ex:
            response_obj.message = {"user_info": "密码更新失败", "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    def update_password_by_user_provider(self, account_id, password, new_password):
        response_obj = ResponseObj()
        try:
            # 用户查询
            password = self.aes_cipher.encrypt(password)
            user_obj = auth_models.BmUserInfo.objects.filter(
                id=account_id, password=password, status=auth_models.USER_ACTIVE).first()
            if not user_obj:
                response_obj.is_ok = False
                response_obj.message = {
                    "user_info": "用户密码不正确",
                    "admin_info": "fail to find user by account_id %s password %s!" % (account_id, password)
                }
                return response_obj

            # 更新密码
            new_password = self.aes_cipher.encrypt(new_password)
            user_obj.password = new_password
            user_obj.save()

            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = "Password reset success!"
        except Exception as ex:
            response_obj.message = {"user_info": "密码更新失败", "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    def phone_code_get(self, phone_number):
        response_obj = ResponseObj()
        try:

            # 生成验证码
            code = random_object_id.gen_verify_code()

            # 发送 手机验证码
            code_send_result = self.short_message_notification.send(phone_number, code)
            if code_send_result.statusCode != 200:
                response_obj.message = {"user_info": "验证码发送失败！", "admin_info": code_send_result}
                response_obj.is_ok = False
                response_obj.no = 300
                return response_obj

            # 更新数据库mapping 表
            auth_models.BmVerifyCode.objects.update_or_create(
                phone_number=phone_number, defaults={"code": code, "ctime": str(time.time())}
            )

            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = {"phone_number": phone_number, "code": code}
        except Exception as ex:
            response_obj.message = {"user_info": "验证码发送失败！", "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    def email_code_get(self, email):
        response_obj = ResponseObj()
        try:
            # 生成验证码
            code = random_object_id.gen_verify_code()

            # 发送邮件
            response = self.__send_email_verify_code_email(email, code)
            if not response.is_ok:
                return response

            # 更新code 数据库信息
            auth_models.BmVerifyCode.objects.update_or_create(email=email,
                                                              defaults={"code": code, "ctime": str(time.time())})

            response_obj.content = {"email": email, "code": code}
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "邮箱获取验证码失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def account_info_verify(param_dict):
        response_obj = ResponseObj()
        try:
            # 查询用户是否存在
            param_dict["status__in"] = auth_models.USER_SHOW_STATUS_LIST
            user_info = auth_models.BmUserInfo.objects.get(**param_dict)
            if user_info.status == auth_models.USER_FORBIDDEN:
                response_obj.no = 204
                response_obj.is_ok = False
                response_obj.message = {"user_info": "账号已被禁用，请确认。", "admin_info": param_dict}
                return response_obj

            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = user_info
        except Exception as ex:
            response_obj.message = {"user_info": "账号对信息不匹配！",
                                    "admin_info": "查询条件：%s ，Error: %s" % (param_dict, str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def account_email_if_exist(param_dict):
        response_obj = ResponseObj()
        try:
            # 查询用户是否存在
            # param_dict["status"] = auth_models.USER_ACTIVE
            user_info = auth_models.BmUserInfo.objects.filter(**param_dict).exclude(status="deleted")
            if user_info:
                response_obj.is_ok = True
                response_obj.content = "account %s is exist!" % param_dict
            else:
                response_obj.is_ok = False
            response_obj.no = 200

        except Exception as ex:
            response_obj.message = {"user_info": "账号对信息不匹配！",
                                    "admin_info": "查询条件：%s ，Error: %s" % (param_dict, str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    def query_account_info_by_keywords(self, keywords):
        response_obj = ResponseObj()
        try:
            # 查询用户
            user_info_obj = auth_models.BmUserInfo.objects.filter(
                Q(account__contains=keywords) |
                Q(identity_card__contains=keywords) |
                Q(identity_name__contains=keywords) |
                Q(phone_number__contains=keywords) |
                Q(status__contains=keywords)
            ).exclude(status="deleted").order_by("-create_at")

            user_info_list = self.__user_obj_to_json(user_info_obj)
            response_obj.content = user_info_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询失败!", "admin_info": "%s " % str(ex)}
        return response_obj

    # @staticmethod
    def query_account_info_in_condition(self, param_dict):
        response_obj = ResponseObj()
        try:
            # 查询用户信息
            user_info_obj = auth_models.BmUserInfo.objects.filter(
                **param_dict).exclude(status="deleted").order_by("-create_at")
            user_info_list = self.__user_obj_to_json(user_info_obj)
            response_obj.content = user_info_list
        except Exception as ex:
            response_obj.message = {
                "user_info": "账号查询失败！", "admin_info": "查询条件：%s ，Error: %s" % (param_dict, str(ex))
            }
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_account_info_by_account(account_id):
        response_obj = ResponseObj()
        try:
            # 查询用户信息
            user_info = auth_models.BmUserInfo.objects.get(id=account_id, status__in=auth_models.USER_SHOW_STATUS_LIST)
            user_dict = user_info.__dict__
            user_dict["default_project_name"] = user_info.default_project.project_name
            user_dict["enterprise_name"] = user_info.enterprise.enterprise_name
            user_dict["role_limit"] = user_info.role.role_limit
            user_dict["role_name"] = user_info.role.role_name
            user_dict.pop("_state")
            user_dict.pop("password")

            # 添加项目信息
            project_id_list = auth_models.BmMappingUserProject.objects.values_list("project_id").filter(
                account_id=account_id).exclude(status="deleted")
            project_name_obj = auth_models.BmProject.objects.values_list("project_name", flat=True).filter(
                id__in=project_id_list, status__in=auth_models.PROJECT_SHOW_STATUS_LIST)
            user_dict["project_list"] = list(project_name_obj)
            response_obj.content = user_dict
        except Exception as ex:
            response_obj.message = {
                "user_info": "账号查询失败！",
                "admin_info": "查询条件：%s ，Error: account_id %s" % (account_id, str(ex))
            }
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    # @staticmethod
    def query_all_account_info(self):
        response_obj = ResponseObj()
        try:
            # 查询用户信息
            user_info_obj = auth_models.BmUserInfo.objects.all().exclude(status="deleted").order_by("-create_at")

            user_info_list = self.__user_obj_to_json(user_info_obj)
            response_obj.content = user_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "账号查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    def query_all_authorizer_account(self):
        response_obj = ResponseObj()
        try:
            # 查询用户信息
            user_info_obj = auth_models.BmUserInfo.objects.filter(
                role__role_name="授权人").order_by("-create_at")
            user_info_list = self.__user_obj_to_json(user_info_obj)
            response_obj.content = user_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "账号查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    def query_all_frame_authorizer_account(self, contract_start_date):
        response_obj = ResponseObj()
        try:
            # 查询所有授权人用户信息
            user_info_obj = auth_models.BmUserInfo.objects.filter(
                role__role_name="授权人").order_by("-create_at")
            user_info_list = self.__user_obj_to_json(user_info_obj)
            if not user_info_list:
                response_obj.no = 300
                response_obj.is_ok = False
                response_obj.content = {"user_info": "授权人列表为空！"}
                return response_obj
            # 进行筛选授权人满足只有一个有效的框架合同
            authorizer_info_list = []
            for user_info in user_info_list:
                authorizer_id = user_info["id"]
                contract_start_timeArray = time.strptime(contract_start_date, "%Y-%m-%d")
                contract_start_timeStamp = int(time.mktime(contract_start_timeArray))
                now = datetime.datetime.now()
                zero_today = now - datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                                      microseconds=now.microsecond)
                last_today = zero_today + datetime.timedelta(hours=23, minutes=59, seconds=59)
                date_now_timeStamp = int(time.mktime(last_today.timetuple()))
                if date_now_timeStamp >= contract_start_timeStamp:
                    authorizer_info_obj = auth_models.BmContract.objects.filter(
                        account_id=authorizer_id, contract_type=auth_models.CONTRACT_FRAME,
                        status=auth_models.CONTRACT_AVTIVE). \
                        order_by("-create_at").first()
                    if not authorizer_info_obj:
                        authorizer_info_list.append(user_info)
                else:
                    authorizer_info_list = user_info_list

            response_obj.content = authorizer_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "账号查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    # @staticmethod
    def update_account_info_provider(self, filter_param_info, param_info):
        response_obj = ResponseObj()
        try:
            # user_id = param_info.pop("id")
            # filter_param_info["status"] = auth_models.USER_ACTIVE
            user_obj = auth_models.BmUserInfo.objects.filter(**filter_param_info).exclude(status="deleted")
            if not user_obj:
                response_obj.no = 300
                response_obj.is_ok = False
                response_obj.content = {"user_info": "用户不存在！",
                                        "admin_info": "faild to find user info by %s!" % filter_param_info}
                return response_obj

            # 查询项目信息
            if param_info.get("default_project"):
                param_info["default_project"] = auth_models.BmProject.objects.get(
                    id=param_info.get("default_project"), status__in=auth_models.PROJECT_SHOW_STATUS_LIST)

            # 公司信息
            if param_info.get("enterprise"):
                param_info["enterprise"] = auth_models.BmEnterprise.objects.get(
                    id=param_info.get("enterprise"), status="active")

            # 角色信息
            if param_info.get("role"):
                param_info["role"] = auth_models.BmRole.objects.get(
                    id=param_info.get("role"), status="active")

            # 密码加密
            if param_info.get("password"):
                param_info["password"] = self.aes_cipher.encrypt(param_info["password"])
            # 更新数据库
            user_obj.update(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            param_info.update(filter_param_info)
            response_obj.content = param_info
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "用户数据更新失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def user_delete(account_id_list):
        response_obj = ResponseObj()
        try:
            # 更新数据库
            account_id_list = account_id_list
            user_delete_obj = auth_models.BmUserInfo.objects.filter(id__in=account_id_list)
            reuslt = user_delete_obj.delete()

            # token 数据库更新
            user_token_delete_obj = auth_models.BmUsertoken.objects.filter(account_id__in=account_id_list)
            user_token_delete_obj.delete()

            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = reuslt
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "用户删除失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def user_token_delete(account_id_list):
        response_obj = ResponseObj()
        try:
            # token 数据库更新
            user_token_delete_obj = auth_models.BmUsertoken.objects.filter(account_id__in=account_id_list)
            user_token_delete_obj.delete()

            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = user_token_delete_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "用户Token删除失败！", "admin_info": str(ex)}
        return response_obj

    # 发送邮件验证邮件
    def __send_update_password_email(self, email, code):

        response_obj = ResponseObj()
        try:
            # get email base information
            notify_model = self.__generate_password_reset_post_data()

            # email info
            notify_model.to_address.append(email)

            # reset_info = self.aes_cipher.decrypt({"email": email, "code": code})
            notify_model.parameter = {
                "email": email,
                "url": "%s?email=%s&code=%s" % (env_config.reset_password_url, email, code),
                "expiration_time": 60
            }

            # send email
            provider_send_email = helper_send_email.ProviderEmailNotification(model_notification=notify_model)
            response_obj = provider_send_email.send()
        except Exception as ex:
            response_obj.message = {"user_info": "邮件发送失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj

        return response_obj

    # 邮件发送基本信息
    @staticmethod
    def __generate_password_reset_post_data():
        notify_model = helper_send_email.ModelEmailNotification()
        notify_model.from_address = notify_model.env_config.notification_reset_pwd_from
        notify_model.bcc_address = notify_model.env_config.notification_reset_pwd_bcc
        notify_model.subject = notify_model.env_config.notification_reset_pwd_subject
        notify_model.email_template_uri = notify_model.env_config.notification_reset_pwd_template_uri
        notify_model.image_uri = notify_model.env_config.notification_reset_pwd_image_uri
        return notify_model

    # 发送获取验证码邮件
    def __send_email_verify_code_email(self, email, code):

        response_obj = ResponseObj()
        try:
            # get email base information
            # notify_model = self.__generate_password_reset_post_data()
            notify_model = self.__generate_email_verify_code_data()

            # email info
            notify_model.to_address.append(email)
            # notify_model.to_address.append("wei286069122@163.com")

            # reset_info = self.aes_cipher.decrypt({"email": email, "code": code})
            notify_model.parameter = {
                "email": email,
                "code": code,
                "expiration_time": int(env_config.code_timeout) / 60
            }

            # send email
            provider_send_email = helper_send_email.ProviderEmailNotification(model_notification=notify_model)
            response_obj = provider_send_email.send()
        except Exception as ex:
            response_obj.message = {"user_info": "邮件发送失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj

        return response_obj

    # 邮件验证码 项目邮件信息
    @staticmethod
    def __generate_email_verify_code_data():
        notify_model = helper_send_email.ModelEmailNotification()
        notify_model.from_address = notify_model.env_config.notification_email_verify_code_from
        notify_model.bcc_address = notify_model.env_config.notification_email_verify_code_bcc
        notify_model.subject = notify_model.env_config.notification_email_verify_code_subject
        notify_model.email_template_uri = notify_model.env_config.notification_email_verify_code_template_uri
        notify_model.image_uri = notify_model.env_config.notification_email_verify_code_image_uri
        return notify_model

    @staticmethod
    def __user_obj_to_json(user_info_obj):
        user_info_list = []
        for user_info in user_info_obj:
            user_dict = user_info.__dict__

            # 值为空时，报错
            if hasattr(user_info, "default_project") and user_info.default_project:
                user_dict["default_project_name"] = user_info.default_project.project_name
            else:
                user_dict["default_project_name"] = ""

            if hasattr(user_info, "enterprise") and user_info.enterprise:
                user_dict["enterprise_name"] = user_info.enterprise.enterprise_name
            else:
                user_dict["enterprise_name"] = ""

            if hasattr(user_info, "role") and user_info.role:
                user_dict["role_limit"] = user_info.role.role_limit
                user_dict["role_name"] = user_info.role.role_name
            else:
                user_dict["role_limit"] = ""
                user_dict["role_name"] = ""
            user_dict.pop("_state")
            user_dict.pop("password")
            user_info_list.append(user_dict)
        return user_info_list


# 项目相关
class AccountProjectProvider(object):

    def __init__(self):
        self.openstack_admin_client = OpenstackClientProvider().get_admin_openstack_client()
        self.keystone_auth = KeystoneAuth(openstack_client=self.openstack_admin_client)

    def crate_project_provider(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        project_id = ""
        try:
            with transaction.atomic():
                # 创建openstack 项目信息
                open_project_obj = self.openstack_admin_client.create_project(name=param_info.get("project_name"),
                                                                              description=param_info.get("description"),
                                                                              domain_id="default")
                # 创建项目信息
                project_id = open_project_obj.id
                param_info["id"] = project_id
                param_info["status"] = auth_models.PROJECT_AVTIVE
                project_obj = auth_models.BmProject.objects.create(**param_info)

                response_obj.no = 200
                response_obj.is_ok = True
                response_obj.content = project_obj
        except Exception as ex:
            if project_id:
                open_project_recycle = self.openstack_admin_client.delete_project(name_or_id=param_info.get("id"),
                                                                                  domain_id="default")
                response_obj.message = {"user_info": "项目创建失败", "admin_info": {"Error": str(ex),
                                                                              "open_project_recycle": open_project_recycle}}
            else:
                response_obj.message = {"user_info": "项目创建失败", "admin_info": str(ex)}
            response_obj.no = 505
            response_obj.is_ok = False
        return response_obj

    def manage_account_to_project_provider(self, project_id, add_account_id_list=[], remove_account_id_list=[]):
        response_obj = ResponseObj()
        try:
            with transaction.atomic():
                # 更新 项目角色成员信息
                account_project_provider = AccountProjectProvider()
                role_response_obj = account_project_provider.update_mapping_project_provider(
                    add_account_id_list=add_account_id_list, remove_account_id_list=remove_account_id_list,
                    project_id=project_id)
                if not role_response_obj.is_ok:
                    return role_response_obj

                # 更新 openstack 项目角色成员信息
                open_role_response_obj = self.keystone_auth.update_role_assignment(
                    add_user_list=add_account_id_list, remove_user_list=[], project=project_id
                )
                if not open_role_response_obj.is_ok:
                    return open_role_response_obj
                response_obj.content = add_account_id_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目成员关联失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def add_vpc_to_project_provider(request, ):
        response_obj = ResponseObj()
        firewall_provider = handler.FirewallProvider()

        project_id = request.param_info.get("id")
        regions = env_config.service_region

        vpc_result_list = []
        try:
            for region in regions.values():
                vpc_result_dict = {}
                if region['enabled']:
                    # self.logger.info("create vpc params region %s, project_id %s :" %
                    #                  (region["region"], project_id))
                    result_vpc = handler.create_vpc(request, region['region'], project_id=project_id)
                    # self.logger.info("create vpc result %s :" % result_vpc)
                    # self.logger.info("create vpc params region %s, project_id %s :" %
                    #                  (region["region"], project_id))
                    vpc_result_dict["vpc_info"] = result_vpc
                    firewall_object = firewall_provider.create_firewall(name=None, region=region['region'],
                                                                        project_id=project_id,
                                                                        enabled=True,
                                                                        description="默认防火墙")
                    # self.logger.info("create vpc result %s :" % firewall_object)
                    # self.logger.info("create vpc params firewall id %s:" % firewall_object.id)
                    default_egress_rule = firewall_provider.create_default_egress_rule(firewall_object.id)
                    default_ingress_rule = firewall_provider.create_default_ingress_rule(firewall_object.id)
                    firewall_rules = default_egress_rule + default_ingress_rule
                    vpc_result_dict["firewall_rules"] = firewall_rules
                    # self.logger.info("create vpc results %s:" % firewall_rules)
                    vpc_result_list.append(vpc_result_dict)
            response_obj.content = vpc_result_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "网络资源创建失败！", "admin_info": str(ex)}
        return response_obj

    def project_resource_recycle(self, project_info):
        response_obj = ResponseObj()
        resource_recycyle_result = {}
        try:
            vpc = project_info.get("vpc")
            if vpc:
                # TODO vpc、防火墙删除
                resource_recycyle_result["vpc"] = ""
                pass

            project_account_list = project_info.get("project_account_list")
            project_id = project_info.get("project_id")

            # 删除项目成员
            if project_id and project_account_list:
                self.manage_account_to_project_provider(project_id=project_id, add_account_id_list=[],
                                                        remove_account_id_list=project_account_list)
            # 删除项目信息
            if project_id:
                # 删除openstack 项目信息
                self.openstack_admin_client.delete_project(name_or_id=project_id, domain_id="default")
                # 删除平台项目信息
                auth_models.BmProject.objects.filter(id=project_id).delete()
            response_obj.content = project_info
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.no = 501
            response_obj.message = "Failed to project resource {project_info} recycle.".format(
                project_info=project_info)
        return response_obj

    @staticmethod
    def update_project_provider(param_info):
        response_obj = ResponseObj()
        try:
            project_id = param_info.get("id")

            # 查询项目是否已存在
            bm_project_obj = auth_models.BmProject.objects.filter(id=project_id).exclude(status="deleted")
            if not bm_project_obj:
                response_obj.is_ok = False
                response_obj.message = "项目 %s 不存在" % project_id
                response_obj.no = 300
                return response_obj

            # 查询项目是否已存在
            project_name = param_info.get("project_name")
            if project_name:
                bm_project_name_obj = auth_models.BmProject.objects.filter(
                    project_name=project_name).exclude(Q(status="deleted") | Q(id=project_id))
                if bm_project_name_obj:
                    response_obj.is_ok = False
                    response_obj.message = "项目%s已存在" % project_name
                    response_obj.no = 300
                    return response_obj

            # 更新项目
            update_project_obj = bm_project_obj.update(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = update_project_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目更新失败",
                                    "admin_info": "参数信息 %s ， Error %s" % (param_info, str(ex))}
        return response_obj

    @staticmethod
    def update_mapping_project_provider(add_account_id_list, remove_account_id_list, project_id):
        response_obj = ResponseObj()
        try:
            # 更新用户 与 项目 mapping 关系
            for account_id in add_account_id_list:
                auth_models.BmMappingUserProject.objects.update_or_create(
                    defaults={"account_id": account_id, "project_id": project_id, "status": "active"},
                    account_id=account_id, project_id=project_id
                )
            for account_id in remove_account_id_list:
                auth_models.BmMappingUserProject.objects.update_or_create(
                    defaults={"account_id": account_id, "project_id": project_id, "status": "deleted"},
                    account_id=account_id, project_id=project_id
                )
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = "项目成员关联成功！"
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目成员关联失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def project_members_delete(filter_param_info):
        # filter_param_info = {"project_id__in": project_id_list}
        response_obj = ResponseObj()
        try:
            mapping_user_project_obj = auth_models.BmMappingUserProject.objects.filter(**filter_param_info)
            # rm_obj = mapping_user_project_obj.delete()
            rm_obj = mapping_user_project_obj.update(status="deleted")
            response_obj.content = rm_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目成员删除失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def project_delete(id_list):
        response_obj = ResponseObj()
        try:
            # 更新role信息
            bm_obj = auth_models.BmProject.objects.filter(id__in=id_list)
            # bm_rm_obj = bm_obj.update(status="deleted")
            bm_rm_obj = bm_obj.delete()
            response_obj.content = bm_rm_obj
        except Exception as ex:
            response_obj.message = {"user_info": "项目删除失败", "admin_info": str(ex)}
            if "Cannot delete or update a parent row" in str(ex):
                response_obj.message = {"user_info": "项目被使用，不能被删除。", "admin_info": str(ex)}
            response_obj.no = 505
            response_obj.is_ok = False
        return response_obj

    # @staticmethod
    def query_project_info_by_keywords(self, keywords):
        response_obj = ResponseObj()
        try:
            # 查询项目
            bm_project_info_obj = auth_models.BmProject.objects.filter(
                (Q(id__contains=keywords) |
                 Q(project_name__contains=keywords) |
                 Q(status__contains=keywords) |
                 Q(description__contains=keywords))
            ).exclude(status__in=["deleted", ""]).order_by("-create_at")
            project_info_list = [u.__dict__ for u in bm_project_info_obj]

            # 查询项目关联 账号信息
            response_obj = self.query_project_info_all_by_project_info_list(project_info_list)
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目 %s 查询失败！" % keywords, "admin_info": str(ex)}
        return response_obj

    # @staticmethod
    def query_all_project_info(self):
        response_obj = ResponseObj()
        try:
            # 查询项目
            bm_project_info_obj = auth_models.BmProject.objects.all().exclude(status="deleted").order_by("-create_at")
            project_info_list = [u.__dict__ for u in bm_project_info_obj]

            # 查询项目关联 账号信息
            response_obj = self.query_project_enterprise(project_info_list)
            response_obj.content = project_info_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目信息查询失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_all_project_member_list():
        response_obj = ResponseObj()
        try:
            all_user_obj = auth_models.BmUserInfo.objects.values(
                "id", "account", "identity_name", "role", "role__role_name").all().exclude(status="deleted")
            response_obj.content = list(all_user_obj)
        except Exception as ex:
            response_obj.message = {"user_info": "账号查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_project_member_list_by_project(project_id):
        response_obj = ResponseObj()
        try:
            # 查询项目是否存在
            project_obj = auth_models.BmProject.objects.filter(
                id=project_id, status__in=auth_models.PROJECT_SHOW_STATUS_LIST).first()
            if not project_obj:
                raise Exception("项目%s不存在！" % project_id)

            # 查询用户信息
            user_info = auth_models.BmMappingUserProject.objects.values_list('account_id', flat=True).filter(
                project_id=project_id).exclude(status="deleted")
            user_id_list = list(user_info)

            all_user_obj = auth_models.BmUserInfo.objects.values(
                "id", "account", "identity_name", "role", "role__role_name").all().exclude(status="deleted")
            # all_user_list = list(all_user_obj)
            no_bound_user_obj = all_user_obj.exclude(id__in=user_id_list)
            no_bound_user_list = list(no_bound_user_obj)

            bound_user_obj = all_user_obj.filter(id__in=user_id_list)
            bound_user_list = list(bound_user_obj)

            response_obj.content = {
                "bound_user_list": bound_user_list,
                "no_bound_user_list": no_bound_user_list
            }
        except Exception as ex:
            response_obj.message = {"user_info": "账号查询失败！",
                                    "admin_info": "查询条件：%s ，Error: account_id %s" % (project_id, str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_project_authorizer(project_id):
        response_obj = ResponseObj()
        try:
            project_obj = auth_models.BmProject.objects.filter(
                id=project_id,
                status__in=auth_models.PROJECT_SHOW_STATUS_LIST).first()
            if not project_obj:
                response_obj.message = {"user_info": "该项目不存在！",
                                        "admin_info": "fail to find project id %s " % project_id}
                response_obj.is_ok = False
                response_obj.no = 406
                return response_obj

            if project_obj.status == auth_models.PROJECT_FORBIDDEN:
                response_obj.message = {"user_info": "该项目被禁用！",
                                        "admin_info": "project info %s" % project_obj.__dict__}
                response_obj.is_ok = False
                response_obj.no = 406
                return response_obj

            # 查询用户信息
            user_info = auth_models.BmMappingUserProject.objects.values_list('account_id', flat=True).filter(
                project_id=project_id).exclude(status="deleted")
            user_id_list = list(user_info)

            authorizer = auth_models.BmUserInfo.objects.values(
                "id", "account", "identity_name", "status", "role", "role__role_name").filter(
                id__in=user_id_list, role__role_name="授权人", status__in=auth_models.USER_SHOW_STATUS_LIST
            ).first()
            if not authorizer:
                response_obj.message = {"user_info": "该项目对应授权人不存在！",
                                        "admin_info": "fail to find authorizer by project id %s " % project_id}
                response_obj.is_ok = False
                response_obj.no = 406
                return response_obj

            if authorizer.get("status") == auth_models.USER_FORBIDDEN:
                response_obj.message = {"user_info": "该项目对应授权人被禁用！",
                                        "admin_info": "authorizer {authorizer} is forbidden ".format(
                                            authorizer=authorizer)}
                response_obj.is_ok = False
                response_obj.no = 406
                return response_obj

            response_obj.content = authorizer
        except Exception as ex:
            response_obj.message = {"user_info": "项目授权人查询失败！",
                                    "admin_info": "查询条件：project id %s, Error: %s" % (project_id, str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_project_list_of_no_authorizer():
        """
        查询 项目不包含
        :return:
        """
        response_obj = ResponseObj()
        try:
            # 查询用户默认项目列表
            project_list = auth_models.BmProject.objects.all().exclude(status="deleted")
            no_authorizer_list = []
            for project in project_list:
                user_id_list_obj = auth_models.BmMappingUserProject.objects.values_list('account_id', flat=True).filter(
                    project_id=project.id).exclude(status="deleted")
                user_id_list = list(user_id_list_obj)
                user_info_list = auth_models.BmUserInfo.objects.filter(
                    id__in=user_id_list, role__role_name="授权人").exclude(status="deleted")
                if not user_info_list:
                    no_authorizer_list.append(project)
            # 查询项目成员信息
            response_obj.content = no_authorizer_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目信息查询失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_project_list_by_account(account_id):
        response_obj = ResponseObj()
        try:
            # 查询用户默认项目列表
            project_id_list_obj = auth_models.BmMappingUserProject.objects.values_list('project_id', flat=True).filter(
                account_id=account_id).exclude(status="deleted")
            project_id_list = list(project_id_list_obj)
            project_list_obj = auth_models.BmProject.objects.filter(
                id__in=project_id_list, status=auth_models.PROJECT_AVTIVE)
            project_dict_list = []
            for project_obj in project_list_obj:
                user_id_list_obj = auth_models.BmMappingUserProject.objects.values_list('account_id', flat=True).filter(
                    project_id=project_obj.id).exclude(status="deleted")

                user_id_list = list(user_id_list_obj)
                user_info_list = auth_models.BmUserInfo.objects.values('account', 'id', "role__role_name").filter(
                    id__in=user_id_list).exclude(status="deleted")
                project_obj.is_authorizer = False
                for user_info in user_info_list:
                    if user_info.get("role__role_name") == "授权人":
                        project_obj.is_authorizer = True

                project_obj.member_info = list(user_info_list)
                project_dict_list.append(project_obj.__dict__)
            response_obj.content = project_dict_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "项目信息查询失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_project_info_all_by_project_info_list(project_info_list):
        response_obj = ResponseObj()
        try:
            for project_info in project_info_list:
                mapping_user_info = auth_models.BmMappingUserProject.objects.values("account_id").filter(
                    project_id=project_info.get("id")).exclude(status="deleted")
                user_id_list = [u.get("account_id") for u in mapping_user_info]
                user_info_obj = auth_models.BmUserInfo.objects.filter(
                    id__in=user_id_list
                )
                user_info_list = [u.__dict__ for u in user_info_obj]
                project_info["user_info_list"] = user_info_list
            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = project_info_list
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 505
            response_obj.message = {"user_info": "用户信息查询失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_project_enterprise(project_info_list):
        response_obj = ResponseObj()
        try:
            for project_info in project_info_list:
                mapping_user_info = auth_models.BmMappingUserProject.objects.values("account_id").filter(
                    project_id=project_info.get("id")).exclude(status="deleted")
                user_id_list = [u.get("account_id") for u in mapping_user_info]
                user_info_obj = auth_models.BmUserInfo.objects.filter(
                    id__in=user_id_list, role__role_name="授权人"
                )
                if user_info_obj:
                    project_info["enterprise"] = user_info_obj[0].enterprise.enterprise_name
                    project_info["enterprise_id"] = user_info_obj[0].enterprise_id
                else:
                    project_info["enterprise"] = "-"
                    project_info["enterprise_id"] = "-"
            response_obj.is_ok = True
            response_obj.no = 200
            response_obj.content = project_info_list
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 505
            response_obj.message = {"user_info": "用户信息查询失败！", "admin_info": str(ex)}
        return response_obj


# 公司相关
class AccountEnterpriseProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def crate_enterprise_provider(param_info):
        response_obj = ResponseObj()
        try:
            enterprise_name = param_info.get("enterprise_name")

            # 查询项目是否已存在
            obj = auth_models.BmEnterprise.objects.filter(
                enterprise_name=enterprise_name).exclude(status="deleted").first()
            if obj:
                response_obj.is_ok = False
                response_obj.message = {"project_name": "公司%s已存在" % enterprise_name}
                response_obj.no = 300
                return response_obj

            # 创建项目
            param_info["status"] = "active"
            enterprise_obj = auth_models.BmEnterprise.objects.create(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = enterprise_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司创建失败!", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def update_enterprise_provider(param_info):
        response_obj = ResponseObj()
        try:
            enterprise_id = param_info.get("id")

            # 查询公司是否已存在
            bm_enterprise_obj = auth_models.BmEnterprise.objects.filter(id=enterprise_id).exclude(status="deleted")
            if not bm_enterprise_obj:
                response_obj.is_ok = False
                response_obj.message = {"user_info": "公司id %s 不存在!" % enterprise_id}
                response_obj.no = 300
                return response_obj

            # 更新公司信息
            update_enterprise_obj = bm_enterprise_obj.update(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = update_enterprise_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司更新失败", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def enterprise_delete(id_list):
        response_obj = ResponseObj()
        try:
            # 更新role信息
            bm_obj = auth_models.BmEnterprise.objects.filter(id__in=id_list)
            bm_rm_obj = bm_obj.delete()
            response_obj.content = bm_rm_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司删除失败", "admin_info": str(ex)}
            if "Cannot delete or update a parent row" in str(ex):
                response_obj.message = {"user_info": "公司被绑定，不能被删除。", "admin_info": str(ex)}

        return response_obj

    @staticmethod
    def query_enterprise_info_by_keywords(keywords):
        response_obj = ResponseObj()
        try:
            # 查询公司信息
            bm_enterprise_info_obj = auth_models.BmEnterprise.objects.filter(
                Q(id__contains=keywords) |
                Q(enterprise_name__contains=keywords) |
                Q(abbreviation__contains=keywords) |
                Q(industry1__contains=keywords) |
                Q(industry2__contains=keywords) |
                Q(location__contains=keywords) |
                Q(sales__contains=keywords) |
                Q(system_id__contains=keywords)
            ).exclude(status="deleted").order_by("-create_at")
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = [u.__dict__ for u in bm_enterprise_info_obj]
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "公司信息 %s 查询失败！" % keywords, "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_all_enterprise_info():
        response_obj = ResponseObj()
        try:
            # 查询公司信息
            enterprise_info_obj = auth_models.BmEnterprise.objects.all().exclude(
                status="deleted").order_by("-create_at")
            auth_models.BmUserInfo.objects.filter(role__role_name="授权人")
            # for user in user_info_obj:
            enterprise_info_list = [u.__dict__ for u in enterprise_info_obj]
            response_obj.content = enterprise_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "公司查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj


# 角色相关
class AccountRoleProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def crate_role_provider(param_info):
        response_obj = ResponseObj()
        try:
            role_name = param_info.get("role_name")

            # 角色是否已存在
            obj = auth_models.BmRole.objects.filter(role_name=role_name).exclude(status="deleted").first()
            if obj:
                response_obj.is_ok = False
                response_obj.message = {"role_name": "该角色%s已存在" % role_name}
                response_obj.no = 300
                return response_obj

            # 创建角色
            param_info["status"] = "active"
            role_obj = auth_models.BmRole.objects.create(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = role_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "角色创建失败!", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def update_role_provider(param_info):
        response_obj = ResponseObj()
        try:
            role_id = param_info.get("id")
            role_limit = param_info.get("role_limit")
            role_name = param_info.get("role_name")

            # 查询角色是否存在
            bm_role_obj = auth_models.BmRole.objects.filter(id=role_id).exclude(status="deleted")
            if not bm_role_obj:
                response_obj.is_ok = False
                response_obj.message = {"user_info": "角色id %s 不存在!" % role_id}
                response_obj.no = 300
                return response_obj

            bm_role_limit_obj = auth_models.BmRole.objects.filter(
                Q(role_limit=role_limit) | Q(role_name=role_name)
            ).exclude(status="deleted").exclude(id=role_id)
            if bm_role_limit_obj:
                response_obj.is_ok = False
                response_obj.message = "角色或角色权限重复!"
                response_obj.no = 300
                return response_obj

            # 更新role信息
            update_role_obj = bm_role_obj.update(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = update_role_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "角色更新失败", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def role_delete_provider(id_list):
        response_obj = ResponseObj()
        try:
            # 更新role信息
            bm_role_obj = auth_models.BmRole.objects.filter(id__in=id_list)
            # bm_rm_obj = bm_role_obj.update(status="deleted")
            bm_rm_obj = bm_role_obj.delete()
            response_obj.content = bm_rm_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "角色删除失败", "admin_info": str(ex)}
            if "Cannot delete or update a parent row" in str(ex):
                response_obj.message = {"user_info": "角色被绑定，不能被删除。", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_all_role_info():
        response_obj = ResponseObj()
        try:
            # 查询用户信息
            role_info_obj = auth_models.BmRole.objects.all().exclude(status="deleted").order_by("-create_at")

            role_info_list = [u.__dict__ for u in role_info_obj]
            response_obj.content = role_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "角色查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_role_info_in_condition(param_dict):
        response_obj = ResponseObj()
        try:
            # 查询角色信息
            role_info_obj = auth_models.BmRole.objects.filter(**param_dict).exclude(
                status="deleted").order_by("-create_at")
            role_info_list = [u.__dict__ for u in role_info_obj]
            response_obj.content = role_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "角色查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj


class AccountContractProvider(object):
    def __init__(self):
        pass

    @staticmethod
    def crate_contract_provider(param_info):
        response_obj = ResponseObj()
        try:
            contract_number = param_info.get("contract_number")
            contract_type = param_info.get("contract_type")
            contract_status_param = param_info.get("status")
            contract_start_date = param_info.get("start_date")
            contract_expire_date = param_info.get("expire_date")
            contract_start_timeArray = time.strptime(contract_start_date, "%Y-%m-%d")
            contract_expire_timeArray = time.strptime(contract_expire_date, "%Y-%m-%d")
            contract_start_timeStamp = int(time.mktime(contract_start_timeArray))
            contract_expire_timeStamp = int(time.mktime(contract_expire_timeArray))

            # 合同是否已存在
            obj = auth_models.BmContract.objects.filter(contract_number=contract_number).exclude(status="deleted")
            if obj:
                response_obj.is_ok = False
                response_obj.message = {"contract_number": "该合同%s已存在" % contract_number}
                response_obj.no = 500
                return response_obj

            # 授权人是否存在
            account_id = param_info.get("account")
            user_obj = auth_models.BmUserInfo.objects.filter(id=account_id).exclude(
                status__in=auth_models.USER_EXCLUDE).first()
            if not user_obj:
                response_obj.is_ok = False
                response_obj.message = {"user_info": "授权人不存在!", "admin_info": "account_id %s " % account_id}
                response_obj.no = 500
                return response_obj
            authorizer_name = user_obj.identity_name
            # 如果是框架合同判断当前授权人下是否有处于active/inactive状态的合同
            if contract_status_param != auth_models.CONTRACT_TERMINATED:
                # 针对框架合同需要对时间重叠进行判断
                if contract_type == auth_models.CONTRACT_FRAME:
                    contract_info_obj = auth_models.BmContract.objects.filter(
                        account_id=account_id, contract_type=auth_models.CONTRACT_FRAME). \
                        exclude(status=auth_models.CONTRACT_TERMINATED)
                    for contract_detail_info_obj in contract_info_obj:
                        contract_start_time = int(time.mktime(contract_detail_info_obj.start_date.timetuple()))
                        contract_exrpre_time = int(time.mktime(contract_detail_info_obj.expire_date.timetuple()))
                        contract_number = contract_detail_info_obj.contract_number
                        if max(contract_start_time, contract_start_timeStamp) <= min(contract_exrpre_time,
                                                                                     contract_expire_timeStamp):
                            response_obj.is_ok = False
                            response_obj.message = {
                                "user_info": "合同创建失败，与授权人{authorizer_name}下的合同{contract_number}存在时间重叠的情况"
                                             "，请重新设置时间!".format(authorizer_name=authorizer_name,
                                                                contract_number=contract_number),
                                "admin_info": "合同创建失败"}
                            response_obj.no = 500
                            return response_obj
                        else:
                            # 进行只有框架合同才有的对active状态的判断
                            if contract_status_param == auth_models.CONTRACT_AVTIVE:
                                authorizer_info_obj = auth_models.BmContract.objects.filter(
                                    account_id=account_id, contract_type=auth_models.CONTRACT_FRAME,
                                    status=auth_models.CONTRACT_AVTIVE). \
                                    order_by("-create_at").first()
                                if authorizer_info_obj:
                                    contract_status = authorizer_info_obj.status
                                    contract_number = authorizer_info_obj.contract_number
                                    response_obj.is_ok = False
                                    response_obj.message = {
                                        "user_info": "创建合同失败，授权人{authorizer_name}下已存在一个处于"
                                                     "{contract_status}状态的合同{contract_number}!".format(
                                            authorizer_name=authorizer_name, contract_status=contract_status,
                                            contract_number=contract_number),
                                        "admin_info": "合同创建失败"}
                                    response_obj.no = 500
                                    return response_obj
            # 创建合同 创建默认值
            # param_info["status"] = "active"
            param_info["account"] = user_obj
            contract_obj = auth_models.BmContract.objects.create(**param_info)
            contract_obj.authorizer = contract_obj.account.identity_name
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = contract_obj.__dict__
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同创建失败!", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def update_contract_provider(param_info):
        response_obj = ResponseObj()
        try:
            contract_id = param_info.get("id")
            account_id = param_info.get("account")
            contract_status_param = param_info.get("status")
            contract_start_date = param_info.get("start_date")
            contract_expire_date = param_info.get("expire_date")
            contract_start_timeArray = time.strptime(contract_start_date, "%Y-%m-%d")
            contract_expire_timeArray = time.strptime(contract_expire_date, "%Y-%m-%d")
            contract_start_timeStamp = int(time.mktime(contract_start_timeArray))
            contract_expire_timeStamp = int(time.mktime(contract_expire_timeArray))
            # 查询合同是否存在
            bm_contract_obj = auth_models.BmContract.objects.filter(id=contract_id).exclude(status="deleted")
            if not bm_contract_obj:
                response_obj.is_ok = False
                response_obj.message = {"user_info": "合同id %s 不存在!" % contract_id}
                response_obj.no = 300
                return response_obj
            bm_contract = bm_contract_obj.first()
            contract_type = bm_contract.contract_type
            # 查询合同编号是否存在
            contract_number = param_info.get("contract_number")
            contract_number_obj = auth_models.BmContract.objects.filter(
                contract_number=contract_number).exclude(Q(status="deleted") | Q(id=contract_id))
            if contract_number_obj:
                response_obj.is_ok = False
                response_obj.message = {"user_info": "合同编号%s已存在!" % contract_number}
                response_obj.no = 300
                return response_obj
            # 查询授权人是否存在
            user_obj = auth_models.BmUserInfo.objects.filter(id=account_id).exclude(
                status__in=auth_models.USER_EXCLUDE).first()
            if not user_obj:
                response_obj.is_ok = False
                response_obj.message = {"user_info": "授权人不存在!", "admin_info": "account_id %s " % account_id}
                response_obj.no = 500
                return response_obj
            authorizer_name = user_obj.identity_name
            # 如果是框架合同判断当前授权人下是否有处于active/inactive状态的合同
            if contract_status_param != auth_models.CONTRACT_TERMINATED:
                # 针对框架合同需要对时间重叠进行判断
                if contract_type == auth_models.CONTRACT_FRAME:
                    contract_info_obj = auth_models.BmContract.objects.filter(
                        account_id=account_id, contract_type=auth_models.CONTRACT_FRAME). \
                        exclude(status=auth_models.CONTRACT_TERMINATED).exclude(id=contract_id)
                    for contract_detail_info_obj in contract_info_obj:
                        contract_start_time = int(time.mktime(contract_detail_info_obj.start_date.timetuple()))
                        contract_exrpre_time = int(time.mktime(contract_detail_info_obj.expire_date.timetuple()))
                        contract_number = contract_detail_info_obj.contract_number
                        if max(contract_start_time, contract_start_timeStamp) <= min(contract_exrpre_time,
                                                                                     contract_expire_timeStamp):
                            response_obj.is_ok = False
                            response_obj.message = {
                                "user_info": "合同更新失败，与授权人{authorizer_name}下的合同{contract_number}"
                                             "存在时间重叠的情况"
                                             "，请重新设置时间!".format(authorizer_name=authorizer_name,
                                                                contract_number=contract_number),
                                "admin_info": "合同更新失败"}
                            response_obj.no = 500
                            return response_obj
                        else:
                            # 进行只有框架合同才有的对active状态的判断
                            if contract_status_param == auth_models.CONTRACT_AVTIVE:
                                authorizer_info_obj = auth_models.BmContract.objects.filter(
                                    account_id=account_id, contract_type=auth_models.CONTRACT_FRAME,
                                    status=auth_models.CONTRACT_AVTIVE). \
                                    order_by("-create_at").exclude(id=contract_id).first()
                                if authorizer_info_obj:
                                    contract_status = authorizer_info_obj.status
                                    contract_number = authorizer_info_obj.contract_number
                                    response_obj.is_ok = False
                                    response_obj.message = {
                                        "user_info": "合同更新失败，授权人{authorizer_name}下已存在一个处于"
                                                     "{contract_status}状态的合同{contract_number}!".format(
                                            authorizer_name=authorizer_name, contract_status=contract_status,
                                            contract_number=contract_number),
                                        "admin_info": "合同更新失败"}
                                    response_obj.no = 500
                                    return response_obj
            # 更新contract信息
            update_contract_obj = bm_contract_obj.update(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = update_contract_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def contract_delete(id_list):
        response_obj = ResponseObj()
        try:
            # 删除合同信息
            bm_obj = auth_models.BmContract.objects.filter(id__in=id_list)
            # bm_rm_obj = bm_obj.update(status="deleted")
            bm_rm_obj = bm_obj.delete()
            response_obj.content = bm_rm_obj
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同删除失败", "admin_info": str(ex)}
            if "Cannot delete or update a parent row" in str(ex):
                response_obj.message = {"user_info": "合同被占用，不能被删除。", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def query_all_contract_info():
        response_obj = ResponseObj()
        try:
            # 查询合同信息
            contract_info_obj = auth_models.BmContract.objects.all().exclude(status="deleted").order_by("-create_at")
            for contract_info in contract_info_obj:
                if contract_info.account:
                    contract_info.authorizer = contract_info.account.identity_name
            contract_info_list = [u.__dict__ for u in contract_info_obj]
            response_obj.content = contract_info_list
        except Exception as ex:
            response_obj.message = {"user_info": "合同查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_contract_info_by_identity_name(identity_name):
        response_obj = ResponseObj()
        try:
            # 查询合同信息
            contract_info_obj = auth_models.BmContract.objects.filter(
                authorizer=identity_name, status=auth_models.CONTRACT_AVTIVE).order_by("-create_at")
            framework_contract_obj = contract_info_obj.filter(contract_type=auth_models.CONTRACT_FRAME).first()
            standardwork_contract_list = [u.__dict__ for u in contract_info_obj]
            response_obj.content = {
                "framework_contract": framework_contract_obj,
                "all_contract": standardwork_contract_list
            }
        except Exception as ex:
            response_obj.message = {"user_info": "合同查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def query_contract_info_by_account_id(account_id):
        response_obj = ResponseObj()
        try:
            # 查询合同信息
            contract_info_obj = auth_models.BmContract.objects.filter(
                account=account_id, status=auth_models.CONTRACT_AVTIVE).order_by("-create_at")
            framework_contract_obj = contract_info_obj.filter(contract_type=auth_models.CONTRACT_FRAME).first()
            standardwork_contract_list = [u.__dict__ for u in contract_info_obj]

            response_obj.content = {
                "framework_contract": framework_contract_obj,
                "all_contract": standardwork_contract_list
            }
        except Exception as ex:
            response_obj.message = {"user_info": "合同查询失败！",
                                    "admin_info": "Error: %s" % (str(ex))}
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @staticmethod
    def contract_terminate_provider():
        response_obj = ResponseObj()
        try:
            # 查询合同是否存在
            bm_contract_obj = auth_models.BmContract.objects.filter(
                expire_date__lt=datetime.datetime.today()).exclude(status=auth_models.CONTRACT_TERMINATED)
            bm_contract_info_obj = bm_contract_obj.values("contract_number", "start_date", "expire_date",
                                                          "account_id__account",
                                                          "account_id__identity_name")
            bm_contract_list = [u for u in bm_contract_info_obj]

            # 更新contract信息
            param_info = {"status": "terminated"}
            bm_contract_obj.update(**param_info)

            # 返回信息
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = bm_contract_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def contract_start_provider():
        response_obj = ResponseObj()
        try:
            # 查询合同是否存在
            bm_contract_obj = auth_models.BmContract.objects.filter(
                start_date__lte=datetime.datetime.today(), expire_date__gte=datetime.datetime.today(),
                status=auth_models.CONTRACT_INAVTIVE
            )
            if not bm_contract_obj:
                response_obj.content = []
                return response_obj
            # bm_contract_info_obj = bm_contract_obj.values("contract_number", "start_date", "expire_date",
            #                                               "account_id__account",
            #                                               "account_id__identity_name")
            # bm_contract_list = [u for u in bm_contract_info_obj]
            bm_contract_list = []
            for bm_contract_obj_detail in bm_contract_obj:
                bm_contract_type = bm_contract_obj_detail.contract_type
                bm_contract_number = bm_contract_obj_detail.contract_number
                bm_contract_status = bm_contract_obj_detail.status
                account_id = bm_contract_obj_detail.account_id
                contract_id = bm_contract_obj_detail.id
                contract_start_date = str(bm_contract_obj_detail.start_date)
                contract_expire_date = str(bm_contract_obj_detail.expire_date)
                contract_start_timeArray = time.strptime(contract_start_date, "%Y-%m-%d")
                contract_expire_timeArray = time.strptime(contract_expire_date, "%Y-%m-%d")
                contract_start_timeStamp = int(time.mktime(contract_start_timeArray))
                contract_expire_timeStamp = int(time.mktime(contract_expire_timeArray))
                # 查询授权人是否存在
                user_obj = auth_models.BmUserInfo.objects.filter(id=account_id).exclude(
                    status__in=auth_models.USER_EXCLUDE).first()
                if not user_obj:
                    response_obj.is_ok = False
                    response_obj.message = {"user_info": "授权人不存在!", "admin_info": "account_id %s " % account_id}
                    response_obj.no = 500
                    return response_obj
                authorizer_name = user_obj.identity_name
                # 如果是框架合同判断当前授权人下是否有处于active/inactive状态的合同
                if bm_contract_status != auth_models.CONTRACT_TERMINATED:
                    # 针对框架合同需要对时间重叠进行判断
                    if bm_contract_type == auth_models.CONTRACT_FRAME:
                        contract_info_obj = auth_models.BmContract.objects.filter(
                            account_id=account_id, contract_type=auth_models.CONTRACT_FRAME). \
                            exclude(status=auth_models.CONTRACT_TERMINATED).exclude(id=contract_id)
                        for contract_detail_info_obj in contract_info_obj:
                            contract_start_time = int(time.mktime(contract_detail_info_obj.start_date.timetuple()))
                            contract_exrpre_time = int(time.mktime(contract_detail_info_obj.expire_date.timetuple()))
                            contract_number = contract_detail_info_obj.contract_number
                            if max(contract_start_time, contract_start_timeStamp) <= min(contract_exrpre_time,
                                                                                         contract_expire_timeStamp):
                                message = {
                                    "user_info": "合同{bm_contract_number}启动失败，与授权人{authorizer_name}下的合同{contract_number}"
                                                 "存在时间重叠的情况"
                                                 "，请重新设置时间!".format(bm_contract_number=bm_contract_number,
                                                                    authorizer_name=authorizer_name,
                                                                    contract_number=contract_number),
                                    "is_ok": False
                                }
                                bm_contract_list.append(message)
                                break
                            else:
                                # 进行只有框架合同才有的对inactive状态的判断
                                if bm_contract_status == auth_models.CONTRACT_INAVTIVE:
                                    authorizer_info_obj = auth_models.BmContract.objects.filter(
                                        account_id=account_id, contract_type=auth_models.CONTRACT_FRAME,
                                        status=auth_models.CONTRACT_AVTIVE). \
                                        order_by("-create_at").exclude(id=contract_id).first()
                                    if authorizer_info_obj:
                                        contract_status = authorizer_info_obj.status
                                        contract_number = authorizer_info_obj.contract_number
                                        message = {
                                            "user_info": "合同{bm_contract_number}启动失败，授权人{authorizer_name}下已存在一个处于"
                                                         "{contract_status}状态的合同{contract_number}!".format(
                                                bm_contract_number=bm_contract_number, authorizer_name=authorizer_name,
                                                contract_status=contract_status,
                                                contract_number=contract_number),
                                            "is_ok": False
                                        }
                                        bm_contract_list.append(message)
                                        break
                                    # 更新contract信息
                                    bm_contract_start_obj = auth_models.BmContract.objects.filter(id=contract_id)
                                    param_info = {"status": "active"}
                                    bm_contract_start_obj.update(**param_info)
                                    message = {
                                        "user_info": bm_contract_obj_detail,
                                        "is_ok": True
                                    }
                                    bm_contract_list.append(message)
                                    break
                    else:
                        # 更新contract信息
                        bm_contract_start_obj = auth_models.BmContract.objects.filter(id=contract_id)
                        param_info = {"status": "active"}
                        bm_contract_start_obj.update(**param_info)
                        message = {
                            "user_info": bm_contract_obj_detail,
                            "is_ok": True
                        }
                        bm_contract_list.append(message)

            # 返回信息
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = bm_contract_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同更新失败", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def contract_prior_terminate_remind_provider(prior_days):
        response_obj = ResponseObj()
        try:
            # 查询合同是否存在
            ten_date_later = datetime.date.today() + datetime.timedelta(days=int(prior_days))
            bm_contract_obj = auth_models.BmContract.objects.filter(
                expire_date=ten_date_later, status=auth_models.CONTRACT_AVTIVE)
            bm_contract_info_obj = bm_contract_obj.values("contract_number", "start_date", "expire_date",
                                                          "account_id__account",
                                                          "account_id__identity_name")
            bm_contract_list = [u for u in bm_contract_info_obj]

            # 返回信息
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = bm_contract_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同查询失败！", "admin_info": str(ex)}
        return response_obj

    def contract_resource_query_provider(self, contract_number):
        response_obj = ResponseObj()
        try:
            resource_dict = {}

            # 通过合同号，查询合同、公司信息
            contract_info_obj = auth_models.BmContract.objects.filter(contract_number=contract_number).extra(
                select={'enterprise_name': 'bm_enterprise.enterprise_name'}, tables=['bm_enterprise'],
                where=['bm_contract.customer_id=bm_enterprise.id']).first()
            if not contract_info_obj:
                return response_obj

            contract_info_dict = contract_info_obj.__dict__
            contract_info_dict.pop("_state")
            # resource_dict["contract_info"] = contract_info_dict

            # 服务器信息
            instance_list_obj = self.get_instance_list_info_by_contract_number(contract_number=contract_number)
            resource_dict[service_model.resource_type_ecbm] = instance_list_obj

            # 磁盘信息
            volume_dict_by_project = self.get_volume_list_info_by_contract_number(contract_number=contract_number)
            resource_dict[service_model.resource_type_volume] = volume_dict_by_project

            # 磁盘备份信息
            volume_backup_dict_by_project = self.get_volume_backup_list_info_by_contract_number(
                contract_number=contract_number)
            resource_dict[service_model.resource_type_volume_backup] = volume_backup_dict_by_project

            # 弹性IP信息
            floating_ip_dict_by_project = self.get_floating_ip_list_info_by_contract_number(
                contract_number=contract_number)
            resource_dict[service_model.resource_type_flaoting_ip] = floating_ip_dict_by_project

            # 以项目分类排序
            resource_dict_by_project = {}
            for resource_type, project_resource_list in resource_dict.items():
                for project_name, resource_list in project_resource_list.items():
                    # resource_dict_by_project[project_name][resource_type] = resource_list
                    if resource_dict_by_project.get(project_name):
                        resource_dict_by_project[project_name][resource_type] = resource_list
                    else:
                        resource_dict_by_project[project_name] = {resource_type: resource_list}

            # 返回信息
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = {"contract_info": contract_info_dict, "resource_info": resource_dict_by_project}
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "合同资源查询失败", "admin_info": str(ex)}
        return response_obj

    def get_instance_list_info_by_contract_number(self, contract_number):

        # 合同下所有服务器信息
        bm_instance_obj_list = service_model.BmServiceInstance.objects.filter(
            contract_number=contract_number, deleted=False).extra(
            select={'project_name': 'bm_project.project_name'}, tables=['bm_project'],
            where=['bm_service_instance.project_id=bm_project.id']
        )

        # 查询openstack 平台各个项目下服务器列表
        project_id_list = bm_instance_obj_list.values_list("project_id", flat=True)
        all_open_instance_obj_list_in_project_dict = self.get_instance_list_in_project_list(
            project_id_list=project_id_list)

        # 裸金属平台与openstck平台服务器列表匹配关联
        instance_list_of_project = self.get_instance_info_associated(bm_instance_obj_list,
                                                                     all_open_instance_obj_list_in_project_dict)
        return instance_list_of_project

    @staticmethod
    def get_instance_list_in_project_list(project_id_list):
        """
        openstack 平台在某项目列表下有服务器列表
        :param project_id_list:
        :return:
        """
        # openstack 平台所有服务器列表
        openstack_client = get_admin_client()
        instance_obj_list = openstack_client.compute.servers(details=True, all_projects=True,
                                                             tags=env_config.baremetal_tag)

        # 通过项目进行分类
        instance_obj_list_of_project_dict = {}
        for instance_obj in instance_obj_list:
            instance_project_id = instance_obj.project_id
            if instance_project_id not in project_id_list:
                continue

            if instance_project_id in instance_obj_list_of_project_dict:
                instance_obj_list_of_project_dict[instance_project_id].append(instance_obj)
            else:
                instance_obj_list_of_project_dict[instance_project_id] = [instance_obj]
        return instance_obj_list_of_project_dict

    @staticmethod
    def get_instance_info_associated(instance_list_obj, all_open_instance_obj_list_in_project_dict):
        """
        裸金属平台与openstck平台服务器列表匹配关联
        :param instance_list_obj:
        :param all_open_instance_obj_list_in_project_dict:
        :return:
        """

        # 项目列表
        project_id_list_obj = instance_list_obj.values("project_id", "project_name")

        instance_list_of_project = {}
        for project_dict in project_id_list_obj:
            project_id = project_dict.get("project_id")
            project_name = project_dict.get("project_name")

            # 合同下项目下的 服务器列表
            bm_instances_query = instance_list_obj.filter(
                project_id=project_id).exclude(status="deleted").order_by("-create_at")
            # 云平台下该项目下的服务器列表
            instance_obj_list = all_open_instance_obj_list_in_project_dict.get(project_id)
            flavor_dict = handler.get_flavor_info()
            image_dict = handler.get_image_info()

            # 平台与openstack 服务器信息匹配关联
            servers = []
            if instance_obj_list:
                for instance in instance_obj_list:
                    instance.flavor['flavor_info'] = flavor_dict.get(instance.flavor.get('original_name'))
                    instance.image['name'] = image_dict.get(instance.image.get('id'))
                    bm = handler.reserial_instance(instance, bm_instances_query)
                    if bm:
                        servers.append(bm)
            instance_list_of_project[project_name] = servers
        return instance_list_of_project

    @staticmethod
    def get_volume_list_info_by_contract_number(contract_number):

        # 根据合同查询磁盘信息
        volume_list_obj = service_model.BmServiceVolume.objects.filter(
            contract_number=contract_number, is_measure_end=False).extra(
            select={'project_name': 'bm_project.project_name'}, tables=['bm_project'],
            where=['bm_service_volume.project_id=bm_project.id'])

        # 根据项目进行磁盘信息合并
        volume_dict_by_project = {}
        for volume_obj in volume_list_obj:
            volume_info_dict = volume_obj.__dict__
            volume_info_dict.pop("_state")
            if volume_dict_by_project.get(volume_obj.project_name):
                volume_dict_by_project.get(volume_obj.project_name).append(volume_info_dict)
            else:
                volume_dict_by_project[volume_obj.project_name] = [volume_info_dict]
        return volume_dict_by_project

    @staticmethod
    def get_volume_backup_list_info_by_contract_number(contract_number):

        # 根据合同查询磁盘备份信息
        volume_backup_list_obj = service_model.BmServiceVolumeBackup.objects.filter(
            contract_number=contract_number, is_measure_end=False).extra(
            select={'project_name': 'bm_project.project_name'}, tables=['bm_project'],
            where=['bm_service_volume_backup.project_id=bm_project.id'])

        # 根据项目进行磁盘备份信息合并
        volume_backup_dict_by_project = {}
        for volume_backup_obj in volume_backup_list_obj:
            volume_backup_info_dict = volume_backup_obj.__dict__
            volume_backup_info_dict.pop("_state")
            if volume_backup_dict_by_project.get(volume_backup_obj.project_name):
                volume_backup_dict_by_project.get(volume_backup_obj.project_name).append(volume_backup_info_dict)
            else:
                volume_backup_dict_by_project[volume_backup_obj.project_name] = [volume_backup_info_dict]
        return volume_backup_dict_by_project

    @staticmethod
    def get_floating_ip_list_info_by_contract_number(contract_number):

        # 根据合同查询弹性IP信息
        floating_ip_list_obj = service_model.BmServiceFloatingIp.objects.filter(
            contract_number=contract_number, status=service_model.FLOATINGIP_ACTIVE, is_measure_end=False).extra(
            select={'project_name': 'bm_project.project_name'}, tables=['bm_project'],
            where=['bm_service_floating_ip.project_id=bm_project.id'])

        # 根据项目进行弹性IP信息合并
        floating_ip_dict_by_project = {}
        for floating_ip_obj in floating_ip_list_obj:
            floating_ip_info_dict = floating_ip_obj.__dict__
            floating_ip_info_dict.pop("_state")
            if floating_ip_dict_by_project.get(floating_ip_obj.project_name):
                floating_ip_dict_by_project.get(floating_ip_obj.project_name).append(floating_ip_info_dict)
            else:
                floating_ip_dict_by_project[floating_ip_obj.project_name] = [floating_ip_info_dict]
        return floating_ip_dict_by_project


# 请求信息封装
class RequestInfoProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def request_info_record_provider(request_param):
        response_obj = ResponseObj()
        try:
            # record_obj = auth_models.BmRequestInfo.objects.create(**request_param)

            # 返回信息
            response_obj.no = 200
            response_obj.is_ok = True
            # response_obj.content = record_obj
            response_obj.content = "successful"
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "请求记录添加失败", "admin_info": str(ex)}
        return response_obj
