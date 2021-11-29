# -*- coding: utf-8 -*-

import datetime
import logging

from baremetal_service.repository.service_model import BmServiceOrder, \
    ORDER_STATUS_DELIVERING, ORDER_TYPE_ALTERATION
from common.lark_common.model.common_model import ResponseObj


LOG = logging.getLogger(__name__)


def create_new_order_for_alter(origin_order_id, alter_order_info, account_id=None,
                               service_count=None, product_type=None):
    response_obj = ResponseObj()
    try:
        LOG.info("find origin order info by order id %s " % origin_order_id)
        origin_order_obj = BmServiceOrder.objects.filter(id=origin_order_id).first()
        if not origin_order_obj:
            LOG.error("fail to find origin order info by order id %s" % origin_order_id)
            raise Exception("fail to find origin order info by order id %s" % origin_order_id)

        LOG.info("combine new order param to resource alter")
        new_order_info = origin_order_obj.__dict__
        pop_list = ["_state", "id", "deleted", "update_at", "create_at"]
        for pop_param in pop_list:
            new_order_info.pop(pop_param)
        new_order_info["delivery_status"] = ORDER_STATUS_DELIVERING
        new_order_info["service_count"] = service_count or 1
        new_order_info["order_type"] = alter_order_info.get("order_type", ORDER_TYPE_ALTERATION)
        new_order_info["order_price"] = alter_order_info.get("order_price", 0)
        new_order_info["product_type"] = alter_order_info.get("product_type", product_type)
        new_order_info["product_info"] = alter_order_info.get("product_info")
        new_order_info["account_id"] = alter_order_info.get("account_id", account_id)
        new_order_info["create_at"] = datetime.datetime.now()

        LOG.info("create alter order by param %s " % new_order_info)
        order_result = BmServiceOrder.objects.create(**new_order_info)
        if not order_result:
            LOG.error("fail to create alter order %s " % order_result)
            raise Exception(order_result)
        response_obj.content = order_result
    except Exception as ex:
        response_obj.message = "Fail to create alter order %s " % str(ex)
        response_obj.is_ok = False
        response_obj.no = 500
    return response_obj
