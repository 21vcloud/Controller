# coding:utf-8
from __future__ import absolute_import

from django.core.cache import cache
from django.shortcuts import reverse
from django.http import HttpRequest
from django.utils.cache import get_cache_key


def expire_page_cache(view, curreq, args=None, key_prefix=None):
    """
    Removes cache created by cache_page functionality.
    Parameters are used as they are in reverse()
    """

    if args is None:
        path = reverse(view)
    else:
        path = reverse(view, args=args)

    http_host = curreq.META.get("HTTP_HOST", "")
    if len(http_host.split(":")) == 1:
        server_name, server_port = http_host, "80"
    else:
        server_name, server_port = http_host.split(":")

    request = HttpRequest()
    request.META = {'SERVER_NAME': server_name, 'SERVER_PORT': server_port}
    request.META.update(dict((header, value) for (header, value) in
                             curreq.META.items() if header.startswith('HTTP_')))
    request.path = path
    key = get_cache_key(request, key_prefix=key_prefix)
    value = cache.get(key)
    if key and cache.get(key):
        a = cache.set(key, None, 0)
        b = cache.get(key)
        return a
