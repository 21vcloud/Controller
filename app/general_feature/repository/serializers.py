from django.db import models
from rest_framework import serializers

class NoneMeta(models.Model):
    class Meta:
        managed = False
        db_table = 'NoneMeta'


class MessageSendSerializer(serializers.Serializer):
    email_to_list = serializers.ListField(required=False, label="收件人", help_text="[wei@163.com]")
    sms_to_list = serializers.ListField(required=False, label="收件人", help_text="[18100009999]")
    param_info = serializers.DictField(required=True, label="发送信息变量",
                                       help_text={"status": "error", "alarm_level": "Error",
                                                  "alarm_content": "邮件测试@23124#￥%", "rule_value": "90",
                                                  "alarm_value": "1000", "rule_id": "EASD12312314", "host": "测试机器",
                                                  "alarm_time": "10"})
    message_type = serializers.ListField(required=True, label="发送消息方式", help_text=["mail", "sms"])

    # class Meta:
    #     model = NoneMeta
    #     fields = ["email_to_list", "sms_to_list", "param_info", "message_type"]
