# Generated by Django 2.1.7 on 2019-11-07 14:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0011_role_role_level'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='permission',
            unique_together={('type', 'type_id', 'action', 'disabled')},
        ),
    ]
