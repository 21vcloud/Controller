# Create your views here.
# -*- coding:utf-8 -*-

import logging

from keystoneauth1 import exceptions as keystone_exceptions

from BareMetalControllerBackend.conf.env import EnvConfig
from common.lark_common.model.common_model import ResponseObj
from common import exceptions as exc
from common import utils
from openstack import connection


config = EnvConfig()
LOG = logging.getLogger(__name__)


class OpenstackClientProvider(object):

    def __init__(self, openstack_client=None):
        self.openstack_client = openstack_client

    def get_openstack_client_by_request(self, request):
        try:
            self.openstack_client = utils.get_openstack_client(request)
        except keystone_exceptions.NotFound:
            # Maybe token has expired,Get client use password
            self.openstack_client = utils.get_openstack_client(request, auth_plugin='password')
        else:
            if not self.openstack_client:
                raise exc.SessionNotFound()

        return self.openstack_client

    def get_admin_openstack_client(self):
        admin_conn = connection.Connection(
            region_name=config.openstack_admin_region_name,
            auth=dict(
                auth_url=config.openstack_admin_auth_url,
                username=config.openstack_admin_username,
                password=config.openstack_admin_password,
                project_id=config.openstack_admin_project_id,
                user_domain_id=config.openstack_admin_user_domain_id
            ),
            compute_api_version=config.openstack_admin_compute_api_version,
            identity_interface=config.openstack_admin_identity_interface
        )
        return admin_conn

    def create_server(self, name, image_id, flavor, network):
        response_obj = ResponseObj()
        try:
            # openstack_client = utils.get_openstack_client()
            server = self.openstack_client.create_server(name=name, image=image_id, flavor=flavor, network=network)
        except Exception as ex:
            response_obj.message = ex
            response_obj.no = 500
            response_obj.is_ok = True
        return server



