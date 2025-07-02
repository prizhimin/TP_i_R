from django.core.management import BaseCommand

from dashboard.models import App, UserApp

class Command(BaseCommand):
    help='Удаляет sixmonths2024 из списка доступных приложений у всех пользователей'

    def handle(self, *args, **kwargs):
        """
        Перебираем циклом все объекты UserApp и удаляем из app ссылки на объект App с name='sixmonths2024'
        """
        sixmonths2024_app = App.objects.filter(name='sixmonths2024').first()
        if sixmonths2024_app:
            for user_app in UserApp.objects.all():
                if sixmonths2024_app in user_app.app.all():
                    user_app.app.remove(sixmonths2024_app)
                    user_app.save()
                    print(f"Приложение sixmonths2024 удалено для пользователя {user_app.user.username}")
        else:
            print("Приложение sixmonths2024 не найдено в базе данных.")
