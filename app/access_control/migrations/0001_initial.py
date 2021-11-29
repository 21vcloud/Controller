# Generated by Django 2.1.7 on 2019-10-21 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Element',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_path', models.CharField(blank=True, help_text='url地址', max_length=256, null=True)),
                ('owner_path', models.CharField(help_text='元素归属模块', max_length=128)),
                ('type', models.CharField(choices=[('saber', 'saber'), ('header', 'header'), ('navbar', 'navbar'), ('button', 'button')], help_text='元素类型', max_length=32)),
                ('html_laber', models.CharField(blank=True, help_text='元素名称', max_length=128, null=True)),
                ('notices', models.TextField(help_text='备注')),
                ('element_id', models.CharField(blank=True, help_text='元素在页面上的id', max_length=64, null=True)),
                ('sort_id', models.CharField(blank=True, help_text='排序id', max_length=64, null=True)),
            ],
            options={
                'db_table': 'bm_access_control_element',
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('Atom', 'Atom')], help_text='权限的类型', max_length=64)),
                ('type_id', models.IntegerField(help_text='控制元素的坐标')),
                ('action', models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE'), ('SHOW', 'SHOW')], help_text='授权动作', max_length=64)),
                ('permission_level', models.CharField(help_text='权限级别', max_length=64)),
            ],
            options={
                'db_table': 'bm_access_control_permission',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='角色名称', max_length=64)),
                ('notices', models.TextField(help_text='备注')),
                ('create_at', models.DateTimeField(auto_now_add=True, help_text='创建时间')),
            ],
            options={
                'db_table': 'bm_access_control_role',
            },
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.ForeignKey(help_text='关联权限', on_delete=django.db.models.deletion.CASCADE, to='access_control.Permission')),
                ('role', models.ForeignKey(help_text='关联角色', on_delete=django.db.models.deletion.CASCADE, to='access_control.Role')),
            ],
        ),
        migrations.CreateModel(
            name='RoleUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.ForeignKey(help_text='关联角色', on_delete=django.db.models.deletion.CASCADE, to='access_control.Role')),
                ('user', models.ForeignKey(help_text='关联用户', on_delete=django.db.models.deletion.CASCADE, to='account.BmUserInfo')),
            ],
        ),
    ]
