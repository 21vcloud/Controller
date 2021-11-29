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
import time,datetime
# from django.test import TestCase
from baremetal_service import handler
from common import exceptions as exc

# class testAddMember(TestCase):
class testAddMember():
    def create_pool_member(self,name=None,address=None,protocol_port=None,weight=None,instance_id=None):
        openstack_client = utils.get_admin_client()
        # To create a member, the load balancer must have an ACTIVE provisioning status.
        # 进行循环获取pool的状态
        begin_time1 = time.time()
        print(begin_time1,"-------------")
        while True:
            end_time1 = time.time()
            run_time1 = end_time1 - begin_time1
            if run_time1 > 10:
                raise exc.TimeoutError()
            pool_detail = openstack_client.load_balancer.get_pool("bbbe12df-9994-4221-a1d0-e1c77bd1a3e5").to_dict()
            pool_status = pool_detail["provisioning_status"]
            now_time1=datetime.datetime.now()
            print(name,now_time1,pool_status)
            if pool_status == "ACTIVE" or pool_status == "ERROR":
                break
            time.sleep(2)

        # 进行循环获取load balancer的状态
        begin_time2 = time.time()
        while True:
            end_time2 = time.time()
            run_time2 = end_time2 - begin_time2
            if run_time2 > 50:
                raise exc.TimeoutError()
            load_balancer_detail = openstack_client.load_balancer.get_load_balancer("bcb25c73-15f3-4e9c-8161-6bc3f1a2a30c").to_dict()
            load_balancer_status = load_balancer_detail["provisioning_status"]
            now_time2 = datetime.datetime.now()
            print("负载均衡状态", now_time2, load_balancer_status)
            if load_balancer_status == "ACTIVE" or load_balancer_status == "ERROR":
                break
            time.sleep(2)

        dict_attrs = {
            'name': name,
            'address': address,
            'protocol_port': protocol_port,
            'weight': weight
        }
        now_time3 = datetime.datetime.now()
        print("开始添加成员的时间", now_time3)
        load_balancer_pool_member = openstack_client.load_balancer.create_member("bbbe12df-9994-4221-a1d0-e1c77bd1a3e5", **dict_attrs)
        # 成员添加成功，增加mapping 关系
        server_mapping_dict = {
            "instance_id": instance_id,
            "pool_id": "bbbe12df-9994-4221-a1d0-e1c77bd1a3e5",
            "loadbancer_id": "bcb25c73-15f3-4e9c-8161-6bc3f1a2a30c",
            "member_id": load_balancer_pool_member.id
        }
        return load_balancer_pool_member
    def add_member(self):

        result=self.create_pool_member(name="liuwei",
                                address="192.168.21.21",
                                protocol_port=22,
                                weight=2,
                                instance_id="48ba69ba-cf47-4307-9880-43483f4edce2")

    def add_member2(self):
        result = self.create_pool_member(name="app5",
                                         address="192.168.21.18",
                                         protocol_port=33,
                                         weight=4,
                                         instance_id="1a28860b-d71d-4bc2-bf45-3a03f82b7eb4")
    def add_member3(self):
        result = self.create_pool_member(name="bz_adminbuy",
                                         address="192.168.21.9",
                                         protocol_port=55,
                                         weight=6,
                                         instance_id="0270d7c2-ffc0-49b7-a798-1a82b2f870b4")

    def test(self):
        threads = []
        threads.append(threading.Thread(target=self.add_member()))
        threads.append(threading.Thread(target=self.add_member2()))
        threads.append(threading.Thread(target=self.add_member3()))
        for t in threads:
            print("%s: %s" % (t, time.ctime(time.time())))
            t.start()

# testAddMember.test()
