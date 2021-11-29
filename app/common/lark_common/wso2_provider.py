# -*- coding: utf-8 -*-

import json, time, requests

from common.lark_common.utils import EncodeHandler


class APIHandler(object):
    def __init__(self, endpoint, wso2_token):
        self.endpoint = endpoint
        self.header = {u"Authorization": u"Bearer " + wso2_token}


class TokenHandler(object):
    def __init__(self, url, username=None, password=None, authorization=None, logger=None):
        self.url = url
        self.__token_obj = None
        self.__token_create_at = None
        self.__username = username
        self.__password = password
        self.__authorization = authorization
        self.__logger = logger

    def get_token(self):
        if self.__token_obj is None:
            self.generate_user_token()
        elif self.__token_create_at + self.__token_obj['expires_in'] - 600 < time.time():
            self.refresh_user_token()

        return self.__token_obj[u'access_token']

    def generate_app_token(self):
        my_headers = {
            "Authorization": "Basic " + self.__authorization}
        post_data = {"grant_type": "client_credentials"}

        r = requests.post(self.url, headers=my_headers, data=post_data, verify=False)
        print(r.content)

        response_obj = EncodeHandler.byteify(json.loads(r.content))
        self.__token_obj = response_obj
        self.__token_create_at = time.time()

    def generate_user_token(self):
        my_headers = {
            "Authorization": "Basic " + self.__authorization,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        post_data = {"grant_type": "password",
                     "username": self.__username,
                     "password": self.__password}

        r = requests.post(self.url, headers=my_headers, data=post_data, verify=False)

        if r.status_code != 200:
            if self.__logger is not None:
                self.__logger.warn("generate_user_token status code error. Status code is " + r.status_code)

            return None

        if self.__logger is not None:
            self.__logger.debug("generate_user_token: " + r.content)

        response_obj = EncodeHandler.byteify(json.loads(r.content))
        self.__token_obj = response_obj
        self.__token_create_at = time.time()

    def refresh_user_token(self):
        if self.__token_obj['refresh_token'] is None:
            return

        my_headers = {
            "Authorization": "Basic " + self.__authorization,
            "Content-Type": "application/x-www-form-urlencoded"}
        post_data = {"grant_type": "refresh_token",
                     "refresh_token": self.__token_obj['refresh_token'],
                     "scope": "PRODUCTION"}

        r = requests.post(self.url, headers=my_headers, data=post_data, verify=False)

        if r.status_code != 200 and self.__logger is not None:
            self.__logger.warn("refresh_user_token status code error. Status code is " + r.status_code)

        if self.__logger is not None:
            self.__logger.debug("refresh_user_token: " + r.content)

        response_obj = EncodeHandler.byteify(json.loads(r.content))
        self.__token_obj = response_obj
        self.__token_create_at = time.time()
