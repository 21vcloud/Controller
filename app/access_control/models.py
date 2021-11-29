# -*- coding: utf-8 -*-

from django.db import models

from account.repository.auth_models import BmUserInfo
from common.lark_common import random_object_id


class Role(models.Model):
    name = models.CharField(max_length=128, unique=True, help_text="角色名称")
    notices = models.TextField(help_text="备注")
    owner = models.CharField(max_length=128, blank=True, null=True, help_text="专有角色关联")
    role_level = models.CharField(max_length=32, default="all_set", help_text="角色级别")
    create_at = models.DateTimeField(auto_now_add=True, help_text="创建时间")

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'bm_access_control_role'


class Permission(models.Model):
    TYPE_LIST = (
        ('element', 'element'),
    )
    ACTION_LIST = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE')
    )
    type = models.CharField(max_length=64, choices=TYPE_LIST, help_text="权限的类型")
    type_id = models.CharField(max_length=64, help_text="控制元素的坐标")
    action = models.CharField(max_length=64, choices=ACTION_LIST, help_text="授权动作")
    disabled = models.BooleanField(blank=True, null=True, help_text="显示控制")
    permission_level = models.CharField(max_length=64, help_text="权限级别")

    def __unicode__(self):
        return self.permission_level

    class Meta:
        db_table = 'bm_access_control_permission'
        unique_together = ('type', 'type_id', 'action', 'disabled')


class RoleUser(models.Model):
    user = models.ForeignKey(BmUserInfo, help_text="关联用户", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, help_text="关联角色", on_delete=models.CASCADE)

    def __unicode__(self):
        return self.role.name

    class Meta:
        db_table = 'bm_access_control_role_user'
        unique_together = ('user', 'role',)


class RolePermission(models.Model):
    permission = models.ForeignKey(Permission, help_text="关联权限", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, help_text="关联角色", on_delete=models.CASCADE)

    def __unicode__(self):
        return self.role.name

    class Meta:
        db_table = 'bm_access_control_role_permission'
        unique_together = ('permission', 'role',)


class Element(models.Model):
    TYPE_LIST = (
        ('sidebar', 'sidebar'),
        ('url', 'url'),
        ('navbar', 'navbar'),
        ('button', 'button'),
        ('role_type', 'role_type'),
    )
    uuid = models.CharField(max_length=64, default=random_object_id.gen_random_object_id, help_text="uuid")
    url_path = models.CharField(max_length=256, blank=True, null=True, help_text="url地址")
    owner_path = models.CharField(max_length=128, help_text="元素归属模块")
    type = models.CharField(max_length=32, choices=TYPE_LIST, help_text="元素类型")
    html_laber = models.CharField(max_length=128, blank=True, null=True, help_text="元素名称")
    notices = models.TextField(help_text="备注")
    element_id = models.CharField(max_length=64, blank=True, null=True, help_text="元素在页面上的id")
    sort_id = models.CharField(max_length=64, blank=True, null=True, help_text="排序id")
    info = models.TextField(blank=True, null=True, help_text="备用信息")
    last_mark = models.BooleanField(default=True, help_text="目录树最底层标签")

    def __unicode__(self):
        return self.owner_path

    class Meta:
        db_table = 'bm_access_control_element'
        unique_together = ('owner_path', 'element_id', 'type', )
