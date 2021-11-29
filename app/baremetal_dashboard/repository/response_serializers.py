# -*- coding:utf-8 -*-

from django.db import models
from rest_framework import serializers


class ResponseNoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'

class GetInfoByKeyResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="根据关键词查询成功后的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContactToUsInfoResponsesSerializer(serializers.ModelSerializer):
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


class ContactToUsResponsesSerializer(serializers.ModelSerializer):
    content = ContactToUsInfoResponsesSerializer(label="提交联系我们表单后返回的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContactToUsForDiscountInfoResponsesSerializer(serializers.ModelSerializer):
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


class ContactToUsForDiscountResponsesSerializer(serializers.ModelSerializer):
    content = ContactToUsForDiscountInfoResponsesSerializer(label="提交优惠表单后返回的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]
