# Generated by Django 2.1.7 on 2019-11-07 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0010_auto_20191031_1453'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='role_level',
            field=models.CharField(default='all_set', help_text='角色级别', max_length=32),
        ),
    ]
