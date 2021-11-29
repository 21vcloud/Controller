# -*- coding:utf-8 -*-
import logging

import jsonpickle
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from baremetal_service.repository import service_model as service_model

from BareMetalControllerBackend.conf.env import EnvConfig
from account.auth import utils as auth_utils
from django.db.models import Q
from baremetal_dashboard.repository import response_serializers
from baremetal_dashboard.repository import baremental_model
from baremetal_dashboard.repository import serializers
from common.lark_common.model.common_model import ResponseObj
from common.lark_common.utils import AESCipher
from common.emial_server import send_email as helper_send_email


class FrontEndViews(viewsets.ViewSet):
    def __init__(self):
        self.env_config = EnvConfig()
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    # @utils.token_verify
    @swagger_auto_schema(query_serializer=serializers.GetConfInfoSerializer,
                         operation_description="根据关键词获取相应信息",
                         responses={200: response_serializers.GetInfoByKeyResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def get_info_by_key(self, request):
        response_obj = ResponseObj()
        try:
            env_config = EnvConfig()
            key_value = request.param_info.get("key_value")
            result = env_config.baremetal_front.get(key_value)
            if not result:
                result = env_config.result_all.get(key_value)

            response_obj.content = result
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "获取配置信息失败", "admin_info": str(ex)}
            response_obj.no = 500

        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.ContactToUsSerializer,
                         operation_description="提交联系我们表单接口",
                         responses={200: response_serializers.ContactToUsResponsesSerializer},
                         )
    @auth_utils.param_info_decrypt
    def view_contact_to_us(self, request):

        response_obj = ResponseObj()
        try:
            post_data = request.param_info
            request = baremental_model.BmContactToUs.objects.create(**post_data)

            post_data["order_number"] = request.id
            email_result = self.__send_contact_email(post_data)
            if not email_result.is_ok:
                raise Exception(email_result.message)

            response_obj.content = request
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "表单提交失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")

    @swagger_auto_schema(request_body=serializers.ContactToUsForDiscountSerializer,
                         operation_description="提交联系我们优惠表单接口",
                         responses={200: response_serializers.ContactToUsForDiscountResponsesSerializer})
    @auth_utils.param_info_decrypt
    def view_contact_to_us_for_discount(self, request):

        response_obj = ResponseObj()
        try:
            post_data = request.param_info
            request = baremental_model.BmContactToUsForDiscount.objects.create(**post_data)

            post_data["order_number"] = request.id
            email_result = self.__send_contact_for_discount_email(post_data)
            if not email_result.is_ok:
                raise Exception(email_result.message)

            response_obj.content = request
            response_obj.is_ok = True
            response_obj.no = 200
        except Exception as ex:
            response_obj.is_ok = False
            response_obj.message = {"user_info": "表单提交失败", "admin_info": str(ex)}
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")


    # 发送联系我们邮件
    def __send_contact_email(self, post_data):

        response_obj = ResponseObj()
        try:
            # get email base information
            notify_model = self.__generate_email_contact_data()

            # email info
            notify_model.subject = notify_model.subject + post_data.get("order_number", "")
            notify_model.parameter = {
                "order_number": post_data.get("order_number"),
                "customer_name": post_data.get("customer_name"),
                "phone": post_data.get("phone"),
                "email": post_data.get("email"),
                "company": post_data.get("company"),
                "department": post_data.get("department"),
                "job_position": post_data.get("job_position"),
                "issue_content": post_data.get("issue_content")
            }
            # send email
            provider_send_email = helper_send_email.ProviderEmailNotification(model_notification=notify_model)
            response_obj = provider_send_email.send()
        except Exception as ex:
            response_obj.message = {"user_info": "邮件发送失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj

        return response_obj

    @staticmethod
    def __generate_email_contact_data():
        notify_model = helper_send_email.ModelEmailNotification()
        notify_model.from_address = notify_model.env_config.notification_email_contact_from
        notify_model.to_address = notify_model.env_config.notification_email_contact_to
        notify_model.bcc_address = notify_model.env_config.notification_email_contact_bcc
        notify_model.subject = notify_model.env_config.notification_email_contact_subject
        notify_model.email_template_uri = notify_model.env_config.notification_email_contact_template_uri
        notify_model.image_uri = notify_model.env_config.notification_email_contact_image_uri
        return notify_model

    # 发送抗疫情优惠邮件
    def __send_contact_for_discount_email(self, post_data):

        response_obj = ResponseObj()
        try:
            # get email base information
            notify_model = self.__generate_email_contact_for_discount_data()

            # email info
            notify_model.subject = notify_model.subject + post_data.get("order_number", "")
            notify_model.parameter = {
                "order_number": post_data.get("order_number"),
                "customer_name": post_data.get("customer_name"),
                "phone": post_data.get("phone"),
                "email": post_data.get("email"),
                "company": post_data.get("company"),
                "industry": post_data.get("industry"),
                "job_position": post_data.get("job_position"),
                # "product_type": post_data.get("product_type"),
                "product_content": post_data.get("product_content")
            }
            # send email
            provider_send_email = helper_send_email.ProviderEmailNotification(model_notification=notify_model)
            response_obj = provider_send_email.send()
        except Exception as ex:
            response_obj.message = {"user_info": "邮件发送失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj

        return response_obj

    @staticmethod
    def __generate_email_contact_for_discount_data():
        notify_model = helper_send_email.ModelEmailNotification()
        notify_model.from_address = notify_model.env_config.notification_email_contact_for_discount_from
        notify_model.to_address = notify_model.env_config.notification_email_contact_for_discount_to
        notify_model.bcc_address = notify_model.env_config.notification_email_contact_for_discount_bcc
        notify_model.subject = notify_model.env_config.notification_email_contact_for_discount_subject
        notify_model.email_template_uri = notify_model.env_config.notification_email_contact_for_discount_template_uri
        notify_model.image_uri = notify_model.env_config.notification_email_contact_for_discount_image_uri
        return notify_model


class BaremetalViews(viewsets.ViewSet):
    def __init__(self):
        self.env_config = EnvConfig()
        self.aes_cipher = AESCipher()
        self.logger = logging.getLogger(__name__)
        self.request_info_logger = logging.getLogger("request_info")

    @swagger_auto_schema(operation_description="获取裸金属列表")
    @auth_utils.param_info_decrypt
    def baremetal_list(self,request):
        response_obj = ResponseObj()
        param_info = request.param_info
        try:

            instance_list = service_model.BmServiceInstance.objects.filter(deleted=False).filter(~Q(uuid = ''))
            instance_list = [u.__dict__ for u in instance_list]

        except Exception as ex:
            return response_obj.json_exception_serial(user_info="获取裸金属列表失败！",
                                                      admin_info=str(ex), no=300)
        return response_obj.json_serial(instance_list)
