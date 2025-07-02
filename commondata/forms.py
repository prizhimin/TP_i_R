from django import forms


class DateForm(forms.Form):
    selected_date = forms.DateField(label='Выберите дату',
                                    input_formats=['%d.%m.%Y'],
                                    widget=forms.DateInput(attrs={'class': 'datepicker'}),
                                    )


class DateSelectionForm(forms.Form):
    report_date = forms.DateField(label='Выберите дату сводного отчёта (в формате дд.мм.гггг)',
                                  input_formats=['%d.%m.%Y'],
                                  widget=forms.DateInput(attrs={'class': 'datepicker'}),
                                  )


class DateRangeForm(forms.Form):
    start_date = forms.DateField(label="Начальная дата",
                                 input_formats=['%d.%m.%Y'],
                                 widget=forms.DateInput(attrs={'class': 'datepicker'}))

    end_date = forms.DateField(label="Конечная дата",
                               input_formats=['%d.%m.%Y'],
                               widget=forms.DateInput(attrs={'class': 'datepicker'}))

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("Конечная дата не может быть раньше начальной даты.")
        else:
            raise forms.ValidationError("Все поля должны быть заполнены.")

        return cleaned_data
