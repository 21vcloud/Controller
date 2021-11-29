# coding: utf-8

import smtplib
import urllib.request
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import common.lark_common.model.common_model as common_model
import common.lark_common.utils as lark_utils
from jinja2 import Template
from BareMetalControllerBackend.conf import env


class ModelEmailNotification:
    def __init__(self):
        self.env_config = env.EnvConfig()
        self.from_address = None
        self.to_address = []
        self.cc_address = []
        self.bcc_address = []
        self.subject = None
        self.email_template_uri = None
        self.image_uri = {}
        self.parameter = {}

        self.smtp_server = self.env_config.notification_smtp_server
        self.smtp_ssl_port = self.env_config.notification_smtp_ssl_port
        self.smtp_login_required = self.env_config.notification_smtp_login_required
        self.smtp_ssl_enable = self.env_config.notification_smtp_ssl_enable
        self.smtp_username = self.env_config.notification_smtp_username
        self.smtp_password = self.env_config.notification_smtp_password


class ProviderEmailNotification(object):
    def __init__(self, model_notification=None):
        self.model_notification = model_notification

        self.env_config = env.EnvConfig()

    def __generate_body(self):
        """
        根据model notification中的模板内容和参数生成邮件正文
        :return: 电子邮件正文
        """

        response = common_model.ResponseObj()

        try:
            email_template_stream = urllib.request.urlopen(self.model_notification.email_template_uri).read().decode('utf-8')
            # email_template_stream = urllib.request.install_opener("static/reset_apssword.html").read().decode('utf-8')
            email_template = Template(email_template_stream)

            parameter_dict = self.model_notification.parameter
            if not isinstance(self.model_notification.parameter, dict):
                parameter_dict = lark_utils.JsonUtils.convert_object_to_dict(self.model_notification.parameter)
            email_body = email_template.render(parameter_dict)

            response.is_ok = True
            response.content = email_body

        except Exception as ex:
            # self.env_config.logger.error(ex)
            response.is_ok = False
            response.message = u"email template is emtpy or can not be downloaded."
            return response

        return response

    def __generate_message(self):
        response = common_model.ResponseObj()

        msg = MIMEMultipart('related')

        response_body = self.__generate_body()
        if not response_body.is_ok:
            return response_body
        content = MIMEText(response_body.content, 'html', 'utf-8')
        msg.attach(content)

        msg['Subject'] = self.model_notification.subject

        msg['From'] = self.model_notification.from_address
        msg['To'] = ','.join(self.model_notification.to_address)
        msg['Cc'] = ','.join(self.model_notification.cc_address)
        msg['Bcc'] = ','.join(self.model_notification.bcc_address)

        try:
            image_uri_dict = self.model_notification.image_uri

            if image_uri_dict and len(image_uri_dict) > 0:
                for (image_key, image_uri) in image_uri_dict.items():
                    image_content = urllib.request.urlopen(image_uri).read()
                    mime_image = MIMEImage(image_content)
                    mime_image.add_header('Content-ID', image_key)
                    msg.attach(mime_image)
        except Exception as ex:
            return ex
            # self.env_config.logger.error("can not download and read image. " + str(ex))

        response.content = msg.as_string()
        response.is_ok = True

        return response

    def send(self):
        response_obj = common_model.ResponseObj()

        try:
            # 邮件主题内容
            response_message = self.__generate_message()
            if not response_message.is_ok:
                return response_message

            # 收件人列表
            receiver = self.model_notification.to_address + self.model_notification.cc_address + self.model_notification.bcc_address

            # 链接smtp 服务器
            if not self.model_notification.smtp_ssl_enable:
                smtp_server = smtplib.SMTP(self.model_notification.smtp_server)
            else:
                smtp_server = smtplib.SMTP_SSL(self.model_notification.smtp_server, self.model_notification.smtp_ssl_port)

            # 登录smtp服务器
            if self.model_notification.smtp_login_required:
                smtp_server.login(self.model_notification.smtp_username, self.model_notification.smtp_password)

            # 邮件发送
            smtp_server.sendmail(self.model_notification.from_address, receiver, msg=response_message.content)
            smtp_server.quit()
        except Exception as ex:
            response_obj.message = "Fail to send email! Error : %s " % str(ex)
            response_obj.is_ok = False
            response_obj.no = 500
            return response_obj

        response_obj.is_ok = True
        response_obj.content = "email send success!"
        return response_obj
