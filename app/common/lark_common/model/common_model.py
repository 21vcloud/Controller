# -*- coding: utf-8 -*-

import json
import jsonpickle

from django.http import HttpResponse


class ResponseObj(object):
    def __init__(self):
        self.message = None
        self.content = None
        self.is_ok = True
        self.no = 200

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def json_exception_serial(self, user_info, admin_info, no):
        self.no = no
        self.message = {"user_info": user_info, "admin_info": admin_info}
        self.is_ok = False

        # logout validate
        logout_list = ["""object has no attribute 'keystone_session'""", 'Failed to validate token (HTTP 404)']
        for logout_error in logout_list:
            if logout_error in admin_info:
                self.no = 401
                break

        json_data = jsonpickle.dumps(self, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    def json_serial(self, info):
        self.content = info
        json_data = jsonpickle.dumps(self, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")


class MonitorResponseObj(object):
    def __init__(self):
        self.message = None
        self.data = {}
        self.success = True

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def json_exception_serial(self, user_info, admin_info):
        self.message = {"user_info": user_info, "admin_info": admin_info}
        self.is_ok = False

        # logout validate
        logout_list = ["""object has no attribute 'keystone_session'""", 'Failed to validate token (HTTP 404)']
        for logout_error in logout_list:
            if logout_error in admin_info:
                break

        json_data = jsonpickle.dumps(self, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    def json_serial(self, info):
        self.content = info
        json_data = jsonpickle.dumps(self, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

