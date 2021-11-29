# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""

from django.test import TestCase
from api_tests.test_api_request import RequestClient
from BareMetalControllerBackend.conf.env import env_config


class TestAccountClient(TestCase):
    def setUp(self):
        self.infra_machine_client = RequestClient(
            # DEV
            endpoint=env_config.baremetal_endpoint,
            # endpoint="http://124.251.110.196:9001/account/",

            # UAT
            # endpoint="http://124.251.110.196:8000/uat/baremental/",
            api_key="")

    def get_info_by_key(self):
        apollo_info_obj = self.infra_machine_client.get_info_by_key(
            dict_param={"key_value ": "wei.panlong@21vianet.com"}, method="GET")
        self.assertTrue(apollo_info_obj.is_ok)

    def create_contact_to_us(self):
        contact_to_us_obj = self.infra_machine_client.contact_to_us(dict_param={"key_value": "string"}, method="POST")
        self.assertTrue(contact_to_us_obj.is_ok)
