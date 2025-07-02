from django import forms
from .models import Tpir, TpirUserDepartment, Department, TpirFacility, TpirFinance
from django.core.exceptions import ValidationError
from django.utils import timezone


class TpirForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор филиалов только теми, к которым привязан пользователь
        user_departments = TpirUserDepartment.objects.filter(user=user)
        department_ids = user_departments.values_list('department__id', flat=True)
        self.fields['department'].queryset = Department.objects.filter(id__in=department_ids).order_by('name')

        # Обновляем queryset для объектов, чтобы показывать только объекты выбранного филиала
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

        # Настройка опциональных полей
        self.fields['existing_shortcomings'].required = False

        # Форматы дат
        self.fields['directive_date'].input_formats = ['%d.%m.%Y']
        self.fields['directive_end_date'].input_formats = ['%d.%m.%Y']

        # Виджеты для полей
        self.fields['directive_date'].widget = forms.DateInput(attrs={'class': 'datepicker'})
        self.fields['directive_end_date'].widget = forms.DateInput(attrs={'class': 'datepicker'})

        # Если объект существует, делаем некоторые поля read-only
        if self.instance.pk:
            self.fields['directive_number'].widget.attrs['readonly'] = True
            self.fields['directive_date'].widget.attrs['readonly'] = True

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

        # Проверка, что срок устранения не раньше даты предписания
        if directive_date and directive_end_date:
            if directive_end_date < directive_date:
                raise ValidationError({
                    'directive_end_date': 'Срок устранения нарушений не может быть раньше даты предписания'
                })

            # Дополнительная проверка, что срок устранения в будущем
            current_date = timezone.now().date()
            if directive_end_date < current_date:
                raise ValidationError({
                    'directive_end_date': 'Срок устранения нарушений должен быть в будущем'
                })

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
