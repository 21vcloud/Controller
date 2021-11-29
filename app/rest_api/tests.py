# -*- coding: utf-8 -*-

import base64
import datetime
from hashlib import sha1
import hmac
import json
import requests
from urllib.parse import quote as urlencode


class BackendRequest(object):

    def __init__(self, AccessKeyId, SecretKey, endpoint):
        self.AccessKeyId = AccessKeyId
        self.SecretKey = SecretKey
        self.version = 'v1'
        self.USER_AGNET = 'BareMetalBackend-agent'
        self.endpoint = endpoint

    def concat_url(self, endpoint, path):

        return "%s%s" % (endpoint, path)


    # 签名算法: by client
    def client_sign(self, method, path, params=None, body=None):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {
            "Access-Key": self.AccessKeyId,
            "Secret-Key": self.SecretKey
        }
        # Basic Signed Headers
        host = "Host: {}\n".format(self.endpoint)
        content_type = "Content-Type: {}\n".format('application/json')
        signed_header = host + content_type

        uri = "{} {}".format(method, path)
        canonical_uri = urlencode(uri)

        # CanonicalizedRequest
        # URL Encoding
        if method == 'POST':
            param_info = ""
        else:
            param_info = params

        canonical_query_str = urlencode(param_info)

        # StringToSign
        string_to_sign = method + '&' + \
                         signed_header + '&' + \
                         canonical_uri + '&' + \
                         canonical_query_str + '&' + \
                         timestamp

        # Calculate Signature
        hmac_data = hmac.new(
            self.SecretKey.encode("utf8"),
            "{}{}".format(string_to_sign.lower(), data).encode("utf8"),
            sha1
        ).digest()
        # b64code = base64.b64encode(hmac_data)
        # b64code = b64code.replace('/', '_').replace('+', '-')
        b64code = base64.urlsafe_b64encode(hmac_data)

        signature = urlencode(b64code)
        return timestamp, signature

    def http_request(self, method, path, **kwargs):
        path = '/' + self.version + path
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGNET
        kwargs['headers']['Accept'] = 'application/json'

        timestamp, signature = self.client_sign(method, path, body=kwargs.get('body'),
                                                params=kwargs.get('params'))

        kwargs['headers']['AUTHORIZATION'] = signature

        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body']['timestamp'] = timestamp
            kwargs['data'] = json.dumps(kwargs['body'])

            del kwargs['body']
        else:
            kwargs.setdefault('params', kwargs.get('params', {}))
            kwargs['params']['timestamp'] = timestamp

        url = self.concat_url(self.endpoint, path)
        resp = requests.request(method, url, **kwargs)
        if resp.status_code == 200:
            response = resp.json()

        else:
            resp.raise_for_status()

        return resp.json()


    def access_login(self):
        body = {
            "AccessKeyId": self.AccessKeyId
        }
        url_path = '/iam/access_login'
        self.http_request('POST', url_path, body=body)


if __name__ == '__main__':
    my_client = BackendRequest(AccessKeyId='ca038fe789854a748e7930610229b7c5',
                               SecretKey='zbsDRJ0odk62rtApgfDcfXyZhp5ywp',
                               endpoint="http://127.0.0.1:8002")
    my_client.access_login()