# -*- coding: utf-8 -*-

from django.contrib import admin

from access_control.models import (Role, Permission, RoleUser, RolePermission, Element)


class RoleForm(admin.ModelAdmin):
    list_display = ('id', 'name', 'notices', 'create_at')
    search_fields = ('id', 'name', 'create_at')


class PermissionForm(admin.ModelAdmin):
    list_display = ('id', 'type', 'type_id', 'element_obj_id', 'action', 'permission_level')
    search_fields = ('id', 'type', 'type_id', 'action', 'permission_level')

    @staticmethod
    def element_obj_id(obj):
        if obj.type == 'element':
            try:
                element_obj = Element.objects.get(uuid=obj.type_id)
                return '%s' % element_obj.uuid
            except Element.DoesNotExist:
                return '%s' % 'Not Find Obj'
        else:
            return '%s' % obj.type


class RoleUserForm(admin.ModelAdmin):
    list_display = ('id', 'user_account', 'role_name')
    search_fields = ('id',)

    @staticmethod
    def user_account(obj):
        return '%s' % obj.user.account

    @staticmethod
    def role_name(obj):
        return '%s' % obj.role.name


class RolePermissionForm(admin.ModelAdmin):
    list_display = ('id', 'permission_type', 'role_name')
    search_fields = ('id',)

    @staticmethod
    def permission_type(obj):
        if obj.permission.type == 'element':
            element_obj = Element.objects.get(uuid=obj.permission.type_id)
            return '%s, %s, %s' % (element_obj.owner_path, element_obj.type, element_obj.element_id)
        else:
            return '%s' % obj.permission.type

    @staticmethod
    def role_name(obj):
        return '%s' % obj.role.name


class ElementForm(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'url_path', 'owner_path', 'type', 'html_laber', 'notices', 'element_id', 'sort_id')
    search_fields = ('id', 'uuid', 'url_path', 'owner_path', 'type', 'html_laber', 'notices', 'element_id', 'sort_id')


admin.site.register(Role, RoleForm)
admin.site.register(Permission, PermissionForm)
admin.site.register(RoleUser, RoleUserForm)
admin.site.register(RolePermission, RolePermissionForm)
admin.site.register(Element, ElementForm)
