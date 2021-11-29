# -*- coding:utf-8 -*-
import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.forms.models import model_to_dict
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from account.repository import auth_models as auth_models
from baremetal_audit import audit_types
from baremetal_audit.handler import send_cloud_log_notification, send_cloud_audit_log_single_request, \
    send_cloud_audit_log_multi_request
from BareMetalControllerBackend.conf.env import env_config
from baremetal_service import order_handler
from baremetal_service.repository import serializers
from baremetal_service.repository import response_serializers
from baremetal_service.repository import service_model as service_model
from baremetal_service.repository.service_provider import ServiceFloatingProvider
from celery_tasks import tasks
from common import utils
from common.lark_common.model.common_model import ResponseObj
from common.lark_common.utils import AESCipher
from common import exceptions as exc

DEFAULT_BANDWIDTH_COUNT = 5
DEFAULT_BANDWIDTH_FLOATINGIP_COUNT = 20


class BmSharedBandwidthsViews(viewsets.ViewSet):

    def __init__(self):
        super(BmSharedBandwidthsViews, self).__init__()
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.BmSharedBandwidthFipViews = BmSharedBandwidthFipViews()

    @swagger_auto_schema(request_body=serializers.BandWidthCreateSerializer,
                         operation_description="创建共享带宽实例",
                         responses={200: response_serializers.BandWidthCreateResponsesSerializer}
                         )
    @utils.param_info
    def create(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        order_info = param_info.get("order_info")
        bandwidth_info = param_info.get("bandwidth_info")
        contract_id = param_info.get("contract_id")
        name = bandwidth_info.get("name")
        max_kbps = int(bandwidth_info.get('max_kbps', 0))
        billing_type = bandwidth_info.get("billing_type")

        region = request.session.get('region', env_config.region_name)

        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("ID 为 %s 的项目不存在！" % project_id)
                order_info["project"] = project_result

                # 名称验证
                if name is "":
                    raise Exception("实例名称为必填项！")
                bandwidth_obj_by_name = service_model.BmShareBandWidth.objects.filter(project_id=project_id,
                                                                                      is_measure_end=False,
                                                                                      name=name)
                if bandwidth_obj_by_name:
                    raise Exception("实例名称 '%s' 已存在！" % name)

                # 实例数量限制
                bandwidth_used_count = service_model.BmShareBandWidth.objects.filter(project_id=project_id,
                                                                                     is_measure_end=False).count()

                bandwidth_quota_info = service_model.ShareBandWidthQuota.objects.filter(project_id=project_id).first()
                bandwidth_quota_count = bandwidth_quota_info.share_bandwidth_count \
                    if bandwidth_quota_info else DEFAULT_BANDWIDTH_COUNT

                if bandwidth_used_count >= bandwidth_quota_count:
                    user_info = "'%s' 项目下共享带宽实例数量已达上限不可再创！" % project_result.project_name
                    return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info="quota error")

                # 创建订单
                self.logger.info("create order info %s", order_info)
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)
                result = {"order_result": order_result, "bandwidth_result": [], "contract_result": []}
                shared_bandwidth_id = service_model.UUIDTools.uuid4_hex()
                # 创建共享带宽实例
                bandwidth_dict = {
                    "order_id": order_result.id,
                    "account_id": account_id,
                    "project_id": project_id,
                    "contract_id": contract_id,
                    "contract_number": order_info.get("contract_number"),
                    "name": name,
                    "max_kbps": max_kbps,
                    "create_at": datetime.datetime.now(),
                    "is_measure_end": False,
                    "first_create_at": datetime.datetime.now(),
                    "billing_type": billing_type,
                    "shared_bandwidth_id": shared_bandwidth_id
                }
                bandwidth_result = service_model.BmShareBandWidth.objects.create(**bandwidth_dict)
                if bandwidth_result:
                    bandwidth_result.status = 'active'
                    bandwidth_result.save()
                result['bandwidth_result'] = bandwidth_result
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()

                # 查看合同详情
                contract_result = auth_models.BmContract.objects.get(id=contract_id)
                if contract_result is None:
                    raise Exception(contract_result)
                result['contract_result'] = contract_result

                async_task = tasks.add_traffic_shaper.delay(shared_bandwidth_id, max_kbps // 8)
                async_result = async_task.get(timeout=30)
                if not async_result:
                    raise exc.SharedBandWidthError(name=name)
                send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                            service_type=audit_types.SBW, resource_id=bandwidth_result.shared_bandwidth_id,
                                            resource_name=bandwidth_result.name, resource_type=audit_types.SBW,
                                            contract_number=order_info.get('contract_number'),
                                            trace_name=audit_types.CREATE, request=request.param_info,
                                            response=result)
        except Exception as ex:
            complete_exception = "共享带宽创建失败: " + str(ex)
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.SBW,
                                        resource_type=audit_types.SBW,
                                        contract_number=order_info.get('contract_number'),
                                        trace_name=audit_types.CREATE, request=request.param_info,
                                        response=str(ex), code=500)
            return response_obj.json_exception_serial(user_info=complete_exception, admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(operation_description="查看共享带宽实例列表",
                         responses={200: response_serializers.BandWidthListResponsesSerializer}
                         )
    @utils.param_info
    def list(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        project_id = request.session.get('project_id')
        result = []
        try:
            openstack_client = utils.get_openstack_client(request)
            filters = {'project_id': project_id,
                       'is_measure_end': False}
            filters.update(param_info)
            bandwidth_objects = service_model.BmShareBandWidth.objects.filter(**filters
                                                                              ).order_by('first_create_at')
            for bandwidth in bandwidth_objects:
                bandwidth_result = []
                contract_result = []
                attached_fip_result = []

                bandwidth_result.append(bandwidth.__dict__)
                if bandwidth.contract_id:
                    contract_info = service_model.BmContract.objects.get(id=bandwidth.contract_id)
                    contract_result.append(contract_info.__dict__)

                floating_ip_query = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                                     is_measure_end=False,
                                                                                     qos_policy_id=bandwidth.shared_bandwidth_id).all()
                openstack_fip_objects = openstack_client.network.ips(project_id=project_id)
                openstack_fip_ids = [fip.id for fip in openstack_fip_objects]
                for floating in floating_ip_query:
                    if floating.floating_ip_id in openstack_fip_ids:
                        attached_fip_result.append(model_to_dict(floating))

                result.append({"bandwidth_result": bandwidth_result, "contract_result": contract_result, "attached_fip_result": attached_fip_result})
        except Exception as ex:
            complete_exception = "查共享带宽列表失败: " + str(ex)
            return response_obj.json_exception_serial(user_info=complete_exception, admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.BandWidthUpdateSerializer,
                         operation_description="编辑共享带宽实例",
                         responses={200: response_serializers.BandWidthUpdateResponsesSerializer}
                         )
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.SBW, resource_type=audit_types.SBW,
                                         trace_name=audit_types.UPDATE, resource_id_key='shared_bandwidth_id')
    def update(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        order_info = param_info.get("order_info")
        shared_bandwidth_id = param_info.get('bandwidth_id')
        name = param_info.get('name')
        max_kbps = int(param_info.get('max_kbps', 0))
        result = None

        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("ID 为 %s 的项目不存在！" % project_id)

                self.logger.info("Update bandwidth %s", param_info)
                bandwidth_object = service_model.BmShareBandWidth.objects.get(project_id=project_id,
                                                                              shared_bandwidth_id=shared_bandwidth_id,
                                                                              is_measure_end=False)
                if not bandwidth_object:
                    raise Exception("ID 为 %s 的共享带宽实例不存在！" % shared_bandwidth_id)

                old_name = str(bandwidth_object.name)
                old_max_kbps = bandwidth_object.max_kbps
                if str(name) != old_name:
                    self.logger.info("Update bandwidth name %s", name)
                    bandwidth_object.update_at = datetime.datetime.now()
                    bandwidth_object.name = name
                    bandwidth_object.save()
                    if self.BmSharedBandwidthFipViews.list_bandwidth_floatingips(request, bandwidth_object.shared_bandwidth_id):
                        floating_ip_objs = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                                            is_measure_end=False,
                                                                                            shared_qos_policy_type=True,
                                                                                            qos_policy_id=bandwidth_object.shared_bandwidth_id).all()
                        for fip_object in floating_ip_objs:
                            fip_object.qos_policy_name = name
                            fip_object.save()
                    result = bandwidth_object

                if max_kbps != old_max_kbps:
                    bandwidth_object.is_measure_end = True
                    bandwidth_object.update_at = datetime.datetime.now()
                    bandwidth_object.save()
                    origin_order_id = bandwidth_object.order_id
                    alter_order_obj = order_handler.create_new_order_for_alter(origin_order_id=origin_order_id,
                                                                               alter_order_info=order_info,
                                                                               account_id=account_id,
                                                                               service_count=1,
                                                                               product_type='共享带宽')
                    if not alter_order_obj.is_ok:
                        raise Exception(alter_order_obj.message)
                    order_result = alter_order_obj.content
                    self.logger.info("extend bandwidth")
                    bandwidth_dict = model_to_dict(bandwidth_object)
                    bandwidth_dict['max_kbps'] = max_kbps
                    bandwidth_dict['is_measure_end'] = False
                    bandwidth_dict['shared_bandwidth_id'] = shared_bandwidth_id
                    bandwidth_dict['create_at'] = datetime.datetime.now()
                    bandwidth_dict['order_id'] = order_result.id
                    bandwidth_dict.pop('update_at')
                    bandwidth_dict.pop('id')
                    bandwidth_dict['account_id'] = account_id
                    new_bandwidth_object = service_model.BmShareBandWidth.objects.create(**bandwidth_dict)
                    self.logger.info("extend bandwidth create result %s" % new_bandwidth_object)

                    # 订单交付
                    order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                    order_result.create_at = datetime.datetime.now()
                    order_result.save()
                    result = new_bandwidth_object

                    async_task = tasks.udate_traffic_shaper.delay(shared_bandwidth_id, max_kbps // 8)

                    async_result = async_task.get(timeout=60)
                    if not async_result:
                        raise exc.SharedBandWidthError(name=shared_bandwidth_id)

        except ObjectDoesNotExist as ex:
            return response_obj.json_exception_serial(user_info="该共享带宽不存在", admin_info=str(ex), no=500)
        except Exception as ex:
            complete_exception = "更新共享带宽失败: " + str(ex)
            return response_obj.json_exception_serial(user_info=complete_exception, admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.BandWidthDeleteSerializer,
                         operation_description="（批量，单个）删除共享带宽实例",
                         responses={200: response_serializers.BandWidthDeleteResponsesSerializer}
                         )
    @utils.param_info
    @send_cloud_audit_log_multi_request(service_type=audit_types.SBW, resource_type=audit_types.SBW,
                                        trace_name=audit_types.DELETE, resource_id_key='shared_bandwidth_id')
    def destroy(self, request):
        response_obj = ResponseObj()
        shared_bandwidth_ids = request.param_info.get("bandwidth_ids")
        result = []
        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("ID 为 %s 的项目不存在！" % project_id)

                self.logger.info("Delete bandwidth %s", request.param_info)
                if shared_bandwidth_ids is None:
                    raise Exception("当前无可删共享带宽实例！")

                for bid in shared_bandwidth_ids:
                    floating_ip_objs = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                                         is_measure_end=False,
                                                                                         qos_policy_id=bid).all()
                    if floating_ip_objs:
                        raise Exception("当前共享带宽实例正在被使用无法删！")
                    bandwidth = service_model.BmShareBandWidth.objects.get(project_id=project_id,
                                                                           shared_bandwidth_id=bid,
                                                                           is_measure_end=False)
                    if not bandwidth:
                        raise Exception("Fail to find floating ip info by id %s " % bandwidth)
                    bandwidth.update_at = datetime.datetime.now()
                    bandwidth.is_measure_end = True
                    bandwidth.deleted_at = datetime.datetime.now()
                    bandwidth.status = 'deleted'
                    bandwidth.save()
                    result.append(bandwidth.__dict__)
                async_task = tasks.delete_traffic_shaper.delay(shared_bandwidth_ids)
                async_result = async_task.get(timeout=60)
                if not async_result:
                    raise exc.SharedBandWidthError(name=shared_bandwidth_ids)
        except ObjectDoesNotExist as ex:
            return response_obj.json_exception_serial(user_info="该共享带宽不存在", admin_info=str(ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除共享带宽失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)


class BmSharedBandwidthViews(viewsets.ViewSet):
    def __init__(self):
        super(BmSharedBandwidthViews, self).__init__()
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(request_body=serializers.BandWidthDetailsSerializer,
                         operation_description="搜索共享带宽实例查看详情",
                         responses={200: response_serializers.ShareBandwidthResponseSerializer}
                         )
    @utils.param_info
    def search(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        fields_key = param_info.get("fields_key")
        fields_value = param_info.get("fields_value")
        project_id = request.session.get('project_id')
        result = []
        try:
            bandwidth_obj = service_model.BmShareBandWidth.objects.filter(project_id=project_id,
                                                                          is_measure_end=False).order_by(
                'first_create_at')
            if fields_key == 'name':
                bandwidth_obj = service_model.BmShareBandWidth.objects.filter(name=fields_value,
                                                                              is_measure_end=False).order_by(
                    'first_create_at')
            if not bandwidth_obj:
                raise Exception("Fail to find floating ip info by id %s " % bandwidth_obj)
            for bandwidth in bandwidth_obj:
                result.append(bandwidth.__dict__)
        except Exception as ex:
            complete_exception = "按条件搜共享带宽实例失败: " + str(ex)
            return response_obj.json_exception_serial(user_info=complete_exception, admin_info=str(ex), no=500)
        return response_obj.json_serial(result)


class BmSharedBandwidthFipViews(viewsets.ViewSet):

    def attach_fip_to_shared_bandwidth(self, project_id, openstack_client, shared_bandwidth_id, shared_bandwidth_name,
                                       floating_ip_id):

        try:
            with transaction.atomic():
                fip_object = service_model.BmServiceFloatingIp.objects.filter(is_measure_end=False,
                                                                              project_id=project_id,
                                                                              floating_ip_id=floating_ip_id).first()

                if not fip_object.shared_qos_policy_type:
                    openstack_client.network.update_ip(floating_ip_id, **{"qos_policy_id": None})

                fip_object.shared_qos_policy_type = True
                fip_object.qos_policy_name = shared_bandwidth_name
                fip_object.qos_policy_id = shared_bandwidth_id
                fip_object.save()

                mappings = service_model.BmFloatingipfirewallMapping.objects.filter(
                    floating_ip_id=floating_ip_id).first()
                firewall_rules = []
                firewall = service_model.Firewalls.objects.get(id=mappings.firewall_id)
                firewall_rule_objects = firewall.firewallrule_set.all()
                for object in firewall_rule_objects:
                    firewall_rules.append(object.to_dict())
                tasks.update_fip_firewall.delay(fip_object.floating_ip, firewall.to_dict(),
                                                firewall.to_dict(), firewall_rules,
                                                traffic_shaper=shared_bandwidth_id)
        except Exception as ex:
            return False, str(ex)
        return True, None, fip_object

    @swagger_auto_schema(
        request_body=serializers.SharedBWFipAttachSerializer,
        operation_description="共享带宽实例添加弹性公网IP",
        responses={200: response_serializers.BandWidthAttachFipResponsesSerializer}
    )
    @utils.param_info
    def attach(self, request, bandwidth_id):
        response_obj = ResponseObj()
        param_info = request.param_info
        floating_ip_ids = param_info.get('floating_ip_ids')
        shared_bandwidth_id = bandwidth_id
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
        region = request.session.get('region', env_config.region_name)
        success_fip = []
        error_fip = []
        try:

            project_result = auth_models.BmProject.objects.filter(id=project_id).first()
            if not project_result:
                raise Exception("ID 为 %s 的项目不存在！" % project_id)

            fip_used_count = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                              is_measure_end=False,
                                                                              qos_policy_id=shared_bandwidth_id).count()

            bandwidth_fip_quota_info = service_model.ShareBandWidthQuota.objects.filter(project_id=project_id).first()
            bandwidth_fip_quota_count = bandwidth_fip_quota_info.floating_ip_count \
                if bandwidth_fip_quota_info else DEFAULT_BANDWIDTH_FLOATINGIP_COUNT

            if fip_used_count + len(floating_ip_ids) > bandwidth_fip_quota_count:
                user_info = "'%s' 项目下当前共享带宽实例可绑定ip已达上限！" % project_result.project_name

                return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info="quota error")

            openstack_client = utils.get_openstack_client(request)

            bandwidth_object = service_model.BmShareBandWidth.objects.filter(
                project_id=project_id,
                is_measure_end=False,
                shared_bandwidth_id=shared_bandwidth_id).first()
            for fip_id in floating_ip_ids:
                fip_obj = service_model.BmServiceFloatingIp.objects.get(project_id=project_id,
                                                                        is_measure_end=False,
                                                                        floating_ip_id=fip_id)
                if fip_obj is None:
                    user_info = "弹性公网IP %s 不存在！" % fip_id
                    return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info="None floating ip!")
                success, error_info, fip_object = self.attach_fip_to_shared_bandwidth(project_id, openstack_client,
                                                                          shared_bandwidth_id,
                                                                          bandwidth_object.name, fip_id)
                fip_object.qos_max_kbps = ServiceFloatingProvider.get_qos_max_kbps(fip_object)
                if success:
                    success_fip.append(fip_object.__dict__)
                else:
                    fip_with_error_info = {"floating_ip_id": fip_obj.__dict__, "error_info": error_info}
                    error_fip.append(fip_with_error_info)
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.SBW, resource_id=bandwidth_object.shared_bandwidth_id,
                                        resource_name=bandwidth_object.name, resource_type=audit_types.SBW,
                                        contract_number=bandwidth_object.contract_number,
                                        trace_name=audit_types.SBW_ADD_EIP, request=request.param_info,
                                        response={"success": success_fip, "error": error_fip})
            return response_obj.json_serial({"success": success_fip, "error": error_fip})
        except ObjectDoesNotExist as ex:
            return response_obj.json_exception_serial(user_info="该对象不存在！", admin_info=str(ex), no=500)
        except Exception as ex:
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.SBW,  resource_type=audit_types.SBW,
                                        trace_name=audit_types.SBW_ADD_EIP, request=request.param_info,
                                        response=str(ex), code=500)
            return response_obj.json_exception_serial(no=400, user_info="添加弹性公网ip失败", admin_info=str(ex))

    def detach_fip_from_shared_bandwidth(self, project_id, openstack_client, shared_bandwidth_id, qos_policy_id,
                                         qos_policy_name, floating_ip_id):
        try:
            with transaction.atomic():
                fip_object = service_model.BmServiceFloatingIp.objects.filter(is_measure_end=False,
                                                                              project_id=project_id,
                                                                              floating_ip_id=floating_ip_id).first()
                if fip_object.shared_qos_policy_type != True or fip_object.qos_policy_id != shared_bandwidth_id:
                    return False, "Not found floating ip %s in this bandwidth" % shared_bandwidth_id
                fip_object.shared_qos_policy_type = False
                fip_object.qos_policy_name = qos_policy_name
                fip_object.qos_policy_id = qos_policy_id
                fip_object.save()

                openstack_client.network.update_ip(floating_ip_id, **{"qos_policy_id": qos_policy_id})

                mappings = service_model.BmFloatingipfirewallMapping.objects.filter(
                    floating_ip_id=floating_ip_id).first()
                firewall_rules = []
                firewall = service_model.Firewalls.objects.get(id=mappings.firewall_id)
                firewall_rule_objects = firewall.firewallrule_set.all()
                for object in firewall_rule_objects:
                    firewall_rules.append(object.to_dict())

                tasks.update_fip_firewall.delay(fip_object.floating_ip, firewall.to_dict(), firewall.to_dict(),
                                          firewall_rules, traffic_shaper=None)

        except Exception as ex:
            return False, str(ex)
        return True, None, fip_object

    @swagger_auto_schema(
        request_body=serializers.SharedBWFipDetachSerializer,
        operation_description="共享带宽实例移除弹性公网IP",
        responses={200: response_serializers.BandWidthAttachFipResponsesSerializer}
    )
    @utils.param_info
    def detach(self, request, bandwidth_id):
        response_obj = ResponseObj()
        param_info = request.param_info
        floating_ip_ids = param_info.get('floating_ip_ids')
        shared_bandwidth_id = bandwidth_id
        qos_policy_name = param_info.get('qos_policy_name')
        order_info_from_user = param_info.get('order_info')
        service_count_from_user = param_info.get('service_count')
        region = request.session.get("region", env_config.region_name)
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        account_id = request.session.get('account_id', request.COOKIES.get("account_id"))

        success_fip = []
        error_fip = []
        try:
            openstack_client = utils.get_openstack_client(request)
            qos = service_model.BmServiceQosPolicy.objects.filter(qos_policy_name=qos_policy_name).first()
            if not qos:
                return response_obj.json_exception_serial(no=404, user_info="该带宽不存在", admin_info="no qos policy")

            bandwidth_object = service_model.BmShareBandWidth.objects.filter(project_id=project_id,
                                                                             is_measure_end=False,
                                                                             shared_bandwidth_id=shared_bandwidth_id).first()
            if not bandwidth_object:
                return response_obj.json_exception_serial(no=404, user_info="该共享带宽实例不存在", admin_info="no shared bandwidth")
            for fip_id in floating_ip_ids:
                complete_success_obj = []
                fip_obj = service_model.BmServiceFloatingIp.objects.get(project_id=project_id,
                                                                        is_measure_end=False,
                                                                        floating_ip_id=fip_id)
                if fip_obj is None:
                    user_info = "弹性公网IP %s 不存在！" % fip_id
                    return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info="None floating ip!")
                success, error_info, fip_object = self.detach_fip_from_shared_bandwidth(project_id, openstack_client,
                                                                                        shared_bandwidth_id,
                                                                                        qos.id, qos_policy_name,
                                                                                        fip_id)
                fip_object.qos_max_kbps = ServiceFloatingProvider.get_qos_max_kbps(fip_object)
                if success:
                    complete_success_obj.append(fip_object.__dict__)
                    # 添加合同信息
                    contract_obj = service_model.BmContract.objects.filter(contract_number=fip_object.contract_number,
                                                                           status="active")
                    if contract_obj:
                        contract_info = contract_obj.first()
                        complete_success_obj.append(contract_info.__dict__)
                    else:
                        contract_info = {}
                        complete_success_obj.append({"contract_info": contract_info})
                    success_fip.append(complete_success_obj)

                    # 新订单交付
                    origin_order_id = bandwidth_object.order_id
                    origin_order_obj = service_model.BmServiceOrder.objects.filter(id=origin_order_id).first()
                    if not origin_order_obj:
                        raise Exception("fail to find origin order info by order id %s" % origin_order_id)

                    new_order_info = origin_order_obj.__dict__
                    pop_list = ["_state", "id", "deleted", "update_at", "create_at"]
                    for pop_param in pop_list:
                        new_order_info.pop(pop_param)
                    new_order_info["delivery_status"] = service_model.ORDER_STATUS_DELIVERING
                    new_order_info["service_count"] = 1
                    new_order_info["order_type"] = order_info_from_user["order_type"]
                    new_order_info["order_price"] = order_info_from_user["order_price"]
                    new_order_info["product_type"] = "弹性公网IP"
                    new_order_info["product_info"] = order_info_from_user["product_info"]
                    new_order_info["account_id"] = account_id
                    order_result = service_model.BmServiceOrder.objects.create(**new_order_info)
                    if not order_result:
                        raise Exception(order_result)
                    order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                    order_result.create_at = datetime.datetime.now()
                    order_result.save()

                else:
                    fip_with_error_info = {"floating_ip_id": fip_obj.__dict__, "error_info": error_info}
                    error_fip.append(fip_with_error_info)
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.SBW, resource_id=bandwidth_object.shared_bandwidth_id,
                                        resource_name=bandwidth_object.name, resource_type=audit_types.SBW,
                                        contract_number=bandwidth_object.contract_number,
                                        trace_name=audit_types.SBW_REMOVE_EIP, request=request.param_info,
                                        response={"success": success_fip, "error": error_fip})
        except Exception as ex:
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.SBW, resource_type=audit_types.SBW,
                                        trace_name=audit_types.SBW_REMOVE_EIP, request=request.param_info,
                                        response=str(ex), code=500)
            return response_obj.json_exception_serial(no=400, user_info="移除弹性公网ip失败", admin_info=str(ex))
        return response_obj.json_serial({"success": success_fip, "error": error_fip})

    @swagger_auto_schema(operation_description="获取某个共享带宽下的弹性公网IP",
                         responses={200: response_serializers.SbwAttachedFipInfoResponsesSerializer})
    @utils.param_info
    def list_bandwidth_floatingips(self, request, bandwidth_id):
        response_obj = ResponseObj()
        shared_bandwidth_id = bandwidth_id
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            res = []
            floating_ip_query = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                                 is_measure_end=False,
                                                                                 shared_qos_policy_type=True,
                                                                                 qos_policy_id=shared_bandwidth_id).all()
            for floating in floating_ip_query:
                complete_success_obj = []
                floating_info = model_to_dict(floating)
                floating_info['qos_max_kbps'] = ServiceFloatingProvider.get_qos_max_kbps(floating)
                complete_success_obj.append(floating_info)
                # 添加合同信息
                contract_obj = service_model.BmContract.objects.filter(contract_number=floating.contract_number,
                                                                       status="active")
                if contract_obj:
                    contract_info = contract_obj.first()
                    complete_success_obj.append(contract_info.__dict__)
                else:
                    contract_info = {}
                    complete_success_obj.append({"contract_info": contract_info})
                res.append(complete_success_obj)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取共享带宽下弹性公网ip失败",
                                                      admin_info=str(ex),
                                                      no=500)

        return response_obj.json_serial(res)

    @swagger_auto_schema(operation_description="获取某个弹性公网IP下的共享带宽实例",
                         responses={200: response_serializers.ShareBandwidthResponseSerializer})
    @utils.param_info
    def list_floatingip_bandwidths(self, request, floating_ip_id):
        response_obj = ResponseObj()
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            project_result = auth_models.BmProject.objects.filter(id=project_id).first()
            if not project_result:
                raise Exception("Project ID 为 %s 的项目不存在！" % project_id)

            fip_obj = service_model.BmServiceFloatingIp.objects.get(project_id=project_id,
                                                                    is_measure_end=False,
                                                                    floating_ip_id=floating_ip_id)
            if fip_obj is None:
                user_info = "弹性公网IP %s 不存在！" % floating_ip_id
                return response_obj.json_exception_serial(no=500, user_info=user_info, admin_info="None floating ip!")

            res = []
            if fip_obj.shared_qos_policy_type is True:
                shared_bandwidth_id = fip_obj.qos_policy_id
                shared_bandwidth_name = fip_obj.qos_policy_name
                bandwidth_objs = service_model.BmShareBandWidth.objects.filter(shared_bandwidth_id=shared_bandwidth_id,
                                                                               name=shared_bandwidth_name,
                                                                               is_measure_end=False).all()
                for bandwidth_obj in bandwidth_objs:
                    res.append(model_to_dict(bandwidth_obj))
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取某个弹性公网IP下的共享带宽实例失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(res)