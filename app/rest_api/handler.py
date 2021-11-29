# -*- coding: utf-8 -*-
import logging
import datetime

from openstack import exceptions as openstack_exc

from BareMetalControllerBackend.conf.env import env_config
from baremetal_service.repository import service_model as service_model
from baremetal_service.repository.service_provider import ServiceProvider, ServiceFloatingProvider, \
    ServiceVolumeProvider
from django.forms.models import model_to_dict
from django.db import transaction
from common import utils
from common import exceptions as exc
from celery_tasks import tasks

LOG = logging.getLogger(__name__)

SHUTOFF = 'SHUTOFF'
EXTEND_ORDER = 'extend_order'
DELETED = 'DELETED'
BUILDING = 'BUILD'
DEFAULT_VPC_TYPE = 'three_line_ip'
DEFAULT_VPC = "默认虚拟私有云"
DEFAULT_NET = '默认网络'
DEFAULT_CIDR = '192.168.0.0/24'
SUBNET_PREFIX = 'subnet_'
AUTO_DELETE_PORT = 'network:dhcp'
ROUTE_INTERFACE_PORT = ['network:router_interface',
                        'network:ha_router_replicated_interface',
                        'network:router_ha_interface']
EGRESS = 'egress'
INGRESS = 'ingress'
CONTRACT_INFO = "contract_info"


def interface_detach_single(openstack_client, server_id, port_id):
    openstack_client.compute.delete_server_interface(port_id, server_id)


def interface_detach_all(openstack_client, server_id):
    interfaceattachments = openstack_client.compute.server_interfaces(server_id)
    for interface_attach in interfaceattachments:
        openstack_client.compute.delete_server_interface(interface_attach, server_id)


def interface_attach(openstack_client, server_id, net_id):
    interfaceattachments = openstack_client.compute.create_server_interface(
        server_id, net_id=net_id)
    return interfaceattachments.to_dict()


def interface_list(openstack_client, server_id):
    interfaceattachments = openstack_client.compute.server_interfaces(server_id)
    return interfaceattachments


def get_bm_instances(project_id):
    bm_instances = service_model.BmServiceInstance.objects.filter(project_id=project_id).order_by("-create_at")
    return bm_instances


def delete_bm_instances(server_id_list):
    instances_obj = service_model.BmServiceInstance.objects.filter(uuid__in=server_id_list)
    update_result = instances_obj.update(**{"status": "DELETED", "deleted": True, "update_at": datetime.datetime.now()})
    machine_obj = service_model.BmServiceMachine.objects.filter(uuid__in=server_id_list)
    machine_obj.update(**{"status": "DELETED", "deleted": True, "update_at": datetime.datetime.now()})
    return update_result


def get_flavor_info():
    flavor_dict = {}
    flavor_info = service_model.BmServiceFlavor.objects.filter(status="active")
    for flavor in flavor_info:
        flavor_dict[flavor.openstack_flavor_name] = {
            "cpu": "%s-%s-%s" % (flavor.cpu_model, flavor.cpu_core, flavor.cpu_hz),
            "memory": flavor.ram,
            "disk": flavor.disk
        }
    return flavor_dict


def get_image_info():
    image_dict = {}
    image_info = service_model.BmServiceImages.objects.filter(status="active")
    for image in image_info:
        image_dict[image.id] = image.image_name
    return image_dict


def reserial_instance(instance, bm_instances_query, flavor_dict, image_dict):
    # if bm_instances:
    #     if instance.status == SHUTOFF and bm_instance.status == DELETED:
    #         return None
    #     else:
    #         return instance.setdefault(EXTEND_ORDER, model_to_dict(bm_instance))
    # else:
    #     return instance
    instance = instance.to_dict()
    instance[EXTEND_ORDER] = {}
    instance[CONTRACT_INFO] = {}
    for bm in bm_instances_query:
        if instance.get("id") == bm.uuid:
            if bm.status == DELETED and bm.deleted:
                LOG.info("ignore instance %s which status is deleted", bm.uuid)
                return None
            elif instance['status'] == 'ACTIVE' and bm.status == BUILDING:
                instance['status'] = BUILDING
            else:
                # 订单信息
                instance[EXTEND_ORDER] = model_to_dict(bm)

                # 合同信息
                contract_obj = service_model.BmContract.objects.filter(
                    contract_number=bm.contract_number, status="active").first()
                if contract_obj:
                    instance[CONTRACT_INFO] = model_to_dict(contract_obj)
                    return instance
    return instance


def soft_delete_instance(openstack_client, server_id_list):
    volume_provider = ServiceVolumeProvider()
    fip_provider = ServiceFloatingProvider()
    delete_result = {}

    server_dict = {}

    error_server_list = []
    instance_objs = openstack_client.compute.servers(details=True, status='ERROR')
    for instance in instance_objs:
        if instance.id in server_id_list:
            if instance.status == 'ERROR':
                openstack_client.compute.delete_server(instance.id)
                server_id_list.remove(instance.id)
                error_server_list.append(instance.id)
            server_dict[instance.id] = instance

    for server_id in server_id_list:
        update_result = openstack_client.compute.update_server(server=server_id,
                                                               **{"name": "%s-deleted" % server_id})
        volume_objects = service_model.BmServiceVolume.objects.filter(is_measure_end=False,
                                                                      instance_uuid=server_id)

        fip_objects = service_model.BmServiceFloatingIp.objects.filter(is_measure_end=False,
                                                                       instance_uuid=server_id)
        for fip in fip_objects:
            fip_provider.detach_ip_from_server(openstack_client, server_id, fip.floating_ip_id)

        for volume in volume_objects:
            volume_provider.detach_volume_from_server(openstack_client, volume.volume_id, server_id)

        interface_detach_all(openstack_client, server_id)
        stop_result = openstack_client.compute.stop_server(server=server_id)
        delete_result[server_id] = {"update_result": update_result, "stop_result": stop_result}
        delete_result[server_id] = True

    delete_bm_instances(error_server_list)
    result = delete_bm_instances(server_id_list)
    return result


def create_network(request, vpc_id, vpc_name=None, project_id=None, name=None,
                   cidr=None, enable_dhcp=True, gateway_ip=None, dns=None,
                   router_id=None):
    LOG.info("Create Vpc network in vpc %d", vpc_id)

    subnet_name = SUBNET_PREFIX + name

    if not router_id:
        router_id = service_model.Vpc.objects.get(id=vpc_id).router_id

    net = None
    subnet = None
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        with transaction.atomic():
            LOG.info("Create openstack network with %s with %s", name, project_id)
            net = openstack_client.create_network(name=name, project_id=project_id)

            subnet = openstack_client.create_subnet(net.id, cidr=cidr,
                                                    enable_dhcp=enable_dhcp,
                                                    subnet_name=subnet_name,
                                                    gateway_ip=gateway_ip,
                                                    dns_nameservers=dns,
                                                    tenant_id=project_id)
            net_object = service_model.Networks.objects.create(network_id=net.id,
                                                               name=name, cidr=cidr,
                                                               enable_dhcp=enable_dhcp,
                                                               gateway_ip=subnet.gateway_ip,
                                                               dns=subnet.dns_nameservers,
                                                               vpc_id=vpc_id, create_at=datetime.datetime.now())
            router_dict = {"id": router_id}
            openstack_client.add_router_interface(router_dict, subnet_id=subnet.id)

    except Exception as e:
        if net:
            openstack_client.delete_network(net.id)
        raise e
    else:

        return net_object.to_dict()


def create_vpc(request, region, vpc_type=None, project_id=None, vpc_name=None, vpc_status=None,
               net_name=None, cidr=None, enable_dhcp=True, gateway_ip=None, dns=None, ):
    # if create by create project
    if not vpc_name:
        vpc_name = DEFAULT_VPC
        net_name = DEFAULT_NET
        cidr = DEFAULT_CIDR
    if not vpc_type:
        vpc_type = DEFAULT_VPC_TYPE

    router = None
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        with transaction.atomic():
            ext_network = env_config.external_networks.get(region).get(vpc_type)[0]
            if not ext_network:
                raise exc.ExternalNetworkNotFound
            router = openstack_client.create_router(name=vpc_name, admin_state_up=True,
                                                    ext_gateway_net_id=ext_network.get('network_id'),
                                                    project_id=project_id)
            router_id = router.id
            vpc_name = vpc_name or DEFAULT_VPC
            status = 'ACTIVE'
            if project_id:
                if project_id == router.tenant_id:
                    project_id = project_id
                else:
                    raise exc.ProjectInvaildState()
            else:
                project_id = router.tenant_id
            vpc_obj = service_model.Vpc.objects.create(vpc_name=vpc_name, region=region,
                                                       project_id=project_id, status=status,
                                                       router_id=router_id, create_at=datetime.datetime.now())
    except Exception as e:
        if router:
            openstack_client.delete_router(router.id)
        raise e

    # create netwrok and subnet
    try:
        net = create_network(request, vpc_obj.id, vpc_name=vpc_obj.vpc_name, project_id=project_id,
                             name=net_name, cidr=cidr, enable_dhcp=enable_dhcp, gateway_ip=gateway_ip,
                             dns=dns)
    except Exception as e:
        service_model.Vpc.objects.filter(id=vpc_obj.id).delete()
        openstack_client.delete_router(router_id)
        raise e
    vpc = vpc_obj.to_dict()
    vpc['network'] = net
    return vpc


def subnet_list(request, project_id=None):
    router = None
    openstack_client = utils.get_openstack_client(request)

    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        with transaction.atomic():

            subnet_list = openstack_client.network.subnets(project_id=project_id)

    except Exception as e:
        if router:
            openstack_client.delete_router(router.id)
        raise e

    return subnet_list


def load_balance_list(request, project_id=None):
    router = None
    openstack_client = utils.get_openstack_client(request)

    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        # load_balances_generator = openstack_client.load_balancer.load_balancers(project_id=project_id, name="string1")
        load_balances_generator = openstack_client.load_balancer.load_balancers(project_id=project_id)
        load_balances=[]
        for load_balance_object in load_balances_generator:
            load_balances.append(load_balance_object.to_dict())

    except Exception as e:
        if router:
            openstack_client.delete_router(router.id)
        raise e

    return load_balances

def create_load_balancers(request, project_id=None, vip_subnet_id=None, name=None):
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        with transaction.atomic():
            load_balancer = openstack_client.load_balancer.create_load_balancer(project_id=project_id,
                                                                                vip_subnet_id=vip_subnet_id,
                                                                                name=name)
    except Exception as ex:
        raise ex
    return load_balancer

def show_load_balancers(request, project_id=None, loadbalancer_id=None, name=None, fields=None):
    router = None
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        load_balances_generator = openstack_client.load_balancer.load_balancers(project_id=project_id, name=name)
        load_balances = []
        for load_balance_object in load_balances_generator:
            load_balances.append(load_balance_object.to_dict())
    except Exception as e:
        if router:
            openstack_client.delete_router(router.id)
        raise e
    return load_balances

def delete_load_balancers(request, loadbalancer_id=None, cascade=None):
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        load_balancer = openstack_client.load_balancer.delete_load_balancer(loadbalancer_id=loadbalancer_id, cascade=cascade)
    except Exception as ex:
        raise ex

def update_load_balancers(request, loadbalancer=None, loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        load_balancer = openstack_client.load_balancer.update_load_balancer(loadbalancer=loadbalancer, loadbalancer_id=loadbalancer_id)
    except Exception as ex:
        raise ex
    return load_balancer

def get_load_balancers_statistics(request, loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        load_balancer = openstack_client.load_balancer.get_load_balancer_statistics(loadbalancer_id=loadbalancer_id)
    except Exception as ex:
        raise ex
    return load_balancer

def get_load_balancers_status_tree(request, loadbalancer_id=None):
    openstack_client = utils.get_openstack_client(request)
    if not openstack_client:
        raise exc.SessionNotFound()
    try:
        load_balancer = openstack_client.load_balancer.find_load_balancer(loadbalancer_id=loadbalancer_id)

    except Exception as ex:
        raise ex
    # return load_balancer


def delete_vpc(request, vpc_id):
    with transaction.atomic():
        vpc = service_model.Vpc.objects.get(id=vpc_id)
        openstack_client = utils.get_openstack_client(request)
        router = openstack_client.delete_router(vpc.router_id)
        vpc.delete()


def get_vpc_net_cidrs(vpc_id):
    vpc_cidrs = []
    cidrs = service_model.Vpc.objects.values('networks__cidr').filter(id=int(vpc_id))
    for cidr in cidrs:
        if cidr.get('networks__cidr'):
            vpc_cidrs.append(cidr.get('networks__cidr'))
    return vpc_cidrs


def reserial_vpcs(project_id=None, openstack_networks=None):
    openstack_netids = [net.id for net in openstack_networks]
    vpcs = []
    vpc_objects = service_model.Vpc.objects.filter(project_id=project_id).order_by('-create_at')
    if not project_id:
        vpc_objects = service_model.Vpc.objects.all()
    for vpc_object in vpc_objects:
        vpc = vpc_object.to_dict()
        networks = []
        networks_object = vpc_object.networks_set.all()
        for net in networks_object:
            if net.network_id in openstack_netids:
                networks.append(net.to_dict())
        vpc['networks'] = networks
        vpcs.append(vpc)
    return vpcs


def update_vpc_network(request, network_id, network_name=None, enalbe_dhcp=None, dns=None):
    """
    Update openstack network and subnet.
    update subnet name when network name change
    :param request:
    :param network_id:
    :param network_name:
    :param enalbe_dhcp:
    :param dns: ['8.8.8.8','114.114.114.114]
    :return:
    """

    subnet_name = None
    openstack_client = utils.get_openstack_client(request)
    try:
        with transaction.atomic():

            vpc_net = service_model.Networks.objects.get(network_id=network_id)
            net_kwargs = {}
            if network_name:
                vpc_net.name = network_name
                net_kwargs['name'] = network_name
                subnet_name = SUBNET_PREFIX + network_name
            try:

                net = openstack_client.update_network(network_id, **net_kwargs)
            except Exception as e:
                raise exc.VpcNetworkUpdateError(reason=e)
            try:
                subnet_id = net.subnets[0]
                subnet = openstack_client.update_subnet(subnet_id,
                                                        subnet_name=subnet_name,
                                                        enable_dhcp=enalbe_dhcp,
                                                        dns_nameservers=dns)
            except Exception as e:
                raise exc.VpcSubnetUpdateError(reason=e)
            vpc_net.enable_dhcp = subnet.enable_dhcp
            vpc_net.dns = subnet.dns_nameservers
            vpc_net.update_at = datetime.datetime.now()
            vpc_net.save()
    except Exception as e:
        LOG.error("update vpc network failed, Reason %s", e)
        raise e
    else:
        return vpc_net


def delete_vpc_network(request, network_id, vpc_id):
    openstack_client = utils.get_openstack_client(request)
    try:
        with transaction.atomic():
            vpc_net = service_model.Networks.objects.get(network_id=network_id)
            vpc_net_ports = openstack_client.list_ports(filters={"network_id": vpc_net.network_id})
            for port in vpc_net_ports:
                if port.device_owner not in [AUTO_DELETE_PORT] + ROUTE_INTERFACE_PORT:
                    raise exc.NetworkInUse(net_id=vpc_net.network_id)

            fixed_ips = vpc_net_ports[0].get('fixed_ips')
            subnet_ids = [item.get('subnet_id') for item in fixed_ips]
            if not subnet_ids:
                subnets = openstack_client.list_subnets(filters={"network_id": vpc_net.network_id})
                subnet_ids = [item.id for item in subnets]

            router_id = service_model.Vpc.objects.get(id=vpc_id).router_id
            router_dict = {"id": router_id}
            for subnet_id in subnet_ids:
                try:
                    openstack_client.remove_router_interface(router_dict, subnet_id=subnet_id)
                except openstack_exc.ResourceNotFound as ex:
                    LOG.info(ex)
                except Exception as e:
                    raise e
            openstack_client.delete_network(network_id)
            LOG.info("network %s has removed from openstack", network_id)
            vpc_net.delete()
    except Exception as ex:
        raise ex


class ResouceProvider(object):
    def __init__(self):
        pass

    def get_instance_count(self, project_id):
        instance_list_obj = service_model.BmServiceInstance.objects.filter(project_id=project_id).exclude(
            status__in=["deleted", "DELETED"])
        all_count = instance_list_obj.count()
        active_count = instance_list_obj.filter(status__in=["ACTIVE", "active"]).count()
        instance_count = {"all_count": all_count, "active_count": active_count}
        return instance_count

    def get_vpc_count(self, project_id):
        vpc_list_obj = service_model.Vpc.objects.filter(project_id=project_id).exclude(
            status__in=["deleted", "DELETED"])
        all_count = vpc_list_obj.count()
        return all_count

    def get_firewall_count(self, project_id):
        firewall_list_obj = service_model.Firewalls.objects.filter(project_id=project_id)
        all_count = firewall_list_obj.count()
        return all_count

    def get_volum_count(self, project_id):
        bm_service_volume_ojbects = service_model.BmServiceVolume.objects.filter(project_id=project_id,
                                                                                 is_measure_end=False)
        all_count = bm_service_volume_ojbects.count()
        return all_count

    def get_volum_backup_count(self, project_id):
        service_backup_objects = service_model.BmServiceVolumeBackup.objects.filter(project_id=project_id,
                                                                                    deleted=False, is_measure_end=False)
        all_count = service_backup_objects.count()
        return all_count

    # def get_key_value_pair_count(self, project_id):
    #     vpc_list_obj = service_model.Vpc.objects.filter(project_id=project_id).exclude(status__in=["deleted", "DELETED"])
    #     all_count = vpc_list_obj.count()
    #     return all_count


class FirewallProvider(object):

    def __init__(self):
        super(FirewallProvider).__init__()

    def check_firewall_exist(self, firewall_id):

        try:
            firewall = service_model.Firewalls.objects.get(id=firewall_id)
        except Exception as e:
            LOG.error("Error !check firewall %s if exist  %s", firewall_id, str(e))
            raise e
        return firewall

    def create_firewall(self, name=None, region=None, project_id=None, enabled=True,
                        description=None):
        if not name:
            name = "默认防火墙"

        firewall = service_model.Firewalls.objects.create(name=name, region=region,
                                                          project_id=project_id,
                                                          enabled=enabled,
                                                          description=description,
                                                          create_at=datetime.datetime.now())
        return firewall

    def create_default_egress_rule(self, firewall_id):
        firewall = self.check_firewall_exist(firewall_id)

        firewall_rule = service_model.FirewallRule.objects.create(firewall=firewall,
                                                                  direction=EGRESS,
                                                                  action='accept',
                                                                  protocol='any',
                                                                  remote_port="-",
                                                                  remote_ip='0.0.0.0/0',
                                                                  create_at=datetime.datetime.now())
        return [firewall_rule.to_dict()]

    def create_default_ingress_rule(self, firewall_id):

        firewall = self.check_firewall_exist(firewall_id)

        firewall_ssh_rule = service_model.FirewallRule.objects.create(firewall=firewall,
                                                                      direction=INGRESS,
                                                                      action='accept', protocol='tcp',
                                                                      remote_ip='0.0.0.0/0',
                                                                      remote_port='22',
                                                                      create_at=datetime.datetime.now())
        firewall_rdp_rule = service_model.FirewallRule.objects.create(firewall=firewall,
                                                                      direction=INGRESS,
                                                                      action='accept', protocol='tcp',
                                                                      remote_ip='0.0.0.0/0',
                                                                      remote_port='3389',
                                                                      create_at=datetime.datetime.now())

        return [firewall_ssh_rule.to_dict(), firewall_rdp_rule.to_dict()]

    def update_firewall(self, firewall_id, name, enabled, description):
        firewall = self.check_firewall_exist(firewall_id)
        firewall.name = name
        firewall.description = description
        firewall.enabled = enabled
        firewall.update_at = datetime.datetime.now()
        firewall.save()
        return firewall

    def delete_firewall(self, firewall_id):

        firewall = self.check_firewall_exist(firewall_id)

        firewall.delete()

    def create_firewall_rule(self, firewall_id, direction=None, action=None, protocol=None,
                             remote_ip=None, remote_port=None):

        firewall = self.check_firewall_exist(firewall_id)

        firewall_rule = service_model.FirewallRule.objects.create(firewall=firewall, direction=direction,
                                                                  action=action, protocol=protocol,
                                                                  remote_ip=remote_ip,
                                                                  remote_port=remote_port,
                                                                  create_at=datetime.datetime.now())

        if self.check_firewall_used(firewall_id):
            # Get floatingip with this firewallid
            floatingip_objects = service_model.BmFloatingipfirewallMapping.objects.filter(firewall_id=firewall_id)
            fips = [fip_object.floating_ip for fip_object in floatingip_objects]
            LOG.info("Add new firewall rule %s in Hardware firewall", firewall_rule.__dict__)
            tasks.add_firewall_rule.delay(fips, firewall.to_dict(), firewall_rule.to_dict())
        return firewall_rule

    def update_firewall_rule(self, firewall_id, firewall_rule_id,
                             direction=None, action=None, protocol=None,
                             remote_ip=None, remote_port=None):
        firewall = self.check_firewall_exist(firewall_id)
        firewall_rule = service_model.FirewallRule.objects.get(id=firewall_rule_id)
        if direction:
            firewall_rule.direction = direction
        if action:
            firewall_rule.action = action
        if protocol:
            firewall_rule.protocol = protocol
        if remote_ip:
            firewall_rule.remote_ip = remote_ip
        if remote_port:
            firewall_rule.remote_port = remote_port
        firewall_rule.update_at = datetime.datetime.now()
        firewall_rule.save()

        if self.check_firewall_used(firewall_id):
            # Get floatingip with this firewallid
            floatingip_objects = service_model.BmFloatingipfirewallMapping.objects.filter(firewall_id=firewall_id)
            fips = [fip_object.floating_ip for fip_object in floatingip_objects]
            LOG.info("Add new firewall rule %s in Hardware firewall", firewall_rule.__dict__)
            tasks.update_firewall_rule.delay(fips, firewall.to_dict(), firewall_rule.to_dict())

        # TODO 修改有floatingip情况下下发防火墙
        return firewall_rule

    def delete_firewall_rule(self, firewall_id, firewall_rule_id):
        firewall = self.check_firewall_exist(firewall_id)
        firewall_rule = service_model.FirewallRule.objects.get(id=firewall_rule_id)
        if self.check_firewall_used(firewall_id):
            tasks.remove_firewall_rule.delay(firewall.to_dict(), firewall_rule.to_dict())
        firewall_rule.delete()
        return firewall_rule

    def check_firewall_used(self, firewall_id):
        mappings = service_model.BmFloatingipfirewallMapping.objects.filter(firewall_id=firewall_id)
        if len(mappings) > 0:
            return True
        else:
            return False
