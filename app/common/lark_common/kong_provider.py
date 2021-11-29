# -*- coding: utf-8 -*-


class APIHandler(object):
    def __init__(self, endpoint, api_key):
        self.endpoint = endpoint
        self.header = {u"apikey": api_key}
