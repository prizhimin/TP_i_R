from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import FileResponse
from django.conf import settings

import os

from .models import UserApp
from .models import App, UserApp
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def dashboard(request):
    # Получаем текущего пользователя
    user = request.user
    # Получаем список приложений для текущего пользователя
    user_apps = UserApp.objects.filter(user=user).first()
    if user_apps:
        apps = user_apps.app.all().order_by('comment')
    else:
        apps = []

    context = {
        'apps': apps,
        'is_admin': user.is_staff  # Добавляем проверку прав администратора
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def ssl_certificate(request):
    return FileResponse(open(os.path.join(settings.BASE_DIR, 'dashboard', 'templates', 'dashboard', 'Сертификат prm-ad01-app97.zip'), 'rb'),
                        as_attachment=True,
                        filename='Сертификат prm-ad01-app97.zip')


# @staff_member_required
# def delete_app_from_all(request, app_id):
#     if not request.user.is_staff:
#         return redirect('admin:login')
#
#     try:
#         app = App.objects.get(id=app_id)
#         # Удаляем приложение у всех пользователей
#         UserApp.objects.filter(app=app).update(app=app.app.remove(app))
#         messages.success(request, f'Приложение "{app.name}" удалено у всех пользователей')
#     except App.DoesNotExist:
#         messages.error(request, 'Приложение не найдено')
#
#     return redirect('admin:app_userapp_changelist')

@staff_member_required
def delete_app_from_all(request, app_id):
    app = get_object_or_404(App, id=app_id)

    # Получаем все UserApp, где есть это приложение
    user_apps = UserApp.objects.filter(app=app)

    # Удаляем приложение из всех связей ManyToMany
    for user_app in user_apps:
        user_app.app.remove(app)

    messages.success(request, f'Приложение "{app.name}" удалено у всех пользователей')
    return redirect('admin:dashboard_userapp_changelist')