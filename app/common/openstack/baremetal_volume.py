# -*- coding: utf-8 -*-
import logging

from openstack import exceptions as openstack_exception
from cinderclient import client as volume_client
from cinderclient import exceptions as cinder_exception
import oslo_messaging
from oslo_config import cfg

from BareMetalControllerBackend.conf.env import env_config
from common import exceptions as exc
from common import utils


LOG = logging.getLogger(__name__)

DEFAULT_URL = None
TRANSPORTS = {}


def get_transport(url, optional=False, cache=True, exchange='vianet_guest'):
    global TRANSPORTS, DEFAULT_URL
    cache_key = url or DEFAULT_URL
    cache_key = '%s_%s' % (cache_key, exchange)
    transport = TRANSPORTS.get(cache_key)
    if not transport or not cache:
        try:
            oslo_messaging.set_transport_defaults(exchange)
            transport = oslo_messaging.get_transport(cfg.CONF, url)
        except (oslo_messaging.InvalidTransportURL,
                oslo_messaging.DriverLoadFailure):
            if not optional or url:
                # NOTE(sileht): oslo_messaging is configured but unloadable
                # so reraise the exception
                raise
            return None
        else:
            if cache:
                TRANSPORTS[cache_key] = transport
    return transport


class BaremetalGuestApi(object):
    def __init__(self, topic):
        self.topic = topic
        transport = get_transport(env_config.guest_transport_url,
                                       exchange=env_config.guest_exchange)
        target = oslo_messaging.Target(exchange=env_config.guest_exchange,
                                       server=self.topic,
                                       topic=self.topic)
        self.client = oslo_messaging.RPCClient(transport, target)

    def get_guest_connector(self):
        ctxt = {}
        return self.client.call(ctxt, method='get_guest_connector')

    def guest_connect_volume(self, attachments):
        """
        Rpc client to guest
        :param attachments: cinder attachments
        :return:
        """
        ctxt = {}
        connection = attachments['connection_info']
        return self.client.call(ctxt, method='guest_connect_volume',
                                connection=connection)

    def guest_deconnect_volume(self, attachments):
        ctxt = {}
        connection = attachments['connection_info']
        return self.client.call(ctxt, method='guest_deconnect_volume',
                                connection=connection)


@utils.check_instance_state(vm_state=['active'])
def baremetal_attach_volume(server, volume, openstack_client):
    """
    Baremetal attach volume
    :param openstack_client: openstack client
    :param server: the server object get by server id
    :param volume: volume object get by volume id
    :return: attachments
    """
    if volume.status != 'available':
        raise exc.VolumeInvalidState(state=volume.status)
    guest_id = server.metadata.get('guest_id')
    if not guest_id:
        raise exc.GuestAgentTopicNotFound
    guest_client = BaremetalGuestApi(guest_id)
    connector_properties = guest_client.get_guest_connector()

    server_id = server.id
    volume_id = volume.id
    cinder = volume_client.Client('3.44', session=openstack_client.session)
    info = cinder.attachments.create(volume_id, connector_properties, server_id)
    try:
        connection = info['connection_info']
        # now we only support ISCSI
        if connection['driver_volume_type'].lower() != 'iscsi':
            raise exc.ProtocolNotSupported
        device_info = guest_client.guest_connect_volume(info)
        cinder.attachments.complete(info['connection_info']['attachment_id'])
        return device_info
    except Exception as e:
        attachment_id = info.get('connection_info').get('attachment_id')
        cinder.attachments.delete(attachment_id)
        raise e


@utils.check_instance_state(vm_state=['active'])
def baremetal_detach_volume(server, volume_id, openstack_client, attachment_uuid=None):
    """
    Baremetal detach volume
    :param openstack_client: openstack client
    :param server: the server object get by server id
    :param volume: volume id
    :return: attachments
    """
    guest_id = server.metadata.get('guest_id')
    if not guest_id:
        raise exc.GuestAgentTopicNotFound
    guest_client = BaremetalGuestApi(guest_id)

    server_id = server.id

    cinder = volume_client.Client('3.44', session=openstack_client.session)
    if not attachment_uuid:
        # We need the specific attachment uuid to know which one to detach.
        # if None was passed in we can only work if there is one and only
        # one attachment for the volume.
        # Get the list of attachments for the volume.
        search_opts = {'volume_id': volume_id}
        attachments = cinder.attachments.list(search_opts=search_opts)
        if len(attachments) == 0:
            raise exc.NoAttachmentsFound(volume_id=volume_id)
        if len(attachments) == 1:
            attachment_uuid = attachments[0].id
        else:
            # We have more than 1 attachment and we don't know which to use
            raise exc.NeedAttachmentUUID(volume_id=volume_id)

    attachment = cinder.attachments.show(attachment_uuid)
    guest_client.guest_deconnect_volume(attachment.to_dict())
    cinder.attachments.delete(attachment_uuid)


def volume_backup_restore(openstack_client, backup_id, volume_id=None, volume_name=None):
    cinder = volume_client.Client('3.44', session=openstack_client.session)
    backups = cinder.restores.restore(backup_id, volume_id, volume_name)
    return backups


def volume_extend(openstack_client, volume_id, new_size):
    try:
        cinder = volume_client.Client('2', session=openstack_client.session)
        volume = cinder.volumes.extend(volume_id, new_size)
        return volume
    except cinder_exception.OverLimit as e:
        raise openstack_exception.HttpException(details=e.message)