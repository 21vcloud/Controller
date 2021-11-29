# -*- coding:utf-8 -*-

from django.db import models
from rest_framework import serializers

from rest_api.models import AccessKey


class ResponseNoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


class FlavorListInfoResponsesSerializer(serializers.ModelSerializer):
    base_price = serializers.CharField(label="基础价格", help_text="示例： 3100")
    count = serializers.CharField(label="机器数量", help_text="示例： 1")
    cpu_core = serializers.CharField(label="内核数", help_text="示例： 6*2")
    cpu_hz = serializers.CharField(label="主频", help_text="示例： 2.4GHz")
    cpu_model = serializers.CharField(label="CPU", help_text="示例： Intel Xeon E5-2620 v3*2")
    disk = serializers.CharField(label="磁盘规格", help_text="示例： 2*600G SAS System Disk RAID 1+ 6*600G SAS RAID 5")
    flavor_info = serializers.CharField(label="机器类型描述", help_text="示例： 2*Intel Xeon E5-2620 v3 | 128G | 8*600G SAS")
    id = serializers.CharField(label="机器id", help_text="示例： 11a2c533-73cc-4f95-8e7b-0055b7ec18a7")
    material_number = serializers.CharField(label="物料编码", help_text="示例：CBMS-S-B111")
    name = serializers.CharField(label="物料名称", help_text="示例： 戴尔")
    openstack_flavor_name = serializers.CharField(label="openstack端的名称", help_text="示例：DELL_VBS_RAID")
    ram = serializers.CharField(label="内存大小", help_text="示例： 128G")
    resource_class = serializers.CharField(label="资源类型", help_text="示例： dell_baremetal")
    status = serializers.CharField(label="状态", help_text="示例： active")
    type = serializers.CharField(label="机器类型", help_text="示例： 基础")
    type_name = serializers.CharField(label="机器类型名称", help_text="示例： base")

    class Meta:
        model = ResponseNoneMeta
        fields = ["base_price", "count", "cpu_core", "cpu_hz", "cpu_model", "disk",
                  "flavor_info", "id", "material_number", "name", "openstack_flavor_name", "ram", "resource_class",
                  "status", "type", "type_name"]


class InstImageListInfoResponsesSerializer(serializers.ModelSerializer):
    id = serializers.CharField(label="镜像id", help_text="示例： 92277119-5647-4525-8670-26460b91e357")
    image_name = serializers.CharField(label="镜像名称", help_text="示例： Ubuntu14.04")
    openstack_image_name = serializers.CharField(label="openstack端的镜像名称",
                                                 help_text="示例： uat-ubuntu-trusty-zabbix-agent.qcow2")
    status = serializers.CharField(label="镜像状态", help_text="示例： active")
    type = serializers.CharField(label="镜像类型", help_text="示例： Ubuntu")

    class Meta:
        model = ResponseNoneMeta
        fields = ["id", "image_name", "openstack_image_name", "status", "type"]


class InstQosPolicyDictInfoResponsesSerializer(serializers.ModelSerializer):
    id = serializers.CharField(label="带宽id", help_text="示例： 2425feb3-f324-44f6-b161-69bcebbb6cb6")
    qos_policy_count = serializers.CharField(label="带宽大小", help_text="示例： 1")
    qos_policy_name = serializers.CharField(label="带宽大小名称", help_text="示例： 1M")

    class Meta:
        model = ResponseNoneMeta
        fields = ["id", "qos_policy_count", "qos_policy_name"]


class InstQosPolicyListInfoResponsesSerializer(serializers.ModelSerializer):
    end = serializers.CharField(label="带宽范围", help_text="示例： 300（代表1-300）")
    qos_policy_dict = InstQosPolicyDictInfoResponsesSerializer(label="带宽字典信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["qos_policy_dict", "end"]


class InstFeedBackInfoResponsesSerializer(serializers.ModelSerializer):
    status = serializers.CharField(label="更新后的实例状态", help_text="示例： active")
    task = serializers.CharField(label="更新后的任务执行结果", help_text="示例：success")
    update_at = serializers.CharField(label="更新时间", help_text="2019-10-11 13:54:37.220506")

    class Meta:
        model = ResponseNoneMeta
        fields = ["status", "task", "update_at"]


class InstMachineGetnfoResponsesSerializer(serializers.ModelSerializer):
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-08-23 16:00:13 ")
    deleted = serializers.CharField(label="删除时间", help_text="示例：2019-08-23 16:00:13 ")
    disk_info = serializers.CharField(label="磁盘信息", help_text="示例： []")
    firewall_id = serializers.CharField(label="防火墙id", help_text="示例： null")
    firewall_name = serializers.CharField(label="防火墙名称", help_text="示例： null")
    flavor_id = serializers.CharField(label="flavor id", help_text="示例： 11a2c533-73cc-4f95-8e7b-0055b7ec18a7")
    flavor_name = serializers.CharField(label="flavor 名称", help_text="示例： 戴尔")
    floating_ip_allocation = serializers.CharField(label="弹性公网IP可用量", help_text="示例：null ")
    floating_ip_bandwidth = serializers.CharField(label="弹性公网IP带宽", help_text="示例：null ")
    floating_ip_info = serializers.CharField(label="弹性公网IP信息", help_text="示例： []")
    floating_ip_line = serializers.CharField(label="弹性公网IP类型", help_text="示例： null")
    id = serializers.CharField(label="machine id", help_text="示例：5d5f9d0c419049990ddd19d2 ")
    image_id = serializers.CharField(label="镜像id", help_text="示例：198e0048-c8b2-4db9-9f08-395ea005af21 ")
    image_name = serializers.CharField(label="镜像名称", help_text="示例：Windows2016 ")
    login_method = serializers.CharField(label="登陆方式", help_text="示例：user_password ")
    monitoring = serializers.CharField(label="是否携带监控", help_text="示例：False/True ")
    network = serializers.CharField(label="网络名称", help_text="示例：zx_vpc2_net ")
    network_id = serializers.CharField(label="网络id", help_text="示例：2a9b9e14-e9f8-4a04-819f-d9f68d4bfbe9 ")
    network_path_type = serializers.CharField(label="网络类型", help_text="示例：private ")
    order_id = serializers.CharField(label="订单id", help_text="示例：BMS201908231600122765752 ")
    public_key = serializers.CharField(label="公钥信息", help_text="示例： null")
    service_name = serializers.CharField(label="所生成服务器名称", help_text="示例：zhouxiao ")
    service_password = serializers.CharField(label="所生成服务器密码", help_text="示例：qwer1234QWER ")
    service_username = serializers.CharField(label="所生成服务器登录名", help_text="示例：root ")
    status = serializers.CharField(label="机器状态", help_text="示例：null ")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-08-26 09:57:29 ")
    uuid = serializers.CharField(label="实例所绑定的实例id", help_text="示例：c4130c54-bc4b-4249-928d-c014827653db ")
    vulnerability_scanning = serializers.CharField(label="是否携带漏洞扫描", help_text="示例：False/True ")

    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted", "disk_info", "firewall_id", "firewall_name", "flavor_id", "flavor_id",
                  "flavor_name", "floating_ip_allocation", "floating_ip_bandwidth", "floating_ip_info", "id",
                  "network_id", "image_id", "image_name", "login_method", "monitoring", "network",
                  "network_path_type", "order_id", "public_key", "service_name", "service_password",
                  "service_username", "status", "update_at", "uuid", "vulnerability_scanning",
                  "floating_ip_line"]


class InstMachineInfoFeedbackInfoResponsesSerializer(serializers.ModelSerializer):
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-08-23 16:00:13 ")
    deleted = serializers.CharField(label="删除时间", help_text="示例：2019-08-23 16:00:13 ")
    disk_info = serializers.CharField(label="磁盘信息", help_text="示例： []")
    firewall_id = serializers.CharField(label="防火墙id", help_text="示例： null")
    firewall_name = serializers.CharField(label="防火墙名称", help_text="示例： null")
    flavor_id = serializers.CharField(label="flavor id", help_text="示例： 11a2c533-73cc-4f95-8e7b-0055b7ec18a7")
    flavor_name = serializers.CharField(label="flavor 名称", help_text="示例： 戴尔")
    floating_ip_allocation = serializers.CharField(label="弹性公网IP可用量", help_text="示例：null ")
    floating_ip_bandwidth = serializers.CharField(label="弹性公网IP带宽", help_text="示例：null ")
    floating_ip_info = serializers.CharField(label="弹性公网IP信息", help_text="示例： []")
    floating_ip_line = serializers.CharField(label="弹性公网IP类型", help_text="示例： null")
    id = serializers.CharField(label="machine id", help_text="示例：5d5f9d0c419049990ddd19d2 ")
    image_id = serializers.CharField(label="镜像id", help_text="示例：198e0048-c8b2-4db9-9f08-395ea005af21 ")
    image_name = serializers.CharField(label="镜像名称", help_text="示例：Windows2016 ")
    login_method = serializers.CharField(label="登陆方式", help_text="示例：user_password ")
    monitoring = serializers.CharField(label="是否携带监控", help_text="示例：False/True ")
    network = serializers.CharField(label="网络名称", help_text="示例：zx_vpc2_net ")
    network_id = serializers.CharField(label="网络id", help_text="示例：2a9b9e14-e9f8-4a04-819f-d9f68d4bfbe9 ")
    network_path_type = serializers.CharField(label="网络类型", help_text="示例：private ")
    order_id = serializers.CharField(label="订单id", help_text="示例：BMS201908231600122765752 ")
    public_key = serializers.CharField(label="公钥信息", help_text="示例： null")
    service_name = serializers.CharField(label="所生成服务器名称", help_text="示例：zhouxiao ")
    service_password = serializers.CharField(label="所生成服务器密码", help_text="示例：qwer1234QWER ")
    service_username = serializers.CharField(label="所生成服务器登录名", help_text="示例：root ")
    status = serializers.CharField(label="机器状态", help_text="示例：null ")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-08-26 09:57:29 ")
    uuid = serializers.CharField(label="实例所绑定的实例id", help_text="示例：c4130c54-bc4b-4249-928d-c014827653db ")
    vulnerability_scanning = serializers.CharField(label="是否携带漏洞扫描", help_text="示例：False/True ")

    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted", "disk_info", "firewall_id", "firewall_name", "flavor_id", "flavor_id",
                  "flavor_name", "floating_ip_allocation", "floating_ip_bandwidth", "floating_ip_info", "id",
                  "network_id", "image_id", "image_name", "login_method", "monitoring", "network",
                  "network_path_type", "order_id", "public_key", "service_name", "service_password",
                  "service_username", "status", "update_at", "uuid", "vulnerability_scanning",
                  "floating_ip_line"]


class InstAllOrderInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：589d0d6781314a8b8c28cf3982ce344c")
    billing_model = serializers.CharField(label="合同类型", help_text="示例：框架合同")
    contract_number = serializers.CharField(label="合同编码", help_text="示例：wer234234324")
    create_at = serializers.CharField(label="合同创建时间", help_text="示例： 2019-10-10 17:06:08")
    deleted = serializers.CharField(label="合同删除时间", help_text="示例： null")
    delivery_status = serializers.CharField(label="订单交付状态", help_text="示例： rejected/delivered")
    id = serializers.CharField(label="订单id", help_text="示例： BMS201910101706051447155")
    order_price = serializers.CharField(label="订单价格", help_text="示例：1")
    order_type = serializers.CharField(label="订单类型", help_text="示例：新购 ")
    product_info = serializers.CharField(label="订单所购买产品信息", help_text="示例： []")
    product_type = serializers.CharField(label="产品类型", help_text="示例： 云硬盘")
    project_id = serializers.CharField(label="项目 id", help_text="示例：55e40f6dbb6549a19e235e1a7f2d88cf ")
    project_name = serializers.CharField(label="项目名称", help_text="示例：wei_forbidden22")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne ")
    service_count = serializers.CharField(label="订单所购买服务个数", help_text="示例：1 ")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "billing_model", "contract_number", "create_at", "deleted", "delivery_status",
                  "id", "order_price", "order_type", "product_info", "product_type", "project_id",
                  "project_name", "region", "service_count", "update_at"]


class InstOrderDeriveryUpdateInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：589d0d6781314a8b8c28cf3982ce344c")
    billing_model = serializers.CharField(label="合同类型", help_text="示例：框架合同")
    contract_number = serializers.CharField(label="合同编码", help_text="示例：wer234234324")
    create_at = serializers.CharField(label="合同创建时间", help_text="示例： 2019-10-10 17:06:08")
    deleted = serializers.CharField(label="合同删除时间", help_text="示例： null")
    delivery_status = serializers.CharField(label="订单交付状态", help_text="示例： rejected/delivered")
    id = serializers.CharField(label="订单id", help_text="示例： BMS201910101706051447155")
    order_price = serializers.CharField(label="订单价格", help_text="示例：1")
    order_type = serializers.CharField(label="订单类型", help_text="示例：新购 ")
    product_info = serializers.CharField(label="订单所购买产品信息", help_text="示例： []")
    product_type = serializers.CharField(label="产品类型", help_text="示例： 云硬盘")
    project_id = serializers.CharField(label="项目 id", help_text="示例：55e40f6dbb6549a19e235e1a7f2d88cf")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne ")
    service_count = serializers.CharField(label="订单所购买服务个数", help_text="示例：1 ")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "billing_model", "contract_number", "create_at", "deleted", "delivery_status",
                  "id", "order_price", "order_type", "product_info", "product_type", "project_id",
                  "region", "service_count", "update_at"]


class InstOrderByAccInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：589d0d6781314a8b8c28cf3982ce344c")
    billing_model = serializers.CharField(label="合同类型", help_text="示例：框架合同")
    contract_number = serializers.CharField(label="合同编码", help_text="示例：wer234234324")
    create_at = serializers.CharField(label="合同创建时间", help_text="示例： 2019-10-10 17:06:08")
    deleted = serializers.CharField(label="合同删除时间", help_text="示例： null")
    delivery_status = serializers.CharField(label="订单交付状态", help_text="示例： rejected/delivered")
    id = serializers.CharField(label="订单id", help_text="示例： BMS201910101706051447155")
    order_price = serializers.CharField(label="订单价格", help_text="示例：1")
    order_type = serializers.CharField(label="订单类型", help_text="示例：新购 ")
    product_info = serializers.CharField(label="订单所购买产品信息", help_text="示例： []")
    product_type = serializers.CharField(label="产品类型", help_text="示例： 云硬盘")
    project_id = serializers.CharField(label="项目 id", help_text="示例：55e40f6dbb6549a19e235e1a7f2d88cf")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne ")
    service_count = serializers.CharField(label="订单所购买服务个数", help_text="示例：1 ")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "billing_model", "contract_number", "create_at", "deleted", "delivery_status",
                  "id", "order_price", "order_type", "product_info", "product_type", "project_id",
                  "region", "service_count", "update_at"]


class InstUpdateFlavorCountInfoResponsesSerializer(serializers.ModelSerializer):
    DELL_VBS_RAID = serializers.CharField(label="基础型")
    DELL_VGS_RAID = serializers.CharField(label="计算型")
    DELL_VSS_RAID = serializers.CharField(label="存储型")

    class Meta:
        model = ResponseNoneMeta
        fields = ["DELL_VBS_RAID", "DELL_VGS_RAID", "DELL_VSS_RAID"]


class FlavorListResponsesSerializer(serializers.ModelSerializer):
    content = FlavorListInfoResponsesSerializer(label="查询到的机器信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstImageListResponsesSerializer(serializers.ModelSerializer):
    content = InstImageListInfoResponsesSerializer(label="查询到的机器信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstQosPolicyListResponsesSerializer(serializers.ModelSerializer):
    content = InstQosPolicyListInfoResponsesSerializer(label="获取到的带宽规则列表信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstFeedBackResponsesSerializer(serializers.ModelSerializer):
    content = InstFeedBackInfoResponsesSerializer(label="更新实例后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstMachineGetResponsesSerializer(serializers.ModelSerializer):
    content = InstMachineGetnfoResponsesSerializer(label="查询到的machine信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstMachineInfoFeedbackResponsesSerializer(serializers.ModelSerializer):
    content = InstMachineInfoFeedbackInfoResponsesSerializer(label="更新订单服务器信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstAllOrderResponsesSerializer(serializers.ModelSerializer):
    content = InstAllOrderInfoResponsesSerializer(label="查询到的所有订单信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstOrderDeliveryUpdateResponsesSerializer(serializers.ModelSerializer):
    content = InstOrderDeriveryUpdateInfoResponsesSerializer(label="查询到的所有订单信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：该订单 BMS201908231116166874034 无对应服务器交付信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class OrderByAccoInfoResponsesSerializer(serializers.ModelSerializer):
    content = InstOrderByAccInfoResponsesSerializer(label="查询到的订单信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：该订单 BMS201908231116166874034 无对应服务器交付信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class InstUpdateFlavorCountResponsesSerializer(serializers.ModelSerializer):
    content = InstUpdateFlavorCountInfoResponsesSerializer(label="更新后的Flavor个数信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：该订单 BMS201908231116166874034 无对应服务器交付信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFirewallInfoResponsesSerializer(serializers.ModelSerializer):
    create_at = serializers.CharField(label="防火墙创建时间", help_text="示例：")
    deleted_at = serializers.CharField(label="防火墙删除时间", help_text="示例：")
    description = serializers.CharField(label="描述信息")
    enabled = serializers.CharField(label="是否启动防火墙", help_text="示例：1/0")
    id = serializers.CharField(label="防火墙id", help_text="示例：5d5f59d7af7b14da70048a6f")
    name = serializers.CharField(label="防火墙名称", help_text="示例：默认防火墙")
    project_id = serializers.CharField(label="项目id", help_text="592a7b130b0c4b48ba3a1f9da70fc86e")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-09-24 14:39:14")

    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted_at", "description", "enabled", "id", "name", "project_id",
                  "region", "update_at"]


class FipFloatingIpAssociateFirewallInfoResponsesSerializer(serializers.ModelSerializer):
    firewall = FipFirewallInfoResponsesSerializer(label="弹性公网IP成功关联后的防火墙返回信息")
    floating_ip_id = serializers.CharField(label="弹性公网IP id",
                                           help_text="示例：1458e4d9-c0f0-46ae-96f6-3eac0cd34d33")

    class Meta:
        model = ResponseNoneMeta
        fields = ["firewall", "floating_ip_id"]


class FipFloatingIpAssociateFirewallResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpAssociateFirewallInfoResponsesSerializer(label="弹性公网IP成功关联后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：该订单 BMS201908231116166874034 无对应服务器交付信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpAttachToServerInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    attached = serializers.CharField(label="是否绑定", help_text="示例：true/False")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：Test_bz")
    create_at = serializers.CharField(label="绑定成功时间", help_text="示例：2019-09-24 14:29:30")
    external_line_type = serializers.CharField(label="对外网络类型", help_text="示例：three_line_ip")
    external_name = serializers.CharField(label="弹性公网IP物料名称", help_text="示例：External_Net1")
    external_name_id = serializers.CharField(label="弹性公网IP物料id",
                                             help_text="示例：98a35cf5-1bab-4950-b947-d9f198db046a")
    fixed_address = serializers.CharField(label="弹性公网IP所绑定的端口", help_text="示例：172.24.0.24")
    floating_ip = serializers.CharField(label="绑定的弹性公网IP", help_text="示例：10.100.2.172")
    floating_ip_id = serializers.CharField(label="绑定的弹性公网IP id",
                                           help_text="示例：172d6c81-595f-4aa6-b2f7-1ec99e01716c")
    id = serializers.CharField(label="标识", help_text="示例：5d89b7cac7c85c7bfc7093e9")
    instance_name = serializers.CharField(label="实例名称", help_text="示例：node_8_32")
    instance_uuid = serializers.CharField(label="实例id", help_text="示例：51c7094c-f039-41b5-865d-d37faa148c96")
    is_measure_end = serializers.CharField(label="当前IP有没有做过变更", help_text="示例：false/True")
    order_id = serializers.CharField(label="订单号", help_text="示例：BMS201909241429300929017")
    project_id = serializers.CharField(label="项目id", help_text="示例：d1f0dbdf0b764e7693e3e19783be0ea9")
    qos_policy_id = serializers.CharField(label="带宽id", help_text="示例：ce801724-7284-4a81-be1b-50b6f330bb29")
    qos_policy_name = serializers.CharField(label="带宽大小", help_text="示例：2M")
    status = serializers.CharField(label="状态", help_text="示例：active")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-10-12 16:21:43.621873")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached", "contract_number", "create_at", "external_line_type", "external_name",
                  "external_name_id", "fixed_address", "floating_ip", "floating_ip_id", "id", "instance_name",
                  "instance_uuid", "is_measure_end", "order_id", "project_id", "qos_policy_id", "qos_policy_name",
                  "status", "update_at", "external_line_type"]


class FipFloatingIpAttachToServerResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpAttachToServerInfoResponsesSerializer(label="弹性公网IP成功关联实例后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：该订单 BMS201908231116166874034 无对应服务器交付信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpListResultInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    attached = serializers.CharField(label="是否绑定服务器", help_text="示例：false/True")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：ding")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-10-14 10:10:08.082042")
    external_line_type = serializers.CharField(label="对外网络类型", help_text="示例：three_line_ip")
    external_name = serializers.CharField(label="弹性公网IP物料名称", help_text="示例：External_Net1")
    external_name_id = serializers.CharField(label="弹性公网IP物料id", help_text="示例：98a35cf5-1bab-4950-b947-d9f198db046a")
    firewall_info = serializers.CharField(label="防火墙信息")
    fixed_address = serializers.CharField(label="服务器内网IP端口")
    floating_ip = serializers.CharField(label="弹性公网IP", help_text="示例：10.100.2.172")
    floating_ip_id = serializers.CharField(label="弹性公网IP id", help_text="示例：41deaaeb-b007-41c2-8150-f953cb9765e9")
    id = serializers.CharField(label="标识", help_text="示例：5da3d900e115747865abf500")
    instance_name = serializers.CharField(label="实例名称", help_text="示例：null")
    instance_uuid = serializers.CharField(label="实例id", help_text="示例：null")
    is_measure_end = serializers.CharField(label="是否做过变更", help_text="示例：false")
    order_id = serializers.CharField(label="订单id", help_text="示例：BMS201910141010033503635")
    project_id = serializers.CharField(label="项目id", help_text="示例：d1f0dbdf0b764e7693e3e19783be0ea9")
    qos_policy_id = serializers.CharField(label="带宽id", help_text="示例：2671fc70-7018-4240-9177-f4209ea7ac35")
    qos_policy_name = serializers.CharField(label="带宽名称", help_text="示例：100M")
    status = serializers.CharField(label="状态", help_text="示例：active")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached", "contract_number", "create_at", "external_line_type",
                  "external_name", "external_name_id", "firewall_info", "fixed_address", "floating_ip",
                  "floating_ip_id", "id", "instance_name", "instance_uuid", "is_measure_end", "order_id",
                  "project_id", "qos_policy_id", "qos_policy_name", "status", "update_at"]


class FipFloatingIpCreatedInfoResponsesSerializer(serializers.ModelSerializer):
    floating_ip_list_result = FipFloatingIpListResultInfoResponsesSerializer(label="弹性公网IP创建成功返回信息")
    order_result = OrderByAccoInfoResponsesSerializer(label="返回订单信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["floating_ip_list_result", "order_result"]


class FipFloatingIpCreatedResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpCreatedInfoResponsesSerializer(label="弹性公网IP创建成功后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpDeletedResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：41deaaeb-b007-41c2-8150-f953cb9765e9: true")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpDetachFromServerInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    attached = serializers.CharField(label="是否绑定服务器", help_text="示例：false/True")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：ding")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-10-14 10:10:08.082042")
    external_line_type = serializers.CharField(label="对外网络类型", help_text="示例：three_line_ip")
    external_name = serializers.CharField(label="弹性公网IP物料名称", help_text="示例：External_Net1")
    external_name_id = serializers.CharField(label="弹性公网IP物料id", help_text="示例：98a35cf5-1bab-4950-b947-d9f198db046a")
    firewall_info = serializers.CharField(label="防火墙信息")
    fixed_address = serializers.CharField(label="服务器内网IP端口")
    floating_ip = serializers.CharField(label="弹性公网IP", help_text="示例：10.100.2.172")
    floating_ip_id = serializers.CharField(label="弹性公网IP id", help_text="示例：41deaaeb-b007-41c2-8150-f953cb9765e9")
    id = serializers.CharField(label="标识", help_text="示例：5da3d900e115747865abf500")
    instance_name = serializers.CharField(label="实例名称", help_text="示例：null")
    instance_uuid = serializers.CharField(label="实例id", help_text="示例：null")
    is_measure_end = serializers.CharField(label="是否做过变更", help_text="示例：false")
    order_id = serializers.CharField(label="订单id", help_text="示例：BMS201910141010033503635")
    project_id = serializers.CharField(label="项目id", help_text="示例：d1f0dbdf0b764e7693e3e19783be0ea9")
    qos_policy_id = serializers.CharField(label="带宽id", help_text="示例：2671fc70-7018-4240-9177-f4209ea7ac35")
    qos_policy_name = serializers.CharField(label="带宽名称", help_text="示例：100M")
    status = serializers.CharField(label="状态", help_text="示例：active")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached", "contract_number", "create_at", "external_line_type",
                  "external_name", "external_name_id", "firewall_info", "fixed_address", "floating_ip",
                  "floating_ip_id", "id", "instance_name", "instance_uuid", "is_measure_end", "order_id",
                  "project_id", "qos_policy_id", "qos_policy_name", "status", "update_at"]


class FipFloatingIpInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    attached = serializers.CharField(label="是否绑定服务器", help_text="示例：false/True")
    contract_info = serializers.CharField(label="合同信息")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：ding")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-10-14 10:10:08.082042")
    external_line_type = serializers.CharField(label="对外网络类型", help_text="示例：three_line_ip")
    external_name = serializers.CharField(label="弹性公网IP物料名称", help_text="示例：External_Net1")
    external_name_id = serializers.CharField(label="弹性公网IP物料id", help_text="示例：98a35cf5-1bab-4950-b947-d9f198db046a")
    firewall_info = serializers.CharField(label="防火墙信息")
    fixed_address = serializers.CharField(label="服务器内网IP端口")
    floating_ip = serializers.CharField(label="弹性公网IP", help_text="示例：10.100.2.172")
    floating_ip_id = serializers.CharField(label="弹性公网IP id", help_text="示例：41deaaeb-b007-41c2-8150-f953cb9765e9")
    id = serializers.CharField(label="标识", help_text="示例：5da3d900e115747865abf500")
    instance_name = serializers.CharField(label="实例名称", help_text="示例：null")
    instance_uuid = serializers.CharField(label="实例id", help_text="示例：null")
    is_measure_end = serializers.CharField(label="是否做过变更", help_text="示例：false")
    order_id = serializers.CharField(label="订单id", help_text="示例：BMS201910141010033503635")
    project_id = serializers.CharField(label="项目id", help_text="示例：d1f0dbdf0b764e7693e3e19783be0ea9")
    qos_policy_id = serializers.CharField(label="带宽id", help_text="示例：2671fc70-7018-4240-9177-f4209ea7ac35")
    qos_policy_name = serializers.CharField(label="带宽名称", help_text="示例：100M")
    status = serializers.CharField(label="状态", help_text="示例：active")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached", "contract_info", "contract_number", "create_at", "external_line_type",
                  "external_name", "external_name_id", "firewall_info", "fixed_address", "floating_ip",
                  "floating_ip_id", "id", "instance_name", "instance_uuid", "is_measure_end", "order_id",
                  "project_id", "qos_policy_id", "qos_policy_name", "status", "update_at"]


class FipFloatingIpQuotaSetInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    attached = serializers.CharField(label="是否绑定服务器", help_text="示例：false/True")
    contract_info = serializers.CharField(label="合同信息")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：ding")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-10-14 10:10:08.082042")
    external_line_type = serializers.CharField(label="对外网络类型", help_text="示例：three_line_ip")
    external_name = serializers.CharField(label="弹性公网IP物料名称", help_text="示例：External_Net1")
    external_name_id = serializers.CharField(label="弹性公网IP物料id", help_text="示例：98a35cf5-1bab-4950-b947-d9f198db046a")
    firewall_info = serializers.CharField(label="防火墙信息")
    fixed_address = serializers.CharField(label="服务器内网IP端口")
    floating_ip = serializers.CharField(label="弹性公网IP", help_text="示例：10.100.2.172")
    floating_ip_id = serializers.CharField(label="弹性公网IP id", help_text="示例：41deaaeb-b007-41c2-8150-f953cb9765e9")
    id = serializers.CharField(label="标识", help_text="示例：5da3d900e115747865abf500")
    instance_name = serializers.CharField(label="实例名称", help_text="示例：null")
    instance_uuid = serializers.CharField(label="实例id", help_text="示例：null")
    is_measure_end = serializers.CharField(label="是否做过变更", help_text="示例：false")
    order_id = serializers.CharField(label="订单id", help_text="示例：BMS201910141010033503635")
    project_id = serializers.CharField(label="项目id", help_text="示例：d1f0dbdf0b764e7693e3e19783be0ea9")
    qos_policy_id = serializers.CharField(label="带宽id", help_text="示例：2671fc70-7018-4240-9177-f4209ea7ac35")
    qos_policy_name = serializers.CharField(label="带宽名称", help_text="示例：100M")
    status = serializers.CharField(label="状态", help_text="示例：active")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached", "contract_info", "contract_number", "create_at", "external_line_type",
                  "external_name", "external_name_id", "firewall_info", "fixed_address", "floating_ip",
                  "floating_ip_id", "id", "instance_name", "instance_uuid", "is_measure_end", "order_id",
                  "project_id", "qos_policy_id", "qos_policy_name", "status", "update_at"]


class FipFloatingIpQuotaInfoResponsesSerializer(serializers.ModelSerializer):
    available_fip_quota = serializers.CharField(label="浮动IP可用配额", help_text="示例：19")

    class Meta:
        model = ResponseNoneMeta
        fields = ["available_fip_quota"]


class FipFloatingIpDetachFromServerResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpDetachFromServerInfoResponsesSerializer(label="弹性公网IP解绑实例成功后返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpListResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpInfoResponsesSerializer(label="查询成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpQuotaResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpQuotaInfoResponsesSerializer(label="查询成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipFloatingIpQuotaSetResponsesSerializer(serializers.ModelSerializer):
    content = FipFloatingIpQuotaSetInfoResponsesSerializer(label="调整弹性公网IP带宽后返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AvaliableInstanceInfoResponsesSerializer(serializers.ModelSerializer):
    instance_id = serializers.CharField(label="实例id", help_text="示例：cafc0e26-7a34-40af-9cb4-ba1d987c6b90")
    instance_name = serializers.CharField(label="浮动IP可用配额", help_text="示例：centos7-base-1011")
    port = serializers.CharField(label="浮动IP可用配额", help_text="示例：['192.168.45.21']")

    class Meta:
        model = ResponseNoneMeta
        fields = ["instance_id", "instance_name", "port"]


class InstAvaliableInstanceListResponsesSerializer(serializers.ModelSerializer):
    content = AvaliableInstanceInfoResponsesSerializer(label="查询可绑定实例列表")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FeedbackVbsAttachInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id", help_text="示例：af95a6b571bd4d7e9e713d8c107d7f89")
    attached_type = serializers.CharField(label="绑定类型", help_text="示例：裸金属服务器")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：ding123")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-10-17 11:18:48")
    first_create_at = serializers.CharField(label="第一次创建时间", help_text="示例：2019-10-17 11:18:48")
    id = serializers.CharField(label="标识", help_text="示例：5da7dd97f37056ff1229ae60")
    instance_name = serializers.CharField(label="实例名称", help_text="示例：cen7")
    instance_uuid = serializers.CharField(label="实例ID", help_text="示例：776c046b-4675-4ccb-a16a-30db03e44caa")
    is_measure_end = serializers.CharField(label="是否做过变更操作", help_text="示例：0/1")
    name = serializers.CharField(label="云硬盘名称", help_text="示例：u1810_14_volume_1")
    order_id = serializers.CharField(label="订单ID", help_text="示例：BMS201910171104454214082")
    project_id = serializers.CharField(label="项目ID", help_text="示例：68c50c64def84818948b1dc4320a44fa")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne")
    size = serializers.CharField(label="云硬盘大小", help_text="示例：13")
    update_at = serializers.CharField(label="更新时间", help_text="示例：null")
    volume_id = serializers.CharField(label="云硬盘ID", help_text="示例：b264e220-8d1c-4695-9941-e1c19a99a246")
    volume_type = serializers.CharField(label="云硬盘类型", help_text="示例：inspure_iscsi")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached_type", "contract_number","create_at", "first_create_at",
                  "id","instance_name","instance_uuid", "is_measure_end", "name", "order_id","project_id",
                  "region", "size","update_at", "volume_id", "volume_type",
                 ]


class FeedbackVbsAttachResponsesSerializer(serializers.ModelSerializer):
    content = FeedbackVbsAttachInfoResponsesSerializer(label="返回的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsObjectStoreInfoResponsesSerializer(serializers.ModelSerializer):
    container_bytes_used = serializers.CharField(label="所用字节数", help_text="0")
    container_object_count = serializers.CharField(label="对象数", help_text="0")
    is_public = serializers.CharField(label="权限是否公有", help_text="True/False")
    name = serializers.CharField(label="桶名称", help_text="ding")
    public_url = serializers.CharField(label="域名", help_text="")
    timestamp = serializers.CharField(label="创建时间", help_text="示例：2019-10-15 12:45:13")

    class Meta:
        model = ResponseNoneMeta
        fields = ["container_bytes_used", "container_object_count", "is_public", "name", "public_url", "timestamp"]


class ObsCreatedBucketInfoResponsesSerializer(serializers.ModelSerializer):
    object_store = ObsObjectStoreInfoResponsesSerializer(label="桶的信息")
    order_result = OrderByAccoInfoResponsesSerializer(label="订单信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["object_store", "order_result"]


class ObsCreatedBucketResponsesSerializer(serializers.ModelSerializer):
    content = ObsCreatedBucketInfoResponsesSerializer(label="返回的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsDeleteBucketResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="删除桶成功")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsDeleteObjectsResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="删除对象成功")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsUpdateBucketResponsesSerializer(serializers.ModelSerializer):
    content = ObsObjectStoreInfoResponsesSerializer(label="成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsBucketListResponsesSerializer(serializers.ModelSerializer):
    content = ObsObjectStoreInfoResponsesSerializer(label="成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsObjectsInfoResponsesSerializer(serializers.ModelSerializer):
    bytes = serializers.CharField(label="字节数", help_text="示例：21735")
    content_type = serializers.CharField(label="类型", help_text="示例：image/png")
    is_object = serializers.CharField(label="是否是对象存储", help_text="示例：true/False")
    is_subdir = serializers.CharField(label="是否是目录", help_text="示例：false/True")
    name = serializers.CharField(label="名称", help_text="示例：2019-04-04_144415.png")
    path = serializers.CharField(label="路径", help_text="示例：2019-04-04_144415.png")
    timestamp = serializers.CharField(label="创建时间", help_text="示例：2019-08-26 10:38:04")

    class Meta:
        model = ResponseNoneMeta
        fields = ["bytes", "content_type", "is_object", "is_subdir", "name", "path", "timestamp"]


class ObsCreatedDirInfoResponsesSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(label="类型", help_text="示例：application/pseudo-folder")
    is_object = serializers.CharField(label="是否是对象存储", help_text="示例：true/False")
    is_subdir = serializers.CharField(label="是否是目录", help_text="示例：false/True")
    name = serializers.CharField(label="名称", help_text="示例：da/ding")
    path = serializers.CharField(label="路径", help_text="示例：da/ding")
    etag = serializers.CharField(label="标签", help_text="示例：d41d8cd98f00b204e9800998ecf8427e")

    class Meta:
        model = ResponseNoneMeta
        fields = ["etag", "content_type", "is_object", "is_subdir", "name", "path"]


class ObsObjectsReturnInfoResponsesSerializer(serializers.ModelSerializer):
    objects = ObsObjectsInfoResponsesSerializer(label="返回信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["objects"]


class ObsObjectsListResponsesSerializer(serializers.ModelSerializer):
    content = ObsObjectsReturnInfoResponsesSerializer(label="成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsCreatedDirResponsesSerializer(serializers.ModelSerializer):
    content = ObsCreatedDirInfoResponsesSerializer(label="成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ObsUploadFileInfoResponsesSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(label="类型", help_text="示例：application/pseudo-folder")
    timestamp = serializers.CharField(label="创建时间", help_text="示例：2019-10-15 16:20:00")
    bytes = serializers.CharField(label="字节数", help_text="示例：1630")
    name = serializers.CharField(label="名称", help_text="示例：da/ding")
    path = serializers.CharField(label="路径", help_text="示例：da/ding")
    etag = serializers.CharField(label="标签", help_text="示例：d41d8cd98f00b204e9800998ecf8427e")

    class Meta:
        model = ResponseNoneMeta
        fields = ["etag", "content_type", "timestamp", "bytes", "name", "path"]


class ObsUploadFileResponsesSerializer(serializers.ModelSerializer):
    content = ObsUploadFileInfoResponsesSerializer(label="成功返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsBackupInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id",help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    backup_id = serializers.CharField(label="云硬盘备份id",help_text="示例：36ba4835-9f1c-4157-99a5-7d68f812fdbb")
    backup_name = serializers.CharField(label="云硬盘备份名称", help_text="示例：ding_test")
    contract_number = serializers.CharField(label="合同编码", help_text="示例：ding123")
    deleted = serializers.CharField(label="是否删除",help_text="示例：false")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-10-31 09:40:02.953899")
    is_incremental = serializers.CharField(label="是否是增量备份", help_text="示例：false")
    is_measure_end = serializers.CharField(label="是否做过变更操作", help_text="示例：0")
    order_id = serializers.CharField(label="订单号", help_text="示例：BMS201910310940014159732")
    project_id = serializers.CharField(label="项目id", help_text="示例：68c50c64def84818948b1dc4320a44fa")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne")
    status = serializers.CharField(label="状态", help_text="示例：creating")
    update_at = serializers.CharField(label="更新时间", help_text="示例：")
    volume_id = serializers.CharField(label="云硬盘id", help_text="示例：bdbdd6f9-6c5f-4b33-bf19-563389565d3f")
    volume_name = serializers.CharField(label="云硬盘名称", help_text="示例：ds2334445555555555555555566666666")



    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "backup_id","backup_name","contract_number","create_at","deleted",
                  "is_incremental","is_measure_end","order_id","project_id","region","status","update_at",
                  "volume_id","volume_name"]


class VbsBackupCreateInfoResponsesSerializer(serializers.ModelSerializer):
    backup_result = VbsBackupInfoResponsesSerializer(label="云硬盘备份的信息")
    order_result = OrderByAccoInfoResponsesSerializer(label="成功返回的信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["backup_result", "order_result"]


class VbsBackupCreateResponsesSerializer(serializers.ModelSerializer):
    content = VbsBackupCreateInfoResponsesSerializer(label="成功返回的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsBackupDeletedResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsBackupListInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id",help_text="示例：af95a6b571bd4d7e9e713d8c107d7f89")
    availability_zone = serializers.CharField(label="", help_text="示例：nova")
    backup_id = serializers.CharField(label="备份id", help_text="示例：3602a578-90e2-4cc0-92f0-557a03072d1b")
    backup_name = serializers.CharField(label="备份名称", help_text="示例：ee")
    container = serializers.CharField(label="容器名称", help_text="示例：backups")
    contract_info = serializers.CharField(label="合同信息", help_text="示例：")
    contract_number = serializers.CharField(label="合同编码", help_text="示例：ECBM0001")
    create_at = serializers.CharField(label="创建时间", help_text="示例：2019-09-24 14:28:52")
    data_timestamp = serializers.CharField(label="", help_text="示例：2019-09-24T06:28:50.000000")
    deleted = serializers.CharField(label="是否删除", help_text="示例：false")
    description = serializers.CharField(label="描述信息", help_text="示例：")
    fail_reason = serializers.CharField(label="失败信息", help_text="示例：")
    has_dependent_backups = serializers.CharField(label="是否有备份", help_text="示例：false")
    id = serializers.CharField(label="", help_text="示例：3602a578-90e2-4cc0-92f0-557a03072d1b")
    is_incremental = serializers.CharField(label="是否是增量备份", help_text="示例：false")
    is_measure_end = serializers.CharField(label="是否做过变更操作", help_text="示例：0")
    links = serializers.CharField(label="链接信息", help_text="示例：")
    name = serializers.CharField(label="备份名称", help_text="示例：ee")
    object_count = serializers.CharField(label="备份数量", help_text="示例：0")
    order_id = serializers.CharField(label="订单号", help_text="示例：BMS201909241428490805483")
    project_id = serializers.CharField(label="项目id", help_text="示例：0c451e4592f34062ad64225b4defb095")
    region = serializers.CharField(label="可用区", help_text="示例：regionOne")
    size = serializers.CharField(label="云硬盘备份大小", help_text="示例：10")
    status = serializers.CharField(label="状态", help_text="示例：available")
    snapshot_id = serializers.CharField(label="快照id", help_text="示例：available")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-09-24T06:36:14.000000")
    volume_id = serializers.CharField(label="云硬盘id", help_text="示例：8a8446f7-3b8c-4017-b46b-557af583c2c0")
    volume_name = serializers.CharField(label="云硬盘名称", help_text="示例：bzadminbuy_volume_1")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id","backup_id","availability_zone", "backup_name", "container","contract_info","contract_number",
                  "create_at","data_timestamp","deleted","has_dependent_backups",
                  "description","fail_reason","has_dependent_backups",
                  "fail_reason","id","is_incremental","is_measure_end","links","name","object_count","order_id",
                  "project_id","region","size","snapshot_id","status","update_at","volume_id","volume_name"]


class VbsBackupListResponsesSerializer(serializers.ModelSerializer):
    content = VbsBackupListInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsResultInfoResponsesSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(label="用户id",help_text="示例：eaaafbf4d92949d2bec2d5e91c0d9940")
    attached_type = serializers.CharField(label="",help_text="示例：")
    contract_number = serializers.CharField(label="合同编号",help_text="示例：ding123")
    create_at = serializers.CharField(label="创建时间",help_text="示例：2019-10-31 14:06:12.173260")
    first_create_at = serializers.CharField(label="第一次创建时间",help_text="示例：2019-10-31 14:06:12.173274")
    id = serializers.CharField(label="",help_text="示例：5dba79d445ae30ff4994cf4c")
    instance_name = serializers.CharField(label="实例名称",help_text="示例：")
    instance_uuid = serializers.CharField(label="实例id",help_text="示例：")
    is_measure_end = serializers.CharField(label="是否做过变更",help_text="示例：false")
    name = serializers.CharField(label="云硬盘名称",help_text="示例：ding")
    order_id = serializers.CharField(label="订单号",help_text="示例：BMS201910311406077779899")
    project_id = serializers.CharField(label="项目id",help_text="示例：68c50c64def84818948b1dc4320a44fa")
    region = serializers.CharField(label="可用区",help_text="示例：regionOne")
    size = serializers.CharField(label="云硬盘大小",help_text="示例：512")
    update_at = serializers.CharField(label="更新时间",help_text="示例：")
    volume_id = serializers.CharField(label="云硬盘id",help_text="示例：017ddedc-e474-4406-9b64-6548de74ac13")
    volume_type = serializers.CharField(label="云硬盘类型",help_text="示例：inspure_iscsi")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "attached_type","contract_number","create_at","first_create_at","id",
                  "instance_name","instance_uuid","is_measure_end","name","order_id","project_id","region",
                  "size","update_at","volume_id","volume_type"]


class VbsCreatedInfoResponsesSerializer(serializers.ModelSerializer):
    order_result = OrderByAccoInfoResponsesSerializer(label="订单信息")
    volumes_result = VbsResultInfoResponsesSerializer(label="云硬盘信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["order_result", "volumes_result"]


class VbsCreatedResponsesSerializer(serializers.ModelSerializer):
    content = VbsCreatedInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsDeletedResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功返回的信息",help_text="示例：删除磁盘成功")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsDetachResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功返回的信息",help_text="示例：磁盘卸载成功")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsListResponsesSerializer(serializers.ModelSerializer):
    content = VbsResultInfoResponsesSerializer(label="成功返回的信息",help_text="示例：磁盘卸载成功")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class VbsUpdateResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class LassLoadBalancersIDsResponsesSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(label="负载均衡器ID")
    class Meta:
        model = ResponseNoneMeta
        fields = ["id"]


class LassListenersIDListResponsesSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(label="监听器ID")
    class Meta:
        model = ResponseNoneMeta
        fields = ["id"]


class LassPoolsIDListResponsesSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(label="资源池ID")
    class Meta:
        model = ResponseNoneMeta
        fields = ["id"]


class LassHealthMonitorsIdsResponsesSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(label="健康监听器ID")
    class Meta:
        model = ResponseNoneMeta
        fields = ["id"]


class LassMembersIDListResponsesSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(label="资源池成员ID")
    class Meta:
        model = ResponseNoneMeta
        fields = ["id"]


class LassHealthMonitorsCreatedInfoResponsesSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(label="资源管理状态")
    created_at = serializers.CharField(label="资源创建时间的UTC日期和时间戳")
    delay = serializers.IntegerField(label="向资源池成员发送检查的时延（单位：秒）")
    domain_name = serializers.CharField(label="HTTP Host Header中包含的域名信息")
    expected_codes = serializers.ListField(label="资源池成员为通报健康状况而响应的HTTP状态码列表")
    http_method = serializers.CharField(label="健康监听器用于请求的HTTP方法")
    http_version = serializers.FloatField(label="HTTP版本")
    id = serializers.UUIDField(label="相关健康监听器ID")
    max_retries = serializers.IntegerField(label="将operating status变为ONLINE之前成功检查的次数")
    max_retries_down = serializers.IntegerField(label="将operating status变为ERROR之前允许的最大检查失败次数")
    name = serializers.CharField(label="资源名称")
    operating_status = serializers.CharField(label="资源操作状态",help_text="示例：ONLINE, DRAINING, OFFLINE, DEGRADED, ERROR, NO_MONITOR")
    pool_id = serializers.UUIDField(label="资源池ID")
    project_id = serializers.CharField(label="资源所属项目ID")
    provisioning_status = serializers.CharField(label="资源供应信息",help_text="示例：ACTIVE, DELETED, ERROR, PENDING_CREATE, PENDING_UPDATE, PENDING_PENDING_DELETE")
    tags = serializers.ListField(label="赋值给资源的字符串列表")
    timeout = serializers.IntegerField(label="健康监听器等待连接的最长时间（单位：秒），该值必须小于delay")
    type = serializers.CharField(label="健康监听器类型",help_text="示例：HTTP, HTTPS, PING, TCP, TLS-HELLO, 或UDP-CONNECT")
    updated_at = serializers.CharField(label="资源最近一次更新时间的UTC日期和时间戳")
    url_path = serializers.CharField(label="健康监听器发送的HTTP请求URL路径")

    class Meta:
        model = ResponseNoneMeta
        fields = ["admin_state_up", "created_at", "delay", "domain_name",
                  'expected_codes', 'http_method', 'http_version', 'id',
                  'max_retries', 'max_retries_down', 'name', 'operating_status',
                  'pool_id', 'project_id', 'provisioning_status', 'tags',
                  'timeout', 'type', 'updated_at', 'url_path']


class LassCreateHealthMonitorsResponsesSerializer(serializers.ModelSerializer):
    content = LassHealthMonitorsCreatedInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class LassMembersCreatedInfoResponsesSerializer(serializers.ModelSerializer):
    address = serializers.CharField(label="后端资源池成员服务器IP地址")
    admin_state_up = serializers.BooleanField(label="资源管理状态")
    backup = serializers.BooleanField(label="资源池成员是否为备份",help_text="示例：true, false")
    created_at = serializers.CharField(label="资源创建时间的UTC日期和时间戳")
    id = serializers.UUIDField(label="资源池成员ID")
    name = serializers.CharField(label="资源名称")
    operating_status = serializers.CharField(label="资源操作状态",help_text="示例：ONLINE, DRAINING, OFFLINE, DEGRADED, ERROR, NO_MONITOR")
    project_id = serializers.CharField(label="资源所属项目ID")
    protocol_port = serializers.IntegerField(label="后端资源池成员服务器监听的协议端口号")
    provisioning_status = serializers.CharField(label="资源供应信息",help_text="示例：ACTIVE, DELETED, ERROR, PENDING_CREATE, PENDING_UPDATE, PENDING_PENDING_DELETE")
    subnet_id = serializers.CharField(label="资源池成员服务子网ID")
    tags = serializers.ListField(label="赋值给资源的字符串列表")
    updated_at = serializers.CharField(label="资源最近一次更新时间的UTC日期和时间戳")
    weight = serializers.IntegerField(label="资源池成员权重")

    class Meta:
        model = ResponseNoneMeta
        fields = ["address", "admin_state_up", "backup", "created_at",
                  'id', 'name', 'operating_status', 'project_id',
                  'protocol_port', 'provisioning_status', 'subnet_id', 'tags',
                  'updated_at', 'weight']


class LassCreateMembersResponsesSerializer(serializers.ModelSerializer):
    content = LassMembersCreatedInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class LassPoolsSessionPersistenceSerializer(serializers.ModelSerializer):
    type = serializers.CharField(label="资源池会话持久类型")
    cookie_name = serializers.CharField(label="会话持久的cookie名称")
    persistence_timeout = serializers.IntegerField(label="UDP流被重新分配到一个不同成员后的超时时间，仅用于UDP资源池（单位：秒）")
    persistence_granularity = serializers.CharField(label="用于确定UDP会话持久的网络掩码，仅用于UDP资源池（default: 255.255.255.255）")

    class Meta:
        model = ResponseNoneMeta
        fields = ["type", "cookie_name", "persistence_timeout", "persistence_granularity"]


class LassPoolsCreatedInfoResponsesSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(label="资源管理状态")
    ca_tls_container_ref = serializers.CharField(label="密钥管理服务的引用")
    created_at = serializers.CharField(label="资源创建时间的UTC日期和时间戳")
    crl_container_ref = serializers.CharField(label="密钥管理服务的URL（PEM格式）")
    description = serializers.CharField(label="资源描述信息")
    healthmonitor_id = serializers.UUIDField(label="健康监听器ID")  # HealthMonitorsIDListResponsesSerializer
    id = serializers.UUIDField(label="资源池ID")
    lb_algorithm = serializers.CharField(label="负载均衡器对资源池的算法")
    listeners = LassListenersIDListResponsesSerializer(label="监听器ID列表")  # LassListenersIDListResponsesSerializer
    loadbalancers = LassLoadBalancersIDsResponsesSerializer(label="监听器ID列表")  # LassLoadBalancersIDsResponsesSerializer
    members = LassMembersIDListResponsesSerializer(label="资源池成员ID列表")  # LassMembersIDListResponsesSerializer
    name = serializers.CharField(label="资源名称")
    operating_status = serializers.CharField(label="资源操作状态",help_text="示例：ONLINE, DRAINING, OFFLINE, DEGRADED, ERROR, NO_MONITOR")
    project_id = serializers.CharField(label="项目ID")
    protocol = serializers.CharField(label="资源协议")
    provisioning_status = serializers.CharField(label="资源供应信息",help_text="示例：ACTIVE, DELETED, ERROR, PENDING_CREATE, PENDING_UPDATE, PENDING_PENDING_DELETE")
    session_persistence = LassPoolsSessionPersistenceSerializer(label="资源池会话持久对象")  # LassPoolsSessionPersistenceSerializer
    tags = serializers.ListField(label="赋值给资源的字符串列表")
    tls_enabled = serializers.BooleanField(label="是否对后端资源池成员服务器的连接使用TLS加密",help_text="示例：true, false（默认）")
    tls_container_ref = serializers.CharField(label="密钥管理服务的引用（PKCS12格式）")
    updated_at = serializers.CharField(label="资源最近一次更新时间的UTC日期和时间戳")

    class Meta:
        model = ResponseNoneMeta
        fields = ["admin_state_up", "ca_tls_container_ref", "created_at", "crl_container_ref",
                  'description', 'healthmonitor_id', 'id', 'lb_algorithm',
                  'listeners', 'loadbalancers', 'members', 'name',
                  'operating_status', 'project_id', 'protocol', 'provisioning_status',
                  'session_persistence', 'tags', 'tls_enabled', 'tls_container_ref', "updated_at"]


class LassCreatePoolsResponsesSerializer(serializers.ModelSerializer):
    content = LassPoolsCreatedInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class HTTPHeaderResponsesSerializer(serializers.ModelSerializer):
    X_Forward_For = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_Forward_Port = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_Forward_Proto = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_Verify = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_Has_Cert = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_DN = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_CN = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Issuer = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_SHA1 = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_Not_Before = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")
    X_SSL_Client_Not_After = serializers.CharField(label="是否插入客户端IP地址到请求头",help_text="示例：true, false")

    class Meta:
        model = ResponseNoneMeta
        fields = ["X_Forward_For", "X_Forward_Port", "X_Forward_Proto", "X_SSL_Client_Verify",
                  "X_SSL_Client_Has_Cert", "X_SSL_Client_DN", "X_SSL_Client_CN", "X_SSL_Issuer",
                  "X_SSL_Client_SHA1", "X_SSL_Client_Not_Before", "X_SSL_Client_Not_After"]


class LassListenersCreatedInfoResponsesSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(label="资源管理状态")
    allowed_cidrs = serializers.ListField(label="CIDR列表")
    client_authentication = serializers.CharField(label="TLS客户端认证模式",help_text="示例：NONE, OPTIONAL, 或MANDATORY")
    client_ca_tls_container_ref = serializers.CharField(label="密钥管理服务的引用")
    client_crl_container_ref = serializers.CharField(label="密钥管理服务的URL（PEM格式）")
    connection_limit = serializers.IntegerField(label="当前监听器的最大连接数")
    created_at = serializers.CharField(label="监听器创建时间的UTC日期和时间戳")
    default_pool_id = serializers.UUIDField(label="监听器的默认资源池ID")
    default_tls_container_ref = serializers.CharField(label="密钥管理服务的URL（PKCS12格式）")
    description = serializers.CharField(label="资源描述信息")
    id = serializers.UUIDField(label="监听器ID")
    insert_headers = HTTPHeaderResponsesSerializer(label="可选请求参数头字典")  # HTTPHeaderResponsesSerializer
    loadbalancers = LassLoadBalancersIDsResponsesSerializer(label="负载均衡器ID列表")  # LassLoadBalancersIDsResponsesSerializer
    name = serializers.CharField(label="资源名称")
    operating_status = serializers.CharField(label="资源操作状态",help_text="示例：ONLINE, DRAINING, OFFLINE, DEGRADED, ERROR, NO_MONITOR")
    project_id = serializers.CharField(label="项目ID")
    protocol = serializers.CharField(label="资源协议")
    protocol_port = serializers.IntegerField(label="资源协议端口号")
    provisioning_status = serializers.CharField(label="资源供应信息",help_text="示例：ACTIVE, DELETED, ERROR, PENDING_CREATE, PENDING_UPDATE, PENDING_PENDING_DELETE")
    sni_container_refs = serializers.ListField(label="密钥管理服务的URL（PKCS12格式）列表")
    tags = serializers.ListField(label="赋值给资源的字符串列表")
    timeout_client_data = serializers.IntegerField(label="前端客户端失活超时（单位：毫秒）")
    timeout_member_conn = serializers.IntegerField(label="后端成员连接超时（单位：毫秒）")
    timeout_member_data = serializers.IntegerField(label="后端成员失活超时（单位：毫秒）")
    timeout_tcp_inspect = serializers.IntegerField(label="等待额外用于内容检查的TCP包的超时时间（单位：毫秒）")
    updated_at = serializers.CharField(label="资源最近一次更新时间的UTC日期和时间戳")

    class Meta:
        model = ResponseNoneMeta
        fields = ['admin_state_up', 'allowed_cidrs', 'client_authentication', 'client_ca_tls_container_ref',
                  'client_crl_container_ref', 'connection_limit', 'created_at', 'default_pool_id',
                  'default_tls_container_ref', 'description', 'id', 'insert_headers',
                  'loadbalancers', 'name', 'operating_status', 'project_id',
                  'protocol', 'protocol_port', 'provisioning_status', 'sni_container_refs',
                  'tags', 'timeout_client_data', 'timeout_member_conn', 'timeout_member_data',
                  'timeout_tcp_inspect', 'updated_at']


class LassCreateListenersResponsesSerializer(serializers.ModelSerializer):
    content = LassListenersCreatedInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class LassLoadBalancersInfoResponsesSerializer(serializers.ModelSerializer):
    admin_state_up = serializers.BooleanField(label="资源管理状态")
    created_at = serializers.CharField(label="资源创建时间的UTC日期和时间戳")
    description = serializers.CharField(label="资源描述信息")
    flavor_id = serializers.UUIDField(label="资源类型ID")
    id = serializers.UUIDField(label="负载均衡器ID")
    listeners = LassListenersCreatedInfoResponsesSerializer(label="监听器列表")  # ListenersCreatedInfoResponsesSerializer
    name = serializers.CharField(label="资源名称")
    operating_status = serializers.CharField(label="资源操作状态",help_text="示例：ONLINE, DRAINING, OFFLINE, DEGRADED, ERROR, NO_MONITOR")
    pools = LassPoolsCreatedInfoResponsesSerializer(label="资源池列表")  # LassPoolsCreatedInfoResponsesSerializer
    project_id = serializers.CharField(label="项目ID")
    provider = serializers.CharField(label="负载均衡器提供商名称")
    provisioning_status = serializers.CharField(label="资源供应信息",help_text="示例：ACTIVE, DELETED, ERROR, PENDING_CREATE, PENDING_UPDATE, PENDING_PENDING_DELETE")
    tags = serializers.ListField(label="赋值给资源的字符串列表")
    updated_at = serializers.CharField(label="资源最近一次更新时间的UTC日期和时间戳")
    vip_address = serializers.CharField(label="VIP的IP地址")
    vip_network_id = serializers.UUIDField(label="VIP网络ID")
    vip_port_id = serializers.UUIDField(label="VIP端口ID")
    vip_qos_policy_id = serializers.UUIDField(label="QoS策略ID")
    vip_subnet_id = serializers.CharField(label="VIP子网ID")

    class Meta:
        model = ResponseNoneMeta
        fields = ['admin_state_up', 'created_at', 'description', 'flavor_id',
                  'id', 'listeners', 'name', 'operating_status',
                  'pools', 'project_id', 'provider', 'provisioning_status',
                  'tags', 'updated_at', 'vip_address', 'vip_network_id',
                  'vip_port_id', 'vip_qos_policy_id', 'vip_subnet_id']


class LassCreateLoadBalancersResponsesSerializer(serializers.ModelSerializer):
    content = LassLoadBalancersInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class LassShowLoadBalancerResponsesSerializer(serializers.ModelSerializer):
    content = LassLoadBalancersInfoResponsesSerializer(label="成功返回的信息",help_text="示例：success")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class GetInfoByKeywordsResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="根据关键词查询成功后的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContactToUsResponsesSerializer(serializers.ModelSerializer):
    company = serializers.CharField(label="公司",help_text="示例： 世纪互联")
    created_at = serializers.CharField(label="表单提交时间",help_text="示例： 2019-10-11 10:03:00")
    customer_name = serializers.CharField(label="客户姓名",help_text="示例： 丁淑倩")
    department = serializers.CharField(label="顾客部门",help_text="示例： 产品研发")
    email = serializers.CharField(label="顾客电子邮箱",help_text="示例： ding.shuqian@21vianet.com")
    id = serializers.CharField(label="表单id",help_text="示例： BMCTU201910111003088751713")
    issue_content = serializers.CharField(label="问题描述",help_text="示例： 用于测试，请忽略本次提交")
    issue_type = serializers.CharField(label="问题类型",help_text="示例： 非必填项")
    connect_referrer = serializers.CharField(label="推荐人", help_text="示例： 丁淑倩")
    job_position = serializers.CharField(label="作废字段")
    phone = serializers.CharField(label="顾客电话号码",help_text="示例： 15103837705")
    update_at = serializers.CharField(label="作废字段")

    class Meta:
        model = ResponseNoneMeta
        fields = ["company", "created_at", "customer_name", "department","email","id",
                  "issue_content","issue_type","job_position","phone","update_at","connect_referrer"]


class IamLoginUserInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="账号邮箱", help_text="示例：wei.admin@21vianet.com")
    default_project_id = serializers.CharField(label="默认项目ID", help_text="示例：7ae5a60714014778baddea703b85cd93")
    default_project_name = serializers.CharField(label="默认项目名称", help_text="示例：admin")
    id = serializers.CharField(label="账号ID", help_text="示例：1fb97752f21e4355a72cce2e9e9beee5")
    identity_name = serializers.CharField(label="账号身份名称", help_text="示例：魏盼龙")
    query_token = serializers.CharField(label="websoket查询token", help_text="示例：")
    role_limit = serializers.CharField(label="账号角色值", help_text="示例：20")
    status = serializers.CharField(label="账号状态", help_text="示例：active")
    user_agreement = serializers.CharField(label="账号是否同意用户协议", help_text="示例：True/False")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "default_project_id", "default_project_name", "id", "identity_name",
                  "query_token", "role_limit", "status","user_agreement"]


class IamLoginResponsesInfo(serializers.ModelSerializer):
    token = serializers.CharField(label="用户验证码", help_text="示例：a7f8e458e808d05e9148a780d412d99b|1568096396.2957418")
    user_info = IamLoginUserInfo(label="用户信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["token", "user_info"]

class IamAkResponsesInfo(serializers.ModelSerializer):
    access_key = serializers.CharField(
        label="访问密钥access key",
        help_text="示例：ca038fe789854a748e7930610229b7c5")
    secret_key = serializers.CharField(
        label="访问秘钥secret key",
        help_text="示例：gJXG62ewNMoGRFcbccijRht6uFgqDv"
    )
    enabled = serializers.BooleanField(label="禁用/启用秘钥")
    create_at = serializers.DateTimeField(label="创建时间")
    class Meta:
        model = ResponseNoneMeta
        fields = ["access_key", 'secret_key', 'enabled', 'create_at']


class IamLoginResponsesSerializer(serializers.ModelSerializer):
    content = IamLoginResponsesInfo(label="成功信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class IamLogoutResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：Logout Successed!")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class IamInfoByAccountInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="所查询的用户账号", help_text="示例：ding.shuqian@21vianet.com")
    application_industry = serializers.CharField(label="应用行业", help_text="示例：金融/金融")
    contact_address = serializers.CharField(label="联系地址", help_text="示例：1234/123456")
    create_at = serializers.CharField(label="该账号创建时间", help_text="示例：2019-09-11 10:49:03")
    default_project_id = serializers.CharField(label="默认项目id", help_text="示例：7ae5a60714014778baddea703b85cd93")
    default_project_name = serializers.CharField(label="默认项目名称",help_text="示例：admin")
    deleted_at = serializers.CharField(label="该账号删除时间", help_text="该字段无意义,不涉及业务")
    description = serializers.CharField(label="该账号描述信息")
    enterprise_id = serializers.CharField(label="该用户所属公司id", help_text="示例：5cffb92400a6ba91f7c5bda6")
    enterprise_name = serializers.CharField(label="该用户所属公司名称", help_text="示例：世纪互联")
    id = serializers.CharField(label="该用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    identity_card = serializers.CharField(label="该用户身份证号码", help_text="示例：130182199910010000")
    identity_name = serializers.CharField(label="该用户名", help_text="示例：丁管")
    name = serializers.CharField(label="该用户姓名", help_text="该字段无意义,不涉及业务")
    phone_number = serializers.CharField(label="该用户电话号码", help_text="示例：15103837705")
    project_list = serializers.CharField(label="该用户所属项目列表")
    role_id = serializers.CharField(label="角色id", help_text="示例：5d2d916a0ff04349ffcae8b0")
    role_limit = serializers.CharField(label="角色权限值", help_text="示例：20")
    role_name = serializers.CharField(label="角色名称", help_text="示例：管理员")
    status = serializers.CharField(label="用户状态", help_text="示例：active（激活）")
    update_at = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")
    user_agreement = serializers.CharField(label="该用户是否同意用户协议", help_text="示例：true")
    user_agreement_at = serializers.CharField(label="该用户同意用户协议的时间", help_text="示例：2019-09-19 16:11:29")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "default_project_id","default_project_name","id","application_industry","contact_address",
                  "role_limit","status","user_agreement_at","user_agreement","update_at","role_name","role_id"
            ,"project_list","phone_number","name","identity_name","identity_card","id","enterprise_name","enterprise_id",
                  "description","deleted_at","create_at"]


class IamAccInfoByAccResponsesSerializer(serializers.ModelSerializer):
    content = IamInfoByAccountInfo(label="查询成功后的该用户信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class FipInstanceListAvaliableInfoResponsesSerializer(serializers.ModelSerializer):
    instance_id = serializers.CharField(label="实例id", help_text="示例：cafc0e26-7a34-40af-9cb4-ba1d987c6b90")
    instance_name = serializers.CharField(label="浮动IP可用配额", help_text="示例：centos7-base-1011")
    port = serializers.CharField(label="浮动IP可用配额", help_text="示例：['192.168.45.21']")

    class Meta:
        model = ResponseNoneMeta
        fields = ["instance_id", "instance_name", "port"]


class FipInstanceListAvaliableResponsesSerializer(serializers.ModelSerializer):
    content = FipInstanceListAvaliableInfoResponsesSerializer(label="查询可绑定实例列表")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AccessKeyListResponsesSerializer(serializers.ModelSerializer):
    class Meta:
        models = AccessKey
        fields = ['access_key']


class SecretKeyListResponsesSerializer(serializers.ModelSerializer):
    class Meta:
        models = AccessKey
        fields = ['secret_key']
