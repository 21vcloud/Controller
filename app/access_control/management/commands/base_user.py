# -*- coding: utf-8 -*-

import os

from django.core.management.base import BaseCommand

from common.access_control.base import AccessSet
from account.repository.auth_models import BmUserInfo, BmMappingUserProject, BmProject


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-user_mail')
        parser.add_argument('-project_name')
        parser.add_argument('-level')
        parser.add_argument('-cfg')

        # if not user.owner_roles:
        #     user.owner_roles = owner
        #     user.save()
        # else:
        #     owner_list = user.owner_roles.split(',')
        #     if owner not in owner_list:
        #         owner_list.append(owner)
        #         user.owner_roles = ','.join(owner_list)
        #         user.save()
        # print("%s add roles successful." % user.account)

    def handle(self, *args, **options):
        user_mail = options.get('user_mail', None)
        project_name = options.get('project_name', None)
        level = options.get('level', None)
        cfg = options.get('cfg', None)
        if not (user_mail and level and project_name and cfg):
            print("not find user_mail, level, project_name or cfg.")
            return None
        try:
            owner = BmProject.objects.get(project_name=project_name)
        except BmProject.DoesNotExist:
            print("not find project.")
            return None
        module_dir = os.path.dirname(__file__)
        if cfg == 'url':
            file_path = os.path.join(module_dir, 'cfg/base_url_user')
        elif cfg == 'bar':
            file_path = os.path.join(module_dir, 'cfg/base_bar_user')
        elif cfg == 'button':
            file_path = os.path.join(module_dir, 'cfg/base_button_user')
        else:
            print("cfg error, please use 'bar', 'url', 'button'.")
            return None
        mail_list = user_mail.split(',')
        for x in mail_list:
            try:
                user = BmUserInfo.objects.get(account=x)
            except BmUserInfo.DoesNotExist:
                print("%s user mail not find" % x)
                continue
            try:
                BmMappingUserProject.objects.get(project_id=owner.id, account_id=user.id)
            except BmMappingUserProject.DoesNotExist:
                print("%s user mail no permission." % x)
                continue
            add_role_name_list = eval(open(file_path, 'rb').read()).get(level)
            print(add_role_name_list)
            AccessSet.add_role_user(user, add_role_name_list, owner.id)
