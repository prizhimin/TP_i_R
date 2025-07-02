from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .forms import TpirForm
from commondata.forms import DateForm, DateSelectionForm, DateRangeForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Tpir, TpirUserDepartment



def get_date_for_report():
    return timezone.now().strftime('%d.%m.%Y')


@login_required
def tpir_list(request):
    """Список отчетов ТПИР, доступных пользователю"""
    # Получаем текущего пользователя
    user = request.user

    # Получаем филиалы, доступные пользователю
    user_departments = TpirUserDepartment.objects.filter(user=user).values_list('department__id', flat=True)

    # Фильтруем отчеты по доступным филиалам
    tpir_queryset = Tpir.objects.select_related('department', 'facility', 'created_by').filter(
        department__id__in=user_departments
    ).order_by('-directive_date', 'facility__name')

    # Если форма была отправлена методом POST, обрабатываем её
    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['selected_date']
            # Фильтруем отчёты по выбранной дате
            tpir_queryset = tpir_queryset.filter(directive_date=selected_date).order_by('created_at')
    else:
        # Если форма не отправлена, создаем форму с начальной датой для отчета
        form = DateForm(initial={'selected_date': get_date_for_report()})

    # Добавляем пагинацию
    paginator = Paginator(tpir_queryset, 14)  # Показывать 14 отчетов на странице
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Если номер страницы не является целым числом, показываем первую страницу
        page_obj = paginator.page(1)
    except EmptyPage:
        # Если номер страницы превышает количество страниц, показываем последнюю страницу
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,  # Используем стандартное имя page_obj для пагинации
        'form': form,
    }
    return render(request, 'tpir/tpir_list.html', context)


# @login_required
# def tpir_add(request):
#     """Добавление нового отчета ТПИР"""
#     if request.method == 'POST':
#         form = TpirForm(request.POST)
#         if form.is_valid():
#             new_tpir = form.save(commit=False)
#             new_tpir.created_by = request.user
#             new_tpir.save()
#             messages.success(request, 'Отчет успешно добавлен')
#             return redirect('tpir:tpir_list')
#     else:
#         form = TpirForm(user=request.user)
#
#     context = {
#         'form': form,
#         'title': 'Добавление нового отчета'
#     }
#     return render(request, 'tpir/tpir_form.html', context)


@login_required
def tpir_detail(request, pk: int):
    # Получаем объект отчёта по его id
    tpir = get_object_or_404(Tpir, pk=pk)

    return HttpResponse(f'Детали ТПиР {pk}')

# @login_required
# def tpir_detail(request, pk: int):
#     """Просмотр деталей отчета ТПИР"""
#     queryset: QuerySet = Tpir.objects.select_related(
#         'department', 'facility', 'created_by', 'updated_by'
#     )
#     tpir = get_object_or_404(queryset, pk=pk)
#
#     context = {
#         'tpir': tpir,
#         'title': f'Отчет #{tpir.id}'
#     }
#     return render(request, 'tpir/tpir_detail.html', context)
#
#
# @login_required
# def tpir_update(request, pk):
#     """Редактирование существующего отчета ТПИР"""
#     tpir = get_object_or_404(Tpir, pk=pk)
#
#     if request.method == 'POST':
#         form = TpirForm(request.POST, instance=tpir, user=request.user)  # Передаем user
#         if form.is_valid():
#             updated_tpir = form.save(commit=False)
#             updated_tpir.updated_by = request.user
#             updated_tpir.save()
#             messages.success(request, 'Отчет успешно обновлен')
#             return redirect('tpir:tpir_detail', pk=pk)
#     else:
#         form = TpirForm(instance=tpir, user=request.user)  # Передаем user
#
#     context = {
#         'form': form,
#         'title': f'Редактирование отчета #{tpir.id}',
#         'tpir': tpir
#     }
#     return render(request, 'tpir/tpir_form.html', context)
#
#
# @login_required
# def tpir_delete(request, pk):
#     """Удаление отчета ТПИР"""
#     tpir = get_object_or_404(Tpir, pk=pk)
#
#     if request.method == 'POST':
#         tpir.delete()
#         messages.success(request, 'Отчет успешно удален')
#         return redirect('tpir:tpir_list')
#
#     context = {
#         'tpir': tpir,
#         'title': f'Удаление отчета #{tpir.id}'
#     }
#     return render(request, 'tpir/tpir_confirm_delete.html', context)
