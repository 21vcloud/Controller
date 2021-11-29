# -*- coding:utf-8 -*-

from __future__ import division


class ModelCredential:
    def __init__(self):
        self.auth_url = None
        self.project_name = None
        self.project_id = None
        self.project_domain_name = None
        self.user_domain_name = None
        self.region = None
        self.username = None
        self.password = None


class ModelInstance:
    def __init__(self):
        self.instance_name = None
        self.availability_zone = None
        self.ip_address = None
        self.image_name = None
        self.boot_type = {}
        self.uuid = None
        self.flavor = None
        self.network_name = None
        self.fixed_ip = None
        self.server_id = None
        self.status = None
        self.block_storage = []


class ModelVolume:
    def __init__(self):
        self.volume_name = None
        self.volume_description = None
        self.volume_type = None
        self.size = None
        self.availability_zone = None
        self.volume_id = None
        self.device = None


class ModelBootType:
    def __init__(self):
        self.boot_index = None
        self.uuid = None
        self.source_type = None
        self.volume_size = None
        self.destination_type = None
        self.delete_on_termination = None
        self.tag = None
