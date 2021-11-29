# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models

from common.lark_common import random_object_id

USER_ACTIVE = "active"
USER_FORBIDDEN = "forbidden"
USER_EXCLUDE = ["deleted"]
USER_SHOW_STATUS_LIST = [USER_ACTIVE, USER_FORBIDDEN]

PROJECT_AVTIVE = "active"
PROJECT_FORBIDDEN = "forbidden"
PROJECT_DELETED = "deleted"
PROJECT_SHOW_STATUS_LIST = [PROJECT_AVTIVE, PROJECT_FORBIDDEN]

CONTRACT_AVTIVE = "active"
CONTRACT_TERMINATED = "terminated"
CONTRACT_INAVTIVE = "inactive"
CONTRACT_FORBIDDEN = "forbidden"
CONTRACT_DELETED = "deleted"

BAREMETAL_DELETED = "DELETED"
BAREMETAL_BUILD = "BUILD"

NETWORK_PUBLIC = "公网"
NETWORK_PRIVATE = "私网"

FLOATINGIP_AVTIVE = "active"

CONTRACT_FRAME = "框架合同"
CONTRACT_STANDARD = "标准合同"

ROLE_AUTHORIZER = "授权人"
OPEN_ROLE_ADMIN = "admin"

ORDER_REJECTED = "rejected"
VOLUME_BACK_TYPE = "backup"
CHAR_TYPE = "base"

help_text_create_time = "创建时间。示例：2019-09-29 09:33:17"
help_text_update_time = "更新时间。示例：2019-09-29 09:33:17"
help_text_deleted_time = "删除时间。示例：2019-09-29 09:33:17"


class BmProject(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="项目ID。示例：7ae5a60714014778baddea703b85cd93")
    project_name = models.CharField(max_length=255, blank=True, null=True, help_text="项目名称。示例：admin")
    description = models.TextField(blank=True, null=True, help_text="项目描述。示例：管理项目")
    status = models.CharField(max_length=255, blank=True, null=True, help_text="项目状态。示例：active/forbidden/deleted")
    create_at = models.DateTimeField(blank=True, null=True, help_text=help_text_create_time)
    update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,
                                     help_text=help_text_update_time)
    deleted_at = models.DateTimeField(blank=True, null=True, help_text=help_text_deleted_time)

    class Meta:
        managed = False
        db_table = 'bm_project'


class BmEnterprise(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="公司ID。示例：")
    enterprise_name = models.CharField(max_length=255, blank=True, null=True,
                                       help_text="公司名称。示例：北京世纪互联宽带数据中心有限公司")
    abbreviation = models.TextField(blank=True, null=True, help_text="公司名称缩写。示例：世纪互联")
    enterprise_number = models.CharField(max_length=255, blank=True, null=True,
                                         help_text="项目状态。示例：active/forbidden/deleted")
    description = models.TextField(blank=True, null=True, help_text="描述。示例：世纪互联公司")
    industry1 = models.CharField(max_length=255, blank=True, null=True, help_text="公司行业1。示例：IT")
    industry2 = models.CharField(max_length=255, blank=True, null=True, help_text="公司行业1。示例：云计算")
    location = models.CharField(max_length=255, blank=True, null=True, help_text="公司所属区域。示例：华北/华东")
    sales = models.CharField(max_length=255, blank=True, null=True, help_text="公司销售姓名。示例：魏一二")
    customer_service_name = models.CharField(max_length=255, blank=True, null=True, help_text="公司客服姓名。示例：魏一二")
    payee = models.CharField(max_length=255, blank=True, null=True, help_text="公司收费姓名。示例：魏一二")
    system_id = models.CharField(max_length=255, blank=True, null=True, help_text="暂时废弃字段。")
    status = models.CharField(max_length=64, blank=True, null=True, help_text="公司状态。示例：active")
    create_at = models.DateTimeField(blank=True, null=True, help_text=help_text_create_time)
    update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,
                                     help_text=help_text_update_time)

    class Meta:
        managed = False
        db_table = 'bm_enterprise'


class BmRole(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="角色ID。示例：5cffb92400a6ba91f7c5bda6")
    role_name = models.CharField(max_length=255, blank=True, null=True, help_text="角色名称。示例：管理员")
    role_limit = models.IntegerField(blank=True, null=True, help_text="角色权限值。示例：10")
    description = models.TextField(blank=True, null=True, help_text="描述。示例：最高管理权限")
    status = models.CharField(max_length=64, blank=True, null=True, help_text="角色状态。示例：active/deleted")
    create_at = models.DateTimeField(blank=True, null=True, help_text=help_text_create_time)
    update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,
                                     help_text=help_text_update_time)

    class Meta:
        managed = False
        db_table = 'bm_role'


class BmUserInfo(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户id。示例：5cffb92400a6ba91f7c5bda6")
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, help_text="父级账号")
    account = models.CharField(max_length=64, help_text="用户邮箱。示例：wei.panlong@21vianet.com")
    password = models.CharField(max_length=64, blank=True, null=True, help_text="用户密码。示例：asdqwe123")
    phone_number = models.CharField(max_length=32, blank=True, null=True, help_text="手机号码。示例：18101029680")
    name = models.CharField(max_length=255, blank=True, null=True, help_text="用户名称。示例：魏一二")
    identity_name = models.CharField(max_length=255, blank=True, null=True, help_text="用户身份证姓名。示例：魏一二")
    identity_card = models.CharField(max_length=18, blank=True, null=True, help_text="用户身份证号。示例：130182199910019999")
    contact_address = models.TextField(blank=True, null=True, help_text="用户地址。示例：北京/朝阳区/世纪互联")
    application_industry = models.CharField(max_length=255, blank=True, null=True, help_text="应用信息。示例：IT/大数据")
    role = models.ForeignKey(BmRole, models.DO_NOTHING, blank=True, help_text="用户角色ID。示例：5d2d916a0ff04349ffcae8b0")
    default_project = models.ForeignKey(BmProject, models.DO_NOTHING, blank=True,
                                        help_text="默认项目ID。示例：1ffe2257b5a5438bba749766f5259433")
    enterprise = models.ForeignKey(BmEnterprise, models.DO_NOTHING, blank=True,
                                   help_text="所属公司ID。示例：5cffb92400a6ba91f7c5bda6")
    user_agreement = models.BooleanField(blank=True, null=True, help_text="是否同意用户协议。示例：True/False")
    user_agreement_at = models.DateTimeField(blank=True, null=True, help_text="同意用户协议时间。示例：2019-09-29 09:33:17")
    status = models.CharField(max_length=11, blank=True, null=True, help_text="用户状态。示例：active/forbidden/deleted")
    description = models.TextField(blank=True, null=True, help_text="用户描述。示例：描述")
    create_at = models.DateTimeField(blank=True, null=True, help_text="创建时间。示例：2019-09-29 09:33:17")
    update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,
                                     help_text="更新时间。示例：2019-09-29 09:33:17")
    deleted_at = models.DateTimeField(blank=True, null=True, help_text="删除时间。示例：2019-09-29 09:33:17")

    class Meta:
        managed = False
        db_table = 'bm_userinfo'
        unique_together = (('id', 'account'),)


class BmUsertoken(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户登录验证码表ID。示例：5cffb92400a6ba91f7c5bda6")
    # user = models.OneToOneField(UserInfo, null=True, on_delete=True)
    account_id = models.CharField(max_length=64, unique=True, help_text="用户ID。示例：5cffb92400a6ba91f7c5bda6")
    account = models.CharField(max_length=64, unique=True, help_text="用户邮箱。示例：wei.yier@21vianet.com")
    token = models.CharField(max_length=64,
                             help_text="用户登录验证码ID。示例：fdade4f221165db56e4299f4bcd8f402|1569489431.1128526")

    class Meta:
        managed = False
        db_table = 'bm_usertoken'


class BmEmailCode(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户邮箱验证码表ID。示例：5d68cb28cdb8ed13baebad9c")
    email = models.CharField(max_length=64, help_text="用户邮箱。示例：wei.yier@21vianet.com")
    code = models.CharField(max_length=64,
                            help_text="用户邮箱验证码。示例：2d17540daa3f86dc2487e8d9a49b24ce|1567148838.0468245")

    class Meta:
        managed = False
        db_table = 'bm_email_code'


class BmPhoneCode(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户手机号验证码表ID。示例：5d68cb28cdb8ed13baebad9c")
    phone_number = models.CharField(max_length=32, blank=True, null=True, help_text="手机号码。示例：18100009999")
    code = models.CharField(max_length=64, blank=True, null=True, help_text="用户手机验证码ID。示例：123321")
    ctime = models.CharField(max_length=64, blank=True, null=True, help_text="验证码时间戳。示例：1567148838.0468245")

    class Meta:
        managed = False
        db_table = 'bm_phone_code'


class BmVerifyCode(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户手机、邮箱验证码表ID。示例：5d5faf299cf80f024abdf787")
    phone_number = models.CharField(max_length=32, blank=True, null=True, help_text="用户手机号。示例：18100009999")
    email = models.CharField(max_length=255, blank=True, null=True, help_text="用户邮箱。示例：wei.yier@21vianet.com")
    code = models.CharField(max_length=64, blank=True, null=True, help_text="用户邮箱或手机验证码。示例：973884")
    ctime = models.CharField(max_length=64, blank=True, null=True, help_text="验证码时间戳。示例：1567148838.0468245")

    class Meta:
        managed = False
        db_table = 'bm_verify_code'


class BmMappingUserProject(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户项目关联表ID。示例：5d5faf299cf80f024abdf787")
    account_id = models.CharField(max_length=64, blank=True, null=True,
                                  help_text="用户ID。示例：5d5faf299cf80f024abdf787")
    project_id = models.CharField(max_length=64, blank=True, null=True,
                                  help_text="项目ID。示例：5d5faf299cf80f024abdf787")
    status = models.CharField(max_length=64, blank=True, null=True, help_text="关联状态。示例：active/deleted")

    # create_at = models.DateTimeField(blank=True, null=True)
    # update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now)

    class Meta:
        managed = False
        db_table = 'bm_mapping_user_project'


class BmContract(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="合同ID。示例：5d5faf299cf80f024abdf787")
    customer_id = models.CharField(max_length=64, blank=True, null=True,
                                   help_text="公司ID。示例：5d5faf299cf80f024abdf787")
    customer_name = models.CharField(max_length=255, blank=True, null=True,
                                     help_text="公司名称。示例：5d5faf299cf80f024abdf787")
    contract_number = models.CharField(max_length=64,
                                       help_text="合同编码。示例：ECBM004")
    account = models.ForeignKey(BmUserInfo, models.DO_NOTHING, blank=True, null=True,
                                help_text="用户ID。示例：5d5faf299cf80f024abdf787")
    authorizer = models.CharField(max_length=255, blank=True, null=True,
                                  help_text="授权人。示例：魏一二")
    start_date = models.DateField(blank=True, null=True,
                                  help_text="合同开始时间。示例：2019-09-29")
    expire_date = models.DateField(blank=True, null=True,
                                   help_text="合同终止时间。示例：2029-09-29")
    contract_type = models.CharField(max_length=64, blank=True, null=True,
                                     help_text="合同类型。示例：标准合同/框架合同")
    payment_date = models.IntegerField(blank=True, null=True,
                                       help_text="账期天数。示例：4/100")
    contract_value = models.BigIntegerField(blank=True, null=True,
                                            help_text="月金额（元）。示例：3000")
    status = models.CharField(max_length=255, blank=True, null=True,
                              help_text="合同状态。示例：active/terminated")
    create_at = models.DateTimeField(blank=True, null=True,
                                     help_text=help_text_create_time)
    update_at = models.DateTimeField(blank=True, null=True,
                                     help_text=help_text_update_time)
    description = models.TextField(blank=True, null=True,
                                   help_text="合同描述。示例：魏一二的测试合同")

    class Meta:
        managed = False
        db_table = 'bm_contract'
        unique_together = (('id', 'contract_number'),)


class BmRequestInfo(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_random_object_id,
                          help_text="用户请求信息表ID。示例：5d5faf299cf80f024abdf787")
    request_user = models.CharField(max_length=255, blank=True, null=True, help_text="接口请求用户。示例：admin")
    request_method = models.CharField(max_length=255, blank=True, null=True, help_text="接口请求方法。示例：GET")
    request_url = models.TextField(blank=True, null=True,
                                   help_text="接口URL。示例：http://61.49.49.37:8002/account/query_all_account_info")
    request_param = models.TextField(blank=True, null=True,
                                     help_text="接口参数。示例：<QueryDict: {}>")
    reqeust_info = models.TextField(blank=True, null=True,
                                    help_text="接口信息。示例：<rest_framework.request.Request object at 0x7f2e0f3d97b8>")
    request_result = models.TextField(blank=True, null=True, help_text="接口返回结果。示例：null")

    class Meta:
        managed = False
        db_table = 'bm_request_info'
