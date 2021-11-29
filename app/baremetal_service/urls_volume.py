# -*- coding:utf-8 -*-

from django.conf.urls import url
from baremetal_service.views import BaremetalServiceVolumeViews


urlpatterns = [

    url(r'^volume_create_with_order$', BaremetalServiceVolumeViews.as_view({"post": "volume_create_with_order"}), name='volume_create_with_order'),
    url(r'^volume_create$', BaremetalServiceVolumeViews.as_view({"post": "volume_create"}), name='volume_create'),
    url(r'^volume_attach$', BaremetalServiceVolumeViews.as_view({"post": "volume_attach"}), name='volume_attach'),
    url(r'^volume_detach$', BaremetalServiceVolumeViews.as_view({"post": "volume_detach"}), name='volume_detach'),
    url(r'^volume_list$', BaremetalServiceVolumeViews.as_view({"get": "volume_list"}), name='volume_list'),
    url(r'^volume_list_no_attached$', BaremetalServiceVolumeViews.as_view({"get": "volume_list_no_attached"}),
        name='volume_list_no_attached'),
    url(r'^volume_update$', BaremetalServiceVolumeViews.as_view({"post": "volume_update"}), name='volume_update'),
    url(r'volume_type_list', BaremetalServiceVolumeViews.as_view({"post": "volume_type_list"}),
        name='volume_type_list'),
    url(r'volume_delete', BaremetalServiceVolumeViews.as_view({"post": "volume_delete"}), name='volume_delete'),
    url(r'volume_roll_back', BaremetalServiceVolumeViews.as_view({"post": "volume_roll_back"}), name='volume_roll_back'),
    url(r'volume_backup_create', BaremetalServiceVolumeViews.as_view({"post": "volume_backup_create"}),
        name='volume_backup_create'),
    url(r'volume_backup_list', BaremetalServiceVolumeViews.as_view({"get": "volume_backup_list"}),
        name='volume_list_backup'),
    url(r'volume_backup_delete', BaremetalServiceVolumeViews.as_view({"post": "volume_backup_delete"}),
        name="volume_backup_delete"),
    url(r'volume_backup_restore', BaremetalServiceVolumeViews.as_view({"post": "volume_backup_restore"}),
        name='volume_backup_restore'),
    url(r'volume_quota', BaremetalServiceVolumeViews.as_view({"get": "volume_quota"}), name='volume_quota'),
    url(r'^feedback_volume_attach$', BaremetalServiceVolumeViews.as_view({"post": "feedback_volume_attach"}),
        name='feedback_volume_attach')
]
