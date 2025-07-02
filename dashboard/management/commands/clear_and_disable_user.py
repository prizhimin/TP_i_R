from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import UserApp
from daily.models import UserDepartment  # Импортируем модель UserDepartment
from general_weekly.models import WeeklyUserDepartment  # Импортируем модель WeeklyUserDepartment
from investigations.models import InvestigationUserDepartment  # Импортируем модель InvestigationUserDepartment
from annualreport2024.models import Annual2024UserCompany  # Импортируем модель Annual2024UserCompany
from sixmonths2024.models import SemiAnnual2024UserCompany  # Импортируем модель SemiAnnual2024Company

class Command(BaseCommand):
    help = "Очищает список доступных приложений и филиалов для указанного пользователя и делает его неактивным."

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')

    def handle(self, *args, **kwargs):
        username = kwargs['username']


        try:
            # Находим пользователя
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print(f"Пользователь '{username}' не найден.")
            return

        # Делаем пользователя неактивным
        user.is_active = False
        user.save()
        print(f"Пользователь '{username}' теперь неактивен.")

        # Очищаем список приложений (если запись UserApp существует)
        if UserApp.objects.filter(user=user).exists():
            user_app = UserApp.objects.get(user=user)
            user_app.app.clear()
            print(f"Список приложений для пользователя '{username}' успешно очищен.")

        # Очищаем список филиалов для ежедневных отчётов (если запись UserDepartment существует)
        if UserDepartment.objects.filter(user=user).exists():
            user_department = UserDepartment.objects.get(user=user)
            user_department.department.clear()
            print(f"Список филиалов для ежедневных отчётов по охране пользователя '{username}' успешно очищен.")

        # Очищаем список филиалов для еженедельных отчётов (если запись WeeklyUserDepartment существует)
        if WeeklyUserDepartment.objects.filter(user=user).exists():
            weekly_user_department = WeeklyUserDepartment.objects.get(user=user)
            weekly_user_department.department.clear()
            print(f"Список филиалов для еженедельных отчётов по охране пользователя '{username}' успешно очищен.")

        # Очищаем список филиалов для служебных проверок (если запись InvestigationUserDepartment существует)
        if InvestigationUserDepartment.objects.filter(user=user).exists():
            investigation_user_department = InvestigationUserDepartment.objects.get(user=user)
            investigation_user_department.department.clear()
            print(f"Список филиалов для служебных проверок пользователя '{username}' успешно очищен.")

        # Очищаем список компаний для отчёта за 2024 год (если запись Annual2024UserCompany существует)
        if Annual2024UserCompany.objects.filter(user=user).exists():
            annual_user_company = Annual2024UserCompany.objects.get(user=user)
            annual_user_company.companies.clear()
            print(f"Список компаний для отчёта за 2024 год пользователя '{username}' успешно очищен.")

        # Очищаем список компаний для отчёта за 6 месяцев 2024 года (если запись SemiAnnual2024Company существует)
        if SemiAnnual2024UserCompany.objects.filter(user=user).exists():
            semi_annual_user_company = SemiAnnual2024UserCompany.objects.get(user=user)
            semi_annual_user_company.companies.clear()
            print(f"Список компаний для отчёта за 6 месяцев 2024 года пользователя '{username}' успешно очищен.")
