from django.apps import apps
from django.shortcuts import redirect
from functools import wraps
from .models import UserApp
from django.utils import timezone
from .models import NoRunDate
from django.core.management.base import CommandError



def access_control_required(allowed_apps):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                user_apps = UserApp.objects.filter(user=request.user)
                user_app_names = [user_app.app.name for user_app in user_apps]
                # Проверяем, есть ли у пользователя доступ к приложению
                if set(allowed_apps).intersection(user_app_names):
                    return view_func(request, *args, **kwargs)
            return redirect('access_denied')
        return wrapper
    return decorator


def restricted_app_decorator_for_command(cls):
    @wraps(cls, updated=())
    class WrappedCommand(cls):
        def handle(self, *args, **options):
            # 1. Определяем текущее приложение
            module_name = cls.__module__
            app_config = apps.get_containing_app_config(module_name)

            if not app_config:
                self.stdout.write(self.style.WARNING(f"Не удалось определить приложение для модуля: {module_name}"))
                return super().handle(*args, **options)

            app_name = app_config.name

            # 2. Проверяем запреты на сегодня
            today = timezone.now().date()
            if NoRunDate.objects.filter(date=today, apps__name=app_name).exists():
                raise CommandError(f"Приложение {app_name} запрещено к запуску сегодня ({today})")

            # 3. Если запретов нет - выполняем команду
            return super().handle(*args, **options)

    return WrappedCommand