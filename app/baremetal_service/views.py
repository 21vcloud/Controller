# -*- coding:utf-8 -*-
import copy
import datetime, time
import logging
import os
import re

import jsonpickle, json
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from rest_framework import status
from django.http import StreamingHttpResponse
from django.utils.encoding import escape_uri_path
from django.utils.http import urlunquote
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from baremetal_service import handler

from BareMetalControllerBackend.conf.env import env_config
from baremetal_audit.handler import send_cloud_log_notification, send_cloud_audit_log_multi_request, \
    send_cloud_audit_log_single_request
from baremetal_audit import audit_types
from account.auth import utils as auth_utils
from account.repository import auth_models as auth_models
from baremetal_openstack.repository.nova_provider import OpenstackClientProvider
from baremetal_service import swift_handler
from baremetal_service.object_forms import UploadObjectForm
from baremetal_service import order_handler
from baremetal_service.repository import serializers
from baremetal_service.repository import response_serializers
from baremetal_service.repository import service_model as service_model
from baremetal_service.repository.service_provider import ServiceProvider, BmMaterialProvider, \
    ServiceFloatingProvider, ServiceVolumeProvider, BmTimeTaskProvider, ServiceCmdbProvider
from celery_tasks.tasks import job_executor, update_fip_firewall, associate_firewall, disassociate_firewall
from common import exceptions as exc
from common import utils
from common.lark_common.model.common_model import ResponseObj
from common.lark_common.utils import AESCipher
from common.openstack.baremetal_volume import baremetal_attach_volume, volume_extend, volume_backup_restore
from openstack import exceptions as openstack_exception
from common.access_control.base import check_element_permission
from baremetal_service.bw_views import DEFAULT_BANDWIDTH_FLOATINGIP_COUNT

from BareMetalControllerBackend.conf.env import EnvConfig

config = EnvConfig()
LOG = logging.getLogger(__name__)


class BaremetalServiceInstanceViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.openstack_provider = OpenstackClientProvider()
        self.floatingip_provider = ServiceFloatingProvider()
        self.volume_provider = ServiceVolumeProvider()
        self.cmdb_provider = ServiceCmdbProvider()

    def _check_instance_quota(self, request):
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        nova_limits = openstack_client.compute.get_limits()
        available_count = int(nova_limits.absolute.instances) - int(nova_limits.absolute.instances_used)
        return available_count

    def check_instance_resource_quota(self, request):
        check_result = True
        order_info = request.param_info.get("order_info")
        post_data = request.param_info.get("service_info")
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))

        service_count = order_info.get("service_count")
        available_count = self._check_instance_quota(request)
        if service_count > available_count:
            user_info = "配额不足，您的剩余可用个数 %s" % available_count
            check_result = False
            return check_result, user_info

        floating_ip_info = post_data.get('floating_ip_info', {})
        if floating_ip_info:
            region = order_info.get("region", request.session.get("region"))
            external_line_type = floating_ip_info.get("external_line_type")
            shared_qos_policy_type = floating_ip_info.get("shared_qos_policy_type", False)
            qos_policy_id = floating_ip_info.get("qos_policy_id", )
            external_region_network = env_config.external_networks.get(region)
            if not external_region_network:
                self.logger.error("Fail to find external network info in region %s" % region)
                raise Exception("Fail to find external network info in region %s" % region)
            external_network_list = external_region_network.get(external_line_type)
            if not external_network_list:
                self.logger.error("Fail to find external network info in network type  %s" % external_line_type)
                raise Exception("Fail to find external network info in network type  %s" % external_line_type)
            external_network = external_network_list[0]
            external_name = external_network.get("network_name")
            external_name_id = external_network.get("network_id")
            # 检查共享带宽是否存在
            if shared_qos_policy_type:
                bandwidth_shared = service_model.BmShareBandWidth.objects.filter(shared_bandwidth_id=qos_policy_id,
                                                                                 is_measure_end=False).first()
                if not bandwidth_shared:
                    user_info = "该共享带宽不存在"
                    check_result = False
                    return check_result, user_info
                # 检查共享带宽下ip个数配额

                fip_used_count = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                                  is_measure_end=False,
                                                                                  qos_policy_id=qos_policy_id).count()
                bandwidth_fip_quota_info = service_model.ShareBandWidthQuota.objects.filter(
                    project_id=project_id).first()
                bandwidth_fip_quota_count = bandwidth_fip_quota_info.floating_ip_count \
                    if bandwidth_fip_quota_info else DEFAULT_BANDWIDTH_FLOATINGIP_COUNT

                if fip_used_count + service_count > bandwidth_fip_quota_count:
                    user_info = "当前共享带宽实例可绑定ip已达上限！"
                    check_result = False
                    return check_result, user_info

            if not self.floatingip_provider.check_fip_pools(service_count,
                                                            external_name_id):
                user_info = "弹性公网ip配额不足"
                check_result = False
                return check_result, user_info

        disk_info = post_data.get('disk_info', {})
        if disk_info:
            size = 0
            for disk in disk_info:
                size += int(disk['size']) * int(disk['count'])

            pool_size = self.volume_provider.get_pool_size()
            if size * service_count > pool_size:
                user_info = '云硬盘配额不足'
                check_result = False
                return check_result, user_info

        fixed_net = post_data.get('network_id')
        if not self.floatingip_provider.check_fip_pools(service_count, fixed_net):
            user_info = "选择的网络ip资源不足，请切换网络"
            check_result = False
            return check_result, user_info
        return check_result, None

    @swagger_auto_schema(operation_description="获取裸金属带监控的列表",
                         query_serializer=serializers.MonitoringInstanceSerializer)
    @utils.param_info
    def monitoring_instance_list(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        project_id = param_info.get("project_id")
        region = param_info.get("region")
        try:

            monitoring_instance_list = service_model.BmServiceInstance.objects.filter(monitoring=True, deleted=False,
                                                                                      project_id=project_id,
                                                                                      region=region)
            monitoring_machine_list = [u.__dict__ for u in monitoring_instance_list]

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取裸金属带监控的列表失败！",
                                                      admin_info=str(ex), no=300)
        return response_obj.json_serial(monitoring_machine_list)

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="购买裸金属服务器",
                         request_body=serializers.ServiceCreateListSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def view_create_baremetal_service(self, request):
        response_obj = ResponseObj()

        check_result, user_info = self.check_instance_resource_quota(request)
        if not check_result:
            return response_obj.json_exception_serial(user_info=user_info, admin_info="Quota error",
                                                      no=300)
        service_name_base = None

        try:
            with transaction.atomic():
                order_info = request.param_info.get("order_info")
                post_data = request.param_info.get("service_info")
                service_count = order_info.get("service_count")
                flavor_id = post_data.get("flavor_id")
                project = request.session.get("project_id")
                account = request.session.get('account_id')
                region = order_info.get('region')

                if service_count <= 0:
                    raise Exception("服务器个数不能小于0")

                image_info = service_model.BmServiceFlavor.objects.get(id=flavor_id)
                if image_info.count < service_count:
                    raise Exception("服务器个数不足！联系管理员")

                # 服务器数量更新
                image_info.count -= service_count
                image_info.save()

                # 创建 表单
                order_info["create_at"] = datetime.datetime.now()

                # TODO 添加外键 aaccount id ， contrack number
                project_result = auth_models.BmProject.objects.filter(id=project).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project)
                order_info["project"] = project_result

                # 创建order
                order_info["delivery_status"] = "delivering"
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)

                # 创建各个服务器数据
                post_data["order"] = order_result
                post_data["create_at"] = datetime.datetime.now()
                machine_obj_list = []
                service_name_base = copy.deepcopy(post_data["service_name"])
                if service_count == 1:
                    machine_obj_list.append(service_model.BmServiceMachine(**post_data))
                else:

                    for count in range(1, service_count + 1):
                        post_data["service_name"] = service_name_base + "_%s" % count
                        machine_obj_list.append(service_model.BmServiceMachine(**post_data))

                service_request = service_model.BmServiceMachine.objects.bulk_create(machine_obj_list)
                if not service_request:
                    raise Exception(service_request)

                response_obj.content = order_result
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "订单提交失败", "admin_info": str(ex)}
            response_obj.no = 500
            json_data = jsonpickle.dumps(response_obj, unpicklable=False)
            # 发送日志
            send_cloud_log_notification(region=region, project_id=project, user_id=account,
                                        service_type=audit_types.ECBM, resource_name=service_name_base,
                                        resource_type=audit_types.ECBM,
                                        contract_number=order_info.get('contract_number', None),
                                        trace_name=audit_types.CREATE, trace_type=audit_types.CONSOLEACTION,
                                        request=request.param_info, response=response_obj.message, code=500)
            return HttpResponse(json_data, content_type="application/json")

        try:
            # 任务下发
            for num, service_info in enumerate(service_request):
                order_info = copy.deepcopy(service_info.order.__dict__)
                service_info_json = copy.deepcopy(service_info.__dict__)
                # if num == 0:
                order_info.pop("_state")
                service_info_json.pop("_state")
                service_info_json["order_info"] = order_info
                service_info_json["session_info"] = request.session._session
                service_info_json["result"] = {}
                self.logger.info("Service Request Info: %s!" % service_info_json)

                # 保存job model 信息
                service_info.job_model = service_info_json
                service_info.save()

                # 任务下发
                job = job_executor.delay(service_info_json)

                # 定义发送日志变量
                code = 200
                log_res = None

            response_obj.content = "success submit!"
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "订单提交失败", "admin_info": str(ex)}
            response_obj.no = 500

            # 发送日志
            log_res = response_obj.message
            code = 500
        # 发送日志

        send_cloud_log_notification(region=region, project_id=project, user_id=account,
                                    service_type=audit_types.ECBM, resource_name=service_name_base,
                                    resource_type=audit_types.ECBM,
                                    contract_number=order_info.get('contract_number', None),
                                    trace_name=audit_types.CREATE, trace_type=audit_types.CONSOLEACTION,
                                    request=request.param_info, response=log_res, code=code)

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取某用户所有的订单信息",
                         responses={200: response_serializers.OrderByAccountResponsesSerializer},
                         query_serializer=serializers.ServiceOrderQuerybyAccountSerializer)
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def view_baremetal_service_order_query_by_account(self, request):
        response_obj = ResponseObj()
        try:
            account_id = request.param_info.get("account_id")
            request = service_model.BmServiceOrder.objects.filter(account_id=account_id).order_by("-create_at")
            result_json = []
            for order_info in request:
                order_dict = order_info.__dict__
                if hasattr(order_info, "project") and order_info.project:
                    order_dict["project_name"] = order_info.project.project_name
                else:
                    order_dict["project_name"] = "-"
                order_dict.pop("_state")
                if order_dict["product_type"] in [env_config.floating_ip_type, env_config.band_width_type]:
                    order_dict["order_price"] = "按实际使用量计费"
                order_dict["order_type"] = service_model.ORDER_TYPE_DICT.get(order_dict["order_type"])
                result_json.append(order_dict)
            response_obj.content = result_json
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "订单查询失败", "admin_info": ex}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(manual_parameters=serializers.TokenParameter,
                         operation_description="获取所有的订单信息",
                         responses={200: response_serializers.AllOrderResponsesSerializer}
                         )
    @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def view_baremetal_service_order_all(self, request):
        response_obj = ResponseObj()
        try:
            request = service_model.BmServiceOrder.objects.all().order_by("-create_at")

            result_json = []
            for order_info in request:
                order_dict = order_info.__dict__
                if hasattr(order_info, "project") and order_info.project:
                    order_dict["project_name"] = order_info.project.project_name
                else:
                    order_dict["project_name"] = "-"
                order_dict.pop("_state")
                if order_dict["product_type"] in [env_config.floating_ip_type, env_config.band_width_type]:
                    order_dict["order_price"] = "按实际使用量计费"
                order_dict["order_type"] = service_model.ORDER_TYPE_DICT.get(order_dict["order_type"])
                result_json.append(order_dict)
            response_obj.content = result_json
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "订单查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.ServiceInstanceSerializer,
                         operation_description="创建实例",
                         )
    @auth_utils.param_info_decrypt
    @send_cloud_audit_log_single_request(service_type=audit_types.ECBM, resource_type=audit_types.ECBM,
                                         trace_name=audit_types.CREATE, trace_type=audit_types.SYSTEMACTION,
                                         resource_id_key='uuid', resource_name_key='name')
    def view_baremetal_service_instance_create(self, request):
        response_obj = ResponseObj()
        try:
            param_info = request.param_info
            param_info["create_at"] = datetime.datetime.now()
            instance_result = service_model.BmServiceInstance.objects.create(**param_info)
            response_obj.content = instance_result
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "实例提交失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.ServiceInstanceFeedbackSerializer,
                         operation_description="实例更新",
                         responses={200: response_serializers.InstanceFeedBackResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def view_baremetal_service_instance_feedback(self, request):
        response_obj = ResponseObj()
        try:
            param_info = request.param_info
            uuid = param_info.pop("uuid")
            param_info["update_at"] = datetime.datetime.now()
            instance_obj = service_model.BmServiceInstance.objects.filter(uuid=uuid, deleted=False)
            instance_obj.update(**param_info)
            response_obj.content = request.param_info

            # 回填成功，同步CMDB数据
            zone = instance_obj.first().region
            project_id = instance_obj.first().project_id
            monitoring=instance_obj.first().monitoring

            cmdb_result = self.cmdb_provider.cmdb_data_sys_post(instance_uuid=uuid, zone=zone, project_id=project_id)
            self.logger.info("The instance create cmdb sys Result : %s " % cmdb_result)
            if monitoring == "True":
                cmdb_tag_result = self.cmdb_provider.cmdb_data_tag_create(instance_uuid=uuid)
                self.logger.info("The instance zabbix tag cmdb sys Result : %s " % cmdb_tag_result)

        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "实例信息更新失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.ServiceMachineFeedbackSerializer,
                         operation_description="更新订单服务器信息",
                         responses={200: response_serializers.MachineInfoFeedbackResponsesSerializer})
    @auth_utils.param_info_decrypt
    def service_machine_info_feedback(self, request):
        response_obj = ResponseObj()
        try:
            machine_id = request.param_info.get("machine_id")
            uuid = request.param_info.get("uuid")
            job_model = request.param_info.get("job_model", {})

            # uuid 回填 machine
            machine_obj = service_model.BmServiceMachine.objects.get(id=machine_id)
            machine_obj.uuid = uuid
            if job_model:
                machine_obj.job_model = job_model
            machine_obj.update_at = datetime.datetime.now()
            machine_obj.save()

            response_obj.content = machine_obj.__dict__
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "订单服务器信息更新失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.ServiceOrderDeliveryUpdateSerializer,
                         operation_description="更新订单交付信息",
                         responses={200: response_serializers.OrderDeliveryUpdateResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def service_order_delivery_update(self, request):
        response_obj = ResponseObj()
        try:
            order_id = request.param_info.get("order_id")
            delivery_status = request.param_info.get("delivery_status")
            if delivery_status == auth_models.ORDER_REJECTED:
                order_obj = service_model.BmServiceOrder.objects.get(id=order_id)
                order_obj.delivery_status = delivery_status
                order_obj.update_at = datetime.datetime.now()
                order_obj.save()
                response_obj.content = order_obj.__dict__
                json_data = jsonpickle.dumps(response_obj, unpicklable=False)
                return HttpResponse(json_data, content_type="application/json")

            # 判断 order 对应服务器是否存在
            machine_result = service_model.BmServiceMachine.objects.filter(order_id=order_id)
            if not machine_result:
                response_obj.message = "该订单 %s 无对应服务器交付信息" % order_id

            # 判断是否已交付
            machine_result = machine_result.filter(uuid__in=["", None])
            if machine_result:
                machine_result = [u.__dict__ for u in machine_result]
                response_obj.message = "还有 %s 台，未交付完成" % len(machine_result)
                response_obj.no = 300
            else:
                order_obj = service_model.BmServiceOrder.objects.get(id=order_id)
                order_obj.delivery_status = delivery_status
                order_obj.update_at = datetime.datetime.now()
                order_obj.save()
                response_obj.content = order_obj.__dict__
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "订单信息更新成功失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ServiceMachineIdSerializer,
                         operation_description="获取machine信息",
                         responses={200: response_serializers.MachineGetResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def view_baremetal_service_machine_get(self, request):
        response_obj = ResponseObj()
        try:
            machine_id = request.param_info.get("machine_id")
            request = service_model.BmServiceMachine.objects.get(id=machine_id)
            order_dict = request.__dict__
            order_dict.pop("_state")
            response_obj.content = order_dict
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "machine 数据查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ServiceRetrySerializer,
                         operation_description="重新执行服务器创建",
                         responses={200: response_serializers.MachineGetResponsesSerializer})
    @auth_utils.param_info_decrypt
    def view_baremetal_service_retry(self, request):
        response_obj = ResponseObj()
        try:
            order_id = request.param_info.get("order_id")
            machine_id = request.param_info.get("machine_id")
            service_machine_list_obj = service_model.BmServiceMachine.objects.filter(order_id=order_id)
            if machine_id:
                service_machine_list_obj = service_machine_list_obj.filter(id=machine_id)
            retry_job_list = []
            for machine_obj in service_machine_list_obj:
                if machine_obj.uuid:
                    continue

                service_info_json = eval(machine_obj.job_model)
                job_executor.delay(service_info_json)
                retry_job_list.append(service_info_json)
            response_obj.content = retry_job_list
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "service create job retry 失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ServiceInstanceUuidSerializer,
                         operation_description="查询服务器挂载信息",
                         responses={200: response_serializers.InstanceAttachedInfoObjResponsesSerializer})
    @auth_utils.param_info_decrypt
    def service_attached_info_of_instance(self, request):
        response_obj = ResponseObj()

        try:
            instance_uuid = request.param_info.get("instance_uuid")

            attached_dict = {}

            # 磁盘挂载信息
            volume_list_obj = service_model.BmServiceVolume.objects.filter(instance_uuid=instance_uuid,
                                                                           is_measure_end=False)
            attached_dict["volume_list"] = [u.__dict__ for u in volume_list_obj]

            # 弹性IP挂载信息
            floating_ip_list_obj = service_model.BmServiceFloatingIp.objects.filter(attached=True,
                                                                                    instance_uuid=instance_uuid,
                                                                                    is_measure_end=False)
            attached_dict["floating_ip_list"] = [u.__dict__ for u in floating_ip_list_obj]
            response_obj.content = attached_dict
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "查询服务器挂载信息失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")


class BaremetalServiceBaseResource(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(operation_description="获取镜像列表",
                         responses={200: response_serializers.ImageListResponsesSerializer}
                         )
    # @auth_utils.token_verify
    @check_element_permission
    @auth_utils.param_info_decrypt
    def images_list(self, request):
        response_obj = ResponseObj()
        try:
            request = service_model.BmServiceImages.objects.filter(status="active").order_by("image_name")
            response_obj.content = [u.__dict__ for u in request]
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "镜像列表查询失败", "admin_info": ex}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(operation_description="获取服务器列表",
                         responses={200: response_serializers.FloverListResponsesSerializer}
                         )
    # @auth_utils.token_verify
    # @check_element_permission
    @auth_utils.param_info_decrypt
    def flavor_list(self, request):
        response_obj = ResponseObj()
        try:
            request = service_model.BmServiceFlavor.objects.filter(status="active").order_by("type_name")
            response_obj.content = [u.__dict__ for u in request]
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "服务器列表查询失败", "admin_info": ex}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(operation_description="更新flavor的数量",
                         responses={200: response_serializers.UpdateFlavorCountResponsesSerializer})
    @utils.param_info
    def update_flavor_count(self, request):
        response_obj = ResponseObj()
        try:
            openstack_client = self.openstack_provider.get_admin_openstack_client()
            # node list 查询
            query_dict = {"provision_state": "available", "instance_id": None}
            node_obj = openstack_client.baremetal.nodes(details=True, **query_dict)
            node_info_list = list(node_obj)

            # flavor 数量 更新
            flavor_count_dict = {}
            flavor_list_obj = service_model.BmServiceFlavor.objects.filter(status=service_model.FLAVOR_ACTIVE)
            for flavor_obj in flavor_list_obj:
                flavor_obj.count = 0
                for node_info in node_info_list:
                    if node_info.resource_class == flavor_obj.resource_class:
                        flavor_obj.count += 1
                flavor_count_dict[flavor_obj.openstack_flavor_name] = flavor_obj.count
                flavor_obj.save()
        except Exception as ex:
            return response_obj.json_exception_serial(user_info='服务器列表查询失败！', admin_info=str(ex), no=500)
        return response_obj.json_serial(flavor_count_dict)

    # @auth_utils.token_verify
    @swagger_auto_schema(operation_description="获取带宽规则列表",
                         responses={200: response_serializers.QosPolicyListResponsesSerializer}
                         )
    @check_element_permission
    @auth_utils.param_info_decrypt
    def qos_policy_list(self, request):
        response_obj = ResponseObj()
        try:
            request = service_model.BmServiceQosPolicy.objects.values("id", "qos_policy_count",
                                                                      "qos_policy_name").all().order_by(
                "qos_policy_count")
            qos_policy_dict = {}
            for qos_policy in request:
                qos_policy_dict[qos_policy["qos_policy_count"]] = qos_policy

            start = request[0].get("qos_policy_count")
            end = start + request.count() - 1
            response_obj.content = {"start": start, "end": end, "qos_policy_dict": qos_policy_dict}
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "带宽规则列表查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")


class BaremetalServiceFloatingIPViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()
        self.cmdb_provider = ServiceCmdbProvider()

    def get_firewall_rule(self, firewall_id):
        firewall_rules = []
        firewall = service_model.Firewalls.objects.get(id=firewall_id)
        firewall_rule_objects = firewall.firewallrule_set.all()
        for object in firewall_rule_objects:
            firewall_rules.append(object.to_dict())
        return firewall.to_dict(), firewall_rules

    @swagger_auto_schema(
        operation_description="检查配额(需要在登陆下调用接口)",
        responses={200: response_serializers.FloatingIpQuotaResponsesSerializer}
    )
    @check_element_permission
    @utils.param_info
    def floating_ip_quota(self, request):
        response_obj = ResponseObj()
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            openstack_client = utils.get_openstack_client(request)
            result = self.service_floatingip_provider.get_floatingip_quota(openstack_client, project_id)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="检查配额失败", admin_info=str(e), no=300)
        return response_obj.json_serial(result)

    @staticmethod
    def check_shared_bandwidth_quota(project_id, shared_bandwidth_id, service_floating_ip_count):
        fip_used_count = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                          is_measure_end=False,
                                                                          qos_policy_id=shared_bandwidth_id).count()
        bandwidth_fip_quota_info = service_model.ShareBandWidthQuota.objects.filter(project_id=project_id).first()
        bandwidth_fip_quota_count = bandwidth_fip_quota_info.floating_ip_count \
            if bandwidth_fip_quota_info else DEFAULT_BANDWIDTH_FLOATINGIP_COUNT

        if fip_used_count + service_floating_ip_count > bandwidth_fip_quota_count:
            return False
        return True

    @swagger_auto_schema(request_body=serializers.ServiceCreateFloatingIpSerializer,
                         operation_description="购买弹性公网ip",
                         responses={200: response_serializers.FloatingIpCreatedResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def floating_ip_create(self, request):
        response_obj = ResponseObj()
        order_info = request.param_info.get("order_info")
        floating_ip_info = request.param_info.get("floating_ip_info")
        firewall_id = request.param_info.get('firewall_id')
        available_count = 0

        try:
            with transaction.atomic():
                account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)

                # 创建订单
                self.logger.info("create order to floating ip :")
                order_info["project"] = project_result
                order_info["delivery_status"] = service_model.ORDER_STATUS_DELIVERING

                self.logger.info("create order param : %s" % order_info)
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    self.logger.error("create order result %s " % order_result)
                    raise Exception(order_result)
                self.logger.info("create order result : %s" % order_result)

                result = {"order_result": order_result, "floating_ip_list_result": []}
                # 获取qos policy id
                shared_qos_policy_type = floating_ip_info.get("shared_qos_policy_type", False)
                if not shared_qos_policy_type:
                    qos_policy_name = floating_ip_info.get("qos_policy_name")
                    qos_policy_obj = self.service_provider.get_qos_policy_info(qos_policy_name=qos_policy_name)
                    if not qos_policy_obj.is_ok:
                        self.logger.error("fail to get qos policy info %s" % qos_policy_obj.message)
                        raise Exception(qos_policy_obj.message)
                    qos_policy_id = qos_policy_obj.content.id
                else:

                    qos_policy_id = floating_ip_info.get('qos_policy_id')
                    if not qos_policy_id:
                        raise Exception("qos_policy_id is None")
                    shared_bandwidth_info = service_model.BmShareBandWidth.objects.filter(
                        shared_bandwidth_id=qos_policy_id, is_measure_end=False).first()
                    if not shared_bandwidth_info:
                        return response_obj.json_exception_serial(user_info="该共享带宽不存在",
                                                                  admin_info="bandwidth not found",
                                                                  no=404)
                    if not self.check_shared_bandwidth_quota(project_id, qos_policy_id,
                                                             order_info.get("service_count", 0)):
                        user_info = "该共享带宽可绑定弹性公网ip超过上限"
                        admin_info = "quota error"
                        return response_obj.json_exception_serial(user_info=user_info,
                                                                  admin_info=admin_info,
                                                                  no=500)
                    qos_policy_name = shared_bandwidth_info.name

                # 创建弹性 IP
                region = order_info.get("region", request.session.get("region"))
                external_line_type = floating_ip_info.get("external_line_type")
                external_region_network = env_config.external_networks.get(region)
                if not external_region_network:
                    self.logger.error("Fail to find external network info in region %s" % region)
                    raise Exception("Fail to find external network info in region %s" % region)
                external_network_list = external_region_network.get(external_line_type)
                if not external_network_list:
                    self.logger.error("Fail to find external network info in network type  %s" % external_line_type)
                    raise Exception("Fail to find external network info in network type  %s" % external_line_type)
                external_network = external_network_list[0]
                external_name = external_network.get("network_name")
                external_name_id = external_network.get("network_id")

                openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
                check_result, available_count = self.service_floatingip_provider.check_fip_quota(
                    openstack_client, order_info.get("service_count", 0), project_id)

                if not check_result:
                    raise exc.QuotaError(count=available_count)

                if not self.service_floatingip_provider.check_fip_pools(order_info.get("service_count", 0),
                                                                        external_name_id):
                    raise exc.PoolResourceError()

                for count in range(order_info.get("service_count", 0)):
                    if not shared_qos_policy_type:
                        ip_create_result = openstack_client.network.create_ip(
                            **{"floating_network_id": external_name_id, "qos_policy_id": qos_policy_id}
                        )
                        if not ip_create_result:
                            self.logger.error("fail to create ip  %s" % ip_create_result)
                            raise Exception(ip_create_result)
                    else:
                        ip_create_result = openstack_client.network.create_ip(
                            **{"floating_network_id": external_name_id}
                        )
                        if not ip_create_result:
                            self.logger.error("fail to create ip  %s" % ip_create_result)
                            raise Exception(ip_create_result)

                    # 通过弹性IP 创建平台数据
                    service_floating_ip_dict = {
                        "order_id": order_result.id,
                        "account_id": account_id,
                        "project_id": project_id,
                        "contract_number": order_result.contract_number,
                        "external_line_type": external_line_type,
                        "external_name": external_name,
                        "external_name_id": external_name_id,
                        "floating_ip_id": ip_create_result.id,
                        "floating_ip": ip_create_result.floating_ip_address,
                        "qos_policy_id": qos_policy_id,
                        "qos_policy_name": qos_policy_name,
                        "create_at": datetime.datetime.now(),
                        "first_create_at": datetime.datetime.now(),
                        "status": "active",
                        "is_measure_end": False,
                        "shared_qos_policy_type": shared_qos_policy_type
                    }
                    # 合同号信息
                    floating_ip_result = service_model.BmServiceFloatingIp.objects.create(**service_floating_ip_dict)
                    if not floating_ip_result:
                        raise Exception(floating_ip_result)

                    floating_ip_firewall_mapping = service_model.BmFloatingipfirewallMapping.objects.create(
                        floating_ip_id=floating_ip_result.floating_ip_id, floating_ip=floating_ip_result.floating_ip,
                        firewall_id=firewall_id)
                    firewall, firewall_rules = self.get_firewall_rule(firewall_id)
                    if shared_qos_policy_type:
                        traffic_shaper = qos_policy_id
                    else:
                        traffic_shaper = None
                    associate_firewall.delay(floating_ip_result.floating_ip, firewall, firewall_rules,
                                             traffic_shaper=traffic_shaper)

                    floating_ip_result.firewall_info = {"firewall_name": firewall.get('name'),
                                                        "firewall_id": firewall.get('id')}
                    # 添加带宽大小信息
                    floating_ip_result.qos_max_kbps = self.service_floatingip_provider.get_qos_max_kbps(
                        floating_ip_result)

                    result["floating_ip_list_result"].append(floating_ip_result)
                    send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                                service_type=audit_types.EIP, resource_id=floating_ip_result.floating_ip_id,
                                                resource_name=floating_ip_result.floating_ip, resource_type=audit_types.EIP,
                                                trace_name=audit_types.CREATE, trace_type=audit_types.CONSOLEACTION,
                                                contract_number=order_info.get('contract_number'), request=request.param_info,
                                                response=result)

                # 订单更新
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()

        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='配额不足，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info="弹性公网ip创建失败",
                    admin_info=str(e),
                    no=500
                )
        except exc.QuotaError as ex:
            return response_obj.json_exception_serial(user_info="配额不足, 您的剩余可用个数为 %s" % available_count,
                                                      admin_info=str(ex),
                                                      no=300)
        except exc.PoolResourceError as ex:
            return response_obj.json_exception_serial(user_info="配额不足，请联系管理员",
                                                      admin_info=str(ex),
                                                      no=300)

        except Exception as ex:
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.EIP, resource_id=None,
                                        resource_name=None, resource_type=audit_types.EIP,
                                        trace_name=audit_types.CREATE, trace_type=audit_types.CONSOLEACTION,
                                        contract_number=order_info.get('contract_number'), request=request.param_info,
                                        response=str(ex), code=500)
            return response_obj.json_exception_serial(user_info="浮动ip创建失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.ServiceCreateFloatingIpWithOrderSerializer,
                         operation_description="服务器申请时，通过job executor里面订单信息创建 弹性公网IP")
    @utils.param_info
    def floating_ip_create_with_order(self, request):
        """
        服务器申请时，通过job executor里面订单信息创建 弹性公网IP
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        order_info = request.param_info.get("order_info")
        floating_ip_info = request.param_info.get("floating_ip_info")
        firewall_id = request.param_info.get('firewall_id')
        region = request.session.get('region', env_config.region_name)
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
            project_result = auth_models.BmProject.objects.filter(id=project_id).first()
            if not project_result:
                raise Exception("project id %s 对项目不存在" % project_id)
            order_info["project"] = project_result

            # 获取qos policy id
            shared_qos_policy_type = floating_ip_info.get("shared_qos_policy_type", False)
            if not shared_qos_policy_type:
                qos_policy_name = floating_ip_info.get("qos_policy_name")
                qos_policy_obj = self.service_provider.get_qos_policy_info(qos_policy_name=qos_policy_name)
                if not qos_policy_obj.is_ok:
                    self.logger.error("fail to get qos policy info %s" % qos_policy_obj.message)
                    raise Exception(qos_policy_obj.message)
                qos_policy_id = qos_policy_obj.content.id
            else:
                qos_policy_id = floating_ip_info.get('qos_policy_id')
                if not qos_policy_id:
                    raise Exception("qos_policy_id is None")
                shared_bandwidth_info = service_model.BmShareBandWidth.objects.filter(
                    shared_bandwidth_id=qos_policy_id, is_measure_end=False).first()
                if not shared_bandwidth_info:
                    return response_obj.json_exception_serial(user_info="改共享带宽不存在",
                                                              admin_info="bandwidth not found",
                                                              no=404)
                if not self.check_shared_bandwidth_quota(project_id, qos_policy_id, order_info.get("service_count", 0)):
                    user_info = "该共享带宽可绑定弹性公网ip超过上限"
                    admin_info = "quota error"
                    return response_obj.json_exception_serial(user_info=user_info,
                                                              admin_info=admin_info,
                                                              no=500)
                qos_policy_name = shared_bandwidth_info.name

            # 获取子网信息
            region = order_info.get("region", request.session.get("region"))
            external_line_type = floating_ip_info.get("external_line_type")
            external_network = env_config.external_networks.get(region).get(external_line_type)[0]
            external_name = external_network.get("network_name")
            external_name_id = external_network.get("network_id")

            # 检查配额
            if not self.service_floatingip_provider.check_fip_pools(order_info.get("service_count", 0),
                                                                    external_name_id):
                return response_obj.json_exception_serial(
                    user_info="配额不足，联系管理员",
                    admin_info="No floatingip resource",
                    no=500)

            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            check_result, available_count = self.service_floatingip_provider.check_fip_quota(
                openstack_client, order_info.get("service_count", 0), project_id)

            if not check_result:
                return response_obj.json_exception_serial(
                    user_info="配额不足，您的可用公网ip个数为%s" % available_count,
                    admin_info="Error! quota is not enough.",
                    no=500
                )

            result = {"floating_ip_list_result": []}
            with transaction.atomic():
                # openstack 平台分配IP
                if not shared_qos_policy_type:
                    ip_create_result = openstack_client.network.create_ip(
                        **{"floating_network_id": external_name_id, "qos_policy_id": qos_policy_id}
                    )
                    if not ip_create_result:
                        self.logger.error("fail to create ip  %s" % ip_create_result)
                        raise Exception(ip_create_result)
                else:
                    ip_create_result = openstack_client.network.create_ip(
                        **{"floating_network_id": external_name_id}
                    )
                    if not ip_create_result:
                        self.logger.error("fail to create ip  %s" % ip_create_result)
                        raise Exception(ip_create_result)

                # 通过openstack 弹性IP 创建平台数据，异常回收IP
                try:
                    # 通过弹性IP 创建平台数据
                    service_floating_ip_dict = {
                        "order_id": order_info.get("id"),
                        "account_id": account_id,
                        "project_id": project_id,
                        "contract_number": order_info.get("contract_number"),
                        "external_line_type": external_line_type,
                        "external_name": external_name,
                        "external_name_id": external_name_id,
                        "floating_ip_id": ip_create_result.id,
                        "floating_ip": ip_create_result.floating_ip_address,
                        "qos_policy_id": qos_policy_id,
                        "qos_policy_name": qos_policy_name,
                        "create_at": datetime.datetime.now(),
                        "first_create_at": datetime.datetime.now(),
                        "status": "active",
                        "is_measure_end": False,
                        "shared_qos_policy_type": shared_qos_policy_type
                    }
                    # 合同号信息
                    floating_ip_result = service_model.BmServiceFloatingIp.objects.create(**service_floating_ip_dict)
                    if not floating_ip_result:
                        raise Exception(floating_ip_result)

                    # 防火墙绑定
                    service_model.BmFloatingipfirewallMapping.objects.create(
                        floating_ip_id=floating_ip_result.floating_ip_id, floating_ip=floating_ip_result.floating_ip,
                        firewall_id=firewall_id)
                    firewall, firewall_rules = self.get_firewall_rule(firewall_id)

                    if shared_qos_policy_type:
                        traffic_shaper = qos_policy_id
                    else:
                        traffic_shaper = None
                    associate_firewall.delay(floating_ip_result.floating_ip, firewall,
                                             firewall_rules, traffic_shaper=traffic_shaper)

                    floating_ip_result.firewall_info = {"firewall_name": firewall.get('name'),
                                                        "firewall_id": firewall.get('id')}

                    floating_ip_result.qos_max_kbps = self.service_floatingip_provider.get_qos_max_kbps(
                        floating_ip_result)

                    result["floating_ip_list_result"].append(floating_ip_result)
                    send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                                service_type=audit_types.EIP, resource_id=floating_ip_result.floating_ip_id,
                                                resource_name=floating_ip_result.floating_ip, resource_type=audit_types.EIP,
                                                trace_name=audit_types.CREATE, trace_type=audit_types.CONSOLEACTION,
                                                contract_number=order_info.get('contract_number'), request=request.param_info,
                                                response=result)

                except Exception as back_ex:
                    openstack_client.network.delete_ip(floating_ip=ip_create_result.id)
                    raise Exception(str(back_ex))
        except Exception as ex:
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.EIP, resource_id=None,
                                        resource_name=None, resource_type=audit_types.EIP,
                                        trace_name=audit_types.CREATE, trace_type=audit_types.CONSOLEACTION,
                                        contract_number=order_info.get('contract_number'), request=request.param_info,
                                        response=str(ex), code=500)
            return response_obj.json_exception_serial(user_info="浮动ip创建失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.ServiceFloatingIpQuotasSetSerializer,
                         operation_description="调整浮动IP带宽",
                         responses={200: response_serializers.FloatingIpQuotaSetResponsesSerializer})
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.EIP, trace_name=audit_types.EIP_UPDATE_BANDWIDTH,
                                         resource_id_key='floating_ip_id', resource_name_key='floating_ip',
                                         resource_type=audit_types.EIP)
    def floating_ip_quotas_set(self, request):
        """
        更新带宽
        扩容，进行本地数据更新
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        order_info = request.param_info.get("order_info")
        floating_ip_id = request.param_info.get("floating_ip_id")
        qos_policy_name = request.param_info.get("qos_policy_name")
        account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
        try:
            with transaction.atomic():
                # 更新源floating ip 状态为完成状态
                self.logger.info("update service floating ip status")
                floating_ip_obj = service_model.BmServiceFloatingIp.objects.filter(
                    floating_ip_id=floating_ip_id, is_measure_end=False, status="active").first()
                if not floating_ip_obj:
                    raise Exception("fail to find floating ip info by id %s " % floating_ip_id)
                if floating_ip_obj.shared_qos_policy_type:
                    return response_obj.json_exception_serial(user_info="带宽类型为共享带宽，无法调整",
                                                              admin_info="shared bandwidth can not "
                                                                         "update with floatingip",
                                                              no=500)
                floating_ip_obj.update_at = datetime.datetime.now()
                floating_ip_obj.is_measure_end = True
                floating_ip_obj.save()
                self.logger.info("update service floating ip status result is done True")

                # 创建新的订单
                origin_order_id = floating_ip_obj.order_id
                order_info["account_id"] = account_id
                alter_order_obj = order_handler.create_new_order_for_alter(origin_order_id=origin_order_id,
                                                                           alter_order_info=order_info,
                                                                           service_count=1)
                if not alter_order_obj.is_ok:
                    raise Exception(alter_order_obj.message)
                order_result = alter_order_obj.content

                # 获取qos policy id
                qos_policy_obj = self.service_provider.get_qos_policy_info(qos_policy_name=qos_policy_name)
                if not qos_policy_obj.is_ok:
                    raise Exception(qos_policy_obj.message)
                qos_policy_id = qos_policy_obj.content.id

                # 根据扩容信息，及新订单信息，创建新的数据信息
                floating_ip_dict = floating_ip_obj.__dict__
                floating_ip_dict["order_id"] = order_result.id
                floating_ip_dict["account_id"] = account_id
                floating_ip_dict["qos_policy_id"] = qos_policy_id
                floating_ip_dict["qos_policy_name"] = qos_policy_name
                floating_ip_dict["is_measure_end"] = False
                floating_ip_dict["create_at"] = datetime.datetime.now()
                floating_ip_dict.pop("id")
                floating_ip_dict.pop("update_at")
                floating_ip_dict.pop("_state")
                self.logger.info("create new service floating ip by param %s" % floating_ip_dict)
                new_floating_ip_obj = service_model.BmServiceFloatingIp.objects.create(**floating_ip_dict)
                if not new_floating_ip_obj:
                    raise Exception(new_floating_ip_obj)
                self.logger.info("create new service floating ip result %s" % new_floating_ip_obj)

                # openstack 更新带宽
                self.logger.info("update openstack floating ip qos:")
                openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
                result = openstack_client.network.update_ip(floating_ip=floating_ip_id,
                                                            **{"qos_policy_id": qos_policy_id})
                if not result:
                    raise Exception(result)
                self.logger.info("update openstack floating ip qos result %s" % result)

                new_floating_ip_obj.qos_max_kbps = self.service_floatingip_provider.get_qos_max_kbps(
                    new_floating_ip_obj)
                # 订单交付
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()
        except Exception as ex:
            self.logger.error("update service floating ip error! %s " % str(ex))
            return response_obj.json_exception_serial(user_info="浮动ip设置带宽失败", admin_info=str(ex), no=300)
        self.logger.info("floating IP qos set success")
        return response_obj.json_serial(new_floating_ip_obj)

    def __create_new_order_for_alter(self, origin_order_id, alter_order_info):
        response_obj = ResponseObj()
        try:
            self.logger.info("find origin order info by order id %s " % origin_order_id)
            origin_order_obj = service_model.BmServiceOrder.objects.filter(id=origin_order_id).first()
            if not origin_order_obj:
                self.logger.error("fail to find origin order info by order id %s" % origin_order_id)
                raise Exception("fail to find origin order info by order id %s" % origin_order_id)

            self.logger.info("combine new order param to resource alter")
            new_order_info = origin_order_obj.__dict__
            pop_list = ["_state", "id", "deleted", "update_at", "create_at"]
            for pop_param in pop_list:
                new_order_info.pop(pop_param)
            new_order_info["delivery_status"] = service_model.ORDER_STATUS_DELIVERING
            new_order_info["service_count"] = 1
            new_order_info["order_type"] = alter_order_info.get("order_type", service_model.ORDER_TYPE_ALTERATION)
            new_order_info["order_price"] = alter_order_info.get("order_price", 0)
            new_order_info["product_type"] = alter_order_info.get("product_type")
            new_order_info["product_info"] = alter_order_info.get("product_info")
            new_order_info["account_id"] = alter_order_info.get("account_id")

            self.logger.info("create alter order by param %s " % new_order_info)
            order_result = service_model.BmServiceOrder.objects.create(**new_order_info)
            if not order_result:
                self.logger.error("fail to create alter order %s " % order_result)
                raise Exception(order_result)
            response_obj.content = order_result
        except Exception as ex:
            response_obj.message = "Fail to create alter order %s " % str(ex)
            response_obj.is_ok = False
            response_obj.no = 505
        return response_obj

    @swagger_auto_schema(request_body=serializers.ServiceDeleteFloatingIpSerializer,
                         operation_description="弹性公网IP的删除操作",
                         responses={200: response_serializers.FloatingIpDeletedResponsesSerializer})
    @check_element_permission
    @utils.param_info
    def floating_ip_delete(self, request):
        response_obj = ResponseObj()
        # account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
        floating_ip_id_list = request.param_info.get("floating_ip_id_list")
        delete_result = {}
        region = request.session.get("region", env_config.region_name)
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            for floating_ip_id in floating_ip_id_list:
                result = openstack_client.delete_floating_ip(floating_ip_id=floating_ip_id)
                delete_result[floating_ip_id] = result

                # 默认防火墙
                mapping = service_model.BmFloatingipfirewallMapping.objects.filter(
                    floating_ip_id=floating_ip_id).first()
                floating_ip = None
                if mapping:
                    floating_ip = mapping.floating_ip
                    firewall, firewall_rules = self.get_firewall_rule(mapping.firewall_id)
                    disassociate_firewall.delay(mapping.floating_ip, firewall)
                    mapping.delete()

                # 平台数据删除
                # floating_ip_result = service_model.BmServiceFloatingIp.objects.filter(
                #     floating_ip_id__in=floating_ip_id_list)
                floating_ip_result = service_model.BmServiceFloatingIp.objects.filter(
                    floating_ip_id=floating_ip_id)
                update_param = {
                    # "account_id": account_id,
                    "status": "deleted",
                    "update_at": datetime.datetime.now(),
                    "attached": False,
                    "attached_type": None,
                    "instance_uuid": None,
                    "instance_name": None,
                    "fixed_address": None,
                    "is_measure_end": True
                }
                floating_ip_result.filter(is_measure_end=False).update(**update_param)
                send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                            service_type=audit_types.EIP, resource_id=floating_ip_id,
                                            resource_name=floating_ip, resource_type=audit_types.EIP,
                                            trace_name=audit_types.DELETE,
                                            request=request.param_info, response="success")
        except Exception as ex:
            send_cloud_log_notification(region=region, project_id=project_id, user_id=account_id,
                                        service_type=audit_types.EIP, resource_type=audit_types.EIP,
                                        trace_name=audit_types.DELETE,
                                        request=request.param_info, response=str(ex), code=500)
            return response_obj.json_exception_serial(user_info="浮动ip删除失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(delete_result)

    @swagger_auto_schema(request_body=serializers.ServiceDeleteFloatingIpSerializer,
                         operation_description="弹性公网IP的回滚操作",
                         responses={200: response_serializers.FloatingIpDeletedResponsesSerializer})
    @utils.param_info
    def floating_ip_roll_back(self, request):
        """
        服务交付异常回滚。通过弹性公网IP的ID列表进行平台弹性ip信息删除，及openstack平台IP回收。
        :param request: floating_ip_id_list
        :return:
        """
        response_obj = ResponseObj()
        floating_ip_id_list = request.param_info.get("floating_ip_id_list")
        delete_result = {}
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            # 平台数据删除
            service_model.BmServiceFloatingIp.objects.filter(
                floating_ip_id__in=floating_ip_id_list).delete()

            # openstack 数据删除，及防火墙解绑。
            for floating_ip_id in floating_ip_id_list:

                result = openstack_client.delete_floating_ip(floating_ip_id=floating_ip_id)
                delete_result[floating_ip_id] = result

                # 默认防火墙
                mapping = service_model.BmFloatingipfirewallMapping.objects.filter(
                    floating_ip_id=floating_ip_id).first()
                if mapping:
                    firewall, firewall_rules = self.get_firewall_rule(mapping.firewall_id)
                    disassociate_firewall.delay(mapping.floating_ip, firewall)
                    mapping.delete()

                # 弹性IP数据删除
                # floating_ip_result = service_model.BmServiceFloatingIp.objects.filter(
                #     floating_ip_id=floating_ip_id).delete()
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="浮动ip删除失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(delete_result)

    @swagger_auto_schema(
        operation_description="查看浮动ip列表",
        responses={200: response_serializers.FloatingIpListResponsesSerializer})
    @check_element_permission
    @utils.param_info
    def floating_ip_list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:

            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            self.logger.info("query openstack floating ip list:")
            floating_ip_obj = openstack_client.list_floating_ips()
            floating_ip_dict = {}
            for floating_ip in floating_ip_obj:
                floating_ip_dict[floating_ip.id] = {"attached": floating_ip.attached,
                                                    "fixed_ip_address": floating_ip.fixed_ip_address}
            self.logger.info("query openstack floating ip result: %s" % floating_ip_dict)

            self.logger.info("query service floating ip list:")
            service_floating_ip_obj = service_model.BmServiceFloatingIp.objects.filter(
                project_id=project_id, status="active", is_measure_end=False).order_by('-create_at')
            service_floating_ip_list = []
            for service_floating_ip in service_floating_ip_obj:
                if service_floating_ip.floating_ip_id in floating_ip_dict:
                    # 添加防火墙 信息
                    firewall = {}
                    mapping = service_model.BmFloatingipfirewallMapping.objects.filter(
                        floating_ip_id=service_floating_ip.floating_ip_id).first()
                    if mapping:
                        firewall, firewall_rule = self.get_firewall_rule(mapping.firewall_id)
                    service_floating_ip.firewall_info = {"firewall_name": firewall.get('name', '-'),
                                                         "firewall_id": firewall.get('id', '-')}

                    # 添加合同信息
                    contract_obj = service_model.BmContract.objects.filter(
                        contract_number=service_floating_ip.contract_number,
                        status="active")
                    if contract_obj:
                        service_floating_ip.contract_info = contract_obj.first()
                    else:
                        service_floating_ip.contract_info = {}
                    service_floating_ip.qos_max_kbps = self.service_floatingip_provider.get_qos_max_kbps(
                        service_floating_ip)
                    service_floating_ip_list.append(service_floating_ip.__dict__)
            self.logger.info("query service floating ip list result : %s " % service_floating_ip_list)
        except Exception as ex:
            self.logger.error("query service floating ip list result : %s " % str(ex))
            return response_obj.json_exception_serial("查看浮动ip列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(service_floating_ip_list)

    @swagger_auto_schema(
        operation_description="查看未绑定的浮动ip列表",
        responses={200: response_serializers.FloatingIpListResponsesSerializer})
    # @check_element_permission
    @utils.param_info
    def floating_ip_list_no_attached(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            self.logger.info("query openstack floating ip list:")
            floating_ip_obj = openstack_client.list_floating_ips()
            floating_ip_dict = {}
            for floating_ip in floating_ip_obj:
                if not floating_ip.attached:
                    floating_ip_dict[floating_ip.id] = {"attached": floating_ip.attached,
                                                        "floating_ip_address": floating_ip.floating_ip_address}
            self.logger.info("query openstack floating ip result: %s" % floating_ip_dict)

            self.logger.info("query service floating ip list:")
            service_floating_ip_obj = service_model.BmServiceFloatingIp.objects.filter(
                project_id=project_id, status="active", is_measure_end=False, attached=False).order_by('-create_at')
            service_floating_ip_list = []
            for service_floating_ip in service_floating_ip_obj:
                if service_floating_ip.floating_ip_id in floating_ip_dict:
                    # 添加防火墙 信息
                    firewall = {}
                    mapping = service_model.BmFloatingipfirewallMapping.objects.filter(
                        floating_ip_id=service_floating_ip.floating_ip_id).first()
                    if mapping:
                        firewall, firewall_rule = self.get_firewall_rule(mapping.firewall_id)
                    service_floating_ip.firewall_info = {"firewall_name": firewall.get('name', '-'),
                                                         "firewall_id": firewall.get('id', '-')}

                    # # 添加合同信息
                    # contract_obj = service_model.BmContract.objects.filter(
                    #     contract_number=service_floating_ip.contract_number,
                    #     status="active")
                    # if contract_obj:
                    #     service_floating_ip.contract_info = contract_obj.first()
                    # else:
                    #     service_floating_ip.contract_info = {}
                    # # service_floating_ip.attached = floating_ip_dict[service_floating_ip.floating_ip_id].get("attached")
                    # # service_floating_i  p.fixed_ip_address= floating_ip_dict[service_floating_ip.floating_ip_id].get("fixed_ip_address")
                    service_floating_ip_list.append(service_floating_ip.__dict__)
            self.logger.info("query service floating ip list result : %s " % service_floating_ip_list)
        except Exception as ex:
            self.logger.error("query service floating ip list result : %s " % str(ex))
            return response_obj.json_exception_serial("查看浮动ip列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(service_floating_ip_list)

    @swagger_auto_schema(request_body=serializers.ServiceAddFloatingIptoServerSerializer,
                         operation_description="实例关联浮动ip",
                         responses={200: response_serializers.FloatingIpAttachToServerResponsesSerializer}
                         )
    @utils.param_info
    # 服务类型归属于ECBM
    @send_cloud_audit_log_single_request(service_type=audit_types.EIP, resource_type=audit_types.EIP,
                                         trace_name=audit_types.EIP_ATTACH, resource_id_key='floating_ip_id',
                                         resource_name_key='floating_ip')
    def attach_ip_to_server(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        instance_uuid = param_info.get("instance_uuid")
        instance_name = param_info.get("instance_name")
        floating_ip_id = param_info.get("floating_ip_id")
        floating_ip_address = param_info.get("floating_ip_address")
        fixed_address = param_info.get("fixed_address", None)
        try:
            self.logger.info("openstack attach ip %s to server %s:" % (floating_ip_id, instance_uuid))
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            # 服务器查询
            server_obj = openstack_client.get_server(name_or_id=instance_uuid)
            if not server_obj:
                raise Exception("Fail to find instance by uuid {uuid}. Result {server_obj}".format(uuid=instance_uuid,
                                                                                                   server_obj=server_obj))
            # 查询弹性IP信息
            service_attach_obj = service_model.BmServiceFloatingIp.objects.get(floating_ip_id=floating_ip_id,
                                                                               is_measure_end=False)
            if not service_attach_obj:
                raise Exception("Fail to find floating IP by id {floating_ip_id}. Result {service_attach_obj}".format(
                    floating_ip_id=floating_ip_id,
                    service_attach_obj=service_attach_obj))

            # 弹性IP挂载
            with transaction.atomic():
                # 平台保存相关挂载数据信息
                service_attach_obj.attached = True
                service_attach_obj.attached_type = service_model.FLOATINGIP_AATTACH_ECBM
                service_attach_obj.instance_uuid = instance_uuid
                service_attach_obj.instance_name = instance_name
                service_attach_obj.fixed_address = fixed_address
                # service_attach_obj.update_at = datetime.datetime.now()
                service_attach_obj.save()

                # openstack进行弹性IP挂载
                openstack_client.add_ip_list(server=server_obj, ips=floating_ip_address,
                                             fixed_address=fixed_address)
                self.logger.info("openstack attach ip to server result: %s" % service_attach_obj)

                # 挂载成功，进行CMDB数据同步
                cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=instance_uuid, status=None)
                self.logger.info("CMDB the ip attach to server sys result: %s" % cmdb_result)
        except Exception as ex:
            self.logger.error("openstack attach ip to server result: %s" % str(ex))
            return response_obj.json_exception_serial(user_info="实例关联浮动ip失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(service_attach_obj)

    @swagger_auto_schema(request_body=serializers.ServiceDetachFloatingIptoServerSerializer,
                         operation_description="实例解绑浮动ip",
                         responses={200: response_serializers.FloatingIpDetachFromServerResponsesSerializer})
    @check_element_permission
    @utils.param_info
    @send_cloud_audit_log_single_request(service_type=audit_types.EIP, resource_type=audit_types.EIP,
                                         trace_name=audit_types.EIP_DETACH, resource_id_key='floating_ip_id',
                                         resource_name_key='floating_ip')
    def detach_ip_from_server(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        instance_uuid = param_info.get("instance_uuid")
        floating_ip_id = param_info.get("floating_ip_id")

        try:
            with transaction.atomic():
                openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)

                service_attach_obj = self.service_floatingip_provider.detach_ip_from_server(
                    openstack_client, instance_uuid, floating_ip_id)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="实例解绑浮动ip失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(service_attach_obj)

    @swagger_auto_schema(
        operation_description="查询可绑定实例列表",
        responses={200: response_serializers.InstanceListAvaliableResponsesSerializer})
    @check_element_permission
    def instance_list_avaliable_to_floating_ip(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            # TODO  待进行与平台数据关联
            self.logger.info("query openstack floating ip list:")
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)

            deleted_instance = service_model.BmServiceInstance.objects.values_list('uuid', flat=True).filter(
                project_id=project_id, deleted=True)

            # 获取已绑定IP的实例port
            floating_ip_obj = openstack_client.list_floating_ips()
            attached_port_list = []
            for floating_ip in floating_ip_obj:
                if floating_ip.attached:
                    attached_port_list.append(floating_ip.fixed_ip_address)

            # 查询可绑定实例列表
            instance_list = openstack_client.compute.servers()
            instance_port_list = []
            for instance in instance_list:
                if instance.id in deleted_instance:
                    continue
                instance_dict = {"instance_name": instance.name, "instance_id": instance.id, "port": []}
                for address in instance.addresses.values():
                    for ip_dict in address:
                        if ip_dict.get("OS-EXT-IPS:type") == "fixed" and ip_dict['addr'] not in attached_port_list:
                            instance_dict["port"].append(ip_dict["addr"])
                if instance_dict:
                    instance_port_list.append(instance_dict)
        except Exception as ex:
            self.logger.error("query service floating ip list result : %s " % str(ex))
            return response_obj.json_exception_serial("查看浮动ip列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(instance_port_list)

    @swagger_auto_schema(request_body=serializers.ServiceFloatingIpAssociateFirewall,
                         operation_description="弹性公网IP关联防火墙",
                         responses={200: response_serializers.FloatingIpAssociateFirewallResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def floating_ip_associate_firewall(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        region = request.session.get('region', env_config.region_name)
        account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        floating_ip_id = param_info.get("floating_ip_id")
        floating_ip = param_info.get('floating_ip')
        firewall_id = param_info.get('firewall_id')
        result = {}
        try:
            fip_info = service_model.BmServiceFloatingIp.objects.filter(floating_ip_id=floating_ip_id,
                                                                        is_measure_end=False).first()
            if fip_info and fip_info.shared_qos_policy_type:
                traffic_shaper = fip_info.qos_policy_id
            else:
                traffic_shaper = None
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
                                          new_firewall_rules, traffic_shaper=traffic_shaper)
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

                associate_firewall.delay(floating_ip, firewall.to_dict(), firewall_rules, traffic_shaper)
                result['floating_ip_id'] = floating_ip_id,
                result['firewall'] = firewall.to_dict()
            send_cloud_log_notification(region=region, user_id=account_id, project_id=project_id,
                                        service_type=audit_types.EIP, resource_id=floating_ip_id,
                                        resource_name=floating_ip, resource_type=audit_types.EIP,
                                        trace_name=audit_types.EIP_AS_FIREWALL, request=request.param_info,
                                        response=result)
        except Exception as ex:
            send_cloud_log_notification(region=region, user_id=account_id, project_id=project_id,
                                        service_type=audit_types.EIP, resource_id=floating_ip_id,
                                        resource_name=floating_ip, resource_type=audit_types.EIP,
                                        trace_name=audit_types.EIP_AS_FIREWALL, request=request.param_info,
                                        response=result, code=500)
            return response_obj.json_exception_serial(user_info="关联防火墙失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(result)


class BaremetalServiceVolumeViews(viewsets.ViewSet):
    def __init__(self):
        super(BaremetalServiceVolumeViews, self).__init__()
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.openstack_provider = OpenstackClientProvider()
        self.volume_provider = ServiceVolumeProvider()
        self.cmdb_provider = ServiceCmdbProvider()

    @utils.param_info
    def volume_quota(self, request):
        response_obj = ResponseObj()
        try:
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            openstack_client = utils.get_openstack_client(request)

            result = self.volume_provider.get_volume_quota(openstack_client, project_id)
        except Exception as e:
            return response_obj.json_exception_serial(user_info="检查配额失败", admin_info=str(e), no=300)
        return response_obj.json_serial(result)

    @utils.param_info
    def volume_type_list(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            result = openstack_client.list_volume_types()
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查看volume type失败", admin_info=ex, no=300)
        return response_obj.json_serial(result)

    def _create_openstack_volume(self, request, name, size, volume_type=None):
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        result = openstack_client.create_volume(size=size, name=name, volume_type=volume_type, wait=True)
        return result

    def _delete_openstack_volume(self, request, volume_id_list):
        self.logger.info("Start volume callback. Params {params}".format(params=volume_id_list))
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        volume_delete_result_dict = {}
        for volume_id in volume_id_list:
            volume_delete_result = openstack_client.delete_volume(name_or_id=volume_id)
            volume_delete_result_dict[volume_id] = volume_delete_result
        self.logger.info("Volume callback result {result}".format(result=volume_delete_result_dict))
        return volume_delete_result_dict

    @swagger_auto_schema(request_body=serializers.VolumeCreateSerializer,
                         operation_description="创建云硬盘",
                         responses={200: response_serializers.VolumeCreatedResponsesSerializer})
    @check_element_permission
    @utils.param_info
    def volume_create(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        order_info = param_info.get("order_info")
        service_count = order_info.get('service_count', 0)
        region = order_info.get("region")
        volume_info = param_info.get("volume_info")
        name = volume_info.get("name")
        size = int(volume_info.get("size", 0))
        volume_type = volume_info.get("volume_type")

        try:
            if not self.volume_provider.check_pool(size, service_count, volume_type):
                return response_obj.json_exception_serial(user_info="配额不足，请联系管理员", admin_info=None, no=500)

            project_id = request.session.get('project_id', request.COOKIES.get("project_id"))
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            check_result, volume_available_count, volume_available_size = self.volume_provider.check_volume_quota(
                openstack_client, size, service_count, project_id)
            if not check_result:
                user_info = "配额不足，您的剩余可用个数为%s, 剩余总大小为%sG " % (volume_available_count, volume_available_size)
                return response_obj.json_exception_serial(user_info=user_info, admin_info="Quota error", no=500)

        except Exception as e:
            return response_obj.json_exception_serial(user_info="创建云硬盘失败", admin_info=str(e), no=500)

        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)
                order_info["project"] = project_result

                # 创建订单
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)

                result = {"order_result": order_result, "volumes_result": []}
                if service_count == 1:
                    volume = self._create_openstack_volume(request, name, size, volume_type=volume_type)

                    server_volume_dict = {
                        "order_id": order_result.id,
                        "account_id": account_id,
                        "project_id": project_id,
                        "volume_type": volume_type,
                        "volume_id": volume.id,
                        "name": name,
                        "size": size,
                        "create_at": datetime.datetime.now(),
                        "is_measure_end": False,
                        "region": region,
                        "contract_number": order_info.get("contract_number"),
                        "first_create_at": datetime.datetime.now()
                    }
                    volume_result = service_model.BmServiceVolume.objects.create(**server_volume_dict)
                    result['volumes_result'].append(volume_result)

                else:
                    for count in range(service_count):
                        volume_name = name + '_' + str(count + 1)
                        volume = self._create_openstack_volume(request, volume_name, size, volume_type=volume_type)
                        server_volume_dict = {
                            "order_id": order_result.id,
                            "account_id": account_id,
                            "project_id": project_id,
                            "volume_type": volume_type,
                            "volume_id": volume.id,
                            "name": volume_name,
                            "size": size,
                            "create_at": datetime.datetime.now(),
                            "is_measure_end": False,
                            "region": region,
                            "contract_number": order_info.get("contract_number"),
                            "first_create_at": datetime.datetime.now()
                        }
                        volume_result = service_model.BmServiceVolume.objects.create(**server_volume_dict)
                        result['volumes_result'].append(volume_result)

                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()
        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='云硬盘大小超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info='云硬盘创建失败',
                    admin_info=str(e),
                    no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="磁盘创建失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.VolumeCreateWithOrderSerializer)
    @utils.param_info
    def volume_create_with_order(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        order_info = param_info.get("order_info")
        service_count = order_info.get('service_count', 0)
        region = order_info.get("region")
        volume_info = param_info.get("volume_info")
        name = volume_info.get("name")
        size = int(volume_info.get("size", 0))
        volume_type = volume_info.get("volume_type")

        try:
            if not self.volume_provider.check_pool(size, service_count, volume_type):
                return response_obj.json_exception_serial(user_info="配额不足，请联系管理员", admin_info=str("pool error"), no=500)

            project_id = request.session.get('project_id', request.COOKIES.get("project_id"))
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            check_result, volume_available_count, volume_available_size = self.volume_provider.check_volume_quota(
                openstack_client, size, service_count, project_id)
            if not check_result:
                user_info = "配额不足，您的剩余可用个数为%s, 剩余总大小为%s" % (volume_available_count, volume_available_size)
                return response_obj.json_exception_serial(user_info=user_info, admin_info="quota error", no=500)

        except Exception as e:
            return response_obj.json_exception_serial(user_info="创建云硬盘失败", admin_info=str(e), no=500)

        volume_id_list = []
        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)
                order_info["project"] = project_result

                # 创建订单
                result = {"volumes_result": []}
                if service_count == 1:
                    volume = self._create_openstack_volume(request, name, size, volume_type=volume_type)
                    volume_id_list.append(volume.id)
                    server_volume_dict = {
                        "order_id": order_info.get("id"),
                        "account_id": account_id,
                        "project_id": project_id,
                        "volume_type": volume_type,
                        "volume_id": volume.id,
                        "name": name,
                        "size": size,
                        "create_at": datetime.datetime.now(),
                        "is_measure_end": False,
                        "region": region,
                        "contract_number": order_info.get("contract_number"),
                        "first_create_at": datetime.datetime.now()
                    }
                    volume_result = service_model.BmServiceVolume.objects.create(**server_volume_dict)
                    result['volumes_result'].append(volume_result)
                else:
                    for count in range(service_count):
                        volume_name = name + '_' + str(count + 1)
                        volume = self._create_openstack_volume(request, volume_name, size, volume_type=volume_type)
                        volume_id_list.append(volume.id)
                        server_volume_dict = {
                            "order_id": order_info.get("id"),
                            "account_id": account_id,
                            "project_id": project_id,
                            "volume_type": volume_type,
                            "volume_id": volume.id,
                            "name": volume_name,
                            "size": size,
                            "create_at": datetime.datetime.now(),
                            "is_measure_end": False,
                            "region": region,
                            "contract_number": order_info.get("contract_number"),
                            "first_create_at": datetime.datetime.now()
                        }
                        volume_result = service_model.BmServiceVolume.objects.create(**server_volume_dict)
                        result['volumes_result'].append(volume_result)
        except Exception as ex:
            try:
                volume_delete_result_list = self._delete_openstack_volume(request=request,
                                                                          volume_id_list=volume_id_list)
            except Exception as ex:
                self.logger.error(
                    "volume {volume_id_list} delete error {error}".format(volume_id_list=volume_id_list, error=ex))
            return response_obj.json_exception_serial(user_info="云硬盘创建失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.VolumeAttachSerializer,
                         operation_description="磁盘挂载",
                         responses={200: response_serializers.FeedbackVolumeAttachResponsesSerializer},
                         )
    @utils.param_info
    def volume_attach(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        volume_id = param_info.get("volume_id")
        server_name = param_info.get("server_name")
        device = param_info.get("device")

        try:
            bm_service_volume = service_model.BmServiceVolume.objects.get(volume_id=volume_id, is_measure_end=False)

            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            volume_result = openstack_client.get_volume(name_or_id=volume_id)
            server_result = openstack_client.compute.get_server(server_id)
            if env_config.baremetal_tag in server_result.tags:
                result = baremetal_attach_volume(server_result, volume_result, openstack_client)
                # openstack_client.add_block_mapping(server_id, volume_id, result.get('path'))
                bm_service_volume.attached_type = "裸金属服务器"
            else:
                result = openstack_client.attach_volume(server=server_result, volume=volume_result, device=device)
                bm_service_volume.attached_type = "虚拟机"

            bm_service_volume.instance_uuid = server_id
            bm_service_volume.instance_name = server_name
            bm_service_volume.save()

            # 挂载成功，同步数据给CMDB
            cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=server_id, status=None)
            self.logger.info("CMDB the volume attach to server sys result: %s" % cmdb_result)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="磁盘挂载失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(bm_service_volume)

    @swagger_auto_schema(request_body=serializers.VolumeAttachSerializer,
                         operation_description="磁盘挂载",
                         responses={200: response_serializers.FeedbackVolumeAttachResponsesSerializer},
                         )
    @utils.param_info
    def feedback_volume_attach(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        server_id = param_info.get("server_id")
        volume_id = param_info.get("volume_id")
        server_name = param_info.get("server_name")
        try:
            bm_service_volume = service_model.BmServiceVolume.objects.get(volume_id=volume_id,
                                                                          is_measure_end=False)
            bm_service_volume.instance_uuid = server_id
            bm_service_volume.instance_name = server_name
            bm_service_volume.attached_type = "裸金属服务器"
            bm_service_volume.save()

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="磁盘挂载失败", admin_info=str(ex), no=300)
        return response_obj.json_serial(bm_service_volume)

    @swagger_auto_schema(request_body=serializers.VolumeAttachSerializer,
                         operation_description="卸载云硬盘",
                         responses={200: response_serializers.VolumeDetachResponsesSerializer})
    @check_element_permission
    @utils.param_info
    def volume_detach(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info
        server_id = param_info.get("server_id")
        volume_id = param_info.get("volume_id")
        try:
            machine = service_model.BmServiceMachine.objects.filter(uuid=server_id).first()
            if machine:
                if machine.status and machine.status != 'active':
                    return response_obj.json_exception_serial(
                        user_info="服务器操作系统未启动，请开机",
                        admin_info="server is down",
                        no=300)
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            bm_service_volume = self.volume_provider.detach_volume_from_server(openstack_client,
                                                                               volume_id, server_id)

            # 同步CMDB数据
            cmdb_result = self.cmdb_provider.cmdb_data_sys_put(instance_uuid=server_id, status=None)
            self.logger.info("CMDB the volume attach to server sys result: %s" % cmdb_result)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="磁盘卸载失败", admin_info=str(ex), no=300)
        return response_obj.json_serial("磁盘卸载成功")

    @swagger_auto_schema(
        operation_description="云硬盘列表",
        responses={200: response_serializers.VolumeListResponsesSerializer},
    )
    @utils.param_info
    def volume_list(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        project_id = request.session.get('project_id')
        result = []
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            volumes_object = openstack_client.list_volumes()
            volumes_result_dict = {}
            for volume_object in volumes_object:
                volumes_result_dict[volume_object.id] = {"status": volume_object.status,
                                                         "attachments": volume_object.attachments}
            bm_service_volume_ojbects = service_model.BmServiceVolume.objects.filter(
                project_id=project_id, is_measure_end=False, ).order_by('-create_at')
            for bm_service_volume in bm_service_volume_ojbects:
                if bm_service_volume.volume_id in volumes_result_dict:
                    service_volume = bm_service_volume.__dict__
                    contract_info = service_model.BmContract.objects.filter(
                        contract_number=bm_service_volume.contract_number,
                        status='active')
                    service_volume.update(volumes_result_dict[bm_service_volume.volume_id])
                    if contract_info:
                        service_volume['contract_info'] = contract_info.first().__dict__
                    else:
                        service_volume['contract_info'] = {}
                    result.append(service_volume)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取云硬盘列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(
        operation_description="未挂载云硬盘列表",
        responses={200: response_serializers.VolumeListResponsesSerializer},
    )
    @utils.param_info
    def volume_list_no_attached(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        project_id = request.session.get('project_id')
        result = []
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            volumes_object = openstack_client.list_volumes()
            volumes_result_dict = {}
            for volume_object in volumes_object:
                volumes_result_dict[volume_object.id] = {"status": volume_object.status,
                                                         "attachments": volume_object.attachments}
            #
            bm_service_volume_ojbects = service_model.BmServiceVolume.objects.filter(
                project_id=project_id, is_measure_end=False, instance_name__isnull=True).order_by('-create_at')
            for bm_service_volume in bm_service_volume_ojbects:
                if bm_service_volume.volume_id in volumes_result_dict:
                    service_volume = bm_service_volume.__dict__
                    contract_info = service_model.BmContract.objects.filter(
                        contract_number=bm_service_volume.contract_number,
                        status='active')
                    service_volume.update(volumes_result_dict[bm_service_volume.volume_id])
                    if contract_info:
                        service_volume['contract_info'] = contract_info.first().__dict__
                    else:
                        service_volume['contract_info'] = {}
                    result.append(service_volume)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取云硬盘列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.VolumeUpdateSerializer,
                         operation_description="更新云硬盘信息",
                         responses={200: response_serializers.VolumeUpdateResponsesSerializer},
                         )
    @check_element_permission
    @utils.param_info
    def volume_update(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        order_info = param_info.get("order_info")
        name = param_info.get("name")
        volume_id = param_info.get('volume_id')
        size = param_info.get("size")
        account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            with transaction.atomic():
                bm_service_volume = service_model.BmServiceVolume.objects.get(volume_id=volume_id,
                                                                              is_measure_end=False)
                if name:
                    volume = openstack_client.update_volume(volume_id, name=name)
                    bm_service_volume.update_at = datetime.datetime.now()
                    bm_service_volume.name = name
                    bm_service_volume.save()
                    self.logger.info("update volume by name,which is not measure ")

                if size:
                    bm_service_volume.is_measure_end = True
                    bm_service_volume.update_at = datetime.datetime.now()
                    bm_service_volume.save()

                    # 创建新的订单
                    origin_order_id = bm_service_volume.order_id
                    alter_order_obj = order_handler.create_new_order_for_alter(origin_order_id=origin_order_id,
                                                                               alter_order_info=order_info,
                                                                               account_id=account_id,
                                                                               service_count=1,
                                                                               product_type="云硬盘")
                    if not alter_order_obj.is_ok:
                        raise Exception(alter_order_obj.message)
                    order_result = alter_order_obj.content

                    self.logger.info("extend volume")
                    # openstack 创建
                    volume = volume_extend(openstack_client, volume_id, size)
                    self.logger.info("openstack extend volume result %s " % volume_id)

                    # 项目信息创建
                    bm_volume_dict = model_to_dict(bm_service_volume)
                    bm_volume_dict['size'] = size
                    bm_volume_dict['is_measure_end'] = False
                    bm_volume_dict['create_at'] = datetime.datetime.now()
                    bm_volume_dict['order_id'] = order_result.id
                    bm_volume_dict.pop('update_at')
                    bm_volume_dict.pop('id')
                    bm_volume_dict['account_id'] = account_id
                    bm_volume = service_model.BmServiceVolume.objects.create(**bm_volume_dict)
                    self.logger.info("extend volume create result %s" % bm_volume)

                    # 订单交付
                    order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                    order_result.create_at = datetime.datetime.now()
                    order_result.save()
        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='云硬盘大小超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info="更新云硬盘失败",
                    admin_info=str(e),
                    no=500
                )
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="更新云硬盘失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("success")

    @swagger_auto_schema(request_body=serializers.VolumeDeleteSerailizer,
                         operation_description="删除云硬盘",
                         responses={200: response_serializers.VolumeDeletedResponsesSerializer},
                         )
    @check_element_permission
    @utils.param_info
    def volume_delete(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        volume_ids = param_info.get("volume_ids")
        try:

            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            for volume_id in volume_ids:
                openstack_client.delete_volume(volume_id)
                bm_service_volume = service_model.BmServiceVolume.objects.get(volume_id=volume_id,
                                                                              is_measure_end=False)
                bm_service_volume.is_measure_end = True
                bm_service_volume.update_at = datetime.datetime.now()
                bm_service_volume.save()

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除云硬盘失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("删除磁盘成功")

    @swagger_auto_schema(request_body=serializers.VolumeRollBackSerailizer,
                         operation_description="云硬盘回滚，裸金属平台及openstack进行相关删除",
                         responses={200: response_serializers.VolumeDeletedResponsesSerializer})
    @utils.param_info
    def volume_roll_back(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        volume_id_list = param_info.get("volume_id_list")
        try:
            # openstack磁盘删除
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            open_volume_delete_result = {}
            for volume_id in volume_id_list:
                # 平台数据删除
                bm_service_volume = service_model.BmServiceVolume.objects.filter(volume_id=volume_id).delete()
                delete_result = openstack_client.delete_volume(volume_id)
                open_volume_delete_result[volume_id] = delete_result
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="云硬盘回滚失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("磁盘回滚成功")

    @swagger_auto_schema(request_body=serializers.VolumeBackCreateSerializer,
                         operation_description="创建云硬盘备份",
                         responses={200: response_serializers.VolumeBackupCreateResponsesSerializer})
    @check_element_permission
    @utils.param_info
    def volume_backup_create(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        order_info = param_info.get("order_info")
        service_count = order_info.get('service_count', 1)
        region = order_info.get("region")

        volume_id = param_info.get('volume_id')
        name = param_info.get("name")
        volume_name = param_info.get('volume_name')
        description = param_info.get("description")
        force = param_info.get("force", True)
        wait = param_info.get("wait", False)

        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)
                order_info["project"] = project_result

                # 创建订单
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)

                result = {"order_result": order_result, "volumes_result": {}}
                openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
                backup = openstack_client.create_volume_backup(volume_id, name=name, description=description,
                                                               force=force, wait=wait)

                backup_dict = {
                    "order_id": order_result.id,
                    "account_id": account_id,
                    "project_id": project_id,
                    "region": region,
                    "backup_id": backup.id,
                    "volume_id": volume_id,
                    "volume_name": volume_name,
                    "is_incremental": False,
                    "deleted": False,
                    "backup_name": name,
                    "contract_number": order_info.get("contract_number"),
                    "create_at": datetime.datetime.now(),
                }

                backup_result = service_model.BmServiceVolumeBackup.objects.create(**backup_dict)
                result['backup_result'] = backup_result.to_dict()
                result['backup_result']['status'] = 'creating'

                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()

        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='云硬盘备份超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info='备份云硬盘失败',
                    admin_info=str(e),
                    no=500
                )
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="备份云硬盘失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(
        operation_description="查看云硬盘备份",
        responses={200: response_serializers.VolumeBackupListResponsesSerializer},
    )
    @utils.param_info
    def volume_backup_list(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        project_id = request.session.get('project_id')

        result = []
        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            backup_objects = openstack_client.list_volume_backups(detailed=True)
            backup_result_dict = {}
            for b_object in backup_objects:
                backup_result_dict[b_object.id] = b_object.__dict__

            service_backup_objects = service_model.BmServiceVolumeBackup.objects.filter(project_id=project_id,
                                                                                        deleted=False).order_by(
                '-create_at')
            for service_bakcup in service_backup_objects:
                if service_bakcup.backup_id in backup_result_dict:
                    service_backup_dict = service_bakcup.to_dict()
                    contract_info = service_model.BmContract.objects.filter(
                        contract_number=service_bakcup.contract_number,
                        status='active')
                    service_backup_dict.update(backup_result_dict[service_bakcup.backup_id])
                    if contract_info:
                        service_backup_dict['contract_info'] = contract_info.first().__dict__
                    else:
                        service_backup_dict['contract_info'] = {}
                    result.append(service_backup_dict)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查看云硬盘备份失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.VolumeBackupDeleteSerializer,
                         operation_description="删除云硬盘备份",
                         responses={200: response_serializers.VolumeBackupDeletedResponsesSerializer},
                         )
    @check_element_permission
    @utils.param_info
    def volume_backup_delete(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        backup_ids = param_info.get('backup_ids')
        force = param_info.get('force', False)

        try:
            openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
            for backup_id in backup_ids:
                backup = openstack_client.delete_volume_backup(backup_id, force=force)
                bm_service_back_up = service_model.BmServiceVolumeBackup.objects.get(backup_id=backup_id)
                bm_service_back_up.is_measure_end = True
                bm_service_back_up.update_at = datetime.datetime.now()
                bm_service_back_up.save()
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除云硬盘备份失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("success")

    @swagger_auto_schema(request_body=serializers.VolumeBackupRestoreSerializer)
    @check_element_permission
    @utils.param_info
    def volume_backup_restore(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        order_info = param_info.get("order_info")
        backup_id = param_info.get('backup_id')
        volume_name = param_info.get('volume_name')

        try:
            with transaction.atomic():
                account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)
                order_info["project"] = project_result

                # 创建订单
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)
                result = {"order_result": order_result, "volumes_result": []}
                openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
                backup_object = openstack_client.get_volume_backup(backup_id)
                if not self.volume_provider.check_pool(backup_object.size, 1):
                    return response_obj.json_exception_serial(user_info="存储池资源不足，请联系管理员",
                                                              admin_info="pool error", no=500)
                backup = volume_backup_restore(openstack_client, backup_id, volume_id=None, volume_name=volume_name)
                volume = openstack_client.get_volume(backup.volume_id)
                service_volume_dict = {
                    "order_id": order_result.id,
                    "account_id": request.session.get('account_id'),
                    "project_id": request.session.get('project_id'),
                    "volume_id": backup.volume_id,
                    "volume_type": volume.volume_type,
                    "name": backup.volume_name,
                    "size": volume.size,
                    "create_at": datetime.datetime.now(),
                    "is_measure_end": False,
                    "region": order_result.region,
                    "contract_number": order_info.get("contract_number")
                }
                volume_result = service_model.BmServiceVolume.objects.create(**service_volume_dict)
                result["volumes_result"] = volume_result

                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()

        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='云硬盘大小超过配额，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info='磁盘创建失败',
                    admin_info=str(e),
                    no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info='恢复备份失败', admin_info=str(ex), no=500)
        return response_obj.json_serial(result)


class ObjectViews(viewsets.ViewSet):
    def __init__(self):
        super(ObjectViews, self).__init__()
        self.aes_cipher = AESCipher()

    @swagger_auto_schema(request_body=serializers.BucketCreateSerializer,
                         operation_description="创建桶",
                         responses={200: response_serializers.CreatedBucketResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def create_bucket(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info

        metadata = {}
        order_info = param_info.get("order_info")
        container_name = param_info.get('container_name')
        is_public = param_info.get('is_public', False)
        metadata['is_public'] = is_public

        try:
            with transaction.atomic():
                project = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project)
                order_info["project"] = project_result

                # 创建订单
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    raise Exception(order_result)
                result = {"order_result": order_result, "object_store": []}
                object_client = swift_handler.ObjectClientProvider(request)
                bucket = object_client.swift_create_container(container_name, metadata)
                result['object_store'].append(bucket.to_dict())
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()
        except exc.ContainserAlreadyExists as e:
            return response_obj.json_exception_serial(user_info='桶%s已经存在' % container_name, admin_info=str(e), no=500)
        except Exception as e:
            return response_obj.json_exception_serial(user_info='创建桶失败', admin_info=str(e), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.BucketDeleteSerializer,
                         operation_description="删除桶",
                         responses={200: response_serializers.DeleteBucketResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def delete_bucket(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        buckets = param_info.get('buckets')
        try:
            object_client = swift_handler.ObjectClientProvider(request)
            for bucket in buckets:
                bucket_head = object_client.swift_client.head_container(bucket)
                if int(bucket_head.get('x-container-object-count')) > 0:
                    return response_obj.json_exception_serial(user_info='桶不为空，不能删除', admin_info='can not delete',
                                                              no=500)
            for bucket in buckets:
                object_client.swift_delete_container(container_name=bucket)
        except Exception as e:
            return response_obj.json_exception_serial(user_info='删除桶失败', admin_info=str(e), no=500)
        return response_obj.json_serial("删除桶成功")

    @swagger_auto_schema(
        operation_description="桶列表",
        responses={200: response_serializers.BucketListResponsesSerializer}
    )
    @check_element_permission
    @utils.param_info
    def list_bucket(self, request):
        response_obj = ResponseObj()
        try:
            object_client = swift_handler.ObjectClientProvider(request)
            object_stores = object_client.swift_get_containers()
            buckets = [store.to_dict() for store in object_stores]
        except Exception as e:
            return response_obj.json_exception_serial(user_info='获取桶失败', admin_info=str(e), no=500)
        return response_obj.json_serial(buckets)

    @swagger_auto_schema(query_serializer=serializers.BucketShowSerializer,
                         operation_description="获取桶信息"
                         )
    @check_element_permission
    @utils.param_info
    def show_bucket(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        container_name = param_info.get('container_name')

        result = {}
        try:
            object_client = swift_handler.ObjectClientProvider(request)
            bucket = object_client.swift_get_container(container_name=container_name)

            objects = object_client.swift_get_objects(container_name)

            result.update(bucket.to_dict())
            result['objects'] = objects
        except Exception as e:
            return response_obj.json_exception_serial(user_info='获取桶失败', admin_info=str(e), no=500)
        return response_obj.json_serial(result)

    # @swagger_auto_schema(query_serializer=serializers.BucketShowSerializer,
    #                      operation_description="获取桶信息"
    #                      )
    # @utils.param_info
    def show_bucket_restful(self, request, pk):
        response_obj = ResponseObj()
        # param_info = request.param_info
        container_name = pk
        result = {}
        try:
            object_client = swift_handler.ObjectClientProvider(request)
            bucket = object_client.swift_get_container(container_name=container_name)

            objects = object_client.swift_get_objects(container_name)

            result.update(bucket.to_dict())
            result['objects'] = objects
        except Exception as e:
            return response_obj.json_exception_serial(user_info='获取桶失败', admin_info=str(e), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.BucketUpdateSeraializer,
                         operation_description="更新桶信息",
                         responses={200: response_serializers.UpdateBucketResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def update_bucket(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        container_name = param_info.get('container_name')
        is_public = param_info.get('is_public', False)
        metadata = {"is_public": param_info.get('is_public')}

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            bucket = object_client.swift_update_container(container_name, metadata=metadata)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="更新桶失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(bucket.to_dict())

    @swagger_auto_schema(request_body=serializers.BucketCreateDirSerializer,
                         operation_description="创建目录",
                         responses={200: response_serializers.CreatedDirResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def create_dir(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        container_name = param_info.get('container_name')
        pseudo_floder_name = param_info.get('floder_name')

        if pseudo_floder_name[:-1] != '/':
            pseudo_floder_name += '/'

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            floder_object = object_client.swift_create_pseudo_folder(container_name, pseudo_floder_name)
        except exc.ObjectAlreadyExist as ex:
            return response_obj.json_exception_serial(user_info='目录已经存在', admin_info=str(ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="创建目录失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(floder_object.to_dict())

    @swagger_auto_schema(request_body=serializers.BucketDeleteObjectSerializer,
                         operation_description="删除对象",
                         responses={200: response_serializers.DeleteObjectsResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def delete_object(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        container_name = param_info.get('container_name')
        object_names = param_info.get('object_names')

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            sorted_objects = sorted(object_names, key=lambda object: object[-1], reverse=True)

            for object_name in sorted_objects:
                if object_name[-1] == '/':
                    object_client.swift_delete_folder(container_name, object_name)
                else:
                    object_client.swift_delete_object(container_name, object_name)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info='删除对象失败', admin_info=str(ex), no=500)
        return response_obj.json_serial("删除对象成功")

    @swagger_auto_schema(query_serializer=serializers.BucketShowObjectSerializer,
                         operation_description="获取对象信息")
    @check_element_permission
    @utils.param_info
    def show_object(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        container_name = param_info.get('container_name')
        object_name = param_info.get('object_name')

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            object_metadata = object_client.swift_get_object(container_name, object_name, with_data=False)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查看对象失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(object_metadata)

    # @swagger_auto_schema(query_serializer=serializers.BucketShowObjectSerializer,
    #                      operation_description="获取对象信息")
    # @utils.param_info
    def show_object_rest(self, request, pk_container_name, pk_object_name):
        response_obj = ResponseObj()
        # param_info = request.param_info
        container_name = pk_container_name
        object_name = pk_object_name

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            object_metadata = object_client.swift_get_object(container_name, object_name, with_data=False)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查看对象失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(object_metadata)

    @swagger_auto_schema(query_serializer=serializers.BucketShowObjectSerializer,
                         operation_description="下载文件",
                         )
    @check_element_permission
    @utils.param_info
    def download_file(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info

        container_name = param_info.get('container_name')
        object_name = param_info.get('object_name')

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            obj = object_client.swift_get_object(container_name, object_name, with_data=True)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查看对象失败", admin_info=str(ex), no=500)
        filename = object_name.rsplit(swift_handler.FOLDER_DELIMITER)[-1]
        if not os.path.splitext(obj.name)[1] and obj.orig_name:
            name, ext = os.path.splitext(obj.orig_name)
            filename = "%s%s" % (filename, ext)
        response = StreamingHttpResponse(obj.data)
        safe = filename.replace(",", "")

        response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(safe))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Length'] = obj.bytes
        return response

    def download_file_rest(self, request, pk_container_name, pk_object_name):
        response_obj = ResponseObj()
        container_name = pk_container_name
        object_name = pk_object_name

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            obj = object_client.swift_get_object(container_name, object_name, with_data=True)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查看对象失败", admin_info=str(ex), no=500)
        filename = object_name.rsplit(swift_handler.FOLDER_DELIMITER)[-1]
        if not os.path.splitext(obj.name)[1] and obj.orig_name:
            name, ext = os.path.splitext(obj.orig_name)
            filename = "%s%s" % (filename, ext)
        response = StreamingHttpResponse(obj.data)
        safe = filename.replace(",", "")

        response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(safe))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Length'] = obj.bytes
        return response

    @swagger_auto_schema(query_serializer=serializers.BucketShowSerializer,
                         operation_description="对象存储列表",
                         responses={200: response_serializers.ObjectsListResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def list_objects(self, request, ):
        response_obj = ResponseObj()
        param_info = request.param_info
        container_name = param_info.get('container_name')
        path = param_info.get('path')

        result = {}
        try:
            object_client = swift_handler.ObjectClientProvider(request)
            # bucket = object_client.swift_get_container(container_name=container_name)
            if path is not None:
                path = urlunquote(path)
            objects = object_client.swift_get_objects(container_name, prefix=path, path=path)
            # result.update(bucket.to_dict())
            result['objects'] = objects
        except Exception as e:
            return response_obj.json_exception_serial(user_info='获取桶失败', admin_info=str(e), no=500)
        return response_obj.json_serial(result)

    # @swagger_auto_schema(manual_parameters=serializers.BucketUploadOjbectSerializer)
    @swagger_auto_schema(
        operation_description="上传文件",
        request_body=serializers.ObjectFileUploadSerializer,
        responses={200: response_serializers.UploadFileResponsesSerializer}
    )
    @check_element_permission
    def upload_file(self, request):
        response_obj = ResponseObj()

        container_name = request.data.get('container_name')
        object_name = request.data.get('object_name')

        form = UploadObjectForm(request.POST, request.FILES)
        if not form.is_valid():
            return response_obj.json_exception_serial(user_info="请求参数错误", admin_info='Invalid request', no=500)
        data = form.clean()

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            result = object_client.swift_upload_object(container_name, object_name, data['file'])
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="上传失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(query_serializer=serializers.BucketShowObjectSerializer)
    @check_element_permission
    @utils.param_info
    def generate_url(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info

        container_name = param_info.get('container_name')
        object_name = param_info.get('object_name')

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            container = object_client.swift_get_container(container_name)
            if not container.is_public:
                return response_obj.json_exception_serial(user_info='请检查桶权限,非公有的无法生成url')

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="生成url失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(container)

    @swagger_auto_schema(request_body=serializers.BucketCopyObjectSerializer,
                         operation_description="复制对象存储（暂时没有这个功能）",
                         # responses={200: response_serializers.CopyObjectResponsesSerializer}
                         )
    @check_element_permission
    @utils.param_info
    def copy_object(self, request):
        response_obj = ResponseObj()

        param_info = request.param_info

        src_container_name = param_info.get('src_container_name')
        src_object_name = param_info.get('src_object_name')

        dst_container_name = param_info.get('dst_container_name')
        dst_object_name = param_info.get('dst_object_name')

        try:
            object_client = swift_handler.ObjectClientProvider(request)
            result = object_client.swift_copy_object(src_container_name, src_object_name,
                                                     dst_container_name, dst_object_name)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="复制对象存储失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)


class BaremetalMaterialViews(viewsets.ViewSet):
    def __init__(self):
        super(BaremetalMaterialViews, self).__init__()
        self.aes_cipher = AESCipher()
        self.bm_material_provider = BmMaterialProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="根据时间范围查询所有合同下云硬盘信息",
                         responses={200: response_serializers.MaterialVolumeResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def material_volume_contract_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.contract_volume_seasonal(
                start_date=start_date, end_date=end_date)
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料Volume信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="按照周期查询云硬盘备份信息",
                         responses={200: response_serializers.MaterialVolumeBakResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def material_volume_bak_contract_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            # contract_number = request.param_info.get('contract_number', "")
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.contract_volume_bak_seasonal(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料Volume信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="根据时间范围查询物料machine信息",
                         responses={200: response_serializers.MaterialMachineResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def material_machine_contract_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.contract_machine_seasonal(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料machine信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.FloatingIPCalculaterInRangeSerializer,
                         operation_description="统计某一时间范围中弹性公网IP的资源信息",
                         responses={200: response_serializers.MaterialIpInRangeResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def material_ip_calculate_in_range(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")

            # 条件查询
            param_dict = dict()
            if request.param_info.get('project_id', None):
                param_dict["project_id"] = request.param_info.get('project_id', None)
            if request.param_info.get('account_id', None):
                param_dict["account_id"] = request.param_info.get('account_id', None)
            if request.param_info.get('contract_number', None):
                param_dict["contract_number"] = request.param_info.get('contract_number', None)

            response_obj = self.bm_material_provider.material_ip_calculate_in_range(
                start_date=start_date, end_date=end_date, param_dict=param_dict)
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料IP信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="统计某一时间范围中弹性公网IP的资源信息",
                         responses={200: response_serializers.MaterialIpInRangeResponsesSerializer}
                         )
    @auth_utils.param_info_decrypt
    def material_ip_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.material_ip_seasonal(
                start_date=start_date, end_date=end_date)
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料IP信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="按照周期查询NAT信息"
                         )
    @auth_utils.param_info_decrypt
    def material_nat_contract_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            # contract_number = request.param_info.get('contract_number', "")
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.contract_nat_seasonal(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料NAT信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="按照周期查询LB物料信息"
                         )
    @auth_utils.param_info_decrypt
    def material_lb_contract_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.contract_lb_seasonal(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料NAT信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="按照周期查询共享带宽物料信息"
                         )
    @auth_utils.param_info_decrypt
    def material_share_band_seasonal(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.material_share_band_seasonal(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料共享带宽信息查询失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="将物料信息导入到数据库表当中"
                         )
    @auth_utils.param_info_decrypt
    def material_into_mysql(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.material_into_mysql(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料导出失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(query_serializer=serializers.ContarctVolumeSeasonalSerializer,
                         operation_description="从数据表中导出一个周期的数据"
                         )
    @auth_utils.param_info_decrypt
    def get_material_from_mysql(self, request):
        response_obj = ResponseObj()
        try:
            start_date = request.param_info.get('start_date', "")
            end_date = request.param_info.get('end_date', "")
            response_obj = self.bm_material_provider.get_material_from_mysql(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "物料导出失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")


class LoadBalanceRestfulViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()

    @staticmethod
    def check_shared_bandwidth_quota(project_id, shared_bandwidth_id, service_floating_ip_count):
        fip_used_count = service_model.BmServiceFloatingIp.objects.filter(project_id=project_id,
                                                                          is_measure_end=False,
                                                                          qos_policy_id=shared_bandwidth_id).count()
        bandwidth_fip_quota_info = service_model.ShareBandWidthQuota.objects.filter(project_id=project_id).first()
        bandwidth_fip_quota_count = bandwidth_fip_quota_info.floating_ip_count \
            if bandwidth_fip_quota_info else DEFAULT_BANDWIDTH_FLOATINGIP_COUNT

        if fip_used_count + service_floating_ip_count > bandwidth_fip_quota_count:
            return False
        return True

    def create_loadbalance_order(self, request, order_info, loadbalance_info, is_new_ip):
        openstack_client = utils.get_openstack_client(request)
        account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        project_result = auth_models.BmProject.objects.filter(id=project_id).first()
        if not project_result:
            raise Exception("project id %s 对项目不存在" % project_id)
        order_info["project"] = project_result
        try:
            with transaction.atomic():
                # 创建订单
                order_result = service_model.BmServiceOrder.objects.create(**order_info)

                if not order_result:
                    raise Exception(order_result)

                result = {"order_result": order_result}
                # 判断vip_network_id是否存在
                networks = openstack_client.list_networks(filters={'id': loadbalance_info.get("vip_network_id")})
                if not networks:
                    load_balancer = {
                        "admin_info": "vip_network_id:{vip_network_id}不存在".format(
                            vip_network_id=loadbalance_info.get("vip_network_id")),
                        "user_info": "vip_network_id:{vip_network_id}不存在".format(
                            vip_network_id=loadbalance_info.get("vip_network_id")),
                        "no": 404
                    }
                    return load_balancer
                # 创建负载均衡器
                load_balancer = handler.create_load_balancers(request, project_id=project_id,
                                                              vip_network_id=loadbalance_info.get("vip_network_id"),
                                                              name=loadbalance_info.get("name"))
                try:
                    server_loadbalance_dict = {
                        "order_id": order_result.id,
                        "account_id": account_id,
                        "project_id": project_id,
                        "created_at": datetime.datetime.now(),
                        "is_measure_end": False,
                        "deleted": False,
                        "is_new_ip": is_new_ip,
                        "region": order_info.get("region"),
                        "loadbalance_id": load_balancer["id"],
                        "loadbalance_name": load_balancer["name"],
                        "location": loadbalance_info.get("location"),
                        "is_public": loadbalance_info.get("is_public"),
                        "network_name": loadbalance_info.get("network_name"),
                        "vip_network_id": loadbalance_info.get("vip_network_id"),
                        "vpc_id": loadbalance_info.get("vpc_id"),
                        "listener_count": loadbalance_info.get("listener_count", 0),
                        "pool_count": loadbalance_info.get("pool_count", 0),
                        "flavor_id": loadbalance_info.get("flavor_id"),
                        "contract_number": order_info.get("contract_number"),
                        "first_create_at": datetime.datetime.now()
                    }
                    loadbalance_result = service_model.BmServiceLoadbalance.objects.create(**server_loadbalance_dict)
                    if not loadbalance_result:
                        raise Exception(loadbalance_result)
                    result['loadbalance_result'] = loadbalance_result
                    load_balancer["admin_info"] = True
                except Exception as back_ex:
                    raise Exception(str(back_ex))
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()
        except Exception as ex:
            if ex.status_code == 403:
                load_balancer = {
                    "admin_info": "当前项目配额已满",
                    "user_info": "当前项目配额已满",
                    "no": 403
                }
            else:
                load_balancer = {
                    "admin_info": str(ex),
                    "user_info": "负载均衡创建失败！！！",
                    "no": 500
                }
            return load_balancer
        return load_balancer

    def create_public_ip(self, request, order_info, floating_ip_info, firewall_id, loadbalance_id):
        # 公网类型的对弹性公网IP的创建和收费
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        response_obj = ResponseObj()
        available_count = 0
        account_id = request.session.get('account_id', request.COOKIES.get("account_id"))
        project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
        project_result = auth_models.BmProject.objects.filter(id=project_id).first()
        if not project_result:
            raise Exception("project id %s 对项目不存在" % project_id)
        order_info["project"] = project_result
        try:
            with transaction.atomic():
                # 创建订单
                self.logger.info("create order to floating ip :")
                order_info["project"] = project_result
                order_info["delivery_status"] = service_model.ORDER_STATUS_DELIVERING

                self.logger.info("create order param : %s" % order_info)
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    self.logger.error("create order result %s " % order_result)
                    raise Exception(order_result)
                self.logger.info("create order result : %s" % order_result)

                result = {"order_result": order_result, "floating_ip_list_result": []}
                # 获取qos policy id
                qos_policy_name = floating_ip_info.get("qos_policy_name")
                qos_policy_obj = self.service_provider.get_qos_policy_info(qos_policy_name=qos_policy_name)
                if not qos_policy_obj.is_ok:
                    self.logger.error("fail to get qos policy info %s" % qos_policy_obj.message)
                    raise Exception(qos_policy_obj.message)
                qos_policy_id = qos_policy_obj.content.id

                # 创建弹性 IP
                region = order_info.get("region", request.session.get("region"))
                external_line_type = floating_ip_info.get("external_line_type")
                external_region_network = env_config.external_networks.get(region)
                if not external_region_network:
                    self.logger.error("Fail to find external network info in region %s" % region)
                    raise Exception("Fail to find external network info in region %s" % region)
                external_network_list = external_region_network.get(external_line_type)
                if not external_network_list:
                    self.logger.error(
                        "Fail to find external network info in network type  %s" % external_line_type)
                    raise Exception(
                        "Fail to find external network info in network type  %s" % external_line_type)
                external_network = external_network_list[0]
                external_name = external_network.get("network_name")
                external_name_id = external_network.get("network_id")
                check_result, available_count = self.service_floatingip_provider.check_fip_quota(
                    openstack_client, order_info.get("service_count", 0), project_id)

                if not check_result:
                    raise exc.QuotaError(count=available_count)

                if not self.service_floatingip_provider.check_fip_pools(order_info.get("service_count", 0),
                                                                        external_name_id):
                    raise exc.PoolResourceError()

                for count in range(order_info.get("service_count", 0)):

                    ip_create_result = openstack_client.network.create_ip(
                        **{"floating_network_id": external_name_id, "qos_policy_id": qos_policy_id}
                    ).to_dict()
                    if not ip_create_result:
                        self.logger.error("fail to create ip  %s" % ip_create_result)
                        raise Exception(ip_create_result)
                    try:
                        # 通过弹性IP 创建平台数据
                        service_floating_ip_dict = {
                            "order_id": order_result.id,
                            "account_id": account_id,
                            "project_id": project_id,
                            "contract_number": order_result.contract_number,
                            "external_line_type": external_line_type,
                            "external_name": external_name,
                            "external_name_id": external_name_id,
                            "floating_ip_id": ip_create_result['id'],
                            "floating_ip": ip_create_result["floating_ip_address"],
                            "qos_policy_id": qos_policy_id,
                            "qos_policy_name": qos_policy_name,
                            "create_at": datetime.datetime.now(),
                            "first_create_at": datetime.datetime.now(),
                            "status": "active",
                            "is_measure_end": False
                        }
                        # 合同号信息
                        floating_ip_result = service_model.BmServiceFloatingIp.objects.create(
                            **service_floating_ip_dict)
                        if not floating_ip_result:
                            raise Exception(floating_ip_result)
                        service_floating_ip_dict["admin_info"] = True
                        floating_ip_firewall_mapping = service_model.BmFloatingipfirewallMapping.objects.create(
                            floating_ip_id=floating_ip_result.floating_ip_id,
                            floating_ip=floating_ip_result.floating_ip,
                            firewall_id=firewall_id)
                        firewall, firewall_rules = handler.get_firewall_rule(firewall_id)
                        associate_firewall.delay(floating_ip_result.floating_ip, firewall, firewall_rules)

                        floating_ip_result.firewall_info = {"firewall_name": firewall.get('name'),
                                                            "firewall_id": firewall.get('id')}
                        result["floating_ip_list_result"].append(floating_ip_result)
                    except Exception as back_ex:
                        # 若数据创建失败则删除对应的IP
                        openstack_client.network.delete_ip(floating_ip=ip_create_result.id)
                        raise Exception(str(back_ex))
                # 订单更新
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()
        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                return response_obj.json_exception_serial(
                    user_info='配额不足，请联系管理员',
                    admin_info=str(e),
                    no=413)
            else:
                return response_obj.json_exception_serial(
                    user_info="弹性公网ip创建失败",
                    admin_info=str(e),
                    no=500
                )
        except exc.QuotaError as ex:
            openstack_client.load_balancer.delete_load_balancer(loadbalance_id)
            return response_obj.json_exception_serial(user_info="配额不足, 您的剩余可用个数为 %s" % available_count,
                                                      admin_info=str(ex),
                                                      no=300)
        except exc.PoolResourceError as ex:
            return response_obj.json_exception_serial(user_info="配额不足，请联系管理员",
                                                      admin_info=str(ex),
                                                      no=300)

        except Exception as ex:
            floating_ip = {
                "admin_info": str(ex)
            }
            return floating_ip

        return service_floating_ip_dict

    def floating_ip_create(self, request, order_info, floating_ip_info, firewall_id):
        available_count = 0
        try:
            with transaction.atomic():
                account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                project_result = auth_models.BmProject.objects.filter(id=project_id).first()
                if not project_result:
                    raise Exception("project id %s 对项目不存在" % project_id)

                # 创建订单
                self.logger.info("create order to floating ip :")
                order_info["project"] = project_result
                order_info["delivery_status"] = service_model.ORDER_STATUS_DELIVERING

                self.logger.info("create order param : %s" % order_info)
                order_result = service_model.BmServiceOrder.objects.create(**order_info)
                if not order_result:
                    self.logger.error("create order result %s " % order_result)
                    raise Exception(order_result)
                self.logger.info("create order result : %s" % order_result)

                result = {"order_result": order_result, "floating_ip_list_result": []}
                # 获取qos policy id
                shared_qos_policy_type = floating_ip_info.get("shared_qos_policy_type", False)
                if not shared_qos_policy_type:
                    qos_policy_name = floating_ip_info.get("qos_policy_name")
                    qos_policy_obj = self.service_provider.get_qos_policy_info(qos_policy_name=qos_policy_name)
                    if not qos_policy_obj.is_ok:
                        self.logger.error("fail to get qos policy info %s" % qos_policy_obj.message)
                        raise Exception(qos_policy_obj.message)
                    qos_policy_id = qos_policy_obj.content.id
                else:

                    qos_policy_id = floating_ip_info.get('qos_policy_id')
                    if not qos_policy_id:
                        raise Exception("qos_policy_id is None")
                    shared_bandwidth_info = service_model.BmShareBandWidth.objects.filter(
                        shared_bandwidth_id=qos_policy_id, is_measure_end=False).first()
                    if not shared_bandwidth_info:
                        floating_ip = {
                            "admin_info": "bandwidth not found",
                            "user_info": "该共享带宽不存在！！",
                            "no": 404
                        }
                        return floating_ip
                    if not self.check_shared_bandwidth_quota(project_id, qos_policy_id,
                                                             order_info.get("service_count", 0)):
                        user_info = "该共享带宽可绑定弹性公网ip超过上限"
                        admin_info = "quota error"
                        floating_ip = {
                            "admin_info": admin_info,
                            "user_info": user_info,
                            "no": 500
                        }
                        return floating_ip
                    qos_policy_name = shared_bandwidth_info.name

                # 创建弹性 IP
                region = order_info.get("region", request.session.get("region"))
                external_line_type = floating_ip_info.get("external_line_type")
                external_region_network = env_config.external_networks.get(region)
                if not external_region_network:
                    self.logger.error("Fail to find external network info in region %s" % region)
                    raise Exception("Fail to find external network info in region %s" % region)
                external_network_list = external_region_network.get(external_line_type)
                if not external_network_list:
                    self.logger.error("Fail to find external network info in network type  %s" % external_line_type)
                    raise Exception("Fail to find external network info in network type  %s" % external_line_type)
                external_network = external_network_list[0]
                external_name = external_network.get("network_name")
                external_name_id = external_network.get("network_id")

                openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
                check_result, available_count = self.service_floatingip_provider.check_fip_quota(
                    openstack_client, order_info.get("service_count", 0), project_id)

                if not check_result:
                    raise exc.QuotaError(count=available_count)

                if not self.service_floatingip_provider.check_fip_pools(order_info.get("service_count", 0),
                                                                        external_name_id):
                    raise exc.PoolResourceError()

                for count in range(order_info.get("service_count", 0)):
                    if not shared_qos_policy_type:
                        ip_create_result = openstack_client.network.create_ip(
                            **{"floating_network_id": external_name_id, "qos_policy_id": qos_policy_id}
                        )
                        if not ip_create_result:
                            self.logger.error("fail to create ip  %s" % ip_create_result)
                            raise Exception(ip_create_result)
                    else:
                        ip_create_result = openstack_client.network.create_ip(
                            **{"floating_network_id": external_name_id}
                        )
                        if not ip_create_result:
                            self.logger.error("fail to create ip  %s" % ip_create_result)
                            raise Exception(ip_create_result)

                    # 通过弹性IP 创建平台数据
                    service_floating_ip_dict = {
                        "order_id": order_result.id,
                        "account_id": account_id,
                        "project_id": project_id,
                        "contract_number": order_result.contract_number,
                        "external_line_type": external_line_type,
                        "external_name": external_name,
                        "external_name_id": external_name_id,
                        "floating_ip_id": ip_create_result.id,
                        "floating_ip": ip_create_result.floating_ip_address,
                        "qos_policy_id": qos_policy_id,
                        "qos_policy_name": qos_policy_name,
                        "create_at": datetime.datetime.now(),
                        "first_create_at": datetime.datetime.now(),
                        "status": "active",
                        "is_measure_end": False,
                        "shared_qos_policy_type": shared_qos_policy_type
                    }
                    # 合同号信息
                    floating_ip_result = service_model.BmServiceFloatingIp.objects.create(
                        **service_floating_ip_dict)
                    if not floating_ip_result:
                        raise Exception(floating_ip_result)
                    service_floating_ip_dict["admin_info"] = True
                    floating_ip_firewall_mapping = service_model.BmFloatingipfirewallMapping.objects.create(
                        floating_ip_id=floating_ip_result.floating_ip_id,
                        floating_ip=floating_ip_result.floating_ip,
                        firewall_id=firewall_id)
                    firewall, firewall_rules = handler.get_firewall_rule(firewall_id)
                    if shared_qos_policy_type:
                        traffic_shaper = qos_policy_id
                    else:
                        traffic_shaper = None
                    associate_firewall.delay(floating_ip_result.floating_ip, firewall, firewall_rules,
                                             traffic_shaper=traffic_shaper)

                    floating_ip_result.firewall_info = {"firewall_name": firewall.get('name'),
                                                        "firewall_id": firewall.get('id')}
                    result["floating_ip_list_result"].append(floating_ip_result)

                # 订单更新
                order_result.delivery_status = service_model.ORDER_STATUS_DELIVERED
                order_result.create_at = datetime.datetime.now()
                order_result.save()

        except openstack_exception.HttpException as e:
            if 'Quota' in e.details or 'quota' in e.details:
                floating_ip = {
                    "admin_info": str(e),
                    "user_info": '配额不足，请联系管理员',
                    "no": 413
                }
                return floating_ip
            else:
                floating_ip = {
                    "admin_info": str(e),
                    "user_info": '弹性公网ip创建失败',
                    "no": 500
                }
                return floating_ip

        except exc.QuotaError as ex:
            floating_ip = {
                "admin_info": str(ex),
                "user_info": "配额不足, 您的剩余可用个数为 %s" % available_count,
                "no": 300
            }
            return floating_ip

        except exc.PoolResourceError as ex:
            floating_ip = {
                "admin_info": str(ex),
                "user_info": "配额不足，请联系管理员",
                "no": 300
            }
            return floating_ip
        except Exception as ex:
            floating_ip = {
                "admin_info": str(ex),
                "user_info": '弹性公网ip创建失败',
                "no": 500
            }
            return floating_ip
        return service_floating_ip_dict

    def lb_attach_floating_ip(self, request, public_ip_id=None,
                              vip_port_id=None, fixed_address=None, loadbalance_id=None, loadbalance_name=None,
                              load_balancer_status=None):
        openstack_client = utils.get_openstack_client(request)
        with transaction.atomic():
            try:
                # 弹性IP挂载
                # openstack进行弹性IP挂载
                if load_balancer_status == service_model.LB_ERROR:
                    raise exc.LbError()
                openstack_client.network.update_ip(public_ip_id, port_id=vip_port_id,
                                                   fixed_ip_address=fixed_address)
                # 平台保存相关挂载数据信息
                service_attach_obj = service_model.BmServiceFloatingIp.objects.filter(floating_ip_id=public_ip_id,
                                                                                      is_measure_end=False,
                                                                                      attached=False)
                if service_attach_obj:
                    service_attach_objs = service_model.BmServiceFloatingIp.objects.get(
                        floating_ip_id=public_ip_id,
                        is_measure_end=False)
                    service_attach_objs.attached_type = service_model.FLOATINGIP_AATTACH_SLB
                    service_attach_objs.attached = True
                    service_attach_objs.instance_uuid = loadbalance_id
                    service_attach_objs.instance_name = loadbalance_name
                    service_attach_objs.fixed_address = fixed_address
                    service_attach_objs.save()
                    self.logger.info("openstack attach ip to server result: %s" % service_attach_obj)
            except Exception as ex:
                attach_type = {
                    "admin_info": str(ex),
                    "user_info": '弹性公网ip挂载负载均衡失败',
                    "no": 500
                }
                return attach_type
            return {"admin_info": True}

    @swagger_auto_schema(operation_description="获取用户当前项目下的负载均衡器列表")
    @utils.param_info
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances = handler.load_balance_list(request, project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取项目下的负载均衡器列表失败", admin_info=str(ex), no=500)
        return load_balances

    @swagger_auto_schema(request_body=serializers.CreateLoadBalancersSerializer,
                         responses={200: response_serializers.CreateLoadBalancersResponsesSerializer},
                         operation_description="创建新的负载均衡器")
    @utils.param_info
    def create(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        floating_ip_order_info = param_info.get("floating_ip_order_info")
        loadbalance_order_info = param_info.get("loadbalance_order_info")
        floating_ip_info = request.param_info.get("floating_ip_info")
        firewall_id = request.param_info.get('firewall_id')
        is_public = param_info.get("is_public")
        is_new_ip = param_info.get("is_new_ip")
        public_ip_id = param_info.get("public_ip_id")
        openstack_client = utils.get_openstack_client(request)
        try:
            # 创建负载均衡器
            loadbalance_result = self.create_loadbalance_order(request, loadbalance_order_info, param_info, is_new_ip)
            if loadbalance_result["admin_info"] != True:
                return response_obj.json_exception_serial(user_info=loadbalance_result["user_info"],
                                                          admin_info=loadbalance_result["admin_info"],
                                                          no=loadbalance_result["no"])
            loadbalance_sql_result = service_model.BmServiceLoadbalance.objects.filter(
                loadbalance_id=loadbalance_result["id"]).first()
            if is_public:
                loadbalance_name = loadbalance_result["name"]
                loadbalance_id = loadbalance_result["id"]
                vip_port_id = loadbalance_result["vip_port_id"]
                fixed_address = loadbalance_result["vip_address"]
                if is_new_ip:
                    # 创建弹性公网IP
                    ip_result = self.floating_ip_create(request, floating_ip_order_info, floating_ip_info, firewall_id)
                    if ip_result["admin_info"] != True:
                        loadbalance_sql_result.error_type = "IP_CREATE_ERROR"
                        loadbalance_sql_result.save()
                        return response_obj.json_exception_serial(user_info=ip_result["user_info"],
                                                                  admin_info=ip_result["admin_info"],
                                                                  no=ip_result["no"])
                    public_ip_id = ip_result["floating_ip_id"]

                # 负载均衡器绑定弹性公网IP操作
                # 判断当前IP是否存在
                floating_ip_obj = openstack_client.network.get_ip(public_ip_id)
                if not floating_ip_obj:
                    raise Exception(
                        "Fail to find floating IP by id {floating_ip_id}".format(
                            floating_ip_id=public_ip_id))
                load_balancer_status = loadbalance_result["provisioning_status"]
                attach_ip_result = self.lb_attach_floating_ip(request, public_ip_id=public_ip_id,
                                                              vip_port_id=vip_port_id, fixed_address=fixed_address,
                                                              loadbalance_id=loadbalance_id,
                                                              loadbalance_name=loadbalance_name,
                                                              load_balancer_status=load_balancer_status)
                if attach_ip_result["admin_info"] != True:
                    loadbalance_sql_result.error_type = "ATTACH_IP_ERROR"
                    loadbalance_sql_result.save()
                    return response_obj.json_exception_serial(user_info=attach_ip_result["user_info"],
                                                              admin_info=attach_ip_result["admin_info"],
                                                              no=attach_ip_result["no"])
            loadbalance_result_obj = service_model.BmServiceLoadbalance.objects.get(
                loadbalance_id=loadbalance_result["id"])
            result = {
                "loadbalance_info": loadbalance_result_obj,
                "floating_ip_order_info": floating_ip_order_info,
                "loadbalance_order_info": loadbalance_order_info
            }
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="创建新的负载均衡器失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result)

    @swagger_auto_schema(request_body=serializers.UpdateLoadBalancersSerializer,
                         operation_description="更新负载均衡器")
    def update(self, request, loadbalancer_id=None):
        response_obj = ResponseObj()
        name = request.data.get('name')
        admin_state_up = request.data.get('admin_state_up')
        try:
            load_balancer = handler.update_load_balancers(request, loadbalancer_id=loadbalancer_id, name=name,
                                                          admin_state_up=admin_state_up)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="更新负载均衡器失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balancer)

    @swagger_auto_schema(operation_description="删除负载均衡器")
    def destroy(self, request, loadbalancer_id=None):
        response_obj = ResponseObj()
        try:
            delete_loadbalance = handler.delete_load_balancers(request, loadbalancer_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除负载均衡器失败", admin_info=str(ex), no=500)
        return delete_loadbalance

    @swagger_auto_schema(query_serializer=serializers.ShowLoadBalancersSerializer,
                         responses={200: response_serializers.ShowLoadBalancersResponsesSerializer},
                         operation_description="获取负载均衡器详细信息")
    def show_load_balancers(self, request, loadbalancer_id=None):
        response_obj = ResponseObj()
        try:
            load_balancers = handler.show_load_balancers(request, loadbalancer_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取负载均衡器详细信息失败", admin_info=str(ex), no=500)
        return load_balancers


class ProjectQuotasRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取用户当前项目下的Barbican各服务份额")
    @utils.param_info
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_secret_quotas_list = handler.quotas_list(request, project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的Barbican各服务份额失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_secret_quotas_list)


class ListenersRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取当前负载均衡器下的监听器列表")
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_listener = handler.listener_list(request, project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取当前负载均衡器下的监听器列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_listener)

    @swagger_auto_schema(operation_description="监听器详情")
    def retrieve(self, request, listener_id=None, pool_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_listener = handler.listener_detail(request, listener_id, pool_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取监听器详情失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_listener)

    @swagger_auto_schema(request_body=serializers.CreateListenerSerializer,
                         operation_description="创建监听器")
    @utils.param_info
    def create(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        loadbalancer_id = request.param_info.get("loadbalancer_id")
        listener_name = request.param_info.get("listener_name")
        protocol_port = request.param_info.get("protocol_port")
        protocol = request.param_info.get("protocol")
        whether_insert_headers = request.param_info.get("whether_insert_headers", "False")
        insert_headers = {
            "X-Forwarded-For": whether_insert_headers
        }
        timeout_member_connect = request.param_info.get("timeout_member_connect", 0)
        try:
            if protocol == 'HTTP' or protocol == 'HTTPS':
                load_balances_listener = handler.create_listener(request,
                                                                 insert_headers=insert_headers,
                                                                 loadbalancer_id=loadbalancer_id,
                                                                 name=listener_name,
                                                                 protocol=protocol,
                                                                 protocol_port=protocol_port,
                                                                 timeout_member_connect=timeout_member_connect
                                                                 )
            else:
                load_balances_listener = handler.create_listener(request,
                                                                 insert_headers=None,
                                                                 loadbalancer_id=loadbalancer_id,
                                                                 name=listener_name,
                                                                 protocol=protocol,
                                                                 protocol_port=protocol_port,
                                                                 timeout_member_connect=timeout_member_connect
                                                                 )
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="添加监听器超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="创建新的监听器失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_listener)

    @swagger_auto_schema(request_body=serializers.CreateSNIListenerSerializer,
                         operation_description="创建支持SNI协议的监听器")
    def create_sni(self, request):
        response_obj = ResponseObj()
        protocol = 'TERMINATED_HTTPS'
        if protocol is 'TERMINATED_HTTPS':
            default_tls_container_ref = request.data["default_tls_container_ref"]
            loadbalancer_id = request.data["loadbalancer_id"]
            listener_name = request.data["listener_name"]
            protocol_port = request.data["protocol_port"]
            timeout_member_connect = request.data["timeout_member_connect"]
            sni_container_refs = request.data["sni_container_refs"]
            try:
                # premise: the server's public endpoint MUST supports Key-Manager Service
                load_balances_sni_listener = handler.create_listener_sni(request,
                                                                         default_tls_container_ref=default_tls_container_ref,
                                                                         loadbalancer_id=loadbalancer_id,
                                                                         name=listener_name,
                                                                         protocol=protocol,
                                                                         protocol_port=protocol_port,
                                                                         sni_container_refs=sni_container_refs,
                                                                         timeout_member_connect=timeout_member_connect)
            except Exception as ex:
                return response_obj.json_exception_serial(user_info="创建支持SNI协议的监听器失败", admin_info=str(ex), no=500)
            return response_obj.json_serial(load_balances_sni_listener)
        else:
            return response_obj.json_serial("创建支持SNI协议的监听器失败")

    @swagger_auto_schema(request_body=serializers.UpdateListenerSerializer,
                         operation_description="编辑监听器")
    @utils.param_info
    def update(self, request, listener_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        listener_name = request.param_info.get("listener_name")
        timeout_member_connect = request.param_info.get("timeout_member_connect")
        default_pool_id = request.param_info.get("default_pool_id")
        whether_insert_headers = request.param_info.get("whether_insert_headers", "False")
        insert_headers = {
            "X-Forwarded-For": whether_insert_headers
        }
        loadbalancer_id = request.param_info.get("loadbalancer_id")
        protocol_port = request.param_info.get("protocol_port")
        protocol = request.param_info.get("protocol")
        try:
            load_balances_listener = handler.update_listener(request,
                                                             listener_id,
                                                             listener_name=listener_name,
                                                             timeout_member_connect=timeout_member_connect,
                                                             default_pool_id=default_pool_id,
                                                             insert_headers=insert_headers)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="编辑监听器超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="编辑当前监听器失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_listener)

    @swagger_auto_schema(operation_description="删除监听器")
    def destroy(self, request, listener_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_listener = handler.delete_listener(request, listener_id)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="删除监听器超时！", admin_info=str(timeout_ex), no=500)
        except exc.L7PolicyError as l7_ex:
            return response_obj.json_exception_serial(user_info="底层监听器删除失败：当前监听器有l7Policy，无法删除！", admin_info=str(l7_ex),
                                                      no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除监听器失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_listener)


class SecretsRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取SNI Constainer References列表")
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_secret_list = handler.secret_list(request, project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取SNI Constainer References列表表失败", admin_info=str(ex),
                                                      no=500)
        return response_obj.json_serial(load_balances_secret_list)

    @swagger_auto_schema(request_body=serializers.CreateSecretsSerializer,
                         operation_description="添加新的secret")
    def create(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        crt_name = request.data["crt_name"]
        crt_contents = request.data["crt_contents"]
        try:
            load_balances_sni_crt = handler.create_secret(request,
                                                          crt_name=crt_name,
                                                          crt_contents=crt_contents,
                                                          project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="添加新的secret失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_sni_crt)


class CertificatesRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取所有证书列表")
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_sni_crt = handler.certificates_list(request, project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取证书列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_sni_crt)

    @swagger_auto_schema(request_body=serializers.CreateCertificatesSerializer,
                         operation_description="上传新证书")
    def create(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')

        crt_name = request.data["crt_name"]
        crt_type = request.data["crt_type"]

        crt_contents = request.data["crt_contents"]
        # PEM formatted certificate
        # cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())

        crt_secret_key = request.data["crt_secret_key"]
        # PEM formatted private key
        # key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())

        crt_domain = request.data["crt_domain"]
        try:
            # create_certificate(name=None, subject_dn=None, source_container_ref=None, ca_id=None, profile=None, request_data=None)
            load_balances_sni_crt = handler.create_certificate(request,
                                                               crt_name=crt_name,
                                                               crt_type=crt_type,
                                                               crt_contents=crt_contents,
                                                               secret_key=crt_secret_key,
                                                               crt_domain=crt_domain,
                                                               project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="上传证书失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_sni_crt)

    @swagger_auto_schema(request_body=serializers.UpdateCertificatesSerializer,
                         operation_description="修改当前证书")
    def update(self, request):
        response_obj = ResponseObj()
        crt_name = request.data["crt_name"]
        crt_domain = request.data["crt_domain"]
        try:
            load_balances_sni_crt = handler.update_certificate(request, crt_name, crt_domain)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="编辑当前证书失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("编辑当前证书成功")

    @swagger_auto_schema(request_body=serializers.DeleteCertificatesSerializer,
                         operation_description="移除证书")
    def destroy(self, request, certificate_id=None):
        response_obj = ResponseObj()
        crt_name = request.data["crt_name"]
        crt_domain = request.data["crt_domain"]
        try:
            load_balances_sni_crt = handler.delete_certificate(request, certificate_id=certificate_id,
                                                               crt_domain=crt_domain)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="移除证书失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("移除证书成功")


class PoliciesRestfulViews(viewsets.ViewSet):

    @swagger_auto_schema(operation_description="策略列表")
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        load_balances_policies_details = []
        try:
            load_balances_listener_policies = handler.policies_list(request, project_id)
            for lb_policy in load_balances_listener_policies:
                local_created_time = swift_handler.utctime_to_localtime(lb_policy.created_at,
                                                                        utc_format='%Y-%m-%dT%H:%M:%S')
                local_updated_time = swift_handler.utctime_to_localtime(lb_policy.updated_at,
                                                                        utc_format='%Y-%m-%dT%H:%M:%S')
                result_dict = {
                    "action": lb_policy.action,
                    "created_at": local_created_time,
                    "id": lb_policy.id,
                    "is_admin_state_up": lb_policy.is_admin_state_up,
                    "listener_id": lb_policy.listener_id,
                    "name": lb_policy.name,
                    "operating_status": lb_policy.operating_status,
                    "provisioning_status": lb_policy.provisioning_status,
                    "redirect_pool_id": lb_policy.redirect_pool_id,
                    "rules": lb_policy.rules,
                    "updated_at": local_updated_time
                }
                load_balances_policies_details.append(result_dict)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取当前项目下的的策略列表失败",
                                                      admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_policies_details)

    @swagger_auto_schema(operation_description="获取当前监听器下的的策略列表")
    def retrieve(self, request, listener_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        load_balances_policies_details = []
        try:
            load_balances_listener_policies = handler.listener_policies_list(request, project_id, listener_id)
            for lb_policy in load_balances_listener_policies:
                local_created_time = swift_handler.utctime_to_localtime(lb_policy.created_at,
                                                                        utc_format='%Y-%m-%dT%H:%M:%S')
                local_updated_time = swift_handler.utctime_to_localtime(lb_policy.updated_at,
                                                                        utc_format='%Y-%m-%dT%H:%M:%S')
                rules = []
                if lb_policy.rules:
                    l7rules = handler.policies_rule_list(request, lb_policy.id, project_id=project_id)
                    rules = handler.l7rule_to_humanrule(l7rules)

                result_dict = {
                    "action": lb_policy.action,
                    "created_at": local_created_time,
                    "id": lb_policy.id,
                    "is_admin_state_up": lb_policy.is_admin_state_up,
                    "listener_id": lb_policy.listener_id,
                    "name": lb_policy.name,
                    "operating_status": lb_policy.operating_status,
                    "provisioning_status": lb_policy.provisioning_status,
                    "redirect_pool_id": lb_policy.redirect_pool_id,
                    "rules": rules,
                    "updated_at": local_updated_time
                }
                load_balances_policies_details.append(result_dict)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取监听器超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取当前监听器下的的策略列表失败",
                                                      admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_policies_details)

    @swagger_auto_schema(request_body=serializers.CreatePoliciesSerializer,
                         operation_description="创建策略")
    @utils.param_info
    def create(self, request, listener_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        param_info = request.param_info
        action = 'REDIRECT_TO_POOL'
        redirect_pool_id = param_info.get('redirect_pool_id')
        domain_name = param_info.get('domain_name', None)
        if domain_name == "":
            domain_name = None
        domain_compare_type = param_info.get("domain_compare_type", "EQUAL_TO")
        url = param_info.get("url", "/")
        if url == "":
            url = None
        url_compare_type = param_info.get("url_compare_type", "STARTS_WITH")
        load_balancer_policies = None
        try:
            load_balances_listener_policies = handler.listener_policies_list(request, project_id, listener_id)
            input_uri = {'HOST_NAME': domain_name, 'PATH': url}

            rule_uris = []
            if domain_name or url:
                for lb_policy in load_balances_listener_policies:
                    rule_uris.append(handler.rule_uri_list(request, lb_policy.id, project_id))

            if input_uri in rule_uris:
                user_info = "规则已存在！请重新选择URL或域名！"
                admin_info = "conflict with path or domain_name"
                return response_obj.json_exception_serial(user_info=user_info, admin_info=admin_info, no=409)
            # 创建策略
            load_balancer_policies = handler.create_policies(request,
                                                             name=param_info.get('name'),
                                                             action=action,
                                                             listener_id=listener_id,
                                                             redirect_pool_id=redirect_pool_id)
            # 创建策略规则：URI验重
            l7_rules = []
            if domain_name:
                pattern_host = r"^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$"
                match_host = re.match(pattern_host, domain_name, re.I)
                if match_host is None:
                    raise Exception("当前域名 '%s' 无效！" % domain_name)
                else:
                    load_balances_policies_rule = handler.create_policies_rule(request,
                                                                               l7policy_id=load_balancer_policies.id,
                                                                               compare_type=domain_compare_type,
                                                                               type='HOST_NAME',
                                                                               value=domain_name)
                    l7_rules.append(load_balances_policies_rule)

            if url:
                pattern_url = r'\A/[a-zA-Z0-9!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~\\]+\Z'
                match_url = re.match(pattern_url, url, re.I)
                if match_url is None:
                    if url == '/':
                        pass
                    else:
                        raise Exception("当前URL '%s' 无效！" % url)

                if isinstance(url, str):
                    load_balances_policies_rule = handler.create_policies_rule(request,
                                                                               l7policy_id=load_balancer_policies.id,
                                                                               compare_type=url_compare_type,
                                                                               type='PATH',
                                                                               value=url)
                    l7_rules.append(load_balances_policies_rule)
            rules = handler.l7rule_to_humanrule(l7_rules)

            result_dict = {
                "action": load_balancer_policies.action,
                "created_at": load_balancer_policies.created_at,
                "id": load_balancer_policies.id,
                "is_admin_state_up": load_balancer_policies.is_admin_state_up,
                "listener_id": load_balancer_policies.listener_id,
                "name": load_balancer_policies.name,
                "operating_status": load_balancer_policies.operating_status,
                "provisioning_status": load_balancer_policies.provisioning_status,
                "redirect_pool_id": load_balancer_policies.redirect_pool_id,
                "rules": rules,
                "updated_at": load_balancer_policies.updated_at
            }
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取资源超时！", admin_info=str(timeout_ex), no=500)
        except exc.L7PolicyCreateProtocolError as policy_ex:
            return response_obj.json_exception_serial(user_info="转发目标pool与当前listener协议类型冲突！", admin_info=str(policy_ex),
                                                      no=500)
        except exc.L7RuleCreateError as rule_ex:
            return response_obj.json_exception_serial(user_info="Openstack创建策略规则失败！", admin_info=str(rule_ex), no=500)
        except Exception as ex:
            if load_balancer_policies:
                handler.delete_policies(request, load_balancer_policies.id)
            return response_obj.json_exception_serial(user_info="创建策略失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(result_dict)

    @swagger_auto_schema(request_body=serializers.UpdatePoliciesSerializer,
                         operation_description="编辑策略")
    @utils.param_info
    def update(self, request, l7policy_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        param_info = request.param_info
        redirect_pool_id = param_info.get('redirect_pool_id')
        name = param_info.get('name')
        try:
            load_balancer_policies = handler.update_policies(request,
                                                             l7policy_id,
                                                             action='REDIRECT_TO_POOL',
                                                             redirect_pool_id=redirect_pool_id,
                                                             name=name)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取资源超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="编辑策略失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balancer_policies)

    @swagger_auto_schema(operation_description="删除策略")
    def destroy(self, request, l7policy_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balancer_policies = handler.delete_policies(request, l7policy_id)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取资源超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除策略失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balancer_policies)


class PoolsRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取用户当前项目下的Pool列表")
    @utils.param_info
    def list(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_pools = handler.pools_list(request, project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的Pool列表失败",
                                                      admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pools)

    @swagger_auto_schema(operation_description="获取用户当前项目下的某个Pool")
    def retrieve(self, request, pool_id=None, loadbalancer_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_pools = handler.pools_detail(request, pool_id, loadbalancer_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的Pool失败",
                                                      admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pools)

    @swagger_auto_schema(request_body=serializers.CreatePoolsSerializer,
                         operation_description="创建新的Pool")
    @utils.param_info
    def create(self, request):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        param_info = request.param_info
        lb_algorithm = param_info.get("lb_algorithm")
        name = param_info.get("name")
        protocol = param_info.get('protocol')
        loadbalancer_id = param_info.get('loadbalancer_id')
        listener_id = param_info.get('listener_id')
        session_persistence = param_info.get('session_persistence')
        is_keep_session = param_info.get('is_keep_session')
        try:
            load_balances_pools = handler.create_pools(request, name=name, lb_algorithm=lb_algorithm,
                                                       protocol=protocol, project_id=project_id,
                                                       loadbalancer_id=loadbalancer_id, listener_id=listener_id,
                                                       session_persistence=session_persistence,
                                                       is_keep_session=is_keep_session)

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="创建新的Pool失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pools)

    @swagger_auto_schema(request_body=serializers.UpdatePoolSerializer,
                         operation_description="更新Pool")
    def update(self, request, pool_id=None, loadbalancer_id=None):
        response_obj = ResponseObj()
        name = request.data.get("name")
        lb_algorithm = request.data.get("lb_algorithm")
        session_persistence = request.data.get('session_persistence')
        is_keep_session = request.data.get('is_keep_session')
        try:
            load_balances_pools = handler.update_pools(request, pool_id, name=name, is_keep_session=is_keep_session,
                                                       session_persistence=session_persistence,
                                                       lb_algorithm=lb_algorithm,
                                                       loadbalancer_id=loadbalancer_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="更新Pool失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pools)

    @swagger_auto_schema(operation_description="删除Pool")
    def destroy(self, request, pool_id=None):
        response_obj = ResponseObj()
        try:
            openstack_client = utils.get_openstack_client(request)
            pool_detail = openstack_client.load_balancer.get_pool(pool_id).to_dict()
            if pool_detail["members"]:
                return response_obj.json_exception_serial(user_info="删除Pool失败,当前pool下存在成员",
                                                          admin_info="当前pool下存在成员,无法进行删除操作", no=500)
            if pool_detail["listeners"]:
                return response_obj.json_exception_serial(user_info="删除Pool失败,当前pool已被listener绑定，无法进行删除操作！",
                                                          admin_info="删除Pool失败,当前pool已被listener绑定，无法进行删除操作！", no=500)
            load_balances_pools = handler.delete_pools(request, pool_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除Pool失败", admin_info=str(ex), no=500)
        return load_balances_pools


class HealthMonitorRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取某Health Monitor详情")
    def retrieve(self, request, healthmonitor_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_pools = handler.health_monitor_detail(request, healthmonitor_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取Health Monitor详情失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pools)

    @swagger_auto_schema(request_body=serializers.CreateHealthMonitorSerializer,
                         operation_description="开启Health Monitor")
    @utils.param_info
    def create(self, request):
        response_obj = ResponseObj()
        url_path = request.param_info.get("url_path", '/')
        delay = request.param_info.get("delay")
        max_retries = request.param_info.get("max_retries")
        timeout = request.param_info.get("timeout")
        pool_id = request.param_info.get("pool_id")
        type = request.param_info.get("type")

        try:
            if type == 'HTTP':
                pattern_url_path = r'^((\/)|(\/[^/]+)+)$'
                match_url_path = re.match(pattern_url_path, url_path, re.I)
                if match_url_path is None:
                    raise Exception("当前URL路径 '%s' 无效！" % url_path)
                if isinstance(url_path, str) and url_path.startswith('/'):
                    load_balancer_health_monitor = handler.create_health_monitor(request,
                                                                                 delay=delay,
                                                                                 max_retries=max_retries,
                                                                                 pool_id=pool_id,
                                                                                 timeout=timeout,
                                                                                 type=type,
                                                                                 url_path=url_path)
            else:
                load_balancer_health_monitor = handler.create_health_monitor(request,
                                                                             delay=delay,
                                                                             max_retries=max_retries,
                                                                             pool_id=pool_id,
                                                                             timeout=timeout,
                                                                             type=type,
                                                                             url_path=None)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取目标pool超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="开启Health Monitor失败！", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balancer_health_monitor)

    @swagger_auto_schema(request_body=serializers.UpdateHealthMonitorSerializer,
                         operation_description="编辑Health Monitor信息")
    @utils.param_info
    def update(self, request, healthmonitor_id=None, pool_id=None):
        response_obj = ResponseObj()
        delay = request.param_info.get("delay")
        max_retries = request.param_info.get("max_retries")
        timeout = request.param_info.get("timeout")
        url_path = request.param_info.get("url_path", "/")
        try:
            load_balances_pool_health_monitor = handler.update_health_monitor(request,
                                                                              healthmonitor_id,
                                                                              pool_id,
                                                                              delay,
                                                                              max_retries,
                                                                              timeout,
                                                                              url_path)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取目标健康检查器超时！", admin_info=str(timeout_ex), no=500)
        except exc.HealthMonitorUrlError as url_ex:
            return response_obj.json_exception_serial(user_info="健康检查器的检查URL路径填写无效！", admin_info=str(url_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="编辑Health Monitor信息失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pool_health_monitor)

    @swagger_auto_schema(operation_description="关闭Health Monitor")
    def destroy(self, request, healthmonitor_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_pools = handler.delete_health_monitor(request, healthmonitor_id)
        except exc.TimeoutError as timeout_ex:
            return response_obj.json_exception_serial(user_info="获取资源超时！", admin_info=str(timeout_ex), no=500)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="关闭Health Monitor失败！", admin_info=str(ex), no=500)
        return response_obj.json_serial("关闭Health Monitor成功！")


class FlavorRestfulViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()

    @swagger_auto_schema(operation_description="获取用户当前项目下的Flavor列表")
    @utils.param_info
    def list(self, request):
        response_obj = ResponseObj()
        try:
            flavor_obj = service_model.BmServiceLoadbalanceFlavor.objects.filter(status="active")
            response_obj.content = [u.__dict__ for u in flavor_obj]
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的Flavor列表失败", admin_info=str(ex),
                                                      no=500)
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")


class BindPublicIPRestfulViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()

    @swagger_auto_schema(operation_description="当前负载均衡实例绑定公网IP",
                         request_body=serializers.ServiceAddFloatingIptoLoadbalanceSerializer)
    @utils.param_info
    def create(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        loadbalance_name = param_info.get("loadbalance_name")
        loadbalance_id = param_info.get("loadbalance_id")
        floating_ip_id = param_info.get("floating_ip_id")
        try:
            attach_ip = handler.attach_ip_lb(request, loadbalance_name, loadbalance_id, floating_ip_id)
        except Exception as ex:
            self.logger.error("openstack attach ip to server result: %s" % str(ex))
            return response_obj.json_exception_serial(user_info="负载均衡实例关联浮动ip失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(attach_ip)


class UnBandPublicIPRestfulViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()

    @swagger_auto_schema(operation_description="当前负载均衡实例解绑公网IP",
                         request_body=serializers.ServiceDetachFloatingIptoLoadbalanceSerializer)
    def destroy(self, request):
        response_obj = ResponseObj()
        loadbalance_id = request.data.get("loadbalance_id")
        floating_ip_id = request.data.get("floating_ip_id")
        try:
            dettach_ip = handler.dettach_ip_lb(request, loadbalance_id, floating_ip_id)
        except Exception as ex:
            self.logger.error("openstack attach ip to server result: %s" % str(ex))
            return response_obj.json_exception_serial(user_info="负载均衡实例解绑浮动ip失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("负载均衡实例解绑浮动ip成功")


class AvailablePublicIPRestfulViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()

    @swagger_auto_schema(operation_description="查询当前负载均衡可绑定的公网IP列表")
    def available_ip_to_lb(self, request):
        response_obj = ResponseObj()
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        try:
            avaliable_ip_list = handler.available_floating_ip_to_lb(request, openstack_client)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查询当前负载均衡可绑定的公网IP列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(avaliable_ip_list)

    @swagger_auto_schema(operation_description="查询当前listener可绑定的pool列表",
                         request_body=serializers.LoadbalanceSerializer)
    @utils.param_info
    def available_pool_to_listener(self, request):
        response_obj = ResponseObj()
        param_info = request.param_info
        loadbalancer_id = param_info.get("loadbalancer_id")
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        try:
            available_pool_to_listener = handler.available_pool_to_listener(request, openstack_client,
                                                                            loadbalancer_id=loadbalancer_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查询当前listener可绑定的pool列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(available_pool_to_listener)


class AvailablePoolRestfulViews(viewsets.ViewSet):
    def __init__(self):
        self.aes_cipher = AESCipher()
        self.openstack_provider = OpenstackClientProvider()
        self.service_provider = ServiceProvider()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")
        self.service_floatingip_provider = ServiceFloatingProvider()

    @swagger_auto_schema(operation_description="查询当前listener可绑定的pool列表")
    def available_pool_to_listener(self, request, loadbalancer_id=None, listener_protocol=None):
        response_obj = ResponseObj()
        openstack_client = self.openstack_provider.get_openstack_client_by_request(request=request)
        try:
            available_pool_to_listener = handler.available_pool_to_listener(request, openstack_client,
                                                                            loadbalancer_id=loadbalancer_id,
                                                                            listener_protocol=listener_protocol)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="查询当前listener可绑定的pool列表失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(available_pool_to_listener)


class PoliciesRuleRestfulRulesViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取用户当前项目下的Policies Rule列表")
    def list(self, request, l7policy_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_policies_rule = handler.policies_rule_list(request, l7policy_id, project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的Policies Rule列表失败", admin_info=str(ex),
                                                      no=500)
        return response_obj.json_serial(load_balances_policies_rule)

    @swagger_auto_schema(operation_description="获取用户当前项目下的某个Policies Rule")
    def retrieve(self, request, l7policy_id=None, l7rule_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_policies_rule = handler.policies_rule_detail(request, l7policy_id, l7rule_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的Policies Rule失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_policies_rule)

    @swagger_auto_schema(request_body=serializers.CreatePoliciesRuleSerializer,
                         operation_description="创建策略规则")
    @utils.param_info
    def create(self, request, l7policy_id=None):
        response_obj = ResponseObj()
        param_info = request.param_info
        project_id = request.session.get('project_id')
        type = param_info.get('type')
        value = param_info.get('value')
        compare_type = param_info.get('compare_type')
        try:
            load_balances_policies_rule = handler.create_policies_rule(request,
                                                                       l7policy_id,
                                                                       compare_type=compare_type,
                                                                       type=type,
                                                                       value=value)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="创建策略规则失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_policies_rule)

    @swagger_auto_schema(request_body=serializers.UpdatePoliciesRuleSerializer,
                         operation_description="更新Policies Rule")
    def update(self, request, l7policy_id=None, l7rule_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_policies_rule = handler.update_policies_rule(request, l7policy_id, l7rule_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="更新Policies Rule失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_policies_rule)

    @swagger_auto_schema(operation_description="删除Policies Rule")
    def destroy(self, request, l7policy_id=None, l7rule_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_policies_rule = handler.delete_policies_rule(request, l7policy_id, l7rule_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="删除Policies Rule失败", admin_info=str(ex), no=500)
        return response_obj.json_serial("删除Policies Rule成功")


class PoolMembersRestfulViews(viewsets.ViewSet):
    @swagger_auto_schema(operation_description="获取资源池成员列表")
    def list(self, request, pool_id=None):
        response_obj = ResponseObj()
        project_id = request.session.get('project_id')
        try:
            load_balances_pool_member_list = handler.pool_member_list(request, pool_id, project_id=project_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取用户当前项目下的资源池成员列表失败", admin_info=str(ex),
                                                      no=500)
        return response_obj.json_serial(load_balances_pool_member_list)

    @swagger_auto_schema(operation_description="获取当前资源池的一个成员详情")
    def retrieve(self, request, pool_id=None, member_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_pool_member_details = handler.pool_member_detail(request, pool_id, member_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取成员详情失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pool_member_details)

    @swagger_auto_schema(request_body=serializers.AttachPoolMemberSerializer,
                         operation_description="添加新的资源池成员（添加成员到当前后端服务器组）")
    def attach_pool(self, request, pool_id=None):
        response_obj = ResponseObj()
        name = request.data['name']
        protocol_port = request.data['protocol_port']
        weight = request.data['weight']
        private_address = request.data['private_address']
        cur_public_address = request.data['public_address']
        instance_id = request.data["instance_id"]
        loadbancer_id = request.data["loadbancer_id"]
        try:

            if cur_public_address is not '':
                public_address = cur_public_address
            else:
                public_address = ''
            current_pool, current_member = handler.create_pool_member(request,
                                                                      pool_id,
                                                                      name=name,
                                                                      address=private_address,
                                                                      protocol_port=protocol_port,
                                                                      weight=weight,
                                                                      instance_id=instance_id,
                                                                      loadbancer_id=loadbancer_id)
            pool_detail = current_pool["location"]
            pool_region = pool_detail["region_name"]
            member_region = current_member.location.get('region_name')
            if pool_region != member_region:
                msg = {"user_info": "添加新的资源池成员失败：非同region！"}
                return HttpResponse(msg, status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)
            if current_member.project_id != current_pool['project_id']:
                msg = {"user_info": "添加新的资源池成员失败：非同Project！"}
                return HttpResponse(msg, status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)
            load_balancer_pool_member_detail = {
                "monitor_port": current_member.monitor_port,
                "subnet_id": current_member.subnet_id,
                "updated_at": current_member.updated_at,
                "weight": current_member.weight,
                "admin_state_up": current_member.is_admin_state_up,
                "provisioning_status": current_member.provisioning_status,
                "created_at": current_member.created_at,
                "monitor_address": current_member.monitor_address,
                'public_ip_address': public_address,
                "operating_status": current_member.operating_status,
                "backup": current_member.backup,
                "name": current_member.name,
                "protocol_port": current_member.protocol_port,
                "project_id": current_member.project_id,
                "id": current_member.id,
                "address": current_member.address
            }
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="添加新的资源池成员失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balancer_pool_member_detail)

    @swagger_auto_schema(request_body=serializers.UpdatePoolMemberSerializer,
                         operation_description="编辑资源池成员")
    def update(self, request, pool_id=None, member_id=None):
        response_obj = ResponseObj()
        # protocol_port = request.data["protocol_port"]
        weight = request.data["weight"]
        try:
            load_balances_pool_member_update = handler.update_pool_member(request,
                                                                          pool_id,
                                                                          member_id,
                                                                          # protocol_port,
                                                                          weight)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="编辑资源池成员失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pool_member_update)

    @swagger_auto_schema(operation_description="从当前后端资源组移除该成员", )
    def destroy(self, request, pool_id=None, member_id=None):
        response_obj = ResponseObj()
        try:
            load_balances_pool_member_removed = handler.delete_pool_member(request, pool_id, member_id)
        except Exception as ex:
            return response_obj.json_exception_serial(user_info="移除一个资源池成员失败", admin_info=str(ex), no=500)
        return response_obj.json_serial(load_balances_pool_member_removed)


class BaremetalServiceForTimeTaskViews(viewsets.ViewSet):
    def __init__(self):
        super(BaremetalServiceForTimeTaskViews, self).__init__()
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.openstack_provider = OpenstackClientProvider()
        self.time_task_provider = BmTimeTaskProvider()

    @swagger_auto_schema(operation_description="获取在使用服务器列表",
                         responses={200: response_serializers.ServiceInstanceInUseResponsesSerializer})
    @utils.param_info
    def service_instance_in_use_count(self, request):
        response_obj = ResponseObj()
        try:
            instance_list = self.time_task_provider.query_service_instance_in_use()
            response_obj.content = instance_list
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "在使用中得服务器列表查询失败", "admin_info": ex}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        return HttpResponse(json_data, content_type="application/json")
