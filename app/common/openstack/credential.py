# -*- coding:utf-8 -*-

from __future__ import division

from openstack import connection
from common.openstack.context import RequestContext
# from openstack import profile
#
#
# class OpenStackCredential(object):
#     def __init__(self, creds_data):
#         self.creds_data = creds_data
#
#     def creds(self):
#         prof = profile.Profile()
#         prof.set_name('compute', 'nova')
#         prof.set_region(prof.ALL, self.creds_data['region'])
#         prof.set_api_version('volume', 'v2')
#         prof.set_version('identity', 'v3')
#         prof.set_interface(prof.ALL, 'public')
#
#         # return creds_data
#         return connection.Connection(
#             profile=prof,
#             **self.creds_data
#         )
# creds_data = dict()
# creds_data['username'] = "admin"
# creds_data['password'] = "ql21Fm7vPMAzbYJvKkf0MsDQj"
# creds_data['auth_url'] = "http://10.200.204.248:5000/v3"
# creds_data['project_id'] = "e5ae1ccc504d4940a236b2922a7c2ca7"
# creds_data['project_name'] = "admin"
# creds_data['project_domain_name'] = "Default"
# creds_data['user_domain_name'] = "Default"
# creds_data['region'] = "Default"
#
# open_stack_credentail = OpenStackCredential(creds_data)
# conn = open_stack_credentail.creds()
# conn.network.list()
token='gAAAAABc3m9maYRfPJrgoRHRh4oElN2lDNUzs3RL_wxVO63QpsjcUMnpEmqtzGJKWweisMrvDqD3VThY6XWwVVYa3GAmFyj2NqHblHpus1hbvk4HSt5_C3U2o6IngvUQQutzPTuSdSgavp6rJOboK3kW__k25TNrzPqZ_EATnkPk4zwESoFxoIw'
context = RequestContext(auth_url="http://10.200.204.248:5000/v3", project_name='admin',token=token,
                         project_domain_name='default')
keystone_session = context.keystone_session

from keystoneclient.v3 import client as keystone_client

# cli = keystone_client.Client(session=session)
# ss = cli.services.list()
#
# auth_info = {"username": "admin", "password": "ql21Fm7vPMAzbYJvKkf0MsDQj", "project_id":'e5ae1ccc504d4940a236b2922a7c2ca7'}
# project_info = {"name": "melon_project", "description": "string"}
# user_info = {"name": "wei286069122@163.com", "password": "abcd-1234", "email": "wei.panlong@21vianet.com",
#              "default_project": "melon_project"}
# role_info = {"name": "member"}

from openstack import connection
admin_conn = connection.Connection(
    session=keystone_session,
    region_name='regionOne',
    # compute_api_version='2',
    identity_interface='public')

# project_info = admin_conn.create_project(name="test_cz3", description="string", domain_id="default")
# print(project_info)
filters = {'project': 'e5ae1ccc504d4940a236b2922a7c2ca7'}
# users = admin_conn.list_role_assignments(filters=filters)
user = admin_conn.get_user('czddd')
print(user)

#
# from openstack import connection
# admin_conn = connection.Connection(
#     region_name='regionOne',
#     auth=dict(
#         auth_url='http://10.200.204.248:5000/v3/',
#         username=auth_info.get("username"),
#         password=auth_info.get("password"),
#         project_id=auth_info.get("project_id"),
#         user_domain_id='default'),
#     compute_api_version='2',
#     identity_interface='public'
# )

# creds_data = dict()
# creds_data['username'] = "admin"
# creds_data['password'] = "ql21Fm7vPMAzbYJvKkf0MsDQj"
# creds_data['project_id'] = "e5ae1ccc504d4940a236b2922a7c2ca7"
# creds_data['project_name'] = "admin"
# creds_data['auth_url'] = "http://10.200.204.248:5000/v3"
# creds_data['project_domain_id'] = "default"
# creds_data['user_domain_name'] = "Default"
# creds_data['region'] = "regionOne"
# creds_data['identity_interface'] = "public"
# admin_conn=connection.Connection(**creds_data)
#
# token = admin_conn.authorize()
#
# ss= admin_conn.session

#print("over")
# 项目创建=
# project_info = admin_conn.create_project(name="melon_project", description="string", domain_id="default")

# 用户创建
# user_info = admin_conn.create_user(name="wei286069122@163.com", password="abcd-1234", email="wei.panlong@21vianet.com", default_project="admin", domain_id="default")

# 绑定用户、项目 role
# grant_role_to_project = admin_conn.grant_role(name_or_id="member", user="wei286069122@163.com", project="melon_project", domain="default")
# grant_role_to_project = admin_conn.grant_role(name_or_id="member", user="admin", project="melon_project", domain="default")
# revoke_role_to_project = admin_conn.revoke_role(name_or_id="b371934a91a74f17a625409ff21ed9d9", user="d65ed799a0534ae89e8c63250ebca4e9", project="d0fe2aea3c074f6eb871ba40bcaf1531", domain="default")

# 计算配额
# compute_quota = admin_conn.get_compute_quotas(name_or_id="melon_project")
# new_compute_quota = {}
# for key in compute_quota:
#     new_compute_quota[key] = -1
# new_compute_quota.pop("id")
# admin_conn.set_compute_quotas(name_or_id="melon_project", **new_compute_quota)
#
# # 网络配额
# network_quota = admin_conn.get_network_quotas(name_or_id="melon_project")
# new_network_quota = {}
# for key in network_quota:
#     new_network_quota[key] = -1
# admin_conn.set_network_quotas(name_or_id="melon_project", **new_network_quota)
#
# # 磁盘配额
# volume_quota = admin_conn.get_volume_quotas(name_or_id="melon_project")
# new_volume_quota = {}
# for key in dict(volume_quota):
#     new_volume_quota[key] = -1
# admin_conn.set_volume_quotas(name_or_id="melon_project", **new_volume_quota)
# a = 1