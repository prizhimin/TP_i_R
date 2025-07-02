from django.contrib import admin
from .models import Department


# Register your models here.
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    # Определяем порядок сортировки по алфавиту по полю 'name'
    ordering = ['name']
