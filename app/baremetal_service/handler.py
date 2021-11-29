# -*- coding: utf-8 -*-
import logging
import datetime, time
import re
import ssl
# from OpenSSL import crypto
# import socket
# from socket import AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, SHUT_RDWR
# import pathlib
# from pathlib import Path
# from typing import Union
# import pem

# import barbicanclient
from barbicanclient import client
# from barbican.common import quota
# from barbicanclient.v1.containers import Container
from barbicanclient.v1.containers import RSAContainer
from barbicanclient.v1.containers import CertificateContainer
from common.lark_common.model.common_model import ResponseObj
from baremetal_service import swift_handler as swift_handler
from baremetal_service.repository import service_model as service_model
from django.db import transaction
from common import utils
from common import exceptions as exc
from account.repository import auth_models as auth_models

LOG = logging.getLogger(__name__)

AUTH_URL = 'http://10.100.2.98:5000/v3'
USERNAME = 'admin'
PASSWORD = 'DDtX5pw2rfw1yyyzEXNLFT3D4'
PROJECT_NAME = 'admin'


def load_balancer_status_verify(openstack_client, loadbalancer_id):
    try:
        # 进行循环获取load balancer的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 50:
                raise exc.TimeoutError()
            load_balancer_detail = openstack_client.load_balancer.get_load_balancer(loadbalancer_id).to_dict()
            load_balancer_status = load_balancer_detail["provisioning_status"]
            if load_balancer_status == "ACTIVE" or load_balancer_status == "ERROR":
                break
            time.sleep(2)
    except Exception as ex:
        raise ex
    return load_balancer_detail, load_balancer_status


def pool_status_verify(request, pool_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        # 进行循环获取pool的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            pool_detail = openstack_client.load_balancer.get_pool(pool_id).to_dict()
            pool_status = pool_detail["provisioning_status"]
            if pool_status == "ACTIVE" or pool_status == "ERROR":
                break
            time.sleep(2)

        for lb in pool_detail["loadbalancers"]:
            load_balancer_detail, load_balancer_status = load_balancer_status_verify(openstack_client, lb)

    except Exception as e:
        raise e
    return pool_detail, pool_status


def listener_status_verify(openstack_client, listener_id):
    try:
        # 进行循环获取listener的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            current_listener = openstack_client.load_balancer.get_listener(listener_id)
            listener_detail = current_listener.to_dict()
            listener_id = listener_detail["id"]
            listener_status = listener_detail["provisioning_status"]
            if listener_status == "ACTIVE" or listener_status == "ERROR":
                break
            time.sleep(2)
    except Exception as ex:
        raise ex
    return current_listener


def policy_status_verify(openstack_client, l7policy_id):
    try:
        # 进行循环获取rule的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            current_policy = openstack_client.load_balancer.get_l7_policy(l7policy_id)
            policy_detail = current_policy.to_dict()
            policy_status = policy_detail["provisioning_status"]
            if policy_status == "ACTIVE" or policy_status == "ERROR":
                break
            time.sleep(2)
    except Exception as ex:
        raise ex
    return current_policy


def health_monitor_status_verify(openstack_client, healthmonitor_id):
    try:
        # 进行循环获取health monitor的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            health_monitor_detail = openstack_client.load_balancer.get_health_monitor(healthmonitor_id).to_dict()
            health_monitor_status = health_monitor_detail["provisioning_status"]
            if health_monitor_status == "ACTIVE" or health_monitor_status == "ERROR":
                break
            time.sleep(2)
    except Exception as ex:
        raise ex
    return health_monitor_detail, health_monitor_status


def pool_member_status_verify(openstack_client, member_id, pool_id):
    try:
        # 进行循环获取member的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            member_detail = openstack_client.load_balancer.get_member(member_id, pool_id).to_dict()
            member_status = member_detail["provisioning_status"]
            if member_status == "ACTIVE" or member_status == "ERROR":
                break
            time.sleep(2)
    except Exception as ex:
        raise ex
    return member_detail, member_status


def listener_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        listener_list = openstack_client.load_balancer.listeners(project_id=project_id)
    except Exception as e:
        raise e
    return listener_list


def policies_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        policies_list = openstack_client.load_balancer.l7_policies(project_id=project_id)
    except Exception as e:
        raise e
    return policies_list


def listener_policies_list(request, project_id=None, listener_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        listener_dict = listener_status_verify(openstack_client, listener_id)
        query = {
            'project_id': project_id,
            'listener_id': listener_id
        }
        policies_list = openstack_client.load_balancer.l7_policies(**query)
    except Exception as e:
        raise e
    return policies_list


def pools_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        policies_list = openstack_client.load_balancer.pools(project_id=project_id)
        load_balances_pool_list = []
        for load_balances_pool in policies_list:
            load_balances_pool_obj = {
                "created_at": load_balances_pool.created_at,
                "health_monitor_id": load_balances_pool.health_monitor_id,
                "id": load_balances_pool.id,
                "is_admin_state_up": load_balances_pool.is_admin_state_up,
                "lb_algorithm": load_balances_pool.lb_algorithm,
                "name": load_balances_pool.name,
                "operating_status": load_balances_pool.operating_status,
                "project_id": load_balances_pool.project_id,
                "protocol": load_balances_pool.protocol,
                "provisioning_status": load_balances_pool.provisioning_status,
                "session_persistence": load_balances_pool.session_persistence,
            }
            load_balances_pool_list.append(load_balances_pool_obj)
    except Exception as e:
        raise e

    return load_balances_pool_list


def health_monitor_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:

        health_monitor_list = openstack_client.load_balancer.health_monitors(project_id=project_id)

    except Exception as e:
        raise e
    return health_monitor_list


def flavor_list(request):
    openstack_client = utils.get_openstack_client(request)

    try:
        flavor_list = openstack_client.compute.flavors()
    except Exception as e:
        raise e
    return flavor_list


def rule_uri_list(request, l7policy_id, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        domain_name = None
        url = None
        rule_uri_list = openstack_client.load_balancer.l7_rules(l7policy_id, project_id=project_id)
        for rule in rule_uri_list:
            if rule.type == 'HOST_NAME':
                domain_name = rule.rule_value
            if rule.type == 'PATH':
                url = rule.rule_value
        result = {'HOST_NAME': domain_name, 'PATH': url}
    except Exception as ex:
        raise ex
    return result


def policies_rule_list(request, l7policy_id, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        policy_dict = policy_status_verify(openstack_client, l7policy_id)
        policies_rule_list = openstack_client.load_balancer.l7_rules(l7policy_id, project_id=project_id)
    except Exception as e:
        raise e
    return policies_rule_list


def l7rule_to_humanrule(l7rules):
    """
    reserial l7 rules to human rule
    :param l7rules:
    :return:[{"domain_name":"test.com","compare_type":"test"},
            {"url":"test", "compare_type":"start_with"}]

    """
    type_mapping = {"HOST_NAME": "domain_name",
                    "PATH": "url",
                    "COOKIE": "cookie"}
    rules = []
    for l7rule in l7rules:
        rule = {}
        rule[type_mapping.get(l7rule.type, l7rule.type)] = l7rule.rule_value
        rule['compare_type'] = l7rule.compare_type
        rules.append(rule)
    return rules


def pool_member_list(request, pool_id, project_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        pool_member_list = openstack_client.load_balancer.members(pool_id)
        members = []
        for member in pool_member_list:
            member_obj = {
                "monitor_port": member["monitor_port"],
                "project_id": member["project_id"],
                "name": member["name"],
                "weight": member["weight"],
                "backup": member["backup"],
                "admin_state_up": member["is_admin_state_up"],
                "subnet_id": member["subnet_id"],
                "created_at": member["created_at"],
                "provisioning_status": member["provisioning_status"],
                "monitor_address": member["monitor_address"],
                "updated_at": member["updated_at"],
                "address": member["address"],
                "protocol_port": member["protocol_port"],
                "id": member["id"],
                "operating_status": member["operating_status"],
            }
            vip_result = service_model.BmServiceFloatingIp.objects.filter(
                fixed_address=member["address"], instance_name=member["name"], is_measure_end=False,
                attached=True).first()
            member_obj["public_ip_adress"] = ""
            if vip_result:
                member_obj["public_ip_adress"] = vip_result.floating_ip
            members.append(member_obj)
    except Exception as e:
        raise e
    return members


def listener_detail(request, listener_id, pool_id):
    openstack_client = utils.get_openstack_client(request)

    try:
        listener_detail = openstack_client.load_balancer.get_listener(listener_id)
        name = listener_detail.name
        id = listener_detail.id
        protocol = listener_detail.protocol
        protocol_port = listener_detail.protocol_port
        created_at = listener_detail.created_at

        listener_detail = {
            'listener_name': name,
            'listener_id': id,
            'protocol': protocol,
            'port': protocol_port,
            'pool_id': pool_id,
            'created_at': created_at
        }

    except Exception as e:
        raise e
    return listener_detail


def policies_detail(request, l7policy_id):
    openstack_client = utils.get_openstack_client(request)

    try:
        policies_detail = openstack_client.load_balancer.get_l7_policy(l7policy_id)

    except Exception as e:
        raise e
    return policies_detail


def health_monitor_detail(request, healthmonitor_id):
    openstack_client = utils.get_openstack_client(request)
    try:
        health_monitor_detail = openstack_client.load_balancer.get_health_monitor(healthmonitor_id)
        health_monitor_detail = {
            'delay': health_monitor_detail.delay,
            'max_retries': health_monitor_detail.max_retries,
            'name': health_monitor_detail.name,
            'pool_id': health_monitor_detail.pools,
            'timeout': health_monitor_detail.timeout,
            'type': health_monitor_detail.type
        }
    except Exception as e:
        raise e
    return health_monitor_detail


def available_floating_ip_to_lb(request, openstack_client):
    try:
        floating_ip_list = openstack_client.network.ips()
        avaliable_ip_list = []
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        fip_querys = service_model.BmServiceFloatingIp.objects.filter(
            project_id=project_id, is_measure_end=False, attached=False).all()
        fip_ids = []
        for fip in floating_ip_list:
            fip_ids.append(fip.id)

        for fip in fip_querys:
            if fip.floating_ip_id in fip_ids:
                # TODO 共享带宽功能拥有后会做修改
                if fip.external_line_type == "three_line_ip":
                    qos_policy_type = "三线公网带宽"
                else:
                    qos_policy_type = '共享带宽'
                obj = {
                    "id": fip.floating_ip_id,
                    "floating_ip_address": fip.floating_ip,
                    "qos_policy_name": fip.qos_policy_name,
                    "attached": fip.attached,
                    "qos_policy_type": qos_policy_type
                }
                avaliable_ip_list.append(obj)

    except Exception as e:
        raise e

    return avaliable_ip_list


def available_pool_to_listener(request, openstack_client, loadbalancer_id=None, listener_protocol=None):
    try:
        pool_obj_list = openstack_client.load_balancer.pools(loadbalancer_id=loadbalancer_id)
        lb_health_monitor_obj = get_lb_health_monitor_obj(request)
        pool_list = []
        for pool_obj in pool_obj_list:
            if not pool_obj.listeners:
                if pool_obj.protocol == listener_protocol:
                    pool_detail_obj = {
                        "pool_name": pool_obj.name,
                        "pool_id": pool_obj.id,
                        "lb_algorithm": pool_obj.lb_algorithm,
                        "protocol": pool_obj.protocol,
                        "session_persistence": pool_obj.session_persistence,
                        "created_at": pool_obj.created_at,
                        "listener_name_list": [],
                        "listeners": pool_obj.listeners
                    }
                    ##获取监听器下的资源池的健康检查信息
                    if not pool_obj.health_monitor_id:
                        health_monitor_dict = {}
                        pool_detail_obj["health_monitor_obj"] = health_monitor_dict
                        pool_list.append(pool_detail_obj)
                        continue
                    health_monitor = lb_health_monitor_obj[pool_obj.health_monitor_id]
                    health_monitor_dict = {
                        "healthmonitor_id": health_monitor.id,
                        "healthmonitor_status": health_monitor.is_admin_state_up,
                        "max_retries": health_monitor.max_retries,
                        "delay": health_monitor.delay,
                        "max_retries_down": health_monitor.max_retries_down,
                        "timeout": health_monitor.timeout,
                        "url_path": health_monitor.url_path
                    }
                    pool_detail_obj["health_monitor_obj"] = health_monitor_dict
                    pool_list.append(pool_detail_obj)
    except Exception as e:
        raise e

    return pool_list


def get_firewall_rule(firewall_id):
    firewall_rules = []
    firewall = service_model.Firewalls.objects.get(id=firewall_id)
    firewall_rule_objects = firewall.firewallrule_set.all()
    for object in firewall_rule_objects:
        firewall_rules.append(object.to_dict())
    return firewall.to_dict(), firewall_rules


def pools_detail(request, pool_id, loadbalancer_id):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_health_monitor_obj = get_lb_health_monitor_obj(request)
        lb_listener_obj = get_lb_listener_obj(request, load_balancer_id=loadbalancer_id)
        lb_pool_dict = openstack_client.load_balancer.get_pool(pool_id)
        l7_policy = get_l7_policy_obj(request)
        pool_detail_obj = {
            "pool_name": lb_pool_dict.name,
            "pool_id": lb_pool_dict.id,
            "lb_algorithm": lb_pool_dict.lb_algorithm,
            "protocol": lb_pool_dict.protocol,
            "session_persistence": lb_pool_dict.session_persistence,
            "created_at": lb_pool_dict.created_at,
        }
        # 获取资源池下的监听器信息
        if lb_pool_dict.listeners and lb_listener_obj:
            listener_name_list = []
            for listener_id_obj in lb_pool_dict.listeners:
                listener_name_list.append(lb_listener_obj[listener_id_obj["id"]].name)
            pool_detail_obj["listener_name_list"] = listener_name_list
        else:
            pool_detail_obj["listener_name_list"] = []
        # 获取资源池下的健康检查信息
        if not lb_pool_dict.health_monitor_id:
            health_monitor_obj = {}
            pool_detail_obj["health_monitor_obj"] = health_monitor_obj
        else:
            if lb_health_monitor_obj:
                lb_health_monitor_dict = lb_health_monitor_obj[lb_pool_dict.health_monitor_id]
                health_monitor_dict = {
                    "healthmonitor_id": lb_health_monitor_dict.id,
                    "healthmonitor_status": lb_health_monitor_dict.is_admin_state_up,
                    "max_retries": lb_health_monitor_dict.max_retries,
                    "delay": lb_health_monitor_dict.delay,
                    "max_retries_down": lb_health_monitor_dict.max_retries_down,
                    "timeout": lb_health_monitor_dict.timeout,
                }
                pool_detail_obj["health_monitor_obj"] = health_monitor_dict
        # 获取pool所对应的转发策略
        l7_policy_id_list = []
        for l7_policy_id, l7_policy_value in l7_policy.items():
            l7_policy_id_list.append(l7_policy_id)
        if lb_pool_dict.id in l7_policy_id_list:
            pool_detail_obj["l7_policy"] = l7_policy[lb_pool_dict.id]
        else:
            pool_detail_obj["l7_policy"] = {}

    except Exception as e:
        raise e

    return pool_detail_obj


def attach_ip_lb(request, loadbalance_name=None, loadbalance_id=None, floating_ip_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        load_balancer_detail, load_balancer_status = lb_status_timeout(request, loadbalance_id)
        vip_port_id = load_balancer_detail["vip_port_id"]
        fixed_address = load_balancer_detail["vip_address"]
        # 查询弹性IP信息
        service_attach_obj = service_model.BmServiceFloatingIp.objects.get(floating_ip_id=floating_ip_id,
                                                                           status=auth_models.CONTRACT_AVTIVE,
                                                                           is_measure_end=False)
        if not service_attach_obj:
            raise Exception("Fail to find floating IP by id {floating_ip_id}. Result {service_attach_obj}".format(
                floating_ip_id=floating_ip_id,
                service_attach_obj=service_attach_obj))

        # 弹性IP挂载
        with transaction.atomic():
            # openstack进行弹性IP挂载
            if load_balancer_status == service_model.LB_ERROR:
                raise exc.LbError()
            openstack_client.network.update_ip(floating_ip_id, port_id=vip_port_id, fixed_ip_address=fixed_address)
            # 平台保存相关挂载数据信息
            if service_attach_obj:
                service_attach_obj.attached_type = service_model.FLOATINGIP_AATTACH_SLB
                service_attach_obj.attached = True
                service_attach_obj.instance_uuid = loadbalance_id
                service_attach_obj.instance_name = loadbalance_name
                service_attach_obj.fixed_address = fixed_address
                # service_attach_obj.update_at = datetime.datetime.now()
                service_attach_obj.save()
    except Exception as e:
        raise e
    return service_attach_obj


def lb_status_timeout(request, loadbalance_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        # 进行循环获取loadbalance的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            load_balancer_detail = openstack_client.load_balancer.get_load_balancer(loadbalance_id).to_dict()
            load_balancer_status = load_balancer_detail["provisioning_status"]
            if load_balancer_status == "ACTIVE" or load_balancer_status == "ERROR":
                break
            time.sleep(2)
    except Exception as e:
        raise e

    return load_balancer_detail, load_balancer_status


def dettach_ip_lb(request, loadbalance_id=None, floating_ip_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        load_balancer_detail, load_balancer_status = lb_status_timeout(request, loadbalance_id)
        # 查询弹性IP信息
        service_attach_obj = service_model.BmServiceFloatingIp.objects.get(floating_ip_id=floating_ip_id,
                                                                           instance_uuid=loadbalance_id,
                                                                           is_measure_end=False)
        if not service_attach_obj:
            raise Exception("Fail to find floating IP by id {floating_ip_id}. Result {service_attach_obj}".format(
                floating_ip_id=floating_ip_id,
                service_attach_obj=service_attach_obj))

        # 弹性IP解绑
        with transaction.atomic():
            # openstack进行弹性IP解绑
            if load_balancer_status == service_model.LB_ERROR:
                raise exc.LbError()
            openstack_client.network.update_ip(floating_ip_id, port_id=None)
            # 平台保存相关挂载数据信息
            service_attach_obj.attached_type = ""
            service_attach_obj.attached = False
            service_attach_obj.instance_uuid = ""
            service_attach_obj.instance_name = ""
            service_attach_obj.fixed_address = ""
            # service_attach_obj.update_at = datetime.datetime.now()
            service_attach_obj.save()
    except Exception as e:
        raise e

    return service_attach_obj


def policies_rule_detail(request, l7policy_id, l7rule_id):
    openstack_client = utils.get_openstack_client(request)
    try:
        policies_rule_detail = openstack_client.load_balancer.get_l7_rule(l7rule_id, l7policy_id)
    except Exception as e:
        raise e
    return policies_rule_detail


def pool_member_detail(request, pool_id, member_id):
    openstack_client = utils.get_openstack_client(request)
    try:

        pool_member_detail = openstack_client.load_balancer.get_member(member_id, pool_id)
        id = pool_member_detail.id
        name = pool_member_detail.name
        ip_address = pool_member_detail.address
        provisioning_status = pool_member_detail.provisioning_status
        protocol_port = pool_member_detail.protocol_port
        weight = pool_member_detail.weight
        pool_member_detail = {
            'pool_member_name': name,
            'pool_member_id': id,
            'address': ip_address,
            'provisioning_status': provisioning_status,
            'protocol_port': protocol_port,
            'weight': weight
        }
    except Exception as ex:
        raise ex
    return pool_member_detail


def load_balance_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    response_obj = ResponseObj()
    try:
        load_balances_generator = openstack_client.load_balancer.load_balancers(project_id=project_id)
        load_balances = []
        for load_balance_object in load_balances_generator:
            load_balances.append(load_balance_object.to_dict())
        load_balance_list = []
        listener_list_obj = get_lb_listener_list_obj(request)
        fip_list_obj = {}
        fips = openstack_client.network.ips(project_id=project_id)
        for fip in fips:
            if fip.port_id:
                fip_list_obj[fip.port_id] = fip
        for load_balance_deatil in load_balances:
            # 获取监听器列表
            listener_list = []
            for listener_id in load_balance_deatil["listeners"]:
                listener_detail_obj = {
                    "id": listener_list_obj[listener_id["id"]].id,
                    "listener_name": listener_list_obj[listener_id["id"]].name,
                    "protocol": listener_list_obj[listener_id["id"]].protocol,
                    "protocol_port": listener_list_obj[listener_id["id"]].protocol_port,
                }
                listener_list.append(listener_detail_obj)
            # 从数据库中拿取VPC得信息
            loadbalance_result = service_model.BmServiceLoadbalance.objects.filter(
                loadbalance_id=load_balance_deatil["id"]).first()
            if loadbalance_result:
                vpc_id = loadbalance_result.vpc_id
                contract_number = loadbalance_result.contract_number
                created_at = loadbalance_result.created_at
                flavor_id = loadbalance_result.flavor_id
            else:
                vpc_id = ""
                flavor_id = ""
                contract_number = ""
                created_at = swift_handler.utctime_to_localtime(load_balance_deatil["created_at"],
                                                                utc_format='%Y-%m-%dT%H:%M:%S')
            # 从数据库中拿对应的Flavor信息
            if flavor_id:
                flavor_obj = service_model.BmServiceLoadbalanceFlavor.objects.filter(
                    id=flavor_id).first()
            else:
                flavor_obj = {}
            vpc_name = ""
            if vpc_id:
                vpc_result = service_model.BmVpc.objects.filter(
                    id=vpc_id).first()
                if vpc_result:
                    vpc_name = vpc_result.vpc_name
            public_ip_adress = ""
            public_ip_id = ""
            fip_info = fip_list_obj.get(load_balance_deatil['vip_port_id'])
            if fip_info:
                public_ip_adress = fip_info.floating_ip_address
                public_ip_id = fip_info.id

            load_balances_obj = {
                "flavor_id": flavor_id,
                "flavor_obj": flavor_obj,
                "vpc_id": vpc_id,
                "id": load_balance_deatil["id"],
                "name": load_balance_deatil["name"],
                "vpc_name": vpc_name,
                "public_ip_adress": public_ip_adress,
                "public_ip_id": public_ip_id,
                "listener_list": listener_list,
                "created_at": created_at,
                "operating_status": load_balance_deatil["operating_status"],
                "project_id": load_balance_deatil["project_id"],
                "provisioning_status": load_balance_deatil["provisioning_status"],
                "vip_address": load_balance_deatil["vip_address"],
                "vip_network_id": load_balance_deatil["vip_network_id"],
                "vip_port_id": load_balance_deatil["vip_port_id"],
                "vip_qos_policy_id": load_balance_deatil["vip_qos_policy_id"],
                "vip_subnet_id": load_balance_deatil["vip_subnet_id"]
            }
            # 添加合同信息
            contract_obj = service_model.BmContract.objects.filter(
                contract_number=contract_number,
                status="active")
            if contract_obj:
                load_balances_obj["contract_info"] = contract_obj.first()
            else:
                load_balances_obj["contract_info"] = {}
            load_balance_list.append(load_balances_obj)

    except Exception as e:
        raise e

    return response_obj.json_serial(load_balance_list)


def create_load_balancers(request, project_id=None, vip_network_id=None, name=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        load_balancer = openstack_client.load_balancer.create_load_balancer(project_id=project_id,
                                                                            vip_network_id=vip_network_id,
                                                                            name=name)
    except Exception as ex:
        raise ex
    return load_balancer.to_dict()


def create_listener(request, insert_headers=None, loadbalancer_id=None, name=None, protocol=None, protocol_port=None,
                    timeout_member_connect=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        # To create a listener, the parent load balancer must have an ACTIVE provisioning status.
        details, status = load_balancer_status_verify(openstack_client, loadbalancer_id)
        dict_attrs = {
            'loadbalancer_id': loadbalancer_id,
            'name': name,
            'protocol': protocol,
            'protocol_port': protocol_port,
            'timeout_member_connect': timeout_member_connect
        }
        if protocol == 'HTTP' or protocol == 'HTTPS':
            dict_attrs = {
                'loadbalancer_id': loadbalancer_id,
                'name': name,
                'insert_headers': insert_headers,
                'protocol': protocol,
                'protocol_port': protocol_port,
                'timeout_member_connect': timeout_member_connect
            }
        load_balances_listener = openstack_client.load_balancer.create_listener(**dict_attrs)

        local_created_time = swift_handler.utctime_to_localtime(load_balances_listener.created_at,
                                                                utc_format='%Y-%m-%dT%H:%M:%S')
        listener_detail = {
            'listener_name': load_balances_listener.name,
            'listener_id': load_balances_listener.id,
            'protocol': load_balances_listener.protocol,
            'protocol_port': load_balances_listener.protocol_port,
            'created_at': local_created_time,
            'timeout_member_connect': load_balances_listener.timeout_member_connect
        }
        if protocol == 'HTTP' or protocol == 'HTTPS':
            listener_detail = {
                'listener_name': load_balances_listener.name,
                'listener_id': load_balances_listener.id,
                'insert_headers': load_balances_listener.insert_headers,
                'protocol': load_balances_listener.protocol,
                'protocol_port': load_balances_listener.protocol_port,
                'created_at': local_created_time,
                'timeout_member_connect': load_balances_listener.timeout_member_connect
            }
    except Exception as ex:
        raise ex
    return listener_detail


def create_listener_sni(request, default_tls_container_ref=None,
                        loadbalancer_id=None, name=None,
                        sni_container_refs=None, protocol=None,
                        protocol_port=None, timeout_member_connect=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        details, status = load_balancer_status_verify(openstack_client, loadbalancer_id)
        dict_attrs = {
            'default_tls_container_ref': default_tls_container_ref,
            'loadbalancer_id': loadbalancer_id,
            'name': name,
            'sni_container_refs': sni_container_refs,
            'protocol': protocol,
            'protocol_port': protocol_port,
            'timeout_member_connect': timeout_member_connect
        }
        load_balances_listener = openstack_client.load_balancer.create_listener(**dict_attrs)

        listener_detail = {
            'listener_name': load_balances_listener.name,
            'listener_id': load_balances_listener.id,
            'protocol': load_balances_listener.protocol,
            'port': load_balances_listener.protocol_port,
            'default_tls_container_ref': default_tls_container_ref,
            'sni_container_refs': sni_container_refs,
            'timeout_member_connect': timeout_member_connect,
            'created_at': load_balances_listener.created_at
        }
    except Exception as ex:
        raise ex
    return listener_detail


def secret_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    secret = barbican.secrets.list()
    name_list = []
    total = 0
    for sec in secret:
        name = sec.name
        created_at = sec.created
        payload = sec.payload
        status = sec.status
        dict_secret = {
            'name': name,
            'created_at': created_at,
            'payload': payload,
            'status': status
        }
        name_list.append(dict_secret)
        total += 1
    # quotas_list('secret', total)
    return name_list


# TODO
def quotas_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    secret_quotas = barbican.project_quota.list(project_id=project_id)
    quotas_list = []
    # try:
    #     for quo in secret_quotas:
    #         id = quo.id
    #         secrets = quo.secrets
    #         orders = quo.orders
    #         containers = quo.containers
    #         dict_secret = {
    #             'project_id': id,
    #             'project_quotas': {
    #                 "secrets": secrets,
    #                 "orders": orders,
    #                 "containers": containers
    #             }
    #         }
    #         quotas_list.append(dict_secret)
    # except Exception as e:
    #     raise e
    # resp = barbican.common.quota.QuotaDriver().get_quotas(project_id)
    # return resp


def certificates_list(request, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    try:
        containers_list = barbican.containers.list()
        ctn_list = []
        total = 0
        for ctn in containers_list:
            name = ctn.name
            created_at = ctn.created
            container_ref = ctn.container_ref
            scheme, uri, domain, version, service, uuid = container_ref.split('/', 5)
            current_container = barbican.containers.get(container_ref)
            if current_container is CertificateContainer:
                type = 'certificate'
            elif current_container is RSAContainer:
                type = 'RSA'
            else:
                type = ''
            dict_container = {
                'name': name,
                'created_at': created_at,
                'domain': domain,
                'container_type': type
            }
            ctn_list.append(dict_container)
            total += 1
    except Exception as e:
        raise e
    # quotas_list('container', total)
    return ctn_list, total


def create_sni_crt(request, crt_name=None, crt_type=None, crt_contents=None, secret_key=None, crt_domain=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    if crt_type == 'CA':
        dict_attrs = {
            'crt_name': crt_name,
            'crt_type': crt_type,
            'crt_contents': crt_contents
        }
    elif crt_type == 'Server':
        dict_attrs = {
            'crt_name': crt_name,
            'crt_type': crt_type,
            'crt_contents': crt_contents,
            'secret_key': secret_key,
            'crt_domain': crt_domain
        }
    else:
        pass
    meta = {
        "name": crt_name,
        "algorithm": "AES",
        "bit_length": 256,
        "mode": "cbc",
        "payload_content_type": "application/octet-stream"
    }
    # cert = barbican.orders.create(type="key", meta=meta)
    cert = barbican.orders.create(type="certificate", name=crt_name)
    cert_details = cert.order_ref
    return cert_details


# TODO
def create_certificate(request, crt_name=None, crt_type=None, crt_contents=None, secret_key=None, crt_domain=None,
                       project_id=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    dict_attrs = {
        'crt_name': crt_name,
        'crt_type': crt_type,
        'crt_contents': crt_contents,
        'secret_key': secret_key,
        'crt_domain': crt_domain
    }

    if crt_type == 'certificate':
        # openssl pkcs12 -export -inkey $DOMAIN1.key -in $DOMAIN1.crt -certfile ca.crt -passout pass: -out $DOMAIN1.p12
        # p12 = OpenSSL.crypto.load_pkcs12()
        # p12.get_certificate()  # signed certificate object
        # p12.get_privatekey()  # private key
        # p12.get_ca_certificates()  # ca chain
        cert = ssl.get_server_certificate()
        # x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        # x509.get_subject().get_components()

        # create_certificate(name=None, request_type=None, subject_dn=None, source_container_ref=None, ca_id=None, profile=None, request_data=None)
        cur_order = barbican.orders.create_certificate()
        cur_order.name = crt_name
        # create container
        container = barbican.containers.create(certificate=crt_contents, private_key=secret_key)
        cur_order.source_container_ref = container
        cur_order_ref = cur_order.submit()
        retrieved_order = barbican.orders.get(cur_order_ref)
        res = retrieved_order
    elif crt_type == 'key':
        # create_key(name=None, algorithm=None, bit_length=None, mode=None, payload_content_type=None, expiration=None)¶
        cur_order = barbican.orders.create_key()
        cur_order.name = crt_name
        cur_order.algorithm = 'AES'
        cur_order.mode = 'CBC'
        cur_order.bit_length = 256
        cur_order_ref = cur_order.submit()
        retrieved_order = barbican.orders.get(cur_order_ref)
        res = retrieved_order
        # cert_details = cert.order_ref
    else:
        pass
    return {'secret_href': res}


def create_secret(request, crt_name=None, crt_contents=None, project_id=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    # CONTENT TYPE: (str) application/json, (default: bytes) application/octet-stream
    secret = barbican.secrets.create(name=crt_name,
                                     payload=crt_contents)
    secret.store()
    secret_ref = secret.secret_ref
    return {'secret_href': secret_ref}


# TODO
def update_certificate(request, crt_name=None, crt_domain=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    # CONTENT TYPE: (str) application/json, (default: bytes) application/octet-stream
    # secret = barbican.secrets.update(payload=crt_contents)
    # secret.store()
    # secret_ref = secret.secret_ref
    # return {'secret_href': secret_ref}


def delete_certificate(request, certificate_id=None, domain=None):
    openstack_client = utils.get_openstack_client(request)
    barbican = client.Client(session=openstack_client.session)
    try:
        scheme = 'http:'
        uri = '/'
        version = 'v1'
        service = 'containers'
        container_ref = scheme + '/' + uri + '/' + domain + '/' + version + '/' + service + '/' + certificate_id
        containers_list = barbican.containers.delete(container_ref)
    except Exception as e:
        raise e
    return containers_list


def create_policies(request, name=None, action=None, listener_id=None, redirect_pool_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        currect_listener = listener_status_verify(openstack_client, listener_id)
        listener_protocol = currect_listener["protocol"]
        currect_pool, currect_pool_status = pool_status_verify(request, redirect_pool_id)
        pool_protocol = currect_pool["protocol"]
        if pool_protocol is 'UDP':
            raise Exception("Pool of type UDP cannot be used in L7 policies at this time!")

        # listener与pool的协议映射需遵循Openstack官方文档要求
        if listener_protocol == 'HTTP' and pool_protocol == 'HTTP':
            load_balancer_policies = openstack_client.load_balancer.create_l7_policy(name=name,
                                                                                     action=action,
                                                                                     listener_id=listener_id,
                                                                                     redirect_pool_id=redirect_pool_id)
        elif listener_protocol == 'HTTPS' and pool_protocol == 'HTTPS':
            load_balancer_policies = openstack_client.load_balancer.create_l7_policy(name=name,
                                                                                     action=action,
                                                                                     listener_id=listener_id,
                                                                                     redirect_pool_id=redirect_pool_id)
        else:
            raise exc.L7PolicyCreateProtocolError()
    except Exception as ex:
        raise ex
    return load_balancer_policies


def create_pools(request, name=None, lb_algorithm=None, protocol=None, project_id=None, loadbalancer_id=None,
                 listener_id=None,
                 session_persistence=None, is_keep_session=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        # 进行循环获取loadbalance的状态
        load_balancer_detail, load_balancer_status = lb_status_timeout(request, loadbalancer_id)
        if is_keep_session:
            # 判断是否满足正则匹配
            if session_persistence["type"] == "APP_COOKIE":
                if not session_persistence["cookie_name"]:
                    raise exc.FormatError()
                cookie_name = session_persistence["cookie_name"]
                bad_cookie_name = re.compile(r'[\x00-\x20\x22\x28-\x29\x2c\x2f'
                                             r'\x3a-\x40\x5b-\x5d\x7b\x7d\x7f]+')
                valid_chars = re.compile(r'[\x00-\xff]+')
                if (bad_cookie_name.search(cookie_name) or
                        not valid_chars.search(cookie_name)):
                    raise exc.FormatError()
            load_balancer_pool = openstack_client.load_balancer.create_pool(
                name=name,
                lb_algorithm=lb_algorithm,
                protocol=protocol, project_id=project_id, loadbalancer_id=loadbalancer_id, listener_id=listener_id,
                session_persistence=session_persistence).to_dict()
        else:
            load_balancer_pool = openstack_client.load_balancer.create_pool(
                name=name,
                lb_algorithm=lb_algorithm,
                protocol=protocol, project_id=project_id, loadbalancer_id=loadbalancer_id,
                listener_id=listener_id).to_dict()

        # 查询对应数据
        if not load_balancer_pool:
            raise exc.PoolError()
        listeners = load_balancer_pool["listeners"]
        listener_name_list = []
        for listener in listeners:
            listener_detail = openstack_client.load_balancer.get_listener(listener["id"]).to_dict()
            if not listener_detail:
                raise exc.ListenerError()
            listener_name_list.append(listener_detail["name"])
        # 获取健康检查状态
        healthmonitor_id = load_balancer_pool.get("health_monitor_id")
        health_monitor_obj = {}
        if healthmonitor_id:
            healthmonitor_detail = openstack_client.load_balancer.get_health_monitor(
                healthmonitor_id).to_dict()
            if not healthmonitor_detail:
                raise exc.HealthmonitorError()
            health_monitor_obj = {
                "healthmonitor_id": healthmonitor_id,
                "healthmonitor_status": healthmonitor_detail["is_admin_state_up"],
                "max_retries": healthmonitor_detail["max_retries"],
                "delay": healthmonitor_detail["delay"],
                "max_retries_down": healthmonitor_detail["max_retries_down"],
                "timeout": healthmonitor_detail["timeout"],
            }

        # 数据处理
        local_created_time = swift_handler.utctime_to_localtime(load_balancer_pool["created_at"],
                                                                utc_format='%Y-%m-%dT%H:%M:%S')
        pool_detail_obj = {
            "pool_name": load_balancer_pool["name"],
            "pool_id": load_balancer_pool["id"],
            "lb_algorithm": load_balancer_pool["lb_algorithm"],
            "protocol": load_balancer_pool["protocol"],
            "session_persistence": load_balancer_pool["session_persistence"],
            "created_at": local_created_time,
            "listener_name_list": listener_name_list,
            "health_monitor_obj": health_monitor_obj,
            "provisioning_status": load_balancer_pool["provisioning_status"],
            "members": load_balancer_pool["members"],
            "operating_status": load_balancer_pool["operating_status"]
        }
    except Exception as ex:
        raise ex
    return pool_detail_obj


def create_health_monitor(request, delay=None, max_retries=None, pool_id=None, timeout=None, type=None, url_path=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        # To create a health monitor, the parent load balancer must have an ACTIVE provisioning status.
        pool_detail, pool_status = pool_status_verify(request, pool_id)

        dict_attrs = {
            'delay': delay,
            'max_retries': max_retries,
            'pool_id': pool_id,
            'timeout': timeout,
            'type': type
        }
        if type == 'HTTP':
            dict_attrs = {
                'delay': delay,
                'max_retries': max_retries,
                'pool_id': pool_id,
                'timeout': timeout,
                'type': type,
                'url_path': url_path
            }
        load_balancer_health_monitor = openstack_client.load_balancer.create_health_monitor(**dict_attrs)

        if load_balancer_health_monitor:
            health_monitor_detail = {
                'delay': load_balancer_health_monitor.delay,
                'max_retries': load_balancer_health_monitor.max_retries,
                'pool_id': load_balancer_health_monitor.pool_id,
                'provisioning_status': load_balancer_health_monitor.provisioning_status,
                'timeout': load_balancer_health_monitor.timeout,
                'type': load_balancer_health_monitor.type,
                'healthmonitor_id': load_balancer_health_monitor.id
            }

            if load_balancer_health_monitor.type == "HTTP":
                health_monitor_detail["url_path"] = load_balancer_health_monitor.url_path
                health_monitor_detail['expected_codes'] = load_balancer_health_monitor.expected_codes
    except Exception as ex:
        raise ex
    return health_monitor_detail


def create_policies_rule(request, l7policy_id, compare_type=None, type=None, value=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        dict_attr = {
            'compare_type': compare_type,
            'type': type,
            'value': value
        }
        policies_result = openstack_client.load_balancer.get_l7_policy(l7policy_id)
        if not policies_result:
            raise Exception("ID 为 %s 的策略不存在！" % l7policy_id)

        policy_status_verify(openstack_client, l7policy_id)

        load_balancer_policies_rule = openstack_client.load_balancer.create_l7_rule(l7policy_id, **dict_attr)
    except Exception as ex:
        raise exc.L7RuleCreateError()
    return load_balancer_policies_rule


def create_pool_member(request, pool_id, name=None, address=None, protocol_port=None, weight=None, instance_id=None,
                       loadbancer_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        # To create a member, the load balancer must have an ACTIVE provisioning status.
        pool_detail, pool_status = pool_status_verify(request, pool_id)
        current_pool = pool_detail

        dict_attrs = {
            'name': name,
            'address': address,
            'protocol_port': protocol_port,
            'weight': weight
        }
        load_balancer_pool_member = openstack_client.load_balancer.create_member(pool_id, **dict_attrs)
        # 成员添加成功，增加mapping 关系
        server_mapping_dict = {
            "instance_id": instance_id,
            "pool_id": pool_id,
            "loadbancer_id": loadbancer_id,
            "member_id": load_balancer_pool_member.id
        }
        mapping_result = service_model.BmInstanceMemberMapping.objects.create(**server_mapping_dict)
        if not mapping_result:
            raise exc.DataIntoSqlError()

    except Exception as ex:
        LOG.error(str(ex))
        raise ex
    return current_pool, load_balancer_pool_member


def update_listener(request, listener_id=None, listener_name=None, default_pool_id=None, timeout_member_connect=None,
                    insert_headers=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        current_listener = listener_status_verify(openstack_client, listener_id)
        dict_attrs = {
            'name': listener_name,
            'timeout_member_connect': timeout_member_connect,
            'default_pool_id': default_pool_id,
            'insert_headers': insert_headers
        }
        load_balances_listener = openstack_client.load_balancer.update_listener(listener_id, **dict_attrs)
        result = {
            'listener_name': load_balances_listener.name,
            'listener_id': load_balances_listener.id,
            'default_pool_id': load_balances_listener.default_pool_id,
            'protocol': load_balances_listener.protocol,
            'port': load_balances_listener.protocol_port,
            'created_at': load_balances_listener.created_at,
            'timeout_member_connect': load_balances_listener.timeout_member_connect
        }
        if load_balances_listener.protocol == 'HTTP' or load_balances_listener.protocol == 'HTTPS':
            result = {
                'listener_name': load_balances_listener.name,
                'listener_id': load_balances_listener.id,
                'insert_headers': load_balances_listener.insert_headers,
                'default_pool_id': load_balances_listener.default_pool_id,
                'protocol': load_balances_listener.protocol,
                'port': load_balances_listener.protocol_port,
                'created_at': load_balances_listener.created_at,
                'timeout_member_connect': load_balances_listener.timeout_member_connect
            }
    except Exception as ex:
        raise ex
    return result


def update_policies(request, l7policy_id=None, action=None, redirect_pool_id=None, name=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        pool_dict, pool_status = pool_status_verify(request, redirect_pool_id)
        policy_dict = policy_status_verify(openstack_client, l7policy_id)

        dict_attr = {
            'action': action,
            'redirect_pool_id': redirect_pool_id,
            'name': name
        }
        load_balances_policies = openstack_client.load_balancer.update_l7_policy(l7policy_id, **dict_attr)
    except Exception as ex:
        raise ex
    return load_balances_policies


def update_health_monitor(request, healthmonitor_id=None, pool_id=None, delay=None, max_retries=None, timeout=None,
                          url_path=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        details, status = health_monitor_status_verify(openstack_client, healthmonitor_id)
        dict_attrs = {
            'delay': delay,
            'max_retries': max_retries,
            'timeout': timeout
        }
        if details["type"] == 'HTTP':
            pattern_url_path = r'^((\/)|(\/[^/]+)+)$'
            match_url_path = re.match(pattern_url_path, url_path, re.I)
            if match_url_path is None:
                raise exc.HealthMonitorUrlError()
            if isinstance(url_path, str) and url_path.startswith('/'):
                dict_attrs = {
                    'delay': delay,
                    'max_retries': max_retries,
                    'timeout': timeout,
                    'url_path': url_path
                }
        load_balances_health_monitor = openstack_client.load_balancer.update_health_monitor(healthmonitor_id,
                                                                                            **dict_attrs)
        load_balances_health_monitor_detail = {
            'delay': load_balances_health_monitor.delay,
            'healthmonitor_id': healthmonitor_id,
            'max_retries': load_balances_health_monitor.max_retries,
            'pool_id': pool_id,
            'timeout': load_balances_health_monitor.timeout
        }
        if load_balances_health_monitor.type == 'HTTP':
            load_balances_health_monitor_detail = {
                'delay': load_balances_health_monitor.delay,
                'healthmonitor_id': healthmonitor_id,
                'max_retries': load_balances_health_monitor.max_retries,
                'pool_id': pool_id,
                'timeout': load_balances_health_monitor.timeout,
                'url_path': load_balances_health_monitor.url_path
            }
    except Exception as ex:
        raise ex
    return load_balances_health_monitor_detail


def update_pools(request, pool_id=None, name=None, is_keep_session=False, session_persistence=None, lb_algorithm=None,
                 loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)

    try:
        # 进行pool状态得判断
        pool_detail, pool_status = pool_status_timeout(request, pool_id)
        #
        # 针对是否开启会话保持做不同得处
        if not is_keep_session:
            session_persistence = None
        else:
            # 判断是否满足正则匹配
            if session_persistence["type"] == "APP_COOKIE":
                if not session_persistence["cookie_name"]:
                    raise exc.FormatError()
                cookie_name = session_persistence["cookie_name"]
                bad_cookie_name = re.compile(r'[\x00-\x20\x22\x28-\x29\x2c\x2f'
                                             r'\x3a-\x40\x5b-\x5d\x7b\x7d\x7f]+')
                valid_chars = re.compile(r'[\x00-\xff]+')
                if (bad_cookie_name.search(cookie_name) or
                        not valid_chars.search(cookie_name)):
                    raise exc.FormatError()
        load_balances_pools = openstack_client.load_balancer.update_pool(pool_id, name=name,
                                                                         session_persistence=session_persistence,
                                                                         lb_algorithm=lb_algorithm)

        lb_health_monitor_obj = get_lb_health_monitor_obj(request)

        lb_listener_obj = get_lb_listener_obj(request, load_balancer_id=loadbalancer_id)

        l7_policy = get_l7_policy_obj(request)

        pool_detail_obj = {
            "pool_name": load_balances_pools.name,
            "pool_id": load_balances_pools.id,
            "lb_algorithm": load_balances_pools.lb_algorithm,
            "protocol": load_balances_pools.protocol,
            "session_persistence": load_balances_pools.session_persistence,
            "created_at": load_balances_pools.created_at,
        }
        # 获取资源池下的监听器信息
        if load_balances_pools.listeners and lb_listener_obj:
            listener_name_list = []
            for listener_id_obj in load_balances_pools.listeners:
                listener_name_list.append(lb_listener_obj[listener_id_obj["id"]].name)
            pool_detail_obj["listener_name_list"] = listener_name_list
        else:
            pool_detail_obj["listener_name_list"] = []
        # 获取资源池下的健康检查信息
        if not load_balances_pools.health_monitor_id:
            health_monitor_obj = {}
            pool_detail_obj["health_monitor_obj"] = health_monitor_obj
        else:
            lb_health_monitor_dict = lb_health_monitor_obj[load_balances_pools.health_monitor_id]
            health_monitor_dict = {
                "healthmonitor_id": lb_health_monitor_dict.id,
                "healthmonitor_status": lb_health_monitor_dict.is_admin_state_up,
                "max_retries": lb_health_monitor_dict.max_retries,
                "delay": lb_health_monitor_dict.delay,
                "max_retries_down": lb_health_monitor_dict.max_retries_down,
                "timeout": lb_health_monitor_dict.timeout,
            }
            pool_detail_obj["health_monitor_obj"] = health_monitor_dict
        # # 获取pool所对应的转发策略
        l7_policy_id_list = []
        for l7_policy_id, l7_policy_value in l7_policy.items():
            l7_policy_id_list.append(l7_policy_id)
        if load_balances_pools.id in l7_policy_id_list:
            pool_detail_obj["l7_policy"] = l7_policy[load_balances_pools.id]
        else:
            pool_detail_obj["l7_policy"] = {}
    except Exception as ex:
        raise ex
    return pool_detail_obj


def update_policies_rule(request, l7policy_id=None, l7rule_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        load_balances_policies_rule = openstack_client.load_balancer.update_l7_rule(l7policy_id, l7rule_id)
    except Exception as ex:
        raise ex
    return load_balances_policies_rule


def update_pool_member(request, pool_id=None, member_id=None, weight=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        details, status = pool_member_status_verify(openstack_client, member_id, pool_id)
        dict_attrs = {
            # 'monitor_port': monitor_port,
            'weight': weight
        }
        load_balances_pool_member = openstack_client.load_balancer.update_member(member_id, pool_id, **dict_attrs)
    except Exception as ex:
        raise ex
    return load_balances_pool_member


def delete_listener(request, listener_id=None):
    openstack_client = utils.get_openstack_client(request)
    response_obj = ResponseObj()

    # 删除监听器：与负载均衡实例解绑，与资源池解绑”
    try:
        current_listener = listener_status_verify(openstack_client, listener_id)
        if current_listener.protocol == 'HTTP' or current_listener.protocol == 'HTTPS':
            if current_listener.l7_policies:
                raise exc.L7PolicyError()
        result = openstack_client.load_balancer.delete_listener(current_listener.id)

        # Delete result verification
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 30:
                raise exc.TimeoutError()
            try:
                deleted_listener_verify = openstack_client.load_balancer.get_listener(listener_id).to_dict()
                time.sleep(2)
            except Exception as ex:
                response_obj.json_serial("底层监听器删除成功!")
                break
    except Exception as ex:
        raise ex
    return result


def delete_policies(request, l7policy_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        policy_dict = policy_status_verify(openstack_client, l7policy_id)
        load_balances_policies = openstack_client.load_balancer.delete_l7_policy(l7policy_id)
    except Exception as ex:
        raise ex
    return load_balances_policies


def delete_health_monitor(request, healthmonitor_id=None):
    openstack_client = utils.get_openstack_client(request)
    response_obj = ResponseObj()
    try:
        details, status = health_monitor_status_verify(openstack_client, healthmonitor_id)
        load_balances_health_monitor = openstack_client.load_balancer.delete_health_monitor(healthmonitor_id)

        # Delete result verification
        while True:
            try:
                deleted_health_monitor_verify = openstack_client.load_balancer.get_health_monitor(
                    healthmonitor_id).to_dict()
                time.sleep(2)
            except Exception as ex:
                response_obj.json_serial("关闭health monitor成功！")
                break
    except Exception as ex:
        raise ex
    return load_balances_health_monitor


def pool_status_timeout(request, pool_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        # 进行循环获取pool的状态
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 10:
                raise exc.TimeoutError()
            pool_detail = openstack_client.load_balancer.get_pool(pool_id).to_dict()
            pool_status = pool_detail["provisioning_status"]
            if pool_status == "ACTIVE" or pool_status == "ERROR":
                break
            time.sleep(2)
    except Exception as e:
        raise e

    return pool_detail, pool_status


def delete_pools(request, pool_id=None):
    openstack_client = utils.get_openstack_client(request)
    response_obj = ResponseObj()
    try:
        pool_detail, pool_status = pool_status_timeout(request, pool_id)
        pool_delete_detail = openstack_client.load_balancer.delete_pool(pool_id)
        begin_time = time.time()
        while True:
            try:
                end_time = time.time()
                run_time = end_time - begin_time
                if run_time > 5:
                    raise exc.TimeoutError()
                pool_detail = openstack_client.load_balancer.get_pool(pool_id).to_dict()
                time.sleep(2)
            except Exception as ex:
                response_obj.json_serial("删除pool成功")
                break
    except Exception as ex:
        raise ex
    return response_obj.json_serial("删除Pool成功")


def delete_policies_rule(request, l7policy_id=None, l7rule_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        load_balances_policies_rule = openstack_client.load_balancer.delete_l7_rule(l7policy_id, l7rule_id)
    except Exception as ex:
        raise ex
    return load_balances_policies_rule


def delete_pool_member(request, pool_id, member_id):
    response_obj = ResponseObj()
    openstack_client = utils.get_openstack_client(request)
    try:
        details, status = pool_member_status_verify(openstack_client, member_id, pool_id)
        load_balances_pool_member = openstack_client.load_balancer.delete_member(member_id, pool_id)

        # Delete result verification
        begin_time = time.time()
        while True:
            end_time = time.time()
            run_time = end_time - begin_time
            if run_time > 12:
                raise exc.TimeoutError()
                break
            try:
                deleted_pool_member_verify = openstack_client.load_balancer.get_member(member_id, pool_id).to_dict()
                time.sleep(2)
            except Exception as ex:
                response_obj.json_serial("删除member成功")
                break
        # 成员移除成功，删除mapping 关系
        mapping_result = service_model.BmInstanceMemberMapping.objects.filter(pool_id=pool_id,
                                                                              member_id=member_id).delete()
    except Exception as ex:
        raise ex
    return load_balances_pool_member


def get_lb_pool_detail(request, lb_health_monitor_obj=None,
                       lb_pool_obj=None, lb_listener_obj=None, l7_policy=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_pool_list = []
        for lb_pool_obj_key, lb_pool_obj_value in lb_pool_obj.items():
            pool_detail_obj = {
                "pool_name": lb_pool_obj_value.name,
                "pool_id": lb_pool_obj_value.id,
                "lb_algorithm": lb_pool_obj_value.lb_algorithm,
                "protocol": lb_pool_obj_value.protocol,
                "session_persistence": lb_pool_obj_value.session_persistence,
                "created_at": lb_pool_obj_value.created_at
            }
            # 获取pool所对应的转发策略
            l7_policy_id_list = []
            for l7_policy_id, l7_policy_value in l7_policy.items():
                l7_policy_id_list.append(l7_policy_id)
            if lb_pool_obj_value.id in l7_policy_id_list:
                pool_detail_obj["l7_policy"] = l7_policy[lb_pool_obj_value.id]
            else:
                pool_detail_obj["l7_policy"] = {}
            # 获取资源池下的监听器信息
            if lb_pool_obj_value.listeners:
                listener_name_list = []
                pool_listener_name_list = []
                for listener_id_obj in lb_pool_obj_value.listeners:
                    listener_name_list.append(lb_listener_obj[listener_id_obj["id"]].name)
                    pool_listener_name_list.append(lb_listener_obj[listener_id_obj["id"]].name)
                pool_detail_obj["pool_listener_name_list"] = pool_listener_name_list
            else:
                pool_detail_obj["pool_listener_name_list"] = []

            # 获取资源池下所绑定的转发策略所对应的监听器信息
            if pool_detail_obj["l7_policy"]:
                listener_name = lb_listener_obj[pool_detail_obj["l7_policy"]["listener_id"]].name
                if listener_name not in listener_name_list:
                    listener_name_list.append(listener_name)
                pool_detail_obj["listener_name_list"] = listener_name_list
            else:
                pool_detail_obj["listener_name_list"] = pool_detail_obj["pool_listener_name_list"]

            # 获取资源池下的健康检查信息
            if not lb_pool_obj_value.health_monitor_id:
                health_monitor_obj = {}
                pool_detail_obj["health_monitor_obj"] = health_monitor_obj
                lb_pool_list.append(pool_detail_obj)
                continue
            lb_health_monitor_dict = lb_health_monitor_obj[lb_pool_obj_value.health_monitor_id]
            health_monitor_dict = {
                "healthmonitor_id": lb_health_monitor_dict.id,
                "healthmonitor_status": lb_health_monitor_dict.is_admin_state_up,
                "max_retries": lb_health_monitor_dict.max_retries,
                "delay": lb_health_monitor_dict.delay,
                "max_retries_down": lb_health_monitor_dict.max_retries_down,
                "timeout": lb_health_monitor_dict.timeout,
            }
            pool_detail_obj["health_monitor_obj"] = health_monitor_dict
            lb_pool_list.append(pool_detail_obj)

    except Exception as ex:
        raise ex
    return lb_pool_list


def get_lb_listener_detail(request, health_monitor_obj=None,
                           pool_obj=None, listener_obj=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_listener_list = []
        for lb_listener_obj_key, lb_listener_obj_value in listener_obj.items():
            pool_list = []
            listener_detail_obj = {
                "listener_name": lb_listener_obj_value.name,
                "listener_id": lb_listener_obj_value.id,
                "protocol": lb_listener_obj_value.protocol,
                "protocol_port": lb_listener_obj_value.protocol_port,
                "created_at": lb_listener_obj_value.created_at,
                "sni_container_refs": lb_listener_obj_value.sni_container_refs,
                "insert_headers": lb_listener_obj_value.insert_headers,
                "l7_policies": lb_listener_obj_value.l7_policies,
                "timeout_member_connect": lb_listener_obj_value.timeout_member_connect,
                "timeout_client_data": lb_listener_obj_value.timeout_client_data,
                "timeout_member_data": lb_listener_obj_value.timeout_member_data,
                "timeout_tcp_inspect": lb_listener_obj_value.timeout_tcp_inspect,
                "connection_limit": lb_listener_obj_value.connection_limit
            }
            # 获取监听器下的资源池信息
            if not lb_listener_obj_value.default_pool_id:
                listener_detail_obj["pool_list"] = pool_list
                lb_listener_list.append(listener_detail_obj)
                continue
            pool_detail_obj = {
                "pool_name": pool_obj[lb_listener_obj_value.default_pool_id].name,
                "pool_id": pool_obj[lb_listener_obj_value.default_pool_id].id,
                "lb_algorithm": pool_obj[lb_listener_obj_value.default_pool_id].lb_algorithm,
                "protocol": pool_obj[lb_listener_obj_value.default_pool_id].protocol,
                "session_persistence": pool_obj[lb_listener_obj_value.default_pool_id].session_persistence,
                "created_at": pool_obj[lb_listener_obj_value.default_pool_id].created_at
            }
            ##获取监听器下的资源池的监听器信息
            if pool_obj[lb_listener_obj_value.default_pool_id].listeners:
                listener_name_list = []
                for listener_id_obj in pool_obj[lb_listener_obj_value.default_pool_id].listeners:
                    listener_name_list.append(listener_obj[listener_id_obj["id"]].name)
                pool_detail_obj["listener_name_list"] = listener_name_list
            else:
                pool_detail_obj["listener_name_list"] = []
            ##获取监听器下的资源池的健康检查信息
            if not pool_obj[lb_listener_obj_value.default_pool_id].health_monitor_id:
                health_monitor_dict = {}
                pool_detail_obj["health_monitor_obj"] = health_monitor_dict
                pool_list.append(pool_detail_obj)
                listener_detail_obj["pool_list"] = pool_list
                lb_listener_list.append(listener_detail_obj)
                continue
            health_monitor = health_monitor_obj[pool_obj[lb_listener_obj_value.default_pool_id].health_monitor_id]
            health_monitor_dict = {
                "healthmonitor_id": health_monitor.id,
                "healthmonitor_status": health_monitor.is_admin_state_up,
                "max_retries": health_monitor.max_retries,
                "delay": health_monitor.delay,
                "max_retries_down": health_monitor.max_retries_down,
                "timeout": health_monitor.timeout,
            }
            pool_detail_obj["health_monitor_obj"] = health_monitor_dict
            pool_list.append(pool_detail_obj)
            listener_detail_obj["pool_list"] = pool_list
            lb_listener_list.append(listener_detail_obj)

    except Exception as ex:
        raise ex
    return lb_listener_list


def get_lb_health_monitor_obj(request):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_health_monitor_list = openstack_client.load_balancer.health_monitors()
        lb_health_monitor_obj = {}
        for lb_health_monitor in lb_health_monitor_list:
            lb_health_monitor_obj[lb_health_monitor.id] = lb_health_monitor
    except Exception as ex:
        raise ex
    return lb_health_monitor_obj


def get_l7_policy_obj(request):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_l7_policies_list = openstack_client.load_balancer.l7_policies()
        lb_l7_policies_obj = {}
        for lb_l7_policy in lb_l7_policies_list:
            lb_l7_policies_obj[lb_l7_policy.redirect_pool_id] = lb_l7_policy
    except Exception as ex:
        raise ex
    return lb_l7_policies_obj


def get_lb_listener_obj(request, load_balancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_listener_list = openstack_client.load_balancer.listeners(load_balancer_id=load_balancer_id)
        lb_listener_obj = {}
        for lb_listener in lb_listener_list:
            lb_listener_obj[lb_listener.id] = lb_listener
    except Exception as ex:
        raise ex
    return lb_listener_obj


def get_lb_listener_list_obj(request):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_listener_list = openstack_client.load_balancer.listeners()
        lb_listener_obj = {}
        for lb_listener in lb_listener_list:
            lb_listener_obj[lb_listener.id] = lb_listener
    except Exception as ex:
        raise ex
    return lb_listener_obj


def get_lb_pool_obj(request, loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        lb_pool_list = openstack_client.load_balancer.pools(loadbalancer_id=loadbalancer_id)
        lb_pool_obj = {}
        for lb_pool in lb_pool_list:
            lb_pool_obj[lb_pool.id] = lb_pool
    except Exception as ex:
        raise ex
    return lb_pool_obj


def show_load_balancers(request, loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    response_obj = ResponseObj()
    try:
        load_balances_detail = openstack_client.load_balancer.get_load_balancer(loadbalancer_id).to_dict()
        # 从数据库中拿取VPC得信息
        load_balancer_result = service_model.BmServiceLoadbalance.objects.filter(
            loadbalance_id=load_balances_detail["id"]).first()
        if load_balancer_result:
            vpc_id = load_balancer_result.vpc_id
            is_public = load_balancer_result.is_public
            network_name = load_balancer_result.network_name
            created_at = load_balancer_result.created_at
            subnet_name = load_balancer_result.network_name
            flavor_id = load_balancer_result.flavor_id
        else:
            vpc_id = ""
            is_public = ""
            network_name = ""
            subnet_name = ""
            flavor_id = ""
            created_at = swift_handler.utctime_to_localtime(load_balances_detail["created_at"],
                                                            utc_format='%Y-%m-%dT%H:%M:%S')
        vpc_name = ""
        if vpc_id:
            vpc_result = service_model.BmVpc.objects.filter(
                id=vpc_id).first()
            if vpc_result:
                vpc_name = vpc_result.vpc_name
        # 从数据库中拿对应的Flavor信息
        if flavor_id:
            flavor_obj = service_model.BmServiceLoadbalanceFlavor.objects.filter(
                id=flavor_id).first()
        else:
            flavor_obj = {}
        # 从数据库中拿公网IP信息
        vip_result = service_model.BmServiceFloatingIp.objects.filter(
            instance_uuid=load_balances_detail["id"], is_measure_end=False).first()
        if vip_result:
            public_ip_adress = vip_result.floating_ip
        else:
            public_ip_adress = ""

        lb_health_monitor_obj = get_lb_health_monitor_obj(request)
        lb_pool_obj = get_lb_pool_obj(request, loadbalancer_id=loadbalancer_id)
        lb_listener_obj = get_lb_listener_obj(request, load_balancer_id=loadbalancer_id)
        l7_policy = get_l7_policy_obj(request)

        pool_list = get_lb_pool_detail(request, lb_health_monitor_obj=lb_health_monitor_obj,
                                       lb_pool_obj=lb_pool_obj, lb_listener_obj=lb_listener_obj,
                                       l7_policy=l7_policy)

        listeners_list = get_lb_listener_detail(request, health_monitor_obj=lb_health_monitor_obj,
                                                pool_obj=lb_pool_obj, listener_obj=lb_listener_obj)
        load_balancer_detail_obj = {
            "vpc_name": vpc_name,
            "vpc_id": vpc_id,
            "listener_list": listeners_list,
            "pool_list": pool_list,
            "subnet_name": subnet_name,
            "is_public": is_public,
            "network_name": network_name,
            "created_at": created_at,
            "public_ip_adress": public_ip_adress,
            "flavor_id": flavor_id,
            "id": load_balances_detail["id"],
            "name": load_balances_detail["name"],
            "operating_status": load_balances_detail["operating_status"],
            "project_id": load_balances_detail["project_id"],
            "provider": load_balances_detail["provider"],
            "provisioning_status": load_balances_detail["provisioning_status"],
            "vip_address": load_balances_detail["vip_address"],
            "vip_network_id": load_balances_detail["vip_network_id"],
            "vip_port_id": load_balances_detail["vip_port_id"],
            "vip_qos_policy_id": load_balances_detail["vip_qos_policy_id"],
            "vip_subnet_id": load_balances_detail["vip_subnet_id"],
            "flavor_obj": flavor_obj
        }
    except Exception as e:
        return response_obj.json_exception_serial(user_info="获取负载均衡器详细信息失败", admin_info=str(e), no=403)
    return response_obj.json_serial(load_balancer_detail_obj)


def delete_load_balancers(request, loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    response_obj = ResponseObj()
    try:
        load_balancer_detail, load_balancer_status = lb_status_timeout(request, loadbalancer_id)
        # 查找当前负载均衡器有没有绑定监听器
        if load_balancer_detail["listeners"]:
            return response_obj.json_exception_serial(user_info="删除负载均衡器失败,当前负载均衡器下存在监听器",
                                                      admin_info="当前负载均衡器下存在监听器,无法进行删除操作", no=400)

        # 查找当前负载均衡器有没有后端服务器组
        if load_balancer_detail["pools"]:
            return response_obj.json_exception_serial(user_info="删除负载均衡器失败,当前负载均衡器下存在后端服务器组",
                                                      admin_info="当前负载均衡器下存在后端服务器组,无法进行删除操作", no=400)

        # 进行删除操作，对相应的IP进行解绑操作/只涉及数据库的解绑操作
        floating_ip_result = service_model.BmServiceFloatingIp.objects.filter(instance_uuid=loadbalancer_id,
                                                                              is_measure_end=False).first()
        if floating_ip_result:
            floating_ip_result.attached_type = None
            floating_ip_result.attached = False
            floating_ip_result.instance_uuid = ""
            floating_ip_result.instance_name = ""
            floating_ip_result.fixed_address = ""
            floating_ip_result.update_at = datetime.datetime.now()
            floating_ip_result.save()

        load_balancer = openstack_client.load_balancer.delete_load_balancer(loadbalancer_id)
        # 更新数据库
        load_balancer_obj = service_model.BmServiceLoadbalance.objects.filter(
            loadbalance_id=loadbalancer_id, is_measure_end=False).first()
        if load_balancer_obj:
            load_balancer_obj.is_measure_end = True
            load_balancer_obj.deleted = True
            load_balancer_obj.updated_at = datetime.datetime.now()
            load_balancer_obj.save()
        begin_time = time.time()
        while True:
            try:
                end_time = time.time()
                run_time = end_time - begin_time
                if run_time > 5:
                    raise exc.TimeoutError()
                load_balancer_detail = openstack_client.load_balancer.get_load_balancer(loadbalancer_id).to_dict()
                time.sleep(2)
            except Exception as ex:
                response_obj.json_serial("删除负载均衡器成功")
                break
    except Exception as ex:
        raise ex
    return response_obj.json_serial("删除负载均衡器成功")


def update_load_balancers(request, loadbalancer_id=None, name=None, admin_state_up=None):
    openstack_client = utils.get_openstack_client(request)
    try:
        load_balancer_detail, load_balancer_status = lb_status_timeout(request, loadbalancer_id)

        load_balancer = openstack_client.load_balancer.update_load_balancer(loadbalancer_id, name=name,
                                                                            admin_state_up=admin_state_up)
        # 更新数据库
        load_balancer_obj = service_model.BmServiceLoadbalance.objects.filter(
            loadbalance_id=loadbalancer_id).first()
        if load_balancer_obj:
            load_balancer_obj.loadbalance_name = load_balancer.name
            load_balancer_obj.updated_at = datetime.datetime.now()
            load_balancer_obj.save()
        floating_ip_obj = service_model.BmServiceFloatingIp.objects.filter(
            instance_uuid=loadbalancer_id).first()
        if floating_ip_obj:
            floating_ip_obj.instance_name = load_balancer.name
            floating_ip_obj.save()
    except Exception as ex:
        raise ex
    return load_balancer.to_dict()
