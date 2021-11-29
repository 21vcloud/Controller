# -*- coding: utf-8 -*-

"""
运行account 相关自动化测试活动。

运行这个测试需要注意这样几点问题：

- 工作目录为项目根目录，因为需要访问配置文件。当前是一套配置文件。
- 当前程序是入口程序，因为设置了环境变量等信息。如果不在这里运行，则可能会出问题。

"""

import unittest

import os


def init_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BareMetalControllerBackend.settings")
    import django
    django.setup()


if __name__ == "__main__":
    init_django()
    from account.tests import test_views_account
    from baremetal_service.tests import test_ceate_listener
    from baremetal_service.tests import test_add_member
    from baremetal_service.tests import test_delete_cmdb
    suite = unittest.TestSuite()

    tests = list()

    # account
    # tests.append(test_views_account.TestAccountClient("token_verify"))
    # tests.append(test_views_account.TestAccountClient("token_verify_not_exit"))
    # tests.append(test_views_account.TestAccountClient("token_verify_not_timeout"))
    # tests.append(test_views_account.TestAccountClient("register"))
    # tests.append(test_views_account.TestAccountClient("register_fail"))
    #tests.append(test_views_account.TestAccountClient("login"))
    # tests.append(test_views_account.TestAccountClient("login_fail"))
    # tests.append(test_views_account.TestAccountClient("logout"))
    # tests.append(test_views_account.TestAccountClient("update_password"))
    # tests.append(test_views_account.TestAccountClient("confirm_update_password"))
    # tests.append(test_views_account.TestVpcs("test_get_vpcs_from_db"))
    # tests.append(test_ceate_listener.testLb("test"))
    # tests.append(test_add_member.testAddMember("test"))
    tests.append(test_delete_cmdb.testCmdb("instance_create"))
    tests.append(test_delete_cmdb.testCmdb("tag_create"))
    tests.append(test_delete_cmdb.testCmdb("instance_put"))
    tests.append(test_delete_cmdb.testCmdb("instance_delete"))

    suite.addTests(tests=tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
