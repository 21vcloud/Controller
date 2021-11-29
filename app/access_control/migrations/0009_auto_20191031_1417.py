# Generated by Django 2.1.7 on 2019-10-31 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0008_auto_20191029_1106'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='owner',
            field=models.CharField(blank=True, help_text='专有角色关联', max_length=64, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='element',
            unique_together={('owner_path', 'element_id')},
        ),
    ]