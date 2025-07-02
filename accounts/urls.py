from django.urls import path
from .views import custom_logout, login_view, change_password

app_name = 'accounts'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', custom_logout, name='custom_logout'),
    path('change_password/', change_password, name='change_password'),
]
