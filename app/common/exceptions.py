# -*- coding: utf-8 -*-
import logging
import six
from six import reraise as raise_
import sys

_FATAL_EXCEPTION_FORMAT_ERRORS = False
LOG = logging.getLogger(__name__)


class BaremetalConsoleLogException(Exception):
    """Base CloudLog Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."

    def __init__(self, **kwargs):
        self.kwargs = kwargs

        try:
            self.message = self.msg_fmt % kwargs
            LOG.error(self.message)
        except KeyError:
            exc_info = sys.exc_info()
            # kwargs doesn't match a variable in the message
            # log the issue and the kwargs
            LOG.exception('Exception in string format operation')
            for name, value in six.iteritems(kwargs):
                LOG.error("%(name)s: %(value)s",
                          {'name': name, 'value': value})  # noqa

            if _FATAL_EXCEPTION_FORMAT_ERRORS:
                raise_(exc_info[0], exc_info[1], exc_info[2])

    def __str__(self):
        return self.message

    def __deepcopy__(self, memo):
        return self.__class__(**self.kwargs)


class MethodNotFound(BaremetalConsoleLogException):
    msg_fmt = "OpenstackSdk Can't found Method %(method)s"


class ConflictException(BaremetalConsoleLogException):
    msg_fmt = "Resource %(resource)s  %(name)s has been created"


class GuestAgentTopicNotFound(BaremetalConsoleLogException):
    msg_fmt = "Guest Agent topic Can't found"


class ProtocolNotSupported(BaremetalConsoleLogException):
    msg_fmt = "Volume Protocol Not Support!"


class InstanceInvalidState(BaremetalConsoleLogException):
    msg_fmt = "Instance %(instance_uuid)s in %(attr)s %(state)s." \
              " Cannot %(method)s while the instance is in this state!"


class VolumeInvalidState(BaremetalConsoleLogException):
    msg_fmt = "Volume status in %(state)s"


class NoAttachmentsFound(BaremetalConsoleLogException):
    msg_fmt = "There were no attachments found for %(volume_id)s"


class NeedAttachmentUUID(BaremetalConsoleLogException):
    msg_fmt = "Volume %(volume_id)s has more than one attachment " \
              "Please pass in the attachment_uuid you wish to detach."


class SessionNotFound(BaremetalConsoleLogException):
    msg_fmt = "Session Cannot found maybe has expired."


class ProjectInvaildState(BaremetalConsoleLogException):
    msg_fmt = 'Project id not match openstack returned.'


class VpcNetworkUpdateError(BaremetalConsoleLogException):
    msg_fmt = 'Vpc Network update error. Reason %(reason)s.'


class VpcSubnetUpdateError(BaremetalConsoleLogException):
    msg_fmt = 'Vpc Subnet update error. Reason %(reason)s.'


class NetworkInUse(BaremetalConsoleLogException):
    msg_fmt = 'Unable to complete operation on network %(net_id)s. ' \
              'There are one or more ports still in use on the network. '


class InVaildRequest(BaremetalConsoleLogException):
    msg_fmt = "Invaild request with param %(param)s."


class ExternalNetworkNotFound(BaremetalConsoleLogException):
    msg_fmt = "External network not found"


class FirewallInUse(BaremetalConsoleLogException):
    msg_fmt = 'Unable to complete operation on Firewall %(firewall_id)s. ' \
              'There are one or more floatingip still in use on the network. '


class ContainserAlreadyExists(BaremetalConsoleLogException):
    msg_fmt = 'Container %(name)s alreadyexist'


class ObjectAlreadyExist(BaremetalConsoleLogException):
    msg_fmt = '%(model)s %(name)salready exist'


class VolumeSizeQuotaError(BaremetalConsoleLogException):
    msg_fmt = 'Volume cannot be created as you only have %(avail)iGiB of ' \
              'your quota available.'


class VolumeCountQuotaError(BaremetalConsoleLogException):
    msg_fmt = 'Volume cannot be created as you only have %(count)s of your quota available'


class VolumeTypeInvalid(BaremetalConsoleLogException):
    msg_fmt = 'Volume type Error!'


class QuotaError(BaremetalConsoleLogException):
    msg_fmt = 'Quota Error, available count %(count)s'


class PoolResourceError(BaremetalConsoleLogException):
    msg_fmt = "Pool resource ERROR!"


class TimeoutError(BaremetalConsoleLogException):
    msg_fmt = 'Request resource timeout!'


class LbError(BaremetalConsoleLogException):
    msg_fmt = 'LoadBalance status is Error! Unable to operate!'


class ListenerError(BaremetalConsoleLogException):
    msg_fmt = 'Failed to get listener data!'


class PoolError(BaremetalConsoleLogException):
    msg_fmt = 'Failed to create a pool!'


class HealthmonitorError(BaremetalConsoleLogException):
    msg_fmt = 'Failed to get healthmonitor data!'


class NatGateWayNotFound(BaremetalConsoleLogException):
    msg_fmt = "Nat gateway %(nat_gateway_id)s not found"


class NatGatewayRuleExist(BaremetalConsoleLogException):
    mst_fmt = "Nat gateway %(nat_gateway_id)s has rules"


class NatRuleNotFound(BaremetalConsoleLogException):
    msg_fmt = "Nat rule %(nat_rule_id)s not found"


class SharedBandWidthError(BaremetalConsoleLogException):
    msg_fmt = "Shared Bandwidth %(name)s driver error!"


class DataIntoSqlError(BaremetalConsoleLogException):
    msg_fmt = "Data creation failed!"

class FormatError(BaremetalConsoleLogException):
    msg_fmt = "Supplied cookie_name is invalid !"

class L7PolicyError(BaremetalConsoleLogException):
    msg_fmt = "This listener has l7Policies. Cannot be deleted!"

class L7PolicyCreateProtocolError(BaremetalConsoleLogException):
    msg_fmt = "Failed to create l7Policy: Invalid Pool! A HTTP listener with a HTTP pool, and a HTTPS listener with a HTTPS pool!"

class L7RuleCreateError(BaremetalConsoleLogException):
    msg_fmt = "Failed to create l7Rule!"

class HealthMonitorUrlError(BaremetalConsoleLogException):
    msg_fmt = "Invalid url path of the HTTP Health Monitor!"
