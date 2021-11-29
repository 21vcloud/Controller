# -*- coding:utf-8 -*-

import hashlib
import time
import datetime
import hmac
import base64
from hashlib import sha1
from random import choice
import string
from urllib.parse import quote as urlencode
from common.lark_common.utils import AESCipher

import jwt
import json
import jsonpickle
from django.http import HttpResponse
from django.db import transaction
from rest_framework import status
import requests as req

from baremetal_openstack.repository.keystone_provider import KeystoneAuth
from BareMetalControllerBackend.settings import EnvConfig
from account.repository.auth_models import BmUsertoken, BmUserInfo
from common.lark_common.model.common_model import ResponseObj
from rest_api.models import AccessKey

# 第一次请求允许访问，code 判断。
visited_keys = {}

# 验证码确认是否使用
visited_phone_code = {}

env_config = EnvConfig()


def info_encryption(info):
    ctime = str(time.time())
    md5_token = hashlib.md5(bytes(info, encoding="utf8"))
    md5_token.update(bytes(ctime, encoding="utf8"))
    return "%s|%s" % (md5_token.hexdigest(), ctime)


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

        self.logger.info("Success to decrypt request param info !")

        self.logger.info("Start to deal with function: %s !" % func.__name__)
        return func(self, request)

    return _inner


# def decode_token(token, access_key):
#     """
#     解密websocket token
#     :param token:
#     :param access_key:
#     :return:
#     """
#     try:
#         secret_key = AccessKey.objects.get(access_key=access_key).secret_key
#     except AccessKey.DoesNotExist:
#         return False, None
#     info = jwt.decode(token, secret_key, algorithms=['HS256'])
#     return True, info


# def decode_token(token, access_key):
#     """
#     解密websocket token
#     :param token:
#     :param access_key:
#     :return:
#     """
#     try:
#         account_obj = AccessKey.objects.get(access_key=access_key).secret_key
#     except AccessKey.DoesNotExist:
#         return False, None
#     info = jwt.decode(token, account_obj.secret_key, algorithms=['HS256'])
#     if type(info) == 'dict':
#         return True, info
#     elif account_obj.second_secret_key:
#         info = jwt.decode(token, account_obj.second_secret_key, algorithms=['HS256'])
#         if type(info) == 'dict':
#             return True, info
#     return False, None


# def encode_token(data, access_key):
#     """
#     加密websocket token
#     :param data:
#     :param access_key:
#     :return:
#     """
#     try:
#         secret_key = AccessKey.objects.get(access_key=access_key).secret_key
#     except AccessKey.DoesNotExist:
#         return False, None
#     token = jwt.encode(data, secret_key, algorithm='HS256')
#     return True, token

def generate_random_secretkey(length=30, chars=string.printable[:62]):
    return ''.join([choice(chars) for i in range(length)])


def get_secret_key(access_key_id):
    """
    获取所有秘钥
    :param access_key_id:
    :return: a list about access_key_info
    """

    aes_cipher = AESCipher()

    encrypt_sk = AccessKey.objects.filter(access_key=access_key_id)
    if not encrypt_sk:
        sk = generate_random_secretkey()
        encryptsk = aes_cipher.encrypt(sk).decode('utf-8')
        access_key_info = {
            'access_key_id': access_key_id,
            'secret_key': encryptsk,
            'enabled': True,
            'create_at': datetime.datetime.now()
        }
        AccessKey.objects.create(**access_key_info)
        access_key_info['secret_key'] = sk
    else:
        access_key_info = encrypt_sk.first().to_dict()
        encrypt_secret_key = access_key_info['secret_key']
        decypt_key = aes_cipher.decrypt(encrypt_secret_key.encode())
        access_key_info['secret_key'] = decypt_key
    return access_key_info


# 验证访问令牌：鉴权
def access_token_verify(func):
    def _inner(self, request):
        try:
            signature = request.META.get('HTTP_AUTHORIZATION')
            if not signature:
                return HttpResponse({'msg': '缺少签名'}, status=status.HTTP_400_BAD_REQUEST)
            res_status = status.HTTP_403_FORBIDDEN

            # 有效期判断
            signature_local = server_sign(request)
            if not signature == signature_local:
                msg = {"user_info": "签名验证失败（认证失败）", "admin_info": "signature invalidate"}
                return HttpResponse(msg, status=status.HTTP_401_UNAUTHORIZED), False

            # 查询数据库

        except Exception as ex:
            res_status = status.HTTP_401_UNAUTHORIZED
            msg = "[验证失败] Error: %s " % str(ex)
            self.logger.error(msg)
            return HttpResponse({'msg': msg}, status=res_status)
        # 设置缓存
        response = func(self, request)
        return response
    return _inner


# 签名算法: by server
def server_sign(request):

    # Request Headers
    HTTPMETHOD = request.method
    PATH = request.path

    # HOST: scheme (the string 'http') + host
    HOST = request._current_scheme_host
    CONTENT_TYPE = request.content_type

    # Basic Signed Headers
    host = "Host: {}\n".format(HOST)
    content_type = "Content-Type: {}\n".format(CONTENT_TYPE)
    signed_header = host + content_type

    # CanonicalizedRequest
    # URL Encoding


    aes_cipher = AESCipher()
    try:
        with transaction.atomic():
            if request.method == "POST":
                if request.data.get("aesRequest"):
                    request.param_info = aes_cipher.decrypt(request.data.get("aesRequest"))
                else:
                    request.param_info = request.data
            elif request.method == "GET":
                request.param_info = request.GET
            AccessKeyId = request.param_info.get("AccessKeyId")
            timestamp = request.param_info.get('timestamp')
            request.META["HTTP_ACCOUNTID"] = request.param_info.get("AccessKeyId")

        try:
            encrypt_secret_key = AccessKey.objects.get(access_key=AccessKeyId).secret_key
            secret_key = aes_cipher.decrypt(encrypt_secret_key.encode())
        except Exception as ex:
            msg = {"user_info": "签名验证失败（用户不存在）", "admin_info": str(ex)}
            return HttpResponse(msg, status=status.HTTP_401_UNAUTHORIZED)
        data = {
            "Access-Key": AccessKeyId,
            "Secret-Key": secret_key
        }
    except Exception as ex:
        msg = {"user_info": "签名失败", "admin_info": str(ex)}
        return HttpResponse(msg, status=status.HTTP_401_UNAUTHORIZED)

    # Calculate Signature

  # ascending order

    # Percent Encoding
    query_string = ''
    if request.method == 'GET':
        query_string = request.param_info
    canonical_query_str = urlencode(query_string)
    uri = "{} {}".format(HTTPMETHOD, PATH)
    canonical_uri = urlencode(uri)

    # StringToSign
    string_to_sign = HTTPMETHOD + '&' + \
                     signed_header + '&' + \
                     canonical_uri + '&' + \
                     canonical_query_str + '&' + \
                     timestamp
    hmac_data = hmac.new(
                         secret_key.encode("utf8"),
                         "{}{}".format(string_to_sign.lower(), data).encode("utf8"),
                         sha1
                         ).digest()
    b64code = base64.urlsafe_b64encode(hmac_data)
    signature = urlencode(b64code)
    return signature



# 验证签名：身份验证
# def signature_verify(request):
#     try:
#         signature = request.META.get('HTTP_AUTHORIZATION', b'')
#         signature_local = server_sign(request)
#         if signature == signature_local:
#             msg = {"user_info": "签名验证成功"}
#             return HttpResponse(msg, status=status.HTTP_200_OK), True
#     except Exception as ex:
#         msg = {"user_info": "签名验证失败（认证失败）", "admin_info": str(ex)}
#         return HttpResponse(msg, status=status.HTTP_401_UNAUTHORIZED), False


# 签名请求
# def sign_request(account_id, host, method):
#     uri = 'v1/iam/signature' + '/'
#     signature = client_sign(urlencode(uri), host, account_id, method)
#     return signature


def access_login(request):
    response_obj = ResponseObj()
    try:
        # 清除缓存
        request.session.flush()
        aes_cipher = AESCipher()
        keystone_auth = KeystoneAuth()
        ACCOUNT_ID = request.META.get('HTTP_ACCOUNTID')
        # 用户登录
        user_obj = BmUserInfo.objects.values(
            "id", "account", "password", "identity_name", "status", "role__role_limit",
            "default_project_id", "default_project__project_name", "user_agreement").filter(
            id=ACCOUNT_ID, ).exclude(status="deleted").first()
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
        account = user_obj.get('account')
        project_name = user_obj.get("default_project_name")
        project_id = user_obj.get("default_project_id")
        role_limit = user_obj.get('role_limit')

        encrypt_password = user_obj.get('password')
        # encrypt_passwod is "b'SeKa6tMH0a1m1riGfCwERQ=='", should get 'SeKa6tMH0a1m1riGfCwERQ=='

        decrypt_password = aes_cipher.decrypt(encrypt_password[2:-1].encode())

        # openstack 登录,生成 session
        auth_obj = keystone_auth.get_session(username=account, password=decrypt_password, project_name=project_name)
        if auth_obj.is_ok:
            request.session['token'] = auth_obj.content.auth_token
            request.session["username"] = account
            request.session['password'] = decrypt_password
            request.session['project_name'] = project_name
            request.session['project_domain_name'] = "default"
            request.session['user_domain_name'] = "default"
            request.session["account_id"] = account_id
            request.session['project_id'] = project_id
            request.session['role_limit'] = role_limit
            request.session.set_expiry(env_config.session_timeout)
    except Exception as ex:
        return response_obj.json_exception_serial(no=500, user_info="服务异常", admin_info=str(ex))

    return response_obj.json_serial(auth_obj)