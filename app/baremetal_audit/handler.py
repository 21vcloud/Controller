# -*- coding: utf-8 -*-
import datetime
import logging
import json
import jsonpickle
import requests
import six

from django.core.exceptions import ObjectDoesNotExist
from oslo_config import cfg
import oslo_messaging as messaging

from account.repository.auth_models import BmMappingUserProject, BmUserInfo
from baremetal_audit import audit_types
from BareMetalControllerBackend.conf.env import env_config

LOG = logging.getLogger('request_info')
PLATFORM = 'BAREMETAL'
AUDITAPI = None
AUDITLOG_NOTIFICATION = None


class AuditLogAPI(object):
    def __init__(self):
        self.endpoint = env_config.audit_api_url
        LOG.info("Audit api_endpoint %s", self.endpoint)
        self.api_version = 'v1'
        self.USER_AGNET = "backend-controller"

    def concat_url(self, path):
        return self.endpoint.rstrip('/') + '/v1' + path

    def http_request(self, method, path, **kwargs):
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGNET
        kwargs['headers']['Accept'] = 'application/json'

        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs['body'])
            del kwargs['body']
        else:
            kwargs.setdefault('params', kwargs.get('params', {}))

        url = self.concat_url(path)
        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def list_audit_log(self, start_time=None, end_time=None, **filters):
        path = '/cloud_audit'

        params = filters
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        params['platform'] = PLATFORM

        return self.http_request('GET', path, params=params)


def get_cloud_audit_api():
    global AUDITAPI
    if AUDITAPI:
        return AUDITAPI
    else:
        AUDITAPI = AuditLogAPI()
        return AUDITAPI


def get_userinfo_by_project(project_id):
    users = []
    mappings = BmMappingUserProject.objects.values_list('account_id', flat=True).filter(project_id=project_id,
                                                                                        status='active')
    for user_id in mappings:
        try:
            user_info = BmUserInfo.objects.values('id', 'account', 'identity_name').get(id=user_id)
            users.append(user_info)
        except ObjectDoesNotExist:
            LOG.debug("user %s not exist", user_id)
    return users


def get_userinfo_by_id(user_id):
    try:
        user_info = BmUserInfo.objects.values('id', 'account', 'identity_name').get(id=user_id)
    except ObjectDoesNotExist:
        LOG.debug("user %s not exist", user_id)
        return {}
    return user_info


class AuditLogNotification(object):

    def __init__(self):
        self.exchange = env_config.audit_mq_info.get("exchange", 'cloudaudit')
        self.topic = env_config.audit_mq_info.get('topic', 'log_audit')
        self.transport_url = env_config.audit_mq_info.get("transport_url", None)
        LOG.debug("Get transport %s , exchange %s, topic %s", self.transport_url, self.exchange, self.topic)
        messaging.set_transport_defaults(self.exchange)  # exchange
        transport = messaging.get_notification_transport(cfg.CONF, url=self.transport_url)  # url
        self.notifier = messaging.Notifier(transport, driver='messagingv2', topics=[self.topic], publisher_id=PLATFORM)

    def _notifier_send(self, payload_info=None):
        if payload_info:
            self.notifier.info(ctxt={}, event_type='cloud_audit.log', payload=payload_info)

    def send(self, platform=PLATFORM, region=env_config.region_name, project_id=None, user_id=None, service_type=None,
             resource_id=None, resource_name=None, resource_type=None, contract_number=None, time=None,
             trace_name=None, trace_type=None, source_ip=None, request=None, response=None, code=200,
             event_type=audit_types.NATIONAL, **kwargs):
        """

        :param platform: str
        :param region: str
        :param project_id: str
        :param user_id: str
        :param service_type: str
        :param resource_id: str
        :param resource_name: str
        :param resource_type: str
        :param contract_number: str
        :param time: str
        :param trace_name: str
        :param trace_type: str
        :param source_ip: str
        :param request: str
        :param response: str
        :param code: int
        :return:
        """
        if not time:
            time = str(datetime.datetime.now().timestamp())
        if not isinstance(time, str):
            time = str(time)

        payload_info = {
            "platform": platform,
            "region": region,
            "project_id": project_id,
            "user_id": user_id,
            "service_type": service_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_name": resource_name,
            "contrace_number": contract_number,
            "time": time,
            "trace_name": trace_name,
            "trace_type": trace_type,
            "source_ip": source_ip,
            "request": request,
            "response": response,
            "code": code,
            "event_type": event_type
        }
        if kwargs:
            payload_info.update(kwargs)
        self._notifier_send(payload_info)


def get_cloud_log_notification():
    global AUDITLOG_NOTIFICATION
    if AUDITLOG_NOTIFICATION:
        return AUDITLOG_NOTIFICATION

    else:
        AUDITLOG_NOTIFICATION = AuditLogNotification()
        return AUDITLOG_NOTIFICATION


def send_cloud_audit_log_single_request(service_type, resource_type, trace_name=None,
                                        trace_type=audit_types.CONSOLEACTION,
                                        resource_id_key='id', resource_name_key='name',
                                        event_type=audit_types.NATIONAL):
    """
    订单请求中请求个数为单个的装饰器，如果为批量请求使用send_cloud_audit_log_multi_request装饰器
    :param service_type: 服务类型，必填
    :param resource_type: 资源类型 必填
    :param trace_name: 操作名称，必填
    :param trace_type: 操作类型，默认为consoleaction
    :param resource_id_key: 从views的response中获取资源id，返回值中的资源id key默认为"id"
    :param resource_name_key: 从views的response获取资源name，返回值中的资源name key默认为"name"
    :return:
    """

    def outer(f):
        @six.wraps(f)
        def _inner(self, request, *args, **kwargs):
            response = f(self, request, *args, **kwargs)
            try:
                project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
                account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
                user = get_userinfo_by_id(account_id)
                region = request.session.get('region', env_config.region_name)
                res_data = json.loads(response.content.decode(encoding='UTF-8',errors='strict'))
                resource_id = None
                resource_name = None
                contract_number = None
                if res_data.get('no') == 200 and res_data.get('is_ok'):
                    content = res_data.get('content')
                    if content:
                        resource_id = content.get(resource_id_key)
                        resource_name = content.get(resource_name_key)
                    order_info = request.param_info.get("order_info", {})
                    if order_info:
                        contract_number = order_info.get("contract_number")
                        if not contract_number:
                            contract_number = content.get("contract_number", None)
                timestamp = str(datetime.datetime.now().timestamp())
                get_cloud_log_notification().send(region=region, project_id=project_id, user_id=account_id,
                                                  service_type=service_type, resource_id=resource_id,
                                                  resource_name=resource_name, resource_type=resource_type,
                                                  contract_number=contract_number, time=timestamp,
                                                  trace_name=trace_name, trace_type=trace_type, source_ip=None,
                                                  request=jsonpickle.dumps(request.param_info), response=jsonpickle.dumps(res_data),
                                                  event_type=event_type, code=res_data.get('no', 200), user=user)
            except Exception as e:
                LOG.exception("Send notification error %s", str(e))
            return response

        return _inner

    return outer


def send_cloud_audit_log_multi_request(service_type, resource_type, trace_name=None,
                                       trace_type=audit_types.CONSOLEACTION,
                                       resource_id_key='id', resource_name_key='name',
                                       event_type=audit_types.NATIONAL):
    def outer(f):
        @six.wraps(f)
        def _inner(self, request, *args, **kwargs):
            project_id = request.session.get("project_id", request.COOKIES.get("project_id"))
            account_id = request.session.get("account_id", request.COOKIES.get("account_id"))
            region = request.session.get('region', env_config.region_name)
            response = f(self, request, *args, **kwargs)
            try:
                user = get_userinfo_by_id(account_id)
                res_data = json.loads(response.content.decode(encoding='UTF-8', errors='strict'))

                contract_number = None
                order_info = request.param_info.get("order_info", {})
                if order_info:
                    contract_number = order_info.get("contract_number")

                if res_data.get('no') == 200 and res_data.get('is_ok'):
                    content = res_data.get('content')

                    if content:
                        for resource in content:
                            resource_id = resource.get(resource_id_key)
                            resource_name = resource.get(resource_name_key)
                            if not contract_number:
                                contract_number = resource.get("contract_number")
                            timestamp = str(datetime.datetime.now().timestamp())
                            get_cloud_log_notification().send(region=region, project_id=project_id, user_id=account_id,
                                                              service_type=service_type, resource_id=resource_id,
                                                              resource_name=resource_name, resource_type=resource_type,
                                                              contract_number=contract_number, time=timestamp,
                                                              trace_name=trace_name, trace_type=trace_type,
                                                              source_ip=None,
                                                              request=jsonpickle.dumps(request.param_info),
                                                              response=jsonpickle.dumps(res_data), event_type=event_type,
                                                              code=res_data.get('no', 200), user=user
                                                              )
                else:
                    timestamp = str(datetime.datetime.now().timestamp())
                    get_cloud_log_notification().send(region=region, project_id=project_id, user_id=account_id,
                                                      service_type=service_type, resource_type=resource_type,
                                                      contract_number=contract_number, time=timestamp,
                                                      trace_name=trace_name, trace_type=trace_type, source_ip=None,
                                                      request=jsonpickle.dumps(request.param_info),
                                                      response=jsonpickle.dumps(res_data),
                                                      event_type=event_type, code=res_data.get('no', 400),
                                                      user=user)
            except Exception as e:
                LOG.exception("Send notification error %s", str(e))
            return response

        return _inner

    return outer


def send_cloud_log_notification(region=env_config.region_name, project_id=None, user_id=None, service_type=None,
                                resource_id=None, resource_name=None, resource_type=None, contract_number=None,
                                trace_name=None, trace_type=audit_types.CONSOLEACTION, source_ip=None, request=None, response=None, code=200,
                                event_type=audit_types.NATIONAL, ):
    try:
        user = None
        if user_id:
            user = get_userinfo_by_id(user_id)

        timestamp = str(datetime.datetime.now().timestamp())
        if request and not isinstance(request, six.string_types):
            request = jsonpickle.dumps(request)
        if response and not isinstance(response, six.string_types):
            response = jsonpickle.dumps(response)

        get_cloud_log_notification().send(region=region, project_id=project_id, user_id=user_id,
                                          service_type=service_type, resource_id=resource_id,
                                          resource_name=resource_name, resource_type=resource_type,
                                          contract_number=contract_number, time=timestamp,
                                          trace_name=trace_name, trace_type=trace_type, source_ip=source_ip,
                                          request=request, response=response,
                                          event_type=event_type, code=code, user=user)
    except Exception as e:
        LOG.exception("Send notification error %s", str(e))
