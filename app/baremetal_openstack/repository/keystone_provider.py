# Create your views here.
# -*- coding:utf-8 -*-

import logging

from django.db import transaction
from keystoneauth1 import exceptions as keystone_exceptions

from BareMetalControllerBackend.conf.env import EnvConfig
from common.lark_common.model.common_model import ResponseObj
from common.openstack import context
from common import utils
from account.repository import auth_models

config = EnvConfig()
LOG = logging.getLogger(__name__)


class KeystoneAuth(object):

    def __init__(self, openstack_client=None):
        self.openstack_client = openstack_client

    def get_openstack_client_by_request(self, request):
        try:
            self.openstack_client = utils.get_openstack_client(request)
        except keystone_exceptions.NotFound:
            # Maybe token has expired,Get client use password
            self.openstack_client = utils.get_openstack_client(request, auth_plugin='password')
        return self.openstack_client

    def get_session(self, username, password, project_name, project_domain_name="default", user_domain_name="default"):
        """
        Return session
        :param param_dict:
        :return: sessionId
        """
        response_obj = ResponseObj()

        try:
            cctext = context.RequestContext(auth_url=config.auth_url, username=username,
                                            password=password, project_name=project_name,
                                            project_domain_name=project_domain_name,
                                            user_domain_name=user_domain_name)

            auth_token = cctext.auth_token
        except keystone_exceptions.Unauthorized as ex:
            response_obj.message = {"user_info": "认证失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 401
            return response_obj
        response_obj.content = cctext
        response_obj.is_ok = True
        return response_obj

    # project 相关
    def create_project(self, project_name, description, domain_id="default"):
        """
        Create an openstack project
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            project = self.openstack_client.create_project(name=project_name, description=description, domain_id=domain_id)
        except Exception as ex:
            response_obj.message = {"user_info": "创建租户失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 505
            return response_obj
        else:
            response_obj.content = project
            return response_obj

    def update_project(self, project_id, project_name=None, description=None, status=None):
        response_obj = ResponseObj()

        param_info = {}
        if project_name:
            param_info["name"] = project_name
        if description:
            param_info["description"] = description
        if status == "active":
            param_info["enabled"] = True
        elif status == "forbidden":
            param_info["enabled"] = False
        try:
            if param_info:
                project = self.openstack_client.update_project(
                    name_or_id=project_id,
                    domain_id="default", **param_info)
                response_obj.content = project
            else:
                response_obj.content = "无信息需更新！"
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.no = 500
            response_obj.message = {"user_info": "为项目更新失败!", "admin_info": ex}
        return response_obj

    def delete_project(self, project_id):
        response_obj = ResponseObj()
        try:
            project_delete_result = {}
            with transaction.atomic():
                # 项目删除
                bm_project_obj = auth_models.BmProject.objects.filter(id=project_id)
                bm_project_delete_obj = bm_project_obj.delete()
                project_delete_result["bm_project_delete_obj"] = bm_project_delete_obj

                #  删除项目成员
                mapping_user_project_obj = auth_models.BmMappingUserProject.objects.filter(project_id=project_id)
                mapping_user_project_delete_obj = mapping_user_project_obj.update(status="deleted")
                project_delete_result["mapping_user_project_delete_obj"] = mapping_user_project_delete_obj

                # openstack 项目删除
                param_info = {"name": "{project_id}-deleted".format(project_id=project_id)}
                open_delete_result = self.openstack_client.update_project(name_or_id=project_id, enabled=False,
                                                                          **param_info)
                project_delete_result["open_delete_result"] = open_delete_result

                response_obj.content = project_delete_result
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.no = 500
            response_obj.message = {"user_info": "openstack项目删除失败!", "admin_info": str(ex)}
        return response_obj

    def update_role_assignment(self, add_user_list, remove_user_list, project, role="_member_", domain="default"):
        response_obj = ResponseObj()
        try:
            content_list = []
            for user in remove_user_list:
                result = self.openstack_client.revoke_role(role, user=user, project=project, domain=domain)
                content_list.append(result)
                if not result:
                    raise Exception("fail ot delete user %s to project %s! Error: %s" % (user, project, result))
            for user in add_user_list:
                result = self.openstack_client.grant_role(role, user=user, project=project, domain=domain)
                content_list.append({user: result})
                if not result:
                    raise Exception("fail ot add user %s to project %s! Error: %s" % (user, project, result))

            response_obj.content = content_list
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.no = 500
            response_obj.message = {"user_info": "为项目更新成员role失败!", "admin_info": ex}
        return response_obj

    # def query_project_quotas(self, project_id):
    #     """
    #     Get compute quotas
    #     :param request: project id
    #     :return:
    #     """
    #     response_obj = ResponseObj()
    #     try:
    #         compute_quotas = self.openstack_client.get_compute_quotas(name_or_id=project_id)
    #         response_obj.content = compute_quotas
    #         response_obj.no = 200
    #         response_obj.is_ok = True
    #     except Exception as e:
    #         response_obj.message = {"user_info": "计算配额!", "admin_info": e}
    #         response_obj.is_ok = False
    #         response_obj.no = 500
    #         return response_obj
    #     return response_obj

    # 用户相关
    def create_user(self, name, password, email, default_project, description, domain_id="default"):
        """
        Create user in keystone
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            user = self.openstack_client.create_user(name=name, password=password, email=email,
                                                default_project=default_project, domain_id=domain_id,
                                                description=description)
            response_obj.content = user
            response_obj.no = 200
            response_obj.is_ok = True
        except Exception as e:
            response_obj.message = {"user_info": "创建用户失败!", "admin_info": e}
            response_obj.is_ok = False
            response_obj.no = 409
            return response_obj
        return response_obj

    def update_user(self, name_or_id, param_info):
        """
        Create user in keystone
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            # openstack user 参数转换
            user_platform_to_openstack = {"name": "account", "email": 'account', 'password': 'password',
                                          'description': 'description', 'default_project_id': 'default_project'}
            openstack_user_info = dict()
            for openstack_param, platform_param in user_platform_to_openstack.items():
                platform_value = param_info.get(platform_param)
                if platform_value:
                    openstack_user_info[openstack_param] = platform_value
            if param_info.get("status") == "active":
                openstack_user_info["enabled"] = True
            elif param_info.get("status") == "forbidden":
                openstack_user_info["enabled"] = False
            if openstack_user_info:
                user = self.openstack_client.update_user(name_or_id=name_or_id, **openstack_user_info)
                response_obj.content = user
        except Exception as ex:
            response_obj.message = {"user_info": "云平台用户更新失败!", "admin_info": str(ex)}
            if "You are not authorized" in str(ex):
                response_obj.message = {"user_info": "该用户无此权限!", "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 409
            return response_obj
        return response_obj

    def delete_user(self, account_id):
        """
        Create user in keystone
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            response_result = {}
            with transaction.atomic():
                # 用户删除
                user_delete_result = auth_models.BmUserInfo.objects.filter(id=account_id).delete()
                response_result["user_delete_result"] = user_delete_result

                # token 数据库更新
                user_token_delete_result = auth_models.BmUsertoken.objects.filter(account_id=account_id).delete()
                response_result["user_token_delete_result"] = user_token_delete_result

                #  删除项目成员
                mapping_user_project_obj = auth_models.BmMappingUserProject.objects.filter(account_id=account_id)
                mapping_user_delete_result = mapping_user_project_obj.update(status="deleted")
                response_result["mapping_user_delete_result"] = mapping_user_delete_result

                # openstack 项目删除
                # result = self.openstack_client.delete_user(name_or_id=id)
                open_delete_result = self.openstack_client.update_user(name_or_id=account_id,
                                                           **{"enabled": False, "name": "%s-deleted" % account_id})
                response_result["open_delete_result"] = open_delete_result
            response_obj.content = response_result
            response_obj.no = 200
            response_obj.is_ok = True
        except Exception as ex:
            response_obj.message = {"user_info": "云平台用户删除失败!", "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 505
            return response_obj
        return response_obj

    # 默认网络创建
    def create_network(self, project_id):
        """Create a network.

                :param string name: Name of the network being created.
                :param bool shared: Set the network as shared.
                :param bool admin_state_up: Set the network administrative state to up.
                :param bool external: Whether this network is externally accessible.
                :param dict provider: A dict of network provider options. Example::

                   { 'network_type': 'vlan', 'segmentation_id': 'vlan1' }
                :param string project_id: Specify the project ID this network
                    will be created on (admin-only).
                :param types.ListType availability_zone_hints: A list of availability
                    zone hints.
                :param bool port_security_enabled: Enable / Disable port security
                :param int mtu_size: maximum transmission unit value to address
                    fragmentation. Minimum value is 68 for IPv4, and 1280 for IPv6.

                :returns: The network object.
                :raises: OpenStackCloudException on operation error.
        """
        response_obj = ResponseObj()
        try:
            user = self.openstack_client.create_network(name="default", project_id=project_id)
            response_obj.content = user
            response_obj.no = 200
            response_obj.is_ok = True
        except Exception as e:
            response_obj.message = {"user_info": "创建网络失败!", "admin_info": e}
            response_obj.is_ok = False
            response_obj.no = 409
            return response_obj
        return response_obj

    def delete_network(self, project_id):
        """Delete a network.
        """
        response_obj = ResponseObj()
        try:
            user = self.openstack_client.create_network(name="default", project_id=project_id)
            response_obj.content = user
            response_obj.no = 200
            response_obj.is_ok = True
        except Exception as e:
            response_obj.message = {"user_info": "创建网络失败!", "admin_info": e}
            response_obj.is_ok = False
            response_obj.no = 409
            return response_obj
        return response_obj

    def create_subnet(self, network_id, project_id):
        response_obj = ResponseObj()
        try:
            user = self.openstack_client.create_subnet(network_name_or_id=network_id, cidr="192.168.0.0/24", subnet_name="default", tenant_id=project_id)
            response_obj.content = user
            response_obj.no = 200
            response_obj.is_ok = True
        except Exception as ex:
            response_obj.message = {"user_info": "创建子网失败!", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 409
            return response_obj
        return response_obj

    class OpenstackNova(object):

        def __init__(self, openstack_client=None):
            self.openstack_client = openstack_client

        def get_openstack_client_by_request(self, request):
            try:
                self.openstack_client = utils.get_openstack_client(request)
            except keystone_exceptions.NotFound:
                # Maybe token has expired,Get client use password
                self.openstack_client = utils.get_openstack_client(request, auth_plugin='password')
            return self.openstack_client

        def create_server(self, name, image_id, flavor, network_dict):
            image_id = "1e9b9e6b-de7f-48b9-8a0b-63b5a1582cc1"
            flavor = "92edc992-fcb6-4cb3-ae86-61996bd3f7b0"
            network_dict = {"id":"28bd6e78-4726-4f06-92e3-d6747d4ae1a3"}
            openstack_client = utils.get_openstack_client()
            server = openstack_client.create_server(name=name, image=image_id, flavor=flavor, network=network_dict)
            return server
