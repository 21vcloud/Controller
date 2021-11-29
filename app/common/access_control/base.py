# -*- coding: utf-8 -*-

import json
import time
import logging

from BareMetalControllerBackend.settings import ACCESS_CONTROL_OUT

from common.lark_common.model.common_model import ResponseObj
from access_control.models import (RoleUser, RolePermission, Element, Role, Permission)
from account.repository.auth_models import (BmUserInfo, BmProject)
from baremetal_service.repository.service_model import BmRequestLog


__all__ = [
    'check_element_permission',
    'check_child',
    'AccessSet',
]

logger = logging.getLogger(__name__)


def url_format(url):
    url_info = url.split('/')
    if url_info[-2].isdigit():
        return '/'.join(url_info[0: -2]) + '/'
    else:
        return url


def insert_request_log(request, data):
    try:
        params = {
            "account_id": request.session["account_id"],
            "account_name": request.session["username"],
            "project_id": request.session["project_id"],
            "project_name": request.session["project_name"],
            "action": request.method,
            "uri": request.path,
            "request_info": data
        }
        BmRequestLog.objects.create(**params)
    except Exception as ex:
        print(ex)
        logger.error("can not get func name: %s" % str(ex))


def check_element_permission(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        response_obj = ResponseObj()
        project_id = None
        if len(args) > 0:
            request = args[-1]
        else:
            default_msg = "No Request."
            response_obj.is_ok = False
            return response_obj.json_exception_serial(user_info=default_msg, admin_info=default_msg, no=400)
        if request.method == "GET":
            # insert_request_log(request, dict(request.query_params))
            project_name = request.query_params.get('project_name', None)
        else:
            # insert_request_log(request, dict(request.data))
            project_name = request.data.get('project_name', None)
        # if project_name:
        #     try:
        #         project_id = BmProject.objects.get(project_name=project_name)
        #     except BmProject.DoesNotExist:
        #         admin_msg = "Not find project_name Path."
        #         user_msg = "No Permission"
        #         response_obj.is_ok = False
        #         return response_obj.json_exception_serial(user_info=user_msg, admin_info=admin_msg, no=403)
        try:
            account_id = request.session["account_id"]
            print(request.session["account_id"])
            print(request.session["username"])
            if request.session["username"] in ACCESS_CONTROL_OUT:
                return func(*args, **kwargs)
        except Exception as ex:
            admin_msg = "No session. %s" % str(ex)
            user_msg = "No Login."
            response_obj.is_ok = False
            return response_obj.json_exception_serial(user_info=user_msg, admin_info=admin_msg, no=403)
        user_role_list = RoleUser.objects.filter(user__id=account_id).values_list('role__id', flat=True)
        try:
            url_obj = Element.objects.get(url_path=url_format(request.path))
        except Element.DoesNotExist:
            admin_msg = "Not find Url Path."
            user_msg = "No Permission"
            response_obj.is_ok = False
            return response_obj.json_exception_serial(user_info=user_msg, admin_info=admin_msg, no=403)
        permission_params = {
            "permission__action": request.method,
            "permission__type": 'element',
            "permission__type_id": url_obj.uuid,
            "role__id__in": user_role_list
        }
        # if project_id:
        #     permission_params['role__owner'] = project_id.id
        permission_list = RolePermission.objects.filter(**permission_params)
        print(time.time() - start_time)
        if permission_list:
            return func(*args, **kwargs)
        else:
            default_msg = "No Permission."
            return response_obj.json_exception_serial(user_info=default_msg, admin_info=default_msg, no=403)

    return wrapper


def check_child(func):
    def wrapper(*args, **kwargs):
        response_obj = ResponseObj()
        if len(args) > 0:
            request = args[-1]
        else:
            default_msg = "No Request."
            response_obj.is_ok = False
            return response_obj.json_exception_serial(user_info=default_msg, admin_info=default_msg, no=400)
        account_id = request.session["account_id"]
        pk = kwargs.get('pk', '-1')
        try:
            child_list = BmUserInfo.objects.get(
                id=account_id
            ).userextend_set.all().values_list('id', flat=True)
        except BmUserInfo.DoesNotExist:
            user_msg = "No Permission."
            admin_msg = "No User."
            response_obj.is_ok = False
            return response_obj.json_exception_serial(user_info=user_msg, admin_info=admin_msg, no=403)
        if pk in child_list:
            return func(*args, **kwargs)
        else:
            user_msg = "No Permission."
            admin_msg = "Can not set this child."
            response_obj.is_ok = False
            return response_obj.json_exception_serial(user_info=user_msg, admin_info=admin_msg, no=403)

    return wrapper


class AccessSet:
    @staticmethod
    def create_role(owner, role_info):
        if not owner:
            create_role_params = {
                "name": role_info.get('name'),
                "notices": role_info.get('notices'),
            }
        else:
            create_role_params = {
                "name": ("%s_" % owner) + role_info.get('name'),
                "notices": ("%s_" % owner) + role_info.get('notices'),
                "owner": owner
            }
        role_obj, _ = Role.objects.get_or_create(**create_role_params)
        return role_obj

    def switch_role(self, cfg_type, role_info_list, owner=None):
        if cfg_type == 'base_bar_role':
            self.create_bar_role(role_info_list, owner)
        elif cfg_type == 'base_button_role':
            self.create_button_role(role_info_list, owner)
        elif cfg_type == 'base_url_role':
            self.create_url_role(role_info_list, owner)
        else:
            return False
        return True

    def switch_data(self, cfg_type, role_info_list):
        if cfg_type == 'base_bar_data':
            self.create_bar_data(role_info_list)
        elif cfg_type == 'base_button_data':
            self.create_button_data(role_info_list)
        elif cfg_type == 'base_url_data':
            self.create_url_data(role_info_list)
        else:
            return False
        return True

    def create_url_role(self, role_info_list, owner):
        for role_info in role_info_list:
            try:
                role_obj = self.create_role(owner, role_info)

                for element_info in role_info['element_info']:
                    try:
                        element_params = {
                            "owner_path": 'None',
                            "type": 'url',
                            "url_path": element_info.get('url'),
                        }
                        element_obj = Element.objects.get(**element_params)
                    except Element.DoesNotExist:
                        print("can not find element_obj, %s" % element_info)
                        continue
                    permission_params = {
                        "type": "element",
                        "type_id": element_obj.uuid,
                        "action": element_info.get('action')
                    }
                    permission_list = Permission.objects.filter(**permission_params)
                    for permission_obj in permission_list:
                        create_role_permission = {
                            "permission": permission_obj,
                            "role": role_obj
                        }
                        try:
                            if RolePermission.objects.filter(**create_role_permission):
                                print("Already Exists")
                                continue
                            RolePermission.objects.create(**create_role_permission)
                            print("%s add roles successful." % permission_obj)
                        except Exception as ex:
                            print(ex)
            except Exception as ex:
                print(ex)

    def create_button_role(self, role_info_list, owner):
        for role_info in role_info_list:
            try:
                role_obj = self.create_role(owner, role_info)

                for element_info in role_info['element_info']:
                    try:
                        element_params = {
                            "owner_path": element_info.get('owner_path'),
                            "type": 'button',
                            "element_id": element_info.get('element_id'),
                        }
                        element_obj = Element.objects.get(**element_params)
                    except Element.DoesNotExist:
                        print("can not find element_obj, %s" % element_info)
                        continue
                    permission_params = {
                        "type": "element",
                        "type_id": element_obj.uuid,
                    }
                    permission_list = Permission.objects.filter(**permission_params)
                    for permission_obj in permission_list:
                        create_role_permission = {
                            "permission": permission_obj,
                            "role": role_obj
                        }
                        try:
                            if RolePermission.objects.filter(**create_role_permission):
                                print("Already Exists")
                                continue
                            RolePermission.objects.create(**create_role_permission)
                            print("%s add roles successful." % permission_obj)
                        except Exception as ex:
                            print(ex)
            except Exception as ex:
                print(ex)

    def create_bar_role(self, role_info_list, owner):
        for role_info in role_info_list:
            try:
                role_obj = self.create_role(owner, role_info)

                for element_info in role_info['element_info']:
                    try:
                        element_params = {
                            "owner_path": element_info.get('owner_path'),
                            "type": element_info.get('type'),
                            "element_id": element_info.get('element_id'),
                        }
                        element_obj = Element.objects.get(**element_params)
                    except Element.DoesNotExist:
                        print("can not find element_obj, %s" % element_info)
                        continue
                    permission_params = {
                        "type": "element",
                        "type_id": element_obj.uuid,
                    }
                    permission_list = Permission.objects.filter(**permission_params)
                    for permission_obj in permission_list:
                        create_role_permission = {
                            "permission": permission_obj,
                            "role": role_obj
                        }
                        try:
                            if RolePermission.objects.filter(**create_role_permission):
                                print("Already Exists")
                                continue
                            RolePermission.objects.create(**create_role_permission)
                            print("%s add roles successful." % permission_obj)
                        except Exception as ex:
                            print(ex)
            except Exception as ex:
                print(ex)

    @staticmethod
    def delete_role(role_info_list, owner):
        try:
            role_name_list = []
            for role_info in role_info_list:
                role_name_list.append(("%s_" % owner) + role_info.get('name'))
            Role.objects.filter(name__in=role_name_list).delete()
            print("delete role name list: ", role_name_list)
        except Exception as ex:
            print(ex)
        return True

    @staticmethod
    def create_bar_data(element_list, permission_level="all_set"):
        for element_dict in element_list:
            try:
                create_element_params = {
                    "owner_path": element_dict.get('owner_path'),
                    "type": element_dict.get('type'),
                    "element_id": element_dict.get('element_id'),
                    "html_laber": element_dict.get('html_laber'),
                    "sort_id": element_dict.get('sort_id'),
                    "notices": "%s %s link" % (element_dict.get('type'), element_dict.get('html_laber'))
                }
                element_obj, _ = Element.objects.get_or_create(**create_element_params)
                try:
                    if 'info' in element_dict:
                        element_obj.info = element_dict["info"]
                    if 'url_path' in element_dict:
                        element_obj.url_path = element_dict["url_path"]
                    element_obj.save()
                except Exception as ex:
                    print("update info error: ", ex)
                print(element_obj)
                print("create/get element obj successful: %s" % element_dict.get('element_id'))

                create_permission_params = {
                    "type": "element",
                    "type_id": element_obj.uuid,
                    "action": "GET",
                    "disabled": False,
                    "permission_level": permission_level
                }
                if Permission.objects.filter(**create_permission_params):
                    print("Already Exists")
                    continue
                Permission.objects.create(**create_permission_params)
                print("create permission successful: %s" % element_dict.get('html_laber'))
            except Exception as ex:
                print(ex)

    @staticmethod
    def create_button_data(element_list, element_type="button", permission_level="all_set"):
        for element_dict in element_list:
            try:
                create_element_params = {
                    "owner_path": element_dict.get('owner_path'),
                    "type": element_type,
                    "element_id": element_dict.get('element_id'),
                    "html_laber": element_dict.get('html_laber'),
                    "notices": "button %s link" % element_dict.get('html_laber')
                }
                element_obj, _ = Element.objects.get_or_create(**create_element_params)
                try:
                    if 'info' in element_dict:
                        element_obj.info = element_dict["info"]
                    if 'sort_id' in element_dict:
                        element_obj.sort_id = element_dict["sort_id"]
                    element_obj.save()
                except Exception as ex:
                    print("update info error: ", ex)
                print("create/get element obj successful: %s" % element_dict.get('element_id'))

                create_permission_params = {
                    "type": "element",
                    "type_id": element_obj.uuid,
                    "action": "GET",
                    "disabled": False,
                    "permission_level": permission_level
                }
                if Permission.objects.filter(**create_permission_params):
                    print("Already Exists")
                    continue
                Permission.objects.create(**create_permission_params)
                print("create permission successful: %s" % element_dict.get('html_laber'))
            except Exception as ex:
                print(ex)

    @staticmethod
    def create_url_data(element_list):
        for element_dict in element_list:
            try:
                create_element_params = {
                    "url_path": element_dict.get('url'),
                    "owner_path": 'None',
                    "type": 'url',
                    "notices": "url: %s 元素" % element_dict.get('url')
                }
                element_obj, _ = Element.objects.get_or_create(**create_element_params)
                print("create/get element obj successful: %s" % element_dict.get('url'))

                create_permission_params = {
                    "type": "element",
                    "type_id": element_obj.uuid,
                    "action": element_dict.get('action'),
                    "disabled": False,
                    "permission_level": element_dict.get('level', 'all_set')
                }
                if Permission.objects.filter(**create_permission_params):
                    print("Already Exists")
                    continue
                Permission.objects.create(**create_permission_params)
                print("create permission successful: %s, %s" % (element_dict.get('url'), element_dict.get('action')))
            except Exception as ex:
                print(ex)

    @staticmethod
    def add_role_user(user, role_name_list, owner=None):
        role_list = []
        if owner:
            for role_name in role_name_list:
                req = Role.objects.filter(name=(('%s_' % owner) + role_name), owner=owner)
                role_list.extend(req)
        else:
            for role_name in role_name_list:
                req = Role.objects.filter(name=role_name, owner=owner)
                role_list.extend(req)

        for x in role_list:
            try:
                params = {
                    "user": user,
                    "role": x
                }
                if RoleUser.objects.filter(**params):
                    print("Already Exists")
                    continue
                RoleUser.objects.create(
                    user=user,
                    role=x
                )
                print("%s add %s successful." % (user.account, x.name))
            except Exception as ex:
                print(ex)
        return True

    @staticmethod
    def delete_role_user(user, role_name_list, owner):
        role_list = []
        for role_name in role_name_list:
            req = Role.objects.filter(name=(('%s_' % owner) + role_name), owner=owner)
            role_list.extend(req)

        RoleUser.objects.filter(user=user, role__in=role_list).delete()
        return True

    @staticmethod
    def get_main_sidebar(email, project_id):
        print(email, project_id)
        role_id_list = RoleUser.objects.filter(
            user__account=email,
            role__owner=project_id
        ).values_list(
            'role__id',
            flat=True
        )
        if not role_id_list:
            role_id_list = RoleUser.objects.filter(
                user__account=email
            ).values_list(
                'role__id',
                flat=True
            )

        element_uuid_list = RolePermission.objects.filter(
            role__id__in=role_id_list,
            permission__type="element"
        ).values_list(
            'permission__type_id',
            flat=True
        )

        res_list = Element.objects.filter(
            uuid__in=element_uuid_list
        ).filter(
            owner_path="main",
            type="sidebar"
        ).order_by('sort_id')

        permission_list = res_list.values_list('element_id', flat=True)
        return permission_list

    @staticmethod
    def check_user_permission(account_id, permission_type, permission_model, **kwargs):
        permission_model_uuid_list = permission_model.objects.filter(
            **kwargs
        ).values_list(
            'uuid',
            flat=True
        )
        role_id = RolePermission.objects.filter(
            permission__type_id__in=permission_model_uuid_list,
            permission__type=permission_type
        ).values_list(
            'role__id',
            flat=True
        )
        role_user = RoleUser.objects.filter(
            role__id__in=role_id,
            user__id=account_id
        )
        if role_user:
            return True
        else:
            return False

    def get_role_type(self, account_id):
        if self.check_user_permission(account_id, 'element', Element, element_id='manager', type='role_type'):
            return 'manager'
        elif self.check_user_permission(account_id, 'element', Element, element_id='authorizener', type='role_type'):
            return 'authorizener'
        else:
            return 'customer'
