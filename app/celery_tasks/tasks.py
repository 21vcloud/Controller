from __future__ import absolute_import
from celery import shared_task


@shared_task
def job_executor(data):
    pass

@shared_task(ignore_result=True)
def associate_firewall(floating_ip, firewall, firewall_rules, traffic_shaper=None):
   pass


@shared_task(ignore_result=True)
def add_firewall_rule(floating_objects, firewall, firewall_rule):
    """

    :param floating_objects: e.g. [{"floating_ip": "10.10.10.10", "traffic_shaper": self.traffic_name},
                             {"floating_ip": "10.10.10.11", "traffic_shaper": self.traffic_name}]
    :param firewall: firewall object
    :param firewall_rule: firewall rule object
    :return:
    """
    pass


@shared_task(ignore_result=True)
def update_firewall_rule(floating_objects, firewall, firewall_rule):
    pass


@shared_task(ignore_result=True)
def remove_firewall_rule(firewall, firewall_rule):
    pass


@shared_task(ignore_result=True)
def disassociate_firewall(floating_ip, firewall):
    pass


@shared_task(ignore_result=True)
def update_fip_firewall(fip, old_firewall, new_firewall, new_firewall_rules, traffic_shaper=None):
    pass


@shared_task
def add_traffic_shaper(name, maximum_bandwidth_KB):
    pass

@shared_task
def udate_traffic_shaper(name, maximum_bandwidth_KB):
    pass

@shared_task
def delete_traffic_shaper(names):
    pass

@shared_task
def test_return_res(name):
    pass