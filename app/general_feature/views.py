from django.shortcuts import render
import jsonpickle
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from common.lark_common.model.common_model import ResponseObj
from general_feature.repository import serializers
from general_feature.repository import  provider_general_feature

# Create your views here.
class MessageSend(APIView):
    def __init__(self):
        super(MessageSend, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.message_send = provider_general_feature.MessageSend()

    @swagger_auto_schema(request_body=serializers.MessageSendSerializer,
                         operation_description="监控告警发送接口")
    def post(self, request):
        """
        :param request:
        :return:
        """
        response_obj = ResponseObj()
        try:
            response_obj = ResponseObj()
            param_info = request.data
            email_to_list = param_info.get("email_to_list")
            message_param_info = param_info.get("param_info")
            message_type = param_info.get("message_type", ["email"])
            response_obj = self.message_send.send_email_verify_code_email(to_list=email_to_list, message_param_info=message_param_info)
        except Exception as ex:
            response_obj.message = {"user_info": "邮件发送失败", "admin_info": ex}
            response_obj.is_ok = False
            response_obj.no = 500
        json_data = jsonpickle.dumps(response_obj, unpicklable=False)
        self.logger.info("Result : %s " % json_data)
        return HttpResponse(json_data, content_type="application/json")
