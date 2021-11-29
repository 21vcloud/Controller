import threading
from common import utils
import asyncio
import time, datetime
from baremetal_service.repository import service_model
from django.db.models import Count
from account.repository import auth_models
from django.test import TestCase
import gevent


# 采用协程的方式和之前的旧方式进行对比
def material_ip_seasonal(start_date, end_date, param_dict=None):
    try:
        # 进行多次筛选操作
        material_ip_list = []
        begin_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        while begin_date <= end_date:
            material_ip_date = datetime.datetime.strftime(begin_date, "%Y-%m-%d")

            # 查询弹性IP某一天的计量信息
            material_day_ip_obj = material_ip_day(
                material_ip_date=material_ip_date, param_dict=param_dict)
            if not material_day_ip_obj.is_ok:
                raise Exception(material_day_ip_obj)

            # 查询结果为空跳过
            if material_day_ip_obj.content:
                material_ip_list.extend(material_day_ip_obj.content)

            begin_date += datetime.timedelta(days=1)

    except Exception as ex:
        return False
    return material_ip_list


# 查询弹性IP某一天的计量信息
async def material_ip_day(param_dict=None):
    try:
        start_time = time.time()
        material_ip_list = []
        material_day_ip_obj1 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-13")
        material_day_ip_obj2 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-14")
        material_day_ip_obj3 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-15")
        material_day_ip_obj4 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-16")
        material_day_ip_obj5 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-17")
        material_day_ip_obj6 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-18")
        material_day_ip_obj7 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-19")
        material_day_ip_obj8 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-20")
        material_day_ip_obj11 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-13")
        material_day_ip_obj22 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-14")
        material_day_ip_obj33 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-15")
        material_day_ip_obj44 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-16")
        material_day_ip_obj55 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-17")
        material_day_ip_obj66 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-18")
        material_day_ip_obj77 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-19")
        material_day_ip_obj88 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-20")
        material_day_ip_obj111 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-13")
        material_day_ip_obj222 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-14")
        material_day_ip_obj333 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-15")
        material_day_ip_obj444 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-16")
        material_day_ip_obj555 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-17")
        material_day_ip_obj666 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-18")
        material_day_ip_obj777 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-19")
        material_day_ip_obj888 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-20")

        tasks = [
            asyncio.ensure_future(material_day_ip_obj11),
            asyncio.ensure_future(material_day_ip_obj22),
            asyncio.ensure_future(material_day_ip_obj33),
            asyncio.ensure_future(material_day_ip_obj44),
            asyncio.ensure_future(material_day_ip_obj55),
            asyncio.ensure_future(material_day_ip_obj66),
            asyncio.ensure_future(material_day_ip_obj77),
            asyncio.ensure_future(material_day_ip_obj88),
            asyncio.ensure_future(material_day_ip_obj111),
            asyncio.ensure_future(material_day_ip_obj222),
            asyncio.ensure_future(material_day_ip_obj333),
            asyncio.ensure_future(material_day_ip_obj444),
            asyncio.ensure_future(material_day_ip_obj555),
            asyncio.ensure_future(material_day_ip_obj666),
            asyncio.ensure_future(material_day_ip_obj777),
            asyncio.ensure_future(material_day_ip_obj888),
            asyncio.ensure_future(material_day_ip_obj1),
            asyncio.ensure_future(material_day_ip_obj2),
            asyncio.ensure_future(material_day_ip_obj3),
            asyncio.ensure_future(material_day_ip_obj4),
            asyncio.ensure_future(material_day_ip_obj5),
            asyncio.ensure_future(material_day_ip_obj6),
            asyncio.ensure_future(material_day_ip_obj7),
            asyncio.ensure_future(material_day_ip_obj8),
        ]

        dones, pendings = await asyncio.wait(tasks)

        # for task in dones:
        #     # 查询结果为空跳过
        #     if not task.result():
        #         continue
        #
        #     material_ip_list.append(task.result())

        end_time = time.time()
        all_time = end_time - start_time
    except Exception as ex:
        return False
    return material_ip_list, all_time

def material_ip_day3(param_dict=None):
    try:
        start_time = time.time()
        material_ip_list = []
        material_day_ip_obj1 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-13")
        material_day_ip_obj2 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-14")
        material_day_ip_obj3 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-15")
        material_day_ip_obj4 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-16")
        material_day_ip_obj5 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-17")
        material_day_ip_obj6 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-18")
        material_day_ip_obj7 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-19")
        material_day_ip_obj8 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-20")
        material_day_ip_obj11 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-13")
        material_day_ip_obj22 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-14")
        material_day_ip_obj33 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-15")
        material_day_ip_obj44 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-16")
        material_day_ip_obj55 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-17")
        material_day_ip_obj66 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-18")
        material_day_ip_obj77 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-19")
        material_day_ip_obj88 = material_ip_day_by_ip_id("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-20")
        material_day_ip_obj111 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-13")
        material_day_ip_obj222 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-14")
        material_day_ip_obj333 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-15")
        material_day_ip_obj444 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-16")
        material_day_ip_obj555 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-17")
        material_day_ip_obj666 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-18")
        material_day_ip_obj777 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-19")
        material_day_ip_obj888 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-20")

        gevent.joinall([gevent.spawn(material_day_ip_obj1),
                        gevent.spawn(material_day_ip_obj2),
                        gevent.spawn(material_day_ip_obj3),
                        gevent.spawn(material_day_ip_obj4),
                        gevent.spawn(material_day_ip_obj5),
                        gevent.spawn(material_day_ip_obj6),
                        gevent.spawn(material_day_ip_obj7),
                        gevent.spawn(material_day_ip_obj8),
                        gevent.spawn(material_day_ip_obj11),
                        gevent.spawn(material_day_ip_obj22),
                        gevent.spawn(material_day_ip_obj33),
                        gevent.spawn(material_day_ip_obj44),
                        gevent.spawn(material_day_ip_obj55),
                        gevent.spawn(material_day_ip_obj66),
                        gevent.spawn(material_day_ip_obj77),
                        gevent.spawn(material_day_ip_obj88),
                        gevent.spawn(material_day_ip_obj111),
                        gevent.spawn(material_day_ip_obj222),
                        gevent.spawn(material_day_ip_obj333),
                        gevent.spawn(material_day_ip_obj444),
                        gevent.spawn(material_day_ip_obj555),
                        gevent.spawn(material_day_ip_obj666),
                        gevent.spawn(material_day_ip_obj777),
                        gevent.spawn(material_day_ip_obj888),
                        ])
        end_time = time.time()
        all_time = end_time - start_time
    except Exception as ex:
        return False
    return material_ip_list, all_time

async def material_ip_day11(param_dict=None):
    try:
        start_time = time.time()
        material_ip_list = []
        material_day_ip_obj11 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-13")
        material_day_ip_obj22 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-14")
        material_day_ip_obj33 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-15")
        material_day_ip_obj44 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-16")
        material_day_ip_obj55 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-17")
        material_day_ip_obj66 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-18")
        material_day_ip_obj77 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-19")
        material_day_ip_obj88 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-20")

        tasks = [
            asyncio.ensure_future(material_day_ip_obj11),
            asyncio.ensure_future(material_day_ip_obj22),
            asyncio.ensure_future(material_day_ip_obj33),
            asyncio.ensure_future(material_day_ip_obj44),
            asyncio.ensure_future(material_day_ip_obj55),
            asyncio.ensure_future(material_day_ip_obj66),
            asyncio.ensure_future(material_day_ip_obj77),
            asyncio.ensure_future(material_day_ip_obj88),
        ]

        dones, pendings = await asyncio.wait(tasks)

        # for task in dones:
        #     # 查询结果为空跳过
        #     if not task.result():
        #         continue
        #
        #     material_ip_list.append(task.result())

        end_time = time.time()
        all_time = end_time - start_time
    except Exception as ex:
        return False
    return material_ip_list, all_time


async def material_ip_day_by_ip_id(floating_ip_id, material_ip_date):
    """
    # 根据IP的查询该合同下某个IP信息
    :param floating_ip_id:
    :param material_ip_date:
    :return:
    """
    try:
        # 进行数据处理
        floating_ip_list_obj = service_model.BmServiceFloatingIp.objects.filter(
            floating_ip_id=floating_ip_id).order_by("create_at")
        floating_ip_list = [u.__dict__ for u in floating_ip_list_obj]
        ip_first_obj = floating_ip_list_obj.first()
        service_start_time = ip_first_obj.create_at

        bm_material_ip_null = floating_ip_list_obj.filter(update_at__isnull=True)
        ip_update_null = [u.__dict__ for u in bm_material_ip_null]

        # 到期时间的处理
        service_expired_time = "-"
        for material_ip in floating_ip_list:
            if material_ip["status"] == "deleted":
                service_expired_time = material_ip["update_at"]
                break

        # 筛选出某天的数据
        date_ip = material_ip_date
        create_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        update_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d')
        bm_material_ip_info = service_model.BmServiceFloatingIp.objects.filter(
            create_at__lte=create_at, update_at__gte=update_at, floating_ip_id=floating_ip_id).order_by("create_at")
        material_ip_list_info = [u.__dict__ for u in bm_material_ip_info]

        # 进行数据拼接得到当天所有IP的完整数据
        if bm_material_ip_null:
            if ip_update_null[0]["create_at"] <= create_at:
                material_ip_list_info.extend(ip_update_null)

        # 进行查到的数据为空数据的处理
        if not material_ip_list_info:
            message = {"user_info": "{date_ip}查询为空！".format(date_ip=date_ip)}
            return message

        # 找出当天的最大带宽
        max_band = -1
        max_band_ip_dict = dict()
        for material_ip in material_ip_list_info:
            material_ip_band = int(material_ip["qos_policy_name"].split("M")[0])
            if max_band <= material_ip_band:
                max_band = material_ip_band
                max_band_ip_dict = material_ip

        # 查找合同的一些信息
        bm_contract_material_obj = auth_models.BmContract.objects.filter(
            contract_number=max_band_ip_dict.get("contract_number")).first()
        if bm_contract_material_obj:
            bm_contract_material = bm_contract_material_obj.__dict__
            bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
            bm_contract_material_account_id = bm_contract_material.get("account_id", "")
            bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
            bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
            bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
            bm_contract_material_expire_date = bm_contract_material.get("expire_date", "")
            bm_contract_material_start_date = bm_contract_material.get("start_date", "")
        else:
            bm_contract_material_customer_id = ""
            bm_contract_material_account_id = ""
            bm_contract_material_customer_name = ""
            bm_contract_material_authorizer = ""
            bm_contract_material_contract_type = ""
            bm_contract_material_start_date = ""
            bm_contract_material_expire_date = ""

        # 查找客户的信息
        bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()

        if not bm_contract_user:
            sales = "",
            enterprise_number = "",
            location = "",
            customer_service_name = ""
        else:
            sales = bm_contract_user.sales,
            enterprise_number = bm_contract_user.enterprise_number,
            location = bm_contract_user.location,
            customer_service_name = bm_contract_user.customer_service_name

        # 查找物料IP的信息
        bm_contract_material_ip = service_model.BmContractFloatingIpMaterial.objects.filter(
            external_line_type=max_band_ip_dict.get("external_line_type")).first()
        if not bm_contract_material_ip:
            material_number = "",
            floating_ip_type_name = "",
            base_price = "",
        else:
            material_number = bm_contract_material_ip.material_number,
            floating_ip_type_name = bm_contract_material_ip.floating_ip_type_name,
            base_price = str(bm_contract_material_ip.base_price),

        # 查找物料带宽的信息
        bm_contract_material_band = service_model.BmContractBandWidthaterial.objects.filter(
            external_line_type=max_band_ip_dict.get("external_line_type")).first()
        if not bm_contract_material_band:
            material_band_material_number = "",
            band_width_type_name = "",
            material_band_base_price = "",
        else:
            material_band_material_number = bm_contract_material_band.material_number,
            band_width_type_name = bm_contract_material_band.band_width_type_name,
            material_band_base_price = str(bm_contract_material_band.base_price)

        # 查找授权人的信息
        bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(id=bm_contract_material_account_id).first()
        if not bm_contract_authorizer:
            account = ""
        else:
            account = bm_contract_authorizer.account
        # 查找下单者的一些信息
        bm_account_info = auth_models.BmUserInfo.objects.filter(id=max_band_ip_dict.get("account_id")).first()
        if not bm_account_info:
            identity_name = "",
            user_account = ""
        else:
            identity_name = bm_account_info.identity_name,
            user_account = bm_account_info.account
        # 查找订单信息
        bm_contract_order = service_model.BmServiceOrder.objects.filter(id=max_band_ip_dict.get("order_id")).first()
        if not bm_contract_order:
            region = ""
        else:
            region = bm_contract_order.region

        # 查找项目信息
        bm_contract_project = service_model.BmProject.objects.filter(id=max_band_ip_dict.get("project_id")).first()
        project_name = ""
        if bm_contract_project:
            project_name = bm_contract_project.project_name

        material_ip_dict = {
            "id": max_band_ip_dict.get("id"),
            "用户ID": max_band_ip_dict.get("account_id"),
            "用户名称": identity_name[0],
            "用户邮箱": user_account,
            "合同编号": max_band_ip_dict.get("contract_number"),
            "查询日期": date_ip,
            "带宽物料编码": material_band_material_number[0],
            "带宽类型": band_width_type_name[0],
            "带宽价格": material_band_base_price,
            "IP物料编码": material_number[0],
            "IP物料类型": floating_ip_type_name[0],
            "IP价格": base_price,
            "合同可用区": region,
            "销售姓名": sales[0],
            "公司编码": enterprise_number[0],
            "公司所属区": location[0],
            "客服姓名": customer_service_name,
            "服务到期时间": service_expired_time,
            "服务开始时间": service_start_time,
            "合同开始时间": bm_contract_material_start_date,
            "合同到期时间": bm_contract_material_expire_date,
            "客户名称": bm_contract_material_customer_name,
            "合同授权人": bm_contract_material_authorizer,
            "合同类型": bm_contract_material_contract_type,
            "合同授权人邮箱": account,
            "IP类型": max_band_ip_dict.get("external_line_type"),
            "IP类型名称": max_band_ip_dict.get("external_name"),
            "IP类型ID": max_band_ip_dict.get("external_name_id"),
            "IP": max_band_ip_dict.get("floating_ip"),
            "ip_id": max_band_ip_dict.get("floating_ip_id"),
            "订单号": max_band_ip_dict.get("order_id"),
            "项目ID": max_band_ip_dict.get("project_id"),
            "项目名称": project_name,
            "服务状态": max_band_ip_dict.get("status"),
            "最大带宽": max_band,
        }

    except Exception as ex:
        return False
    return material_ip_dict


def material_ip_day_by_ip_id2(floating_ip_id, material_ip_date):
    """
    # 根据IP的查询该合同下某个IP信息
    :param floating_ip_id:
    :param material_ip_date:
    :return:
    """
    try:
        # 进行数据处理
        floating_ip_list_obj = service_model.BmServiceFloatingIp.objects.filter(
            floating_ip_id=floating_ip_id).order_by("create_at")
        floating_ip_list = [u.__dict__ for u in floating_ip_list_obj]
        ip_first_obj = floating_ip_list_obj.first()
        service_start_time = ip_first_obj.create_at

        bm_material_ip_null = floating_ip_list_obj.filter(update_at__isnull=True)
        ip_update_null = [u.__dict__ for u in bm_material_ip_null]

        # 到期时间的处理
        service_expired_time = "-"
        for material_ip in floating_ip_list:
            if material_ip["status"] == "deleted":
                service_expired_time = material_ip["update_at"]
                break

        # 筛选出某天的数据
        date_ip = material_ip_date
        create_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        update_at = datetime.datetime.strptime(material_ip_date, '%Y-%m-%d')
        bm_material_ip_info = service_model.BmServiceFloatingIp.objects.filter(
            create_at__lte=create_at, update_at__gte=update_at, floating_ip_id=floating_ip_id).order_by("create_at")
        material_ip_list_info = [u.__dict__ for u in bm_material_ip_info]

        # 进行数据拼接得到当天所有IP的完整数据
        if bm_material_ip_null:
            if ip_update_null[0]["create_at"] <= create_at:
                material_ip_list_info.extend(ip_update_null)

        # 进行查到的数据为空数据的处理
        if not material_ip_list_info:
            message = {"user_info": "{date_ip}查询为空！".format(date_ip=date_ip)}
            return message

        # 找出当天的最大带宽
        max_band = -1
        max_band_ip_dict = dict()
        for material_ip in material_ip_list_info:
            material_ip_band = int(material_ip["qos_policy_name"].split("M")[0])
            if max_band <= material_ip_band:
                max_band = material_ip_band
                max_band_ip_dict = material_ip

        # 查找合同的一些信息
        bm_contract_material_obj = auth_models.BmContract.objects.filter(
            contract_number=max_band_ip_dict.get("contract_number")).first()
        if bm_contract_material_obj:
            bm_contract_material = bm_contract_material_obj.__dict__
            bm_contract_material_customer_id = bm_contract_material.get("customer_id", "")
            bm_contract_material_account_id = bm_contract_material.get("account_id", "")
            bm_contract_material_customer_name = bm_contract_material.get("customer_name", "")
            bm_contract_material_authorizer = bm_contract_material.get("authorizer", "")
            bm_contract_material_contract_type = bm_contract_material.get("contract_type", "")
            bm_contract_material_expire_date = bm_contract_material.get("expire_date", "")
            bm_contract_material_start_date = bm_contract_material.get("start_date", "")
        else:
            bm_contract_material_customer_id = ""
            bm_contract_material_account_id = ""
            bm_contract_material_customer_name = ""
            bm_contract_material_authorizer = ""
            bm_contract_material_contract_type = ""
            bm_contract_material_start_date = ""
            bm_contract_material_expire_date = ""

        # 查找客户的信息
        bm_contract_user = auth_models.BmEnterprise.objects.filter(id=bm_contract_material_customer_id).first()

        if not bm_contract_user:
            sales = "",
            enterprise_number = "",
            location = "",
            customer_service_name = ""
        else:
            sales = bm_contract_user.sales,
            enterprise_number = bm_contract_user.enterprise_number,
            location = bm_contract_user.location,
            customer_service_name = bm_contract_user.customer_service_name

        # 查找物料IP的信息
        bm_contract_material_ip = service_model.BmContractFloatingIpMaterial.objects.filter(
            external_line_type=max_band_ip_dict.get("external_line_type")).first()
        if not bm_contract_material_ip:
            material_number = "",
            floating_ip_type_name = "",
            base_price = "",
        else:
            material_number = bm_contract_material_ip.material_number,
            floating_ip_type_name = bm_contract_material_ip.floating_ip_type_name,
            base_price = str(bm_contract_material_ip.base_price),

        # 查找物料带宽的信息
        bm_contract_material_band = service_model.BmContractBandWidthaterial.objects.filter(
            external_line_type=max_band_ip_dict.get("external_line_type")).first()
        if not bm_contract_material_band:
            material_band_material_number = "",
            band_width_type_name = "",
            material_band_base_price = "",
        else:
            material_band_material_number = bm_contract_material_band.material_number,
            band_width_type_name = bm_contract_material_band.band_width_type_name,
            material_band_base_price = str(bm_contract_material_band.base_price)

        # 查找授权人的信息
        bm_contract_authorizer = auth_models.BmUserInfo.objects.filter(id=bm_contract_material_account_id).first()
        if not bm_contract_authorizer:
            account = ""
        else:
            account = bm_contract_authorizer.account
        # 查找下单者的一些信息
        bm_account_info = auth_models.BmUserInfo.objects.filter(id=max_band_ip_dict.get("account_id")).first()
        if not bm_account_info:
            identity_name = "",
            user_account = ""
        else:
            identity_name = bm_account_info.identity_name,
            user_account = bm_account_info.account
        # 查找订单信息
        bm_contract_order = service_model.BmServiceOrder.objects.filter(id=max_band_ip_dict.get("order_id")).first()
        if not bm_contract_order:
            region = ""
        else:
            region = bm_contract_order.region

        # 查找项目信息
        bm_contract_project = service_model.BmProject.objects.filter(id=max_band_ip_dict.get("project_id")).first()
        project_name = ""
        if bm_contract_project:
            project_name = bm_contract_project.project_name

        material_ip_dict = {
            "id": max_band_ip_dict.get("id"),
            "用户ID": max_band_ip_dict.get("account_id"),
            "用户名称": identity_name[0],
            "用户邮箱": user_account,
            "合同编号": max_band_ip_dict.get("contract_number"),
            "查询日期": date_ip,
            "带宽物料编码": material_band_material_number[0],
            "带宽类型": band_width_type_name[0],
            "带宽价格": material_band_base_price,
            "IP物料编码": material_number[0],
            "IP物料类型": floating_ip_type_name[0],
            "IP价格": base_price,
            "合同可用区": region,
            "销售姓名": sales[0],
            "公司编码": enterprise_number[0],
            "公司所属区": location[0],
            "客服姓名": customer_service_name,
            "服务到期时间": service_expired_time,
            "服务开始时间": service_start_time,
            "合同开始时间": bm_contract_material_start_date,
            "合同到期时间": bm_contract_material_expire_date,
            "客户名称": bm_contract_material_customer_name,
            "合同授权人": bm_contract_material_authorizer,
            "合同类型": bm_contract_material_contract_type,
            "合同授权人邮箱": account,
            "IP类型": max_band_ip_dict.get("external_line_type"),
            "IP类型名称": max_band_ip_dict.get("external_name"),
            "IP类型ID": max_band_ip_dict.get("external_name_id"),
            "IP": max_band_ip_dict.get("floating_ip"),
            "ip_id": max_band_ip_dict.get("floating_ip_id"),
            "订单号": max_band_ip_dict.get("order_id"),
            "项目ID": max_band_ip_dict.get("project_id"),
            "项目名称": project_name,
            "服务状态": max_band_ip_dict.get("status"),
            "最大带宽": max_band,
        }

    except Exception as ex:
        return False
    return material_ip_dict


class Material(TestCase):
    def material_test(self):
        now = lambda: time.time()
        start = now()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(material_ip_day())
        print('使用协程TIME: ', now() - start)

    def material_test11(self):
        now = lambda: time.time()
        start = now()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(material_ip_day11())
        print('使用协程TIME: ', now() - start)

    def material_test2(self):
        now = lambda: time.time()
        start = now()
        # material_day_ip_obj1 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-13")
        # material_day_ip_obj2 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-14")
        # material_day_ip_obj3 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-15")
        # material_day_ip_obj4 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-16")
        # material_day_ip_obj5 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-17")
        # material_day_ip_obj6 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-18")
        # material_day_ip_obj7 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-19")
        # material_day_ip_obj8 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-20")
        material_day_ip_obj1 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-13")
        material_day_ip_obj2 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-14")
        material_day_ip_obj3 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-15")
        material_day_ip_obj4 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-16")
        material_day_ip_obj5 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-17")
        material_day_ip_obj6 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-18")
        material_day_ip_obj7 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-19")
        material_day_ip_obj8 = material_ip_day_by_ip_id2("b67037e1-85a2-436d-b232-566d861637d3", "2020-2-20")
        # material_day_ip_obj1 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-13")
        # material_day_ip_obj2 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-14")
        # material_day_ip_obj3 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-15")
        # material_day_ip_obj4 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-16")
        # material_day_ip_obj5 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-17")
        # material_day_ip_obj6 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-18")
        # material_day_ip_obj7 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-19")
        # material_day_ip_obj8 = material_ip_day_by_ip_id2("726efd82-6ceb-44ae-93b9-ba55abb02f32", "2020-2-20")
        print('不使用协程TIME: ', now() - start)

    def material_test22(self):
        now = lambda: time.time()
        start = now()
        material_day_ip_obj1 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-13")
        material_day_ip_obj2 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-14")
        material_day_ip_obj3 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-15")
        material_day_ip_obj4 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-16")
        material_day_ip_obj5 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-17")
        material_day_ip_obj6 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-18")
        material_day_ip_obj7 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-19")
        material_day_ip_obj8 = material_ip_day_by_ip_id2("5e749686-25f7-4a62-a59a-534c4035db92", "2020-2-20")
        print('不使用协程TIME: ', now() - start)

    def material_test3(self):
        now = lambda: time.time()
        start = now()
        threads = []
        threads.append(threading.Thread(target=self.material_test22()))
        threads.append(threading.Thread(target=self.material_test2()))
        for t in threads:
            print("%s: %s" % (t, time.ctime(time.time())))
            t.start()

        print('使用多线程TIME: ', now() - start)

    def material_test4(self):
        now = lambda: time.time()
        start = now()
        threads = []
        threads.append(threading.Thread(target=self.material_test()))
        threads.append(threading.Thread(target=self.material_test11()))
        for t in threads:
            print("%s: %s" % (t, time.ctime(time.time())))
            t.start()

        print('使用多线程TIME: ', now() - start)

    def material_test33(self):
        now = lambda: time.time()
        start = now()
        material_ip_day3()
        print('使用gevent——TIME: ', now() - start)
