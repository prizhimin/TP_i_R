from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .forms import CustomAuthenticationForm, ChangePasswordForm


from django.contrib.auth import update_session_auth_hash
#  from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.shortcuts import render, redirect


def custom_logout(request):
    # Выполнение дополнительных действий перед выходом
    # Например, сохранение логов или установка флага "выход выполнен"

    # Вызов стандартной функции выхода из системы
    logout(request)

    # Перенаправление на страницу, указанную в настройках LOGIN_REDIRECT_URL
    return redirect('accounts:login')


def login_view(request):
    return auth_views.LoginView.as_view(template_name='accounts/login.html',
                                        authentication_form=CustomAuthenticationForm)(request)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            new_password2 = form.cleaned_data['new_password2']

            # Проверяем, совпадают ли новый пароль и его подтверждение
            if new_password1 != new_password2:
                return redirect('accounts:change_password')

            # Проверяем, правильно ли введён старый пароль
            if not request.user.check_password(old_password):
                return redirect('accounts:change_password')

            # Изменяем пароль пользователя
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Обновляем сессию пользователя
            messages.success(request, "Пароль успешно изменен.")
            return render(request, 'accounts/password_changed.html')

    else:
        form = ChangePasswordForm()

    return render(request, 'accounts/change_password.html', {'form': form})
