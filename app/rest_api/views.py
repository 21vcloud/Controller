# -*- coding:utf-8 -*-

import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.views import APIView

from account.auth import utils as auth_utils
from account.repository import serializers as account_serializers
from account.repository import response_serializers as account_response_serializers
from account.views import AccountContractViews, AccountRoleViews, AccountProjectViews, AccountUserViews, \
    AccountEnterpriseViews

from baremetal_openstack.views import KeyPairViews, FirewallViews, NeutronViews
from baremetal_openstack.views import InstanceViews as NovaInstanceViews

from baremetal_service.repository import service_model
from baremetal_service.views import BaremetalServiceBaseResource, BaremetalServiceVolumeViews, \
    BaremetalServiceFloatingIPViews, ObjectViews, BaremetalServiceInstanceViews

from rest_api.auth import utils as rest_auth_utils
from rest_api.repository import serializers
from rest_api.repository import response_serializers

from celery_tasks.tasks import update_fip_firewall, associate_firewall

from common import utils
from common.lark_common.model.common_model import ResponseObj

from BareMetalControllerBackend.conf.env import EnvConfig


config = EnvConfig()
LOG = logging.getLogger(__name__)


# firewall
class FirewallsRulesRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(FirewallsRulesRestfulViews, self).__init__()
        self.firewall_class = FirewallViews()
        self.logger = LOG

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         query_serializer=serializers.FirewallRulesListSerializer)
    @utils.param_info
    @auth_utils.token_verify
    def list(self, request):
        request.method = "GET"
        return self.firewall_class.list_firewall_rules(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=serializers.FirewallRulePost)
    @utils.param_info
    @auth_utils.token_verify
    def create(self, request):
        request.method = "POST"
        return self.firewall_class.add_firewallrule(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=serializers.FirewallRulePut)
    @utils.param_info
    @auth_utils.token_verify
    def update(self, request):
        request.method = "POST"
        return self.firewall_class.update_firewallrule(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=serializers.FirewallRuleDel)
    @utils.param_info
    @auth_utils.token_verify
    def destroy(self, request):
        request.method = "POST"
        return self.firewall_class.delete_firewallrule(request)


class FirewallsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(FirewallsRestfulViews, self).__init__()
        self.firewall_class = FirewallViews()
        self.logger = LOG

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter)
    @utils.param_info
    @auth_utils.token_verify
    def list(self, request):
        request.method = "GET"
        return self.firewall_class.list_firewalls(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=serializers.FirewallPost)
    @utils.param_info
    @auth_utils.token_verify
    def create(self, request):
        request.method = "POST"
        return self.firewall_class.create_firewall(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=serializers.FirewallPut)
    @utils.param_info
    @auth_utils.token_verify
    def update(self, request):
        request.method = "POST"
        return self.firewall_class.update_firewall(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=serializers.FirewallDel)
    @utils.param_info
    @auth_utils.token_verify
    def destroy(self, request):
        request.method = "POST"
        return self.firewall_class.delete_firewall(request)


# floating IP
class FloatingIpFirewallAttachments(APIView):
    @swagger_auto_schema(request_body=serializers.FipServiceFloatingIpAssociateFirewall,
                         operation_description="弹性公网IP关联防火墙",
                         responses={200: response_serializers.FipFloatingIpAssociateFirewallResponsesSerializer}
                         )
    @utils.param_info
    def get(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        floating_ip_id = param_info.get("floating_ip_id")
        floating_ip = param_info.get('floating_ip')
        firewall_id = param_info.get('firewall_id')
        result = {}
        try:
            mappings = service_model.BmFloatingipfirewallMapping.objects.filter(
                floating_ip_id=floating_ip_id).first()

            if mappings:
                old_firewall_id = mappings.firewall_id
                mappings.firewall_id = firewall_id
                mappings.save()

                new_firewall_rules = []
                old_firewall = service_model.Firewalls.objects.get(id=old_firewall_id)
                new_firewall = service_model.Firewalls.objects.get(id=firewall_id)
                new_firewall_object = new_firewall.firewallrule_set.all()
                for object in new_firewall_object:
                    new_firewall_rules.append(object.to_dict())

                update_fip_firewall.delay(floating_ip, old_firewall.to_dict(), new_firewall.to_dict(),
                                          new_firewall_rules)
                result['floating_ip_id'] = floating_ip_id,
                result['firewall'] = new_firewall.to_dict()
            else:
                firewall_rules = []
                mappings = service_model.BmFloatingipfirewallMapping.objects.create(
                    floating_ip_id=floating_ip_id, firewall_id=firewall_id, floating_ip=floating_ip)
                firewall = service_model.Firewalls.objects.get(id=firewall_id)
                firewall_rule_objects = firewall.firewallrule_set.all()
                for object in firewall_rule_objects:
                    firewall_rules.append(object.to_dict())

                associate_firewall.delay(floating_ip, firewall.to_dict(), firewall_rules)
                result['floating_ip_id'] = floating_ip_id,
                result['firewall'] = firewall.to_dict()
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="关联防火墙失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(result)


class FloatingIpInstancesRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(FloatingIpInstancesRestfulViews, self).__init__()
        self.fip_class = BaremetalServiceFloatingIPViews()

    @swagger_auto_schema(
        operation_description="查询可绑定实例列表",
        responses={200: response_serializers.FipInstanceListAvaliableResponsesSerializer})
    def list(self, request):
        request.method = "GET"
        return self.fip_class.instance_list_avaliable_to_floating_ip(request)

    @swagger_auto_schema(request_body=serializers.FipServiceAddFloatingIptoServerSerializer,
                         operation_description="实例关联浮动ip",
                         responses={200: response_serializers.FipFloatingIpAttachToServerResponsesSerializer}
                         )
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.fip_class.attach_ip_to_server(request)

    @swagger_auto_schema(request_body=serializers.FipServiceDetachFloatingIptoServerSerializer,
                         operation_description="实例解绑浮动ip",
                         responses={200: response_serializers.FipFloatingIpDetachFromServerResponsesSerializer})
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.fip_class.detach_ip_from_server(request)


class FloatingIpQuotasRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(FloatingIpQuotasRestfulViews, self).__init__()
        self.fip_class = BaremetalServiceFloatingIPViews()

    @swagger_auto_schema(
        operation_description="检查配额(需要在登陆下调用接口)",
        responses={200: response_serializers.FipFloatingIpQuotaResponsesSerializer}
    )
    @utils.param_info
    def retrieve(self, request):
        request.method = "GET"
        return self.fip_class.floating_ip_quota(request)

    @swagger_auto_schema(request_body=serializers.FloatingIpQuotasSetSerializer,
                         operation_description="调整浮动IP带宽",
                         responses={200: response_serializers.FipFloatingIpQuotaSetResponsesSerializer})
    @utils.param_info
    def update(self, request):
        request.method = "POST"
        return self.fip_class.floating_ip_quotas_set(request)


class FloatingIPsRestfulViews(viewsets.ViewSet):

    def __init__(self):
        super(FloatingIPsRestfulViews, self).__init__()
        self.floating_ip_class = BaremetalServiceFloatingIPViews()

    @swagger_auto_schema(
        operation_description="查看浮动ip列表",
        responses={200: response_serializers.FipFloatingIpListResponsesSerializer})
    @utils.param_info
    def list(self, request):
        return self.floating_ip_class.floating_ip_list(request)

    @swagger_auto_schema(request_body=serializers.FipServiceCreateFloatingIpSerializer,
                         operation_description="购买弹性公网ip",
                         responses={200: response_serializers.FipFloatingIpCreatedResponsesSerializer}
                         )
    @utils.param_info
    def create(self, request):
        return self.floating_ip_class.floating_ip_create(request)

    @swagger_auto_schema(request_body=serializers.FipServiceDeleteFloatingIpSerializer,
                         operation_description="弹性公网IP的删除操作",
                         responses={200: response_serializers.FipFloatingIpDeletedResponsesSerializer})
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.floating_ip_class.floating_ip_delete(request)


class FipRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(FipRestfulViews, self).__init__()
        self.floating_ip_class = BaremetalServiceFloatingIPViews()

    @swagger_auto_schema(request_body=serializers.FipServiceFloatingIpAssociateFirewall,
                         operation_description="弹性公网IP关联防火墙",
                         responses={200: response_serializers.FipFloatingIpAssociateFirewallResponsesSerializer}
                         )
    @utils.param_info
    def associate_firewall(self, request):
        request.method = "POST"
        return self.floating_ip_class.floating_ip_associate_firewall(request)


# IAM (Identity Access Management)
class IamAccountRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(IamAccountRestfulViews, self).__init__()
        self.account_user_class = AccountUserViews()
        self.env_config = config
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         response_serializers={200: response_serializers.IamAkResponsesInfo},
                         operation_description="获取当前用户下所有秘钥")
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def retrieve_key(self, request):
        response_obj = ResponseObj()
        try:
            response_obj = ResponseObj()
            account_id = request.META['HTTP_ACCOUNTID']
            if not account_id:
                user_info = "您必须通过web控制台查看AK/SK，"
                admin_info = "Cant create Ak/Sk by RESTfulApi"
                return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info=admin_info)

            access_key_info = rest_auth_utils.get_secret_key(account_id)
        except Exception as e:
            user_info = "获取AK/SK"
            return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info=str(e))
        return response_obj.json_serial(access_key_info)

    @swagger_auto_schema(request_body=serializers.IamLoginSerializer,
                         responses={200: response_serializers.IamLoginResponsesInfo},
                         operation_description="用户登录接口")
    @rest_auth_utils.access_token_verify
    @auth_utils.param_info_decrypt
    def login(self, request):
        return rest_auth_utils.access_login(request)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.IamLogoutSerializer,
                         responses={200: response_serializers.IamLogoutResponsesSerializer},
                         operation_description="用户登出接口")
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def logout(self, request):
        request.method = "POST"
        return self.account_user_class.logout(request)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="查询个人账户信息",
                         query_serializer=serializers.IamQueryAccountByAccountSerializer,
                         responses={200: response_serializers.IamAccInfoByAccResponsesSerializer}
                         )
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def query_account_info_by_account(self, request):
        request.method = "GET"
        return self.account_user_class.query_account_info_by_account(request)


class AccountContractRestfulViews(APIView):
    def __init__(self):
        super(AccountContractRestfulViews, self).__init__()
        self.account_contract_class = AccountContractViews()

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="合同信息的更新",
                         responses={200: account_response_serializers.ContractUpdateResponsesSerializer},
                         request_body=account_serializers.UpdateContractSerializer)
    def put(self, request):
        request.method = 'POST'
        return self.account_contract_class.contract_update(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="合同的创建",
                         responses={200: account_response_serializers.ContractCreatedResponsesSerializer},
                         request_body=account_serializers.CreateContractSerializer)
    def post(self, request):
        return self.account_contract_class.contract_create(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="合同的删除",
                         responses={200: account_response_serializers.ContractDeletedResponsesSerializer},
                         request_body=account_serializers.DeleteListSerializer)
    def delete(self, request):
        request.method = 'POST'
        return self.account_contract_class.contract_delete(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="获取所有的合同信息",
                         responses={200: account_response_serializers.AllInfoResponsesSerializer}
                         )
    def get(self, request):
        return self.account_contract_class.query_all_contract_info(request)


class AccountRoleRestfulViews(APIView):
    def __init__(self):
        super(AccountRoleRestfulViews, self).__init__()
        self.account_role_class = AccountRoleViews()

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         responses={200: account_response_serializers.RoleUpdateResponsesSerializer},
                         operation_description="更新角色",
                         request_body=account_serializers.UpdateRoleSerializer)
    def put(self, request):
        request.method = 'POST'
        return self.account_role_class.role_update(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         responses={200: account_response_serializers.RoleCreatedResponsesSerializer},
                         operation_description="创建角色",
                         request_body=account_serializers.CreateRoleSerializer)
    def post(self, request):
        return self.account_role_class.role_create(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         responses={200: account_response_serializers.RoleDeletedResponsesSerializer},
                         operation_description="删除角色",
                         request_body=account_serializers.DeleteListSerializer)
    def delete(self, request):
        request.method = 'POST'
        return self.account_role_class.role_delete(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         responses={200: account_response_serializers.AllRoleResponsesSerializer},
                         operation_description="获取所有角色信息")
    def get(self, request):
        return self.account_role_class.query_all_role_info(request)


class AccountProjectRestfulViews(APIView):
    def __init__(self):
        super(AccountProjectRestfulViews, self).__init__()
        self.account_project_class = AccountProjectViews()

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="更新项目信息",
                         responses={200: account_response_serializers.ProjectRoleManageResponsesSerializer},
                         request_body=account_serializers.UpdateProjectInfoSerializer)
    def put(self, request):
        request.method = 'POST'
        return self.account_project_class.project_update(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="项目创建",
                         responses={200: account_response_serializers.ProjectCreatedResponsesSerializer},
                         request_body=account_serializers.CreateProjectSerializer)
    def post(self, request):
        return self.account_project_class.project_create(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="项目的删除",
                         responses={200: account_response_serializers.ProjectDeletedResponsesSerializer},
                         request_body=account_serializers.DeleteListSerializer)
    def delete(self, request):
        request.method = 'POST'
        return self.account_project_class.project_delete(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="获取项目信息",
                         responses={200: account_response_serializers.ProjectInfoResponsesSerializer},
                         )
    def get(self, request):
        return self.account_project_class.query_all_project_info(request)


class AccountUserRestfulViews(APIView):
    def __init__(self):
        super(AccountUserRestfulViews, self).__init__()
        self.account_user_class = AccountUserViews()

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         request_body=account_serializers.UpateUserInfoSerializer,
                         responses={200: account_response_serializers.UserInfoUpdateResponsesSerializer},
                         operation_description="用户更新接口")
    def put(self, request):
        request.method = 'POST'
        return self.account_user_class.user_info_update(request)

    @swagger_auto_schema(request_body=account_serializers.RegisterSerializer,
                         responses={200: account_response_serializers.GetWebsocketResponsesSerializer},
                         operation_description="用户注册接口")
    def post(self, request):
        return self.account_user_class.register(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         responses={200: account_response_serializers.DeleteUserResponsesSerializer},
                         operation_description="删除用户接口",
                         request_body=account_serializers.DeleteUserInfoSerializer)
    def delete(self, request):
        request.method = 'POST'
        return self.account_user_class.user_delete(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="查询所有用户信息",
                         responses={200: account_response_serializers.AllAccountInfoResponsesSerializer},
                         )
    def get(self, request):
        return self.account_user_class.query_all_account_info(request)


class AccountEnterpriseRestfulViews(APIView):
    def __init__(self):
        super(AccountEnterpriseRestfulViews, self).__init__()
        self.account_enterprise_class = AccountEnterpriseViews()

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="更新公司信息",
                         responses={200: account_response_serializers.EnterpriseUpdateResponsesSerializer},
                         request_body=account_serializers.UpdateEnterpriseSerializer)
    def put(self, request):
        request.method = 'POST'
        return self.account_enterprise_class.enterprise_update(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="公司的创建",
                         responses={200: account_response_serializers.EnterpriseCreatedResponsesSerializer},
                         request_body=account_serializers.CreateEnterpriseSerializer)
    def post(self, request):
        return self.account_enterprise_class.enterprise_create(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="获取所有的公司信息",
                         responses={200: account_response_serializers.AllEnterpriseResponsesSerializer},
                         )
    def delete(self, request):
        request.method = 'POST'
        return self.account_enterprise_class.enterprise_delete(request)

    @swagger_auto_schema(manual_parameters=account_serializers.TokenParameter,
                         operation_description="查询所有用户信息",
                         responses={200: account_response_serializers.AllAccountInfoResponsesSerializer},
                         )
    def get(self, request):
        return self.account_enterprise_class.query_all_enterprise_info(request)


# instances
class InstanceRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(InstanceRestfulViews, self).__init__()
        self.logger = LOG
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

        self.instance_class = BaremetalServiceInstanceViews()
        self.nova_class = NovaInstanceViews()
        self.base_service_class = BaremetalServiceBaseResource()

    @swagger_auto_schema(request_body=serializers.InstStopSerializer,
                         operation_description="服务器关机")
    @utils.param_info
    def instance_stop(self, request):
        request.method = "POST"
        return self.nova_class.instance_stop(request)

    @swagger_auto_schema(request_body=serializers.InstStartSerializer,
                         operation_description="服务器开机")
    @utils.param_info
    def instance_start(self, request):
        request.method = "POST"
        return self.nova_class.instance_start(request)

    @swagger_auto_schema(request_body=serializers.InstRestartSerializer,
                         operation_description="服务器重启")
    @utils.param_info
    def instance_restart(self, request):
        request.method = "POST"
        return self.nova_class.instance_restart(request)

    @swagger_auto_schema(operation_description="获取机器的端口")
    @utils.param_info
    def get_instance_ports(self, request):
        request.method = "GET"
        return self.nova_class.get_instance_ports(request)

    @swagger_auto_schema(operation_description="获取服务器列表",
                         responses={200: response_serializers.FlavorListResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def flavor_list(self, request):
        request.method = "GET"
        return self.base_service_class.flavor_list(request)

    @swagger_auto_schema(operation_description="更新flavor的数量",
                         responses={200: response_serializers.InstUpdateFlavorCountInfoResponsesSerializer}
                         )
    @utils.param_info
    def update_flavor_count(self, request):
        request.method = "POST"
        return self.base_service_class.update_flavor_count(request)

    @swagger_auto_schema(query_serializer=serializers.InstServiceMachineIdSerializer,
                         operation_description="获取machine信息",
                         responses={200: response_serializers.InstMachineGetResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def view_baremetal_service_machine_get(self, request):
        request.method = "GET"
        return self.instance_class.view_baremetal_service_machine_get(request)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有的订单信息",
                         responses={200: response_serializers.InstAllOrderResponsesSerializer}
                         )
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def view_baremetal_service_order_all(self, request):
        request.method = "GET"
        return self.instance_class.view_baremetal_service_order_all(request)

    @swagger_auto_schema(query_serializer=serializers.InstanceIdListSerializer,
                         operation_description="获取服务器网络接口列表")
    @utils.param_info
    def instance_list_interface(self, request):
        request.method = "GET"
        return self.nova_class.instance_list_interface(request)

    @swagger_auto_schema(operation_description="获取镜像列表",
                         responses={200: response_serializers.InstImageListResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def images_list(self, request):
        request.method = "GET"
        return self.base_service_class.images_list(request)


class ServiceOrderRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ServiceOrderRestfulViews, self).__init__()
        self.instance_class = BaremetalServiceInstanceViews()
        self.logger = LOG
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取某用户所有的订单信息",
                         responses={200: response_serializers.InstOrderByAccInfoResponsesSerializer},
                         query_serializer=serializers.InstServiceOrderQuerybyAccountSerializer)
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def list(self, request):
        request.method = "GET"
        return self.instance_class.view_baremetal_service_order_query_by_account(request)


class ServiceInstanceRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ServiceInstanceRestfulViews, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.nova_class = NovaInstanceViews()
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(operation_description="获取可以挂载云硬盘的机器")
    @utils.param_info
    def retrieve(self, request):
        request.method = "GET"
        return self.nova_class.instance_list_by_os_active(request)

    @swagger_auto_schema(request_body=serializers.ServiceInstFeedbackSerializer,
                         operation_description="实例更新",
                         responses={200: response_serializers.InstFeedBackResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def update(self, request):
        request.method = "POST"
        return BaremetalServiceInstanceViews.view_baremetal_service_instance_feedback(request)


class ServiceInstancesRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ServiceInstancesRestfulViews, self).__init__()
        self.instance_class = BaremetalServiceInstanceViews()
        self.nova_class = NovaInstanceViews()

    @swagger_auto_schema(
        operation_description="查询可绑定实例列表",
        responses={200: response_serializers.InstAvaliableInstanceListResponsesSerializer})
    def list(self, request):
        request.method = "GET"
        return self.nova_class.instance_list(request)

    # 购买服务器
    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="购买裸金属服务器",
                         request_body=serializers.InstServiceCreateListSerializer)
    @auth_utils.token_verify
    @auth_utils.param_info_decrypt
    def create(self, request):
        request.method = "POST"
        return self.instance_class.view_create_baremetal_service(request)

    @swagger_auto_schema(request_body=serializers.InstanceDelSerializer,
                         operation_description="删除挂载了云硬盘的实例")
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.nova_class.instance_delete(request)


class InterfaceAttachmentsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(InterfaceAttachmentsRestfulViews, self).__init__()
        self.nova_class = NovaInstanceViews()

    @swagger_auto_schema(request_body=serializers.InstanceInterfaceAttachmentSerializer,
                         operation_description="服务器添加网络接口")
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.nova_class.instance_attach_interface(request)

    @swagger_auto_schema(request_body=serializers.InstanceInterfaceDetSerializer,
                         operation_description="服务器网络接口分离")
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.nova_class.instance_detach_interface(request)


# keypair
class KeypairsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(KeypairsRestfulViews, self).__init__()
        self.key_pair_class = KeyPairViews()

    @swagger_auto_schema(request_body=serializers.KeypairsCreate,
                         operation_description="创建密钥对"
                         )
    @utils.param_info
    def create(self, request):
        return self.key_pair_class.keypair_create(request)

    @swagger_auto_schema(
                        manual_parameters=serializers.TokenParameter,
                        operation_description="获取密钥对列表"
                        )
    @utils.param_info
    # @rest_auth_utils.signature_verify
    @rest_auth_utils.access_token_verify
    def list(self, request):
        return self.key_pair_class.keypair_list(request)

    @swagger_auto_schema(request_body=serializers.KeypairsDelete,
                         operation_description="删除密钥对")
    @utils.param_info
    def destroy(self, request):
        request.method = 'POST'
        return self.key_pair_class.keypair_delete(request)


# OBS: object storage
class ObsBucketsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ObsBucketsRestfulViews, self).__init__()
        self.obs_class = ObjectViews()

    @swagger_auto_schema(
        operation_description="桶列表",
        responses={200: response_serializers.ObsBucketListResponsesSerializer}
    )
    @utils.param_info
    def list(self, request):
        request.method = "GET"
        return self.obs_class.list_bucket(request)

    @swagger_auto_schema(request_body=serializers.ObsBucketCreateSerializer,
                         operation_description="创建桶",
                         responses={200: response_serializers.ObsCreatedBucketResponsesSerializer}
                         )
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.obs_class.create_bucket(request)

    @swagger_auto_schema(request_body=serializers.ObsBucketDeleteSerializer,
                         operation_description="删除桶",
                         responses={200: response_serializers.ObsDeleteBucketResponsesSerializer}
                         )
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.obs_class.delete_bucket(request)

    @swagger_auto_schema(request_body=serializers.ObsBucketUpdateSeraializer,
                         operation_description="更新桶信息",
                         responses={200: response_serializers.ObsUpdateBucketResponsesSerializer}
                         )
    @utils.param_info
    def update(self, request):
        request.method = "POST"
        return self.obs_class.update_bucket(request)


class ObsFilesRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ObsFilesRestfulViews, self).__init__()
        self.obs_class = ObjectViews()

    @swagger_auto_schema(operation_description="下载文件")
    def retrieve(self, request,container_name=None,object_name=None):
        request.method = "GET"
        return self.obs_class.download_file_rest(request,container_name,object_name)

    @swagger_auto_schema(
        request_body=serializers.ObsFileUploadSerializer,
        operation_description="上传文件",
        responses={200: response_serializers.ObsUploadFileResponsesSerializer}
    )
    def create(self, request):
        request.method = "POST"
        return self.obs_class.upload_file(request)


class ObsObjectsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ObsObjectsRestfulViews, self).__init__()
        self.obs_class = ObjectViews()

    @swagger_auto_schema(query_serializer=serializers.ObsBucketShowSerializer,
                         operation_description="对象存储列表",
                         responses={200: response_serializers.ObsObjectsListResponsesSerializer}
                         )
    @utils.param_info
    def list(self, request):
        request.method = "GET"
        return self.obs_class.list_objects(request)

    @swagger_auto_schema(request_body=serializers.ObsBucketDeleteObjectSerializer,
                         operation_description="删除对象",
                         responses={200: response_serializers.ObsDeleteObjectsResponsesSerializer}
                         )
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.obs_class.delete_object(request)


class ObsObjectRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ObsObjectRestfulViews, self).__init__()
        self.obs_class = ObjectViews()

    @swagger_auto_schema(request_body=serializers.ObsBucketCreateDirSerializer,
                         operation_description="创建目录",
                         responses={200: response_serializers.ObsCreatedDirResponsesSerializer}
                         )
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.obs_class.create_dir(request)

    @swagger_auto_schema(operation_description="获取对象信息")
    def retrieve(self, request,container_name=None,object_name=None):
        request.method = "GET"
        return self.obs_class.show_object_rest(request,container_name,object_name)


class ObsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(ObsRestfulViews, self).__init__()
        self.obs_class = ObjectViews()

    @swagger_auto_schema(request_body=serializers.ObsBucketCreateDirSerializer,
                         operation_description="创建目录",
                         responses={200: response_serializers.ObsCreatedDirResponsesSerializer}
                         )
    @utils.param_info
    def create_dir(self, request):
        request.method = "POST"
        return self.obs_class.create_dir(request)

    @swagger_auto_schema(operation_description="获取桶信息")
    def show_bucket(self, request, container_name=None):
        request.method = "GET"
        return self.obs_class.show_bucket_restful(request, container_name)

    @swagger_auto_schema(query_serializer=serializers.ObsBucketShowObjectSerializer,
                         operation_description="获取对象信息")
    @utils.param_info
    def show_object(self, request):
        request.method = "GET"
        return self.obs_class.show_object(request)


# VBS: volume and volume backup
class VolumesRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(VolumesRestfulViews, self).__init__()
        self.volume_class = BaremetalServiceVolumeViews()

    @swagger_auto_schema(request_body=serializers.VbsCreateSerializer,
                         operation_description="创建云硬盘",
                         responses={200: response_serializers.VbsCreatedResponsesSerializer})
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.volume_class.volume_create(request)

    @swagger_auto_schema(
        operation_description="云硬盘列表",
        responses={200: response_serializers.VbsListResponsesSerializer},
    )
    @utils.param_info
    def list(self, request):
        request.method = "GET"
        return self.volume_class.volume_list(request)

    @swagger_auto_schema(request_body=serializers.VbsUpdateSerializer,
                         operation_description="更新云硬盘信息",
                         responses={200: response_serializers.VbsUpdateResponsesSerializer},
                         )
    @utils.param_info
    def update(self, request):
        request.method = "POST"
        return self.volume_class.volume_update(request)

    @swagger_auto_schema(request_body=serializers.VbsDeleteSerailizer,
                         operation_description="删除云硬盘",
                         responses={200: response_serializers.VbsDeletedResponsesSerializer},
                         )
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.volume_class.volume_delete(request)


class VolumeBackupsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(VolumeBackupsRestfulViews, self).__init__()
        self.volume_class = BaremetalServiceVolumeViews()

    @swagger_auto_schema(
        operation_description="查看云硬盘备份",
        responses={200: response_serializers.VbsBackupListResponsesSerializer},
    )
    @utils.param_info
    def list(self, request):
        request.method = "POST"
        return self.volume_class.volume_backup_list(request)

    @swagger_auto_schema(request_body=serializers.VbsBackupCreateSerializer,
                         operation_description="创建云硬盘备份",
                         responses={200: response_serializers.VbsBackupCreateResponsesSerializer})
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.volume_class.volume_backup_create(request)

    @swagger_auto_schema(request_body=serializers.VbsBackupDeleteSerializer,
                         operation_description="删除云硬盘备份",
                         responses={200: response_serializers.VbsBackupDeletedResponsesSerializer},
                         )
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.volume_class.volume_backup_delete(request)


class VolumeAttachmentsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(VolumeAttachmentsRestfulViews, self).__init__()
        self.volume_class = BaremetalServiceVolumeViews()

    @swagger_auto_schema(request_body=serializers.VbsAttachSerializer,
                         operation_description="磁盘挂载",
                         responses={200: response_serializers.FeedbackVbsAttachResponsesSerializer},
                         )
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.volume_class.volume_attach(request)

    @swagger_auto_schema(request_body=serializers.VbsAttachSerializer,
                         operation_description="卸载云硬盘",
                         responses={200: response_serializers.VbsDetachResponsesSerializer},
                         )
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.volume_class.volume_detach(request)


class VbsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(VbsRestfulViews, self).__init__()
        self.volume_class = BaremetalServiceVolumeViews()

    @swagger_auto_schema(request_body=serializers.VbsBackupRestoreSerializer)
    @utils.param_info
    def volume_backup_restore(self, request):
        request.method = "POST"
        return self.volume_class.volume_backup_restore(request)

    @utils.param_info
    def volume_type_list(self, request):
        request.method = "GET"
        return self.volume_class.volume_type_list(request)

    @utils.param_info
    def volume_quota(self, request):
        request.method = "GET"
        return self.volume_class.volume_quota(request)


# VPC
class VpcsRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(VpcsRestfulViews, self).__init__()
        self.vpc_class = NeutronViews()

    @swagger_auto_schema(request_body=serializers.CreateVpcsSerializer)
    @utils.param_info
    @utils.check_invalid_kwargs_with_normal_user('project_id')
    def create(self, request):
        request.method = "POST"
        return self.vpc_class.create_vpc(request)

    @swagger_auto_schema()
    @utils.param_info
    @utils.check_invalid_kwargs_with_normal_user('project_id')
    def list(self, request):
        request.method = "GET"
        return self.vpc_class.list_vpcs(request)

    @swagger_auto_schema(request_body=serializers.UpdateVpcsSerializer)
    @utils.param_info
    def update(self, request):
        request.method = "POST"
        return self.vpc_class.update_vpc(request)

    @swagger_auto_schema(request_body=serializers.DeleteVpcsSerializer)
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.vpc_class.delete_vpc(request)


class VpcNetworksRestfulViews(viewsets.ViewSet):
    def __init__(self):
        super(VpcNetworksRestfulViews, self).__init__()
        self.vpc_class = NeutronViews()

    def list(self, request, vpc_id=None):
        request.method = "GET"
        return self.vpc_class.list_networks_by_vpc_rest(request, vpc_id)

    @swagger_auto_schema(request_body=serializers.PostVpcNetwork)
    @utils.param_info
    def create(self, request):
        request.method = "POST"
        return self.vpc_class.add_network_by_vpc(request)

    @swagger_auto_schema(request_body=serializers.PutVpcNetwork)
    @utils.param_info
    def update(self, request):
        request.method = "POST"
        return self.vpc_class.update_network_by_vpc(request)

    @swagger_auto_schema(request_body=serializers.DelVpcNetwork)
    @utils.param_info
    def destroy(self, request):
        request.method = "POST"
        return self.vpc_class.delete_network_by_vpc(request)
