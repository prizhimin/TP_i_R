from django.contrib import admin
from django import forms
from django.contrib.auth.models import User

from commondata.models import Department
from .models import Tpir, TpirFacility, TpirAttachedFile, TpirFinance, TpirUserDepartment
from dashboard.models import UserApp


class DepartmentAdmin(admin.ModelAdmin):
    list_filter = ('name',)
    ordering = ('name',)
    list_display = ('name',)
    search_fields = ('name',)


class DepartmentFilter(admin.SimpleListFilter):
    title = 'Доступные филиалы'
    parameter_name = 'department'

    def lookups(self, request, model_admin):
        departments = Department.objects.all()
        return [(dept.id, dept.name) for dept in departments]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department__id=self.value())
        return queryset


class TpirUserDepartmentForm(forms.ModelForm):
    class Meta:
        model = TpirUserDepartment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        users_with_departments = TpirUserDepartment.objects.values_list('user_id', flat=True)
        users_with_tpir_app = UserApp.objects.filter(
            app__name='tpir'
        ).values_list('user_id', flat=True)

        eligible_users = User.objects.filter(
            is_active=True,
            id__in=users_with_tpir_app
        ).exclude(
            id__in=users_with_departments
        ).order_by('last_name', 'first_name')

        if self.instance and self.instance.user_id:
            eligible_users = eligible_users | User.objects.filter(id=self.instance.user_id)

        self.fields['user'].queryset = eligible_users
        self.fields['user'].label_from_instance = lambda obj: (
            f"{obj.last_name} {obj.first_name} ({obj.username})"
            if obj.last_name and obj.first_name
            else obj.username
        )


class TpirUserDepartmentAdmin(admin.ModelAdmin):
    form = TpirUserDepartmentForm
    list_display = ('get_user_fullname', 'get_departments')
    list_filter = (DepartmentFilter,)
    filter_horizontal = ('department',)
    search_fields = (
        'user__username',
        'user__last_name',
        'user__first_name',
        'user__email'
    )

    def get_user_fullname(self, obj):
        fullname = f"{obj.user.last_name} {obj.user.first_name}".strip()
        return f"{fullname} ({obj.user.username})" if fullname else obj.user.username

    get_user_fullname.short_description = 'Пользователь'
    get_user_fullname.admin_order_field = 'user__last_name'

    def get_departments(self, obj):
        return ", ".join([d.name for d in obj.department.all().order_by('name')])

    get_departments.short_description = 'Доступные филиалы'


class TpirFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'department__name')
    ordering = ('name',)


class TpirAttachedFileInline(admin.TabularInline):
    model = TpirAttachedFile
    extra = 0


class TpirFinanceInline(admin.TabularInline):
    model = TpirFinance
    extra = 0


class TpirAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'department', 'facility', 'directive_date', 'directive_end_date', 'danger')
    list_filter = ('department', 'facility', 'danger', 'directive_date')
    search_fields = (
        'directive_number',
        'facility__name',
        'department__name',
        'remedial_action'
    )
    inlines = [TpirAttachedFileInline, TpirFinanceInline]
    date_hierarchy = 'directive_date'


class TpirFinanceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'report', 'year', 'amount')
    list_filter = ('year',)
    search_fields = ('report__directive_number', 'report__facility__name')


admin.site.register(TpirFacility, TpirFacilityAdmin)
admin.site.register(Tpir, TpirAdmin)
admin.site.register(TpirFinance, TpirFinanceAdmin)
admin.site.register(TpirUserDepartment, TpirUserDepartmentAdmin)
