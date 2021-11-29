# Register your models here.

from django.contrib import admin

from .repository.auth_models import BmUserInfo, BmProject


class BmUserInfoForm(admin.ModelAdmin):
    list_display = ('id', 'account', 'identity_name', 'identity_card', 'create_at',  'update_at',  'deleted_at')
    search_fields = ('account', )


class BmProjectForm(admin.ModelAdmin):
    list_display = ('id', 'project_name', 'status')
    search_fields = ('id', 'project_name', 'status')


admin.site.register(BmUserInfo, BmUserInfoForm)
admin.site.register(BmProject, BmProjectForm)
