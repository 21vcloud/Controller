# Generated by Django 2.1.7 on 2019-10-22 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0003_auto_20191022_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permission',
            name='type_id',
            field=models.CharField(help_text='控制元素的坐标', max_length=64),
        ),
    ]