# -*- coding: utf-8 -*-

from keystoneauth1 import session as _session
from keystoneauth1.identity import v3


DEFAULT_USER_AGENT = '21vianet'


def ksa_session(auth_url, project_id=None, auth_ref=None, auth=None, **kwargs):
    if not auth:
        auth = _create_authenticator(auth_url=auth_url,
                                     project_id=project_id,
                                     **kwargs)
    auth.auth_ref = auth_ref
    return _session.Session(auth=auth, user_agent=DEFAULT_USER_AGENT)


def _create_authenticator(**auth_args):
    auth_url = auth_args.get('auth_url')
    if auth_url:
        if 'password' in auth_args:
            return v3.Password(**auth_args)

        if 'token' in auth_args:
            return v3.Token(**auth_args)


