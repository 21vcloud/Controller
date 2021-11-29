# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.fields.related import ManyToManyField
from account.repository.auth_models import BmUserInfo


class AccessKey(models.Model):
    access_key = models.ForeignKey(BmUserInfo, help_text="访问密钥ID", on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=256, help_text="访问秘钥")
    enabled = models.BooleanField(default=True, help_text="启动/禁用")
    create_at = models.DateTimeField(blank=True, null=True, help_text="创建时间")
    # second_secret_key = models.CharField(max_length=256, blank=True, null=True, help_text="备用密钥")

    def to_dict(self):
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    def __unicode__(self):
        return self.access_key

    class Meta:
        db_table = 'bm_access_key'
        unique_together = ('access_key', 'secret_key')





