import sys
import time
from argparse import ArgumentParser

import binascii
import os
import random


def gen_random_object_id():
    timestamp = '{0:x}'.format(int(time.time()))
    rest = binascii.b2a_hex(os.urandom(8)).decode('ascii')
    return timestamp + rest


def gen_bmctu_order_code():
    print(time.time())
    order_no = "BMCTU" + str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))+ str(time.time()).replace('.', '')[-7:]
    return order_no


def gen_bm_service_order_code():
    print(time.time())
    order_no = "BMS" + str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))+ str(time.time()).replace('.', '')[-7:]
    return order_no


def gen_verify_code():
    """
               生成手机验证码
    """
    code = ''
    for x in range(6):
        code += str(random.randint(0, 9))
    return code

def parse_args(args):
    parser = ArgumentParser(description='Generate a random MongoDB ObjectId')
    parser.add_argument('-l', '--longform',
                        action="store_true",
                        dest="long_form",
                        help='prints the ID surrounded by ObjectId("...")')

    return parser.parse_args(args)


def main():
    object_id = gen_random_object_id()
    args = parse_args(sys.argv[1:])

    if args.long_form:
        print('ObjectId("{}")'.format(object_id))
    else:
        print(object_id)
