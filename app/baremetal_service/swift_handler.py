# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import functools
import swiftclient
from keystoneauth1 import exceptions as keystone_exceptions
import six.moves.urllib.parse as urlparse

from BareMetalControllerBackend.conf.env import env_config
from common import exceptions as exc
from common import utils


GLOBAL_READ_ACL = ".r:*"
LIST_CONTENTS_ACL = ".rlistings"
FOLDER_DELIMITER = "/"
CHUNK_SIZE = 512*1024
OBJECT_ENDPOINT = env_config.object_endpoint


def utctime_to_localtime(utc, utc_format='%Y-%m-%dT%H:%M:%S.%fZ'):
    if not utc:
        return None
    utc_time = datetime.strptime(utc, utc_format)
    local_time = utc_time + timedelta(hours=8)
    return local_time.strftime("%Y-%m-%d %H:%M:%S")


class APIDictWrapper(object):
    """Simple wrapper for api dictionaries

    Some api calls return dictionaries.  This class provides identical
    behavior as APIResourceWrapper, except that it will also behave as a
    dictionary, in addition to attribute accesses.

    Attribute access is the preferred method of access, to be
    consistent with api resource objects from novaclient.
    """

    _apidict = {}  # Make sure _apidict is there even in __init__.

    def __init__(self, apidict):
        self._apidict = apidict

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            if attr not in self._apidict:
                raise
            return self._apidict[attr]

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except (AttributeError, TypeError) as e:
            # caller is expecting a KeyError
            raise KeyError(e)

    def __contains__(self, item):
        try:
            return hasattr(self, item)
        except TypeError:
            return False

    def get(self, item, default=None):
        try:
            return getattr(self, item)
        except (AttributeError, TypeError):
            return default

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self._apidict)

    def to_dict(self):
        return self._apidict


class Container(APIDictWrapper):
    pass


class PseudoFolder(APIDictWrapper):
    def __init__(self, apidict, container_name):
        super(PseudoFolder, self).__init__(apidict)
        self.container_name = container_name

    @property
    def id(self):
        return '%s/%s' % (self.container_name, self.name)

    @property
    def name(self):
        return self.subdir.rstrip(FOLDER_DELIMITER)

    @property
    def bytes(self):
        return 0

    @property
    def content_type(self):
        return "application/pseudo-folder"


class StorageObject(APIDictWrapper):
    def __init__(self, apidict, container_name, orig_name=None, data=None):
        super(StorageObject, self).__init__(apidict)
        self.container_name = container_name
        self.orig_name = orig_name
        self.data = data

    @property
    def id(self):
        return self.name


def safe_swift_exception(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except swiftclient.client.ClientException as e:
            e.http_scheme = e.http_host = e.http_port = ''
            raise e

    return wrapper


def _objectify(items, container_name):
    """Splits a listing of objects into their appropriate wrapper classes."""
    objects = []

    # Deal with objects and object pseudo-folders first, save subdirs for later
    for item in items:
        if item.get("subdir", None) is not None:
            object_cls = PseudoFolder
        else:
            object_cls = StorageObject

        objects.append(object_cls(item, container_name))

    return objects


def _metadata_to_header(metadata):
    headers = {}
    public = metadata.get('is_public')

    if public is True:
        public_container_acls = [GLOBAL_READ_ACL, LIST_CONTENTS_ACL]
        headers['x-container-read'] = ",".join(public_container_acls)
    elif public is False:
        headers['x-container-read'] = ""

    return headers


class ObjectClientProvider(object):

    def __init__(self, request):
        try:
            self.openstack_client = utils.get_openstack_client(request)
            self.swift_client = swiftclient.client.Connection(session=self.openstack_client.session)
        except keystone_exceptions.NotFound:
            # Maybe token has expired,Get client use password
            openstack_client = utils.get_openstack_client(request, auth_plugin='password')
            self.swift_client = swiftclient.client.Connection(session=self.openstack_client.session)
        else:
            if not self.swift_client:
                raise exc.SessionNotFound()
        self.region = request.session.get('region', 'regionOne')

    def swift_container_exist(self, container_name):
        try:
            self.swift_client.head_container(container_name)
            return True
        except swiftclient.client.ClientException:
            return False

    def swift_object_exists(self, container_name, object_name):
        try:
            self.swift_client.head_object(container_name, object_name)
            return True
        except swiftclient.client.ClientException:
            return False

    @safe_swift_exception
    def swift_create_container(self, container_name, metadata):
        if self.swift_container_exist(container_name):
            raise exc.ContainserAlreadyExists(name=container_name)
        headers = _metadata_to_header(metadata or {})
        self.swift_client.put_container(container_name, headers=headers)
        new_headers = self.swift_client.head_container(container_name)
        public_url = None
        if metadata.get('is_public'):
            parameters = urlparse.quote(container_name.encode('utf8'))
            public_url = OBJECT_ENDPOINT.get('regionOne') + '/' + parameters
        ts_float = float(new_headers.get('x-timestamp'))
        timestamp = datetime.utcfromtimestamp(ts_float).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        container_info = {
            'name': container_name,
            'container_object_count': new_headers.get('x-container-object-count'),
            'container_bytes_used': new_headers.get('x-container-bytes-used'),
            'timestamp': utctime_to_localtime(timestamp),
            'is_public': metadata.get('is_public'),
            'public_url': public_url,
        }
        return Container(container_info)


    @safe_swift_exception
    def swift_get_containers(self):
        headers, containers = self.swift_client.get_account(full_listing=True)

        container_objs = []
        for c in containers:
            container = self.swift_get_container(c['name'])

            container_objs.append(container)

        return container_objs

    @safe_swift_exception
    def swift_get_container(self, container_name,):
        headers = self.swift_client.head_container(container_name)

        timestamp = None
        is_public = False
        public_url = None
        try:
            is_public = GLOBAL_READ_ACL in headers.get('x-container-read', '')
            parameters = urlparse.quote(container_name.encode('utf8'))
            if is_public:
                public_url = OBJECT_ENDPOINT.get('regionOne') + '/' + parameters
            ts_float = float(headers.get('x-timestamp'))
            timestamp = datetime.utcfromtimestamp(ts_float).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except Exception:
            pass
        container_info = {
            'name': container_name,
            'container_object_count': headers.get('x-container-object-count'),
            'container_bytes_used': headers.get('x-container-bytes-used'),
            'timestamp': utctime_to_localtime(timestamp),
            'is_public': is_public,
            'public_url': public_url,
        }
        return Container(container_info)

    @safe_swift_exception
    def swift_delete_container(self, container_name):
        self.swift_client.delete_container(container_name)

    @safe_swift_exception
    def swift_update_container(self, container_name, metadata=None):
        headers = _metadata_to_header(metadata or {})
        self.swift_client.post_container(container_name, headers=headers)
        new_headers = self.swift_client.head_container(container_name)
        public_url = None
        if metadata.get('is_public'):
            parameters = urlparse.quote(container_name.encode('utf8'))
            public_url = OBJECT_ENDPOINT.get('regionOne') + '/' + parameters
        ts_float = float(new_headers.get('x-timestamp'))
        timestamp = datetime.utcfromtimestamp(ts_float).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        container_info = {
            'name': container_name,
            'container_object_count': new_headers.get('x-container-object-count'),
            'container_bytes_used': new_headers.get('x-container-bytes-used'),
            'timestamp': utctime_to_localtime(timestamp),
            'is_public': metadata.get('is_public'),
            'public_url': public_url,
        }
        return Container(container_info)

    @safe_swift_exception
    def swift_get_objects(self, container_name, prefix=None, path=None):
        kwargs = dict(prefix=prefix,
                      delimiter=FOLDER_DELIMITER,
                      full_listing=True)
        headers, objects = self.swift_client.get_container(container_name, **kwargs)

        object_objs = _objectify(objects, container_name)

        contents = [{
            'path': o.subdir if isinstance(o, PseudoFolder) else o.name,
            'name': o.name.split('/')[-1],
            'bytes': o.bytes,
            'is_subdir': isinstance(o, PseudoFolder),
            'is_object': not isinstance(o, PseudoFolder),
            'content_type': getattr(o, 'content_type', None),
            'timestamp': utctime_to_localtime(getattr(o, 'last_modified', None)),
        } for o in object_objs if o.name != path]

        return contents

    @safe_swift_exception
    def swift_create_pseudo_folder(self, container_name, pseudo_folder_name):
        if self.swift_object_exists(container_name, pseudo_folder_name):
            name =pseudo_folder_name.strip('/')
            raise exc.ObjectAlreadyExist(model='folder', name=name)
        headers = {}
        etag = self.swift_client.put_object(container_name,
                                            pseudo_folder_name,
                                            None,
                                            headers=headers)
        obj_info = {
            'name': pseudo_folder_name.strip('/'),
            'etag': etag,
            'is_subdir': True,
            'is_object': False,
            'content_type': 'application/pseudo-folder',
            'path': pseudo_folder_name
        }

        return PseudoFolder(obj_info, container_name)

    @safe_swift_exception
    def swift_delete_object(self, container_name, object_name):
        self.swift_client.delete_object(container_name, object_name)
        return True

    @safe_swift_exception
    def swift_get_object(self, container_name, object_name, with_data=True,
                     resp_chunk_size=CHUNK_SIZE):
        if with_data:
            headers, data = self.swift_client.get_object(
                container_name, object_name, resp_chunk_size=resp_chunk_size)
        else:
            data = None
            headers = self.swift_client.head_object(container_name,
                                                     object_name)
        orig_name = headers.get("x-object-meta-orig-filename")
        timestamp = None
        try:
            ts_float = float(headers.get('x-timestamp'))
            timestamp = datetime.utcfromtimestamp(ts_float).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except Exception:
            pass
        obj_info = {
            'name': object_name,
            'bytes': headers.get('content-length'),
            'content_type': headers.get('content-type'),
            'etag': headers.get('etag'),
            'timestamp': utctime_to_localtime(timestamp),
        }
        return StorageObject(obj_info,
                             container_name,
                             orig_name=orig_name,
                             data=data)

    @safe_swift_exception
    def swift_delete_folder(self, container_name, object_name):
        objects = self.swift_get_objects(container_name, prefix=object_name)
        for object in objects:
            self.swift_client.delete_object(container_name, object.get('path'))

    @safe_swift_exception
    def swift_upload_object(self, container_name, object_name,
                            object_file=None):
        headers = {}
        size = 0
        if object_file:
            headers['X-Object-Meta-Orig-Filename'] = object_file.name
            size = object_file.size
        if not object_name:
            object_name = object_file.name
        if object_name[-1] == '/':
            object_name = object_name + object_file.name
        etag = self.swift_client.put_object(container_name,
                                            object_name,
                                            object_file,
                                            content_length=size,
                                            headers=headers)
        object = self.swift_get_object(container_name, object_name, with_data=False)
        result = object.to_dict()
        result['path'] = object_name
        return result

    @safe_swift_exception
    def swift_copy_object(self, orig_container_name, orig_object_name,
                          new_container_name, new_object_name):
        if self.swift_object_exists(new_container_name, new_object_name):
            raise exc.ObjectAlreadyExist(model='object', name=new_object_name)

        headers = {"X-Copy-From": FOLDER_DELIMITER.join([orig_container_name,
                                                         orig_object_name])}
        etag = self.swift_client.put_object(new_container_name,
                                            new_object_name,
                                            None,
                                            headers=headers)

        obj_info = {'name': new_object_name, 'etag': etag}
        return StorageObject(obj_info, new_container_name)