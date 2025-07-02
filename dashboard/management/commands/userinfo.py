from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import UserApp
from daily.models import UserDepartment
from general_weekly.models import WeeklyUserDepartment
from investigations.models import InvestigationUserDepartment
from annualreport2024.models import Annual2024UserCompany
from sixmonths2024.models import SemiAnnual2024UserCompany

class Command(BaseCommand):
    help = "Выводит информацию о пользователе, включая доступные приложения, филиалы и компании."

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

        # Выводим информацию о пользователе
        print(f"Информация о пользователе '{username}':")

        # Проверяем и выводим доступные приложения
        if UserApp.objects.filter(user=user).exists():
            user_app = UserApp.objects.get(user=user)
            apps = user_app.app.all()
            if apps:
                print("Доступные приложения:")
                for app in apps:
                    print(f" - {app.name}")
            else:
                print("Нет доступных приложений.")
        else:
            print("Нет доступных приложений.")

        # Проверяем и выводим доступные филиалы для ежедневных отчётов
        if UserDepartment.objects.filter(user=user).exists():
            user_department = UserDepartment.objects.get(user=user)
            departments = user_department.department.all()
            if departments:
                print("Доступные филиалы для ежедневных отчётов:")
                for department in departments:
                    print(f" - {department.name}")
            else:
                print("Нет доступных филиалов для ежедневных отчётов.")
        else:
            print("Нет доступных филиалов для ежедневных отчётов.")

        # Проверяем и выводим доступные филиалы для еженедельных отчётов
        if WeeklyUserDepartment.objects.filter(user=user).exists():
            weekly_user_department = WeeklyUserDepartment.objects.get(user=user)
            departments = weekly_user_department.department.all()
            if departments:
                print("Доступные филиалы для еженедельных отчётов:")
                for department in departments:
                    print(f" - {department.name}")
            else:
                print("Нет доступных филиалов для еженедельных отчётов.")
        else:
            print("Нет доступных филиалов для еженедельных отчётов.")

        # Проверяем и выводим доступные филиалы для служебных проверок
        if InvestigationUserDepartment.objects.filter(user=user).exists():
            investigation_user_department = InvestigationUserDepartment.objects.get(user=user)
            departments = investigation_user_department.department.all()
            if departments:
                print("Доступные филиалы для служебных проверок:")
                for department in departments:
                    print(f" - {department.name}")
            else:
                print("Нет доступных филиалов для служебных проверок.")
        else:
            print("Нет доступных филиалов для служебных проверок.")

        # Проверяем и выводим доступные компании для отчёта за 2024 год
        if Annual2024UserCompany.objects.filter(user=user).exists():
            annual_user_company = Annual2024UserCompany.objects.get(user=user)
            companies = annual_user_company.companies.all()
            if companies:
                print("Доступные компании для отчёта за 2024 год:")
                for company in companies:
                    print(f" - {company.name}")
            else:
                print("Нет доступных компаний для отчёта за 2024 год.")
        else:
            print("Нет доступных компаний для отчёта за 2024 год.")

        # Проверяем и выводим доступные компании для отчёта за 6 месяцев 2024 года
        if SemiAnnual2024UserCompany.objects.filter(user=user).exists():
            semi_annual_user_company = SemiAnnual2024UserCompany.objects.get(user=user)
            companies = semi_annual_user_company.companies.all()
            if companies:
                print("Доступные компании для отчёта за 6 месяцев 2024 года:")
                for company in companies:
                    print(f" - {company.name}")
            else:
                print("Нет доступных компаний для отчёта за 6 месяцев 2024 года.")
        else:
            print("Нет доступных компаний для отчёта за 6 месяцев 2024 года.")
