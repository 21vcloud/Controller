from functools import wraps
import hashlib
import time

import jsonpickle
from django.http import HttpResponse
from django.core.cache import cache
import jwt

from BareMetalControllerBackend.settings import EnvConfig
# from account.repository.auth_models import BmUsertoken, BmRequestInfo
from account.repository.auth_models import BmUsertoken
from common.lark_common.model.common_model import ResponseObj
from common.utils import openstack_exceptions, get_openstack_client

# 第一次请求允许访问，code 判断。
visited_keys = {}

# 验证码确认是否使用
visited_phone_code = {}

env_config = EnvConfig()


# 进行信息加密
def info_encryption(info):
    ctime = str(time.time())
    md5_token = hashlib.md5(bytes(info, encoding="utf8"))
    md5_token.update(bytes(ctime, encoding="utf8"))
    return "%s|%s" % (md5_token.hexdigest(), ctime)


# 进行token 验证
# def token_verify(func):
#     def _inner(self, request):
#
#         try:
#             token_info = request.META.get('HTTP_TOKEN', "")
#
#             response_obj = ResponseObj()
#             response_obj.no = 401
#             response_obj.is_ok = False
#
#             # 是否过期
#             token, client_time = token_info.split("|", maxsplit=1)
#             if float(client_time) + env_config.token_timeout < time.time():
#                 response_obj.message = "Fail to verifiy! Error:  token is timeout !"
#                 json_data = jsonpickle.dumps(response_obj, unpicklable=False)
#                 return HttpResponse(json_data, content_type="application/json")
#
#             # 查询数据库
#             user_token_obj = BmUsertoken.objects.filter(token=token_info).first()
#             if not user_token_obj:
#                 response_obj.message = "Fail to verifiy! Error:  token  %s is not exist! " % token_info
#                 json_data = jsonpickle.dumps(response_obj, unpicklable=False)
#                 return HttpResponse(json_data, content_type="application/json")
#         except Exception as ex:
#             response_obj = ResponseObj()
#             response_obj.no = 500
#             response_obj.is_ok = False
#             response_obj.message = "Fail to verifiy! Error: %s " % ex
#             json_data = jsonpickle.dumps(response_obj, unpicklable=False)
#             return HttpResponse(json_data, content_type="application/json")
#         return func(self, request)
#
#     return _inner


# 进行token 验证
def token_verify(func):
    @wraps(func)
    def _inner(self, request, *args, **kwargs):
        try:
            token_info = request.META.get('HTTP_TOKEN', request.META.get('HTTP_AUTHORIZATION', request.GET.get("token", "")))
            if not token_info:
                raise Exception("token info is null!")
            self.logger.info("token_info %s" % str(token_info))

            # 缓存查询
            # if cache.get(token_info):
            #     return cache.get(token_info)

            response_obj = ResponseObj()
            response_obj.no = 401
            response_obj.is_ok = False

            # 是否过期
            token, client_time = token_info.split("|", maxsplit=1)
            token_timeout = env_config.token_timeout
            now = time.time()
            token_time = float(client_time) + token_timeout
            session_token = request.session.get("token")
            self.logger.info("token_time %s" % str(token_time))
            self.logger.info("now %s" % str(now))
            self.logger.info("session_token %s" % str(session_token))
            if float(client_time) + token_timeout < now:
                response_obj.message = "Fail to verifiy! Error: token is timeout ! token_time %s, now %s, session_token %s" % (str(token_time), str(now), str(session_token))
                self.logger.error(response_obj.message)
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                return HttpResponse(json_data, content_type="application/json")

            # 查询数据库
            user_token_obj = BmUsertoken.objects.filter(token=token_info).first()
            if not user_token_obj:
                response_obj.message = "Fail to verifiy! Error:  token  %s is not exist! " % token_info
                self.logger.error(response_obj.message)
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                return HttpResponse(json_data, content_type="application/json")
            request.META["HTTP_ACCOUNTID"] = user_token_obj.account_id

            # 检验token验证。
            get_openstack_client(request).auth_token
            # session_token = request.session.get("token")
            # if not session_token:
            #     response_obj.message = "Fail to verifiy! Error:  session %s is time out  ! " % request.session
            #     json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            #     return HttpResponse(json_data, content_type="application/json")
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 401
            response_obj.is_ok = False
            response_obj.message = "Fail to verifiy! Error: %s " % str(ex)
            self.logger.error(response_obj.message)
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            response = HttpResponse(json_data, content_type="application/json")
            return response
        self.logger.info("token verify success!")
        # 设置缓存
        response = func(self, request, *args, **kwargs)
        # cache.set(token_info, response, 60*5)
        return response
    return _inner

def token_verify_single(func):
    @wraps(func)
    def _inner(self, request, *args, **kwargs):
        try:
            response_obj = ResponseObj()
            token_info = request.META.get('HTTP_TOKEN', request.META.get('HTTP_AUTHORIZATION', request.GET.get("token", "")))
            if not token_info:
                raise Exception("token info is null!")

            if token_info == env_config.monitor_token_ignore:
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                response = HttpResponse(json_data, content_type="application/json")
                return response

            self.logger.info("token_info %s" % str(token_info))
            response_obj.no = 401
            response_obj.is_ok = False

            # 是否过期
            token, client_time = token_info.split("|", maxsplit=1)
            token_timeout = env_config.token_timeout
            now = time.time()
            token_time = float(client_time) + token_timeout
            session_token = request.session.get("token")
            self.logger.info("token_time %s" % str(token_time))
            self.logger.info("now %s" % str(now))
            self.logger.info("session_token %s" % str(session_token))
            if float(client_time) + token_timeout < now:
                response_obj.message = "Fail to verifiy! Error: token is timeout ! token_time %s, now %s, session_token %s" % (str(token_time), str(now), str(session_token))
                self.logger.error(response_obj.message)
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                return HttpResponse(json_data, content_type="application/json")

            # 查询数据库
            user_token_obj = BmUsertoken.objects.filter(token=token_info).first()
            if not user_token_obj:
                response_obj.message = "Fail to verifiy! Error:  token  %s is not exist! " % token_info
                self.logger.error(response_obj.message)
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                return HttpResponse(json_data, content_type="application/json")
            request.META["HTTP_ACCOUNTID"] = user_token_obj.account_id

        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 401
            response_obj.is_ok = False
            response_obj.message = "Fail to verifiy! Error: %s " % str(ex)
            self.logger.error(response_obj.message)
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            response = HttpResponse(json_data, content_type="application/json")
            return response
        self.logger.info("token verify success!")
        # 设置缓存
        response = func(self, request, *args, **kwargs)
        return response
    return _inner


# c参数解密验证
def param_info_decrypt(func):
    def _inner(self, request):
        request_info = "Request info: User {username}, {method} {url}{path}, ".format(
            username=request.session.get("username"), method=request.method,
            url=request._current_scheme_host, path=request.path)
        self.logger.info(request_info)
        self.request_info_logger.info(request_info)

        self.logger.info("Start to decrypt request param info!")
        try:
            if request.method == "POST":
                if request.data.get("aesRequest"):
                    self.request_info_logger.info("encrypt param info : %s" % request.data)
                    request.param_info = self.aes_cipher.decrypt(request.data.get("aesRequest"))
                else:
                    self.request_info_logger.info("encrypt param info : %s" % request.data)
                    request.param_info = request.data
            elif request.method in ("GET", "DELETE"):
                self.request_info_logger.info("encrypt param info : %s" % request.GET)
                request.param_info = request.GET
            else:
                request.param_info = {}
        except Exception as ex:
            response_obj = ResponseObj()
            response_obj.no = 500
            response_obj.is_ok = False
            response_obj.message = "Fail to decrypt! Error: %s !" % str(ex)
            self.logger.error(response_obj.message)
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            return HttpResponse(json_data, content_type="application/json")
        self.request_info_logger.info("decrypt param info : %s" % request.param_info)

        # try:
        #     request_param = {
        #         "request_user": request.session.get("username"),
        #         "request_method": request.method,
        #         "request_url": request._current_scheme_host+request.path,
        #         "request_param": request.param_info,
        #         "reqeust_info": str(request)
        #     }
        #     BmRequestInfo.objects.create(**request_param)
        # except Exception as ex:
        #     self.logger.error("fail ot record request info %s" % str(ex))

        self.logger.info("Success to decrypt request param info !")

        self.logger.info("Start to deal with function: %s !" % func.__name__)
        return func(self, request)

    return _inner


def decode_token(token, secret_key):
    """
    解密websocket token
    :param token:
    :param secret_key:
    :return:
    """
    info = jwt.decode(token, secret_key, algorithms=['HS256'])
    return info


def encode_token(data, secret_key):
    """
    加密websocket token
    :param data:
    :param secret_key:
    :return:
    """
    token = jwt.encode(data, secret_key, algorithm='HS256')
    return token
