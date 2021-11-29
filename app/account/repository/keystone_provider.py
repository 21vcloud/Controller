# Create your views here.
# -*- coding:utf-8 -*-

import logging

from keystoneauth1 import exceptions as keystone_exceptions
from openstack import exceptions as openstack_exceptions

from BareMetalControllerBackend.conf.env import EnvConfig
from common.lark_common.model.common_model import ResponseObj
from common.openstack import context

config = EnvConfig()
LOG = logging.getLogger(__name__)


class KeystoneAuth(object):

    def __init__(self):
        pass

    def get_session(self, request, username, password, project_name, project_domain_name="default", user_domain_name="default"):
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
        response_obj.content = auth_token
        response_obj.is_ok = True
        return response_obj

    def create_project(self, request, project_name, description, domain_id="default"):
        """
        Create an openstack project
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            openstack_client = context.get_openstack_client_from_session(request)
            project = openstack_client.create_project(name=project_name, description=description, domain_id=domain_id)
        except keystone_exceptions.NotFound as ex:
            # Maybe token has expired,Get client use password
            openstack_client = context.get_openstack_client_from_session(request, auth_plugin='password')
            project = openstack_client.create_project(name=project_name, description=description, domain_id=domain_id)
        except openstack_exceptions.ConflictException as ex:
            response_obj.message = {"user_info": "租户已经创建", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 409
            return response_obj
        except Exception as ex:
            response_obj.message = {"user_info": "创建租户失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj
        else:
            response_obj.content = project
            return response_obj


    def create_user(self, request):
        """
        Create user in keystone
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        openstack_client = context.get_openstack_client_from_session(request)
        name = request.data.get("name", )
        password = request.data.get("password")
        email = request.data.get("email")
        default_project = request.data.get("default_project")
        domain_id = request.data.get('domain_name') or 'default'
        description = request.data.get('description')
        try:
            user = openstack_client.create_user(name=name, password=password, email=email,
                                                default_project=default_project, domain_id=domain_id,
                                                description=description)
        except keystone_exceptions.NotFound as e:
            # Maybe token has expired,Get client use password
            openstack_client = context.get_openstack_client_from_session(request, auth_plugin='password')
            user = openstack_client.create_user(name=name, password=password, email=email,
                                                default_project=default_project, domain_id=domain_id,
                                                description=description)
        except openstack_client.ConflictException as ex:
            return response_obj.json_exception_serial("用户%s已经创建" % name, admin_info=str(ex), no=409)
        except Exception as e:
            return response_obj.json_exception_serial("用户%s创建失败", admin_info=str(e), no=409)
        return response_obj.json_serial(user)
