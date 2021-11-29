# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""

from django.test import TestCase
from common.api_request import RequestClient, RequestClientTwo
from BareMetalControllerBackend.conf.env import env_config
from common import utils
import datetime

class testCmdb(TestCase):


    def instance_delete(self,):
        request_cmdb_customize_client = RequestClientTwo(endpoint=env_config.cmdb_customize_service,
                                                         api_key="")
        result = request_cmdb_customize_client.baremetal(dict_param={}, method="DELETE",
                                                         url_param_list=["b18eca49-5bb3-402b-af41-c18619f4fd0f"+"/"])
        print(result.success)


    def instance_create(self):
        # request_client = RequestClient(endpoint="http://127.0.0.1:8002/service/", api_key="")
        # job_model = {
        #     "id": "5e951f21232407d88a9eb248", "order_id": "BMS201911201138533331803", "uuid": "83097289-7f8a-46fd-bdfe-fcab82ede06e",
        #     "flavor_name": "戴尔", "flavor_id": "11a2c533-73cc-4f95-8e7b-0055b7ec18a7", "image_name": "Ubuntu14.04",
        #     "image_id": "b3966f8b-0bc3-4b38-8ade-dc2350097dc2", "monitoring": False, "vulnerability_scanning": False,
        #     "disk_info": [{"count": 1, "size": 100, "volume_order_price": 100, "volume_type": "inspure_iscsi"},
        #                   {"count": 2, "size": 100, "volume_order_price": 200, "volume_type": "inspure_iscsi"}],
        #     "network_path_type": "private", "network": "oyguyj", "network_id": "5856ff0c-b989-475a-bf85-f09cce87ebb6",
        #     "floating_ip_info": {"external_line_type": "three_line_ip", "firewall_id": "5dc0df6ce063aa50a2e3768a",
        #                          "firewall_name": "默认防火墙kkk", "floating_ip_allocation": True, "floating_ip_order_price": 5025,
        #                          "qos_policy_name": "100M"}, "floating_ip_allocation": None, "floating_ip_bandwidth": None,
        #     "floating_ip_line": None, "firewall_id": None, "firewall_name": None, "service_name": "wei_test",
        #     "login_method": "keypair", "service_username": "", "service_password": "", "public_key": "p",
        #     "create_at": datetime.datetime(2019, 11, 20, 11, 38, 53, 334989), "update_at": None, "deleted": None, "status": None,
        #     "order_info": {"id": "BMS201911201138533331803", "account_id": "ca038fe789854a748e7930610229b7c5",
        #                    "contract_number": "qq1233", "project_id": "4f97f27cb0af4878bd081a7784d59dae",
        #                    "region": "regionOne", "order_type": "increase", "order_price": "8450.00",
        #                    "product_type": "ECBM",
        #                    "product_info": '{"裸金属":"实例名称：liuwei","实例":"基础型 (Intel Xeon E5-2620 v3*2|6*2|2.4GHz|128G|2*600G SAS System Disk RAID 1+ 6*600G SAS RAID 5)","操作系统":"Ubuntu14.04","云硬盘":"高速云盘100G*3个","网络":"dsssss-oyguyj","公网IP":"是","带宽":"100Mbps 三线","防火墙":"默认防火墙kkk","登录方式":"密钥对"}',
        #                     "billing_model": "标准合同", "service_count": 1, "delivery_status": "delivering",
        #                    "create_at": datetime.datetime(2019, 11, 20, 11, 38, 53, 296090), "update_at": None,
        #                    "deleted": None},
        #     "session_info": {
        #                      # "token": "gAAAAABd1LUpR3U6GE4aqvQgGAmnMmqpFimjkX5pH6dX4zBDf4azlYs5Ne7eqe7p04sCMcZWxyrbxf4Dqe8HvbpvNNOBKYTC7zAcnYhuxHTV9k2iXPrY0nJTjSXKFEHFooOe2U1_zJJuAmOKIFd7qoYfve49AAJQY51xInt6xS60txQ4_ee5u4A",
        #                      "username": "admin", "password": "Fp5SQB9uN6T0uR1xWn9h2tVB2", "project_name": "qq",
        #                      "project_domain_name": "default", "user_domain_name": "default", "account_id": "589d0d6781314a8b8c28cf3982ce344c",
        #                      "project_id": "4f97f27cb0af4878bd081a7784d59dae", "role_limit": 20, "_session_expiry": 2700},
        #     "result": {
        #                'volume_create': {'volume_id_list': ['a2fcc4c3-0eda-4184-8676-cb40ba4a4bc3', 'da9d9e16-c0dc-462b-9734-c6e3831cefd4', 'a3fec6ac-6c20-4973-976e-8d01eaeda9c6'], 'success': True},
        #                'volume_attach': {'volume_id_list': ['a2fcc4c3-0eda-4184-8676-cb40ba4a4bc3', 'da9d9e16-c0dc-462b-9734-c6e3831cefd4', 'a3fec6ac-6c20-4973-976e-8d01eaeda9c6'], 'instance_uuid': '4dc5029a-ca1c-42d8-a71f-5241d3b62451', 'success': True},
        #                'floating_ip_create': {'floating_ip_id_list': ['95be14c9-5507-4b78-8f7d-204b0128d9b9'], 'success': True},
        #                'floating_ip_attach': {'floating_ip_id_list': ['95be14c9-5507-4b78-8f7d-204b0128d9b9'], 'instance_uuid': '4dc5029a-ca1c-42d8-a71f-5241d3b62451', 'success': True},
        #                'instance_create': {'uuid': '4dc5029a-ca1c-42d8-a71f-5241d3b62451', 'status': 'active',
        #                                'service_instance_id': '4dc5029a-ca1c-42d8-a71f-5241d3b62451', 'success': True}
        #     }
        # }
        # machine_callback = {
        #     "machine_id": job_model.get("id"),
        #     "uuid": job_model.get("uuid"),
        #     "job_model": job_model
        # }
        # machine_result = request_client.service_machine_info_feedback(dict_param=machine_callback,
        #                                                                    method="POST")
        from BareMetalControllerBackend.conf.env import EnvConfig
        env_config = EnvConfig()
        request_cmdb_customize_client = RequestClientTwo(endpoint=env_config.cmdb_customize_service,
                                                              api_key="")
        request_cmdb_asset_client = RequestClientTwo(endpoint=env_config.cmdb_asset_service,
                                                          api_key="")

        dict_info = {
            "uuid": "b18eca49-5bb3-402b-af41-c18619f4fd0f",
            "zone": "regionOne",
            "project_id": "a5eb3c5c013b49119bfd856cd3fcb4d6"
        }
        result = request_cmdb_customize_client.baremetal(dict_param=dict_info, method="POST", is_add=True)

        print(result.success)


    def tag_create(self):
        from BareMetalControllerBackend.conf.env import EnvConfig
        env_config = EnvConfig()
        request_cmdb_customize_client = RequestClientTwo(endpoint=env_config.cmdb_customize_service,
                                                              api_key="")
        request_cmdb_asset_client = RequestClientTwo(endpoint=env_config.cmdb_asset_service,
                                                          api_key="")

        dict_info = {
            "abstract_custom": "b18eca49-5bb3-402b-af41-c18619f4fd0f",
            "tag_name": "zabbix",
            "tag_type": "agent"
        }
        result = request_cmdb_asset_client.abstract_tag(dict_param=dict_info, method="POST", is_add=True)

        print(result.success)


    def instance_put(self):
        from BareMetalControllerBackend.conf.env import EnvConfig
        env_config = EnvConfig()
        request_cmdb_customize_client = RequestClientTwo(endpoint=env_config.cmdb_customize_service,
                                                              api_key="")
        request_cmdb_asset_client = RequestClientTwo(endpoint=env_config.cmdb_asset_service,
                                                          api_key="")

        dict_info = {
            "uuid": "b18eca49-5bb3-402b-af41-c18619f4fd0f",
            "status":"power on"
        }

        result = request_cmdb_customize_client.baremetal(dict_param=dict_info, method="PUT")

        print(result.success)






