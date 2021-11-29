# Create your views here.
# -*- coding:utf-8 -*-

from drf_yasg.utils import swagger_auto_schema
import datetime
import ipaddress
import jsonpickle
import logging

from django.db import transaction
from django.http import HttpResponse
from keystoneauth1 import exceptions as keystone_exceptions
from openstack import exceptions as openstack_exceptions
from baremetal_service.repository.service_provider import ServiceCmdbProvider
from rest_framework.viewsets import ViewSet

from account.auth import utils as auth_utils
from account.repository import serializers as auth_serializers
from baremetal_audit.handler import send_cloud_audit_log_single_request, send_cloud_audit_log_multi_request, \
    send_cloud_log_notification
from baremetal_audit import audit_types
from baremetal_openstack.repository import serializers
from baremetal_openstack.repository.nova_provider import OpenstackClientProvider
from baremetal_openstack import handler
from baremetal_openstack.handler import ResouceProvider
from baremetal_service.repository import service_model
from baremetal_service.repository.service_model import Vpc, Firewalls, BmServiceMachine, BmServiceInstance, \
    BmServiceVolume
from baremetal_service.swift_handler import ObjectClientProvider
from BareMetalControllerBackend.conf.env import EnvConfig
from common.lark_common.model.common_model import ResponseObj
from common.lark_common.utils import AESCipher
from common.access_control.base import AccessSet
from common.openstack import context
from common import utils
from common import exceptions as common_exceptions
from common.access_control.base import check_element_permission

config = EnvConfig()
LOG = logging.getLogger(__name__)


class SessionViews(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()

    @swagger_auto_schema(request_body=serializers.SessionSerializer)
    @check_element_permission
    def get_session(self, request):
        """
        Return session
        :param request:
        :return: sessionId
        """
        response_obj = ResponseObj()
        username = request.data.get('username')
        password = request.data.get('password')
        project_name = request.data.get('project_name')
        project_domain_name = request.data.get('project_domain_name') or 'default'
        user_domain_name = request.data.get('user_domain_name') or 'default'

        try:
            cctext = context.RequestContext(auth_url=config.auth_url, username=username,
                                            password=password, project_name=project_name,
                                            project_domain_name=project_domain_name,
                                            user_domain_name=user_domain_name)

            request.session['token'] = cctext.auth_token
        except keystone_exceptions.Unauthorized as ex:
            response_obj.message = {"user_info": "认证失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 401
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            return HttpResponse(json_data, content_type="application/json")
        request.session['token'] = cctext.auth_token
        request.session["username"] = username
        request.session['password'] = password
        request.session['project_name'] = project_name
        request.session['project_domain_name'] = project_domain_name
        request.session['user_domain_name'] = user_domain_name
        request.session.set_expiry(config.session_timeout)
        response_obj.content = "Sucess get session"
        response_obj.is_ok = True
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter, request_body=serializers.ProjectSerializer)
    @check_element_permission
    @utils.param_info
    def create_project(self, request):
        """
        Create an openstack project
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        openstack_client = context.get_openstack_client_from_session(request)
        project_name = request.data.get("project_name", )
        domain_id = request.data.get("domain_name", 'default')
        try:
            project = openstack_client.create_project(name=project_name, domain_id=domain_id)
        except keystone_exceptions.NotFound as e:
            # Maybe token has expired,Get client use password
            openstack_client = context.get_openstack_client_from_session(request, auth_plugin='password')
            project = openstack_client.create_project(name=project_name, domain_id=domain_id)

        except openstack_exceptions.ConflictException as ex:
            response_obj.message = {"user_info": "租户已经创建", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 409
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            return HttpResponse(json_data, content_type="application/json")

        except Exception as ex:
            response_obj.message = {"user_info": "创建租户失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            return HttpResponse(json_data, content_type="application/json")
        else:
            return response_obj.json_serial(project)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         query_serializer=serializers.ListProjectSerializer)
    @check_element_permission
    @utils.param_info
    def list_projects(self, request):
        LOG.info("Request function:list_projects")
        LOG.info("Start to decrypt request param info!")
        response_obj = ResponseObj()
        param_info = request.GET

        openstack_client = context.get_openstack_client_from_session(request)
        domain_id = param_info.get("domain_name", 'default')
        try:
            projects = openstack_client.list_projects(domain_id=domain_id, filters=param_info)
        except Exception as ex:
            return response_obj.json_exception_serial("查看租户列表失败", admin_info=ex, no=500)
        else:
            return response_obj.json_serial(projects)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         request_body=serializers.DeleteProjectSerializer)
    @check_element_permission
    @utils.param_info
    def delete_project(self, request):
        LOG.info("Request function:delete_projects")
        LOG.info("Start to decrypt request param info!")
        response_obj = ResponseObj()

        openstack_client = context.get_openstack_client_from_session(request)
        name_or_id = request.data.get('project_name')
        domain_id = request.data.get('domain_name') or 'default'
        try:
            project = openstack_client.delete_project(name_or_id, domain_id=domain_id)
        except Exception as ex:
            LOG.error(ex)
            return response_obj.json_exception_serial("删除租户列表", admin_info=ex, no=500)
        else:
            return response_obj.json_serial(project)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         query_serializer=serializers.GetProjectSerializer)
    @check_element_permission
    @utils.param_info
    def get_project(self, request):
        LOG.info("Request function:get_project")
        response_obj = ResponseObj()
        param_info = request.GET
        openstack_client = context.get_openstack_client_from_session(request)
        domain_id = param_info.get("domain_name", 'default')
        project_name = param_info.get('project_name')
        try:
            project = openstack_client.get_project(project_name, domain_id=domain_id)
        except Exception as ex:
            return response_obj.json_exception_serial("获取租户失败", admin_info=ex, no=500)
        else:
            return response_obj.json_serial(project)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         request_body=serializers.UpdateProjectSerializer)
    @check_element_permission
    @utils.param_info
    def update_project(self, request):
        LOG.info("Request function:update_project")
        LOG.info("Request Body is %s " % request.data)
        response_obj = ResponseObj()
        openstack_client = context.get_openstack_client_from_session(request)
        name = request.data.get("project_name")
        domain_name = request.data.get("domain_name") or 'default'
        description = request.data.get("description")
        try:
            project = openstack_client.update_project(name_or_id=name, enabled=True,
                                                      domain_id=domain_name,
                                                      description=description)
        except Exception as ex:
            return response_obj.json_exception_serial("更新租户失败", admin_info=ex, no=500)
        else:
            return response_obj.json_serial(project)


class UserView(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter, request_body=serializers.UserSerializer)
    @check_element_permission
    @utils.param_info
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
            return response_obj.json_exception_serial("用户%s已经创建" % name, admin_info=ex, no=409)
        except Exception as e:
            return response_obj.json_exception_serial("用户%s创建失败", admin_info=e, no=409)
        return response_obj.json_serial(user)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         query_serializer=serializers.ListUserSerializer)
    @check_element_permission
    @utils.param_info
    def list_users(self, request):
        response_obj = ResponseObj()
        param_info = request.GET
        project_name = param_info.get("project_name")
        domain_name = param_info.get('domain_name') or 'default'
        openstack_client = utils.get_openstack_client(request)

        if not project_name:
            try:
                users = openstack_client.list_users()
            except keystone_exceptions.NotFound:
                # Maybe token has expired,Get client use password
                openstack_client = utils.get_openstack_client(request, auth_plugin='password')
                users = openstack_client.list_users()

            except Exception as e:
                return response_obj.json_exception_serial("查看用户列表失败", admin_info=e, no=500)
            return response_obj.json_serial(users)
        else:
            try:
                project = openstack_client.get_project(name_or_id=project_name, domain_id=domain_name)
                filters = {'project': project.id}
                role_assignments = openstack_client.list_role_assignments(filters=filters)
                user_ids = set()
                for assignment in role_assignments:
                    if hasattr(assignment, 'user'):
                        user_ids.add(assignment.user)
                data = []
                for user_id in user_ids:
                    user = openstack_client.get_user_by_id(user_id, normalize=False)
                    data.append(user)
                return response_obj.json_serial(data)
            except Exception as e:
                return response_obj.json_exception_serial("查看用户列表失败", admin_info=e, no=500)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         request_body=serializers.DeleteUserSerializer)
    @check_element_permission
    @utils.param_info
    def delete_user(self, request):
        response_obj = ResponseObj()
        user_name = request.data.get('user_name')
        openstack_client = utils.get_openstack_client(request)

        try:
            user = openstack_client.delete_user(user_name)
        except keystone_exceptions.NotFound:
            # Maybe token has expired,Get client use password
            openstack_client = utils.get_openstack_client(request, auth_plugin='password')
            user = openstack_client.delete_user(user_name)
        except Exception as e:
            LOG.error("Delete user %s error", user_name)
            return response_obj.json_exception_serial("删除用户%s失败" % user_name, admin_info=e, no=500)
        return response_obj.json_serial(user)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         query_serializer=serializers.DeleteUserSerializer)
    @check_element_permission
    def get_user(self, request):
        response_obj = ResponseObj()
        param_info = request.GET
        user_name = param_info.get('user_name')
        domain_name = param_info.get('domain_name') or 'default'
        openstack_client = utils.get_openstack_client(request)
        try:
            user = openstack_client.get_user(user_name)
        except Exception as e:
            LOG.error("get user %s error", user_name)
            return response_obj.json_exception_serial("查看用户%s失败" % user_name, admin_info=e, no=500)
        return response_obj.json_serial(user)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         request_body=serializers.UpdateUserSerializer)
    @check_element_permission
    @utils.param_info
    def update_user(self, request):
        response_obj = ResponseObj()
        kwargs = request.param_info
        user = kwargs.pop('origin_user')
        openstack_client = utils.get_openstack_client(request)
        try:
            user = openstack_client.update_user(user, **kwargs)
        except Exception as e:
            LOG.error("Update user %s error", kwargs)
            return response_obj.json_exception_serial("更新用户%s失败" % user, admin_info=e, no=500)
        return response_obj.json_serial(user)


class RoleAssignmentView(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         request_body=serializers.RoleAssignmentSerializer)
    @check_element_permission
    @utils.param_info
    def add_role_assignment(self, request):
        response_obj = ResponseObj()
        user = request.data.get('user')
        project = request.data.get('project')
        role = request.data.get('role', '_member_')
        domain = request.data.get('domain', 'default')
        openstack_client = utils.get_openstack_client(request)
        try:
            result = openstack_client.grant_role(role, user=user, project=project, domain=domain)
        except keystone_exceptions.NotFound:
            # Maybe token has expired,Get client use password
            openstack_client = utils.get_openstack_client(request, auth_plugin='password')
            result = openstack_client.grant_role(role, user=user, project=project, domain=domain)

        except Exception as e:
            return response_obj.json_exception_serial("为用户设置role失败", admin_info=e, no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(manual_parameters=serializers.SessionParameter,
                         request_body=serializers.RoleAssignmentSerializer)
    @check_element_permission
    @utils.param_info
    def remove_role_assignment(self, request):
        response_obj = ResponseObj()
        user = request.data.get('user')
        project = request.data.get('project')
        role = request.data.get('role', '_member_')
        domain = request.data.get('domain', 'default')
        openstack_client = utils.get_openstack_client(request)
        try:
            result = openstack_client.revoke_role(role, user=user, project=project, domain=domain)
        except keystone_exceptions.NotFound:
            # Maybe token has expired,Get client use password
            openstack_client = utils.get_openstack_client(request, auth_plugin='password')
            result = openstack_client.revoke_role(role, user=user, project=project, domain=domain)

        except Exception as e:
            return response_obj.json_exception_serial("为用户删除role失败", admin_info=e, no=500)
        return response_obj.json_serial(result)


class InstanceViews(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.instance_provider = OpenstackClientProvider()
        self.env_config = EnvConfig()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.cmdb_provider = ServiceCmdbProvider()

    @swagger_auto_schema(request_body=serializers.InstanceInterfaceAttachSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                         trace_name=audit_types.INTERFACT_ATTACH, resource_id_key='uuid',
                                         resource_name_key='name')
    def instance_attach_interface(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        net_id = param_info.get("net_id")
        try:
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            result = handler.interface_attach(openstack_client, server_id, net_id)
            instance_info = service_model.BmServiceInstance.objects.filter(uuid=server_id).first()
            if instance_info:
                result = instance_info.__dict__
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="服务器添加网络接口失败！",
                                                      admin_info=str(ex), no=300)
        # 进行数据得同步
        cmdb_result = self.cmdb_provider.cmdb_data_sys_put2(instance_uuid=server_id, status="connect")
        self.logger.info("The instance attach_interface sys Result : %s " % cmdb_result)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.InstanceInterfaceDetachSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                         trace_name=audit_types.INTERFACE_DETACH, resource_id_key='uuid',
                                         resource_name_key='name')
    def instance_detach_interface(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        port_ids = param_info.get("port_ids")
        result = None
        floatingips = service_model.BmServiceFloatingIp.objects.filter(instance_uuid=server_id, is_measure_end=False)
        # 判断当前实例有没有加入到资源池当中
        pool_mapping_result = service_model.BmInstanceMemberMapping.objects.filter(instance_id=server_id)
        if pool_mapping_result:
            loadbalance_name_list = []
            for pool_mapping_result_detail in pool_mapping_result:
                loadbancer_id = pool_mapping_result_detail.loadbancer_id
                lb_result = service_model.BmServiceLoadbalance.objects.filter(
                    loadbalance_id=loadbancer_id).first()
                loadbalance_name = lb_result.loadbalance_name
                if loadbalance_name not in loadbalance_name_list:
                    loadbalance_name_list.append(loadbalance_name)
            return response_obj.json_exception_serial(user_info="该裸金属实例正在被{loadbalance_name_list}使用，"
                                                                "请先将实例从负载均衡实例中移除，再分离网络".
                                                      format(loadbalance_name_list=loadbalance_name_list),
                                                      admin_info="被负载均衡使用，无法分离网络", no=409)
        if floatingips.count() > 0:
            return response_obj.json_exception_serial(user_info="请手动解绑公网ip", admin_info="Floatingip conflict", no=409)
        try:
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            for port_id in port_ids:
                handler.interface_detach_single(openstack_client, server_id, port_id)

            instance_info = service_model.BmServiceInstance.objects.filter(uuid=server_id).first()
            if instance_info:
                result = instance_info.__dict__
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="服务器网络接口分离失败！",
                                                      admin_info=str(ex), no=300)
        # 进行数据得同步
        cmdb_result = self.cmdb_provider.cmdb_data_sys_put2(instance_uuid=server_id, status="disconnect")
        self.logger.info("The instance detach_interface sys Result : %s " % cmdb_result)
        return response_obj.json_serial(result)

    @swagger_auto_schema(query_serializer=serializers.InstanceIdSerializer)
    @check_element_permission
    @utils.param_info
    def instance_list_interface(self, request):
        response_obj = ResponseObj()
        LOG.info("get server serial console")
        server_id = request.param_info.get("server_id")
        result = []
        try:
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            attachemtns = handler.interface_list(openstack_client, server_id)
            for interface in attachemtns:
                result.append(interface.to_dict())
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取服务器网络接口列表失败",
                                                      admin_info=str(ex), no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.InstanceCreateSerializer)
    @check_element_permission
    @utils.param_info
    def instance_create(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        name = param_info.get("name")
        image = param_info.get("image")
        flavor = param_info.get("flavor")
        network_dict = param_info.get("network_dict")
        try:
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            result = openstack_client.create_server(
                name=name, image=image, flavor=flavor, network=network_dict
            )

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="服务器创建失败！", admin_info=ex, no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.InstanceStopSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                         trace_name=audit_types.STOP, resource_id_key='uuid',
                                         resource_name_key='name')
    def instance_stop(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        result = None
        try:
            instance_info = service_model.BmServiceInstance.objects.filter(uuid=server_id).first()
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            openstack_client.compute.stop_server(server=server_id)
            bm_machine = BmServiceMachine.objects.filter(uuid=server_id).first()
            if bm_machine:
                bm_machine.status = handler.SHUTOFF
                bm_machine.save()
            instance_obj = BmServiceInstance.objects.filter(uuid=server_id).first()
            if instance_obj:
                instance_obj.status = handler.SHUTOFF
                instance_obj.save()
            # 进行数据得同步
            cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=server_id,
                                                               status="power off")
            self.logger.info("The instance stop sys Result : %s " % cmdb_result)
            if instance_info:
                result = instance_info.__dict__
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="服务器关机失败！",
                                                      admin_info=str(ex), no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.InstanceStartSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                         trace_name=audit_types.START, resource_id_key='uuid',
                                         resource_name_key='name')
    def instance_start(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        result = None
        try:
            instance_info = service_model.BmServiceInstance.objects.filter(uuid=server_id).first()
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            instance_obj = BmServiceInstance.objects.filter(uuid=server_id).first()
            if instance_obj:
                instance_obj.status = 'active'
                instance_obj.save()
            result = openstack_client.compute.start_server(server=server_id)
            # 进行数据得同步
            cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=server_id,
                                                               status="power on")
            self.logger.info("The instance start sys Result : %s " % cmdb_result)

            if instance_info:
                result = instance_info.__dict__
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="服务器开机失败！", admin_info=ex, no=300)
        return response_obj.json_serial(result)

    @utils.param_info
    def instance_list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        servers = []
        try:
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            instances = openstack_client.compute.servers(details=True, tags=config.baremetal_tag)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取服务器列表失败", admin_info=str(ex), no=300)
        bm_instances_query = handler.get_bm_instances(project_id=project_id)
        flavor_dict = handler.get_flavor_info()
        image_dict = handler.get_image_info()
        for instance in instances:
            instance.flavor['flavor_info'] = flavor_dict.get(instance.flavor.get('original_name'))
            image_info = image_dict.get(instance.image.get('id'))
            instance.image['name'] = image_info.get("name")
            instance.image['openstack_image_name'] = image_info.get("openstack_image_name")
            bm = handler.reserial_instance(instance, bm_instances_query)
            if bm:
                servers.append(bm)
        data = {"servers": servers}
        return response_obj.json_serial(data)

    @swagger_auto_schema(query_serializer=serializers.BalancersPoolIdSerializer)
    @utils.param_info
    def instance_list_not_in_slb_pool(self, request):
        """
        获取不在该负载均衡,后端资源组的服务器列表
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        LOG.info("get not in slb pool servers ")
        project_id = request.session.get('project_id')
        pool_id = request.param_info.get('pool_id')
        servers = []
        try:
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            # 负载均衡下,
            pool_member_list = openstack_client.load_balancer.members(pool_id, project_id=project_id)
            pool_fixed_ip_list = [u.address for u in pool_member_list]
            instances = openstack_client.compute.servers(details=True, tags=config.baremetal_tag)
            bm_instances_query = handler.get_bm_instances(project_id=project_id)
            instance_uuid_mappings = {}
            for instance in instances:
                # 判断是否在后端资源组中
                is_in_pool = handler.check_instance_in_pool(instance, pool_fixed_ip_list)
                if is_in_pool:
                    continue
                bm = handler.reserial_instance(instance, bm_instances_query)
                if bm:
                    instance_uuid_mappings[bm["id"]] = bm

            # 查询当前pool所对应的lb
            pool_detail = openstack_client.load_balancer.get_pool(pool_id).to_dict()
            loadbalance_id_list = pool_detail['loadbalancers']
            for loadbalance_id_obj in loadbalance_id_list:
                loadbalance_id = loadbalance_id_obj["id"]
                loadbalance_result = service_model.BmServiceLoadbalance.objects.filter(
                    loadbalance_id=loadbalance_id).first()
                network_id_list = []
                if loadbalance_result:
                    vpc_id = loadbalance_result.vpc_id
                    network_result = service_model.BmNetworks.objects.filter(vpc_id=vpc_id)
                    if network_result:
                        for network_detail in network_result:
                            network_id_list.append(network_detail.network_id)
                    # 筛选instance对应的network_id
                    filters = {'device_owner': "compute:nova", }
                    ports = openstack_client.list_ports(filters=filters)
                    if not ports:
                        continue
                    # 如果不在当前负载均衡对应VPC的网络下，则过滤。
                    server_host_id_list = []
                    for ports_detail in ports:
                        if ports_detail.network_id in network_id_list:
                            server = instance_uuid_mappings.get(ports_detail.get('device_id'))
                            if server:
                                if server["id"] not in server_host_id_list:
                                    server_host_id_list.append(server["id"])
                                    servers.append(server)
            data = {"servers": servers}
        except Exception as ex:
            LOG.error("get os active error %s", str(ex))
            return response_obj.json_exception_serial(user_info="获取不属于该资源池的服务器列表失败",
                                                      admin_info=str(ex),
                                                      no=300)
        return response_obj.json_serial(data)

    @swagger_auto_schema(request_body=serializers.InstanceRestartSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                         trace_name=audit_types.REBOOT, resource_id_key='uuid',
                                         resource_name_key='name')
    def instance_restart(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        result = None
        try:
            instance_info = service_model.BmServiceInstance.objects.filter(uuid=server_id).first()
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            openstack_client.compute.reboot_server(server=server_id, reboot_type="HARD")
            # 进行数据得同步
            cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=server_id,
                                                               status="power on")
            self.logger.info("The instance restart sys Result : %s " % cmdb_result)
            if instance_info:
                result = instance_info.__dict__
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="服务器重启失败！", admin_info=ex, no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.InstanceDeleteSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_multi_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                        trace_name=audit_types.DELETE, resource_id_key='uuid', resource_name_key='name')
    def instance_delete(self, request):
        response_obj = ResponseObj()

        # 判断是否有值
        server_id_list = request.param_info.get("server_id_list")
        if not server_id_list:
            return response_obj

        try:
            has_volume_servers = []
            for server_id in server_id_list:
                volume_instance_mapping = BmServiceVolume.objects.filter(is_measure_end=False,
                                                                         instance_uuid=server_id).first()
                if volume_instance_mapping:
                    server_dict = {"server_name": volume_instance_mapping.instance_name,
                                   "server_id": server_id}
                    has_volume_servers.append(server_dict)
                instance_dict = BmServiceMachine.objects.filter(uuid=server_id).first()
                server_name = ""
                if instance_dict:
                    server_name = instance_dict.service_name
                pool_mapping_result = service_model.BmInstanceMemberMapping.objects.filter(instance_id=server_id)
                if pool_mapping_result:
                    loadbalance_name_list = []
                    for pool_mapping_result_detail in pool_mapping_result:
                        loadbancer_id = pool_mapping_result_detail.loadbancer_id
                        lb_result = service_model.BmServiceLoadbalance.objects.filter(
                            loadbalance_id=loadbancer_id).first()
                        loadbalance_name = lb_result.loadbalance_name
                        if loadbalance_name not in loadbalance_name_list:
                            loadbalance_name_list.append(loadbalance_name)
                    return response_obj.json_exception_serial(user_info="{server_name}正在被{loadbalance_name_list}使用，"
                                                                        "请先将实例从负载均衡实例中移除，再进行删除".
                                                              format(server_name=server_name,
                                                                     loadbalance_name_list=loadbalance_name_list),
                                                              admin_info="被负载均衡使用，无法删除", no=409)
            if has_volume_servers:
                return response_obj.json_exception_serial(user_info="挂载了云硬盘的实例无法被删除,请手动卸载",
                                                          admin_info="%s" % has_volume_servers,
                                                          no=500)

            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            delete_result = handler.soft_delete_instance(openstack_client, server_id_list,
                                                         cmdb_provider=self.cmdb_provider)
            self.logger.info("The instance delete sys Result : %s " % delete_result)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除服务器失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(delete_result)

    @swagger_auto_schema(query_serializer=serializers.InstanceIdSerializer)
    @check_element_permission
    @utils.param_info
    def get_server_serial_console(self, request):
        response_obj = ResponseObj()
        LOG.info("get server serial console")
        server_id = request.param_info.get("server_id")
        region = request.session.get('region', self.env_config.region_name)
        project_id = request.session.get('project_id')
        user_id = request.session.get("account_id")

        try:

            LOG.info("get admin openstack client :")
            admin_client = self.instance_provider.get_admin_openstack_client()

            # 获取 node 信息
            LOG.info("get baremetal node info by server id %s" % server_id)
            instance_obj = admin_client.baremetal.nodes(**{"instance_id": server_id})
            instance_list = list(instance_obj)
            if not instance_list:
                raise Exception("Fail to find node by server id %s " % server_id)
            LOG.info("get baremetal node info result %s" % instance_list)

            # 设置 node console 为 True
            node_id = instance_list[0].id
            LOG.info("set baremetal node  console state True by node id %s" % node_id)
            console_obj = admin_client.baremetal.set_node_console_state(node=node_id, enabled=True)
            # console_obj = admin_client.baremetal.set_node_console_state(node=node_id, enabled=True)
            # console_state_result = admin_client.baremetal.wait_for_nodes_provision_state(nodes=[node_id], expected_state=True)
            if console_obj:
                raise Exception("Fail to set node console state to True!")
            LOG.info("set baremetal node  console state result %s" % console_obj)

            # 获取serial console url
            openstack_client = self.instance_provider.get_openstack_client_by_request(request=request)
            console_result = openstack_client.compute.get_server_serial_console(server=server_id)
            LOG.info("get console url result %s" % console_result)

            instance_info = service_model.BmServiceInstance.objects.filter(uuid=server_id).first()
            if instance_info:
                send_cloud_log_notification(region=region, project_id=project_id, user_id=user_id,
                                            service_type=audit_types.ECBM, resource_id=server_id,
                                            resource_name=instance_info.name, resource_type=audit_types.ECBM,
                                            contract_number=instance_info.contract_number, trace_name=audit_types.VNC,
                                            source_ip=None, request=console_result, response=None)
        except Exception as ex:
            LOG.error("get console url result Error : %s" % str(ex))
            return response_obj.json_exception_serial(user_info="获取console失败！", admin_info=str(ex), no=300)
        return response_obj.json_serial(console_result)

    @utils.param_info
    def get_instance_ports(self, request):
        """
        Get all instance port by project
        if server_id is specified, then return the instance ports
        :param request:
        :return: Ports dict
        """
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        server_id = request.param_info.get('server_id', )
        try:
            LOG.info("get instances ports with instance %s", server_id)
            admin_client = self.instance_provider.get_admin_openstack_client()
            filters = {'device_owner': "compute:nova", "project_id": project_id}
            if server_id:
                filters['device_id'] = server_id
            ports = admin_client.list_ports(filters=filters)
        except Exception as ex:
            LOG.error("Cann't instances ports")
            return response_obj.json_exception_serial(user_info="获取机器的端口失败",
                                                      admin_info=str(ex),
                                                      no=300)
        return response_obj.json_serial(ports)

    @utils.param_info
    def instance_list_by_os_active(self, request):
        response_obj = ResponseObj()
        LOG.info("get os active servers ")
        project_id = request.session.get('project_id')
        try:
            servers = []
            instance_objects = BmServiceInstance.objects.filter(project_id=project_id, deleted=False)
            for in_object in instance_objects:
                machine = BmServiceMachine.objects.values('service_name').filter(uuid=in_object.uuid,
                                                                                 status='active').first()
                if machine:
                    machine_dict = {'server_id': in_object.uuid,
                                    'server_name': machine['service_name']}
                    servers.append(machine_dict)
        except Exception as ex:
            LOG.error("get os active error %s", str(ex))
            return response_obj.json_exception_serial(user_info="获取可以挂在云硬盘的机器失败",
                                                      admin_info=str(ex),
                                                      no=300)
        return response_obj.json_serial(servers)


class NeutronViews(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()

    @swagger_auto_schema(request_body=serializers.CreateVpcSerializer)
    @check_element_permission
    @utils.param_info
    @utils.check_invalid_kwargs_with_normal_user('project_id')
    @send_cloud_audit_log_single_request(service_type=audit_types.VPC, trace_name=audit_types.CREATE,
                                         resource_type=audit_types.VPC, resource_id_key='id',
                                         resource_name_key='vpc_name')
    def create_vpc(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        region = param_info.get("region", "regionOne")
        vpc_type = param_info.get("vpc_type")
        vpc_name = param_info.get("vpc_name")
        net_name = param_info.get("net_name")
        cidr = param_info.get("cidr")
        enable_dhcp = param_info.get("enable_dhcp", True)
        gateway_ip = param_info.get("gateway_ip")
        dns = param_info.get("dns")
        # TODO 项目信息
        project_id = param_info.get("project_id")
        try:
            if not self.validate_gateway(cidr, gateway_ip):
                return response_obj.json_exception_serial(user_info="网关地址错误，请重新填写",
                                                          admin_info="Error gateway",
                                                          no=500)

            vpc = handler.create_vpc(request, region=region, vpc_type=vpc_type,
                                     project_id=project_id, vpc_name=vpc_name,
                                     net_name=net_name, cidr=cidr, enable_dhcp=enable_dhcp,
                                     gateway_ip=gateway_ip, dns=dns)
        except openstack_exceptions.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='虚拟私有云超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(user_info="VPC创建失败",
                                                          admin_info=str(e),
                                                          no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="VPC创建失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(vpc)

    @swagger_auto_schema()
    @check_element_permission
    @utils.param_info
    @utils.check_invalid_kwargs_with_normal_user('project_id')
    def list_vpcs(self, request):
        response_obj = ResponseObj()

        project_id = request.session.get("project_id")

        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            openstack_networks = openstack_client.list_networks(filters={"shared": False, "router:external": False})
            vpcs = handler.reserial_vpcs(project_id, openstack_networks)

        except Exception as e:
            return response_obj.json_exception_serial("查看VPC列表失败", admin_info=str(e), no=500)
        return response_obj.json_serial({"vpcs": vpcs})

    @swagger_auto_schema(request_body=serializers.UpdateVpcSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.VPC, trace_name=audit_types.UPDATE,
                                         resource_type=audit_types.VPC, resource_id_key='id',
                                         resource_name_key='vpc_name')
    def update_vpc(self, request):
        response_obj = ResponseObj()

        vpc_id = request.param_info.get("vpc_id")
        name = request.param_info.get("name")

        try:
            with transaction.atomic():
                vpc = Vpc.objects.get(id=int(vpc_id))
                openstack_client = self.openstack_provider.get_openstack_client_by_request(
                    request=request)

                openstack_client.update_router(vpc.router_id, name=name)
                vpc.vpc_name = name
                vpc.update_at = datetime.datetime.now()
                vpc.save()
        except Exception as e:
            return response_obj.json_exception_serial("更新VPC失败", admin_info=str(e), no=500)
        return response_obj.json_serial(vpc)

    @swagger_auto_schema(request_body=serializers.DleleteVpcSerializer)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_multi_request(service_type=audit_types.VPC, trace_name=audit_types.DELETE,
                                        resource_id_key='id', resource_name_key='vpc_name',
                                        resource_type=audit_types.VPC)
    def delete_vpc(self, request):
        project_id = request.session.get("project_id")
        response_obj = ResponseObj()
        vpc_ids = request.param_info.get("vpc_ids")
        vpcs = []

        try:
            for vpc_id in vpc_ids:
                nat_gateways = service_model.BmServiceNatGateway.objects.filter(vpc_id=vpc_id,
                                                                                is_measure_end=False).all()

                if nat_gateways:
                    return response_obj.json_exception_serial("VPC下有NAT网关，先删除NAT网关",
                                                              admin_info="Vpc has nat gateway",
                                                              no=500)
                vpc_networks = Vpc.objects.get(id=int(vpc_id), project_id=project_id)
                networks = vpc_networks.networks_set.all()

                if len(networks) > 0:
                    return response_obj.json_exception_serial("VPC 下有网络，先删除所有网络",
                                                              admin_info='Vpc has network',
                                                              no=500)
                else:
                    vpc = handler.delete_vpc(request, vpc_id)
                    vpcs.append(vpc)
        except Exception as e:
            return response_obj.json_exception_serial("删除VPC失败", admin_info=str(e), no=500)
        return response_obj.json_serial(vpcs)

    @swagger_auto_schema(query_serializer=serializers.ListVpcNetworks)
    @check_element_permission
    @utils.param_info
    def list_networks_by_vpc(self, request):
        response_obj = ResponseObj()
        vpc_id = request.param_info.get("vpc_id")

        try:
            vpc_object = Vpc.objects.get(id=int(vpc_id))
            vpc = vpc_object.to_dict()
            networks = []
            network_objects = vpc_object.networks_set.all()
            for net in network_objects:
                networks.append(net.to_dict())
            vpc['networks'] = networks
        except Exception as e:
            return response_obj.json_exception_serial("获取VPC下网络失败",
                                                      admin_info=str(e), no=500)
        return response_obj.json_serial(vpc)

    # @swagger_auto_schema(query_serializer=serializers.ListVpcNetworks)
    # @utils.param_info
    def list_networks_by_vpc_rest(self, request, pk):
        response_obj = ResponseObj()
        # vpc_id = request.param_info.get("vpc_id")
        vpc_id = pk

        vpc_network_ids = Vpc.objects.values('networks__network_id').filter(id=int(vpc_id))
        network_ids = [net.get('networks__network_id') for net in vpc_network_ids]
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(
                request=request)
            networks = openstack_client.list_networks(filters={'id': network_ids})
        except Exception as e:
            return response_obj.json_exception_serial("获取网络失败",
                                                      admin_info=str(e),
                                                      no=500)
        return response_obj.json_serial(networks)

    def validate_gateway(self, cidr, gateway_ip=None):
        net_cidr = ipaddress.ip_network(cidr)
        broadcast_and_network_address = (str(net_cidr.broadcast_address), str(net_cidr.network_address))
        if gateway_ip and gateway_ip in broadcast_and_network_address:
            return False
        return True

    @swagger_auto_schema(request_body=serializers.AddVpcNetwork)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.VPC, resource_type=audit_types.NETWORK,
                                         trace_name=audit_types.CREATE, resource_id_key='network_id',
                                         resource_name_key='name')
    def add_network_by_vpc(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        vpc_id = param_info.get('vpc_id')
        net_name = param_info.get("net_name")
        cidr = param_info.get("cidr")
        enable_dhcp = param_info.get("enable_dhcp", True)
        gateway_ip = param_info.get("gateway_ip")
        dns = param_info.get("dns")

        # 获取已有的cidrs
        try:
            exist_cidrs = handler.get_vpc_net_cidrs(vpc_id)
            # 校验是否cidr有重复
            if exist_cidrs:
                net_cidr = ipaddress.ip_network(cidr)
                for exist_cidr in exist_cidrs:
                    if net_cidr.overlaps(ipaddress.ip_network(exist_cidr)):
                        return response_obj.json_exception_serial(user_info="网段地址重叠，选择其他网段",
                                                                  admin_info="ovelap cidrs",
                                                                  no=409)
                # 校验网络地址和broadcast
            if not self.validate_gateway(cidr, gateway_ip):
                return response_obj.json_exception_serial(user_info="网关地址错误，请重新填写",
                                                          admin_info="Error gateway",
                                                          no=500)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="网络创建失败", admin_info=str(ex),
                                                      no=500)

        try:
            vpc = Vpc.objects.get(id=int(vpc_id))
            network = handler.create_network(request, vpc_id=vpc_id, name=net_name,
                                             cidr=cidr, enable_dhcp=enable_dhcp,
                                             gateway_ip=gateway_ip, dns=dns,
                                             router_id=vpc.router_id)
        except openstack_exceptions.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='网络超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(user_info="网络创建失败",
                                                          admin_info=str(e),
                                                          no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="网络创建失败", admin_info=ex, no=300)
        return response_obj.json_serial(network)

    @swagger_auto_schema(request_body=serializers.UpdateVpcNetwork)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.VPC, resource_type=audit_types.NETWORK,
                                         trace_name=audit_types.UPDATE, resource_id_key='network_id',
                                         resource_name_key='name')
    def update_network_by_vpc(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        vpc_id = param_info.get('vpc_id')
        network_id = param_info.get('net_id')
        net_name = param_info.get("net_name")
        dns = param_info.get("dns")
        enabled_dhcp = param_info.get("enable_dhcp")

        try:
            vpc = Vpc.objects.get(id=int(vpc_id))
            network = handler.update_vpc_network(request, network_id, network_name=net_name,
                                                 enalbe_dhcp=enabled_dhcp, dns=dns)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="更新VPC网络失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(network)

    @swagger_auto_schema(request_body=serializers.DeleteVpcNetwork)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.VPC, resource_type=audit_types.NETWORK,
                                         trace_name=audit_types.DELETE, resource_id_key='network_id',
                                         resource_name_key='name')
    def delete_network_by_vpc(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        vpc_id = param_info.get('vpc_id')
        network_id = param_info.get('net_id')

        try:
            net_info = handler.delete_vpc_network(request, network_id, vpc_id)
        except common_exceptions.NetworkInUse as e:
            return response_obj.json_exception_serial(user_info="网络正在使用中，请先删除资源",
                                                      admin_info=str(e),
                                                      no=409)
        except openstack_exceptions.ConflictException as e:
            return response_obj.json_exception_serial(user_info="有公网ip绑定在该网络上，请先解绑公网ip",
                                                      admin_info=str(e),
                                                      no=300)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除VPC网络失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(net_info)


class KeyPairViews(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()

    @swagger_auto_schema(request_body=serializers.KeypairCreate)
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, trace_name=audit_types.CREATE,
                                         resource_name_key='name', resource_id_key='id',
                                         resource_type=audit_types.KEYPAIR)
    def keypair_create(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        name = param_info.get('name')
        public_key = param_info.get('public_key')
        LOG.info("Create keypair %s with public_key: %s", name, public_key)
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
            keypair = openstack_client.create_keypair(name=name, public_key=public_key)
            LOG.info("Keypair %s create success with %s", name, keypair)
        except openstack_exceptions.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='秘钥对超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info="公钥校验失败",
                    admin_info=str(e),
                    no=500,
                )
        except Exception as e:
            return response_obj.json_exception_serial(user_info='创建秘钥对失败', admin_info=str(e), no=500)
        return response_obj.json_serial(keypair)

    @utils.param_info
    def keypair_list(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
            keypairs = openstack_client.list_keypairs()
        except Exception as e:
            return response_obj.json_exception_serial(user_info='查看秘钥对失败', admin_info=str(e), no=500)
        return response_obj.json_serial(keypairs)

    @swagger_auto_schema(request_body=serializers.KeypairDelete)
    @check_element_permission
    @utils.param_info
    def keypair_delete(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        region = request.session.get('region', 'regionOne')
        project_id = request.session.get('project_id')
        account_id = request.session.get('account_id')
        keypair_name_list = param_info.get('keypair_name_list')
        LOG.info("Keypair %s will be deleted" % keypair_name_list)
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
            keypair_delete_result = []
            for keypair_name in keypair_name_list:
                keypair = openstack_client.delete_keypair(name=keypair_name)
                keypair_delete_result.append({keypair_name: keypair})
                LOG.info("Keypair %s delete success", keypair_name)
                send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                            service_type=audit_types.ECBM, resource_id=keypair_name,
                                            resource_name=keypair_name, resource_type=audit_types.KEYPAIR,
                                            trace_name=audit_types.DELETE, request=request.param_info,
                                            response=keypair_delete_result
                                            )

            LOG.info("Keypair delete result: %s!" % keypair_delete_result)
        except Exception as e:
            LOG.error("keypair delete error : Ex %s" % str(e))
            return response_obj.json_exception_serial(user_info='删除秘钥对失败', admin_info=str(e), no=500)
        return response_obj.json_serial(keypair_delete_result)


class ResourceCountViews(ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.resource_provider = ResouceProvider()
        self.instance_provider = OpenstackClientProvider()

    @utils.param_info
    def query_all_resource_count(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get("project_id")

        LOG.info("query resource by project id %s " % project_id)

        email = request.session.get("username")
        access_set_obj = AccessSet()
        permission_list = access_set_obj.get_main_sidebar(email, project_id)
        print(permission_list)

        try:
            resource_count = []

            # 查询实例 数量
            if 'instance' in permission_list:
                LOG.info("query instance count by project id %s " % project_id)
                instacne_count = self.resource_provider.get_instance_count(project_id)
                LOG.info("instance count result %s " % instacne_count)
                # resource_count["instance_all_count"] = instacne_count.get("all_count")
                # resource_count["instance_active_count"] = instacne_count.get("active_count")
                resource_count.append({"instance_all_count": instacne_count.get("all_count")})
                resource_count.append({"instance_active_count": instacne_count.get("active_count")})

            # 查询VPC 数量
            if 'VPC' in permission_list:
                LOG.info("query vpc count by project id %s " % project_id)
                vpc_count = self.resource_provider.get_vpc_count(project_id)
                # resource_count["vpc_count"] = vpc_count
                resource_count.append({"vpc_count": vpc_count})
                LOG.info("query vpc result %s " % vpc_count)

            openstack_client = self.instance_provider.get_openstack_client_by_request(request)
            # 查询密钥对数量
            if 'keyPairManage' in permission_list:
                LOG.info("query key/value pair count by project id %s " % project_id)
                keypairs_count = openstack_client.list_keypairs()
                # resource_count["keypairs_count"] = len(keypairs_count)
                resource_count.append({"keypairs_count": len(keypairs_count)})
                LOG.info("query key/value pair count result %s " % keypairs_count)

            # 查询floating ip count
            if 'publicIP' in permission_list:
                LOG.info("query floating ip count by project id %s " % project_id)
                floating_ip_list = openstack_client.list_floating_ips(filters={"project_id": project_id})
                # resource_count["floating_ip_count"] = len(floating_ip_list)
                resource_count.append({"floating_ip_count": len(floating_ip_list)})
                LOG.info("query floating ip count result %s " % floating_ip_list)

            # 查询防火墙
            if 'fireWall' in permission_list:
                LOG.info("query firewall count by project id %s " % project_id)
                firewall_count = self.resource_provider.get_firewall_count(project_id=project_id)
                # resource_count["firewall_count"] = firewall_count
                resource_count.append({"firewall_count": firewall_count})
                LOG.info("query firewall count result %s " % firewall_count)

            # 查询磁盘
            if 'cloudDrive' in permission_list:
                LOG.info("query volume count by project id %s " % project_id)
                volume_count = self.resource_provider.get_volum_count(project_id=project_id)
                # resource_count["volume_count"] = volume_count
                resource_count.append({"volume_count": volume_count})
                LOG.info("query volume count result %s " % volume_count)

            # 查询备份
            if 'OSBackup' in permission_list:
                LOG.info("query volume backup count by project id %s " % project_id)
                volume_backup_count = self.resource_provider.get_volum_backup_count(project_id=project_id)
                # resource_count["volume_backup_count"] = volume_backup_count
                resource_count.append({"volume_backup_count": volume_backup_count})
                LOG.info("query volume backup count result %s " % volume_backup_count)

            # 查询对象存储
            if 'objectStorage' in permission_list:
                LOG.info("query object count by project id %s" % project_id)
                swift_client = ObjectClientProvider(request)
                headers, containers = swift_client.swift_client.get_account(full_listing=True)
                # resource_count["object_count"] = len(containers)
                resource_count.append({"object_count": len(containers)})

            # 查询负载均衡
            if 'loadBalance' in permission_list:
                LOG.info("query object count by project id %s" % project_id)
                loadbalance_count = self.resource_provider.get_loadbalance_count(project_id=project_id)
                resource_count.append({"loadbalance_count": loadbalance_count})
                LOG.info("query loadbalance count result %s " % loadbalance_count)

            # 查询nat网关个数
            if 'NAT' in permission_list:
                LOG.info("query Nat count by project id %s" % project_id)
                nat_count = service_model.BmServiceNatGateway.objects.filter(project_id=project_id,
                                                                             is_measure_end=False).count()
                resource_count.append({"nat_count": nat_count})

            # 查询共享带宽实例个数
            if 'BindWidth' in permission_list:
                LOG.info("query Nat count by project id %s" % project_id)
                bandwidth_used_count = service_model.BmShareBandWidth.objects.filter(project_id=project_id,
                                                                                     is_measure_end=False).count()
                resource_count.append({"shared_bandwidth_count": bandwidth_used_count})

            # 查询操作日志，操作日志没有个数
            if 'oplog' in permission_list:
                LOG.info("query op log by project id")
                resource_count.append({"oplog":0})

        except Exception as ex:
            return response_obj.json_exception_serial(user_info='查询资源列表失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(resource_count)


class FirewallViews(ViewSet):

    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.firewall_provider = handler.FirewallProvider()
        self.logger = LOG

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter)
    @utils.param_info
    @auth_utils.token_verify
    def list_firewalls(self, request):
        response_obj = ResponseObj()

        project_id = request.session.get('project_id')
        try:
            firewalls = []
            firewall_objects = Firewalls.objects.filter(project_id=project_id).order_by('create_at')
            for firewall_object in firewall_objects:
                firewall = firewall_object.to_dict()

                firewall_rule_count = firewall_object.firewallrule_set.count()

                firewall['firewall_rule_count'] = firewall_rule_count
                firewalls.append(firewall)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info='查询防火墙失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(firewalls)

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         query_serializer=serializers.FirewallRuleListSerializer)
    @utils.param_info
    @auth_utils.token_verify
    def list_firewall_rules(self, request):
        response_obj = ResponseObj()
        firewall_id = request.param_info.get('firewall_id')
        try:
            firewall_rule_objects = service_model.FirewallRule.objects.filter(
                firewall_id=firewall_id).all()
            firewall_rules = list(firewall_rule_objects)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info='查询防火墙规则失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(firewall_rules)

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         request_body=serializers.FirewallCreate)
    @check_element_permission
    @utils.param_info
    @auth_utils.token_verify
    @send_cloud_audit_log_single_request(service_type=audit_types.FIREWALL, resource_type=audit_types.FIREWALL,
                                         trace_name=audit_types.CREATE)
    def create_firewall(self, request):
        response_obj = ResponseObj()

        project_id = request.session.get('project_id')
        param_info = request.param_info

        region = param_info.get('region')
        name = param_info.get('name')
        enabled = param_info.get('enabled', True)
        description = param_info.get("description")
        result = {}
        try:
            with transaction.atomic():
                firewall_object = self.firewall_provider.create_firewall(name=name, region=region,
                                                                         project_id=project_id,
                                                                         enabled=enabled,
                                                                         description=description)
                result.update(firewall_object.to_dict())

                default_egress_rule = self.firewall_provider.create_default_egress_rule(firewall_object.id)
                default_ingress_rule = self.firewall_provider.create_default_ingress_rule(firewall_object.id)
                result['firewall_rule_count'] = 3
        except Exception as ex:
            return response_obj.json_exception_serial(user_info='创建防火墙失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         request_body=serializers.FirewallUpdate)
    @check_element_permission
    @utils.param_info
    @auth_utils.token_verify
    @send_cloud_audit_log_single_request(service_type=audit_types.FIREWALL, resource_type=audit_types.FIREWALL,
                                         trace_name=audit_types.UPDATE)
    def update_firewall(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        firewall_id = param_info.get('firewall_id')
        name = param_info.get('name')
        enabled = param_info.get('enabled', True)
        description = param_info.get("description")

        try:
            with transaction.atomic():
                firewall_object = self.firewall_provider.update_firewall(firewall_id=firewall_id, name=name,
                                                                         enabled=enabled,
                                                                         description=description)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info='更新防火墙失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(firewall_object.to_dict())

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         request_body=serializers.FirewallDelete)
    @check_element_permission
    @utils.param_info
    @auth_utils.token_verify
    @send_cloud_audit_log_multi_request(service_type=audit_types.FIREWALL, resource_type=audit_types.FIREWALL,
                                        trace_name=audit_types.DELETE)
    def delete_firewall(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        firewalls = param_info.get('firewalls')
        project_id = request.session.get('project_id')

        result = []
        try:
            for firewall_id in firewalls:
                with transaction.atomic():
                    # Check if some floatingip use this firewall
                    firewall = service_model.Firewalls.objects.get(id=firewall_id, project_id=project_id)
                    if self.firewall_provider.check_firewall_used(firewall_id):
                        return response_obj.json_exception_serial(user_info='防火墙%s使用中，请先解绑' % firewall.name,
                                                                  admin_info="Firewall in use", no=409)

                    self.firewall_provider.delete_firewall(firewall_id=firewall_id)
                    result.append(firewall.to_dict())
        except Exception as ex:
            return response_obj.json_exception_serial(user_info='删除防火墙失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         request_body=serializers.FirewallRuleCreate)
    @check_element_permission
    @utils.param_info
    @auth_utils.token_verify
    @send_cloud_audit_log_single_request(service_type=audit_types.FIREWALL, resource_type=audit_types.FIREWALL_RULE,
                                         trace_name=audit_types.CREATE)
    def add_firewallrule(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        firewall_id = param_info.get("firewall_id")
        direction = param_info.get('direction')
        action = param_info.get('action')
        protocol = param_info.get('protocol')
        remote_ip = param_info.get('remote_ip')
        remote_port = param_info.get('remote_port')

        try:
            with transaction.atomic():
                firewall_rule = self.firewall_provider.create_firewall_rule(firewall_id,
                                                                            direction=direction,
                                                                            action=action,
                                                                            protocol=protocol,
                                                                            remote_ip=remote_ip,
                                                                            remote_port=remote_port)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info='创建防火墙规则失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(firewall_rule.to_dict())

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         request_body=serializers.FirewallRuleUpdate)
    @check_element_permission
    @utils.param_info
    @auth_utils.token_verify
    @send_cloud_audit_log_single_request(service_type=audit_types.FIREWALL, resource_type=audit_types.FIREWALL_RULE,
                                         trace_name=audit_types.UPDATE)
    def update_firewallrule(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        firewall_id = param_info.get("firewall_id")
        firewall_rule_id = param_info.get("firewall_rule_id")
        direction = param_info.get('direction')
        action = param_info.get('action')
        protocol = param_info.get('protocol')
        remote_ip = param_info.get('remote_ip')
        remote_port = param_info.get('remote_port')
        try:
            with transaction.atomic():
                firewall_rule = self.firewall_provider.update_firewall_rule(firewall_id,
                                                                            firewall_rule_id,
                                                                            direction=direction,
                                                                            action=action,
                                                                            protocol=protocol,
                                                                            remote_ip=remote_ip,
                                                                            remote_port=remote_port)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info='更新防火墙规则失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(firewall_rule.to_dict())

    @swagger_auto_schema(manual_parameters=auth_serializers.TokenParameter,
                         request_body=serializers.FirewallRuleDelete)
    @check_element_permission
    @utils.param_info
    @auth_utils.token_verify
    @send_cloud_audit_log_multi_request(service_type=audit_types.FIREWALL, resource_type=audit_types.FIREWALL_RULE,
                                         trace_name=audit_types.DELETE)
    def delete_firewallrule(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        firewall_id = param_info.get("firewall_id")
        firewall_rule_ids = param_info.get('firewall_rule_id')
        result = []
        try:
            for rule_id in firewall_rule_ids:
                with transaction.atomic():
                    firewall_rule = self.firewall_provider.delete_firewall_rule(firewall_id, rule_id)
                    result.append(firewall_rule.to_dict())
        except Exception as e:
            return response_obj.json_exception_serial(user_info='删除防火墙规则失败', admin_info=str(e), no=500)
        return response_obj.json_serial(result)
