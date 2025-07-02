from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from .models import App, UserApp, NoRunDate
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count

class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'comment')
    list_filter = ('name', 'comment')
    search_fields = ('name', 'comment')
    ordering = ('name',)


class AppFilter(admin.SimpleListFilter):
    title = 'Доступные приложения'
    parameter_name = 'app'

    def lookups(self, request, model_admin):
        # Получаем приложения с аннотацией количества пользователей
        apps = App.objects.annotate(user_count=Count('userapp')).order_by('name')
        lookups = []

        for app in apps:
            # Формируем базовое отображение названия приложения
            app_display = app.name

            # Добавляем крестик только если приложение используется (user_count > 0)
            if app.user_count > 0:
                delete_url = reverse('dashboard:delete_app_from_all', args=[app.id])
                app_display = mark_safe(
                    f'{app.name} <a href="{delete_url}" style="color: red; margin-left: 5px;" '
                    f'title="Удалить у всех пользователей" onclick="return confirm(\'Вы уверены?\')">×</a>'
                )

            lookups.append((app.id, app_display))

        return lookups

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(app__id=self.value())
        return queryset


class UserAppAdminForm(forms.ModelForm):
    class Meta:
        model = UserApp
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Получаем ID активных пользователей (is_active=True) с привязками
        users_with_apps = UserApp.objects.filter(
            user__is_active=True
        ).values_list('user_id', flat=True)

        # Формируем queryset: активные пользователи без привязок
        free_users = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=users_with_apps
        ).order_by('last_name', 'first_name')

        # При редактировании добавляем текущего пользователя
        if self.instance and self.instance.user_id:
            free_users = free_users | User.objects.filter(id=self.instance.user_id)

        # Настраиваем поле user
        self.fields['user'].queryset = free_users
        self.fields['user'].label_from_instance = lambda obj: (
            f"{obj.last_name} {obj.first_name} - {obj.username}"
            if obj.last_name and obj.first_name
            else obj.username
        )


class UserAppAdmin(admin.ModelAdmin):
    form = UserAppAdminForm
    list_display = ('get_user_fullname', 'user', 'display_apps')
    list_filter = (AppFilter, 'user__username', 'user__last_name')
    filter_horizontal = ('app',)
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email'
    )
    list_select_related = ('user',)

    def get_user_fullname(self, obj):
        """Формат: Фамилия Имя (логин)"""
        fullname = f"{obj.user.last_name} {obj.user.first_name}".strip()
        return f"{fullname} ({obj.user.username})" if fullname else obj.user.username

    get_user_fullname.short_description = 'Пользователь'
    get_user_fullname.admin_order_field = 'user__last_name'

    def display_apps(self, obj):
        """Отображает список приложений пользователя"""
        return ", ".join([app.comment for app in obj.app.all().order_by('comment')])

    display_apps.short_description = 'Доступные приложения'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('app')


class NoRunDateAdmin(admin.ModelAdmin):
    list_display = ('date', 'display_apps')
    list_filter = ('date', 'apps')
    filter_horizontal = ('apps',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    def display_apps(self, obj):
        return ", ".join([app.comment for app in obj.apps.all().order_by('comment')])

    display_apps.short_description = 'Запрещенные приложения'


admin.site.register(App, AppAdmin)
admin.site.register(UserApp, UserAppAdmin)
admin.site.register(NoRunDate, NoRunDateAdmin)
