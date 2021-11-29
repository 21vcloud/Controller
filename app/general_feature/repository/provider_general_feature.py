# -*- coding:utf-8 -*-

from common.emial_server import send_email as helper_send_email
from common.lark_common.model.common_model import ResponseObj


class MessageSend(object):

    # 发送获取验证码邮件
    def send_email_verify_code_email(self, to_list, message_param_info):

        response_obj = ResponseObj()
        try:
            notify_model = self.__generate_email_alarm_data()

            # email info
            notify_model.to_address += to_list
            notify_model.parameter = message_param_info

            # send email
            provider_send_email = helper_send_email.ProviderEmailNotification(model_notification=notify_model)
            response_obj = provider_send_email.send()
        except Exception as ex:
            response_obj.message = {"user_info": "邮件发送失败", "admin_info": str(ex)}
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj
        return response_obj

    # 邮件验证码 项目邮件信息
    @staticmethod
    def __generate_email_alarm_data():
        notify_model = helper_send_email.ModelEmailNotification()
        notify_model.from_address = notify_model.env_config.notification_monitor_alarm_from
        notify_model.bcc_address = notify_model.env_config.notification_monitor_alarm_bcc
        notify_model.subject = notify_model.env_config.notification_monitor_alarm_subject
        notify_model.email_template_uri = notify_model.env_config.notification_monitor_alarm_template_uri
        notify_model.image_uri = notify_model.env_config.notification_email_verify_code_image_uri
        return notify_model
