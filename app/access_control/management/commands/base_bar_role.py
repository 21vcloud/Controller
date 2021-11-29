# -*- coding: utf-8 -*-

import os

from django.core.management.base import BaseCommand

from common.access_control.base import AccessSet
from account.repository.auth_models import BmProject


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-project_name')

    def handle(self, *args, **options):
        project_name = options.get('project_name', None)
        if not project_name:
            print("not find owner")
            return None
        try:
            owner = BmProject.objects.get(project_name=project_name)
        except BmProject.DoesNotExist:
            print("not find project.")
            return None
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, 'cfg/base_bar_role')
        role_list = open(file_path, 'rb').read()
        AccessSet.create_bar_role(eval(role_list), owner.id)
