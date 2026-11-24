from django.urls import path
from admin_me import viewss

urlpatterns = [
    path('', viewss.login_view, name='admin_login'),
    path('index2/', viewss.index, name='index2'),
    path('accounts/', viewss.accounts, name='accounts'), 
]
