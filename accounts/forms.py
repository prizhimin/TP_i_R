from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Пользователь', max_length=254)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="Старый пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Подтвердите новый пароль", widget=forms.PasswordInput)
