# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import uuid
from django.db import models
from django.db.models.fields.related import ManyToManyField

from common.lark_common import random_object_id
from account.repository.auth_models import BmContract, BmProject

ORDER_TYPE_INCREASE = "increase"
ORDER_TYPE_ALTERATION = "alteration"
ORDER_STATUS_DELIVERED = "delivered"
ORDER_STATUS_DELIVERING = "delivering"
ORDER_TYPE_DICT = {"increase": "新购", "alteration": "变更"}

FLAVOR_ACTIVE = "active"
VOLUME_ACTIVE = "active"
VOLUME_BACKUP_ACTIVE = "active"
FLOATINGIP_ACTIVE = "active"

LB_ERROR = "ERROR"

resource_type_volume = "volume"
resource_type_volume_backup = "volume_backup"
resource_type_flaoting_ip = "flaoting_ip"
resource_type_ecbm = "ECBM"
resource_contract_info = "contract_info"

FLOATINGIP_AATTACH_ECBM = "ECBM"
FLOATINGIP_AATTACH_SLB = "LoadBalance"


class BmServiceOrder(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_bm_service_order_code)
    account_id = models.CharField(max_length=64, blank=True, null=True,
                                  help_text="客户id  示例：3f4cb35aeec544d3af33150f38b55286")
    contract_number = models.CharField(max_length=64, blank=True, null=True, help_text="合同编码  示例：ding11")
    project = models.ForeignKey(BmProject, models.DO_NOTHING, blank=True, null=True, help_text="项目  示例：test")
    # contract_number = models.CharField(max_length=64, blank=True, null=True)
    # project_id = models.CharField(max_length=64, blank=True, null=True)
    # project_name = models.CharField(max_length=64, blank=True, null=True)
    region = models.CharField(max_length=64, blank=True, null=True, help_text="可用区  示例：华北区")
    order_type = models.CharField(max_length=64, blank=True, null=True, default=ORDER_TYPE_INCREASE,
                                  help_text="订单类型  示例：increase")
    order_price = models.FloatField(blank=True, null=True, help_text="订单价格  示例：1300")
    product_type = models.CharField(max_length=64, blank=True, null=True, help_text="产品类型  示例：ECBM")
    product_info = models.TextField(blank=True, null=True, help_text="产品详细信息")
    billing_model = models.CharField(max_length=64, blank=True, null=True, help_text="绑定的合同类型 示例：框架合同 ")
    service_count = models.IntegerField(blank=True, null=True, help_text="所购买的服务数量  示例：3")
    delivery_status = models.CharField(max_length=64, blank=True, null=True, help_text="")
    create_at = models.DateTimeField(blank=True, null=True, help_text="")
    update_at = models.DateTimeField(blank=True, null=True, help_text="")
    deleted = models.CharField(max_length=11, blank=True, null=True, help_text="")

    class Meta:
        managed = False
        db_table = 'bm_service_order'


class BmServiceMachine(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    order = models.ForeignKey('BmServiceOrder', models.DO_NOTHING, blank=True, null=True)
    uuid = models.CharField(max_length=64, blank=True, null=True)
    flavor_name = models.CharField(max_length=255, blank=True, null=True, help_text="机器名称  示例：戴尔")
    flavor_id = models.CharField(max_length=64, blank=True, null=True,
                                 help_text="机器id  示例：11a2c533-73cc-4f95-8e7b-0055b7ec18a7")
    image_name = models.CharField(max_length=255, blank=True, null=True, help_text="镜像名称  示例：Windows2016")
    image_id = models.CharField(max_length=64, blank=True, null=True,
                                help_text="镜像id 示例：198e0048-c8b2-4db9-9f08-395ea005af21")
    monitoring = models.CharField(max_length=11, blank=True, null=True, help_text="是否携带监控  示例：True/False")
    vulnerability_scanning = models.CharField(max_length=11, blank=True, null=True, help_text="是否携带扫描  示例：True/False")
    disk_info = models.TextField(blank=True, null=True, help_text="磁盘信息")
    network_path_type = models.CharField(max_length=64, blank=True, null=True, help_text="网络类型")
    network = models.CharField(max_length=64, blank=True, null=True, help_text="网络名称")
    network_id = models.CharField(max_length=64, blank=True, null=True, help_text="网络id")
    floating_ip_info = models.TextField(blank=True, null=True, help_text="弹性公网IP信息")
    floating_ip_allocation = models.BooleanField(max_length=64, blank=True, null=True, help_text="弹性公网IP可用量")
    floating_ip_bandwidth = models.CharField(max_length=64, blank=True, null=True, help_text="弹性公网IP带宽")
    floating_ip_line = models.CharField(max_length=64, blank=True, null=True, help_text="弹性公网IP类型")
    firewall_id = models.CharField(max_length=64, blank=True, null=True, help_text="防火墙id")
    firewall_name = models.CharField(max_length=64, blank=True, null=True, help_text="防火墙名称")
    service_name = models.CharField(max_length=64, blank=True, null=True, help_text="所生成的服务器名称")
    login_method = models.CharField(max_length=64, blank=True, null=True,
                                    help_text="登陆方式（user_password-密码登陆）（keypair-密钥登陆）")
    service_username = models.CharField(max_length=64, blank=True, null=True, help_text="所生成服务器的登录名")
    service_password = models.CharField(max_length=64, blank=True, null=True, help_text="所生成服务器的密码")
    public_key = models.TextField(blank=True, null=True, help_text="公钥信息")
    create_at = models.DateTimeField(blank=True, null=True, help_text="服务创建时间")
    update_at = models.DateTimeField(blank=True, null=True, help_text="服务更新时间")
    deleted = models.CharField(max_length=11, blank=True, null=True, help_text="服务删除时间")
    status = models.CharField(max_length=64, blank=True, null=True, help_text="状态（active-激活）（DELETED-删除）")
    job_model = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_machine'


class BmRequestLog(models.Model):
    account_id = models.CharField(max_length=64, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    object_id = models.CharField(max_length=64, blank=True, null=True)
    object_name = models.CharField(max_length=255, blank=True, null=True)
    object_type = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    request_info = models.TextField(blank=True, null=True)
    extra = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_request_log'


class BmServiceInstance(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=64, blank=True, null=True,
                                  help_text="客户id  示例：3f4cb35aeec544d3af33150f38b55286")
    project_id = models.CharField(max_length=64, blank=True, null=True,
                                  help_text="项目id  示例：7ae5a60714014778baddea703b85cd93")
    region = models.CharField(max_length=64, blank=True, null=True, help_text="区域  示例：regionOne")
    monitoring = models.CharField(max_length=11, blank=True, null=True,help_text="是否带监控  示例：True")
    contract_number = models.CharField(max_length=64, blank=True, null=True, help_text="合同编号  示例：ding111")
    product_type = models.CharField(max_length=64, blank=True, null=True, help_text="产品类型  示例：ECBM")
    billing_model = models.CharField(max_length=64, blank=True, null=True, help_text="绑定合同类型  示例：标准合同")
    uuid = models.CharField(unique=True, max_length=64, help_text="对应机器id  示例：c4130c54-bc4b-4249-928d-c014827653db")
    name = models.CharField(max_length=255, help_text="机器名称", blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True, help_text="状态   示例：active/DELETED")
    task = models.CharField(max_length=64, blank=True, null=True, help_text="实例创建结果  示例：success/instance_build")
    create_at = models.DateTimeField(blank=True, null=True, help_text="实例创建时间")
    update_at = models.DateTimeField(blank=True, null=True, help_text="实例更新时间")
    deleted = models.NullBooleanField(blank=True, null=True, default=False, help_text="实例删除时间")

    class Meta:
        managed = False
        db_table = 'bm_service_instance'


class BmServiceFloatingIp(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id, help_text="")
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    contract_number = models.CharField(max_length=64, blank=True, null=True)
    external_line_type = models.CharField(max_length=64, blank=True, null=True, help_text="进出网络类型 "
                                                                                          "示例：three_line_ip")
    external_name = models.CharField(max_length=255, blank=True, null=True)
    external_name_id = models.CharField(max_length=255, blank=True, null=True)
    floating_ip = models.CharField(max_length=64, blank=True, null=True)
    floating_ip_id = models.CharField(max_length=64, blank=True, null=True)
    attached = models.NullBooleanField(blank=True, null=True, default=False)
    instance_uuid = models.CharField(max_length=64, blank=True, null=True)
    instance_name = models.CharField(max_length=255, blank=True, null=True)
    fixed_address = models.CharField(max_length=255, blank=True, null=True)
    shared_qos_policy_type = models.BooleanField(default=False)
    qos_policy_name = models.CharField(max_length=64, blank=True, null=True, help_text="带宽大小 示例：100M")
    qos_policy_id = models.CharField(max_length=64, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    first_create_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)
    is_measure_end = models.NullBooleanField(blank=True, null=True, default=False)
    attached_type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_floating_ip'


class BmContractFloatingIpMaterial(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    floating_ip_type_name = models.CharField(max_length=255, blank=True, null=True)
    floating_ip_type = models.CharField(max_length=255, blank=True, null=True)
    external_line_type = models.CharField(max_length=255, blank=True, null=True)
    charge_type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    floating_ip_available = models.IntegerField(blank=True, null=True)
    floating_ip_capacity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_material_floating_ip'


class BmContractBandWidthaterial(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    band_width_type_name = models.CharField(max_length=255, blank=True, null=True)
    band_width_type = models.CharField(max_length=255, blank=True, null=True)
    external_line_type = models.CharField(max_length=255, blank=True, null=True)
    charge_type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    band_width_available = models.IntegerField(blank=True, null=True)
    band_width_capacity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_material_band_width'


class BmServiceLoadbalanceFlavor(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    type = models.CharField(max_length=255, blank=True, null=True)
    max_connect = models.CharField(max_length=255, blank=True, null=True)
    new_connetc = models.CharField(max_length=255, blank=True, null=True)
    second_query = models.CharField(max_length=255, blank=True, null=True)
    openstack_name = models.CharField(max_length=255, blank=True, null=True)
    memory = models.CharField(max_length=255, blank=True, null=True)
    disk = models.CharField(max_length=255, blank=True, null=True)
    vcpus = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_loadbalance_flavor'


class BmServiceMaterialVolume(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    volume_type_name = models.CharField(max_length=255, blank=True, null=True)
    volume_type = models.CharField(max_length=255, blank=True, null=True)
    openstack_volume_type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.FloatField(blank=True, null=True)
    volume_available = models.IntegerField(blank=True, null=True)
    volume_capacity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_material_volume'


class BmServiceMaterialNat(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    nat_getway_type_name = models.CharField(max_length=255, blank=True, null=True)
    charge_type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.FloatField(blank=True, null=True)
    nat_getway_available = models.IntegerField(blank=True, null=True)
    nat_getway_capacity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    nat_getway_type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_material_nat'


class BmServiceMaterialLb(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    lb_type_name = models.CharField(max_length=255, blank=True, null=True)
    charge_type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.FloatField(blank=True, null=True)
    lb_available = models.IntegerField(blank=True, null=True)
    lb_capacity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    lb_type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_material_lb'


class BmServiceMaterialBandWidth(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    band_width_type_name = models.CharField(max_length=255, blank=True, null=True)
    band_width_type = models.CharField(max_length=255, blank=True, null=True)
    external_line_type = models.CharField(max_length=255, blank=True, null=True)
    charge_type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.FloatField(blank=True, null=True)
    band_width_available = models.IntegerField(blank=True, null=True)
    band_width_capacity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_material_band_width'


class BmMaterialFloatingIpSeasonal(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    identity_name = models.CharField(max_length=255, blank=True, null=True)
    user_account = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    band_material_number = models.CharField(max_length=255, blank=True, null=True)
    band_width_type_name = models.CharField(max_length=255, blank=True, null=True)
    material_band_base_price = models.CharField(max_length=255, blank=True, null=True)
    material_number = models.CharField(max_length=255, blank=True, null=True)
    floating_ip_type_name = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    sales = models.CharField(max_length=255, blank=True, null=True)
    enterprise_number = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    service_expired_time = models.CharField(max_length=255, blank=True, null=True)
    service_start_time = models.CharField(max_length=255, blank=True, null=True)
    contract_start_date = models.CharField(max_length=255, blank=True, null=True)
    contract_expire_date = models.CharField(max_length=255, blank=True, null=True)
    contract_customer_name = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer = models.CharField(max_length=255, blank=True, null=True)
    contract_type = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer_account = models.CharField(max_length=255, blank=True, null=True)
    external_line_type = models.CharField(max_length=255, blank=True, null=True)
    external_name = models.CharField(max_length=255, blank=True, null=True)
    external_name_id = models.CharField(max_length=255, blank=True, null=True)
    floating_ip = models.CharField(max_length=255, blank=True, null=True)
    floating_ip_id = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    max_band = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_material_floating_ip_seasonal'


class BmMaterialVolumeSeasonal(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    user_account = models.CharField(max_length=255, blank=True, null=True)
    identity_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)
    end_at = models.CharField(max_length=255, blank=True, null=True)
    volume_id = models.CharField(max_length=255, blank=True, null=True)
    volume_type = models.CharField(max_length=255, blank=True, null=True)
    contract_customer_name = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer = models.CharField(max_length=255, blank=True, null=True)
    contract_type = models.CharField(max_length=255, blank=True, null=True)
    sales = models.CharField(max_length=255, blank=True, null=True)
    enterprise_number = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    account = models.CharField(max_length=255, blank=True, null=True)
    material_number = models.CharField(max_length=255, blank=True, null=True)
    volume_type_name = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_material_volume_seasonal'


class BmMaterialLbSeasonal(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    user_account = models.CharField(max_length=255, blank=True, null=True)
    identity_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    delete_at = models.CharField(max_length=255, blank=True, null=True)
    ip_adress = models.CharField(max_length=255, blank=True, null=True)
    loadbalance_id = models.CharField(max_length=255, blank=True, null=True)
    loadbalance_name = models.CharField(max_length=255, blank=True, null=True)
    contract_customer_name = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer = models.CharField(max_length=255, blank=True, null=True)
    contract_type = models.CharField(max_length=255, blank=True, null=True)
    sales = models.CharField(max_length=255, blank=True, null=True)
    enterprise_number = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    account = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    material_number = models.CharField(max_length=255, blank=True, null=True)
    lb_type_name = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_material_lb_seasonal'


class BmMaterialNetGetwaySeasonal(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    user_account = models.CharField(max_length=255, blank=True, null=True)
    identity_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    delete_at = models.CharField(max_length=255, blank=True, null=True)
    net_getway_id = models.CharField(max_length=255, blank=True, null=True)
    net_getway_name = models.CharField(max_length=255, blank=True, null=True)
    contract_customer_name = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer = models.CharField(max_length=255, blank=True, null=True)
    contract_type = models.CharField(max_length=255, blank=True, null=True)
    sales = models.CharField(max_length=255, blank=True, null=True)
    enterprise_number = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    account = models.CharField(max_length=255, blank=True, null=True)
    material_number = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)
    nat_getway_type_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_material_net_getway_seasonal'


class BmMaterialMachineSeasonal(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    user_account = models.CharField(max_length=255, blank=True, null=True)
    identity_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.CharField(max_length=255, blank=True, null=True)
    flavor_name = models.CharField(max_length=255, blank=True, null=True)
    image_name = models.CharField(max_length=255, blank=True, null=True)
    monitoring = models.CharField(max_length=255, blank=True, null=True)
    vulnerability_scanning = models.CharField(max_length=255, blank=True, null=True)
    network = models.CharField(max_length=255, blank=True, null=True)
    network_path_type = models.CharField(max_length=255, blank=True, null=True)
    service_name = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    product_type = models.CharField(max_length=255, blank=True, null=True)
    service_count = models.CharField(max_length=255, blank=True, null=True)
    delete_at = models.CharField(max_length=255, blank=True, null=True)
    contract_customer_name = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer = models.CharField(max_length=255, blank=True, null=True)
    contract_type = models.CharField(max_length=255, blank=True, null=True)
    sales = models.CharField(max_length=255, blank=True, null=True)
    enterprise_number = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    account = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    material_number = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.CharField(max_length=255, blank=True, null=True)
    flavor_info = models.CharField(max_length=255, blank=True, null=True)
    cpu_model = models.CharField(max_length=255, blank=True, null=True)
    cpu_core = models.CharField(max_length=255, blank=True, null=True)
    cpu_hz = models.CharField(max_length=255, blank=True, null=True)
    ram = models.CharField(max_length=255, blank=True, null=True)
    disk = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_material_machine_seasonal'


class BmMaterialVolumeBakSeasonal(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    user_account = models.CharField(max_length=255, blank=True, null=True)
    identity_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.CharField(max_length=255, blank=True, null=True)
    backup_name = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    service_count = models.CharField(max_length=255, blank=True, null=True)
    delete_time = models.CharField(max_length=255, blank=True, null=True)
    volume_id = models.CharField(max_length=255, blank=True, null=True)
    contract_customer_name = models.CharField(max_length=255, blank=True, null=True)
    contract_authorizer = models.CharField(max_length=255, blank=True, null=True)
    contract_type = models.CharField(max_length=255, blank=True, null=True)
    sales = models.CharField(max_length=255, blank=True, null=True)
    enterprise_number = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    account = models.CharField(max_length=255, blank=True, null=True)
    material_number = models.CharField(max_length=255, blank=True, null=True)
    volume_type_name = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.CharField(max_length=255, blank=True, null=True)
    date = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_material_volume_bak_seasonal'


class BmContractFloatingIp(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    contract_number = models.CharField(max_length=64, blank=True, null=True)
    external_line_type = models.CharField(max_length=64, blank=True, null=True)
    external_name = models.CharField(max_length=255, blank=True, null=True)
    external_name_id = models.CharField(max_length=255, blank=True, null=True)
    floating_ip = models.CharField(max_length=64, blank=True, null=True)
    floating_ip_id = models.CharField(max_length=64, blank=True, null=True)
    attached = models.NullBooleanField(blank=True, null=True, default=False)
    instance_uuid = models.CharField(max_length=64, blank=True, null=True)
    instance_name = models.CharField(max_length=255, blank=True, null=True)
    fixed_address = models.CharField(max_length=255, blank=True, null=True)
    qos_policy_name = models.CharField(max_length=64, blank=True, null=True)
    qos_policy_id = models.CharField(max_length=64, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)
    is_measure_end = models.NullBooleanField(blank=True, null=True, default=False)

    class Meta:
        managed = False
        db_table = 'bm_contract_floating_ip'


class BmServiceFlavor(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    material_number = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    openstack_flavor_name = models.CharField(max_length=64, blank=True, null=True)
    type = models.CharField(max_length=64, blank=True, null=True)
    type_name = models.CharField(max_length=64, blank=True, null=True)
    resource_class = models.CharField(max_length=255, blank=True, null=True)
    cpu_model = models.CharField(max_length=64, blank=True, null=True)
    base_price = models.FloatField(blank=True, null=True)
    cpu_core = models.CharField(max_length=64, blank=True, null=True)
    cpu_hz = models.CharField(max_length=64, blank=True, null=True)
    gpu = models.CharField(max_length=255, blank=True, null=True)
    ram = models.CharField(max_length=64, blank=True, null=True)
    disk = models.CharField(max_length=255, blank=True, null=True)
    flavor_info = models.CharField(max_length=255, blank=True, null=True)
    count = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_flavor'


class BmServiceImages(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    type = models.CharField(max_length=64, blank=True, null=True)
    image_name = models.CharField(max_length=64, blank=True, null=True)
    openstack_image_name = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_images'


class BmServiceQosPolicy(models.Model):
    # id = models.CharField(primary_key=True, max_length=64)
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    qos_policy_name = models.CharField(max_length=64, blank=True, null=True)
    qos_policy_count = models.IntegerField(blank=True, null=True)
    shared = models.IntegerField(blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_qos_policy'


class Networks(models.Model):
    network_id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=255, blank=True, null=True)
    cidr = models.CharField(max_length=64, blank=True, null=True)
    enable_dhcp = models.NullBooleanField(blank=True, null=True, default=True)
    gateway_ip = models.CharField(max_length=64, blank=True, null=True)
    dns = models.TextField(max_length=255, blank=True, null=True)
    vpc = models.ForeignKey('Vpc', on_delete=models.CASCADE)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_networks'


class Vpc(models.Model):
    vpc_name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    deleted = models.IntegerField(blank=True, null=True)
    router_id = models.CharField(max_length=64, blank=True, null=True)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_vpc'
        unique_together = (('vpc_name', 'project_id'),)


class FirewallRule(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    firewall = models.ForeignKey('Firewalls', models.CASCADE, blank=True, null=True)
    direction = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    protocol = models.CharField(max_length=255, blank=True, null=True)
    remote_ip = models.CharField(max_length=255, blank=True, null=True)
    remote_port = models.TextField(max_length=255, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_firewall_rule'


class Firewalls(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    name = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    enabled = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_firewalls'


class BmServiceLoadbalance(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    contract_number = models.CharField(max_length=64, blank=True, null=True)
    loadbalance_id = models.CharField(max_length=64, blank=True, null=True)
    loadbalance_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=64, blank=True, null=True)
    region = models.CharField(max_length=64, blank=True, null=True)
    flavor_id = models.CharField(max_length=64, blank=True, null=True)
    is_public = models.IntegerField(blank=True, null=True)
    network_name = models.CharField(max_length=255, blank=True, null=True)
    vip_network_id = models.CharField(max_length=255, blank=True, null=True)
    vpc_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    first_create_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    listener_count = models.IntegerField(blank=True, null=True)
    pool_count = models.IntegerField(blank=True, null=True)
    deleted = models.IntegerField(blank=True, null=True)
    is_measure_end = models.IntegerField(blank=True, null=True)
    is_new_ip = models.IntegerField(blank=True, null=True)
    error_type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_loadbalance'


class BmNetworks(models.Model):
    network_id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=255, blank=True, null=True)
    cidr = models.CharField(max_length=64, blank=True, null=True)
    enable_dhcp = models.IntegerField(blank=True, null=True)
    gateway_ip = models.CharField(max_length=64, blank=True, null=True)
    dns = models.TextField(blank=True, null=True)
    vpc = models.ForeignKey('BmVpc', models.DO_NOTHING)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_networks'


class BmVpc(models.Model):
    vpc_name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    deleted = models.IntegerField(blank=True, null=True)
    router_id = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_vpc'
        unique_together = (('vpc_name', 'project_id'),)


class BmServiceVolume(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    volume_type = models.CharField(max_length=255, blank=True, null=True)
    volume_id = models.CharField(max_length=255, blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    create_at = models.DateTimeField(null=True)
    update_at = models.DateTimeField(null=True)
    is_measure_end = models.IntegerField(blank=True, null=True, default=0)
    region = models.CharField(max_length=255, blank=True, null=True)
    attached_type = models.CharField(max_length=255, blank=True, null=True)
    instance_uuid = models.CharField(max_length=64, blank=True, null=True)
    instance_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    first_create_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_service_volume'


class BmFloatingipfirewallMapping(models.Model):
    floating_ip_id = models.CharField(max_length=64, blank=True, null=True)
    firewall = models.ForeignKey(Firewalls, models.CASCADE, blank=True, null=True)
    floating_ip = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_floatingipfirewall_mapping'


class BmInstanceMemberMapping(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id)
    instance_id = models.CharField(max_length=255, blank=True, null=True)
    pool_id = models.CharField(max_length=255, blank=True, null=True)
    loadbancer_id = models.CharField(max_length=255, blank=True, null=True)
    member_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_instance_member_mapping'


class BmServiceVolumeBackup(models.Model):
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    region = models.CharField(max_length=64, blank=True, null=True)
    backup_id = models.CharField(max_length=64, primary_key=True)
    volume_id = models.CharField(max_length=64, blank=True, null=True)
    volume_name = models.CharField(max_length=64, blank=True, null=True)
    is_incremental = models.BooleanField(default=False)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    deleted = models.NullBooleanField(blank=True, null=True, default=False)
    status = models.CharField(max_length=255, blank=True, null=True)
    backup_name = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    is_measure_end = models.IntegerField(blank=True, null=True, default=0)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_service_volume_backup'


class UUIDTools(object):
    @staticmethod
    def uuid4_hex():
        # retun uuid4 hex string
        return uuid.uuid4().hex


class BmServiceNatGateway(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=UUIDTools.uuid4_hex)
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    vpc = models.ForeignKey('Vpc', models.DO_NOTHING, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    is_measure_end = models.BooleanField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    deleted = models.BooleanField(blank=True, null=True, default=False)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    delete_at = models.DateTimeField(blank=True, null=True)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_nat_gateway'


class NatRule(models.Model):
    nat_rule_id = models.CharField(primary_key=True, max_length=36)
    nat_gateway = models.ForeignKey('BmServiceNatGateway', on_delete=models.PROTECT, related_name='nat_rule')
    floatingip_id = models.CharField(max_length=36)
    floating_ip_address = models.CharField(max_length=64, null=True, blank=True)
    scenes = models.CharField(max_length=64, blank=True, null=True, default='vpc')
    external_port = models.IntegerField(max_length=11, blank=True, null=True)
    protocol = models.CharField(max_length=36, blank=True, null=True)
    internal_ip_address = models.CharField(max_length=64, blank=True, null=True)
    internal_port_id = models.CharField(max_length=64, blank=True, null=True)
    internal_port = models.IntegerField(max_length=11, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        managed = False
        db_table = 'bm_nat_rule'


class BmShareBandWidth(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=UUIDTools.uuid4_hex, help_text="")
    shared_bandwidth_id = models.CharField(max_length=64, help_text="")
    billing_type = models.CharField(max_length=64, blank=True, null=True)
    order_id = models.CharField(max_length=64, blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    contract_id = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    max_kbps = models.IntegerField(blank=True, null=True)
    create_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)
    is_measure_end = models.IntegerField(blank=True, null=True, default=0)
    first_create_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=64, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bm_share_bandwidth'


class ShareBandWidthQuota(models.Model):
    project_id = models.CharField(unique=True, max_length=64)
    share_bandwidth_count = models.IntegerField(default=5)
    floating_ip_count = models.IntegerField(default=20)

    class Meta:
        managed = False
        db_table = 'share_bandwidth_quota'
