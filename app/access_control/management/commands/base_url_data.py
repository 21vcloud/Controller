# -*- coding: utf-8 -*-

import os

from django.core.management.base import BaseCommand

from common.access_control.base import AccessSet


class Command(BaseCommand):
    def handle(self, *args, **options):
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, 'cfg/base_url_data')
        url_list = open(file_path, 'rb').read()
        AccessSet.create_url_data(eval(url_list))
