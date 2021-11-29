# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""

import jsonpickle
import requests

from common.lark_common.kong_provider import APIHandler
from common.lark_common.model.common_model import ResponseObj
from common.lark_common.utils import EncodeHandler, JsonUtils
from common.lark_common.utils import AESCipher


class RequestClient(APIHandler):
    def __init__(self, endpoint=None, api_key=None, logger=None):
        APIHandler.__init__(self, endpoint=endpoint, api_key=api_key)

        self.__post_header = self.header
        self.__post_header['Accept'] = u'application/json'
        self.__post_header['Content-type'] = u'application/json'
        self.__post_header['Connection'] = u'close'
        self.__get_header = self.header
        self.logger = logger
        self.aes_cipher = AESCipher()

    def __getattr__(self, name):
        def handler_function(dict_param, method, token=None):
            return self.make_request_by_operation(name, dict_param, method, token)

        return handler_function

    def make_request_by_operation(self, path_url, args, method, token):
        if method and method == "POST":
            self.__post_header["token"] = token
            ret = self.__post(url=path_url, post_data=args)
            self.__post_header.pop("token")
        else:
            self.__get_header["token"] = token
            ret = self.__get(url=path_url, param=args)
            self.__get_header.pop("token")
        return ret

    def __get(self, url, param):
        """
        HTTP Get 方法工具类
        :param url:  目标地址
        :param param:  参数
        :return:  返回对象，通常为Response Obj
        """
        response_obj = ResponseObj()

        url = self.endpoint + url

        http_response = requests.get(url, headers=self.__get_header, verify=False, params=param)

        response_obj.no = http_response.status_code

        if http_response.status_code != 200:
            response_obj.is_ok = False
            response_obj.message = http_response.reason
        else:
            response_obj.is_ok = True
            http_content = EncodeHandler.byteify(jsonpickle.loads(http_response.content))
            response_obj = JsonUtils.convert_dict_to_object(http_content)
            response_obj.json = http_content

        return response_obj

    def __post(self, url, post_data):
        """
        HTTP POST 方法工具类
        :param url:  目标地址
        :param post_data:  参数
        :return:  返回对象，通常为Response Obj
        """
        response_obj = ResponseObj()
        # 加密

        encrypt_post_data = self.aes_cipher.encrypt(post_data)
        json_data = {"aesRequest": encrypt_post_data.decode()}
        json_data = jsonpickle.dumps(json_data)
        post_url = self.endpoint + url
        http_response = requests.post(post_url, headers=self.__post_header, data=json_data, verify=False)

        if http_response.status_code != 200:
            response_obj.is_ok = False
            response_obj.no = http_response.status_code
            response_obj.message = http_response.reason
            return response_obj
        http_content = EncodeHandler.byteify(jsonpickle.loads(http_response.content))
        response_obj = JsonUtils.convert_dict_to_object(http_content)
        response_obj.json = http_content
        return response_obj

    def __post_list(self, url, post_data):
        """
        HTTP Post支持批量数据提交，例如批量添加。函数内会将对象类型转化为list对象
        :param url:  POST提交地址
        :param post_data: 批量提交数据
        :return:  返回值，通常为Response Obj
        """
        post_data_list = []
        if isinstance(post_data, list):
            post_data_list = post_data
        else:
            post_data_list.append(post_data)

        return self.__post(url=url, post_data=post_data_list)
