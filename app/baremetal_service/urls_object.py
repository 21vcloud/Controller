# -*- coding: utf-8 -*-

from django.conf.urls import url
from baremetal_service import views

urlpatterns = [
    url(r'create_bucket', views.ObjectViews.as_view({"post": "create_bucket"}), name='create_bucket'),
    url(r'list_bucket', views.ObjectViews.as_view({"get": "list_bucket"}), name='list_bucket'),
    url(r'show_bucket', views.ObjectViews.as_view({"get": "show_bucket"}), name='show_bucket'),
    url(r'delete_bucket', views.ObjectViews.as_view({"post": "delete_bucket"}), name='delete_bucket'),
    url(r'update_bucket', views.ObjectViews.as_view({"post": "update_bucket"}), name='update_bucket'),

    # object
    url(r'create_dir', views.ObjectViews.as_view({"post": "create_dir"}), name='create_dir'),
    url(r'list_objects', views.ObjectViews.as_view({"get": "list_objects"}), name='list_objects'),
    url(r'show_object', views.ObjectViews.as_view({"get": "show_object"}), name='show_object'),
    url(r'delete_object', views.ObjectViews.as_view({"post": "delete_object"}), name='delete_object'),
    url(r'download_file', views.ObjectViews.as_view({"get": "download_file"}), name='download_file'),
    url(r'upload_file', views.ObjectViews.as_view({"post": "upload_file"}), name='upload_file'),
    # url(r'generate_url', views.ObjectViews.as_view({"get": "generate_url"}), name='generate_url'),
    url(r'copy_object', views.ObjectViews.as_view({"post": "copy_object"}), name="copy_object"),
]
