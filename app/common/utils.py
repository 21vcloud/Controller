# -*- coding: utf-8 -*-
from functools import wraps
import jsonpickle
import logging
import six

from keystoneauth1 import exceptions as keystone_exceptions
from openstack import exceptions as openstack_exceptions

from account.repository import auth_models as auth_models
from common import exceptions
from common.lark_common.model.common_model import ResponseObj
from common.openstack import context
# from account.repository.auth_models import BmRequestInfo


LOG = logging.getLogger(__name__)
REQUEST_INFO_LOGGER = logging.getLogger("request_info")


def param_info(func):
    @wraps(func)
    def _inner(self, request, *args, **kwargs):
        LOG.info("Request function: %s " % func.__name__)
        LOG.info("Start to decrypt request param info!")
        try:

            if request.method == "POST" or request.method == 'PUT' or request.method == 'DELETE':
                if request.data.get("aesRequest"):
                    REQUEST_INFO_LOGGER.info("encrypt param info : %s" % request.data)
                    request.param_info = self.aes_cipher.decrypt(request.data.get("aesRequest"))
                else:
                    REQUEST_INFO_LOGGER.info("encrypt param info : %s" % request.data)
                    request.param_info = request.data
            elif request.method == "GET":
                REQUEST_INFO_LOGGER.info("encrypt param info : %s" % request.GET)
                request.param_info = request.GET
            else:
                request.param_info = {}
        except Exception as ex:
            response_obj = ResponseObj()
            LOG.error(response_obj.message)
            return response_obj.json_exception_serial(user_info="Failed to decrypt !",
                                                      admin_info=ex,
                                                      no=500)
        REQUEST_INFO_LOGGER.info("decrypt param info : %s" % request.param_info)
        LOG.info("Success to decrypt request param info !")
        # try:
        #     request_param = {
        #         "request_user": request.session.get("username"),
        #         "request_method": request.method,
        #         "request_url": request._current_scheme_host+request.path,
        #         "request_param": request.param_info,
        #         "reqeust_info": request
        #     }
        #     BmRequestInfo.objects.create(**request_param)
        # except Exception as ex:
        #     self.logger.error("fail ot record request info %s" % str(ex))

        # Check project status
        project_id = request.session.get('project_id', request.COOKIES.get("project_id"))

        if project_id:
            project_result = auth_models.BmProject.objects.filter(id=project_id, status='active').first()
            if not project_result:
                response_obj = ResponseObj()
                return response_obj.json_exception_serial(user_info="项目不存在，请联系管理员",
                                                          admin_info="project not exist",
                                                          no=404)

        LOG.info("Start to deal with function: %s !" % func.__name__)
        return func(self, request, *args, **kwargs)
    return _inner


def get_openstack_client(request, auth_plugin=None):
    openstack_client = context.get_openstack_client_from_session(request, auth_plugin=auth_plugin)
    if not openstack_client:
        raise exceptions.SessionNotFound()
    return openstack_client


def get_admin_client(project='admin'):
    admin_client = context.get_openstack_admin_client(project_name=project)
    if not admin_client:
        raise exceptions.SessionNotFound()
    return admin_client


def request_to_openstack(client, request, response, method, resource, *args, **kwargs):
    func = getattr(client, method, None)
    if not func:
        raise exceptions.MethodNotFound(method=method)
    try:
        result = func(*args, **kwargs)

    except openstack_exceptions.ConflictException as e:

        user_info = "Resource %(resource)s  %(name)s has been created", {'resource': resource,
                                                                         'name': kwargs.get('name')}
        LOG.info(user_info)
        raise e
    except Exception as e:
        raise e
    return result


def check_instance_state(vm_state=None, task_state=(None,),
                         must_have_launched=True):
    """Decorator to check VM and/or task state before entry to API functions.

    If the instance is in the wrong state, or has not been successfully
    started at least once the wrapper will raise an exception.
    """

    if vm_state is not None and not isinstance(vm_state, set):
        vm_state = set(vm_state)
    if task_state is not None and not isinstance(task_state, set):
        task_state = set(task_state)

    def outer(f):
        @six.wraps(f)
        def inner(instance, *args, **kw):
            if vm_state is not None and instance.vm_state not in vm_state:
                raise exceptions.InstanceInvalidState(
                    attr='vm_state',
                    instance_uuid=instance.id,
                    state=instance.vm_state,
                    method=f.__name__)
            if (task_state is not None and
                    instance.task_state not in task_state):
                raise exceptions.InstanceInvalidState(
                    attr='task_state',
                    instance_uuid=instance.id,
                    state=instance.task_state,
                    method=f.__name__)
            if must_have_launched and not instance.launched_at:
                raise exceptions.InstanceInvalidState(
                    attr='launched_at',
                    instance_uuid=instance.id,
                    state=instance.launched_at,
                    method=f.__name__)

            return f(instance, *args, **kw)
        return inner
    return outer


def check_invalid_kwargs_with_normal_user(invalid_args):
    """Check role limit with request param info"""

    def outer(f):
        @six.wraps(f)
        def inner(self, request,):
            # get role
            if int(request.session.get('role_limit', 10)) < 30:

                invalid_param = set(request.param_info.keys()) & set(invalid_args)
                if invalid_param:
                    print(invalid_param)
                    # raise exceptions.InVaildRequest(param=invalid_param)
            return f(self, request)
        return inner
    return outer


def check_request_params(allowed_params):
    """
    Check request params if in allowsd_params
    只能在django views类中使用
    必须在装饰器@param_info 后使用


    :param allowed_params: An request allowed params in this

    """
    def outer(f):
        @six.wraps(f)
        def _inner(self, request, *args, **kwargs):
            invalid_param = set(request.param_info.keys()) - set(allowed_params)
            if invalid_param:
                response_obj = ResponseObj()
                error_msg = "Invalid request params %s", invalid_param
                LOG.error(error_msg)
                return response_obj.json_exception_serial(user_info="错误的请求参数",
                                                          admin_info=error_msg,
                                                          no=500)
            return f(self, request, *args, **kwargs)
        return _inner
    return outer
