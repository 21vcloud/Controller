# -*- coding:utf-8 -*-

from django.conf.urls import url
from baremetal_service.views import BaremetalMaterialViews

urlpatterns = [
    # url(r'^material_ip_calculate_in_range$', BaremetalMaterialViews.as_view({"get": "material_ip_calculate_in_range"}), name='material_ip_calculate_in_range'),
    url(r'^material_volume_seasonal$', BaremetalMaterialViews.as_view({"get": "material_volume_contract_seasonal"}), name='material_volume_contract_seasonal'),
    url(r'^material_volume_bak_seasonal$', BaremetalMaterialViews.as_view({"get": "material_volume_bak_contract_seasonal"}), name='material_volume_bak_contract_seasonal'),
    url(r'^material_machine_seasonal$', BaremetalMaterialViews.as_view({"get": "material_machine_contract_seasonal"}), name='material_machine_contract_seasonal'),
    url(r'^material_nat_seasonal$', BaremetalMaterialViews.as_view({"get": "material_nat_contract_seasonal"}), name='material_nat_contract_seasonal'),
    url(r'^material_ip_seasonal', BaremetalMaterialViews.as_view({"get": "material_ip_seasonal"}), name='material_ip_seasonal'),
    url(r'^material_lb_seasonal', BaremetalMaterialViews.as_view({"get": "material_lb_contract_seasonal"}), name='material_lb_contract_seasonal'),
    url(r'^material_into_mysql', BaremetalMaterialViews.as_view({"get": "material_into_mysql"}), name='material_into_mysql'),
    url(r'^get_material_from_mysql', BaremetalMaterialViews.as_view({"get": "get_material_from_mysql"}), name='get_material_from_mysql'),
    url(r'^material_share_band_seasonal', BaremetalMaterialViews.as_view({"get": "material_share_band_seasonal"}), name='material_share_band_seasonal'),
]
