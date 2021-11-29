# -*- coding:utf-8 -*-

from __future__ import division

import os
import configparser
from common.innerpyapollo.apollo_client import ApolloClient
import jsonpickle

class EnvConfig(object):
    def __init__(self):

        # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
        config_file = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/conf/baremetal.ini"
        config = configparser.ConfigParser()

        config.read(config_file)
        client = ApolloClient(app_id=config.get('apollo_server', 'app_id'),
                              config_server_url=config.get('apollo_server', 'config_server_url'),
                              ip=config.get('apollo_server', 'ip'))
        client.start(use_eventlet=True)
        self.result_all = client.all()

        intro_list = client.get_value(key="introList", namespace="baremetal_front")
        self.baremetal_front = client.all(namespace="baremetal_front")
        product_type = jsonpickle.loads(client.get_value(key="product_type", namespace="baremetal_front"))

        # Common Section
        mysql_result = jsonpickle.loads(self.result_all['backend_mysql_info'])
        # notification_smtp = jsonpickle.loads(self.result_all['notification_smtp_weipl'])
        notification_smtp = jsonpickle.loads(self.result_all['notification_smtp'])
        notification_reset_pwd = jsonpickle.loads(self.result_all['notification_reset_pwd'])
        notification_email_verify_code = jsonpickle.loads(self.result_all['notification_email_verify_code'])
        notification_email_contact = jsonpickle.loads(client.get_value(key="notification_email_contact"))
        notification_email_contact_for_discount = jsonpickle.loads(
            client.get_value(key="notification_email_contact_for_discount"))
        notification_monitor_alarm = jsonpickle.loads(
            client.get_value(key="monitor_alarm_notification", namespace="MonitoringMiddleGround"))
        short_message_info = jsonpickle.loads(self.result_all['short_message_info'])
        account = jsonpickle.loads(self.result_all['account'])
        api_test = jsonpickle.loads(self.result_all['api_test'])
        open_info = jsonpickle.loads(self.result_all['open_info'])
        controller = jsonpickle.loads(self.result_all['controller'])
        celery_conf_info = jsonpickle.loads(client.get_value(key="celery_conf_info"))
        openstack_admin_info = jsonpickle.loads(
            client.get_value(key="openstack_admin_info", namespace="job_executor"))
        baremetal = jsonpickle.loads(self.result_all['baremetal'])
        baremetal_guest = jsonpickle.loads(self.result_all['baremetal_guest'])
        websocket = jsonpickle.loads(self.result_all['websocket'])
        monitoring_token_info = jsonpickle.loads(
            client.get_value(key="token_info", namespace="MonitoringMiddleGround"))

        monitoring_api_url = jsonpickle.loads(
            client.get_value(key="monitoring_api_url", namespace="MonitoringMiddleGround"))

        # external_network
        external_networks = jsonpickle.loads(self.result_all['external_networks'])
        self.object_endpoint = jsonpickle.loads(self.result_all['object_endpoint'])
        self.service_region = jsonpickle.loads(client.get_value(key='service_region'))

        # mysql info
        self.backend_mysql_db_name = mysql_result.get('backend_mysql_db_name')
        self.backend_mysql_db_user = mysql_result.get('backend_mysql_db_user')
        self.backend_mysql_db_password = mysql_result.get('backend_mysql_db_password')
        self.backend_mysql_db_host = mysql_result.get('backend_mysql_db_host')
        self.backend_mysql_db_port = mysql_result.get('backend_mysql_db_port')

        # account
        self.token_timeout = account.get('token_timeout', 2700)
        self.code_timeout = account.get('code_timeout')
        self.reset_password_url = account.get('reset_password_url')

        # keystone admin user info
        self.auth_url = open_info.get('auth_url')
        self.project_domain_name = open_info.get('project_domain_name', 'default')
        self.user_domain_name = open_info.get('user_domain_name', 'default')
        self.admin_user = open_info.get('username')
        self.admin_password = open_info.get('password')
        self.region_name = open_info.get('region_name', 'regionOne')

        # controller config
        self.session_timeout = controller.get('session_timeout')
        self.session_cookie_domain = self.result_all.get('session_cookie_domain')
        self.api_debug = self.result_all.get('debug', False)

        # notification base conf info
        self.notification_smtp_server = notification_smtp.get('notification_smtp_server')
        self.notification_smtp_ssl_port = notification_smtp.get('notification_smtp_ssl_port')
        self.notification_smtp_username = notification_smtp.get('notification_smtp_username')
        self.notification_smtp_password = notification_smtp.get('notification_smtp_password')
        self.notification_smtp_login_required = notification_smtp.get('notification_smtp_login_required')
        self.notification_smtp_ssl_enable = notification_smtp.get('notification_smtp_ssl_enable')

        # notification reset password conf info
        self.notification_reset_pwd_from = notification_reset_pwd.get('notification_reset_pwd_from')
        self.notification_reset_pwd_bcc = notification_reset_pwd.get('notification_reset_pwd_bcc')
        self.notification_reset_pwd_subject = notification_reset_pwd.get('notification_reset_pwd_subject')
        self.notification_reset_pwd_template_uri = notification_reset_pwd.get('notification_reset_pwd_template_uri')
        self.notification_reset_pwd_image_uri = notification_reset_pwd.get('notification_reset_pwd_image_uri')

        # notification email verify code conf
        self.notification_email_verify_code_from = notification_email_verify_code.get('notification_email_verify_code_from')
        self.notification_email_verify_code_bcc = notification_email_verify_code.get('notification_email_verify_code_bcc')
        self.notification_email_verify_code_subject = notification_email_verify_code.get('notification_email_verify_code_subject')
        self.notification_email_verify_code_template_uri = notification_email_verify_code.get('notification_email_verify_code_template_uri')
        self.notification_email_verify_code_image_uri = notification_email_verify_code.get('notification_email_verify_code_image_uri')

        # 联系我们
        self.notification_email_contact_from = notification_email_contact.get(
            'notification_email_contact_from')
        self.notification_email_contact_to = notification_email_contact.get(
            'notification_email_contact_to')
        self.notification_email_contact_bcc = notification_email_contact.get(
            'notification_email_contact_bcc')
        self.notification_email_contact_subject = notification_email_contact.get(
            'notification_email_contact_subject')
        self.notification_email_contact_template_uri = notification_email_contact.get(
            'notification_email_contact_template_uri')
        self.notification_email_contact_image_uri = notification_email_contact.get(
            'notification_email_contact_image_uri')

        # 联系我们优惠
        self.notification_email_contact_for_discount_from = notification_email_contact_for_discount.get(
            'notification_email_contact_for_discount_from')
        self.notification_email_contact_for_discount_to = notification_email_contact_for_discount.get(
            'notification_email_contact_for_discount_to')
        self.notification_email_contact_for_discount_bcc = notification_email_contact_for_discount.get(
            'notification_email_contact_for_discount_bcc')
        self.notification_email_contact_for_discount_subject = notification_email_contact_for_discount.get(
            'notification_email_contact_for_discount_subject')
        self.notification_email_contact_for_discount_template_uri = notification_email_contact_for_discount.get(
            'notification_email_contact_for_discount_template_uri')
        self.notification_email_contact_for_discount_image_uri = notification_email_contact_for_discount.get(
            'notification_email_contact_for_discount_image_uri')


        # short message  info 短信发送相关配置
        self.short_message_sms_user = short_message_info.get('short_message_sms_user')
        self.short_message_sms_key = short_message_info.get('short_message_sms_key')
        self.short_message_smsapi_endpoint = short_message_info.get('short_message_smsapi_endpoint')
        self.short_message_label_id = short_message_info.get('short_message_label_id')
        self.short_message_sign_name = short_message_info.get('short_message_sign_name')

        # api_test
        self.account_endpoint = api_test.get("account_endpoint")
        self.account_project_endpoint = api_test.get("account_project_endpoint")
        self.account_enterprise_endpoint = api_test.get("account_enterprise_endpoint")
        self.baremetal_endpoint = api_test.get("baremetal_endpoint")
        self.service_endpoint = api_test.get("service_endpoint")
        # baremetal
        self.baremetal_tag = baremetal.get('tag')
        self.guest_transport_url = baremetal_guest.get('transport_url')
        self.guest_exchange = baremetal_guest.get('exchange')

        # celery conf info
        self.celery_main = celery_conf_info.get("celery_main")
        self.celery_broker = celery_conf_info.get("celery_broker")
        self.celery_backend = celery_conf_info.get("celery_backend")

        # websocket
        self.websocket_namespace = websocket.get('namespace')
        self.collect_info = websocket.get('collect_info')
        self.websocket_secret_key = websocket.get('secret_key')
        self.external_networks = external_networks

        # openstack_admin_info
        self.openstack_admin_auth_url = openstack_admin_info.get("auth_url")
        self.openstack_admin_username = openstack_admin_info.get("username")
        self.openstack_admin_password = openstack_admin_info.get("password")
        self.openstack_admin_project_id = openstack_admin_info.get("project_id")
        self.openstack_admin_project_domain_name = openstack_admin_info.get("project_domain_name")
        self.openstack_admin_region_name = openstack_admin_info.get("region_name")
        self.openstack_admin_compute_api_version = openstack_admin_info.get("compute_api_version")
        self.openstack_admin_identity_interface = openstack_admin_info.get("identity_interface")
        self.openstack_admin_user_domain_id = openstack_admin_info.get("user_domain_id")

        # 产品类型
        self.floating_ip_type = product_type.get("floating_ip", "弹性公网IP")
        self.band_width_type = product_type.get("band_width", "带宽")
        self.volume_type = product_type.get("volume", "云硬盘")
        self.volume_backup_type = product_type.get("volume_backup", "云硬盘备份")
        self.ecbm_type = product_type.get("ECBM", "裸金属")


        # 监控告警邮件通知
        self.notification_monitor_alarm_from = notification_monitor_alarm.get(
            'notification_monitor_alarm_from')
        self.notification_monitor_alarm_to = notification_monitor_alarm.get(
            'notification_monitor_alarm_to', [])
        self.notification_monitor_alarm_bcc = notification_monitor_alarm.get(
            'notification_monitor_alarm_bcc', [])
        self.notification_monitor_alarm_subject = notification_monitor_alarm.get(
            'notification_monitor_alarm_subject')
        self.notification_monitor_alarm_template_uri = notification_monitor_alarm.get(
            'notification_monitor_alarm_template_uri')
        self.notification_monitor_alarm_image_uri = notification_monitor_alarm.get(
            'notification_monitor_alarm_image_uri')

        self.monitor_token_ignore = monitoring_token_info.get("token_ignore")

        # monitoring api url
        self.monitoring_service = monitoring_api_url.get("monitoring_service")
        self.cmdb_asset_service = monitoring_api_url.get("cmdb_asset_service")
        self.cmdb_customize_service = monitoring_api_url.get("cmdb_customize_service")
        self.cmdb_structure_service = monitoring_api_url.get("cmdb_structure_service")

        self.audit_api_url = client.get_value(key='audit_api_url', namespace='AuditMiddleGroup')
        self.audit_mq_info = jsonpickle.loads(client.get_value(key='mq_info', namespace='AuditMiddleGroup'))


env_config = EnvConfig()
