from django.db import models
from rest_framework import serializers
from baremetal_service.repository import service_model
from drf_yasg import openapi


class NoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


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
        description="token",
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


class ObjectFileUploadSerializer(serializers.ModelSerializer):
    object_name = serializers.CharField(required=True)
    container_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'object_name']


class GetConfInfoSerializer(serializers.ModelSerializer):
    key_value = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["key_value"]


class ServiceInstanceFeedbackSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField(required=True, label="实例所对应的机器", help_text="示例： c4130c54-bc4b-4249-928d-c014827653db")
    status = serializers.CharField(required=True, label="当前实例状态", help_text="示例：active/DELETED")
    task = serializers.CharField(required=True, label="实例更新结果", help_text="示例：success/instance_build")

    class Meta:
        model = NoneMeta
        fields = ["uuid", "status", "task"]


class ServiceMachineFeedbackSerializer(serializers.ModelSerializer):
    machine_id = serializers.CharField(required=True, label="machine id", help_text="5d5f9d0c419049990ddd19d2")
    uuid = serializers.CharField(required=True, label="对应flavor id", help_text="c4130c54-bc4b-4249-928d-c014827653db")
    job_model = serializers.JSONField(required=False, label="job model")

    class Meta:
        model = NoneMeta
        fields = ["machine_id", "uuid", "job_model"]


class ServiceOrderWithIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = service_model.BmServiceOrder
        exclude = ["deleted", "create_at", "update_at", "delivery_status", "project"]


class ServiceOrderDeliveryUpdateSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(required=True, label="订单id", help_text="示例：BMS201908231116166874034")
    delivery_status = serializers.CharField(required=True, label="订单状态", help_text="示例：delivered")

    class Meta:
        model = NoneMeta
        fields = ["order_id", "delivery_status"]


class DiskInfoSerializer(serializers.ModelSerializer):
    volume_type = serializers.CharField(required=True, label="云硬盘类型", help_text="inspure_iscsi")
    size = serializers.IntegerField(required=True, label="云硬盘大小", help_text="1")
    volume_order_price = serializers.IntegerField(required=True, label="所购买云硬盘价格", help_text="30")
    count = serializers.IntegerField(required=True, label="所购买云硬盘数量", help_text="2")

    class Meta:
        model = NoneMeta
        fields = ["volume_type", "size", "volume_order_price", "count"]


class FloatingIPInfoSerializer(serializers.ModelSerializer):
    # floating_ip_allocation = serializers.BooleanField(required=True)
    shared_qos_policy_type = serializers.BooleanField(required=False, default=False, label="带宽类型")
    qos_policy_id = serializers.CharField(required=False, label="共享带宽id")
    qos_policy_name = serializers.CharField(required=True, label="带宽名称")
    external_line_type = serializers.CharField(required=True, label="对外网络类型")
    firewall_id = serializers.CharField(required=True, label="防火墙id")
    firewall_name = serializers.CharField(required=True, label="防火墙名称")
    floating_ip_order_price = serializers.IntegerField(required=True, label="所购买弹性公网IP价格")

    class Meta:
        model = NoneMeta
        fields = ["qos_policy_name", "external_line_type", "firewall_id", "firewall_name", "floating_ip_order_price",
                  "shared_qos_policy_type", "qos_policy_id"]


class ServiceMachineCreateSerializer(serializers.ModelSerializer):
    disk_info = DiskInfoSerializer(many=True)
    floating_ip_info = FloatingIPInfoSerializer(many=False)

    class Meta:
        model = service_model.BmServiceMachine
        exclude = ['id', "deleted", "create_at", "update_at", "order", "uuid", "status", "firewall_id",
                   "firewall_name", "floating_ip_line", "floating_ip_bandwidth"]


class ServiceOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = service_model.BmServiceOrder
        exclude = ['id', "deleted", "create_at", "update_at", "delivery_status", "project"]


class ServiceOrderAlterationSerializer(serializers.ModelSerializer):
    order_type = serializers.CharField(required=True, label="订单类型", help_text="alteration")
    order_price = serializers.FloatField(required=True, label="订单价格", help_text="-4000")
    product_type = serializers.CharField(required=True, label="产品类型", help_text="带宽")
    product_info = serializers.CharField(required=True, label="产品信息")

    class Meta:
        model = NoneMeta
        fields = ['order_type', "order_price", "product_type", "product_info"]


class ServiceCreateListSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True)
    service_info = ServiceMachineCreateSerializer(required=True)

    class Meta:
        model = NoneMeta
        fields = ["order_info", "service_info"]


class MonitoringInstanceSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(required=True)
    region = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['project_id', "region"]


class ServiceInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = service_model.BmServiceInstance
        exclude = ['id', "deleted", "update_at"]


class ServiceOrderQuerybyAccountSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, help_text="示例：3f4cb35aeec544d3af33150f38b55286")

    class Meta:
        model = NoneMeta
        fields = ["account_id"]


class ServiceMachineIdSerializer(serializers.ModelSerializer):
    machine_id = serializers.CharField(required=True, label="Machine id", help_text="示例：5d5f9d0c419049990ddd19d2")

    class Meta:
        model = NoneMeta
        fields = ["machine_id"]


class ServiceRetrySerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(required=True, label="Order id", help_text="示例：BMS201911251135127208056")
    machine_id = serializers.CharField(required=False, label="Machine id", help_text="示例：5d5f9d0c419049990ddd19d2")

    class Meta:
        model = NoneMeta
        fields = ["order_id", "machine_id"]


class ServiceInstanceUuidSerializer(serializers.ModelSerializer):
    instance_uuid = serializers.CharField(required=True, label="instance uuid ",
                                          help_text="示例：c63a51b9-ccbf-412a-b250-661791473a6b")

    class Meta:
        model = NoneMeta
        fields = ["instance_uuid"]


class ServiceBmServiceFloatingIp(serializers.ModelSerializer):
    class Meta:
        model = service_model.BmServiceFloatingIp
        exclude = ['id', "order_id", "account_id", "project_id", "contract_number",
                   "create_at", "update_at", "status",
                   "is_measure_end", "floating_ip", "floating_ip_id", "attached",
                   "instance_uuid", "instance_name", "fixed_address",
                   "external_name", "external_name_id", "first_create_at", "attached_type"]


class ServiceCreateFloatingIpSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True)
    floating_ip_info = ServiceBmServiceFloatingIp(required=True)
    firewall_id = serializers.CharField(required=True, label="防火墙id 示例：5d68dbc679580c3d577bca3e")

    class Meta:
        model = NoneMeta
        fields = ["order_info", "floating_ip_info", "firewall_id"]


class ServiceCreateFloatingIpWithOrderSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderWithIdSerializer(required=True)
    floating_ip_info = ServiceBmServiceFloatingIp(required=True)
    firewall_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["order_info", "floating_ip_info", "firewall_id"]


class ServiceFloatingIpQuotasSetSerializer(serializers.ModelSerializer):
    # qos_policy_id = serializers.CharField(required=True)
    order_info = ServiceOrderAlterationSerializer(required=True)
    floating_ip_id = serializers.CharField(required=True)
    qos_policy_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['order_info', 'floating_ip_id', 'qos_policy_name']


class ServiceDeleteFloatingIpSerializer(serializers.ModelSerializer):
    floating_ip_id_list = serializers.ListField(required=True, label="",
                                                help_text="示例：[‘41deaaeb-b007-41c2-8150-f953cb9765e9’]")

    class Meta:
        model = NoneMeta
        fields = ['floating_ip_id_list']


class ServiceAddFloatingIptoServerSerializer(serializers.ModelSerializer):
    instance_uuid = serializers.CharField(required=True, label="实例 id",
                                          help_text="51c7094c-f039-41b5-865d-d37faa148c96")
    instance_name = serializers.CharField(required=True, label="实例名称", help_text="node_8_32")
    floating_ip_id = serializers.CharField(required=True, label="弹性公网IP id",
                                           help_text="172d6c81-595f-4aa6-b2f7-1ec99e01716c")
    floating_ip_address = serializers.CharField(required=False, label="弹性公网IP", help_text="10.100.2.172")
    fixed_address = serializers.CharField(required=True, label="所绑定的端口", help_text="172.24.0.24")

    class Meta:
        model = NoneMeta
        fields = ['instance_uuid', "instance_name", 'floating_ip_id', "floating_ip_address", "fixed_address"]


class ServiceAddFloatingIptoLoadbalanceSerializer(serializers.Serializer):
    loadbalance_name = serializers.CharField(required=True)
    loadbalance_id = serializers.CharField(required=True)
    floating_ip_id = serializers.CharField(required=True)


class ServiceDetachFloatingIptoLoadbalanceSerializer(serializers.Serializer):
    loadbalance_id = serializers.CharField(required=True)
    floating_ip_id = serializers.CharField(required=True)


class LoadbalanceSerializer(serializers.Serializer):
    loadbalancer_id = serializers.CharField(required=True)
    listener_protocol = serializers.CharField(required=True)


class ServiceDetachFloatingIptoServerSerializer(serializers.ModelSerializer):
    instance_uuid = serializers.CharField(required=True, label="实例 id",
                                          help_text="51c7094c-f039-41b5-865d-d37faa148c96")
    floating_ip_id = serializers.CharField(required=True, label="弹性公网IP id",
                                           help_text="172d6c81-595f-4aa6-b2f7-1ec99e01716c")

    class Meta:
        model = NoneMeta
        fields = ['instance_uuid', 'floating_ip_id']


class ServiceFloatingIpAssociateFirewall(serializers.ModelSerializer):
    floating_ip_id = serializers.CharField(required=True, label="弹性公网IP  id",
                                           help_text="1458e4d9-c0f0-46ae-96f6-3eac0cd34d33")
    floating_ip = serializers.CharField(required=True, label="弹性公网IP", help_text="10.200.204.107")
    firewall_id = serializers.CharField(required=True, label="防火墙id", help_text="5d5f59d7af7b14da70048a6f")

    class Meta:
        model = NoneMeta
        fields = ['floating_ip_id', 'floating_ip', 'firewall_id']


class ServiceBmServiceVolume(serializers.ModelSerializer):
    class Meta:
        model = service_model.BmServiceVolume
        exclude = ['id', 'order_id', 'account_id', 'project_id',
                   'create_at', 'update_at', 'is_measure_end',
                   'region', 'attached_type', 'instance_uuid', 'instance_name',
                   'volume_id', 'contract_number']


class VolumeCreateSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True)
    volume_info = ServiceBmServiceVolume(required=True)

    class Meta:
        model = NoneMeta
        fields = ['order_info', 'volume_info']


class VolumeCreateWithOrderSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderWithIdSerializer(required=True)
    volume_info = ServiceBmServiceVolume(required=True)

    class Meta:
        model = NoneMeta
        fields = ['order_info', 'volume_info']


class VolumeUpdateSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderAlterationSerializer(required=True)
    volume_id = serializers.CharField(required=True)
    name = serializers.CharField(required=False)
    size = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['order_info', 'volume_id', 'name', 'size']


class VolumeDeleteSerailizer(serializers.ModelSerializer):
    volume_ids = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['volume_ids']


class VolumeRollBackSerailizer(serializers.ModelSerializer):
    volume_id_list = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['volume_id_list']


class VolumeBackCreateSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True, label="订单信息", help_text="示例：")
    volume_id = serializers.CharField(required=True, label="云硬盘id", help_text="示例：bdbdd6f9-6c5f-4b33-bf19-563389565d3f")
    name = serializers.CharField(required=False, label="备份名称", help_text="示例：ding_test")
    volume_name = serializers.CharField(required=True, label="云硬盘名称", help_text="示例：ds2334445555555555555555566666666")
    description = serializers.CharField(required=False, label="描述信息", help_text="示例：")

    class Meta:
        model = NoneMeta
        fields = ['volume_id', 'name', 'description', 'order_info', "volume_name"]


class VolumeBackupDeleteSerializer(serializers.ModelSerializer):
    backup_ids = serializers.ListField(required=True, label="所删除的云硬盘备份id列表",
                                       help_text="[6d4dafbf-cb34-47f6-953e-f45e084cf8fa]")

    class Meta:
        model = NoneMeta
        fields = ['backup_ids']


class VolumeBackupRestoreSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True)
    backup_id = serializers.CharField(required=True)
    volume_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['backup_id', 'volume_name', 'order_info']


class VolumeAttachSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True, label="绑定的示例ID",
                                      help_text="示例：776c046b-4675-4ccb-a16a-30db03e44caa")
    volume_id = serializers.CharField(required=True, label="云硬盘ID", help_text="示例：b264e220-8d1c-4695-9941-e1c19a99a246")
    server_name = serializers.CharField(required=False, label="实例名称", help_text="示例：cen7")

    class Meta:
        model = NoneMeta
        fields = ['server_id', 'volume_id', 'server_name']


class BucketCreateSerializer(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True, label="订单信息")
    container_name = serializers.CharField(required=True, label="桶名称  示例：ding")
    is_public = serializers.BooleanField(required=False, default=False, label="权限是否公有  示例：True/False")

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'is_public', 'order_info']


class BucketDeleteSerializer(serializers.ModelSerializer):
    buckets = serializers.ListField(required=True, label="删除桶列表", help_text="示例：[ding]")

    class Meta:
        model = NoneMeta
        fields = ['buckets']


class MaterialSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['contract_number']


class MaterialIPSerializer(serializers.ModelSerializer):
    floating_ip_id = serializers.CharField(required=True, label="弹性公网IP ",
                                           help_text="示例：eb345bb0-9bf0-461d-b5e1-ca1896d50997")
    material_ip_date = serializers.DateField(required=True, label="查询时间", help_text="示例：2019-08-20")

    class Meta:
        model = NoneMeta
        exclude = ["id"]


class MaterialIPSeasonSerializer(serializers.ModelSerializer):
    # contract_number = serializers.CharField(required=True)
    floating_ip_id = serializers.CharField(required=True, label="",
                                           help_text="示例：eb345bb0-9bf0-461d-b5e1-ca1896d50997")
    start_date = serializers.DateField(required=True, label="", help_text="示例：2019-08-20")
    end_date = serializers.DateField(required=True, label="", help_text="示例：2019-08-20")

    class Meta:
        model = NoneMeta
        exclude = ["id"]


class ContarctIPSeasonSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(required=True, label="合同编码", help_text="示例：huo123456")
    start_date = serializers.DateField(required=True, label="开始日期", help_text="示例：2019-09-26")
    end_date = serializers.DateField(required=True, label="结束日期", help_text="示例：2019-09-26")

    class Meta:
        model = NoneMeta
        exclude = ["id"]


class ContarctVolumeSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(required=True, label="合同编码", help_text="示例：ding")

    class Meta:
        model = NoneMeta
        exclude = ["id"]


class ContarctVolumeSeasonalSerializer(serializers.ModelSerializer):
    # contract_number = serializers.CharField(required=True, label="合同编码", help_text="示例：ding")
    start_date = serializers.DateField(required=True, label="开始日期", help_text="示例：2019-09-26")
    end_date = serializers.DateField(required=True, label="结束日期", help_text="示例：2019-09-26")

    class Meta:
        model = NoneMeta
        exclude = ["id"]


class MaterialIpContract(serializers.ModelSerializer):
    contract_number = serializers.CharField(required=True, label="合同编码", help_text="示例：ding")
    contract_ip_date = serializers.DateField(required=True, label="所查询的日期", help_text="示例：2019-10-14")

    class Meta:
        model = NoneMeta
        exclude = ["id"]


class FloatingIPCalculaterInRangeParamDictSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(default=None)
    project_id = serializers.CharField(required=False)
    account_id = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ["contract_number", "project_id", "account_id"]


class FloatingIPCalculaterInRangeSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=True, label="开始日期", help_text="示例：2019-09-26")
    end_date = serializers.DateField(required=True, label="结束日期", help_text="示例：2019-09-26")
    contract_number = serializers.CharField(required=False, label="合同编号", help_text="示例：w20190924")
    project_id = serializers.CharField(required=False, label="项目id",
                                       help_text="示例：7ae5a60714014778baddea703b85cd93")
    account_id = serializers.CharField(required=False, label="用户id",
                                       help_text="示例：c46c3de5d6984241ad21e8fe45761059")

    class Meta:
        model = NoneMeta
        fields = ["start_date", "end_date", "contract_number", "project_id", "account_id"]


class BucketUpdateSeraializer(serializers.ModelSerializer):
    container_name = serializers.CharField(required=True, label="桶名称", help_text="示例：ding")
    is_public = serializers.BooleanField(required=False, default=False, label="是否公有", help_text="示例：True/False")

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'is_public']


class BucketShowSerializer(serializers.ModelSerializer):
    container_name = serializers.CharField(required=True, label="桶名称", help_text="示例：container_jacky_test")
    path = serializers.CharField(required=False, label="路径", help_text="示例：container_jacky_test")

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'path']


class BucketCreateDirSerializer(serializers.ModelSerializer):
    container_name = serializers.CharField(required=True)
    floder_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'floder_name']


class BucketShowObjectSerializer(serializers.ModelSerializer):
    container_name = serializers.CharField(required=True, help_text="示例：韩总Q1_-")
    object_name = serializers.CharField(required=True, help_text="object_name为目录时末尾加斜杠/")

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'object_name']


class BucketDeleteObjectSerializer(serializers.ModelSerializer):
    container_name = serializers.CharField(required=True)

    object_names = serializers.ListField(required=True,
                                         help_text="""object_name为目录时末尾加斜杠/, ['ccc/ddd/, 'ccc/eee/d']""")

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'object_names']


class BucketUploadParamOjbectSerializer(serializers.ModelSerializer):
    object_name = serializers.CharField(required=True)
    # file = serializers.FileField(required=True)
    container_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['container_name', 'object_name']


class BucketCopyObjectSerializer(serializers.ModelSerializer):
    src_container_name = serializers.CharField(required=True)

    src_object_name = serializers.CharField(required=True,
                                            help_text="""object_name为目录时末尾加斜杠/, ['ccc/ddd/, 'ccc/eee/d']""")

    dst_container_name = serializers.CharField(required=True)
    dst_object_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['src_container_name', 'src_object_name',
                  'dst_container_name', 'dst_object_name']


class CreateLoadBalancersSerializer(serializers.Serializer):
    floating_ip_order_info = ServiceOrderCreateSerializer(required=False)
    loadbalance_order_info = ServiceOrderCreateSerializer(required=False)
    floating_ip_info = ServiceBmServiceFloatingIp(required=False)
    firewall_id = serializers.CharField(required=False, label="防火墙id 示例：5d68dbc679580c3d577bca3e")
    name = serializers.CharField(required=True)
    flavor_id = serializers.CharField(required=False)
    vip_network_id = serializers.CharField(required=True)
    location = serializers.CharField(required=False)
    is_public = serializers.BooleanField(required=False)
    network_name = serializers.CharField(required=False)
    public_ip_id = serializers.CharField(required=False)
    vpc_name = serializers.CharField(required=False)
    vpc_id = serializers.CharField(required=False)
    listener_count = serializers.CharField(required=False)
    pool_count = serializers.CharField(required=False)
    is_new_ip = serializers.BooleanField(required=False)


class CreateListenerSerializer(serializers.Serializer):
    whether_insert_headers = serializers.CharField(required=False, help_text="判断监听器是否需要获取客户端真实IP的头字典")
    listener_name = serializers.CharField(required=True, help_text="监听器名称")
    loadbalancer_id = serializers.CharField(required=True, help_text="负载均衡器ID")
    protocol = serializers.CharField(required=True, help_text="监听器协议")
    protocol_port = serializers.IntegerField(required=True, help_text="监听器协议端口")
    timeout_member_connect = serializers.IntegerField(required=True, help_text="监听器成员连接超时时限（秒）")


class CreateSNIListenerSerializer(serializers.Serializer):
    default_tls_container_ref = serializers.CharField(required=False, help_text="监听器SNI证书管理处的引用")
    listener_name = serializers.CharField(required=True, help_text="监听器名称")
    loadbalancer_id = serializers.CharField(required=True, help_text="负载均衡器ID")
    protocol = serializers.CharField(required=True, help_text="监听器协议")
    protocol_port = serializers.IntegerField(required=True, help_text="监听器协议端口")
    sni_container_refs = serializers.ListField(required=False, help_text="监听器SNI证书的引用（PKCS12格式）")
    timeout_member_connect = serializers.IntegerField(required=False, help_text="监听器成员连接超时时限（秒）")


class UpdateListenerSerializer(serializers.Serializer):
    whether_insert_headers = serializers.CharField(required=False, help_text="判断监听器是否需要获取客户端真实IP的头字典")
    loadbalancer_id = serializers.CharField(required=True, help_text="负载均衡器ID")
    protocol = serializers.CharField(required=True, help_text="监听器协议")
    protocol_port = serializers.IntegerField(required=True, help_text="监听器协议端口")
    listener_name = serializers.CharField(required=False, help_text="监听器名称")
    timeout_member_connect = serializers.IntegerField(required=False, help_text="监听器成员连接超时时限（秒）")
    default_pool_id = serializers.CharField(required=True, help_text="监听器所绑定的资源池")


class DeleteCertificatesSerializer(serializers.Serializer):
    crt_name = serializers.CharField(required=False, help_text="SNI证书名称")
    crt_domain = serializers.IntegerField(required=False, help_text="SNI证书对应域名")


class UpdateCertificatesSerializer(serializers.Serializer):
    crt_name = serializers.CharField(required=False, help_text="SNI证书名称")
    crt_domain = serializers.IntegerField(required=False, help_text="SNI证书对应域名")


class CreateCertificatesSerializer(serializers.Serializer):
    crt_name = serializers.CharField(required=True, help_text="Secret名称")
    crt_type = serializers.CharField(required=True, help_text="SNI证书类型")
    crt_contents = serializers.CharField(required=True, help_text="Secret内容")
    crt_secret_key = serializers.CharField(required=False, help_text="SNI证书私钥")
    crt_domain = serializers.CharField(required=False, help_text="当前SNI证书对应域名")


class CreateSecretsSerializer(serializers.Serializer):
    crt_name = serializers.CharField(required=True, help_text="Secret名称")
    # crt_type = serializers.CharField(required=True, help_text="SNI证书类型")
    crt_contents = serializers.CharField(required=True, help_text="Secret内容")
    # crt_secret_key = serializers.CharField(required=False, help_text="SNI证书私钥")
    # crt_domain = serializers.CharField(required=False, help_text="当前SNI证书对应域名")


class CreatePoliciesSerializer(serializers.Serializer):
    # admin_state_up = serializers.BooleanField(required=False)
    name = serializers.CharField(required=False)
    # position = serializers.IntegerField(required=False)
    # redirect_http_code = serializers.IntegerField(required=False)
    redirect_pool_id = serializers.CharField(required=False)
    # redirect_prefix = serializers.CharField(required=False)
    # redirect_url = serializers.CharField(required=False)
    # tags = serializers.ListField(required=False)
    domain_compare_type = serializers.CharField(required=False, default="EQUAL_TO")
    domain_name = serializers.CharField(required=False)
    url_compare_type = serializers.CharField(required=False, default="STARTS_WITH")
    url = serializers.CharField(required=True, )


class CreateSessionSerializer(serializers.ModelSerializer):
    type = serializers.CharField(required=True)
    persistence_timeout = serializers.CharField(required=False)
    cookie_name = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['type', 'persistence_timeout', 'cookie_name']


class CreatePoolsSerializer(serializers.Serializer):
    lb_algorithm = serializers.CharField(required=True)
    loadbalancer_id = serializers.CharField(required=False)
    listener_id = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    protocol = serializers.CharField(required=True)
    session_persistence = CreateSessionSerializer(required=False)
    is_keep_session = serializers.BooleanField(required=False)


class CreateHealthMonitorSerializer(serializers.Serializer):
    delay = serializers.IntegerField(required=True, help_text="健康检查器检查间隔（秒）")
    max_retries = serializers.IntegerField(required=True, help_text="转为ONLINE状态前健康检查器最大重试次数（次）")
    timeout = serializers.IntegerField(required=True, help_text="健康检查器超时时间（秒）")
    pool_id = serializers.CharField(required=True, help_text="健康检查器将要绑定的资源池ID")
    type = serializers.CharField(required=True,
                                 help_text="健康检查器协议类型（One of HTTP, HTTPS, PING, TCP, TLS-HELLO, or UDP-CONNECT）")
    url_path = serializers.CharField(required=False, help_text="健康检查器的请求的HTTP URL路径；必须以'/'开头，default：/")
    # expected_codes = serializers.CharField(required=False,
    #                                        help_text="后端成员的预期HTTP状态码；单个状态码'200'，或列表[200, 202]，或状态码范围200-204，default：200")


class CreatePoliciesRuleSerializer(serializers.Serializer):
    compare_type = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    value = serializers.CharField(required=False)


class AttachPoolMemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, help_text="成员名称")
    private_address = serializers.CharField(required=True, help_text="当前成员private IP地址")
    public_address = serializers.CharField(required=False, help_text="当前成员public IP地址")
    protocol_port = serializers.IntegerField(required=True, help_text="当前成员端口号")
    weight = serializers.IntegerField(required=True, help_text="当前成员权重")
    instance_id = serializers.CharField(required=True, help_text="添加的裸金属实例id")
    loadbancer_id = serializers.CharField(required=True, help_text="当前资源池所对应的负载均衡名称")

    class Meta:
        model = NoneMeta
        fields = ["name", "private_address", "public_address", "protocol_port", "weight", "instance_id",
                  "loadbancer_id"]


class AttachPoolMemberListSerializer(serializers.ModelSerializer):
    member_obj_list = AttachPoolMemberSerializer(many=True)

    class Meta:
        model = NoneMeta
        fields = ["member_obj_list"]


class CreatePoolMemberSerializer(serializers.Serializer):
    address = serializers.CharField(required=True, help_text="当前成员IP地址")
    protocol_port = serializers.IntegerField(required=True, help_text="当前成员端口号")
    weight = serializers.IntegerField(required=True, help_text="当前成员权重")


class UpdateLoadBalancersSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    admin_state_up = serializers.BooleanField(required=False)


class UpdatePoliciesSerializer(serializers.Serializer):
    redirect_pool_id = serializers.CharField(required=False)
    name = serializers.CharField(required=False)


class UpdatePoolSerializer(serializers.Serializer):
    lb_algorithm = serializers.CharField(required=True)
    name = serializers.CharField(required=False)
    session_persistence = CreateSessionSerializer(required=False)
    is_keep_session = serializers.BooleanField(required=False)


class UpdateHealthMonitorSerializer(serializers.Serializer):
    delay = serializers.IntegerField(required=True, help_text="健康检查器检查间隔（秒）")
    max_retries = serializers.IntegerField(required=True, help_text="转为ONLINE状态前健康检查器最大重试次数（次）")
    timeout = serializers.IntegerField(required=True, help_text="健康检查器超时时间（秒）")
    url_path = serializers.CharField(required=False, help_text="健康检查器的请求的HTTP URL路径；必须以'/'开头，default：/")


class UpdatePoolsSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(required=False)
    ca_tls_container_ref = serializers.CharField(required=False)
    crl_container_ref = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    lb_algorithm = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    session_persistence = serializers.CharField(required=False)
    tags = serializers.ListField(required=False)
    tls_enabled = serializers.BooleanField(required=False)
    tls_container_ref = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['admin_state_up', 'ca_tls_container_ref', 'crl_container_ref', 'description',
                  'lb_algorithm', 'listener_id', 'loadbalancer_id', 'name',
                  'session_persistence', 'tags', "tls_enabled", "tls_container_ref"]


class UpdatePoliciesRuleSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(required=False)
    compare_type = serializers.CharField(required=False)
    invert = serializers.BooleanField(required=False)
    key = serializers.CharField(required=False)
    tags = serializers.ListField(required=False)
    type = serializers.CharField(required=False)
    value = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['admin_state_up', 'compare_type', 'invert', 'key',
                  'tags', "type", "value"]


class UpdatePoolMemberSerializer(serializers.Serializer):
    # protocol_port = serializers.IntegerField(required=True, help_text="当前成员监控端口")
    weight = serializers.IntegerField(required=True, help_text="当前成员权重")


class ShowLoadBalancersSerializer(serializers.Serializer):
    # loadbalancer_id = serializers.UUIDField(required=True)
    fields = serializers.CharField(required=False, help_text="可提供参数值，按需返回；如果该参数为空，返回默认策略设置的所有属性")


class ListenerDeatilSerializer(serializers.ModelSerializer):
    listener_id = serializers.UUIDField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['listener_id']


class GetBalancersStatisticsSerializer(serializers.ModelSerializer):
    loadbalancer_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['loadbalancer_id']


class InstanceInterfaceAttachmentSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)
    net_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id', 'net_id']


class InstanceInterfaceDetSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)
    port_ids = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id', 'port_ids']


class InstancePostSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    image = serializers.CharField(required=True)
    flavor = serializers.CharField(required=True)
    network_dict = serializers.DictField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['name', 'image', 'flavor', 'network_dict']


class InstStopSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class InstRestartSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class InstStartSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class InstanceDelSerializer(serializers.ModelSerializer):
    server_id_list = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id_list']


class InstanceIdListSerializer(serializers.ModelSerializer):
    server_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['server_id']


class CreateVpcsSerializer(serializers.ModelSerializer):
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


class UpdateVpcsSerializer(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'name']


class DleleteVpcsSerializer(serializers.ModelSerializer):
    vpc_ids = serializers.ListField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_ids']


class ListVpcNetworks(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id']


class PostVpcNetwork(serializers.ModelSerializer):
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


class PutVpcNetwork(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    net_id = serializers.CharField(required=True)
    net_name = serializers.CharField(required=False)
    enable_dhcp = serializers.BooleanField(required=False)
    dns = serializers.ListField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'net_id', 'net_name',
                  'enable_dhcp', 'dns']


class DelVpcNetwork(serializers.ModelSerializer):
    vpc_id = serializers.IntegerField(required=True)
    net_id = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['vpc_id', 'net_id']


class NatGateWayCreate(serializers.ModelSerializer):
    order_info = ServiceOrderCreateSerializer(required=True, label="订单信息", help_text="示例：")
    name = serializers.CharField(required=True)
    vpc_id = serializers.IntegerField(required=True)
    description = serializers.CharField(required=False)

    class Meta:
        model = NoneMeta
        fields = ['order_info', 'name', 'vpc_id', 'description']


class DnatRuleCreate(serializers.ModelSerializer):
    scenes = serializers.CharField(required=False, label="使用场景", default="VPC")
    floatingip_id = serializers.CharField(required=True, label="floating ip id")
    floating_ip_address = serializers.CharField(required=True, label='floating ip 地址')
    external_port = serializers.IntegerField(required=True, label="公网端口")
    protocol = serializers.ChoiceField(choices=['tcp', 'udp'])
    internal_ip_address = serializers.CharField(required=True, label="内网ip地址")
    internal_port_id = serializers.CharField(required=True, label="内网port id")
    internal_port = serializers.IntegerField(required=True, label="内网端口号")
    description = serializers.CharField(required=False, label="描述")

    class Meta:
        model = NoneMeta
        fields = ['scenes', 'floatingip_id', 'floating_ip_address', 'external_port', 'protocol',
                  'internal_ip_address', 'internal_port_id', 'internal_port', 'description']


class DnatRuleUpdate(serializers.ModelSerializer):
    external_port = serializers.IntegerField(required=True, label="公网端口")
    protocol = serializers.ChoiceField(choices=['tcp', 'udp'])
    internal_ip_address = serializers.CharField(required=True, label="内网ip地址")
    internal_port_id = serializers.CharField(required=True, label="内网port id")
    internal_port = serializers.IntegerField(required=True, label="内网端口号")
    description = serializers.CharField(required=False, label="描述")

    class Meta:
        model = NoneMeta
        fields = ['external_port', 'protocol',
                  'internal_ip_address', 'internal_port_id', 'internal_port',
                  'description']


class NatGateWayUpdate(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ['name', 'description']


class DnatRuleDelete(serializers.ModelSerializer):
    nat_rules = serializers.ListField(required=True, label='nat规则列表')

    class Meta:
        model = NoneMeta
        fields = ['nat_rules']


class ServiceBandWidth(serializers.ModelSerializer):
    class Meta:
        model = service_model.BmShareBandWidth
        exclude = ['id', 'order_id', 'account_id', 'project_id',
                   'create_at', 'update_at', 'is_measure_end',
                   'contract_number', 'first_create_at',
                   'shared_bandwidth_id', "contract_id",
                   'status', 'deleted_at']


class BandWidthCreateSerializer(serializers.Serializer):
    order_info = ServiceOrderCreateSerializer(required=True)
    bandwidth_info = ServiceBandWidth(required=True)
    contract_id = serializers.CharField(required=True)


class BandWidthUpdateNameSerializer(serializers.Serializer):
    bandwidth_id = serializers.CharField(required=True)
    name = serializers.CharField(required=False)


class BandWidthUpdateSerializer(serializers.Serializer):
    order_info = ServiceOrderAlterationSerializer(required=False)
    bandwidth_id = serializers.CharField(required=True)
    name = serializers.CharField(required=False)
    max_kbps = serializers.IntegerField(required=False)


class BandWidthDeleteSerializer(serializers.Serializer):
    bandwidth_ids = serializers.ListField(required=True)


class BandWidthDetailsSerializer(serializers.Serializer):
    fields_key = serializers.CharField(required=False, help_text="取值：name, fip")
    fields_value = serializers.CharField(required=False)


class SharedBWFipAttachSerializer(serializers.Serializer):
    floating_ip_ids = serializers.ListField(required=True)


class SharedBWFipDetachSerializer(serializers.Serializer):
    order_info = ServiceOrderAlterationSerializer(required=False)
    floating_ip_ids = serializers.ListField(required=True)
    qos_policy_name = serializers.CharField(required=True, help_text="150M")
    service_count = serializers.IntegerField(required=True, help_text="1")
