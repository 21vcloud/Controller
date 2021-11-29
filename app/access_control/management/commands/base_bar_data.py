# -*- coding: utf-8 -*-

import os

from django.core.management.base import BaseCommand

from common.access_control.base import AccessSet


class Command(BaseCommand):
    def handle(self, *args, **options):
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, 'cfg/base_bar_data')
        info_list = open(file_path, 'rb').read()
        AccessSet.create_bar_data(eval(info_list))
