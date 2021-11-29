# -*- coding:utf-8 -*-
from django.shortcuts import render
from rest_framework import viewsets


class DashboardViews(viewsets.ViewSet):
    def get_index(self, request):
        return render(request, 'index.html')
