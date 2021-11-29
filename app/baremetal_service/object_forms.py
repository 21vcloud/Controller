# -*- coding: utf-8 -*-

from django import forms


class UploadObjectForm(forms.Form):
    file = forms.FileField(required=False)