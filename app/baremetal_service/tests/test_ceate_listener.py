# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""

# from django.test import TestCase
# from api_tests.test_api_request import RequestClient
# from BareMetalControllerBackend.conf.env import env_config
from baremetal_service import handler
# from common.lark_common.model.common_model import ResponseObj
# from rest_framework import viewsets
import threading
from common import utils
import time
from django.test import TestCase

class testLb(TestCase):
    def delete_test1(self):
        openstack_client = utils.get_admin_client()
        pool_delete = openstack_client.load_balancer.delete_pool("17ba943d-1d96-40d5-a2ed-b017f43e4ae5")

    def update_test1(self):
        openstack_client = utils.get_admin_client()
        pool_update = openstack_client.load_balancer.update_pool("ab82c371-5d4d-4f5b-a721-fad9f89ba10e",
                                                                     name="ding_test_update")

    def test(self):
        threads = []
        threads.append(threading.Thread(target=self.update_test1()))
        threads.append(threading.Thread(target=self.delete_test1()))
        for t in threads:
            print("%s: %s" % (t, time.ctime(time.time())))
            t.start()
        print("删除成功")
