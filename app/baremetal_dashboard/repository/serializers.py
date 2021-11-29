from django.db import models
from rest_framework import serializers

from baremetal_dashboard.repository import baremental_model


class NoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


class GetConfInfoSerializer(serializers.ModelSerializer):
    key_value = serializers.CharField(required=True, label="关键词",help_text="示例：ApplicationIndustryList")

    class Meta:
        model = NoneMeta
        fields = ["key_value"]


class ContactToUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = baremental_model.BmContactToUs
        exclude = ('id', "update_at")


class ContactToUsForDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = baremental_model.BmContactToUsForDiscount
        exclude = ('id', "update_at")
