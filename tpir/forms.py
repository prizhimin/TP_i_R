# from django import forms
# from .models import Tpir, TpirUserDepartment, Department, TpirFacility, TpirFinance
# from django.core.exceptions import ValidationError
# from django.utils import timezone
#

# class TpirForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)  # Добавляем прием пользователя
#         super().__init__(*args, **kwargs)
#
#         # Фильтрация филиалов для пользователя
#         if self.user:
#             user_departments = TpirUserDepartment.objects.filter(user=self.user)
#             department_ids = user_departments.values_list('department__id', flat=True)
#             self.fields['department'].queryset = Department.objects.filter(
#                 id__in=department_ids
#             ).order_by('name')
#
#         # Динамический queryset для объектов
#         if 'department' in self.data:
#             try:
#                 department_id = int(self.data.get('department'))
#                 self.fields['facility'].queryset = TpirFacility.objects.filter(
#                     department_id=department_id,
#                     is_active=True
#                 ).order_by('name')
#             except (ValueError, TypeError):
#                 pass
#         elif self.instance.pk:
#             self.fields['facility'].queryset = self.instance.department.tpirfacility_set.filter(
#                 is_active=True
#             ).order_by('name')
#         else:
#             self.fields['facility'].queryset = TpirFacility.objects.none()
#
#         # Добавляем классы для стилизации как в отчете по охране
#         self.fields['facility'].widget.attrs.update({
#             'style': 'width: calc(100% - 150px); display: inline-block; vertical-align: middle;'
#         })
#         self.fields['directive_executive'].widget.attrs.update({
#             'style': 'width: calc(100% - 150px); display: inline-block; vertical-align: middle;'
#         })
#         self.fields['remedial_action'].widget.attrs.update({
#             'style': 'width: calc(100% - 150px); display: inline-block; vertical-align: middle;'
#         })
#         self.fields['directive_date'].widget = forms.DateInput(attrs={'class': 'datepicker'})
#         self.fields['directive_end_date'].widget = forms.DateInput(attrs={'class': 'datepicker'})
#
#
#     class Meta:
#         model = Tpir
#         fields = [
#             'directive_number', 'directive_date', 'directive_end_date',
#             'department', 'facility', 'danger', 'type_tpir',
#             'remedial_action', 'directive_executive',
#             'existing_shortcomings'
#         ]
#         widgets = {
#             'existing_shortcomings': forms.Textarea(attrs={'rows': 3}),
#         }
#
#     def clean(self):
#         cleaned_data = super().clean()
#         directive_date = cleaned_data.get('directive_date')
#         directive_end_date = cleaned_data.get('directive_end_date')
#
#         if directive_date and directive_end_date:
#             if directive_end_date < directive_date:
#                 raise ValidationError({
#                     'directive_end_date': 'Срок устранения нарушений не может быть раньше даты предписания'
#                 })
#             if directive_end_date < timezone.now().date():
#                 raise ValidationError({
#                     'directive_end_date': 'Срок устранения нарушений должен быть в будущем'
#                 })
#         return cleaned_data
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Tpir, TpirUserDepartment, Department, TpirFacility, TpirFinance


class TpirForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            user_departments = TpirUserDepartment.objects.filter(user=self.user)
            department_ids = user_departments.values_list('department__id', flat=True)
            self.fields['department'].queryset = Department.objects.filter(
                id__in=department_ids
            ).order_by('name')

        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['facility'].queryset = TpirFacility.objects.filter(
                    department_id=department_id,
                    is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['facility'].queryset = self.instance.department.tpirfacility_set.filter(
                is_active=True
            ).order_by('name')
        else:
            self.fields['facility'].queryset = TpirFacility.objects.none()

        self.fields['facility'].widget.attrs.update({
            'style': 'width: calc(100% - 150px); display: inline-block; vertical-align: middle;'
        })
        self.fields['directive_executive'].widget.attrs.update({
            'style': 'width: calc(100% - 150px); display: inline-block; vertical-align: middle;'
        })
        self.fields['remedial_action'].widget.attrs.update({
            'style': 'width: calc(100% - 150px); display: inline-block; vertical-align: middle;'
        })
        self.fields['directive_date'].widget = forms.DateInput(attrs={'class': 'datepicker'})
        self.fields['directive_end_date'].widget = forms.DateInput(attrs={'class': 'datepicker'})

    class Meta:
        model = Tpir
        fields = [
            'directive_number', 'directive_date', 'directive_end_date',
            'department', 'facility', 'danger', 'type_tpir',
            'remedial_action', 'directive_executive',
            'existing_shortcomings'
        ]
        widgets = {
            'existing_shortcomings': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        directive_date = cleaned_data.get('directive_date')
        directive_end_date = cleaned_data.get('directive_end_date')

        if directive_date and directive_end_date:
            if directive_end_date < directive_date:
                raise ValidationError({
                    'directive_end_date': 'Срок устранения нарушений не может быть раньше даты предписания'
                })
            if directive_end_date < timezone.now().date():
                raise ValidationError({
                    'directive_end_date': 'Срок устранения нарушений должен быть в будущем'
                })

        # Валидация финансовых данных
        finance_errors = {}
        for key, value in self.data.items():
            if key.startswith('finance_year_'):
                prefix = key.replace('finance_year_', '')
                year = value
                amount = self.data.get(f'finance_amount_{prefix}', 0)

                if year and amount:
                    try:
                        year_int = int(year)
                        amount_float = float(amount)

                        if year_int < 2025:
                            finance_errors[key] = 'Год должен быть не меньше 2025'
                        if amount_float < 0:
                            finance_errors[f'finance_amount_{prefix}'] = 'Сумма не может быть отрицательной'

                    except ValueError:
                        finance_errors[key] = 'Некорректное значение'

        if finance_errors:
            raise ValidationError(finance_errors)

        return cleaned_data


class TpirFinanceForm(forms.ModelForm):
    class Meta:
        model = TpirFinance
        fields = ['year', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем минимальный год (можно настроить по необходимости)
        self.fields['year'].widget.attrs['min'] = 2025


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class TpirAttachedFileForm(forms.Form):
    file_field = MultipleFileField()


class TpirFilterForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        label='Филиал'
    )
    facility = forms.ModelChoiceField(
        queryset=TpirFacility.objects.none(),
        required=False,
        label='Объект'
    )
    start_date = forms.DateField(
        input_formats=['%d.%m.%Y'],
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False,
        label='С даты'
    )
    end_date = forms.DateField(
        input_formats=['%d.%m.%Y'],
        widget=forms.DateInput(attrs={'class': 'datepicker'}),
        required=False,
        label='По дату'
    )
    danger = forms.ChoiceField(
        choices=[('', 'Все')] + Tpir.DANGER_CATEGORY,
        required=False,
        label='Категория опасности'
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор филиалов для пользователя
        user_departments = TpirUserDepartment.objects.filter(user=user)
        department_ids = user_departments.values_list('department__id', flat=True)
        self.fields['department'].queryset = Department.objects.filter(
            id__in=department_ids
        ).order_by('name')

        # Динамическое обновление списка объектов при выборе филиала
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['facility'].queryset = TpirFacility.objects.filter(
                    department_id=department_id,
                    is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass


class TpirAttachedFileForm(forms.Form):
    file_field = MultipleFileField(label="Файлы для загрузки")
