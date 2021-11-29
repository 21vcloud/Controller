# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import datetime

from django.db import models

from common.lark_common import random_object_id


class BmContactToUs(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_bmctu_order_code)
    customer_name = models.CharField(max_length=64, blank=True, null=True,help_text="顾客姓名  示例：丁淑倩" )
    phone = models.CharField(max_length=32, blank=True, null=True,help_text="顾客电话号码  示例：15103837705")
    email = models.CharField(max_length=32, blank=True, null=True,help_text="顾客电子邮箱  示例：ding.adin@21vianet.com")
    company = models.CharField(max_length=255, blank=True, null=True,help_text="顾客公司  示例：世纪互联")
    department = models.CharField(max_length=255, blank=True, null=True,help_text="顾客部门  示例：产品研发")
    job_position = models.CharField(max_length=255, blank=True, null=True,help_text="顾客岗位  示例：开发工程师")
    issue_content = models.TextField(blank=True, null=True,help_text="问题描述  示例：产品咨询")
    issue_type = models.CharField(max_length=255, blank=True, null=True,help_text="非必填项")
    created_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,help_text="表单提交时间")
    update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,help_text="非必填项")
    connect_referrer = models.CharField(max_length=255, blank=True, null=True, help_text="推荐人  示例：丁淑倩")

    class Meta:
        managed = False
        db_table = 'bm_contact_to_us'


class BmContactToUsForDiscount(models.Model):
    id = models.CharField(primary_key=True, max_length=64, default=random_object_id.gen_bmctu_order_code)
    customer_name = models.CharField(max_length=64, blank=True, null=True,help_text="顾客姓名  示例：丁淑倩" )
    phone = models.CharField(max_length=32, blank=True, null=True,help_text="顾客电话号码  示例：15103837705")
    email = models.CharField(max_length=32, blank=True, null=True,help_text="顾客电子邮箱  示例：ding.adin@21vianet.com")
    company = models.CharField(max_length=255, blank=True, null=True,help_text="顾客公司  示例：世纪互联")
    industry = models.CharField(max_length=255, blank=True, null=True,help_text="顾客公司行业  示例：IT")
    job_position = models.CharField(max_length=255, blank=True, null=True, help_text="顾客岗位  示例：开发工程师")
    # product_type = models.CharField(max_length=255, blank=True, null=True, help_text="产品类型：云主机、裸金属云服务器、托管私有云")
    product_content = models.TextField(blank=True, null=True, help_text="产品类型及配置数量信息  示例：'云主机':'存储型-windows-'")
    created_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,help_text="表单提交时间")
    update_at = models.DateTimeField(blank=True, null=True, default=datetime.datetime.now,help_text="非必填项")

    class Meta:
        managed = False
        db_table = 'bm_contact_to_us_for_discount'
