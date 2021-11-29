# -*- coding: utf-8 -*-
"""
Web Console Api Client
"""

import threading
from common import utils
import time

def delete_test1(request):
    openstack_client = utils.get_openstack_client(request)
    pool_delete = openstack_client.load_balancer.delete_pool(pool_id="bf0b150c-4221-4112-9589-8b3b943db142")

def update_test1(request):
    openstack_client = utils.get_openstack_client(request)
    pool_update = openstack_client.load_balancer.update_pool(pool_id="ab82c371-5d4d-4f5b-a721-fad9f89ba10e",
                                                                 name="ding_test_update")

def test(self, request):
    threads = []
    threads.append(threading.Thread(target=update_test1(request)))
    threads.append(threading.Thread(target=delete_test1(request)))
    for t in threads:
        print("%s: %s" % (t, time.ctime(time.time())))
        t.start()
    print("删除成功")

test()