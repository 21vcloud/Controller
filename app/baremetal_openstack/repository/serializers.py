from django.db import models
from drf_yasg import openapi
from rest_framework import serializers

SessionParameter = [
    openapi.Parameter(
        name='Cookie', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="Cookie",
        required=True,
        default=""
    ),
    openapi.Parameter(
        name='Cookies', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="Cookies",
        required=False,
        default=""
    ),
]


class NoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


class GetConfInfoSerializer(serializers.ModelSerializer):
    key_value = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["key_value"]


class SessionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    project_name = serializers.CharField(required=True)
    project_domain_name = serializers.CharField(required=False)
    user_domain_name = serializers.CharField(required=False)
    region = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ["username", "password", "project_name", "project_domain_name",
                  "user_domain_name", 'region']


class ProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(required=True)
    domain_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['project_name', 'domain_name']


class DeleteProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(required=True)
    domain_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['project_name', 'domain_name']


class ListProjectSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['domain_name']


class GetProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(required=True)
    domain_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['project_name', 'domain_name']


class UpdateProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['project_name', 'description']


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    default_project = serializers.CharField(required=False)
    domain_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['name', 'password', 'email',
                  'default_project', 'domain_name',
                  'description']


class ListUserSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(required=False)
    domain_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['project_name', 'domain_name']


class DeleteUserSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['user_name']


class UpdateUserSerializer(serializers.ModelSerializer):
    origin_user = serializers.CharField(required=True)
    name = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    default_project = serializers.CharField(required=False)
    domain_id = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['origin_user', 'name', 'email', 'domain_id', 'password',
                  'description', 'default_project']


class RoleAssignmentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=True)
    project = serializers.CharField(required=True)
    role = serializers.CharField(required=False, default='_member_')
    domain = serializers.CharField(required=False, default='default')

    class Meta:
        model = NoneMeta
        fields = ['user', 'project', 'role', 'domain']


class InstanceCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    image = serializers.CharField(required=True)
    flavor = serializers.CharField(required=True)
    network_dict = serializers.DictField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['name', 'image', 'flavor', 'network_dict']


class InstanceStopSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class InstanceRestartSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class InstanceStartSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class InstanceDeleteSerializer(serializers.ModelSerializer):
    server_id_list = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id_list']


class InstanceIdSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class RouterCreateSerializer(serializers.ModelSerializer):
    router_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['router_name']


class DeleteRouterSerializer(serializers.ModelSerializer):
    router_of_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['router_of_name']


class CreateFloatingIpSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(required=False)
    region = serializers.CharField(required=True)
    external_line_type = serializers.CharField(required=True)
    floating_network_id = serializers.CharField(required=True)
    qos_policy_id = serializers.CharField(required=True)
    count = serializers.IntegerField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["contract_number", "region", "external_line_type", "floating_network_id", "qos_policy_id", "count"]


class DeleteFloatingIpSerializer(serializers.ModelSerializer):
    floating_ip_id_list = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['floating_ip_id_list']


class FloatingIpQuotasSetSerializer(serializers.ModelSerializer):
    qos_policy_id = serializers.CharField(required=True)
    floating_ip_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['qos_policy_id', 'floating_ip_id']


class AddFloatingIptoServerSerializer(serializers.ModelSerializer):
    instance_id = serializers.CharField(required=True)
    floating_ip_id = serializers.CharField(required=True)
    fixed_address = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['instance_id', 'floating_ip_id', "fixed_address"]


class DetachFloatingIptoServerSerializer(serializers.ModelSerializer):
    instance_id = serializers.CharField(required=True)
    floating_ip_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['instance_id', 'floating_ip_id']


class AddRouterInterfaceSerializer(serializers.ModelSerializer):
    router_id = serializers.CharField(required=True)
    subnet_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['router_id', 'subnet_id']


class SetRouterGatewaySerializer(serializers.ModelSerializer):
    router_id = serializers.CharField(required=True)
    external_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['router_id', 'external_id']


class CreateNetworksSerializer(serializers.ModelSerializer):
    network_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['network_name']


class CreateTenantSubnetSerializer(serializers.ModelSerializer):
    tenant_network_name = serializers.CharField(required=True)
    tenant_network_cidr = serializers.CharField(required=True)
    enable_dhcp_server = serializers.BooleanField(required=True)
    gateway = serializers.CharField(required=True)
    disable_gateway_ip = serializers.BooleanField(required=True)
    subnet_name = serializers.CharField(required=True)
    dns_name_server = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['tenant_network_name', 'tenant_network_cidr', 'enable_dhcp_server',
                  'gateway', 'disable_gateway_ip', 'subnet_name', 'dns_name_server']


class CreateVpcSerializer(serializers.ModelSerializer):
    vpc_name = serializers.CharField(required=True)
    region = serializers.CharField(required=True)
    net_name = serializers.CharField(required=True)
    vpc_type = serializers.CharField(required=True)
    cidr = serializers.CharField(required=True)
    enable_dhcp = serializers.BooleanField(required=False)
    gateway_ip = serializers.CharField(required=False)
    dns = serializers.ListField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['vpc_name', 'region', 'net_name', 'cidr',
                  'enable_dhcp', 'gateway_ip', 'dns', 'vpc_type']


class UpdateVpcSerializer(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'name']


class DleleteVpcSerializer(serializers.ModelSerializer):
    vpc_ids = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_ids']


class ListVpcNetworks(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id']


class AddVpcNetwork(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    net_name = serializers.CharField(required=True)
    cidr = serializers.CharField(required=True)
    enable_dhcp = serializers.BooleanField(required=False)
    gateway_ip = serializers.CharField(required=False)
    dns = serializers.ListField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'net_name', 'cidr',
                  'enable_dhcp', 'gateway_ip', 'dns']


class UpdateVpcNetwork(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    net_id = serializers.CharField(required=True)
    net_name = serializers.CharField(required=False)
    enable_dhcp = serializers.BooleanField(required=False)
    dns = serializers.ListField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'net_id', 'net_name',
                  'enable_dhcp', 'dns']


class DeleteVpcNetwork(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    net_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'net_id']


class KeypairCreate(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    public_key = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['name', 'public_key']


class KeypairDelete(serializers.ModelSerializer):
    keypair_name_list = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['keypair_name_list']


class ProjectIdSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['project_id']


class FirewallCreate(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    region = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['name', 'enabled', 'description', 'region']


class FirewallRuleListSerializer(serializers.ModelSerializer):
    firewall_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['firewall_id']


class FirewallUpdate(serializers.ModelSerializer):
    firewall_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['firewall_id', 'name', 'enabled',
                  'description']


class FirewallDelete(serializers.ModelSerializer):
    firewalls = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['firewalls']


class FirewallRuleCreate(serializers.ModelSerializer):
    firewall_id = serializers.CharField(required=True)
    direction = serializers.CharField(required=True)
    action = serializers.CharField(required=True)
    protocol = serializers.CharField(required=True)
    remote_ip = serializers.CharField(required=True)
    remote_port = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['firewall_id', 'direction', 'action',
                  'protocol', 'remote_ip', 'remote_port']


class FirewallRuleUpdate(serializers.ModelSerializer):
    firewall_id = serializers.CharField(required=True)
    firewall_rule_id = serializers.CharField(required=True)
    direction = serializers.CharField(required=False)
    action = serializers.CharField(required=False)
    protocol = serializers.CharField(required=False)
    remote_ip = serializers.CharField(required=False)
    remote_port = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['firewall_id', 'firewall_rule_id', 'direction', 'action',
                  'protocol', 'remote_ip', 'remote_port']


class FirewallRuleDelete(serializers.ModelSerializer):
    firewall_id = serializers.CharField(required=True)
    firewall_rule_id = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['firewall_id', 'firewall_rule_id']


class InstanceInterfaceAttachSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)
    net_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id', 'net_id']


class InstanceInterfaceDetachSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)
    port_ids = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id', 'port_ids']


class CreateLoadBalancersSerializer(serializers.ModelSerializer):
    vip_subnet_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    listeners = serializers.ListField(required=False)
    admin_state_up = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    flavor_id = serializers.UUIDField(required=False)
    provider = serializers.CharField(required=False)
    tags = serializers.ListField(required=False)
    vip_address = serializers.CharField(required=False)
    vip_network_id = serializers.UUIDField(required=False)
    vip_port_id = serializers.UUIDField(required=False)
    vip_qos_policy_id = serializers.UUIDField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['vip_subnet_id', 'name', 'listeners', 'admin_state_up',
                  'description', 'flavor_id', 'provider', 'tags',
                  'vip_address', 'vip_network_id', 'vip_port_id', 'vip_qos_policy_id']


class UpdateLoadBalancersSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    loadbalancer_id = serializers.UUIDField(required=True)
    name = serializers.CharField(required=False)
    tags = serializers.ListField(required=False)
    vip_qos_policy_id = serializers.UUIDField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['admin_state_up', 'description', 'loadbalancer_id', 'name', 'tags', 'vip_qos_policy_id']


class ShowLoadBalancersSerializer(serializers.ModelSerializer):
    loadbalancer_id = serializers.UUIDField(required=True)
    fields = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['loadbalancer_id', 'fields']


class DeleteLoadBalancersSerializer(serializers.ModelSerializer):
    loadbalancer_id = serializers.UUIDField(required=True)
    cascade = serializers.BooleanField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['loadbalancer_id', 'cascade']


class GetBalancersStatisticsSerializer(serializers.ModelSerializer):
    loadbalancer_id = serializers.UUIDField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['loadbalancer_id']


class GetBalancersStatusTreeSerializer(serializers.ModelSerializer):
    loadbalancer_id = serializers.UUIDField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['loadbalancer_id']


class FailoverBalancersSerializer(serializers.ModelSerializer):
    loadbalancer_id = serializers.UUIDField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['loadbalancer_id']


# 负载均衡
class BalancersPoolIdSerializer(serializers.ModelSerializer):
    pool_id = serializers.UUIDField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['pool_id']



