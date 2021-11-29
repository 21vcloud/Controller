# -*- coding:utf-8 -*-

from django.db import models
from drf_yasg import openapi
from rest_framework import serializers

from account.repository import auth_models


class NoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


TokenParameter = [
    openapi.Parameter(
        name='token', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="用户登录验证码",
        required=True,
        default=""
    )
]

IdListParameter = [
    openapi.Parameter(
        name='token', in_=openapi.IN_HEADER,
        type=openapi.TYPE_STRING,
        description="用户登录验证码",
        required=True,
        default=""
    ),
    openapi.Parameter(
        name='id_list', in_=openapi.IN_QUERY,
        type=openapi.TYPE_ARRAY,
        description="用户ID列表",
        required=True,
        items=[""]
    )
]


class TokenVerifySerializer(serializers.ModelSerializer):
    token = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["token"]


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmUserInfo
        exclude = ["id", "update_at", "deleted_at", "status"]


class UpateUserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmUserInfo
        exclude = ["create_at"]


class DeleteUserInfoSerializer(serializers.ModelSerializer):
    id_list = serializers.ListField(required=True, label="所删除的用户id列表",
                                    help_text="示例：['f7e034f44464430da05425a70caf9fe7']")
    status = serializers.CharField(required=True, label="将删除的用户所设置的状态", help_text="示例：deleted")
    deleted_at = serializers.DateTimeField(required=True, label="删除时间", help_text="示例：2019-10-09 14:34:23")

    class Meta:
        model = NoneMeta
        fields = ["id_list", "status", "deleted_at"]


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.CharField(label="账号邮箱", max_length=64, required=True, initial="示例：wei.panlong@21vianet.com")
    password = serializers.CharField(label="账号密码", max_length=64, required=True, help_text="示例：qwer1234")

    class Meta:
        model = NoneMeta
        fields = ["email", "password"]


class ProjectSwitchSerializer(serializers.ModelSerializer):
    region = serializers.CharField(required=True, label="所属区域", help_text="示例：华北")
    project_id = serializers.CharField(required=True, label="切换后的项目id", help_text="示例：82b7cf3042324f1a8efe5850ba84662b")
    project_name = serializers.CharField(required=True, label="切换后的项目名称", help_text="示例：ding_test123123")

    class Meta:
        model = NoneMeta
        fields = ["region", "project_id", "project_name"]


class LogoutSerializer(serializers.ModelSerializer):
    account = serializers.CharField(required=True, label="账号邮箱", help_text="示例：wei.panlong@21vianet.com")

    class Meta:
        model = NoneMeta
        fields = ["account"]


class UpdatePasswordSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True, label="账号邮箱", help_text="示例：wei.panlong@21vianet.com")

    class Meta:
        model = NoneMeta
        fields = ["email"]


class ConfirmUpdatePasswordSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True, label="邮箱账号", help_text="示例：ding.admin@21vianet.com")
    code = serializers.CharField(required=True, label="所发送的验证码",
                                 help_text="示例：a55cd12349ec6033ae99fe5184439a7b|1570517272.3922255")
    new_password = serializers.CharField(required=True, label="用户所设置的新密码", help_text="示例：qwer12345")

    class Meta:
        model = NoneMeta
        fields = ["email", "code", "new_password"]


class UpdatePasswordByUserSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, label="用户id", help_text="示例：94c0aec439cb4ce2b8e8f72d6c40de45")
    password = serializers.CharField(required=True, label="该用户旧密码", help_text="示例：qwer1234")
    new_password = serializers.CharField(required=True, label="所设置的新密码", help_text="示例：qwer12345")

    class Meta:
        model = NoneMeta
        fields = ["account_id", "password", "new_password"]


class QueryInfoByKeywordsSerializer(serializers.ModelSerializer):
    keywords = serializers.CharField(required=False, label="查询关键字", help_text="示例：ding.shuqian@21vianet.com")

    class Meta:
        model = NoneMeta
        fields = ["keywords"]


class QueryEnterpriseInfoInCondition(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmEnterprise
        exclude = ["create_at", "update_at"]


class QueryUserInfoInCondition(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmUserInfo
        exclude = ["create_at", "update_at"]


class QueryAccountByProjectSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField()

    class Meta:
        model = NoneMeta
        fields = ["project_id"]


class QueryAccountByAccountSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, label="查询用户的id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")

    class Meta:
        model = NoneMeta
        fields = ["account_id"]


class PhoneOfAccountCodeGetSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["account_id", "phone_number"]


class PhoneOfAccountCodeVerifySerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["account_id", "phone_number", "code"]


class PhoneCodeGetSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True, help_text="手机号码  示例：15103837705")

    class Meta:
        model = NoneMeta
        fields = ["phone_number"]


class PhoneCodeVerifySerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["phone_number", "code"]


class EmialCodeGetSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True, help_text="邮箱账号  示例：ding.admin@21vianet.com")

    class Meta:
        model = NoneMeta
        fields = ["email"]


class EmialCodeVerifySerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True, label="邮箱账号", help_text="示例：ding.admin@21vianet.com")
    code = serializers.CharField(required=True, label="邮箱所发送的验证码", help_text="示例：123456")

    class Meta:
        model = NoneMeta
        fields = ["email", "code"]


class PhoneUpdateSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, label="用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    phone_number = serializers.CharField(required=True, label="旧手机号码", help_text="示例：15103837705")
    new_phone_number = serializers.CharField(required=True, label="新手机号码", help_text="示例：15103837707")
    code = serializers.CharField(required=True, label="新手机号码所发送的验证码", help_text="示例：123456")

    class Meta:
        model = NoneMeta
        fields = ["account_id", "phone_number", "new_phone_number", "code"]


class EmailUpdateSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, label="用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    email = serializers.CharField(required=True, label="邮箱账号", help_text="示例：ding.admin@21vianet.com")
    new_email = serializers.CharField(required=True, label="新邮箱账号", help_text="示例：ding.shuqian@21vianet.com")
    code = serializers.CharField(required=True, label="新邮箱所发送的验证码", help_text="示例：123456")

    class Meta:
        model = NoneMeta
        fields = ["account_id", "email", "new_email", "code"]


class AccountInfoSrializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, help_text="账号 ID")

    class Meta:
        model = NoneMeta
        fields = ["account_id"]


class UidAuthorizerSrializer(serializers.Serializer):
    uuid = serializers.CharField(required=False, help_text="示例：regionOne:1d9e26b737e94d5a871e8654609622f6",
                                 label="授权uid")


# 项目 对应 serializer
class CreateProjectSerializer(serializers.ModelSerializer):
    account_list = serializers.ListField(required=False)

    class Meta:
        model = auth_models.BmProject
        exclude = ["id", "update_at", "deleted_at", "status"]


class UpdateProjectInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmProject
        exclude = ["create_at", "update_at", "deleted_at"]


class DeleteListSerializer(serializers.ModelSerializer):
    id_list = serializers.ListField(required=True, label="所删除的列表",
                                    help_text="示例：ding11")

    class Meta:
        model = NoneMeta
        fields = ["id_list"]


class QueryProjectByProjectNameSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["project_name"]


class PorjectRoleManagerSerializer(serializers.ModelSerializer):
    grant_account_list = serializers.ListField(required=False, help_text="增加的成员列表")
    revoke_account_list = serializers.ListField(required=False, help_text="减少的成员列表")
    project_id = serializers.CharField(required=True, help_text="项目 ID")

    class Meta:
        model = NoneMeta
        fields = ["project_id", "revoke_account_list", "grant_account_list"]


class PorjectIdSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(required=True, help_text="项目 ID")

    class Meta:
        model = NoneMeta
        fields = ["project_id"]


class ComputeQuotasSerializer(serializers.ModelSerializer):
    cores = serializers.IntegerField(required=True)
    instances = serializers.IntegerField(required=True)
    ram = serializers.IntegerField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["cores", "instances", "ram"]


class NetworkQuotasSerializer(serializers.ModelSerializer):
    floatingip = serializers.IntegerField(required=True)
    network = serializers.IntegerField(required=True)
    router = serializers.IntegerField(required=True)
    subnet = serializers.IntegerField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["floatingip", "network", "router", "subnet"]


class VolumeQuotasSerializer(serializers.ModelSerializer):
    gigabytes = serializers.IntegerField(required=True)
    volumes = serializers.IntegerField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["gigabytes", "volumes"]


class PorjectQuotasSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(required=True, help_text="项目 ID")
    compute_quotas_dict = ComputeQuotasSerializer()
    network_quotas_dict = NetworkQuotasSerializer()
    volume_quotas_dict = VolumeQuotasSerializer()

    class Meta:
        model = NoneMeta
        fields = ["project_id", "compute_quotas_dict", "network_quotas_dict", "volume_quotas_dict"]


class PorjectMembersListSerializer(serializers.ModelSerializer):
    project_id = serializers.CharField(required=True, help_text="项目 ID")

    class Meta:
        model = NoneMeta
        fields = ["project_id"]


class PorjectListOfAccountSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, help_text="账号 ID")

    class Meta:
        model = NoneMeta
        fields = ["account_id"]


# 公司 对应 serializer
class CreateEnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmEnterprise
        exclude = ["id", "update_at", "status"]


class UpdateEnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmEnterprise
        exclude = ["create_at", "update_at"]


class DeleteEnterpriseSerializer(serializers.ModelSerializer):
    id_list = serializers.ListField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["id_list", "status"]


class CreateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmRole
        exclude = ["id", "update_at", "status"]


class UpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmRole
        exclude = ["create_at", "update_at"]


class DeleteRoleSerializer(serializers.ModelSerializer):
    id_list = serializers.ListField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["id_list", "status"]


class CreateContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmContract
        exclude = ["id", "update_at", "authorizer"]


class UpdateContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.BmContract
        exclude = ["create_at", "update_at", "authorizer"]


class DeleteContractSerializer(serializers.ModelSerializer):
    id_list = serializers.ListField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = NoneMeta
        fields = ["id_list", "status"]


class IdentityNameSerializer(serializers.ModelSerializer):
    identity_name = serializers.CharField(required=True, help_text="用户姓名信息")

    class Meta:
        model = NoneMeta
        fields = ["identity_name"]


class ContractNumberSerializer(serializers.ModelSerializer):
    contract_number = serializers.CharField(required=True, label="合同编码", help_text="示例：ding123")

    class Meta:
        model = NoneMeta
        fields = ["contract_number"]


class ContractTerminatePriorDaysSerializer(serializers.ModelSerializer):
    prior_days = serializers.IntegerField(required=True, label="合同到期前天数", help_text="示例：3")

    class Meta:
        model = NoneMeta
        fields = ["prior_days"]


class RequestInfoRecordSerializer(serializers.ModelSerializer):
    request_user = serializers.CharField(required=True, help_text="发送请求的用户")
    request_method = serializers.CharField(required=True, help_text="请求的方式")
    request_url = serializers.CharField(required=True, help_text="发送请求的URL")
    request_param = serializers.CharField(required=True, help_text="请求所携带的参数")
    reqeust_info = serializers.CharField(required=True, help_text="请求所返回的信息")

    class Meta:
        model = NoneMeta
        fields = ["request_user", "request_method", "request_url", "request_param", "reqeust_info"]


class FrameDateInfoRecordSerializer(serializers.ModelSerializer):
    contract_start_date = serializers.DateField(required=True, help_text="合同开始日期")

    class Meta:
        model = NoneMeta
        fields = ["contract_start_date"]


class UserAgreementUpdateSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(required=True, label="用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    user_agreeement = serializers.BooleanField(required=True, label="是否同意协议： true 、false", help_text="示例：true\ false")
    # user_agreeement_at = serializers.DateTimeField(required=True, label="同意时间", help_text="示例：2020-04-26 09:50:37")

    class Meta:
        model = NoneMeta
        fields = ["account_id", "user_agreeement"]
