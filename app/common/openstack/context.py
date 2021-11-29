# -*- coding: utf-8 -*-

from werkzeug.local import Local as local
from importlib import import_module

from keystoneauth1 import exceptions as keysteone_exceptions

from BareMetalControllerBackend.conf.env import env_config
from common.openstack import auth
from openstack import connection
from django.conf import settings

engine = import_module(settings.SESSION_ENGINE)
SessionStore = engine.SessionStore

_request_store = local()
identity_interface = 'public'
IDENTITY_INTERFACE = 'public'
COMPUTE_API_VERSION = '2.65'
VOLUME_API_VERSION = '3'


class RequestContext(object):
    """
    Stores information about the security context under which the user
    accesses the system, as well as additional request information.
    """

    def __init__(self, auth_url, project_id=None, region_name=None,
                 auth_ref=None, auth_plugin=None, bind_to_thread=None,
                 **kwargs):
        self.auth_url = auth_url
        self.region_name = region_name
        self.project_id = project_id
        self._auth_ref = None
        if auth_ref:
            # 当都使用keystoneauth1进行认证时，可传入，可以避免再次认证
            from keystoneauth1.access import AccessInfo
            if isinstance(auth_ref, AccessInfo):
                self._auth_ref = auth_ref
        self.kwargs = kwargs

        self.endpoint_type = 'publicURL'
        self._auth_plugin = auth_plugin
        self.auth_token_info = kwargs.get('auth_token_info')

        self.username = kwargs.get('username')
        self.password = kwargs.get('password')

        self._keystone_session = auth.ksa_session(self.auth_url,
                                                  auth_ref=self._auth_ref,
                                                  project_id=self.project_id,
                                                  auth=self._auth_plugin,
                                                  **self.kwargs)
        if bind_to_thread:
            self.update_store()

    def to_dict(self):
        return {
            'auth_url': self.auth_url,
            'auth_token': self.auth_token,

            'region': self.region_name,

            'domain': self.auth_ref.user_domain_id,
            'domain_id': self.auth_ref.user_domain_id,
            'domain_name': self.auth_ref.user_domain_name,

            'project_id': self.project_id,
            'tenant': self.project_id,
            'tenant_id': self.project_id,
            'project_name': self.auth_ref.project_name,

            'user_id': self.auth_ref.user_id,
            'username': self.auth_ref.username,

            'roles': self.auth_ref.role_names,
            'is_admin': self.is_admin,

            'transport_urls': self.transport_urls
        }

    @classmethod
    def from_dict(cls, values):
        return cls(**values)

    @property
    def is_admin(self):
        """Evaluates whether this user has admin privileges.

        Returns ``True`` or ``False``.
        """
        admin_roles = ['admin']
        user_roles = [role.lower() for role in self.auth_ref.role_names]
        return True if set(admin_roles).intersection(user_roles) else False

    @property
    def keystone_session(self):
        return self._keystone_session

    @property
    def auth_ref(self):
        if not self.keystone_session.auth.auth_ref:
            token = self.auth_token  # 触发认证
        return self.keystone_session.auth.auth_ref

    @property
    def auth_token(self):
        try:
            return self.keystone_session.get_token()
        except keysteone_exceptions.http.NotFound as e:
            e.http_status = 401
            raise e

    def update_store(self):
        if not self.auth_ref.domain_scoped:
            _request_store.project_context = self
        else:
            _request_store.domain_context = self


def get_openstack_client_from_session(request, auth_plugin=None):

    context = None
    project_name = request.session.get("project_name")
    project_domain_name = request.session.get("project_domain_name")
    user_domain_name = request.session.get("user_domain_name")
    username = request.session.get("username")
    password = request.session.get("password")
    region = request.session.get("region") or env_config.region_name
    token = request.session.get("token")
    if not project_name and request.COOKIES.get("project_name"):
        project_name = request.COOKIES.get("project_name")
        project_domain_name = request.COOKIES.get("project_domain_name")
        token = request.COOKIES.get("openstack_token")
        if not token:
            return None

    if token and not auth_plugin:
        context = RequestContext(auth_url=env_config.auth_url, project_name=project_name,
                                 token=token, project_domain_name=project_domain_name, )
    elif auth_plugin == 'password':

        context = RequestContext(auth_url=env_config.auth_url, username=username,
                                 password=password, project_name=project_name,
                                 project_domain_name=project_domain_name,
                                 user_domain_name=user_domain_name)
        request.session['token'] = context.auth_token
    admin_conn = connection.Connection(session=context.keystone_session,
                                       region_name=region,
                                       identity_interface=IDENTITY_INTERFACE,
                                       compute_api_version=COMPUTE_API_VERSION,
                                       volume_api_version=VOLUME_API_VERSION)
    return admin_conn


def get_openstack_admin_client(project_name='admin'):
    context = RequestContext(auth_url=env_config.auth_url, username=env_config.admin_user,
                             password=env_config.admin_password, project_name=project_name,
                             project_domain_name=env_config.project_domain_name,
                             user_domain_name=env_config.user_domain_name)
    admin_conn = connection.Connection(session=context.keystone_session,
                                       identity_interface=IDENTITY_INTERFACE,
                                       compute_api_version=COMPUTE_API_VERSION,
                                       volume_api_version=VOLUME_API_VERSION)
    return admin_conn
