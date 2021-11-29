# -*- coding: utf-8 -*-

import datetime
import logging
import uuid

from django.db import transaction
from django.db import utils as db_utils
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework import viewsets
from openstack import exceptions as openstack_exc

from baremetal_audit import audit_types
from baremetal_audit.handler import send_cloud_audit_log_single_request, send_cloud_log_notification
from BareMetalControllerBackend.conf.env import env_config
from account.auth import utils as auth_utils
from account.repository import auth_models as auth_models
from baremetal_openstack.repository.nova_provider import OpenstackClientProvider
from baremetal_service.repository import service_model as service_model
from baremetal_service.repository import serializers
from common.lark_common.model.common_model import ResponseObj
from common import utils
from common import exceptions as exc

LOG = logging.getLogger(__name__)
FIP_ATTACHED_TYPE = "NAT_GATEWAY"


def get_nat_gateway(project_id, nat_gateway_id):
    """
    获取 NAT 网关
    :param nat_gateway_id: nat 网关id
    :return:
    """
    nat_gateway_obj = service_model.BmServiceNatGateway.objects.filter(project_id=project_id,
                                                                       id=nat_gateway_id,
                                                                       deleted=False).first()
    if not nat_gateway_obj:
        raise exc.NatGateWayNotFound(nat_gateway_id=nat_gateway_id)
    return nat_gateway_obj


class NatGateWayViews(viewsets.ViewSet):

    def __init__(self, *args, **kwargs):
        super(NatGateWayViews, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取可用的vpc列表")
    @auth_utils.token_verify
    @utils.param_info
    def get_available_vpc(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        inuse_vpc_list= service_model.BmServiceNatGateway.objects.filter(
            project_id=project_id, is_measure_end=False).values_list('vpc_id', flat=True)
        available_vpc = service_model.Vpc.objects.filter(
            project_id=project_id).exclude(id__in=inuse_vpc_list).all()
        return response_obj.json_serial(list(available_vpc))

    def check_nat_vpc(self, project_id, vpc_id):
        # 检查vpc是否存在
        vpc = service_model.Vpc.objects.filter(project_id=project_id, id=vpc_id).first()
        if not vpc:
            user_info = "该VPC不存在"
            admin_info = "VPC not found"
            return False, user_info, admin_info

        # 检查VPC是否被绑定
        check_vpc_binded = service_model.BmServiceNatGateway.objects.filter(
            project_id=project_id, vpc_id=vpc_id, is_measure_end=False).first()
        if check_vpc_binded:
            user_info = "该VPC已经被绑定"
            admin_info = "vpc already exist"
            return False, user_info, admin_info
        return True, None, None

    def check_nat_name_duplicate(self, project_id, name):
        check_name = service_model.BmServiceNatGateway.objects.filter(
            project_id=project_id, name=name, is_measure_end=False).first()

        if check_name:
            user_info = "NAT网关%s已存在" % name
            admin_info = "Nat gateway dulicate"
            return False, user_info, admin_info
        return True, None, None

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.NatGateWayCreate,
                         operation_description="创建Nat网关",
                         )
    @auth_utils.token_verify
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.NATWAGEWAY, resource_type=audit_types.NATWAGEWAY,
                                         trace_name=audit_types.CREATE)
    def create(self, request):

        response_obj = ResponseObj()

        param_info = request.param_info
        order_info = param_info.get("order_info")
        name = request.param_info.get('name')
        vpc_id = request.param_info.get('vpc_id')
        description = request.param_info.get('description')

        try:
            with transaction.atomic():

                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))

                check_nat_vpc, user_info, admin_info = self.check_nat_vpc(project_id, vpc_id)
                if not check_nat_vpc:
                    return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info=admin_info)

                check_name, user_info, admin_info = self.check_nat_name_duplicate(project_id, name)
                if not check_name:
                    return response_obj.json_exception_serial(no=409, user_info=user_info, admin_info=admin_info)

                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)
                order_info["project"] = project_result

                # 创建订单
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)
                create_at = datetime.datetime.now()
                nat_gateway_dict = {
                    "order_id": order_result.id,
                    "account_id": account_id,
                    "project_id": project_id,
                    "name": name,
                    "vpc_id": vpc_id,
                    "contract_number": order_info.get("contract_number"),
                    "is_measure_end": False,
                    "create_at": create_at,
                    "description": description
                }
                natgateway_obj = service_model.BmServiceNatGateway.objects.create(**nat_gateway_dict)

                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = create_at
                order_result.save()

                nat_gateway_info = natgateway_obj.to_dict()
                nat_gateway_info['vpc_name'] = service_model.Vpc.objects.get(id=vpc_id).vpc_name

        except Exception as e:
            return response_obj.json_exception_serial(user_info="创建NAT网关失败", admin_info=str(e),
                                                      no=500)

        return response_obj.json_serial(nat_gateway_info)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="查看Nat网关列表",
                         )
    @auth_utils.token_verify
    @utils.param_info
    def list(self, request):
        response_obj = ResponseObj()
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            gateways = []
            nat_gateway_obj = service_model.BmServiceNatGateway.objects.filter(project_id=project_id,
                                                                               is_measure_end=False,
                                                                               ).all()
            for obj in nat_gateway_obj:
                gateway_info = obj.to_dict()
                nat_rule_mappings = obj.nat_rule.all()
                gateway_info['floagintip_count'] = len(nat_rule_mappings.values('floatingip_id').distinct())
                gateway_info['nat_rule_count'] = len(nat_rule_mappings)
                gateway_info['vpc_name'] = service_model.Vpc.objects.get(id=obj.vpc_id).vpc_name
                contract_info = service_model.BmContract.objects.filter(
                    contract_number=obj.contract_number,
                    status='active')
                if contract_info:
                    gateway_info['contract_info'] = contract_info.first().__dict__
                gateways.append(gateway_info)
        except Exception as e:

            return response_obj.json_exception_serial(user_info="获取NAT网关列表失败", admin_info=str(e),
                                                      no=500)
        return response_obj.json_serial(gateways)

    def vaildate_gateway_delete(self, nat_gateway_id):
        """
        检查gateway是否可以删除
        :param nat_gateway_id:
        :return: True or False
        """
        rule_mappings = service_model.NatRule.objects.filter(nat_gateway_id=nat_gateway_id).all()
        if len(rule_mappings) != 0:
            return False
        else:
            return True

    def delete_one_gateway(self, project_id, nat_gateway_id):
        with transaction.atomic():
            nat_gateway_obj = get_nat_gateway(project_id, nat_gateway_id)
            if self.vaildate_gateway_delete(nat_gateway_id):
                nat_gateway_obj.is_measure_end = True
                nat_gateway_obj.deleted = True
                nat_gateway_obj.delete_at = datetime.datetime.now()
                nat_gateway_obj.save()
            else:
                raise exc.NatGatewayRuleExist(nat_gateway_id=nat_gateway_id)
            return nat_gateway_obj.to_dict()

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="删除Nat网关",
                         )
    @auth_utils.token_verify
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.NATWAGEWAY, resource_type=audit_types.NATWAGEWAY,
                                         trace_name=audit_types.DELETE)
    def destroy(self, request, nat_gateway_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        try:
            nat_gateway_info = self.delete_one_gateway(project_id, nat_gateway_id)
        except exc.NatGateWayNotFound as e:
            user_info = "该NAT网关不存在"
            return response_obj.json_exception_serial(user_info=user_info, admin_info=str(e), no=404)
        except exc.NatGatewayRuleExist as e:
            user_info = "该NAT网关下有规则，请先手动删除相应规则"
            return response_obj.json_exception_serial(user_info=user_info, admin_info=str(e), no=409)
        return response_obj.json_serial(nat_gateway_info)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取Nat网关",
                         )
    @auth_utils.token_verify
    @utils.param_info
    def retrieve(self, request, nat_gateway_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        try:
            nat_gateway_obj = get_nat_gateway(project_id, nat_gateway_id)
            nat_rule = nat_gateway_obj.nat_rule.all()
            nat_gateway_info = nat_gateway_obj.to_dict()
            nat_gateway_info['nat_rules'] = [rule.to_dict() for rule in nat_rule]
            nat_gateway_info['vpc_name'] = service_model.Vpc.objects.get(id=nat_gateway_obj.vpc_id).vpc_name

        except exc.NatGateWayNotFound as e:
            user_info = "该NAT网关不存在"
            return response_obj.json_exception_serial(user_info=user_info, admin_info=str(e), no=404)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="获取NAT网关详情失败", admin_info=str(e), no=404)
        return response_obj.json_serial(nat_gateway_info)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.NatGateWayUpdate,
                         operation_description="更新Nat网关",
                         )
    @auth_utils.token_verify
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.NATWAGEWAY, resource_type=audit_types.NATWAGEWAY,
                                         trace_name=audit_types.UPDATE)
    def update(self, request, nat_gateway_id):
        response_obj = ResponseObj()
        name = request.param_info.get('name')
        description = request.param_info.get("description")
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        try:
            with transaction.atomic():
                nat_gateway_obj = get_nat_gateway(project_id, nat_gateway_id)
                if name:
                    check_nat_name, user_info, admin_info = self.check_nat_name_duplicate(
                        project_id, name)
                    if not check_nat_name:
                        return response_obj.json_exception_serial(no=409, user_info=user_info,
                                                                  admin_info=admin_info)
                    nat_gateway_obj.name = name
                    service_model.BmServiceFloatingIp.objects.filter(
                        project_id=project_id, is_measure_end=False,
                        instance_uuid=nat_gateway_id).update(instance_name=name)
                if description:
                    nat_gateway_obj.description = description
                nat_gateway_obj.save()

        except exc.NatGateWayNotFound as e:
            user_info = "该NAT网关不存在"
            return response_obj.json_exception_serial(user_info=user_info, admin_info=str(e), no=404)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="更新NAT网关详情失败", admin_info=str(e), no=404)
        return response_obj.json_serial(nat_gateway_obj)


class DnatRuleViews(viewsets.ViewSet):

    def __init__(self, *args, **kwargs):
        super(DnatRuleViews, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.openstack_provider = OpenstackClientProvider()

    # def list(self, request, nat_gateway_id=None):
    #     pass

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.DnatRuleCreate,
                         operation_description="创建DNAT规则",
                         )
    @auth_utils.token_verify
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.NATWAGEWAY, trace_name=audit_types.CREATE,
                                         resource_id_key='nat_rule_id', resource_type=audit_types.NATRULE)
    def create(self, request, nat_gateway_id=None):

        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        response_obj = ResponseObj()

        fip_id = request.param_info.get('floatingip_id')
        internal_port_id = request.param_info.get('internal_port_id')
        internal_ip_address = request.param_info.get('internal_ip_address')
        internal_port = request.param_info.get('internal_port')
        external_port = request.param_info.get('external_port')
        protocol = request.param_info.get('protocol')
        floating_ip_address = request.param_info.get("floating_ip_address")
        description = request.param_info.get('description')
        port_forward = None
        openstack_client = None

        try:
            nat_gateway = get_nat_gateway(project_id, nat_gateway_id)
            nat_gateway_name = nat_gateway.name

            with transaction.atomic():
                openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
                port_forward = openstack_client.network.create_port_forwarding(
                    floatingip_id=fip_id,
                    internal_port_id=internal_port_id,
                    internal_ip_address=internal_ip_address,
                    internal_port=int(internal_port),
                    external_port=int(external_port),
                    protocol=protocol.lower())
                nat_rule_dict = {
                    'nat_rule_id': port_forward.id,
                    'nat_gateway_id': nat_gateway_id,
                    'floatingip_id': fip_id,
                    'floating_ip_address': floating_ip_address,
                    'external_port': external_port,
                    'protocol': protocol.lower(),
                    'internal_ip_address': internal_ip_address,
                    'internal_port_id': internal_port_id,
                    'internal_port': internal_port,
                    'description': description,
                    'create_at': datetime.datetime.now()
                }
                create_result = service_model.NatRule.objects.create(**nat_rule_dict)

                floating = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                            floating_ip_id=fip_id,
                                                                            is_measure_end=False).first()
                if not floating:
                    return response_obj.json_exception_serial(user_info="该弹性公网ip不存在",
                                                              admin_info="floatingip not found %s" % fip_id,
                                                              no=404)
                if floating.attached and floating.instance_uuid != nat_gateway_id:
                    return response_obj.json_exception_serial(user_info="该公网ip已被其他实例绑定",
                                                              admin_info='floatingip has attached',
                                                              no=409)
                elif not floating.attached:
                    floating.attached = True
                    floating.instance_uuid = nat_gateway_id
                    floating.instance_name = nat_gateway_name
                    # floating.fixed_address = internal_ip_address
                    floating.attached_type = 'NAT'
                    # floating.update_at = datetime.datetime.now()
                    floating.save()
        except openstack_exc.BadRequestException as e:
            user_info = "端口冲突, 冲突端口为:"

            if "internal_port" in e.details:
                user_info += " 内网端口 %d" % internal_port
            if "external_port" in e.details:
                user_info += " 外网端口 %d" % external_port
            elif "The Floating IP" in e.details:
                user_info = "公网ip已被其他NAT网关占用"
            return response_obj.json_exception_serial(user_info=user_info,
                                                      admin_info=e.details,
                                                      no=409)

        except exc.NatGateWayNotFound as e:
            return response_obj.json_exception_serial(user_info="该AT网关不存在",
                                                      admin_info=str(e),
                                                      no=404)

        except Exception as e:
            if port_forward:
                openstack_client.network.delete_port_forwarding(port_forward.id,
                                                                port_forward.floatingip_id,
                                                                ignore_missing=False)
            return response_obj.json_exception_serial(user_info="创建DNAT规则失败", admin_info=str(e), no=500)
        return response_obj.json_serial(create_result.to_dict())

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.DnatRuleUpdate,
                         operation_description="修改Nat规则",
                         )
    @utils.param_info
    @utils.check_request_params(['internal_port_id', 'internal_ip_address', 'internal_port',
                                 'external_port', 'protocol', 'description'])
    @send_cloud_audit_log_single_request(service_type=audit_types.NATWAGEWAY, trace_name=audit_types.UPDATE,
                                         resource_id_key='nat_rule_id', resource_type=audit_types.NATRULE)
    def update(self, request, nat_gateway_id=None, nat_rule_id=None):
        response_obj = ResponseObj()

        updates = request.param_info
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))

        try:
            nat_gateway = get_nat_gateway(project_id, nat_gateway_id)
            with transaction.atomic():

                nat_rule = service_model.NatRule.objects.filter(nat_rule_id=nat_rule_id)
                nat_rule.update(**updates)
                rule = nat_rule.first()
                updates.pop('description')
                openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
                port_forward = openstack_client.network.update_port_forwarding(
                    port_forwarding=nat_rule_id,
                    floating_ip=rule.floatingip_id,
                    **updates)
        except exc.NatGateWayNotFound:
            return response_obj.json_exception_serial(user_info="该NAT网关不存在",
                                                      admin_info="nat_gateway not found %s" % nat_gateway_id,
                                                      no=404)
        except db_utils.IntegrityError as e:
            if "Duplicate entry" in str(e):
                user_info = "端口冲突, 冲突端口为:"
                if "internal_port" in str(e):
                    user_info += " 内网端口 %d" % updates.get('internal_port')
                if "external_port" in str(e):
                    user_info += " 外网端口 %d" % updates.get('external_port')
                return response_obj.json_exception_serial(no=409, user_info=user_info, admin_info=str(e))
        except Exception as e:
            return response_obj.json_exception_serial(user_info="更新DNAT规则失败", admin_info=str(e), no=500)
        return response_obj.json_serial(rule.to_dict())

    def delete_one_nat_rule(self, openstack_client, nat_rule_id):
        with transaction.atomic():
            nat_rule = service_model.NatRule.objects.filter(nat_rule_id=nat_rule_id).first()
            if not nat_rule:
                raise exc.NatRuleNotFound(nat_rule_id=nat_rule_id)
            fip_id = nat_rule.floatingip_id
            nat_rule.delete()
            openstack_client.network.delete_port_forwarding(nat_rule_id, nat_rule.floatingip_id)
            fip = service_model.NatRule.objects.filter(floatingip_id=fip_id)
            if not fip:
                update_dict = {
                    "attached": False,
                    "instance_uuid": None,
                    "attached_type": None,
                    "instance_name": None,
                    # "update_at": datetime.datetime.now()
                }
                service_model.BmServiceFloatingIp.objects.select_for_update().filter(
                    floating_ip_id=nat_rule.floatingip_id).update(**update_dict)

    @auth_utils.token_verify
    @utils.param_info
    def destroy(self, request, nat_gateway_id=None, nat_rule_id=None):
        response_obj = ResponseObj()

        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))

        try:
            nat_gateway = get_nat_gateway(project_id, nat_gateway_id)
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
            self.delete_one_nat_rule(openstack_client, nat_rule_id)

        except exc.NatRuleNotFound as e:
            return response_obj.json_exception_serial(user_info="该DNAT规则不存在", admin_info=str(e), no=404)
        except exc.NatGateWayNotFound:
            return response_obj.json_exception_serial(user_info="该NAT网关不存在",
                                                      admin_info="nat_gateway not found %s" % nat_gateway_id,
                                                      no=404)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="更新DNAT规则失败", admin_info=str(e), no=500)
        return response_obj.json_serial(nat_rule_id)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         request_body=serializers.DnatRuleDelete,
                         operation_description="批量删除Nat规则")
    @auth_utils.token_verify
    @utils.param_info
    def delete_rules(self, request, nat_gateway_id=None):
        response_obj = ResponseObj()

        region = request.session.get('region', env_config.region_name)
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        account_id = request.session.get('account_id', request.COOKIES.get('account_id'))
        nat_rules = request.param_info.get('nat_rules')

        try:
            nat_gateway = get_nat_gateway(project_id, nat_gateway_id)
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request)
            for nat_rule_id in nat_rules:
                self.delete_one_nat_rule(openstack_client, nat_rule_id)
                send_cloud_log_notification(region=region, user_id=account_id, project_id=project_id,
                                            service_type=audit_types.NATWAGEWAY, resource_id=nat_rule_id,
                                            resource_type=audit_types.NATRULE, trace_name=audit_types.DELETE,
                                            request=request.param_info)
        except exc.NatRuleNotFound as e:
            return response_obj.json_exception_serial(user_info="该DAT规则不存在", admin_info=str(e), no=404)
        except exc.NatGateWayNotFound:
            return response_obj.json_exception_serial(user_info="该NAT网关不存在",
                                                      admin_info="nat_gateway not found %s" % nat_gateway_id,
                                                      no=404)
        except Exception as e:
            send_cloud_log_notification(region=region, user_id=account_id, project_id=project_id,
                                        service_type=audit_types.NATWAGEWAY,
                                        resource_type=audit_types.NATRULE, trace_name=audit_types.DELETE,
                                        request=request.param_info)
            return response_obj.json_exception_serial(user_info="批量删除DNAT规则失败", admin_info=str(e), no=500)
        return response_obj.json_serial(nat_rules)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取ports",
                         )
    @auth_utils.token_verify
    @utils.param_info
    def get_ports(self, request, nat_gateway_id=None):
        response_obj = ResponseObj()
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))

            result = []
            network_ids = service_model.Networks.objects.filter(vpc__bmservicenatgateway=nat_gateway_id
                                                                ).values_list('network_id', flat=True)

            admin_client = self.openstack_provider.get_admin_openstack_client()
            filters = {"device_owner": "compute:nova", "project_id": project_id}
            ports = admin_client.list_ports(filters)

            for port in ports:
                if port.get('network_id') in network_ids:
                    port_info = {
                        "id": port.id,
                        "fixed_ips": port.fixed_ips
                    }
                    result.append(port_info)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="获取可转发port失败", admin_info=str(e), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取floatingip_ids",
                         )
    @auth_utils.token_verify
    @utils.param_info
    def get_floatingips(self, request, nat_gateway_id=None):
        response_obj = ResponseObj()
        try:
            res = []
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))

            openstack_client = self.openstack_provider.get_openstack_client_by_request(request)

            fips = openstack_client.network.ips(project_id=project_id)

            query = service_model.BmServiceFloatingIp.objects.filter(
                is_measure_end=False, project_id=project_id).values_list('floating_ip_id', flat=True)
            floatingips_query = query.filter(
                Q(attached=False) | (Q(attached=True) & Q(instance_uuid=nat_gateway_id)))
            floatingips = list(floatingips_query)
            for fip in fips:
                if fip.id in floatingips:
                    res.append({"floating_ip": fip.floating_ip_address, "floating_ip_id": fip.id})
        except Exception as e:
            return response_obj.json_exception_serial(user_info="获取公网ip失败", admin_info=str(e), no=500)
        return response_obj.json_serial(res)
