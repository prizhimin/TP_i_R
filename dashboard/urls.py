from django.urls import path

from .views import dashboard, ssl_certificate, delete_app_from_all

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('ssl_certificate/', ssl_certificate, name='ssl_certificate'),
    path('delete_app_from_all/<int:app_id>/', delete_app_from_all, name='delete_app_from_all'),
]
