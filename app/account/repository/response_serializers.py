# -*- coding:utf-8 -*-

from django.db import models
from rest_framework import serializers


class ResponseNoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


class LoginUserInfo(serializers.ModelSerializer):
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

class EmailCodeInfo(serializers.ModelSerializer):
    code = serializers.CharField(label="邮箱所发送的验证码", help_text="示例：123456")
    email = serializers.CharField(label="所发送验证码的邮箱", help_text="示例：ding.admin@21vianet.com")

    class Meta:
        model = ResponseNoneMeta
        fields = ["code", "email"]

class PhoneCodeInfo(serializers.ModelSerializer):
    code = serializers.CharField(label="手机号所发送的验证码", help_text="示例：123456")
    email = serializers.CharField(label="所发送验证码的手机号", help_text="示例：15103837705")

    class Meta:
        model = ResponseNoneMeta
        fields = ["code", "email"]


class UpdatePasswdInfo(serializers.ModelSerializer):
    code = serializers.CharField(label="邮箱所发送的验证码", help_text="示例：123456")
    email = serializers.CharField(label="所发送验证码的邮箱", help_text="示例：ding.shuqian@21vianet.com")

    class Meta:
        model = ResponseNoneMeta
        fields = ["code", "email"]

class EmailUpdateInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="更新成功后的邮箱账号", help_text="示例：ding.shuqian@21vianet.com")
    id = serializers.CharField(label="邮箱所对应的用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    status = serializers.CharField(label="邮箱状态", help_text="示例：active")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "id","status"]


class PhoneUpdateInfo(serializers.ModelSerializer):
    phone_number = serializers.CharField(label="更新成功后的手机号", help_text="示例：15103837707")
    id = serializers.CharField(label="手机号所对应的用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    status = serializers.CharField(label="手机号状态", help_text="示例：active")

    class Meta:
        model = ResponseNoneMeta
        fields = ["phone_number", "id","status"]


class ProjectSwitchInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="所切换项目的用户账号", help_text="示例：ding.shuqian@21vianet.com")
    default_project_id = serializers.CharField(label="该用户的默认项目id", help_text="示例：7ae5a60714014778baddea703b85cd93")
    default_project_name = serializers.CharField(label="该用户的默认项目", help_text="示例：admin")
    id = serializers.CharField(label="该用户的id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    identity_name = serializers.CharField(label="该用户名", help_text="示例：丁管")
    query_token = serializers.CharField(label="websocket 查询token")
    role_limit = serializers.CharField(label="该用户权限值", help_text="示例：20")
    status = serializers.CharField(label="项目状态", help_text="示例：active")

    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "default_project_id","default_project_name","id","identity_name","query_token","role_limit","status"]


class InfoByAccountInfo(serializers.ModelSerializer):
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


class InfoByAccountInfo(serializers.ModelSerializer):
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


class UserInfoListInfo(serializers.ModelSerializer):
            account = serializers.CharField(label="用户账号", help_text="示例：ding.shuqian@21vianet.com")
            application_industry = serializers.CharField(label="应用行业", help_text="示例：金融/金融")
            contact_address = serializers.CharField(label="联系地址", help_text="示例：1234/123456")
            create_at = serializers.CharField(label="该账号创建时间", help_text="示例：2019-09-11 10:49:03")
            default_project_id = serializers.CharField(label="默认项目id", help_text="示例：7ae5a60714014778baddea703b85cd93")
            default_project_name = serializers.CharField(label="默认项目名称", help_text="示例：admin")
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
                fields = ["account", "default_project_id", "default_project_name", "id", "application_industry",
                          "contact_address",
                          "role_limit", "status", "user_agreement_at", "user_agreement", "update_at", "role_name",
                          "role_id"
                    , "project_list", "phone_number", "name", "identity_name", "identity_card", "id", "enterprise_name",
                          "enterprise_id",
                          "description", "deleted_at", "create_at"]





class InfoByKeywordsInfo(serializers.ModelSerializer):
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
            ,"phone_number","name","identity_name","identity_card","id","enterprise_name","enterprise_id",
                  "description","deleted_at","create_at"]


class AllAccountInfo(serializers.ModelSerializer):
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
            ,"phone_number","name","identity_name","identity_card","id","enterprise_name","enterprise_id",
                  "description","deleted_at","create_at"]


class AllAuthorizerInfo(serializers.ModelSerializer):
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
            ,"phone_number","name","identity_name","identity_card","id","enterprise_name","enterprise_id",
                  "description","deleted_at","create_at"]

class DefaultProjectInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="该账号创建时间", help_text="示例：2019-09-11 10:49:03")
    project_name = serializers.CharField(label="默认项目名称",help_text="示例：admin")
    deleted_at = serializers.CharField(label="该账号删除时间", help_text="该字段无意义,不涉及业务")
    description = serializers.CharField(label="该账号描述信息")
    id = serializers.CharField(label="该用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    status = serializers.CharField(label="用户状态", help_text="示例：active（激活）")
    update_at = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "project_name","deleted_at","description","id","update_at","status"]


class EnterpriseInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="该账号创建时间", help_text="示例：2019-09-11 10:49:03")
    project_name = serializers.CharField(label="默认项目名称",help_text="示例：admin")
    deleted_at = serializers.CharField(label="该账号删除时间", help_text="该字段无意义,不涉及业务")
    description = serializers.CharField(label="该账号描述信息")
    id = serializers.CharField(label="该用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    status = serializers.CharField(label="用户状态", help_text="示例：active（激活）")
    abbreviation = serializers.CharField(label="用户信息更新时间", help_text="示例：霍傻子")
    customer_service_name = serializers.CharField(label="客服姓名", help_text="示例：霍小伟")
    enterprise_name = serializers.CharField(label="公司名称", help_text="示例：霍小伟")
    enterprise_number = serializers.CharField(label="公司编号", help_text="示例：ershazi")
    industry1 = serializers.CharField(label="应用行业1", help_text="示例：电子商务")
    industry2 = serializers.CharField(label="应用行业2", help_text="示例：互联网-电子商务")
    location = serializers.CharField(label="所属区域", help_text="示例：华北")
    payee = serializers.CharField(label="收费姓名", help_text="示例：霍小伟")
    sales = serializers.CharField(label="销售姓名", help_text="示例：霍小伟")
    system_id = serializers.CharField(label="该字段暂时未被使用")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-10-09 15:04:30")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "project_name","deleted_at","description","id","update_at","status","abbreviation"
            ,"customer_service_name","enterprise_name","enterprise_number","industry1","industry2","location","payee"
                  ,"sales","system_id"]


class EnterpriseCreatedInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="该账号创建时间", help_text="示例：2019-09-11 10:49:03")
    project_name = serializers.CharField(label="默认项目名称",help_text="示例：admin")
    description = serializers.CharField(label="该账号描述信息")
    status = serializers.CharField(label="用户状态", help_text="示例：active（激活）")
    abbreviation = serializers.CharField(label="用户信息更新时间", help_text="示例：霍傻子")
    customer_service_name = serializers.CharField(label="客服姓名", help_text="示例：霍小伟")
    enterprise_name = serializers.CharField(label="公司名称", help_text="示例：霍小伟")
    enterprise_number = serializers.CharField(label="公司编号", help_text="示例：ershazi")
    industry1 = serializers.CharField(label="应用行业1", help_text="示例：电子商务")
    industry2 = serializers.CharField(label="应用行业2", help_text="示例：互联网-电子商务")
    location = serializers.CharField(label="所属区域", help_text="示例：华北")
    payee = serializers.CharField(label="收费姓名", help_text="示例：霍小伟")
    sales = serializers.CharField(label="销售姓名", help_text="示例：霍小伟")
    system_id = serializers.CharField(label="该字段暂时未被使用")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-10-09 15:04:30")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "project_name","description","update_at","status","abbreviation"
            ,"customer_service_name","enterprise_name","enterprise_number","industry1","industry2","location","payee"
                  ,"sales","system_id"]


class AllEnterpriseInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="该账号创建时间", help_text="示例：2019-09-11 10:49:03")
    id = serializers.CharField(label="公司id",help_text="示例：5d8b2d2158ae407851c79a9f")
    description = serializers.CharField(label="该账号描述信息")
    status = serializers.CharField(label="用户状态", help_text="示例：active（激活）")
    abbreviation = serializers.CharField(label="用户信息更新时间", help_text="示例：霍傻子")
    customer_service_name = serializers.CharField(label="客服姓名", help_text="示例：霍小伟")
    enterprise_name = serializers.CharField(label="公司名称", help_text="示例：霍小伟")
    enterprise_number = serializers.CharField(label="公司编号", help_text="示例：ershazi")
    industry1 = serializers.CharField(label="应用行业1", help_text="示例：电子商务")
    industry2 = serializers.CharField(label="应用行业2", help_text="示例：互联网-电子商务")
    location = serializers.CharField(label="所属区域", help_text="示例：华北")
    payee = serializers.CharField(label="收费姓名", help_text="示例：霍小伟")
    sales = serializers.CharField(label="销售姓名", help_text="示例：霍小伟")
    system_id = serializers.CharField(label="该字段暂时未被使用")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-10-09 15:04:30")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "id","description","update_at","status","abbreviation"
            ,"customer_service_name","enterprise_name","enterprise_number","industry1","industry2","location","payee"
                  ,"sales","system_id"]

class RoleInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="角色创建时间", help_text="示例：2019-09-11 10:49:03")
    role_name = serializers.CharField(label="角色名称",help_text="示例：admin")
    role_limit = serializers.CharField(label="角色权限值", help_text="10")
    description = serializers.CharField(label="角色描述信息")
    id = serializers.CharField(label="角色id", help_text="示例：5cf24cc36e2fa72ab32d1efa")
    status = serializers.CharField(label="角色状态", help_text="示例：active（激活）")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-10-09 15:04:30")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "role_name","role_limit","description","id","update_at","status"]


class RoleCreatedInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="角色创建时间", help_text="示例：2019-09-11 10:49:03")
    role_name = serializers.CharField(label="角色名称",help_text="示例：admin")
    role_limit = serializers.CharField(label="角色权限值", help_text="10")
    description = serializers.CharField(label="角色描述信息")
    id = serializers.CharField(label="角色id", help_text="示例：5cf24cc36e2fa72ab32d1efa")
    status = serializers.CharField(label="角色状态", help_text="示例：active（激活）")
    update_at = serializers.CharField(label="更新时间", help_text="示例：2019-10-09 15:04:30")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "role_name","role_limit","description","id","update_at","status"]


class ContractTenTerminate(serializers.ModelSerializer):
    account_id__account = serializers.CharField(label="合同授权人账号", help_text="示例：zhouxiao@qq.com")
    account_id__identity_name = serializers.CharField(label="合同授权人名称",help_text="示例：周潇")
    contract_number = serializers.CharField(label="合同编号", help_text="示例：wer234234324")
    expire_date = serializers.CharField(label="合同到期日期",help_text="示例：2019-10-19")
    start_date = serializers.CharField(label="合同开始日期", help_text="示例：2019-09-03")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id__account", "account_id__identity_name","contract_number",
                  "expire_date","start_date"]


class UpdateUserInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="所更新的用户账号", help_text="示例：ding.shuqian@21vianet.com")
    default_project = DefaultProjectInfo(label="默认的项目信息")
    enterprise = EnterpriseInfo(label="所属公司信息")
    role = RoleInfo(label="所属角色信息")
    id = serializers.CharField(label="该用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    identity_card = serializers.CharField(label="该用户身份证号码", help_text="示例：130182199910010000")
    identity_name = serializers.CharField(label="该用户名", help_text="示例：丁管")
    phone_number = serializers.CharField(label="该用户电话号码", help_text="示例：15103837705")
    update_at = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "default_project","enterprise","role","id","identity_card",
                  "identity_name","phone_number","update_at"]

#TODO   字段信息不准确
class ProjetctCreatedInfo(serializers.ModelSerializer):
    description = serializers.CharField(label="项目描述信息", help_text="示例：ding.shuqian@21vianet.com")

    # domain_id = serializers.CharField(label="该字段暂时未被使用")
    # enabled = serializers.CharField(label="所属公司信息")
    id = serializers.CharField(label="项目id", help_text="示例：f749f0c38cb7463d9bf2452de29764dd")
    # is_domain = serializers.CharField(label="该用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    # is_enabled = serializers.CharField(label="该用户身份证号码", help_text="示例：130182199910010000")
    # location = serializers.CharField(label="该用户名", help_text="示例：丁管")

    name = serializers.CharField(label="项目名称", help_text="示例：ding_111")

    # parent_id = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")
    # properties = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")
    # tags = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")


    class Meta:
        model = ResponseNoneMeta
        # fields = ["description", "domain_id","enabled","is_domain","id","is_enabled",
        #           "location","name","parent_id","properties","tags"]
        fields = ["description", "id", "name"]


class ProjetctDeletedInfo(serializers.ModelSerializer):
    description = serializers.CharField(label="项目描述信息", help_text="示例：ding.shuqian@21vianet.com")

    # domain_id = serializers.CharField(label="该字段暂时未被使用")
    # enabled = serializers.CharField(label="所属公司信息")
    id = serializers.CharField(label="项目id", help_text="示例：f749f0c38cb7463d9bf2452de29764dd")
    # is_domain = serializers.CharField(label="该用户id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    # is_enabled = serializers.CharField(label="该用户身份证号码", help_text="示例：130182199910010000")
    # location = serializers.CharField(label="该用户名", help_text="示例：丁管")

    name = serializers.CharField(label="项目名称", help_text="示例：ding_111")

    # parent_id = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")
    # properties = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")
    # tags = serializers.CharField(label="用户信息更新时间", help_text="示例：2019-10-08 16:49:58")


    class Meta:
        model = ResponseNoneMeta
        # fields = ["description", "domain_id","enabled","is_domain","id","is_enabled",
        #           "location","name","parent_id","properties","tags"]
        fields = ["description", "id", "name"]


class ProjetctKeywordsInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="项目创建时间", help_text="示例：2019-09-29 11:41:33")
    deleted_at = serializers.CharField(label="项目删除时间", help_text="示例：2019-10-29 11:41:33")
    description = serializers.CharField(label="项目描述信息")
    id = serializers.CharField(label="项目id", help_text="示例：f749f0c38cb7463d9bf2452de29764dd")
    project_name = serializers.CharField(label="项目名称", help_text="示例：huo_")
    status = serializers.CharField(label="项目状态", help_text="示例：forbidden/active")
    update_at = serializers.CharField(label="项目更新时间", help_text="示例：2019-09-29 11:41:33")
    user_info_list = UserInfoListInfo(label="项目成员列表")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted_at","description","id","project_name","status",
                  "update_at","user_info_list"]


class MemberInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="成员账号", help_text="示例：ding.shuqian@21vianet.com")
    id = serializers.CharField(label="成员id", help_text="示例：3f4cb35aeec544d3af33150f38b55286")
    role__role_name = serializers.CharField(label="成员角色名称")


    class Meta:
        model = ResponseNoneMeta
        fields = ["role__role_name", "id","account"]


class ProjetctInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="项目创建时间", help_text="示例：2019-09-29 11:41:33")
    deleted_at = serializers.CharField(label="项目删除时间", help_text="示例：2019-10-29 11:41:33")
    description = serializers.CharField(label="项目描述信息")
    id = serializers.CharField(label="项目id", help_text="示例：f749f0c38cb7463d9bf2452de29764dd")
    project_name = serializers.CharField(label="项目名称", help_text="示例：huo_")
    status = serializers.CharField(label="项目状态", help_text="示例：forbidden/active")
    update_at = serializers.CharField(label="项目更新时间", help_text="示例：2019-09-29 11:41:33")
    enterprise = serializers.CharField(label="所属公司",help_text="示例：世纪互联")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted_at","description","id","project_name","status",
                  "update_at","enterprise"]


class ProjetctListByAccountInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="项目创建时间", help_text="示例：2019-09-29 11:41:33")
    deleted_at = serializers.CharField(label="项目删除时间", help_text="示例：2019-10-29 11:41:33")
    description = serializers.CharField(label="项目描述信息")
    id = serializers.CharField(label="项目id", help_text="示例：f749f0c38cb7463d9bf2452de29764dd")
    project_name = serializers.CharField(label="项目名称", help_text="示例：huo_")
    status = serializers.CharField(label="项目状态", help_text="示例：forbidden/active")
    update_at = serializers.CharField(label="项目更新时间", help_text="示例：2019-09-29 11:41:33")
    enterprise = serializers.CharField(label="所属公司",help_text="示例：世纪互联")
    is_authorizer = serializers.CharField(label="受否存在授权人", help_text="示例：True/False")
    member_info = MemberInfo(label="项目成员信息")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted_at","description","id","project_name","status",
                  "update_at","enterprise","member_info","is_authorizer"]



class ProjetctNoAuthorizerInfo(serializers.ModelSerializer):
    create_at = serializers.CharField(label="项目创建时间", help_text="示例：2019-09-29 11:41:33")
    deleted_at = serializers.CharField(label="项目删除时间", help_text="示例：2019-10-29 11:41:33")
    description = serializers.CharField(label="项目描述信息")
    id = serializers.CharField(label="项目id", help_text="示例：f749f0c38cb7463d9bf2452de29764dd")
    project_name = serializers.CharField(label="项目名称", help_text="示例：huo_")
    status = serializers.CharField(label="项目状态", help_text="示例：forbidden/active")
    update_at = serializers.CharField(label="项目更新时间", help_text="示例：2019-09-29 11:41:33")


    class Meta:
        model = ResponseNoneMeta
        fields = ["create_at", "deleted_at","description","id","project_name","status",
                  "update_at"]


class ComputeQuotaInfo(serializers.ModelSerializer):
    cores = serializers.CharField(label="CPU", help_text="示例：600")
    id = serializers.CharField(label="配额id", help_text="示例：592a7b130b0c4b48ba3a1f9da70fc86e")
    instances = serializers.CharField(label="实例数",help_text="100")
    key_pairs = serializers.CharField(label="密钥对个数", help_text="示例：100")
    metadata_items = serializers.CharField(label="元数据数目", help_text="示例：128")
    ram = serializers.CharField(label="内存", help_text="示例：5120000")
    server_group_members = serializers.CharField(label="主机组成员数目", help_text="示例：10")
    server_groups = serializers.CharField(label="主机组个数", help_text="示例：200")


    class Meta:
        model = ResponseNoneMeta
        fields = ["cores", "id","instances","key_pairs","ram","server_group_members",
                  "server_groups","metadata_items"]


class NetworkQuotaInfo(serializers.ModelSerializer):
    floatingip = serializers.CharField(label="弹性公网IP个数", help_text="示例：50")
    network = serializers.CharField(label="网络数目", help_text="示例：100")
    port = serializers.CharField(label="端口数目",help_text="100")
    rbac_policy = serializers.CharField(label="展示数据（）", help_text="示例：100")
    router = serializers.CharField(label="路由数目", help_text="示例：128")
    security_group = serializers.CharField(label="安全组数目", help_text="示例：100")
    security_group_rule = serializers.CharField(label="安全组规则数目", help_text="示例：10")
    subnet = serializers.CharField(label="子网数目", help_text="示例：100")
    subnetpool = serializers.CharField(label="展示数据（）", help_text="示例：-1")
    trunk = serializers.CharField(label="展示数据（）", help_text="示例：-1")


    class Meta:
        model = ResponseNoneMeta
        fields = ["floatingip", "network","port","rbac_policy","router","security_group",
                  "security_group_rule","subnet","subnetpool","trunk"]


class VolumeQuotaInfo(serializers.ModelSerializer):
    backup_gigabytes = serializers.CharField(label="展示数据（）", help_text="示例：50")
    backups = serializers.CharField(label="展示数据（）", help_text="示例：100")
    gigabytes = serializers.CharField(label="展示数据（）",help_text="100")
    gigabytes_ceph = serializers.CharField(label="展示数据（）", help_text="示例：100")
    gigabytes_inspure_iscsi = serializers.CharField(label="展示数据（）", help_text="示例：128")
    groups = serializers.CharField(label="展示数据（）", help_text="示例：100")
    id = serializers.CharField(label="展示数据（）", help_text="示例：10")
    per_volume_gigabytes = serializers.CharField(label="展示数据（）", help_text="示例：100")
    snapshots = serializers.CharField(label="展示数据（）", help_text="示例：-1")
    snapshots_ceph = serializers.CharField(label="展示数据（）", help_text="示例：-1")
    snapshots_inspure_iscsi = serializers.CharField(label="展示数据（）", help_text="示例：-1")
    volumes = serializers.CharField(label="展示数据（）", help_text="示例：-1")
    volumes_ceph = serializers.CharField(label="展示数据（）", help_text="示例：-1")
    volumes_inspure_iscsi = serializers.CharField(label="展示数据（）", help_text="示例：-1")


    class Meta:
        model = ResponseNoneMeta
        fields = ["backup_gigabytes", "backups","gigabytes","gigabytes_ceph","gigabytes_inspure_iscsi",
                  "groups","id","volumes","volumes_ceph","volumes_inspure_iscsi",
                  "per_volume_gigabytes","snapshots","snapshots_ceph","snapshots_inspure_iscsi"]


class ProjetctQuotaInfo(serializers.ModelSerializer):
    compute_quotas = ComputeQuotaInfo(label="项目计算配额信息")
    network_quotas = NetworkQuotaInfo(label="项目网络配额信息")
    volume_quotas = VolumeQuotaInfo(label="项目存储配额信息")


    class Meta:
        model = ResponseNoneMeta
        fields = ["compute_quotas", "network_quotas","volume_quotas"]


class ProjetctBoundMemberListByProjectInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="成员账号",help_text="huo.auth@21vianet.com")
    id = serializers.CharField(label="成员id",help_text="c7fe61996a9e470f9ff99de09a0e7004")
    identity_name = serializers.CharField(label="成员姓名",help_text="霍唯")
    role = serializers.CharField(label="成员角色id",help_text="5cee78cf85c323077c18f36b")
    role__role_name = serializers.CharField(label="成员角色名称",help_text="授权人")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "id","identity_name","role","role__role_name"]


class ProjetctNoBoundMemberListByProjectInfo(serializers.ModelSerializer):
    account = serializers.CharField(label="成员账号",help_text="huo.auth@21vianet.com")
    id = serializers.CharField(label="成员id",help_text="c7fe61996a9e470f9ff99de09a0e7004")
    identity_name = serializers.CharField(label="成员姓名",help_text="霍唯")
    role = serializers.CharField(label="成员角色id",help_text="5cee78cf85c323077c18f36b")
    role__role_name = serializers.CharField(label="成员角色名称",help_text="授权人")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account", "id","identity_name","role","role__role_name"]


class ProjetctMemberListByProjectInfo(serializers.ModelSerializer):
    bound_user_list =ProjetctBoundMemberListByProjectInfo(label="项目所绑定的成员信息")
    no_bound_user_list = ProjetctNoBoundMemberListByProjectInfo(label="项目未绑定的成员信息")


    class Meta:
        model = ResponseNoneMeta
        fields = ["bound_user_list", "no_bound_user_list"]

class ContractCreatedInfo(serializers.ModelSerializer):
    account_id = serializers.CharField(label="合同授权人id", help_text="示例：2eae2b20143d4f5db1e74ba825b46cae")
    authorizer = serializers.CharField(label="合同授权人",help_text="马云")
    contract_number = serializers.CharField(label="合同编号",help_text="ding123")
    contract_type = serializers.CharField(label="合同类型",help_text="标准合同")
    contract_value = serializers.CharField(label="合同月金额", help_text="示例：11")
    create_at = serializers.CharField(label="合同创建时间", help_text="示例：2019-10-09 16:18:49")
    customer_id = serializers.CharField(label="合同客户id", help_text="示例：5d8b2da25d151a4bbb583b24")
    customer_name = serializers.CharField(label="合同客户名称", help_text="示例：lkj2")
    description = serializers.CharField(label="描述性信息", help_text="示例：null")
    expire_date = serializers.CharField(label="合同到期时间", help_text="示例：2019-10-25")
    id = serializers.CharField(label="合同id", help_text="示例：5d9d97f105d9e6841c624f0a")
    payment_date = serializers.CharField(label="合同账期", help_text="示例：1")
    start_date = serializers.CharField(label="合同开始日期", help_text="示例：2019-10-10")
    status = serializers.CharField(label="合同状态", help_text="示例：active")
    update_at = serializers.CharField(label="合同信息更新时间", help_text="示例：2019-10-08 16:49:58")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "authorizer","contract_number","contract_type","contract_value","create_at",
                  "customer_id","customer_name","description","expire_date","id","payment_date","start_date",
                  "status","update_at"]


class AllContractInfo(serializers.ModelSerializer):
    account_id = serializers.CharField(label="合同授权人id", help_text="示例：2eae2b20143d4f5db1e74ba825b46cae")
    authorizer = serializers.CharField(label="合同授权人",help_text="马云")
    contract_number = serializers.CharField(label="合同编号",help_text="ding123")
    contract_type = serializers.CharField(label="合同类型",help_text="标准合同")
    contract_value = serializers.CharField(label="合同月金额", help_text="示例：11")
    create_at = serializers.CharField(label="合同创建时间", help_text="示例：2019-10-09 16:18:49")
    customer_id = serializers.CharField(label="合同客户id", help_text="示例：5d8b2da25d151a4bbb583b24")
    customer_name = serializers.CharField(label="合同客户名称", help_text="示例：lkj2")
    description = serializers.CharField(label="描述性信息", help_text="示例：null")
    expire_date = serializers.CharField(label="合同到期时间", help_text="示例：2019-10-25")
    id = serializers.CharField(label="合同id", help_text="示例：5d9d97f105d9e6841c624f0a")
    payment_date = serializers.CharField(label="合同账期", help_text="示例：1")
    start_date = serializers.CharField(label="合同开始日期", help_text="示例：2019-10-10")
    status = serializers.CharField(label="合同状态", help_text="示例：active")
    update_at = serializers.CharField(label="合同信息更新时间", help_text="示例：2019-10-08 16:49:58")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id", "authorizer","contract_number","contract_type","contract_value","create_at",
                  "customer_id","customer_name","description","expire_date","id","payment_date","start_date",
                  "status","update_at"]

class ContractResourceInfo(serializers.ModelSerializer):
    ECBM = serializers.CharField(label="ECBM")
    flaoting_ip = serializers.CharField(label="弹性公网IP资源信息")
    volume = serializers.CharField(label="云硬盘资源信息")
    volume_backup = serializers.CharField(label="云硬盘备份资源信息")


    class Meta:
        model = ResponseNoneMeta
        fields = ["ECBM", "flaoting_ip","volume","volume_backup"]


class ContractTerminateInfo(serializers.ModelSerializer):
    account_id__account = serializers.CharField(label="合同授权人账号",help_text="zhouxiao@qq.com")
    account_id__identity_name = serializers.CharField(label="合同授权人姓名",help_text="周潇")
    contract_number = serializers.CharField(label="合同编号",help_text="123")
    expire_date = serializers.CharField(label="合同到期时间",help_text="2019-09-25")
    start_date = serializers.CharField(label="合同开始时间",help_text="2019-09-17")


    class Meta:
        model = ResponseNoneMeta
        fields = ["account_id__account", "account_id__identity_name","contract_number","expire_date",
                  "expire_date","start_date"]


class LoginResponsesInfo(serializers.ModelSerializer):
    token = serializers.CharField(label="用户验证码", help_text="示例：a7f8e458e808d05e9148a780d412d99b|1568096396.2957418")
    user_info = LoginUserInfo(label="用户信息")

    class Meta:
        model = ResponseNoneMeta
        fields = ["token", "user_info"]


class LoginResponsesSerializer(serializers.ModelSerializer):
    content = LoginResponsesInfo(label="成功信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class LogoutResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：Logout Successed!")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class GetWebsocketContent(serializers.ModelSerializer):
    query_token = serializers.CharField(label="Websocket Token",
        help_text="示例：eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1aWQi"
                  "OiJkNzUyMjJjMTM2ODU0YjgxYjNjYThmMWEyNjYwZWEwMyIsImV4cCI6M"
                  "TU2OTc0ODU5OX0.Lk1YZRhq8s3m3_JQJXIgOq3Hzmu2y5sXxL9uWD5iqR8")

    class Meta:
        model = ResponseNoneMeta
        fields = ["query_token"]


get_websocket_content = {"query_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1aWQi"
                  "OiJkNzUyMjJjMTM2ODU0YjgxYjNjYThmMWEyNjYwZWEwMyIsImV4cCI6M"
                  "TU2OTc0ODU5OX0.Lk1YZRhq8s3m3_JQJXIgOq3Hzmu2y5sXxL9uWD5iqR8"}


class GetWebsocketResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例 ：{get_websocket_content}".format(
        get_websocket_content=get_websocket_content))
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class TokenVerifyResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例 ：{help_text}".format(
        help_text="null"))
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Erro info")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、400、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class EmailCodeGetResponsesSerializer(serializers.ModelSerializer):
    content = EmailCodeInfo(label="邮箱发送验证码信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]

class PhoneCodeGetResponsesSerializer(serializers.ModelSerializer):
    content = PhoneCodeInfo(label="手机发送验证码信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]

class EmailCodeVerifyResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="Verified success!")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]

class PhoneCodeVerifyResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="Verified success!")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class EmailUpdateResponsesSerializer(serializers.ModelSerializer):
    content = EmailUpdateInfo(label="邮箱更新成功后信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class PhoneUpdateResponsesSerializer(serializers.ModelSerializer):
    content = PhoneUpdateInfo(label="手机号更新成功后信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectSwitchResponsesSerializer(serializers.ModelSerializer):
    content = ProjectSwitchInfo(label="项目切换成功后信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AccountInfoByAccountResponsesSerializer(serializers.ModelSerializer):
    content = InfoByAccountInfo(label="查询成功后的该用户信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AccountInfoByKeywordsResponsesSerializer(serializers.ModelSerializer):
    content = InfoByKeywordsInfo(label="根据关键词查询成功后的该用户信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AllAccountInfoResponsesSerializer(serializers.ModelSerializer):
    content = AllAccountInfo(label="查询成功后的所有用户信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AllAuthorizerAccountInfoResponsesSerializer(serializers.ModelSerializer):
    content = AllAuthorizerInfo(label="查询成功后的所有授权人用户信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class UpdatePasswdResponsesSerializer(serializers.ModelSerializer):
    content = UpdatePasswdInfo(label="进行更新密码验证时，发送的验证码信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class UpdatePasswdByUserResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：Password reset success!")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class DeleteUserResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：[1, {account.BmUserInfo: 1}]")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]

class UserInfoUpdateResponsesSerializer(serializers.ModelSerializer):
    content = UpdateUserInfo(label="用户信息更新成功后返回的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ConfirmUpdatePasswordResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：Password reset success!")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContractTenDaysTerminateResponsesSerializer(serializers.ModelSerializer):
    content = ContractTenTerminate(label="还有十天过期的合同信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContractCreatedResponsesSerializer(serializers.ModelSerializer):
    content = ContractCreatedInfo(label="创建后的合同信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContractDeletedResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息",help_text="示例： [0,{ 'account.BmContract': 0}")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContractResourceResponsesSerializer(serializers.ModelSerializer):
    content = ContractResourceInfo(label="以合同进行查询后的资源信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContractTerminateResponsesSerializer(serializers.ModelSerializer):
    content = ContractTerminateInfo(label="所终止的合同的信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ContractUpdateResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息",help_text="示例：1")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AllInfoResponsesSerializer(serializers.ModelSerializer):
    content = AllContractInfo(label="查询出来的所有合同信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class EnterpriseDeletedResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息",help_text="示例：[1, {account.BmEnterprise: 1}]")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class EnterpriseCreatedResponsesSerializer(serializers.ModelSerializer):
    content = EnterpriseCreatedInfo(label="公司创建成功后信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]

class EnterpriseInfoResponsesSerializer(serializers.ModelSerializer):
    content = EnterpriseCreatedInfo(label="关键词查询后信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class EnterpriseUpdateResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：1")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AllEnterpriseResponsesSerializer(serializers.ModelSerializer):
    content = AllEnterpriseInfo(label="查询出的所有公司信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectCreatedResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctCreatedInfo(label="创建项目后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectDeletedResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctDeletedInfo(label="删除项目后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectKeywordsInfoResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctKeywordsInfo(label="删除项目后的返回信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectRoleManageResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息",help_text="项目成员更新成功！")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectUpdateResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息",help_text="1")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectInfoResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctInfo(label="查询出来的项目信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectMembersResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctInfo(label="查询出来的项目信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectListByAccountResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctListByAccountInfo(label="查询出来的项目信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectMemberListByProjectResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctMemberListByProjectInfo(label="查询出来的项目信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectNoAuthorizerResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctNoAuthorizerInfo(label="查询出来的项目信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectQuotaResponsesSerializer(serializers.ModelSerializer):
    content = ProjetctQuotaInfo(label="查询出来的项目配额信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class ProjectUpdateQuotaResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：{compute_quotas: null}")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class AllRoleResponsesSerializer(serializers.ModelSerializer):
    content = RoleInfo(label="角色信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class RoleCreatedResponsesSerializer(serializers.ModelSerializer):
    content = RoleCreatedInfo(label="所创建成功的角色信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class RoleDeletedResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：[1, {account.BmRole: 1}]")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]


class RoleUpdateResponsesSerializer(serializers.ModelSerializer):
    content = serializers.CharField(label="成功信息", help_text="示例：1")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]

class UserAgreementUpdateResponsesSerializer(serializers.ModelSerializer):
    content = PhoneUpdateInfo(label="用户协议更新成功后信息")
    is_ok = serializers.BooleanField(label="成功标识", help_text="示例：{成功：True、失败：False}")
    message = serializers.CharField(label="错误信息", help_text="示例：Fail to verifiy! Error: not enough values to unpack (expected 2, got 1)")
    no = serializers.IntegerField(label="返回码", help_text="示例：200、401、500、505、300")

    class Meta:
        model = ResponseNoneMeta
        fields = ["content", "is_ok", "message", "no"]
