from django.conf.urls import url
from rest_api.views import  AccountRoleRestfulViews,AccountContractRestfulViews,AccountProjectRestfulViews,\
    AccountUserRestfulViews,AccountEnterpriseRestfulViews


urlpatterns = [
    #restful
    url(r'^contract', AccountContractRestfulViews.as_view()),
    url(r'^role', AccountRoleRestfulViews.as_view()),
    url(r'^project', AccountProjectRestfulViews.as_view()),
    url(r'^user', AccountUserRestfulViews.as_view()),
    url(r'^enterprise', AccountEnterpriseRestfulViews.as_view()),
]

