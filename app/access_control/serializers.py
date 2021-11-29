# -*- coding:utf-8 -*-

from rest_framework import serializers

from access_control.models import Element, Permission


class ConsoleQueryListSerializer(serializers.Serializer):
    # user = serializers.CharField()
    project_name = serializers.CharField()
    type = serializers.CharField()
    owner_path = serializers.CharField()


class ConsoleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = '__all__'

    disabled = serializers.SerializerMethodField()

    @staticmethod
    def get_disabled(obj):
        if obj.type in ['button', 'sidebar', 'navbar']:
            try:
                res = Permission.objects.get(type='element', type_id=obj.uuid, action='GET').disabled
            except Permission.DoesNotExist:
                res = None
            return res
        else:
            return None


class ButtonQueryListSerializer(serializers.Serializer):
    project_name = serializers.CharField()
    owner_path = serializers.CharField()


class RolePostSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False)
    project_name = serializers.CharField(required=False)


class RoleDeleteSerializer(serializers.Serializer):
    project_id = serializers.CharField()


class BaseRoleUserPostSerializer(serializers.Serializer):
    LEVEL_LIST = (
        ('0', '管理员'),
        ('1', '主账号权限'),
        ('2', '无删除操作权限'),
        ('3', '无金额/删除权限'),
        ('4', '只读权限'),
    )
    email = serializers.CharField()
    project_id = serializers.CharField(required=False)
    project_name = serializers.CharField(required=False)
    level = serializers.ChoiceField(choices=LEVEL_LIST)


class BaseRoleUserDeleteSerializer(serializers.Serializer):
    email = serializers.CharField()
    project_id = serializers.CharField()


class RoleUserPostSerializer(serializers.Serializer):
    email = serializers.CharField()
    role_name = serializers.CharField()
