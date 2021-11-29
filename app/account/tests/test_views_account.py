# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""
import datetime

from django.test import TestCase

from BareMetalControllerBackend.conf.env import env_config
from common.api_request import RequestClient
from baremetal_service.repository import service_model as service_model
from baremetal_openstack import handler


class TestAccountClient(TestCase):
    def setUp(self):
        self.infra_machine_client = RequestClient(
            # DEV
            # endpoint=env_config.account_endpoint,
            # endpoint="http://124.251.110.196:9001/account/",
            endpoint="http://127.0.0.1:8003/account/",

            # UAT
            # endpoint="http://124.251.110.196:8000/uat/account/",
            api_key="")

    def token_verify(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei.panlong"}, method="GET")

        content = response_obj.content[0]
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": content.account, "password": content.password}, method="POST")

        response_obj = self.infra_machine_client.token_verify(dict_param={"token": login_response_obj.content.token},
                                                              method="GET")
        self.assertTrue(response_obj.is_ok)

    def token_verify_not_exit(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei.panlong"}, method="GET")
        content = response_obj.content[0]
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": content.account, "password": content.password}, method="POST")
        response_obj = self.infra_machine_client.token_verify(
            dict_param={"token": "123" + login_response_obj.content.token}, method="GET")
        self.assertFalse(response_obj.is_ok)

    def token_verify_not_timeout(self):
        response_obj = self.infra_machine_client.token_verify(
            dict_param={"token": "123123|1231231"}, method="GET")
        self.assertFalse(response_obj.is_ok)

    def register(self):
        import datetime
        response_obj = self.infra_machine_client.register(
            dict_param={"account": "%s@21vianet.com" % datetime.datetime.now(), "password": "abcd-1234"}, method="POST")
        self.assertTrue(response_obj.is_ok)

    def register_fail(self):
        response_obj = self.infra_machine_client.register(
            dict_param={"account": "wei.panlong@21vianet.com", "password": "abcd-1234"}, method="POST")
        self.assertFalse(response_obj.is_ok)

    def login(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei"}, method="GET")
        content = response_obj.content[0]
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": content.account, "password": content.password}, method="POST")
        self.assertTrue(response_obj.is_ok)

    def login_fail(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei.panlong"}, method="GET")
        content = response_obj.content[0]
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": content.account, "password": content.password + '1'}, method="POST")
        self.assertFalse(login_response_obj.is_ok)

    def login_fail_for_account(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei.panlong"}, method="GET")
        content = response_obj.content[0]
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": content.account + '1', "password": content.password}, method="POST")
        self.assertFalse(login_response_obj.is_ok)

    def logout(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei.panlong"}, method="GET")
        content = response_obj.content[0]
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": content.account, "password": content.password}, method="POST")
        logout_response_obj = self.infra_machine_client.logout(
            dict_param={"account": content.account, "password": content.password}, method="POST",
            token=login_response_obj.content.token)
        self.assertTrue(logout_response_obj.is_ok)

    def update_password(self):
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "wei.panlong"}, method="GET")
        content = response_obj.content[0]
        update_response_obj = self.infra_machine_client.update_password(
            dict_param={"email": content.account}, method="POST")
        self.assertTrue(update_response_obj.is_ok)

    def confirm_update_password(self):
        response_obj_password = self.infra_machine_client.update_password(
            dict_param={"email": "wei.panlong@21vianet.com"}, method="POST")
        response_obj = self.infra_machine_client.confirm_update_password(
            dict_param={"email": "wei.panlong@21vianet.com", "code": response_obj_password.content.code,
                        "new_password": "abcd-1234"}, method="POST")
        self.assertTrue(response_obj.is_ok)

    def query_account_info_by_keywords(self):
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": "wei.panlong@21vianet.com", "password": "abcd-1234"}, method="POST")
        response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "huo.weiwei"}, method="GET", token=login_response_obj.content.token)
        self.assertTrue(response_obj.is_ok)

    def user_info_update(self):
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": "wei.panlong@21vianet.com", "password": "abcd-1234"}, method="POST")
        user_response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "huo.weiwei"}, method="GET", token=login_response_obj.content.token)
        dict_param = user_response_obj.json["content"][0]
        dict_param.pop("_state")

        response_obj = self.infra_machine_client.user_info_update(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)

    def user_info_update_user_id_error(self):
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": "wei.panlong@21vianet.com", "password": "abcd-1234"}, method="POST")
        user_response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "huo.weiwei"}, method="GET", token=login_response_obj.content.token)
        dict_param = user_response_obj.json["content"][0]
        dict_param.pop("_state")
        dict_param["id"] = "1231123123"
        response_obj = self.infra_machine_client.user_info_update(dict_param=dict_param, method="POST")
        self.assertFalse(response_obj.is_ok)

    def user_info_update_user_id_not_exit(self):
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": "wei.panlong@21vianet.com", "password": "abcd-1234"}, method="POST")
        user_response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "huo.weiwei"}, method="GET", token=login_response_obj.content.token)
        dict_param = user_response_obj.json["content"][0]
        dict_param.pop("_state")
        dict_param.pop("id")
        response_obj = self.infra_machine_client.user_info_update(dict_param=dict_param, method="POST")
        self.assertFalse(response_obj.is_ok)

    def user_info_update_param_error(self):
        login_response_obj = self.infra_machine_client.login(
            dict_param={"account": "wei.panlong@21vianet.com", "password": "abcd-1234"}, method="POST")
        user_response_obj = self.infra_machine_client.query_account_info_by_keywords(
            dict_param={"keywords": "huo.weiwei"}, method="GET", token=login_response_obj.content.token)
        dict_param = user_response_obj.json["content"][0]
        response_obj = self.infra_machine_client.user_info_update(dict_param=dict_param, method="POST")
        self.assertFalse(response_obj.is_ok)

    def update_phone(self):
        """
        {
  "account_id": "5cc1afe1acaea162074f0761",
  "phone_number": "15010824265"
}
{
  "account_id": "5cc1afe1acaea162074f07611",
  "phone_number": "15010824266"
}{
  "account_id": "5cc1afe1acaea162074f0761",
  "phone_number": "15010824266"
}{
  "account_id": "5cc1afe1acaea162074f0761",
  "phone_number": "18101029681",
  "new_phone_number": "15010824266",
  "code": "891547"
}
        :return:
        """
        pass


class TestAccountProjectClient(TestCase):
    def setUp(self):
        self.infra_machine_client = RequestClient(
            # DEV
            endpoint=env_config.account_project_endpoint,
            # endpoint="http://124.251.110.196:9001/account/",

            # UAT
            # endpoint="http://124.251.110.196:8000/uat/account/",
            api_key="")

    def project_create(self):
        dict_param = {
            "account_list": ["5cc1afe1acaea162074f0761"],
            "project_name": "%s" % datetime.datetime.now(),
            "description": "string",
            "status": "active",
            "create_at": "2019-04-29T03:47:14.025Z"
        }
        response_obj = self.infra_machine_client.project_create(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)

    def project_create_double_project(self):
        dict_param = {
            "keywords": "2019",
        }
        response_obj = self.infra_machine_client.project_info_query_by_keywords(dict_param=dict_param, method="GET")
        dict_param = response_obj.json["content"][0]
        dict_param.pop("_state")
        dict_param.pop("update_at")
        response_obj = self.infra_machine_client.project_create(dict_param=dict_param, method="POST")
        self.assertFalse(response_obj.is_ok)

    def project_create_no_account(self):
        dict_param = {
            "project_name": "%s" % datetime.datetime.now(),
            "description": "string",
            "status": "active",
            "create_at": datetime.datetime.now()
        }
        response_obj = self.infra_machine_client.project_create(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)

    def project_update(self):
        dict_param = {
            "id": "5cc6a02dac578ba9e7b4624a",
            "account_list": [
                "5cc1832aab85c31d2a7b975e", "5cc1832aab85c31d2a7b975e"
            ],
            "project_name": "Melon Test",
            "update_at": "2019-04-29T07:13:25.049Z",
        }
        response_obj = self.infra_machine_client.project_update(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)

    def project_update_no_proejct(self):
        dict_param = {
            "id": "5cc6a02dac578ba9e7b4624a123",
            "account_list": [
                "5cc1832aab85c31d2a7b975e",
            ],
            "project_name": "Melon Test",
            "update_at": "2019-04-29T07:13:25.049Z",
        }
        response_obj = self.infra_machine_client.project_update(dict_param=dict_param, method="POST")
        self.assertFalse(response_obj.is_ok)

    def project_info_query_by_keywords(self):
        dict_param = {
            "keywords": "Melon",
        }
        response_obj = self.infra_machine_client.project_info_query_by_keywords(dict_param=dict_param, method="GET")
        self.assertTrue(response_obj.is_ok)

    def project_info_query_by_no_keywords(self):
        dict_param = {
            "keywords": "",
        }
        response_obj = self.infra_machine_client.project_info_query_by_keywords(dict_param=dict_param, method="GET")
        self.assertTrue(response_obj.is_ok)

    def project_info_query_by_no_results(self):
        dict_param = {
            "keywords": str(datetime.datetime.now()),
        }
        response_obj = self.infra_machine_client.project_info_query_by_keywords(dict_param=dict_param, method="GET")
        self.assertTrue(response_obj.is_ok)


class TestAccountEnterpriseClient(TestCase):
    def setUp(self):
        self.infra_machine_client = RequestClient(
            # DEV
            # endpoint=env_config.account_enterprise_endpoint,
            # endpoint="http://124.251.110.196:9001/account/",
            endpoint="http://172.16.107.71:8000/auth/",

            # UAT
            # endpoint="http://124.251.110.196:8000/uat/account/",
            api_key="")

    def enterprise_create(self):
        dict_param = {
            "enterprise_name": str(datetime.datetime.now()),
            "abbreviation": "lenovo",
            "description": "联想世纪",
            "industry1": "IT服务",
            "industry2": "实际",
            "location": "北京",
            "sales": "魏盼龙",
            "system_id": "1232233456789",
            "create_at": "2019-04-29T08:39:27.751Z"
        }
        response_obj = self.infra_machine_client.enterprise_create(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)

    def enterprise_create_repeat_name(self):
        dict_param = {
            "enterprise_name": "北京联想",
            "abbreviation": "lenovo",
            "description": "联想世纪",
            "industry1": "IT服务",
            "industry2": "实际",
            "location": "北京",
            "sales": "魏盼龙",
            "system_id": "1232233456789"
        }
        response_obj = self.infra_machine_client.enterprise_create(dict_param=dict_param, method="POST")
        self.assertFalse(response_obj.is_ok)

    def enterprise_info_query_by_keywords(self):
        dict_param = {
            "keywords": "2019"
        }
        response_obj = self.infra_machine_client.enterprise_info_query_by_keywords(dict_param=dict_param, method="GET")
        self.assertTrue(response_obj.is_ok)

    def enterprise_update(self):
        query_dict_param = {
            "keywords": "2019"
        }
        query_response_obj = self.infra_machine_client.enterprise_info_query_by_keywords(dict_param=query_dict_param,
                                                                                         method="GET")
        dict_param = query_response_obj.json["content"][0]
        dict_param.pop("_state")
        dict_param.pop("update_at")
        dict_param["enterprise_name"] = "wei_%s" % datetime.datetime.now()
        response_obj = self.infra_machine_client.enterprise_update(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)



    def get_session(self):
        dict_param = {
  "username": "admin",
  "password": "ql21Fm7vPMAzbYJvKkf0MsDQj",
  "project_name": "admin",
  "project_domain_name": "default",
  "user_domain_name": "default",
  "region": "regionOne"
}
        response_obj = self.infra_machine_client.get_session(dict_param=dict_param, method="POST")
        self.assertTrue(response_obj.is_ok)


class TestVpcs(TestCase):
    def setUp(self):
        self.project_id = "7ae5a60714014778baddea703b85cd93"
        self.vpc_id = 448

    def test_get_vpcs_from_db(self):
        result = handler.get_vpc_net_cidrs(self.vpc_id)



class TestServiceCreate(TestCase):

    def setUp(self):
        self.project_id = "7ae5a60714014778baddea703b85cd93"
        self.request_client = RequestClient(endpoint=env_config.service_volume_endpoint, api_key="")

    def service_create(self):
        self.request_client = RequestClient(endpoint=env_config.service_volume_endpoint, api_key="")
