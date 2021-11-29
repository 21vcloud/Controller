# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""

from django.test import TestCase

from BareMentalConsole.utils.env import env_config
from common.api_request import RequestClient


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
            dict_param={"key_value": "introList"}, method="GET")
        self.assertTrue(apollo_info_obj.is_ok)

    def create_contact_to_us(self):
        dict_param = {
            "customer_name": "string",
            "phone": "string",
            "email": "string",
            "company": "string",
            "department": "string",
            "job_position": "string",
            "issue_content": "string",
            "issue_type": "string",
            "created_at": "2019-04-23T02:23:49.682Z"
        }
        contact_to_us_obj = self.infra_machine_client.contact_to_us(dict_param=dict_param, method="POST")
        self.assertTrue(contact_to_us_obj.is_ok)
