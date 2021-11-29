from django.db import models
from rest_framework import serializers
# from rest_api.repository import service_model
from baremetal_service.repository import service_model
from account.repository import auth_models
from drf_yasg import openapi


CookiesParameter = [
    openapi.Parameter(
        name='COOKIE', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="COOKIES",
        required=True,
        default=""
    ),
    openapi.Parameter(
        name='cookies', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="cookies",
        required=False,
        default=""
    ),
]

TokenParameter = [
    openapi.Parameter(
        name='token', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="access_token",
        required=True,
        default=""
    )
]


BucketUploadOjbectSerializer = [
    # openapi.Parameter(
    #     name='container_name', in_=openapi.IN_PATH,
    #     type=openapi.TYPE_STRING,
    #     description="container_name",
    #     required=True,
    #     default=""
    # ),
    # openapi.Parameter(
    #     name='object_name', in_=openapi.IN_PATH,
    #     type=openapi.TYPE_STRING,
    #     description="object_name",
    #     required=True,
    #     default=""
    # ),
    openapi.Parameter(
        name='file', in_=openapi.IN_FORM,
        type=openapi.TYPE_FILE,
        description="file",
        required=True,
    )
]


# instances
class ServiceInstFeedbackSerializer(serializers.Serializer):
    uuid = serializers.CharField(required=True,label="实例所对应的机器",help_text="示例： c4130c54-bc4b-4249-928d-c014827653db")
    status = serializers.CharField(required=True,label="当前实例状态",help_text="示例：active/DELETED")
    task = serializers.CharField(required=True,label="实例更新结果",help_text="示例：success/instance_build")


class InstServerMachineFeedbackSerializer(serializers.Serializer):
    machine_id = serializers.CharField(required=True,label="machine id",help_text="5d5f9d0c419049990ddd19d2")
    uuid = serializers.CharField(required=True,label="对应flavor id",help_text="c4130c54-bc4b-4249-928d-c014827653db")


class InstOrderWithIdSerializer(serializers.Serializer):
    class Meta:
        model = service_model.BmServiceOrder
        exclude = ["deleted", "create_at", "update_at", "delivery_status", "project"]


class InstServiceOrderDeliveryUpdateSerializer(serializers.Serializer):
    order_id = serializers.CharField(required=True,label="订单id",help_text="示例：BMS201908231116166874034")
    delivery_status = serializers.CharField(required=True,label="订单状态",help_text="示例：delivered")


class InstServiceMachineFeedbackSerializer(serializers.Serializer):
    machine_id = serializers.CharField(required=True,label="machine id", help_text="5d5f9d0c419049990ddd19d2")
    uuid = serializers.CharField(required=True, label="对应flavor id", help_text="c4130c54-bc4b-4249-928d-c014827653db")
    job_model = serializers.JSONField(required=False, label="job model")


# from 'VBS'
class VbsDiskInfoSerializer(serializers.Serializer):
    volume_type = serializers.CharField(required=True,label="云硬盘类型",help_text="inspure_iscsi")
    size = serializers.IntegerField(required=True,label="云硬盘大小",help_text="1")
    volume_order_price = serializers.IntegerField(required=True,label="所购买云硬盘价格",help_text="30")
    count = serializers.IntegerField(required=True,label="所购买云硬盘数量",help_text="2")


# from 'floating IP'
class FipFloatingIPInfoSerializer(serializers.Serializer):
    qos_policy_name = serializers.CharField(required=True,label="带宽名称")
    external_line_type = serializers.CharField(required=True,label="对外网络类型")
    firewall_id = serializers.CharField(required=True,label="防火墙id")
    firewall_name = serializers.CharField(required=True,label="防火墙名称")
    floating_ip_order_price = serializers.IntegerField(required=True,label="所购买弹性公网IP价格")


class InstServiceMachineCreateSerializer(serializers.Serializer):
    disk_info = VbsDiskInfoSerializer(many=True)
    floating_ip_info = FipFloatingIPInfoSerializer(many=False)

    class Meta:
        model = service_model.BmServiceMachine
        exclude = ['id', "deleted", "create_at", "update_at", "order", "uuid", "status",  "firewall_id",
                   "firewall_name", "floating_ip_line", "floating_ip_bandwidth"]


class InstanOrderCreateSerializer(serializers.Serializer):
    class Meta:
        model = service_model.BmServiceOrder
        exclude = ['id', "deleted", "create_at", "update_at", "delivery_status", "project"]


class InstServiceOrderAlterationSerializer(serializers.Serializer):
    order_type = serializers.CharField(required=True,label="订单类型",help_text="alteration")
    order_price = serializers.FloatField(required=True,label="订单价格",help_text="-4000")
    product_type = serializers.CharField(required=True,label="产品类型",help_text="带宽")
    product_info = serializers.CharField(required=True,label="产品信息")


class InstServiceCreateListSerializer(serializers.Serializer):
    order_info = InstanOrderCreateSerializer(required=True)
    service_info = InstServiceMachineCreateSerializer(required=True)


class InstServiceInstancesSerializer(serializers.Serializer):
    class Meta:
        model = service_model.BmServiceInstance
        exclude = ['id', "deleted", "update_at"]


class InstServiceOrderQuerybyAccountSerializer(serializers.Serializer):
    account_id = serializers.CharField(required=True,help_text="示例：3f4cb35aeec544d3af33150f38b55286")


class InstServiceMachineIdSerializer(serializers.Serializer):
    machine_id = serializers.CharField(required=True,label="Machine id",help_text="示例：5d5f9d0c419049990ddd19d2")


class InstanceInterfaceAttachmentSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True)
    net_id = serializers.CharField(required=True)


class InstanceInterfaceDetSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True)
    port_ids = serializers.ListField(required=True)


class InstStopSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True)


class InstRestartSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True)


class InstStartSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True)


class InstanceDelSerializer(serializers.Serializer):
    server_id_list = serializers.ListField(required=True)


class InstanceIdListSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True)


# floating IPs
class FipServiceBmServiceFloatingIp(serializers.Serializer):
    class Meta:
        model = service_model.BmServiceFloatingIp
        exclude = ['id', "order_id", "account_id", "project_id", "contract_number",
                   "create_at", "update_at", "status",
                   "is_measure_end", "floating_ip", "floating_ip_id", "attached", "attached_type"
                   "instance_uuid", "instance_name", "fixed_address", "qos_policy_id",
                   "external_name", "external_name_id"]


class FipServiceCreateFloatingIpSerializer(serializers.Serializer):
    order_info = InstanOrderCreateSerializer(required=True)
    floating_ip_info = FipServiceBmServiceFloatingIp(required=True)
    firewall_id = serializers.CharField(required=True, label="防火墙id 示例：5d68dbc679580c3d577bca3e")


class FloatingIpQuotasSetSerializer(serializers.Serializer):
    order_info = InstServiceOrderAlterationSerializer(required=True)
    floating_ip_id = serializers.CharField(required=True)
    qos_policy_name = serializers.CharField(required=True)


class FipServiceDeleteFloatingIpSerializer(serializers.Serializer):
    floating_ip_id_list = serializers.ListField(required=True, label="",
                                                help_text="示例：[‘41deaaeb-b007-41c2-8150-f953cb9765e9’]")


class FipServiceAddFloatingIptoServerSerializer(serializers.Serializer):
    instance_uuid = serializers.CharField(required=True,label="实例 id",help_text="51c7094c-f039-41b5-865d-d37faa148c96")
    instance_name = serializers.CharField(required=True,label="实例名称",help_text="node_8_32")
    floating_ip_id = serializers.CharField(required=True,label="弹性公网IP id",help_text="172d6c81-595f-4aa6-b2f7-1ec99e01716c")
    floating_ip_address = serializers.CharField(required=False,label="弹性公网IP",help_text="10.100.2.172")
    fixed_address = serializers.CharField(required=True,label="所绑定的端口",help_text="172.24.0.24")


class FipServiceDetachFloatingIptoServerSerializer(serializers.Serializer):
    instance_uuid = serializers.CharField(required=True,label="实例 id",help_text="51c7094c-f039-41b5-865d-d37faa148c96")
    floating_ip_id = serializers.CharField(required=True,label="弹性公网IP id",help_text="172d6c81-595f-4aa6-b2f7-1ec99e01716c")


class FipServiceFloatingIpAssociateFirewall(serializers.Serializer):
    floating_ip_id = serializers.CharField(required=True,label="弹性公网IP  id",
                                           help_text="1458e4d9-c0f0-46ae-96f6-3eac0cd34d33")
    floating_ip = serializers.CharField(required=True,label="弹性公网IP",help_text="10.200.204.107")
    firewall_id = serializers.CharField(required=True,label="防火墙id",help_text="5d5f59d7af7b14da70048a6f")


class FloatingIPCalculaterInRangeParamDictSerializer(serializers.Serializer):
    contract_number = serializers.CharField(default=None)
    project_id = serializers.CharField(required=False)
    account_id = serializers.CharField(required=False)


class FloatingIPCalculaterInRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True,label="开始日期",help_text="示例：2019-09-26")
    end_date = serializers.DateField(required=True,label="结束日期",help_text="示例：2019-09-26")
    contract_number = serializers.CharField(required=False,label="合同编号",help_text="示例：w20190924")
    project_id = serializers.CharField(required=False,label="项目id",help_text="示例：7ae5a60714014778baddea703b85cd93")
    account_id = serializers.CharField(required=False,label="用户id",help_text="示例：c46c3de5d6984241ad21e8fe45761059")


# VBS: volumes
class ServiceBmServiceVbs(serializers.Serializer):

    class Meta:
        model = service_model.BmServiceVolume
        exclude = ['id', 'order_id', 'account_id', 'project_id',
                    'create_at', 'update_at', 'is_measure_end',
                    'region', 'attached_type', 'instance_uuid', 'instance_name',
                   'volume_id', 'contract_number']


class VbsCreateSerializer(serializers.Serializer):
    order_info = InstanOrderCreateSerializer(required=True)
    volume_info = ServiceBmServiceVbs(required=True)


class VbsUpdateSerializer(serializers.Serializer):
    order_info = InstServiceOrderAlterationSerializer(required=True)
    volume_id = serializers.CharField(required=True)
    name = serializers.CharField(required=False)
    size = serializers.CharField(required=False)


class VbsDeleteSerailizer(serializers.Serializer):
    volume_ids = serializers.ListField(required=True)


class VbsBackupCreateSerializer(serializers.Serializer):
    order_info = InstanOrderCreateSerializer(required=True,label="订单信息",help_text="示例：")
    volume_id = serializers.CharField(required=True,label="云硬盘id",help_text="示例：bdbdd6f9-6c5f-4b33-bf19-563389565d3f")
    name = serializers.CharField(required=False,label="备份名称",help_text="示例：ding_test")
    volume_name = serializers.CharField(required=True,label="云硬盘名称",help_text="示例：ds2334445555555555555555566666666")
    description = serializers.CharField(required=False,label="描述信息",help_text="示例：")


class VbsBackupDeleteSerializer(serializers.Serializer):
    backup_ids = serializers.ListField(required=True,label="所删除的云硬盘备份id列表",help_text="[6d4dafbf-cb34-47f6-953e-f45e084cf8fa]")


class VbsBackupRestoreSerializer(serializers.Serializer):
    order_info = InstanOrderCreateSerializer(required=True)
    backup_id = serializers.CharField(required=True)
    volume_name = serializers.CharField(required=False)


class VbsAttachSerializer(serializers.Serializer):
    server_id = serializers.CharField(required=True,label="绑定的示例ID",help_text="示例：776c046b-4675-4ccb-a16a-30db03e44caa")
    volume_id = serializers.CharField(required=True,label="云硬盘ID",help_text="示例：b264e220-8d1c-4695-9941-e1c19a99a246")
    server_name = serializers.CharField(required=False,label="实例名称",help_text="示例：cen7")


# OBS: object storage
class ObsBucketCreateSerializer(serializers.Serializer):
    order_info = InstanOrderCreateSerializer(required=True,label="订单信息")
    container_name = serializers.CharField(required=True,label="桶名称  示例：ding")
    is_public = serializers.BooleanField(required=False, default=False,label="权限是否公有  示例：True/False")


class ObsBucketDeleteSerializer(serializers.Serializer):
    buckets = serializers.ListField(required=True,label="删除桶列表",help_text="示例：[ding]")


class ObsBucketUpdateSeraializer(serializers.Serializer):
    container_name = serializers.CharField(required=True,label="桶名称",help_text="示例：ding")
    is_public = serializers.BooleanField(required=False, default=False,label="是否公有",help_text="示例：True/False")


class ObsBucketShowSerializer(serializers.Serializer):
    container_name = serializers.CharField(required=True,label="桶名称",help_text="示例：container_jacky_test")
    path = serializers.CharField(required=False,label="路径",help_text="示例：container_jacky_test")


class ObsBucketCreateDirSerializer(serializers.Serializer):
    container_name = serializers.CharField(required=True)
    floder_name = serializers.CharField(required=True)


class ObsBucketShowObjectSerializer(serializers.Serializer):
    container_name = serializers.CharField(required=True,help_text="示例：韩总Q1_-")
    object_name = serializers.CharField(required=True, help_text="object_name为目录时末尾加斜杠/")


class ObsBucketDeleteObjectSerializer(serializers.Serializer):
    container_name = serializers.CharField(required=True)

    object_names = serializers.ListField(required=True,
                                         help_text="""object_name为目录时末尾加斜杠/, ['ccc/ddd/, 'ccc/eee/d']""")


class BucketUploadParamOjbectSerializer(serializers.Serializer):
    object_name = serializers.CharField(required=True)
    container_name = serializers.CharField(required=True)


class BucketCopyObjectSerializer(serializers.Serializer):
    src_container_name = serializers.CharField(required=True)

    src_object_name = serializers.CharField(required=True,
                                         help_text="""object_name为目录时末尾加斜杠/, ['ccc/ddd/, 'ccc/eee/d']""")

    dst_container_name = serializers.CharField(required=True)
    dst_object_name = serializers.CharField(required=True)


class ObsFileUploadSerializer(serializers.Serializer):
    object_name = serializers.CharField(required=True)
    container_name = serializers.CharField(required=True)


# VPC
class CreateVpcsSerializer(serializers.Serializer):
    vpc_name = serializers.CharField(required=True)
    region = serializers.CharField(required=True)
    net_name = serializers.CharField(required=True)
    vpc_type = serializers.CharField(required=True)
    cidr = serializers.CharField(required=True)
    enable_dhcp = serializers.BooleanField(required=False)
    gateway_ip = serializers.CharField(required=False)
    dns = serializers.ListField(required=False)


class UpdateVpcsSerializer(serializers.Serializer):
    vpc_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)


class DeleteVpcsSerializer(serializers.Serializer):
    vpc_ids = serializers.ListField(required=True)


class ListVpcNetworks(serializers.Serializer):
    vpc_id = serializers.IntegerField(required=False)


class PostVpcNetwork(serializers.Serializer):
    vpc_id = serializers.IntegerField(required=True)
    net_name = serializers.CharField(required=True)
    cidr = serializers.CharField(required=True)
    enable_dhcp = serializers.BooleanField(required=False)
    gateway_ip = serializers.CharField(required=False)
    dns = serializers.ListField(required=False)


class PutVpcNetwork(serializers.Serializer):
    vpc_id = serializers.IntegerField(required=True)
    net_id = serializers.CharField(required=True)
    net_name = serializers.CharField(required=False)
    enable_dhcp = serializers.BooleanField(required=False)
    dns = serializers.ListField(required=False)


class DelVpcNetwork(serializers.Serializer):
    vpc_id = serializers.IntegerField(required=True)
    net_id = serializers.CharField(required=True)


# IAM: accounts management
class IamRegisterSerializer(serializers.Serializer):
    class Meta:
        model = auth_models.BmUserInfo
        exclude = ["id", "update_at", "deleted_at", "status"]


class IamLoginSerializer(serializers.Serializer):
    AccessKeyId = serializers.CharField(required=True, label="access key")


class IamLogoutSerializer(serializers.Serializer):
    account = serializers.CharField(required=True, label="账号邮箱", help_text="示例：wei.panlong@21vianet.com")


class IamQueryAccountByAccountSerializer(serializers.Serializer):
    account_id = serializers.CharField(required=True,label="查询用户的id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")


# firewall
class FirewallPost(serializers.Serializer):
    name = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    region = serializers.CharField(required=True)


class FirewallRulesListSerializer(serializers.Serializer):
    firewall_id = serializers.CharField(required=True)


class FirewallPut(serializers.Serializer):
    firewall_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)


class FirewallDel(serializers.Serializer):
    firewalls = serializers.ListField(required=True)


class FirewallRulePost(serializers.Serializer):
    firewall_id = serializers.CharField(required=True)
    direction = serializers.CharField(required=True)
    action = serializers.CharField(required=True)
    protocol = serializers.CharField(required=True)
    remote_ip = serializers.CharField(required=True)
    remote_port = serializers.CharField(required=True)


class FirewallRulePut(serializers.Serializer):

    firewall_id = serializers.CharField(required=True)
    firewall_rule_id = serializers.CharField(required=True)
    direction = serializers.CharField(required=False)
    action = serializers.CharField(required=False)
    protocol = serializers.CharField(required=False)
    remote_ip = serializers.CharField(required=False)
    remote_port = serializers.CharField(required=False)


class FirewallRuleDel(serializers.Serializer):
    firewall_id = serializers.CharField(required=True)
    firewall_rule_id = serializers.ListField(required=True)


# keypairs
class KeypairsCreate(serializers.Serializer):
    name = serializers.CharField(required=True)
    public_key = serializers.CharField(required=False)


class KeypairsDelete(serializers.Serializer):
    keypair_name_list = serializers.ListField(required=True)


class KeypairSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    public_key = serializers.CharField(required=False)
    keypair_name_list = serializers.ListField(required=False)
