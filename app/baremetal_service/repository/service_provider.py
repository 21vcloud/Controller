# -*- coding:utf-8 -*-
import datetime
import logging
import requests

# Only use in current version
from cinderclient import client as volume_client
from baremetal_openstack.repository.nova_provider import OpenstackClientProvider
from django.db.models import Count
from django.db import connections
from BareMetalControllerBackend.conf.env import EnvConfig
from common.api_request import RequestClient, RequestClientTwo

from BareMetalControllerBackend.conf.env import env_config
from account.repository import auth_models
from baremetal_service.repository import service_model
from common import exceptions as exc
from common import utils
from common.lark_common.model.common_model import ResponseObj
from common.openstack.baremetal_volume import baremetal_detach_volume

LOG = logging.getLogger(__name__)
REQUEST_INFO_LOGGER = logging.getLogger("request_info")
FIP_SERVICE_TYPE = 'network:floatingip'


# 服务器相关接口
class ServiceProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def baremetal_service_order_create(param_info):
        response_obj = ResponseObj()
        try:
            request = service_model.ServiceOrder.objects.using("controller").create(**param_info)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = request
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "提交失败！", "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def get_qos_policy_info(qos_policy_name):
        response_obj = ResponseObj()
        try:
            request = service_model.BmServiceQosPolicy.objects.get(qos_policy_name=qos_policy_name)
            response_obj.no = 200
            response_obj.is_ok = True
            response_obj.content = request
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询带宽信息失败！", "admin_info": str(ex)}
        return response_obj


# 服务器相关接口
class ServiceFloatingProvider(object):

    def __init__(self):
        self.cmdb_provider = ServiceCmdbProvider()

    def floating_ip_list(self, openstack_client):
        floating_ip_obj = openstack_client.list_floating_ips()
        attached_port_list = []
        for floating_ip in floating_ip_obj:
            if floating_ip.attached:
                attached_port_list.append(floating_ip.fixed_ip_address)

    def detach_ip_from_server(self, openstack_client, instance_uuid, floating_ip_id):
        result = openstack_client.detach_ip_from_server(server_id=instance_uuid, floating_ip_id=floating_ip_id)
        if not result:
            raise Exception(result)

        # 更新 实例信息到 平台数据库
        service_attach_obj = service_model.BmServiceFloatingIp.objects.get(floating_ip_id=floating_ip_id,
                                                                           is_measure_end=False)
        instance_uuid = service_attach_obj.instance_uuid
        service_attach_obj.attached = False
        service_attach_obj.attached_type = None
        service_attach_obj.instance_uuid = None
        service_attach_obj.instance_name = None
        service_attach_obj.fixed_address = None
        # service_attach_obj.update_at = datetime.datetime.now()
        service_attach_obj.save()

        cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=instance_uuid, status=None)

        LOG.info("CMDB the ip detach to server sys result: %s" % cmdb_result)

        return service_attach_obj

    def get_floatingip_quota(self, openstack_client, project_id):
        LOG.info("Get floatingip quota for project %s", project_id)
        network_quota = openstack_client.network.get_quota(project_id, details=True)
        LOG.info("network quota %s", network_quota)
        REQUEST_INFO_LOGGER.info("Get network quota %s", network_quota.floating_ips)
        available_fip_quota = network_quota.floating_ips['limit'] - \
                              network_quota.floating_ips['used'] - int(network_quota.floating_ips['reserved'])
        return {"available_fip_quota": available_fip_quota}

    def check_fip_quota(self, openstack_client, fip_count, project_id):
        LOG.info("Check network quota with %s count %s", project_id, fip_count)
        check_result = True
        available_fip_quota = self.get_floatingip_quota(openstack_client, project_id).get('available_fip_quota')
        if fip_count > available_fip_quota:
            check_result = False
        return check_result, available_fip_quota

    def check_fip_pools(self, fip_count, external_net_id):
        LOG.info("Check fip pools")
        admin_client = utils.get_admin_client()

        LOG.info("Get available_ips")
        available_ips = admin_client.network.get_network_ip_availability(external_net_id)
        REQUEST_INFO_LOGGER.info("Get fip pools %s", available_ips)
        subnet_ip_availability_dict = {}
        for ip_available in available_ips.subnet_ip_availability:
            subnet_ip_availability_dict[ip_available['subnet_id']] = ip_available

        LOG.debug("Find floatingip subnets begin")
        subnets = admin_client.network.subnets(network_id=external_net_id)
        fip_subnet_ids = []

        for subnet in subnets:
            if FIP_SERVICE_TYPE in subnet.service_types:
                fip_subnet_ids.append(subnet.id)
        LOG.info("Floaginip subnets %s", fip_subnet_ids)

        ip_available_count = 0
        if fip_subnet_ids:
            for subnet_id in fip_subnet_ids:
                ip_avialability = subnet_ip_availability_dict.get(subnet_id)
                if ip_avialability:
                    ip_available_count += ip_avialability['total_ips'] - ip_avialability['used_ips']
        else:
            for ip_avialability in subnet_ip_availability_dict.values():
                ip_available_count += ip_avialability['total_ips'] - ip_avialability['used_ips']

        if fip_count > ip_available_count:
            return False
        return True

    @staticmethod
    def get_qos_max_kbps(service_fip_object):
        """
        Get fip qos max kbps
        :param service_fip_object:
        :return: max_kbps
        """
        REQUEST_INFO_LOGGER.info("Get fip qos max kbps %s", service_fip_object)
        if service_fip_object.shared_qos_policy_type:
            shared_bandwidth = service_model.BmShareBandWidth.objects.filter(
                shared_bandwidth_id=service_fip_object.qos_policy_id, is_measure_end=False).first()
            REQUEST_INFO_LOGGER.error("No shared bandwidth found ,we will use measure end query ")
            if not shared_bandwidth:
                shared_bandwidth = service_model.BmShareBandWidth.objects.filter(
                    shared_bandwidth_id=service_fip_object.qos_policy_id).first()
            if shared_bandwidth:
                return shared_bandwidth.max_kbps
            else:
                return None
        else:
            qos_policy_name = service_fip_object.qos_policy_name
            if not qos_policy_name.endswith("M"):
                qos_policy_name = service_model.BmServiceQosPolicy.objects.get(
                    id=service_fip_object.qos_policy_id).qos_policy_name
            return int(qos_policy_name.rstrip("M")) * 1024


class ServiceCmdbProvider(object):

    def __init__(self):
        self.env_config = EnvConfig()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.openstack_provider = OpenstackClientProvider()
        self.openstack_client = self.openstack_provider.get_admin_openstack_client()
        self.request_cmdb_customize_client = RequestClientTwo(endpoint=self.env_config.cmdb_customize_service,
                                                              api_key="")
        self.request_cmdb_asset_client = RequestClientTwo(endpoint=self.env_config.cmdb_asset_service,
                                                          api_key="")

    def cmdb_data_sys_post(self, instance_uuid, zone, project_id):
        is_success = True
        try:
            query_dict = {"instance_uuid": instance_uuid}
            node_obj = self.openstack_client.baremetal.nodes(details=True, **query_dict)
            node_info_list = list(node_obj)
            for node_info in node_info_list:
                dict_info = {
                    "uuid": node_info.id,
                    "zone": zone,
                    "project_id": project_id
                }
                result = self.request_cmdb_customize_client.baremetal(dict_param=dict_info, method="POST", is_add=True)
                self.logger.error("The instance post into cmdb result %s" % result)
                if not result.success:
                    is_success = False
        except Exception as ex:
            self.logger.error("Fail to sys the instance post into cmdb %s" % ex)

        return is_success

    def cmdb_data_sys_put(self, instance_uuid, status):
        success = True
        try:
            query_dict = {"instance_uuid": instance_uuid}
            node_obj = self.openstack_client.baremetal.nodes(details=True, **query_dict)
            node_info_list = list(node_obj)
            for node_info in node_info_list:

                dict_info = {
                    "uuid": node_info.id
                }
                if status:
                    dict_info["status"] = status

                result = self.request_cmdb_customize_client.baremetal(dict_param=dict_info, method="PUT")
                self.logger.error("The instance put into cmdb result %s" % result)
                if not result.success:
                    success = False
        except Exception as ex:
            self.logger.error("Fail to sys the instance put into cmdb %s" % ex)

        return success

    def cmdb_data_sys_put2(self, instance_uuid, status):
        success = True
        try:
            query_dict = {"instance_uuid": instance_uuid}
            node_obj = self.openstack_client.baremetal.nodes(details=True, **query_dict)
            node_info_list = list(node_obj)
            for node_info in node_info_list:

                dict_info = {
                    "uuid": node_info.id
                }
                if status:
                    dict_info["net_status"] = status

                result = self.request_cmdb_customize_client.baremetal(dict_param=dict_info, method="PUT")
                self.logger.error("The instance put into cmdb result %s" % result)
                if not result.success:
                    success = False
        except Exception as ex:
            self.logger.error("Fail to sys the instance put into cmdb %s" % ex)

        return success

    def cmdb_data_sys_del(self, instance_uuid):
        try:
            query_dict = {"instance_uuid": instance_uuid}
            node_obj = self.openstack_client.baremetal.nodes(details=True, **query_dict)
            node_info_list = list(node_obj)
            for node_info in node_info_list:
                result = self.request_cmdb_customize_client.baremetal(dict_param={}, method="DELETE",
                                                                      url_param_list=[node_info.id + "/"])
                self.logger.error("The instance delete into cmdb result %s" % result)
        except Exception as ex:
            self.logger.error("Fail to sys the instance delete into cmdb %s" % ex)

        return True

    def cmdb_data_tag_create(self, instance_uuid):
        is_success = True
        try:
            query_dict = {"instance_uuid": instance_uuid}
            node_obj = self.openstack_client.baremetal.nodes(details=True, **query_dict)
            node_info_list = list(node_obj)
            for node_info in node_info_list:
                dict_info = {
                    "abstract_custom": node_info.id,
                    "tag_name": "zabbix",
                    "tag_type": "agent"
                }
                result = self.request_cmdb_asset_client.abstract_tag(dict_param=dict_info, method="POST", is_add=True)
                self.logger.error("The instance tag post into cmdb result %s" % result)
                if not result.success:
                    is_success = False
        except Exception as ex:
            self.logger.error("Fail to sys the tag create into cmdb %s" % ex)

        return is_success


class ServiceVolumeProvider(object):

    def __init__(self):
        pass

    def detach_volume_from_server(self, openstack_client, volume_id, server_id,
                                  volume_result=None, server_result=None):
        bm_service_volume = service_model.BmServiceVolume.objects.get(volume_id=volume_id, is_measure_end=False)

        if not server_result:
            server_result = openstack_client.compute.get_server(server_id)
        if env_config.baremetal_tag in server_result.tags:
            baremetal_detach_volume(server_result, volume_id, openstack_client)
            # openstack_client.delete_block_mapping(server_id, volume_id)
        else:
            if not volume_result:
                volume_result = openstack_client.get_volume(volume_id)
            openstack_client.detach_volume(server=server_result, volume=volume_result)

        bm_service_volume.attached_type = None
        bm_service_volume.instance_uuid = None
        bm_service_volume.instance_name = None
        bm_service_volume.save()
        return bm_service_volume

    def get_volume_quota(self, openstack_client, project_id):
        LOG.info("Get %s volume quota", project_id)
        cinder = volume_client.Client('3.44', session=openstack_client.session)
        volume_quota = cinder.quotas.get(project_id, usage=True)
        volume_available_count = int(volume_quota.volumes['limit']) - int(volume_quota.volumes['in_use']) - int(
            volume_quota.volumes['reserved'])
        volume_available_size = int(volume_quota.gigabytes['limit']) - int(volume_quota.gigabytes['in_use']) - int(
            volume_quota.gigabytes['reserved'])
        return {"volume_available_count": volume_available_count, "volume_available_size": volume_available_size}

    def check_volume_quota(self, openstack_client, need_single_size, need_count, project_id):
        """
        检查磁盘配额和后台存储池是否满足资源需要
        :param request: request
        :param need_single_size: 单个盘的大小
        :param need_count: 盘个数
        :param project_id: 项目id
        :return:
        """
        check_result = True
        LOG.info("Check volume quota with single size %s, count %s for project %s",
                 need_single_size, need_count, project_id)

        volume_quota = self.get_volume_quota(openstack_client, project_id)

        volume_available_count = int(volume_quota.get('volume_available_count'))
        volume_available_size = int(volume_quota.get('volume_available_size'))
        if need_count > volume_available_count or need_single_size * need_count > volume_available_size:
            check_result = False

        if not check_result:
            return check_result, volume_available_count, volume_available_size
        return check_result, None, None

    def get_pool_size(self, volume_type='inspure_iscsi'):
        LOG.info("Check backend store size")
        admin_client = utils.get_admin_client()
        cinder = volume_client.Client('2', session=admin_client.session)

        pool = cinder.volumes.get_pools(detail=True, )
        volume_pools_info = {}
        for info in pool._info['pools']:
            volume_pools_info[info['capabilities']['volume_backend_name']] = info['capabilities']

        # TODO it's only in dev environment
        if volume_type not in volume_pools_info:
            volume_type = 'tripleo_iscsi'
        backend_info = volume_pools_info.get(volume_type, None)
        # if not backend_info or backend_info.get('backend_state', 'down') != 'up':
        if not backend_info:
            raise exc.VolumeTypeInvalid

        free_capacity_gb = float(backend_info['free_capacity_gb'])
        reserved_percentage = float(backend_info['reserved_percentage'])
        max_over_subscription_ratio = float(backend_info['max_over_subscription_ratio'])

        pool_available_size = (free_capacity_gb * (100 - reserved_percentage) / 100) * max_over_subscription_ratio
        return pool_available_size

    def check_pool(self, need_single_size, need_count, volume_type='inspure_iscsi'):
        check_result = True
        pool_available_size = self.get_pool_size(volume_type=volume_type)

        if need_single_size * need_count > pool_available_size:
            check_result = False
        return check_result


# 物料相关接口
class BmMaterialProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def contract_volume_bak_seasonal(start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出合同下的所有Volume信息
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            volume_list_obj = service_model.BmServiceVolumeBackup.objects.filter(
                create_at__lte=end_date,
                create_at__gte=start_date)
            if not volume_list_obj:
                response_obj.content = []
                return response_obj
            # 筛选出每个Volume下的最后的信息
            volume_list = []
            for volume_obj in volume_list_obj:
                #  服务结束时间
                if volume_obj.deleted:
                    delete_time = volume_obj.updated_at
                else:
                    delete_time = ""
                # 查找合同的一些信息
                bm_contract_material_obj = auth_models.BmContract.objects.filter(
                    contract_number=volume_obj.contract_number).first()
                if bm_contract_material_obj:
                    bm_contract_material = bm_contract_material_obj.__dict__
                    bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                    bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                    bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                    bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                    bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                else:
                    bm_contract_material_customer_id = ""
                    bm_contract_material_account_id = ""
                    bm_contract_material_customer_name = ""
                    bm_contract_material_authorizer = ""
                    bm_contract_material_contract_type = ""
                # 查找客户的信息
                bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()
                if not bm_contract_user:
                    sales = ""
                    enterprise_number = ""
                    location = ""
                    customer_service_name = ""
                else:
                    sales = bm_contract_user.sales
                    enterprise_number = bm_contract_user.enterprise_number
                    location = bm_contract_user.location
                    customer_service_name = bm_contract_user.customer_service_name
                # 查找授权人的信息
                bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(
                    id=bm_contract_material_account_id).first()
                if not bm_contract_authorizer:
                    account = ""
                else:
                    account = bm_contract_authorizer.account
                # 查找订单信息
                bm_contract_order = service_model.BmServiceOrder.objects.filter(id=volume_obj.order_id).first()
                if not bm_contract_order:
                    region = ""
                    service_count = ""
                else:
                    region = bm_contract_order.region
                    service_count = bm_contract_order.service_count
                # 查找下单者的一些信息
                bm_account_info = auth_models.BmUserInfo.objects.filter(id=volume_obj.account_id).first()
                if not bm_account_info:
                    user_account = ""
                    identity_name = ""
                else:
                    user_account = bm_account_info.account
                    identity_name = bm_account_info.identity_name
                # 查找项目信息
                bm_contract_project = service_model.BmProject.objects.filter(id=volume_obj.project_id).first()
                if not bm_contract_project:
                    project_name = ""
                else:
                    project_name = bm_contract_project.project_name

                # 查找volume信息
                bm_contract_volume = service_model.BmServiceMaterialVolume.objects.filter(
                    openstack_volume_type=auth_models.VOLUME_BACK_TYPE).first()
                if not bm_contract_volume:
                    material_number = ""
                    volume_type_name = ""
                    base_price = ""
                else:
                    material_number = bm_contract_volume.material_number
                    volume_type_name = bm_contract_volume.volume_type_name
                    base_price = str(bm_contract_volume.base_price)

                material_volume_dict_all = {
                    "用户ID": volume_obj.account_id,
                    "用户邮箱": user_account,
                    "用户姓名": identity_name,
                    "合同编码": volume_obj.contract_number,
                    "备份时间": volume_obj.create_at,
                    "云硬盘备份名称": volume_obj.backup_name,
                    "订单号": volume_obj.order_id,
                    "项目ID": volume_obj.project_id,
                    "项目名称": project_name,
                    "云硬盘大小": service_count,
                    "服务结束时间": delete_time,
                    "云硬盘id": volume_obj.volume_id,
                    "客户名称": bm_contract_material_customer_name,
                    "合同授权人": bm_contract_material_authorizer,
                    "合同类型": bm_contract_material_contract_type,
                    "销售姓名": sales,
                    "公司编码": enterprise_number,
                    "公司所属区": location,
                    "客服姓名": customer_service_name,
                    "合同授权人邮箱": account,
                    "合同可用区": region,
                    "云硬盘备份物料编码": material_number,
                    "云硬盘物料类型": volume_type_name,
                    "基础价格": base_price
                }
                volume_list.append(material_volume_dict_all)

            response_obj.content = volume_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "云硬盘物料查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    def contract_nat_seasonal(self, start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出合同下的所有Nat信息
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            nat_list_obj = service_model.BmServiceNatGateway.objects.filter(
                create_at__lte=end_date,
                create_at__gte=start_date)
            if not nat_list_obj:
                response_obj.content = []
                return response_obj
            nat_list = []
            for nat_obj in nat_list_obj:
                # 查找合同的一些信息
                bm_contract_material_obj = auth_models.BmContract.objects.filter(
                    contract_number=nat_obj.contract_number).first()
                if bm_contract_material_obj:
                    bm_contract_material = bm_contract_material_obj.__dict__
                    bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                    bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                    bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                    bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                    bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                else:
                    bm_contract_material_customer_id = ""
                    bm_contract_material_account_id = ""
                    bm_contract_material_customer_name = ""
                    bm_contract_material_authorizer = ""
                    bm_contract_material_contract_type = ""
                # 查找客户的信息
                bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()
                if not bm_contract_user:
                    sales = ""
                    enterprise_number = ""
                    location = ""
                    customer_service_name = ""
                else:
                    sales = bm_contract_user.sales
                    enterprise_number = bm_contract_user.enterprise_number
                    location = bm_contract_user.location
                    customer_service_name = bm_contract_user.customer_service_name
                # 查找授权人的信息
                bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(
                    id=bm_contract_material_account_id).first()
                if not bm_contract_authorizer:
                    account = ""
                else:
                    account = bm_contract_authorizer.account
                # 查找订单信息
                bm_contract_order = service_model.BmServiceOrder.objects.filter(id=nat_obj.order_id).first()
                if not bm_contract_order:
                    region = ""
                else:
                    region = bm_contract_order.region
                # 查找下单者的一些信息
                bm_account_info = auth_models.BmUserInfo.objects.filter(id=nat_obj.account_id).first()
                if not bm_account_info:
                    user_account = ""
                    identity_name = ""
                else:
                    user_account = bm_account_info.account
                    identity_name = bm_account_info.identity_name
                # 查找项目信息
                bm_contract_project = service_model.BmProject.objects.filter(id=nat_obj.project_id).first()
                if not bm_contract_project:
                    project_name = ""
                else:
                    project_name = bm_contract_project.project_name

                # 查找Nat信息
                bm_material_nat = service_model.BmServiceMaterialNat.objects.filter(
                    charge_type=auth_models.CHAR_TYPE).first()
                if not bm_material_nat:
                    material_number = ""
                    nat_getway_type_name = ""
                    base_price = ""
                else:
                    material_number = bm_material_nat.material_number
                    nat_getway_type_name = bm_material_nat.nat_getway_type_name
                    base_price = str(bm_material_nat.base_price)

                material_nat_dict_all = {
                    "用户ID": nat_obj.account_id,
                    "用户邮箱": user_account,
                    "用户姓名": identity_name,
                    "合同编码": nat_obj.contract_number,
                    "创建时间": nat_obj.create_at,
                    "订单号": nat_obj.order_id,
                    "项目ID": nat_obj.project_id,
                    "项目名称": project_name,
                    "服务结束时间": nat_obj.delete_at,
                    "NAT网关id": nat_obj.id,
                    "NAT网关名称": nat_obj.name,
                    "客户名称": bm_contract_material_customer_name,
                    "合同授权人": bm_contract_material_authorizer,
                    "合同类型": bm_contract_material_contract_type,
                    "销售姓名": sales,
                    "公司编码": enterprise_number,
                    "公司所属区": location,
                    "客服姓名": customer_service_name,
                    "合同授权人邮箱": account,
                    "合同可用区": region,
                    "NAT物料编码": material_number,
                    "NAT物料类型": nat_getway_type_name,
                    "基础价格": base_price
                }
                nat_list.append(material_nat_dict_all)

            response_obj.content = nat_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "NAT网关物料查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def contract_machine_seasonal(start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出合同下的所有instance信息
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            instance_list_obj = service_model.BmServiceInstance.objects.filter(task="success", create_at__lte=end_date,
                                                                               create_at__gte=start_date)
            instance_id_list = []
            for instance_uuid in instance_list_obj:
                if instance_uuid.uuid not in instance_id_list:
                    instance_id_list.append(instance_uuid.uuid)

            # 筛选出每个下的instance机器配置信息
            machine_list = []
            if instance_id_list.__len__() > 0:
                for instance_id in instance_id_list:
                    machine_list_obj = service_model.BmServiceMachine.objects.filter(
                        uuid=instance_id).first()
                    if not machine_list_obj:
                        response_obj.message = {
                            "user_info": "查询为空！uuid不存在"
                        }
                        continue
                    if machine_list_obj.deleted:
                        delete_at = machine_list_obj.update_at
                    else:
                        delete_at = ""
                    # 查找服务信息
                    bm_contract_service_obj = service_model.BmServiceInstance.objects.filter(uuid=instance_id).first()
                    if bm_contract_service_obj:
                        bm_contract_service = bm_contract_service_obj.__dict__
                        bm_contract_service_contract_number = bm_contract_service.get("contract_number", "")
                        bm_contract_service_account_id = bm_contract_service.get("account_id", "")
                        bm_contract_service_project_id = bm_contract_service.get("project_id", "")
                        bm_contract_service_product_type = bm_contract_service.get("product_type", "")
                    else:
                        bm_contract_service_contract_number = ""
                        bm_contract_service_account_id = ""
                        bm_contract_service_project_id = ""
                        bm_contract_service_product_type = ""
                    # 查找合同的一些信息
                    bm_contract_material_obj = auth_models.BmContract.objects.filter(
                        contract_number=bm_contract_service_contract_number).first()
                    if bm_contract_material_obj:
                        bm_contract_material = bm_contract_material_obj.__dict__
                        bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                        bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                        bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                        bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                        bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                    else:
                        bm_contract_material_customer_id = ""
                        bm_contract_material_account_id = ""
                        bm_contract_material_customer_name = ""
                        bm_contract_material_authorizer = ""
                        bm_contract_material_contract_type = ""
                    # 查找客户的信息
                    bm_contract_user = auth_models.BmEnterprise.objects.filter(
                        id=bm_contract_material_customer_id).first()
                    if not bm_contract_user:
                        sales = ""
                        enterprise_number = ""
                        location = ""
                        customer_service_name = ""
                    else:
                        sales = bm_contract_user.sales
                        enterprise_number = bm_contract_user.enterprise_number
                        location = bm_contract_user.location
                        customer_service_name = bm_contract_user.customer_service_name
                    # 查找授权人的信息
                    bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(
                        id=bm_contract_material_account_id).first()
                    if not bm_contract_authorizer:
                        account = ""
                    else:
                        account = bm_contract_authorizer.account

                    # 查找订单信息
                    bm_contract_order = service_model.BmServiceOrder.objects.filter(
                        id=machine_list_obj.order_id).first()
                    if not bm_contract_order:
                        region = ""
                        service_count = ""
                    else:
                        region = bm_contract_order.region
                        service_count = bm_contract_order.service_count
                    # 查找物料信息
                    bm_contract_machine = service_model.BmServiceFlavor.objects.filter(
                        id=machine_list_obj.flavor_id).first()
                    if not bm_contract_machine:
                        material_number = ""
                        type = ""
                        base_price = ""
                        flavor_info = ""
                        cpu_model = ""
                        cpu_core = ""
                        cpu_hz = ""
                        ram = ""
                        disk = ""
                    else:
                        material_number = bm_contract_machine.material_number
                        type = bm_contract_machine.type
                        base_price = str(bm_contract_machine.base_price)
                        flavor_info = bm_contract_machine.flavor_info
                        cpu_model = bm_contract_machine.cpu_model
                        cpu_core = bm_contract_machine.cpu_core
                        cpu_hz = bm_contract_machine.cpu_hz
                        ram = bm_contract_machine.ram
                        disk = bm_contract_machine.disk
                    # 查找下单者的一些信息
                    bm_account_info = auth_models.BmUserInfo.objects.filter(id=bm_contract_service_account_id).first()
                    if not bm_account_info:
                        user_account = ""
                        identity_name = ""
                    else:
                        user_account = bm_account_info.account
                        identity_name = bm_account_info.identity_name
                    # 查找项目信息
                    bm_contract_project = service_model.BmProject.objects.filter(
                        id=bm_contract_service_project_id).first()
                    if not bm_contract_project:
                        project_name = ""
                    else:
                        project_name = bm_contract_project.project_name

                    material_machine_dict_all = {
                        "用户ID": bm_contract_service_account_id,
                        "用户邮箱": user_account,
                        "用户姓名": identity_name,
                        "合同编号": bm_contract_service_contract_number,
                        "机器创建时间": machine_list_obj.create_at,
                        "flavor名称": machine_list_obj.flavor_name,
                        "镜像名称": machine_list_obj.image_name,
                        "是否携带监控": machine_list_obj.monitoring,
                        "是否携带漏洞扫描": machine_list_obj.vulnerability_scanning,
                        "网络名称": machine_list_obj.network,
                        "网络类型名称": machine_list_obj.network_path_type,
                        "机器名称": machine_list_obj.service_name,
                        "订单号": machine_list_obj.order_id,
                        "项目ID": bm_contract_service_project_id,
                        "项目名称": project_name,
                        "产品类型": bm_contract_service_product_type,
                        "机器数量": service_count,
                        "服务结束时间": delete_at,
                        "客户名称": bm_contract_material_customer_name,
                        "合同授权人": bm_contract_material_authorizer,
                        "合同类型": bm_contract_material_contract_type,
                        "销售姓名": sales,
                        "公司编号": enterprise_number,
                        "公司所属区": location,
                        "客服姓名": customer_service_name,
                        "合同授权人邮箱": account,
                        "合同可用区": region,
                        "Flavor物料编码": material_number,
                        "flavor类型": type,
                        "基础价格": base_price,
                        "机器配置信息": flavor_info,
                        "CPU": cpu_model,
                        "内核": cpu_core,
                        "主频": cpu_hz,
                        "内存": ram,
                        "磁盘信息": disk
                    }
                    machine_list.append(material_machine_dict_all)

            response_obj.content = machine_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "machine物料查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def contract_volume_seasonal(start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出合同下的所有Volume信息
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            volume_list_obj = service_model.BmServiceVolume.objects.filter(
                create_at__lte=end_date,
                create_at__gte=start_date)
            volume_id_list = []
            for volume_ids in volume_list_obj:
                if volume_ids.volume_id not in volume_id_list:
                    volume_id_list.append(volume_ids.volume_id)

            # 筛选出每个Volume下的最后的信息
            volume_list = []
            for volume_id_1 in volume_id_list:
                volume_list_obj = service_model.BmServiceVolume.objects.filter(
                    volume_id=volume_id_1, create_at__lte=end_date,
                    create_at__gte=start_date, ).last()
                if not volume_list_obj:
                    response_obj.message = {
                        "user_info": "查询为空！"
                    }
                    return response_obj
                # 查找合同的一些信息
                bm_contract_material_obj = auth_models.BmContract.objects.filter(
                    contract_number=volume_list_obj.contract_number).first()
                if bm_contract_material_obj:
                    bm_contract_material = bm_contract_material_obj.__dict__
                    bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                    bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                    bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                    bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                    bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                else:
                    bm_contract_material_customer_id = ""
                    bm_contract_material_account_id = ""
                    bm_contract_material_customer_name = ""
                    bm_contract_material_authorizer = ""
                    bm_contract_material_contract_type = ""

                # 查找客户的信息
                bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()
                if not bm_contract_user:
                    sales = ""
                    enterprise_number = ""
                    location = ""
                    customer_service_name = ""
                else:
                    sales = bm_contract_user.sales
                    enterprise_number = bm_contract_user.enterprise_number
                    location = bm_contract_user.location
                    customer_service_name = bm_contract_user.customer_service_name

                # 查找授权人的信息
                bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(
                    id=bm_contract_material_account_id).first()
                if not bm_contract_authorizer:
                    account = ""
                else:
                    account = bm_contract_authorizer.account

                # 查找订单信息
                bm_contract_order = service_model.BmServiceOrder.objects.filter(id=volume_list_obj.order_id).first()
                if not bm_contract_order:
                    region = ""
                else:
                    region = bm_contract_order.region

                # 查找volume信息
                bm_contract_volume = service_model.BmServiceMaterialVolume.objects.filter(
                    openstack_volume_type=volume_list_obj.volume_type).first()
                if not bm_contract_volume:
                    material_number = ""
                    volume_type_name = ""
                    base_price = ""
                else:
                    material_number = bm_contract_volume.material_number
                    volume_type_name = bm_contract_volume.volume_type_name
                    base_price = str(bm_contract_volume.base_price)

                # 查找下单者的一些信息
                bm_account_info = auth_models.BmUserInfo.objects.filter(id=volume_list_obj.account_id).first()
                if not bm_account_info:
                    user_account = ""
                    identity_name = ""
                else:
                    user_account = bm_account_info.account
                    identity_name = bm_account_info.identity_name
                # 查找项目信息
                bm_contract_project = service_model.BmProject.objects.filter(id=volume_list_obj.project_id).first()
                if not bm_contract_project:
                    project_name = ""
                else:
                    project_name = bm_contract_project.project_name

                material_volume_dict_all = {
                    "用户ID": volume_list_obj.account_id,
                    "用户邮箱": user_account,
                    "用户姓名": identity_name,
                    "合同编码": volume_list_obj.contract_number,
                    "云硬盘创建时间": volume_list_obj.create_at,
                    "云硬盘名称": volume_list_obj.name,
                    "订单号": volume_list_obj.order_id,
                    "项目ID": volume_list_obj.project_id,
                    "项目名称": project_name,
                    "云硬盘大小": volume_list_obj.size,
                    "服务结束时间": volume_list_obj.update_at,
                    "云硬盘id": volume_list_obj.volume_id,
                    "云硬盘类型": volume_list_obj.volume_type,
                    "客户名称": bm_contract_material_customer_name,
                    "合同授权人": bm_contract_material_authorizer,
                    "合同类型": bm_contract_material_contract_type,
                    "销售姓名": sales,
                    "公司编码": enterprise_number,
                    "公司所属区": location,
                    "客服名称": customer_service_name,
                    "合同授权人邮箱": account,
                    "合同可用区": region,
                    "云硬盘物料编码": material_number,
                    "云硬盘类型名称": volume_type_name,
                    "基础价格": base_price
                }
                volume_list.append(material_volume_dict_all)

            response_obj.content = volume_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "云硬盘物料查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    def material_ip_calculate_in_range(self, start_date, end_date, param_dict=None):
        response_obj = ResponseObj()
        try:
            # 进行多次筛选操作
            material_ip_list = []
            begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            while begin_date <= end_date:
                material_ip_date = datetime.datetime.strftime(begin_date, "%Y-%m-%d")

                # 查询弹性IP某一天的计量信息
                material_day_ip_obj = self.material_ip_calculate_in_one_day(
                    material_ip_date=material_ip_date, param_dict=param_dict)
                if not material_day_ip_obj.is_ok:
                    raise Exception(material_day_ip_obj)

                # 查询结果为空跳过
                if material_day_ip_obj.content:
                    material_ip_list.extend(material_day_ip_obj.content)

                begin_date += datetime.timedelta(days=1)

            response_obj.content = material_ip_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "contract_number 查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    # 查询弹性IP某一天的计量信息
    def material_ip_calculate_in_one_day(self, material_ip_date, param_dict=None):
        response_obj = ResponseObj()
        try:
            # 查询需计费的弹性ip列表
            create_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            floating_ip_id_list_obj = service_model.BmServiceFloatingIp.objects.filter(
                create_at__lte=create_at).values('floating_ip_id').annotate(Count=Count('floating_ip_id'))

            # 根据额外条件进行弹性IP列表过滤
            if param_dict:
                floating_ip_id_list_obj = floating_ip_id_list_obj.filter(**param_dict).values(
                    'floating_ip_id').annotate(Count=Count('floating_ip_id'))

            # 查询当天宽带最大及相关IP信息
            material_ip_list = []
            for floating_ip_dict in floating_ip_id_list_obj:
                floating_ip_id = floating_ip_dict.get("floating_ip_id")
                if not floating_ip_id:
                    continue
                material_day_ip_obj = self.material_ip_day_by_ip_id(floating_ip_id, material_ip_date)

                # 查询结果异常 跳出
                if not material_day_ip_obj.is_ok:
                    raise Exception(material_day_ip_obj.message)

                # 查询结果为空跳过
                if not material_day_ip_obj.content:
                    continue

                material_ip_list.append(material_day_ip_obj.content)

            response_obj.content = material_ip_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "contract_number 查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    # 优化获取弹性公网IP的取值
    def material_ip_seasonal(self, start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出当前周期下的所有IP
            material_ip_list = []
            material_ip_id_list = []
            begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            start_date = begin_date.replace(day=1)
            # 筛选出当月创建的IP
            floating_ip_id_list_obj = service_model.BmServiceFloatingIp.objects.filter(
                create_at__lte=end_date, create_at__gte=start_date).values('floating_ip_id').annotate(
                Count=Count('floating_ip_id'))
            for floating_ip_dict in floating_ip_id_list_obj:
                floating_ip_id = floating_ip_dict.get("floating_ip_id")
                if not floating_ip_id:
                    continue
                material_ip_id_list.append(floating_ip_id)
            # 筛选出当月之前未结束计费的IP---需要叠加在本月的数据当中进行计费
            floating_ip_id_list_before_obj = service_model.BmServiceFloatingIp.objects.filter(
                create_at__lte=start_date, is_measure_end=False).values('floating_ip_id').annotate(
                Count=Count('floating_ip_id'))
            for floating_ip_dict in floating_ip_id_list_before_obj:
                floating_ip_id = floating_ip_dict.get("floating_ip_id")
                if not floating_ip_id:
                    continue
                material_ip_id_list.append(floating_ip_id)
            while begin_date < end_date:
                material_ip_date = datetime.datetime.strftime(begin_date, "%Y-%m-%d")
                # 查询弹性IP某一天的计量信息
                for floating_ip_id_single in material_ip_id_list:
                    material_day_ip_obj = self.material_ip_day_by_ip_id(
                        material_ip_date=material_ip_date, floating_ip_id=floating_ip_id_single)
                    if not material_day_ip_obj.is_ok:
                        response_obj.no = 500
                        response_obj.is_ok = False
                        response_obj.message = {"user_info": "物料IP信息查询失败！",
                                                "admin_info": material_ip_date}
                        return response_obj
                    # 查询结果为空跳过
                    if material_day_ip_obj.content:
                        material_ip_list.append(material_day_ip_obj.content)

                begin_date += datetime.timedelta(days=1)

            response_obj.content = material_ip_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料IP信息查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    def material_ip_day_by_ip_id(self, floating_ip_id, material_ip_date):
        """
        # 根据IP的查询该合同下某个IP信息
        :param floating_ip_id:
        :param material_ip_date:
        :return:
        """
        response_obj = ResponseObj()
        try:
            # 进行数据处理
            floating_ip_list_obj = service_model.BmServiceFloatingIp.objects.filter(
                floating_ip_id=floating_ip_id).order_by("create_at")
            floating_ip_list = [u.__dict__ for u in floating_ip_list_obj]
            ip_first_obj = floating_ip_list_obj.first()
            service_start_time = ip_first_obj.create_at

            bm_material_ip_null = floating_ip_list_obj.filter(is_measure_end=False)
            ip_update_null = [u.__dict__ for u in bm_material_ip_null]

            # 到期时间的处理
            service_expired_time = "-"
            for material_ip in floating_ip_list:
                if material_ip["status"] == "deleted":
                    service_expired_time = material_ip["update_at"]
                    break

            # 筛选出某天的数据
            date_ip = material_ip_date
            create_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            update_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d')
            bm_material_ip_info = service_model.BmServiceFloatingIp.objects.filter(
                create_at__lte=create_at, update_at__gte=update_at, floating_ip_id=floating_ip_id).order_by("create_at")
            material_ip_list_info = [u.__dict__ for u in bm_material_ip_info]

            # 进行数据拼接得到当天所有IP的完整数据
            if bm_material_ip_null:
                if ip_update_null[0]["create_at"] <= create_at:
                    material_ip_list_info.extend(ip_update_null)

            # 进行查到的数据为空数据的处理
            if not material_ip_list_info:
                response_obj.message = {"user_info": "{date_ip}查询为空！".format(date_ip=date_ip)}
                return response_obj

            # 找出当天的最大带宽
            max_band = -1
            max_band_ip_dict = dict()
            max_band_persional = -1
            max_band_ip_dict_persional = {}
            max_band_ip_dict_share = {}
            for material_ip in material_ip_list_info:
                # 如果是共享带宽则无对应的最大带宽
                if material_ip["shared_qos_policy_type"]:
                    max_band_ip_dict_share = material_ip
                else:
                    material_ip_band = int(material_ip["qos_policy_name"].split("M")[0])
                    if max_band <= material_ip_band:
                        max_band_persional = material_ip_band
                        max_band_ip_dict_persional = material_ip
                if max_band_persional != -1:
                    max_band = max_band_persional
                    max_band_ip_dict = max_band_ip_dict_persional
                else:
                    max_band = 0
                    max_band_ip_dict = max_band_ip_dict_share

            # 查找合同的一些信息
            bm_contract_material_obj = auth_models.BmContract.objects.filter(
                contract_number=max_band_ip_dict.get("contract_number")).first()
            if bm_contract_material_obj:
                bm_contract_material = bm_contract_material_obj.__dict__
                bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                bm_contract_material_expire_date = bm_contract_material.get("expire_date", "")
                bm_contract_material_start_date = bm_contract_material.get("start_date", "")
            else:
                bm_contract_material_customer_id = ""
                bm_contract_material_account_id = ""
                bm_contract_material_customer_name = ""
                bm_contract_material_authorizer = ""
                bm_contract_material_contract_type = ""
                bm_contract_material_start_date = ""
                bm_contract_material_expire_date = ""

            # 查找客户的信息
            bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()

            if not bm_contract_user:
                sales = ""
                enterprise_number = ""
                location = ""
                customer_service_name = ""
            else:
                sales = bm_contract_user.sales
                enterprise_number = bm_contract_user.enterprise_number
                location = bm_contract_user.location
                customer_service_name = bm_contract_user.customer_service_name

            # 查找物料IP的信息
            bm_contract_material_ip = service_model.BmContractFloatingIpMaterial.objects.filter(
                external_line_type=max_band_ip_dict.get("external_line_type")).first()
            if not bm_contract_material_ip:
                material_number = ""
                floating_ip_type_name = ""
                base_price = ""
            else:
                material_number = bm_contract_material_ip.material_number
                floating_ip_type_name = bm_contract_material_ip.floating_ip_type_name
                base_price = str(bm_contract_material_ip.base_price)

            # 查找物料带宽的信息
            if max_band_ip_dict.get("shared_qos_policy_type"):
                material_band_material_number = "CBMS-N-S003"
                band_width_type_name = "共享带宽"
                material_band_base_price = "根据实际共享带宽大小而定"
            else:
                if max_band > 5:
                    band_type = "base2"
                else:
                    band_type = "base1"
                bm_contract_material_band = service_model.BmContractBandWidthaterial.objects.filter(
                    band_width_type="band_width", charge_type=band_type).first()
                if not bm_contract_material_band:
                    material_band_material_number = ""
                    band_width_type_name = ""
                    material_band_base_price = ""
                else:
                    material_band_material_number = bm_contract_material_band.material_number
                    band_width_type_name = bm_contract_material_band.band_width_type_name
                    material_band_base_price = str(bm_contract_material_band.base_price)

            # 查找授权人的信息
            bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(id=bm_contract_material_account_id).first()
            if not bm_contract_authorizer:
                account = ""
            else:
                account = bm_contract_authorizer.account
            # 查找下单者的一些信息
            bm_account_info = auth_models.BmUserInfo.objects.filter(id=max_band_ip_dict.get("account_id")).first()
            if not bm_account_info:
                identity_name = ""
                user_account = ""
            else:
                identity_name = bm_account_info.identity_name
                user_account = bm_account_info.account
            # 查找订单信息
            bm_contract_order = service_model.BmServiceOrder.objects.filter(id=max_band_ip_dict.get("order_id")).first()
            if not bm_contract_order:
                region = ""
            else:
                region = bm_contract_order.region

            # 查找项目信息
            bm_contract_project = service_model.BmProject.objects.filter(id=max_band_ip_dict.get("project_id")).first()
            project_name = ""
            if bm_contract_project:
                project_name = bm_contract_project.project_name

            material_ip_dict = {
                "用户ID": max_band_ip_dict.get("account_id"),
                "用户名称": identity_name,
                "用户邮箱": user_account,
                "合同编号": max_band_ip_dict.get("contract_number"),
                "查询日期": date_ip,
                "带宽物料编码": material_band_material_number,
                "带宽类型": band_width_type_name,
                "带宽价格": material_band_base_price,
                "IP物料编码": material_number,
                "IP物料类型": floating_ip_type_name,
                "IP价格": base_price,
                "合同可用区": region,
                "销售姓名": sales,
                "公司编码": enterprise_number,
                "公司所属区": location,
                "客服姓名": customer_service_name,
                "服务到期时间": service_expired_time,
                "服务开始时间": service_start_time,
                "合同开始时间": bm_contract_material_start_date,
                "合同到期时间": bm_contract_material_expire_date,
                "客户名称": bm_contract_material_customer_name,
                "合同授权人": bm_contract_material_authorizer,
                "合同类型": bm_contract_material_contract_type,
                "合同授权人邮箱": account,
                "IP类型": max_band_ip_dict.get("external_line_type"),
                "IP类型名称": max_band_ip_dict.get("external_name"),
                "IP类型ID": max_band_ip_dict.get("external_name_id"),
                "IP": max_band_ip_dict.get("floating_ip"),
                "ip_id": max_band_ip_dict.get("floating_ip_id"),
                "订单号": max_band_ip_dict.get("order_id"),
                "项目ID": max_band_ip_dict.get("project_id"),
                "项目名称": project_name,
                "服务状态": max_band_ip_dict.get("status"),
                "最大带宽": max_band,
            }
            response_obj.content = material_ip_dict
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "floating_ip_id %s 查询失败！" % floating_ip_id,
                                    "admin_info": str(ex)}
        return response_obj

    @staticmethod
    def contract_lb_seasonal(start_date, end_date):
        response_obj = ResponseObj()
        try:
            begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            lb_list_obj = service_model.BmServiceLoadbalance.objects.filter(
                created_at__lte=end_date,
                created_at__gte=begin_date,
            )
            if not lb_list_obj:
                response_obj.content = []
                return response_obj
            lb_list = []
            for lb_obj in lb_list_obj:
                # 查找LB得删除时间
                if lb_obj.deleted:
                    delete_time = lb_obj.updated_at
                else:
                    delete_time = ""
                # 查找合同的一些信息
                bm_contract_material_obj = auth_models.BmContract.objects.filter(
                    contract_number=lb_obj.contract_number).first()
                if bm_contract_material_obj:
                    bm_contract_material = bm_contract_material_obj.__dict__
                    bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                    bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                    bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                    bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                    bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                else:
                    bm_contract_material_customer_id = ""
                    bm_contract_material_account_id = ""
                    bm_contract_material_customer_name = ""
                    bm_contract_material_authorizer = ""
                    bm_contract_material_contract_type = ""
                # 查找客户的信息
                bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()
                if not bm_contract_user:
                    sales = ""
                    enterprise_number = ""
                    location = ""
                    customer_service_name = ""
                else:
                    sales = bm_contract_user.sales
                    enterprise_number = bm_contract_user.enterprise_number
                    location = bm_contract_user.location
                    customer_service_name = bm_contract_user.customer_service_name
                # 查找授权人的信息
                bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(
                    id=bm_contract_material_account_id).first()
                if not bm_contract_authorizer:
                    account = ""
                else:
                    account = bm_contract_authorizer.account
                # 查找订单信息
                bm_contract_order = service_model.BmServiceOrder.objects.filter(id=lb_obj.order_id).first()
                if not bm_contract_order:
                    region = ""
                else:
                    region = bm_contract_order.region
                # 查找下单者的一些信息
                bm_account_info = auth_models.BmUserInfo.objects.filter(id=lb_obj.account_id).first()
                if not bm_account_info:
                    user_account = ""
                    identity_name = ""
                else:
                    user_account = bm_account_info.account
                    identity_name = bm_account_info.identity_name
                # 查找项目信息
                bm_contract_project = service_model.BmProject.objects.filter(id=lb_obj.project_id).first()
                if not bm_contract_project:
                    project_name = ""
                else:
                    project_name = bm_contract_project.project_name

                # 查找对应IP地址
                if lb_obj.is_public:
                    bm_floating_ip = service_model.BmServiceFloatingIp.objects.filter(
                        instance_uuid=lb_obj.loadbalance_id).first()
                    if not bm_floating_ip:
                        ip_adress = ""
                    else:
                        ip_adress = bm_floating_ip.floating_ip

                # 查找LB物料信息
                bm_material_lb = service_model.BmServiceMaterialLb.objects.filter(
                    charge_type=auth_models.CHAR_TYPE).first()
                if not bm_material_lb:
                    material_number = ""
                    lb_type_name = ""
                    base_price = ""
                else:
                    material_number = bm_material_lb.material_number
                    lb_type_name = bm_material_lb.lb_type_name
                    base_price = str(bm_material_lb.base_price)

                material_lb_dict_all = {
                    "用户ID": lb_obj.account_id,
                    "用户邮箱": user_account,
                    "用户姓名": identity_name,
                    "合同编码": lb_obj.contract_number,
                    "创建时间": lb_obj.first_create_at,
                    "订单号": lb_obj.order_id,
                    "项目ID": lb_obj.project_id,
                    "项目名称": project_name,
                    "服务结束时间": delete_time,
                    "所绑定的IP地址": ip_adress,
                    "负载均衡实例id": lb_obj.loadbalance_id,
                    "LB名称": lb_obj.loadbalance_name,
                    "客户名称": bm_contract_material_customer_name,
                    "合同授权人": bm_contract_material_authorizer,
                    "合同类型": bm_contract_material_contract_type,
                    "销售姓名": sales,
                    "公司编码": enterprise_number,
                    "公司所属区": location,
                    "客服姓名": customer_service_name,
                    "合同授权人邮箱": account,
                    "合同可用区": region,
                    "LB物料编码": material_number,
                    "LB物料类型": lb_type_name,
                    "基础价格": base_price
                }
                lb_list.append(material_lb_dict_all)

            response_obj.content = lb_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "NAT网关物料查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    # 查询所有物料某一天的计量信息并存储到数据库表当中
    def material_into_mysql(self, start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出当前周期下的所有IP
            material_ip_id_list = []
            begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            start_date = begin_date.replace(day=1)
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            # 筛选出当天/当前周期创建的IP
            floating_ip_id_list_obj = service_model.BmServiceFloatingIp.objects.filter(
                create_at__lte=end_date, create_at__gte=start_date).values('floating_ip_id').annotate(
                Count=Count('floating_ip_id'))
            for floating_ip_dict in floating_ip_id_list_obj:
                floating_ip_id = floating_ip_dict.get("floating_ip_id")
                if not floating_ip_id:
                    continue
                material_ip_id_list.append(floating_ip_id)
            # 筛选出开始时间之前未结束计费的IP---需要叠加在本月的数据当中进行计费
            floating_ip_id_list_before_obj = service_model.BmServiceFloatingIp.objects.filter(
                create_at__lte=start_date, is_measure_end=False).values('floating_ip_id').annotate(
                Count=Count('floating_ip_id'))
            for floating_ip_dict in floating_ip_id_list_before_obj:
                floating_ip_id = floating_ip_dict.get("floating_ip_id")
                if not floating_ip_id:
                    continue
                material_ip_id_list.append(floating_ip_id)
            while begin_date < end_date:
                material_ip_date = datetime.datetime.strftime(begin_date, "%Y-%m-%d")
                # 查询弹性IP某一天的计量信息
                for floating_ip_id_single in material_ip_id_list:
                    material_day_ip_obj = self.material_ip_day_by_ip_id(
                        material_ip_date=material_ip_date, floating_ip_id=floating_ip_id_single)
                    if not material_day_ip_obj.is_ok:
                        raise Exception(material_day_ip_obj)
                    # 查询结果为空跳过
                    if material_day_ip_obj.content:
                        float_ip_dict = material_day_ip_obj.content
                        server_ip__dict = {
                            "account_id": float_ip_dict["用户ID"],
                            "identity_name": float_ip_dict["用户名称"],
                            "user_account": float_ip_dict["用户邮箱"],
                            "contract_number": float_ip_dict["合同编号"],
                            "date": float_ip_dict["查询日期"],
                            "band_material_number": float_ip_dict["带宽物料编码"],
                            "band_width_type_name": float_ip_dict["带宽类型"],
                            "material_band_base_price": str(float_ip_dict["带宽价格"]),
                            "material_number": float_ip_dict["IP物料编码"],
                            "floating_ip_type_name": float_ip_dict["IP物料类型"],
                            "base_price": str(float_ip_dict["IP价格"]),
                            "region": float_ip_dict["合同可用区"],
                            "sales": float_ip_dict["销售姓名"],
                            "enterprise_number": float_ip_dict["公司编码"],
                            "location": float_ip_dict["公司所属区"],
                            "customer_service_name": float_ip_dict["客服姓名"],
                            "service_expired_time": float_ip_dict["服务到期时间"],
                            "service_start_time": float_ip_dict["服务开始时间"],
                            "contract_start_date": float_ip_dict["合同开始时间"],
                            "contract_expire_date": float_ip_dict["合同到期时间"],
                            "contract_customer_name": float_ip_dict["客户名称"],
                            "contract_authorizer": float_ip_dict["合同授权人"],
                            "contract_type": float_ip_dict["合同类型"],
                            "contract_authorizer_account": float_ip_dict["合同授权人邮箱"],
                            "external_line_type": float_ip_dict["IP类型"],
                            "external_name": float_ip_dict["IP类型名称"],
                            "external_name_id": float_ip_dict["IP类型ID"],
                            "floating_ip": float_ip_dict["IP"],
                            "floating_ip_id": float_ip_dict["ip_id"],
                            "order_id": float_ip_dict["订单号"],
                            "project_id": float_ip_dict["项目ID"],
                            "project_name": float_ip_dict["项目名称"],
                            "status": float_ip_dict["服务状态"],
                            "max_band": float_ip_dict["最大带宽"]
                        }
                        ip_result = service_model.BmMaterialFloatingIpSeasonal.objects.create(
                            **server_ip__dict)
                # # 查询云硬盘某一天的物料信息
                material_day_volume_obj = self.contract_volume_seasonal(start_date=material_ip_date,
                                                                        end_date=material_ip_date)
                if not material_day_volume_obj.is_ok:
                    raise Exception(material_day_volume_obj)
                # 查询结果为空跳过
                if material_day_volume_obj.content:
                    volume_dict_list = material_day_volume_obj.content
                    for volume_dict in volume_dict_list:
                        server_volume__dict = {
                            "account_id": volume_dict["用户ID"],
                            "user_account": volume_dict["用户姓名"],
                            "identity_name": volume_dict["用户邮箱"],
                            "contract_number": volume_dict["合同编码"],
                            "create_at": volume_dict["云硬盘创建时间"],
                            "name": volume_dict["云硬盘名称"],
                            "order_id": volume_dict["订单号"],
                            "project_id": volume_dict["项目ID"],
                            "project_name": volume_dict["项目名称"],
                            "size": volume_dict["云硬盘大小"],
                            "end_at": volume_dict["服务结束时间"],
                            "volume_id": volume_dict["云硬盘id"],
                            "volume_type": volume_dict["云硬盘类型"],
                            "contract_customer_name": volume_dict["客户名称"],
                            "contract_authorizer": volume_dict["合同授权人"],
                            "contract_type": volume_dict["合同类型"],
                            "sales": volume_dict["销售姓名"],
                            "enterprise_number": volume_dict["公司编码"],
                            "location": volume_dict["公司所属区"],
                            "customer_service_name": volume_dict["客服名称"],
                            "account": volume_dict["合同授权人邮箱"],
                            "region": volume_dict["合同可用区"],
                            "material_number": volume_dict["云硬盘物料编码"],
                            "volume_type_name": volume_dict["云硬盘类型名称"],
                            "base_price": str(volume_dict["基础价格"]),
                            "date": material_ip_date
                        }
                        volume_result = service_model.BmMaterialVolumeSeasonal.objects.create(
                            **server_volume__dict)

                # # 查询云硬盘备份某一天的物料信息
                material_day_volume_bak_obj = self.contract_volume_bak_seasonal(start_date=material_ip_date,
                                                                                end_date=material_ip_date)
                if not material_day_volume_bak_obj.is_ok:
                    raise Exception(material_day_volume_bak_obj)
                # 查询结果为空跳过
                if material_day_volume_bak_obj.content:
                    volume_back_list = material_day_volume_bak_obj.content
                    for volume_back_dict in volume_back_list:
                        material_volume_back_dict_all = {
                            "account_id": volume_back_dict["用户ID"],
                            "user_account": volume_back_dict["用户邮箱"],
                            "identity_name": volume_back_dict["用户姓名"],
                            "contract_number": volume_back_dict["合同编码"],
                            "create_at": volume_back_dict["备份时间"],
                            "backup_name": volume_back_dict["云硬盘备份名称"],
                            "order_id": volume_back_dict["订单号"],
                            "project_id": volume_back_dict["项目ID"],
                            "project_name": volume_back_dict["项目名称"],
                            "service_count": volume_back_dict["云硬盘大小"],
                            "delete_time": volume_back_dict["服务结束时间"],
                            "volume_id": volume_back_dict["云硬盘id"],
                            "contract_customer_name": volume_back_dict["客户名称"],
                            "contract_authorizer": volume_back_dict["合同授权人"],
                            "contract_type": volume_back_dict["合同类型"],
                            "sales": volume_back_dict["销售姓名"],
                            "enterprise_number": volume_back_dict["公司编码"],
                            "location": volume_back_dict["公司所属区"],
                            "customer_service_name": volume_back_dict["客服姓名"],
                            "account": volume_back_dict["合同授权人邮箱"],
                            "region": volume_back_dict["合同可用区"],
                            "material_number": volume_back_dict["云硬盘备份物料编码"],
                            "volume_type_name": volume_back_dict["云硬盘物料类型"],
                            "base_price": str(volume_back_dict["基础价格"]),
                            "date": material_ip_date
                        }
                        volume_bak_result = service_model.BmMaterialVolumeBakSeasonal.objects.create(
                            **material_volume_back_dict_all)

                # # 查询裸金属某一天的物料信息
                material_day_machine_obj = self.contract_machine_seasonal(start_date=material_ip_date,
                                                                          end_date=material_ip_date)
                if not material_day_machine_obj.is_ok:
                    raise Exception(material_day_machine_obj)
                # 查询结果为空跳过
                if material_day_machine_obj.content:
                    machine_dict_list = material_day_machine_obj.content
                    for machine_dict in machine_dict_list:
                        material_machine_dict_all = {
                            "account_id": machine_dict["用户ID"],
                            "user_account": machine_dict["用户邮箱"],
                            "identity_name": machine_dict["用户姓名"],
                            "contract_number": machine_dict["合同编号"],
                            "create_at": machine_dict["机器创建时间"],
                            "flavor_name": machine_dict["flavor名称"],
                            "image_name": machine_dict["镜像名称"],
                            "monitoring": machine_dict["是否携带监控"],
                            "vulnerability_scanning": machine_dict["是否携带漏洞扫描"],
                            "network": machine_dict["网络名称"],
                            "network_path_type": machine_dict["网络类型名称"],
                            "service_name": machine_dict["机器名称"],
                            "order_id": machine_dict["订单号"],
                            "project_id": machine_dict["项目ID"],
                            "project_name": machine_dict["项目名称"],
                            "product_type": machine_dict["产品类型"],
                            "service_count": machine_dict["机器数量"],
                            "delete_at": machine_dict["服务结束时间"],
                            "contract_customer_name": machine_dict["客户名称"],
                            "contract_authorizer": machine_dict["合同授权人"],
                            "contract_type": machine_dict["合同类型"],
                            "sales": machine_dict["销售姓名"],
                            "enterprise_number": machine_dict["公司编号"],
                            "location": machine_dict["公司所属区"],
                            "customer_service_name": machine_dict["客服姓名"],
                            "account": machine_dict["合同授权人邮箱"],
                            "region": machine_dict["合同可用区"],
                            "material_number": machine_dict["Flavor物料编码"],
                            "type": machine_dict["flavor类型"],
                            "base_price": str(machine_dict["基础价格"]),
                            "flavor_info": machine_dict["机器配置信息"],
                            "cpu_model": machine_dict["CPU"],
                            "cpu_core": machine_dict["内核"],
                            "cpu_hz": machine_dict["主频"],
                            "ram": machine_dict["内存"],
                            "disk": machine_dict["磁盘信息"],
                            "date": material_ip_date
                        }
                        machine_result = service_model.BmMaterialMachineSeasonal.objects.create(
                            **material_machine_dict_all)
                #
                # # 查询NAT网关某一天的物料信息
                material_day_nat_getway_obj = self.contract_nat_seasonal(start_date=material_ip_date,
                                                                         end_date=material_ip_date)
                if not material_day_nat_getway_obj.is_ok:
                    raise Exception(material_day_nat_getway_obj)
                # 查询结果为空跳过
                if material_day_nat_getway_obj.content:
                    net_getway_list = material_day_nat_getway_obj.content
                    for net_getway_dict in net_getway_list:
                        material_nat_dict_all = {
                            "account_id": net_getway_dict["用户ID"],
                            "user_account": net_getway_dict["用户邮箱"],
                            "identity_name": net_getway_dict["用户姓名"],
                            "contract_number": net_getway_dict["合同编码"],
                            "create_at": net_getway_dict["创建时间"],
                            "order_id": net_getway_dict["订单号"],
                            "project_id": net_getway_dict["项目ID"],
                            "project_name": net_getway_dict["项目名称"],
                            "delete_at": net_getway_dict["服务结束时间"],
                            "net_getway_id": net_getway_dict["NAT网关id"],
                            "net_getway_name": net_getway_dict["NAT网关名称"],
                            "contract_customer_name": net_getway_dict["客户名称"],
                            "contract_authorizer": net_getway_dict["合同授权人"],
                            "contract_type": net_getway_dict["合同类型"],
                            "sales": net_getway_dict["销售姓名"],
                            "enterprise_number": net_getway_dict["公司编码"],
                            "location": net_getway_dict["公司所属区"],
                            "customer_service_name": net_getway_dict["客服姓名"],
                            "account": net_getway_dict["合同授权人邮箱"],
                            "region": net_getway_dict["合同可用区"],
                            "material_number": net_getway_dict["NAT物料编码"],
                            "nat_getway_type_name": net_getway_dict["NAT物料类型"],
                            "base_price": str(net_getway_dict["基础价格"]),
                            "date": material_ip_date
                        }
                        nat_getway_result = service_model.BmMaterialNetGetwaySeasonal.objects.create(
                            **material_nat_dict_all)
                # # 查询负载均衡某一天的物料信息
                material_day_lb_obj = self.contract_lb_seasonal(start_date=material_ip_date,
                                                                end_date=material_ip_date)
                if not material_day_lb_obj.is_ok:
                    raise Exception(material_day_lb_obj)
                # 查询结果为空跳过
                if material_day_lb_obj.content:
                    lb_list = material_day_lb_obj.content
                    for lb_dict in lb_list:
                        material_lb_dict_all = {
                            "account_id": lb_dict["用户ID"],
                            "user_account": lb_dict["用户邮箱"],
                            "identity_name": lb_dict["用户姓名"],
                            "contract_number": lb_dict["合同编码"],
                            "create_at": lb_dict["创建时间"],
                            "order_id": lb_dict["订单号"],
                            "project_id": lb_dict["项目ID"],
                            "project_name": lb_dict["项目名称"],
                            "delete_at": lb_dict["服务结束时间"],
                            "ip_adress": lb_dict["所绑定的IP地址"],
                            "loadbalance_id": lb_dict["负载均衡实例id"],
                            "loadbalance_name": lb_dict["LB名称"],
                            "contract_customer_name": lb_dict["客户名称"],
                            "contract_authorizer": lb_dict["合同授权人"],
                            "contract_type": lb_dict["合同类型"],
                            "sales": lb_dict["销售姓名"],
                            "enterprise_number": lb_dict["公司编码"],
                            "location": lb_dict["公司所属区"],
                            "customer_service_name": lb_dict["客服姓名"],
                            "account": lb_dict["合同授权人邮箱"],
                            "region": lb_dict["合同可用区"],
                            "material_number": lb_dict["LB物料编码"],
                            "lb_type_name": lb_dict["LB物料类型"],
                            "base_price": str(lb_dict["基础价格"]),
                            "date": material_ip_date
                        }
                        lb_result = service_model.BmMaterialLbSeasonal.objects.create(
                            **material_lb_dict_all)

                begin_date += datetime.timedelta(days=1)

            response_obj.content = "数据导入数据库成功！！！"
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "数据导入数据库失败！",
                                    "admin_info": str(ex)}
        return response_obj

    def get_material_from_mysql(self, start_date, end_date):
        response_obj = ResponseObj()
        try:
            ip_all_list = []
            volume_all_list = []
            volume_bak_all_list = []
            machine_all_list = []
            nat_all_list = []
            lb_all_list = []
            # 筛选出当前周期下的所有IP
            begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            # 查询弹性IP某时间段的计量信息
            ip_list_obj = service_model.BmMaterialFloatingIpSeasonal.objects.filter(
                date__lte=end_date,
                date__gte=begin_date)
            if ip_list_obj:
                for ip_dict in ip_list_obj:
                    server_ip__dict = {
                        "用户ID": ip_dict.account_id,
                        "用户名称": ip_dict.identity_name,
                        "用户邮箱": ip_dict.user_account,
                        "合同编号": ip_dict.contract_number,
                        "查询日期": ip_dict.date,
                        "带宽物料编码": ip_dict.band_material_number,
                        "带宽类型": ip_dict.band_width_type_name,
                        "带宽价格": ip_dict.material_band_base_price,
                        "IP物料编码": ip_dict.material_number,
                        "IP物料类型": ip_dict.floating_ip_type_name,
                        "IP价格": ip_dict.base_price,
                        "合同可用区": ip_dict.region,
                        "销售姓名": ip_dict.sales,
                        "公司编码": ip_dict.enterprise_number,
                        "公司所属区": ip_dict.location,
                        "客服姓名": ip_dict.customer_service_name,
                        "服务到期时间": ip_dict.service_expired_time,
                        "服务开始时间": ip_dict.service_start_time,
                        "合同开始时间": ip_dict.contract_start_date,
                        "合同到期时间": ip_dict.contract_expire_date,
                        "客户名称": ip_dict.contract_customer_name,
                        "合同授权人": ip_dict.contract_authorizer,
                        "合同类型": ip_dict.contract_type,
                        "合同授权人邮箱": ip_dict.contract_authorizer_account,
                        "IP类型": ip_dict.external_line_type,
                        "IP类型名称": ip_dict.external_name,
                        "IP类型ID": ip_dict.external_name_id,
                        "IP": ip_dict.floating_ip,
                        "ip_id": ip_dict.floating_ip_id,
                        "订单号": ip_dict.order_id,
                        "项目ID": ip_dict.project_id,
                        "项目名称": ip_dict.project_name,
                        "服务状态": ip_dict.status,
                        "最大带宽": ip_dict.max_band,
                    }
                    ip_all_list.append(server_ip__dict)

            # 查询云硬盘某时间段计量信息
            volume_list_obj = service_model.BmMaterialVolumeSeasonal.objects.filter(
                date__lte=end_date,
                date__gte=begin_date)
            if volume_list_obj:
                for volume_dict in volume_list_obj:
                    material_volume_dict_all = {
                        "用户ID": volume_dict.account_id,
                        "用户邮箱": volume_dict.user_account,
                        "用户姓名": volume_dict.identity_name,
                        "合同编码": volume_dict.contract_number,
                        "云硬盘创建时间": volume_dict.create_at,
                        "云硬盘名称": volume_dict.name,
                        "订单号": volume_dict.order_id,
                        "项目ID": volume_dict.project_id,
                        "项目名称": volume_dict.project_name,
                        "云硬盘大小": volume_dict.size,
                        "服务结束时间": volume_dict.end_at,
                        "云硬盘id": volume_dict.volume_id,
                        "云硬盘类型": volume_dict.volume_type,
                        "客户名称": volume_dict.contract_customer_name,
                        "合同授权人": volume_dict.contract_authorizer,
                        "合同类型": volume_dict.contract_type,
                        "销售姓名": volume_dict.sales,
                        "公司编码": volume_dict.enterprise_number,
                        "公司所属区": volume_dict.location,
                        "客服名称": volume_dict.customer_service_name,
                        "合同授权人邮箱": volume_dict.account,
                        "合同可用区": volume_dict.region,
                        "云硬盘物料编码": volume_dict.material_number,
                        "云硬盘类型名称": volume_dict.volume_type_name,
                        "基础价格": volume_dict.base_price
                    }
                    volume_all_list.append(material_volume_dict_all)

            # 查询云硬盘备份某时间段计量信息
            volume_bak_list_obj = service_model.BmMaterialVolumeBakSeasonal.objects.filter(
                date__lte=end_date,
                date__gte=begin_date)
            if volume_bak_list_obj:
                for volume_dict in volume_bak_list_obj:
                    material_volume_dict_all = {
                        "用户ID": volume_dict.account_id,
                        "用户邮箱": volume_dict.user_account,
                        "用户姓名": volume_dict.identity_name,
                        "合同编码": volume_dict.volume_obj.contract_number,
                        "备份时间": volume_dict.volume_obj.create_at,
                        "云硬盘备份名称": volume_dict.volume_obj.backup_name,
                        "订单号": volume_dict.volume_obj.order_id,
                        "项目ID": volume_dict.volume_obj.project_id,
                        "项目名称": volume_dict.project_name,
                        "可用区": volume_dict.region,
                        "云硬盘大小": volume_dict.service_count,
                        "服务结束时间": volume_dict.delete_time,
                        "云硬盘id": volume_dict.volume_id,
                        "客户名称": volume_dict.contract_customer_name,
                        "合同授权人": volume_dict.contract_authorizer,
                        "合同类型": volume_dict.contract_type,
                        "销售姓名": volume_dict.sales,
                        "公司编码": volume_dict.enterprise_number,
                        "公司所属区": volume_dict.location,
                        "客服姓名": volume_dict.customer_service_name,
                        "合同授权人邮箱": volume_dict.account,
                        "合同可用区": volume_dict.region,
                        "云硬盘备份物料编码": volume_dict.material_number,
                        "云硬盘物料类型": volume_dict.volume_type_name,
                        "基础价格": volume_dict.base_price
                    }
                    volume_bak_all_list.append(material_volume_dict_all)

            # 查询裸金属某一时间段计量信息
            machine_list_obj = service_model.BmMaterialMachineSeasonal.objects.filter(
                date__lte=end_date,
                date__gte=begin_date)
            if machine_list_obj:
                for machine_dict in machine_list_obj:
                    material_machine_dict_all = {
                        "用户ID": machine_dict.account_id,
                        "用户邮箱": machine_dict.user_account,
                        "用户姓名": machine_dict.identity_name,
                        "合同编号": machine_dict.contract_number,
                        "机器创建时间": machine_dict.create_at,
                        "flavor名称": machine_dict.flavor_name,
                        "镜像名称": machine_dict.image_name,
                        "是否携带监控": machine_dict.monitoring,
                        "是否携带漏洞扫描": machine_dict.vulnerability_scanning,
                        "网络名称": machine_dict.network,
                        "网络类型名称": machine_dict.network_path_type,
                        "机器名称": machine_dict.service_name,
                        "订单号": machine_dict.order_id,
                        "项目ID": machine_dict.project_id,
                        "项目名称": machine_dict.project_name,
                        "产品类型": machine_dict.product_type,
                        "机器数量": machine_dict.service_count,
                        "服务结束时间": machine_dict.delete_at,
                        "客户名称": machine_dict.contract_customer_name,
                        "合同授权人": machine_dict.contract_authorizer,
                        "合同类型": machine_dict.contract_type,
                        "销售姓名": machine_dict.sales,
                        "公司编号": machine_dict.enterprise_number,
                        "公司所属区": machine_dict.location,
                        "客服姓名": machine_dict.customer_service_name,
                        "合同授权人邮箱": machine_dict.account,
                        "合同可用区": machine_dict.region,
                        "Flavor物料编码": machine_dict.material_number,
                        "flavor类型": machine_dict.type,
                        "基础价格": machine_dict.base_price,
                        "机器配置信息": machine_dict.flavor_info,
                        "CPU": machine_dict.cpu_model,
                        "内核": machine_dict.cpu_core,
                        "主频": machine_dict.cpu_hz,
                        "内存": machine_dict.ram,
                        "磁盘信息": machine_dict.disk
                    }
                    machine_all_list.append(material_machine_dict_all)

            # 查询NAT网关某一段时间的计量信息
            nat_list_obj = service_model.BmMaterialNetGetwaySeasonal.objects.filter(
                date__lte=end_date,
                date__gte=begin_date)
            if nat_list_obj:
                for nat_obj in nat_list_obj:
                    material_nat_dict_all = {
                        "用户ID": nat_obj.account_id,
                        "用户邮箱": nat_obj.user_account,
                        "用户姓名": nat_obj.identity_name,
                        "合同编码": nat_obj.contract_number,
                        "创建时间": nat_obj.create_at,
                        "订单号": nat_obj.order_id,
                        "项目ID": nat_obj.project_id,
                        "项目名称": nat_obj.project_name,
                        "服务结束时间": nat_obj.delete_at,
                        "NAT网关id": nat_obj.net_getway_id,
                        "NAT网关名称": nat_obj.net_getway_name,
                        "客户名称": nat_obj.contract_customer_name,
                        "合同授权人": nat_obj.contract_authorizer,
                        "合同类型": nat_obj.contract_type,
                        "销售姓名": nat_obj.sales,
                        "公司编码": nat_obj.enterprise_number,
                        "公司所属区": nat_obj.location,
                        "客服姓名": nat_obj.customer_service_name,
                        "合同授权人邮箱": nat_obj.account,
                        "合同可用区": nat_obj.region,
                        "NAT物料编码": nat_obj.material_number,
                        "NAT物料类型": nat_obj.nat_getway_type_name,
                        "基础价格": nat_obj.base_price
                    }
                    nat_all_list.append(material_nat_dict_all)

            # 查询负载均衡某一段时间的计量信息
            lb_list_obj = service_model.BmMaterialLbSeasonal.objects.filter(
                date__lte=end_date,
                date__gte=begin_date)
            if lb_list_obj:
                for lb_obj in lb_list_obj:
                    material_lb_dict_all = {
                        "用户ID": lb_obj.account_id,
                        "用户邮箱": lb_obj.user_account,
                        "用户姓名": lb_obj.identity_name,
                        "合同编码": lb_obj.contract_number,
                        "创建时间": lb_obj.create_at,
                        "订单号": lb_obj.order_id,
                        "项目ID": lb_obj.project_id,
                        "项目名称": lb_obj.project_name,
                        "服务结束时间": lb_obj.delete_at,
                        "所绑定的IP地址": lb_obj.ip_adress,
                        "负载均衡实例id": lb_obj.loadbalance_id,
                        "LB名称": lb_obj.loadbalance_name,
                        "客户名称": lb_obj.contract_customer_name,
                        "合同授权人": lb_obj.contract_authorizer,
                        "合同类型": lb_obj.contract_type,
                        "销售姓名": lb_obj.sales,
                        "公司编码": lb_obj.enterprise_number,
                        "公司所属区": lb_obj.location,
                        "客服姓名": lb_obj.customer_service_name,
                        "合同授权人邮箱": lb_obj.account,
                        "合同可用区": lb_obj.region,
                        "LB物料编码": lb_obj.material_number,
                        "LB物料类型": lb_obj.lb_type_name,
                        "基础价格": lb_obj.base_price
                    }
                    lb_all_list.append(material_lb_dict_all)

            material_dict = {
                "material_ip": ip_all_list,
                "material_volume": volume_all_list,
                "material_volume_bak": volume_bak_all_list,
                "material_machine": machine_all_list,
                "material_nat_getway": nat_all_list,
                "material_lb": lb_all_list
            }
            response_obj.content = material_dict
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "数据导出失败！",
                                    "admin_info": str(ex)}

        return response_obj

    def material_share_band_seasonal(self, start_date, end_date):
        response_obj = ResponseObj()
        try:
            # 筛选出当前周期下的所有共享带宽
            material_share_band_list = []
            material_share_band_id_list = []
            begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            # 筛选出当月创建的共享带宽
            share_band_list_obj = service_model.BmShareBandWidth.objects.filter(
                create_at__lte=end_date, create_at__gte=begin_date).values('shared_bandwidth_id').annotate(
                Count=Count('shared_bandwidth_id'))
            for share_band_dict in share_band_list_obj:
                share_band_id = share_band_dict.get("shared_bandwidth_id")
                if not share_band_id:
                    continue
                material_share_band_id_list.append(share_band_id)
            # 筛选出当月之前未结束计费的共享带宽--需要叠加在本月的数据当中进行计费
            share_band_id_list_before_obj = service_model.BmShareBandWidth.objects.filter(
                create_at__lte=begin_date, is_measure_end=False).values('shared_bandwidth_id').annotate(
                Count=Count('shared_bandwidth_id'))
            for share_band_dict in share_band_id_list_before_obj:
                share_band_id = share_band_dict.get("shared_bandwidth_id")
                if not share_band_id:
                    continue
                material_share_band_id_list.append(share_band_id)
            while begin_date < end_date:
                material_date = datetime.datetime.strftime(begin_date, "%Y-%m-%d")
                # 查询弹性IP某一天的计量信息
                for share_band_id_single in material_share_band_id_list:
                    material_day_share_band_obj = self.material_share_band_day_by_ip_id(
                        material_date=material_date, shared_bandwidth_id=share_band_id_single)
                    if not material_day_share_band_obj.is_ok:
                        raise Exception(material_day_share_band_obj)
                    # 查询结果为空跳过
                    if material_day_share_band_obj.content:
                        material_share_band_list.append(material_day_share_band_obj.content)

                begin_date += datetime.timedelta(days=1)

            response_obj.content = material_share_band_list
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料共享带宽信息查询失败！",
                                    "admin_info": str(ex)}
        return response_obj

    def material_share_band_day_by_ip_id(self, material_date, shared_bandwidth_id):
        response_obj = ResponseObj()
        try:
            # 进行数据处理
            share_band_list_obj = service_model.BmShareBandWidth.objects.filter(
                shared_bandwidth_id=shared_bandwidth_id).order_by("create_at")
            share_band_list = [u.__dict__ for u in share_band_list_obj]
            share_band_first_obj = share_band_list_obj.first()
            service_start_time = share_band_first_obj.first_create_at

            bm_material_share_band_null = share_band_list_obj.filter(update_at__isnull=True)
            share_band_update_null = [u.__dict__ for u in bm_material_share_band_null]

            # 到期时间的处理
            bm_material_share_band_delete = share_band_list_obj.filter(status="deleted").first()
            if bm_material_share_band_delete:
                service_expired_time = bm_material_share_band_delete.deleted_at
            else:
                service_expired_time = "-"
            # for material_share_band in share_band_list:
            #     if material_share_band["status"] == "deleted":
            #         service_expired_time = material_share_band["update_at"]
            #         break

            # 筛选出某天的数据
            create_at = datetime.datetime.strptime(material_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            update_at = datetime.datetime.strptime(material_date, '%Y-%m-%d')
            bm_material_share_band_info = service_model.BmShareBandWidth.objects.filter(
                create_at__lte=create_at, update_at__gte=update_at, shared_bandwidth_id=shared_bandwidth_id).order_by(
                "create_at")
            material_share_band_list_info = [u.__dict__ for u in bm_material_share_band_info]

            # 进行数据拼接得到当天所有共享带宽的完整数据
            if bm_material_share_band_null:
                if share_band_update_null[0]["create_at"] <= create_at:
                    material_share_band_list_info.extend(share_band_update_null)

            # 进行查到的数据为空数据的处理
            if not material_share_band_list_info:
                response_obj.message = {"user_info": "{material_date}查询为空！".format(material_date=material_date)}
                return response_obj

            # 找出当天的最大带宽
            max_band = -1
            max_band_dict = dict()
            for material_share_band in material_share_band_list_info:
                material_share_band_size = int(material_share_band["max_kbps"])
                if max_band <= material_share_band_size:
                    max_band = material_share_band_size
                    max_band_dict = material_share_band

            # 查找合同的一些信息
            bm_contract_material_obj = auth_models.BmContract.objects.filter(
                contract_number=max_band_dict.get("contract_number")).first()
            if bm_contract_material_obj:
                bm_contract_material = bm_contract_material_obj.__dict__
                bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
                bm_contract_material_account_id = bm_contract_material.get("account_id", "")
                bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
                bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
                bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
                bm_contract_material_expire_date = bm_contract_material.get("expire_date", "")
                bm_contract_material_start_date = bm_contract_material.get("start_date", "")
            else:
                bm_contract_material_customer_id = ""
                bm_contract_material_account_id = ""
                bm_contract_material_customer_name = ""
                bm_contract_material_authorizer = ""
                bm_contract_material_contract_type = ""
                bm_contract_material_start_date = ""
                bm_contract_material_expire_date = ""

            # 查找客户的信息
            bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()

            if not bm_contract_user:
                sales = ""
                enterprise_number = ""
                location = ""
                customer_service_name = ""
            else:
                sales = bm_contract_user.sales
                enterprise_number = bm_contract_user.enterprise_number
                location = bm_contract_user.location
                customer_service_name = bm_contract_user.customer_service_name

            # 查找物料带宽的信息
            if max_band > 5120:
                band_type = "base2"
            else:
                band_type = "base1"
            bm_contract_material_band = service_model.BmContractBandWidthaterial.objects.filter(
                band_width_type="shared_band_width", charge_type=band_type).first()
            if not bm_contract_material_band:
                material_band_material_number = ""
                band_width_type_name = ""
                material_band_base_price = ""
            else:
                material_band_material_number = bm_contract_material_band.material_number
                band_width_type_name = bm_contract_material_band.band_width_type_name
                material_band_base_price = str(bm_contract_material_band.base_price)

            # 查找授权人的信息
            bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(id=bm_contract_material_account_id).first()
            if not bm_contract_authorizer:
                account = ""
            else:
                account = bm_contract_authorizer.account
            # 查找下单者的一些信息
            bm_account_info = auth_models.BmUserInfo.objects.filter(id=max_band_dict.get("account_id")).first()
            if not bm_account_info:
                identity_name = ""
                user_account = ""
            else:
                identity_name = bm_account_info.identity_name
                user_account = bm_account_info.account
            # 查找订单信息
            bm_contract_order = service_model.BmServiceOrder.objects.filter(id=max_band_dict.get("order_id")).first()
            if not bm_contract_order:
                region = ""
            else:
                region = bm_contract_order.region

            # 查找项目信息
            bm_contract_project = service_model.BmProject.objects.filter(id=max_band_dict.get("project_id")).first()
            project_name = ""
            if bm_contract_project:
                project_name = bm_contract_project.project_name

            material_share_band_dict = {
                "用户ID": max_band_dict.get("account_id"),
                "用户名称": identity_name,
                "用户邮箱": user_account,
                "合同编号": max_band_dict.get("contract_number"),
                "查询日期": material_date,
                "带宽物料编码": material_band_material_number,
                "带宽类型": band_width_type_name,
                "带宽价格": material_band_base_price,
                "合同可用区": region,
                "销售姓名": sales,
                "公司编码": enterprise_number,
                "公司所属区": location,
                "客服姓名": customer_service_name,
                "服务到期时间": service_expired_time,
                "服务开始时间": service_start_time,
                "合同开始时间": bm_contract_material_start_date,
                "合同到期时间": bm_contract_material_expire_date,
                "客户名称": bm_contract_material_customer_name,
                "合同授权人": bm_contract_material_authorizer,
                "合同类型": bm_contract_material_contract_type,
                "合同授权人邮箱": account,
                "共享带宽id": max_band_dict.get("shared_bandwidth_id"),
                "共享带宽名称": max_band_dict.get("name"),
                "订单号": max_band_dict.get("order_id"),
                "项目ID": max_band_dict.get("project_id"),
                "项目名称": project_name,
                "最大带宽": max_band,
            }
            response_obj.content = material_share_band_dict
        except Exception as ex:
            response_obj.no = 505
            response_obj.is_ok = False
            response_obj.message = {"user_info": "shared_bandwidth_id %s 查询失败！" % shared_bandwidth_id,
                                    "admin_info": str(ex)}
        return response_obj


class BmTimeTaskProvider(object):
    def __init__(self):
        self.__db_conn = connections['default']

    def query_service_instance_in_use(self):
        model_list = ["01-客户名称", "02-客户公司", "03-账号名称", "04-账号邮箱", "05-项目", "06-合同号",
                      "07-服务器类型", "08-物料编码", "09-服务器镜像", "10-服务器名称", "11-服务UUID",
                      "12-服务器状态", "13-服务器开通时间", "14-合同截至日期"]
        sql = """ 
            SELECT 
                 bm_contract.authorizer,	bm_contract.customer_name, bm_userinfo.identity_name, bm_userinfo.account, 
                bm_project.project_name, bm_contract.contract_number, 
                    bm_service_flavor.type, bm_service_flavor.material_number, bm_service_machine.image_name,
                  bm_service_machine.service_name, bm_service_instance.uuid, bm_service_instance.`status`,
                  bm_service_instance.create_at, bm_contract.expire_date
                from bm_service_instance 
                LEFT JOIN bm_service_machine on bm_service_instance.uuid = bm_service_machine.uuid
                left join bm_service_flavor on bm_service_flavor.id = bm_service_machine.flavor_id 
                left JOIN bm_userinfo on bm_service_instance.account_id = bm_userinfo.id
                LEFT join bm_project on bm_service_instance.project_id = bm_project.id
                LEFT JOIN bm_contract on bm_service_instance.contract_number = bm_contract.contract_number 
                where bm_service_instance.`status` in ("SHUTOFF", "active") ORDER BY authorizer
        """
        with self.__db_conn.cursor() as cursor:
            cursor.execute(sql)
            result_ids = cursor.fetchall()
        dict_result = list(map(lambda x: dict(zip(model_list, x)), result_ids))
        return dict_result
