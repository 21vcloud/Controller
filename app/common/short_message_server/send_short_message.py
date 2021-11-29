# coding: utf-8

import hashlib
from BareMetalControllerBackend.conf.env import EnvConfig

from common.api_request import RequestClient

def get_info_by_key(self):
    apollo_info_obj = self.infra_machine_client.get_info_by_key(
        dict_param={"key_value": "introList"}, method="GET")
    self.assertTrue(apollo_info_obj.is_ok)


class ProviderShortMessageNotification(object):

    def __init__(self):
        self.env_config = EnvConfig()
        self.SMS_USER = self.env_config.short_message_sms_user
        self.SMS_KEY = self.env_config.short_message_sms_key
        self.smsapi_client = RequestClient(
            # endpoint=env_config.baremetal_endpoint,
            endpoint=self.env_config.short_message_smsapi_endpoint,
            api_key="")

    def send(self, phone_number, code):
        dict_param = self.__generate_code_send_info()
        dict_param["phone"] = phone_number
        dict_param["code"] = code

        signature = self.__signature_encypt(dict_param=dict_param)
        dict_param["signature"] = signature

        response_obj = self.smsapi_client.sendCode(dict_param=dict_param, method="GET")
        return response_obj

    def __generate_code_send_info(self):
        dict_parm = dict()
        dict_parm["smsUser"] = self.env_config.short_message_sms_user
        dict_parm["labelId"] = self.env_config.short_message_label_id
        dict_parm["signName"] = self.env_config.short_message_sign_name
        return dict_parm

    def __signature_encypt(self, dict_param):
        param_keys = list(dict_param.keys())
        param_keys.sort()

        param_str = ''
        for key in param_keys:
            param_str += key + '=' + str(dict_param[key]) + '&'

        param_str = param_str[:-1]

        sign_str = self.SMS_KEY + '&' + param_str + '&' + self.SMS_KEY
        signature = hashlib.md5(sign_str.encode('utf8')).hexdigest()
        print(signature)
        return signature
